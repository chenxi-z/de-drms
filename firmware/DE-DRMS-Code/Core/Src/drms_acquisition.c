/*****************************************************************************
 * 文件：drms_acquisition.c
 * 职责：ADS131A02 采集通道——把 DRDY 边沿变成一帧 12 字节数据并送进采集环。
 *
 * 在整机中的位置：
 *   DRDY(PA3) → 本模块 → 采集环(4096 帧) → 应用线程取走做解码与记录
 *   本模块只负责"把原始字节搬进来"，不做校验、累计和判级；那些在
 *   drms_measurement.c 与 drms_application.c 里完成。
 *
 * 两条传输路径：
 *   1. 快速路径（默认）：每帧只重装两路 GPDMA 通道并置 CSTART，
 *      由 GPDMA1_Channel1 中断收尾。64 kSPS 以下零丢帧。
 *   2. HAL 路径：仅在注释掉快速路径时用于对照，已不参与生产。
 *
 * 关键设计取舍（每条都有实机证据，改动前请先读）：
 *   · SPI 配置只做一次，不每帧重写。实测传输结束后 TSIZE 保持 12、SPE 保持 1，
 *     所以每帧重写既多余又会引入 UDR/OVR 错误。
 *   · 每帧必须清 IFCR 错误标志。上一帧锁存的 UDR/OVR 会让下一帧直接失败，
 *     这是最早卡住整整十几轮调试的死结。
 *   · 每帧必须断言 SPE。有错误路径会把 SPE 清掉，而 CSTART 在 SPE=0 时被忽略。
 *   · 完成时必须同时关两路通道。只关发送侧会让下一帧的占用检查必然失败，
 *     这个疏漏曾让 64 kSPS 100% 丢帧。
 *   · DRDY 中断优先级必须低于 GPDMA。否则新转换会抢占上一帧的通道重装，
 *     实测重装被拉长到 16 µs，超过整帧预算。
 *
 * 采样率上限：64 kSPS。128 kSPS 下 ADC 会返回 F_DRDY（输出寄存器未及时读出），
 * 属读取时序不足而非通信错误，详见 README.md 的实测记录。
 *****************************************************************************/

#include "drms_acquisition.h"
#include "drms_measurement.h"
#include "drms_fifo.h"
#include "drms_capture_time.h"
#include "main.h"
#include "spi.h"
#include <string.h>

/* 一帧的字节数。DMA 块长度与 SPI 的 TSIZE 都用它，两者必须始终一致。 */
#define EXCHANGE_BYTES (12u)

/* 实机验证过的无损采样率上限，超过即在入口拒绝（见 drms_acq_start）。 */
#define DRMS_ACQ_MAX_RATE (64000u)

/* 采集环：ISR 写入、应用线程读取，4096 帧的深度在 64 kSPS 下约 64 ms 缓冲。
 * 单生产者单消费者，drms_fifo 内部无锁。 */
static DRMS_RawFrame frames[4096];
static DRMS_FIFO queue;

/* 接收双缓冲。单缓冲时下一帧必须等上一帧的 DMA 与完成中断都结束，
 * 这个闭环在高速档放不进帧预算；双缓冲让 DMA 可以在消费上一帧的同时
 * 装填下一帧，可容忍的闭环时间翻倍。
 * dma_rx 保存"最近一次完成"的帧，供 complete_frame 读取。 */
static uint8_t dma_rx_buf[2][12] __attribute__((aligned(4)));
static uint8_t dma_rx[12] __attribute__((aligned(4)));
static uint8_t dma_tx[12] __attribute__((aligned(4)));
static volatile uint32_t rx_buf_index;

/* 主机测试用钩子：单元测试需要把模拟的帧写进快速路径刚装填的缓冲区。
 * 64 位主机上寄存器只能存下地址低 32 位，无法还原指针，所以直接交出地址。
 * 固件本身从不调用。 */
uint8_t *drms_acq_test_rx_buffer(void)
{
  return dma_rx_buf[rx_buf_index ^ 1u];
}

/*============================================================================
 * 快速采集路径
 *
 * 为什么不用 HAL：HAL_SPI_TransmitReceive_DMA 每帧都要重新校验句柄、
 * 重算收发长度、重挂四个 DMA 回调，再调用两次 HAL_DMA_Start_IT。
 * 64 kSPS 时每帧预算 15.6 µs，SPI 传输占 4.0 µs，剩下的时间放不下这些开销。
 *
 * 实机验证过的事实（改动前务必先读）：
 *   传输结束后 SPI 的 TSIZE 仍是 12、SPE 仍是 1、CSTART 归 0，
 *   所以外设只需在启动时配置一次，每帧只重装 DMA 通道并置 CSTART。
 *============================================================================*/

/* 快速路径当前是否持有一帧传输的所有权（正在等 DMA 完成）。 */
static int fast_path_active;

/* 调试计数器。通过 SWD 读，用来判断快速路径启动了几次、中断来了几次、
 * 失败了几次。生产环境不会用到，但排查"帧丢了"这类问题非常有效。 */
volatile uint32_t drms_acq_fx_start, drms_acq_fx_fail, drms_acq_fx_irq, drms_acq_fx_done;

/* 时序探针（DWT 周期计数器，核心 160 MHz）。三段分别测量：
 *   isr_us：ISR 入口 → CS 拉低，覆盖中断前导、序号记账、时间戳
 *   arm_us：CS 拉低 → CSTART，即 DMA 重装这一段
 *   tot_us：ISR 入口 → CSTART
 * 同时保留最小/最大/累计值，避免抖动被平均值掩盖。 */
volatile uint32_t drms_acq_t_isr_min, drms_acq_t_isr_max, drms_acq_t_isr_sum;
volatile uint32_t drms_acq_t_arm_min, drms_acq_t_arm_max, drms_acq_t_arm_sum;
volatile uint32_t drms_acq_t_tot_min, drms_acq_t_tot_max, drms_acq_t_tot_sum;
volatile uint32_t drms_acq_t_n;

/* Enable explicitly when profiling ISR latency. Keep division/statistics out of
 * every production DRDY interrupt; this does not disable any integrity checks. */
#ifndef DRMS_ACQ_TIMING_PROBE
#define DRMS_ACQ_TIMING_PROBE 0
#endif

/* 装填并启动一次 12 字节交换。
 *
 * 返回值：0 = 已启动；非 0 = 上一帧的通道还没释放，调用方按丢帧计。
 *
 * 调用约束：只在 DRDY 中断里调用；调用前必须已拉低 CS。
 * 执行时间：实测 arm 段平均约 1.9 µs（含被抢占的尖峰），是高速档的关键路径。 */
static int fast_exchange_start(void)
{
  DMA_Channel_TypeDef *rx_ch = hspi1.hdmarx->Instance;
  DMA_Channel_TypeDef *tx_ch = hspi1.hdmatx->Instance;

  /* 上一帧的通道若仍使能，此刻重装会让两帧的数据互相覆盖，
   * 宁可直接放弃这一帧。 */
  if ((rx_ch->CCR & DMA_CCR_EN) || (tx_ch->CCR & DMA_CCR_EN))
    return 1;

  /* 两片缓冲交替使用：DMA 装填下一帧的同时，刚完成的那帧保持完好可读。 */
  uint32_t slot = rx_buf_index ^ 1u;

  /* 通道重装：块长度、源/目的地址、清挂起标志。
   * 顺序与 HAL 的 DMA_SetConfig 一致——先写几何参数再清标志。
   * 残留的 TC/DTE/USE 标志会让下一帧无法启动，这是必须清的原因。 */
  rx_ch->CBR1 = EXCHANGE_BYTES;
  rx_ch->CSAR = (uint32_t)(uintptr_t)&hspi1.Instance->RXDR;
  rx_ch->CDAR = (uint32_t)(uintptr_t)dma_rx_buf[slot];
  rx_ch->CFCR = DMA_FLAG_TC | DMA_FLAG_HT | DMA_FLAG_DTE | DMA_FLAG_ULE |
                DMA_FLAG_USE | DMA_FLAG_SUSP | DMA_FLAG_TO;

  tx_ch->CBR1 = EXCHANGE_BYTES;
  tx_ch->CSAR = (uint32_t)(uintptr_t)dma_tx;
  tx_ch->CDAR = (uint32_t)(uintptr_t)&hspi1.Instance->TXDR;
  tx_ch->CFCR = DMA_FLAG_TC | DMA_FLAG_HT | DMA_FLAG_DTE | DMA_FLAG_ULE |
                DMA_FLAG_USE | DMA_FLAG_SUSP | DMA_FLAG_TO;

  /* 只让接收侧产生中断——它标志着一次交换结束。
   * 发送侧由 SPI 的请求线驱动，若放开它的中断会进入 HAL_DMA_IRQHandler，
   * 而 HAL 并不认识这个传输，会把状态机搞乱。 */
  SET_BIT(rx_ch->CCR, DMA_CCR_TCIE | DMA_CCR_DTEIE);
  CLEAR_BIT(tx_ch->CCR, DMA_CCR_TCIE | DMA_CCR_HTIE | DMA_CCR_DTEIE);

  /* 清掉上一帧遗留的 SPI 错误标志。
   * 锁存的 UDR（发送下溢）或 OVR（接收溢出）会让外设认为仍在故障中，
   * 拒绝执行下一次交换——这是最初"只有第一帧成功"的真正原因。
   * 通过 IFCR 清除，不去动 SPE。 */
  SET_BIT(hspi1.Instance->IFCR, SPI_IFCR_OVRC | SPI_IFCR_UDRC | SPI_IFCR_EOTC |
                                  SPI_IFCR_TXTFC | SPI_IFCR_SUSPC | SPI_IFCR_MODFC);

  /* 打开 SPI 的 DMA 请求闸门，再使能两路通道。
   * SPI 本身保持使能跨帧复用——在这里 disable 会制造 UDR/OVR，
   * 并且会破坏后续切换采样率时 HAL 的 exchange()。 */
  SET_BIT(hspi1.Instance->CFG1, SPI_CFG1_TXDMAEN | SPI_CFG1_RXDMAEN);
  SET_BIT(rx_ch->CCR, DMA_CCR_EN);
  SET_BIT(tx_ch->CCR, DMA_CCR_EN);

  /* 每帧都要断言 SPE。初始化后的 exchange() 会留下使能状态，但完成清理
   * 或某条错误路径可能把它清掉，而 SPE=0 时 CSTART 会被硬件忽略，
   * 表现为"启动了但一帧也收不到"。SPE 能跨完成保持，这里不会重启状态机。 */
  __HAL_SPI_ENABLE(&hspi1);
  SET_BIT(hspi1.Instance->CR1, SPI_CR1_CSTART);
  ++drms_acq_fx_start;
  return 0;
}

/* 在中断里收尾一次交换：交出刚完成的帧、释放两路通道、关掉 DMA 请求闸门。
 *
 * 调用约束：只在 GPDMA1_Channel1 中断里调用，且调用前 fast_path_active 必须为 1。 */
static void fast_exchange_finish(void)
{
  DMA_Channel_TypeDef *rx_ch = hspi1.hdmarx->Instance;
  DMA_Channel_TypeDef *tx_ch = hspi1.hdmatx->Instance;
  uint32_t flags = rx_ch->CSR;

  /* 先把刚填满的那片缓冲交给消费者，同时把另一片选给下一次传输。
   * 交换必须在关通道之前完成，否则 complete_frame() 里的拷贝会和
   * 下一次 DMA 抢同一块内存。 */
  rx_buf_index ^= 1u;
  memcpy(dma_rx, dma_rx_buf[rx_buf_index], sizeof(dma_rx));

  rx_ch->CFCR = flags;
  /* 两路通道都要关，不能只关发送侧。
   * 正常模式下接收通道完成时会自动清 EN，但指望这一点并不可靠——
   * 实测 64 kSPS 以上它常常还留着使能，导致下一帧的占用检查每次失败，
   * 表现为 100% 丢帧。显式关掉两路，才能让帧首的前置条件确定。 */
  CLEAR_BIT(tx_ch->CCR, DMA_CCR_EN);
  CLEAR_BIT(rx_ch->CCR, DMA_CCR_EN);
  CLEAR_BIT(hspi1.Instance->CFG1, SPI_CFG1_TXDMAEN | SPI_CFG1_RXDMAEN);
  fast_path_active = 0;
}

static volatile uint32_t busy, last_completion, abort_unconfirmed;
static uint32_t inflight_sequence;
static uint64_t inflight_capture_us, consumed_ticket;
static uint64_t cached_capture_us;
static uint32_t clock_last_tick;
static uint64_t clock_epoch_ms;
static unsigned int frame_size, powered;
volatile uint32_t drms_acq_running, drms_acq_rate, drms_acq_reference;
volatile uint32_t drms_acq_last_push_ms; /* 最近帧入环时刻（过渡用；T8 换 DRDY 实测） */
volatile uint32_t drms_acq_edges, drms_acq_overruns, drms_acq_queue_drops;
volatile uint32_t drms_acq_error;
/* 初始化往来记录：只记录启动阶段，供 SWD 读取，不必逐帧停核。
 * 布局：word0 = command | length<<16 | HAL_status<<24，word1..3 = 收到的数据。
 * 当初就是靠它发现 ADC 返回的是 HAL_TIMEOUT。 */
volatile uint32_t drms_acq_init_trace[24][4];
volatile uint32_t drms_acq_init_trace_count;

/* 64 位流记账（C1）。生产端唯一写者：DRDY ISR / DMA 完成 ISR / 启停路径。
 * 跨上下文一致读取仅在边界快照的短临界区内进行。 */
static uint64_t sample_seq_next, raw_ticket_next, capture_lost_total, unknown_loss_epoch;
static uint32_t acquisition_generation;
static struct { DRMS_Token token; uint32_t armed; } boundary_pending;
static struct { DRMS_Token token; uint32_t valid; DRMS_CaptureBoundary boundary; } boundary_reply;

/* 进临界区：关全局中断，返回进入前的 PRIMASK。
 * 只能保护"几条赋值"这种粒度；任何可能阻塞的操作都不该放进来。 */
static uint32_t crit_enter(void)
{
  uint32_t mask = __get_PRIMASK();
  __disable_irq();
  return mask;
}

/* 退出临界区，恢复 crit_enter 保存的中断屏蔽状态。 */
static void crit_exit(uint32_t mask) { __set_PRIMASK(mask); }

/* 读当前时间（微秒），单调递增。
 *
 * 内部处理了 32 位 tick 回绕：检测到 tick 变小就把高位纪元加一，
 * 因此可以长时间运行而不返回倒退的时间。
 * 注意要进临界区，在中断里调用有约 2 µs 的代价。 */
uint64_t drms_acq_now_us(void)
{
  uint32_t mask = crit_enter();
  uint32_t tick = HAL_GetTick();
  if (tick < clock_last_tick)
    clock_epoch_ms += (1ULL << 32);
  clock_last_tick = tick;
  uint64_t now = (clock_epoch_ms + tick) * 1000u;
  crit_exit(mask);
  return now;
}

/* 比较两个令牌是否指向同一次操作：操作号与代次都必须相同。
 * 代次用于区分"重启后复用了同一个操作号"的情况。 */
static uint32_t token_match(DRMS_Token a, DRMS_Token b)
{
  return a.operation_id == b.operation_id && a.generation == b.generation;
}

/* 以下一组只读访问器供其他模块查询采集侧状态。
 * 它们都在极短的函数里读取 volatile 变量，不需要额外同步。 */
uint32_t drms_acq_generation(void) { return acquisition_generation; }
uint64_t drms_acq_sample_seq_next(void) { return sample_seq_next; }
uint64_t drms_acq_raw_ticket_next(void) { return raw_ticket_next; }
uint64_t drms_acq_capture_lost_total(void) { return capture_lost_total; }
uint64_t drms_acq_unknown_loss_epoch(void) { return unknown_loss_epoch; }

/* 请求一次采集边界快照。
 *
 * 边界只在"没有在途 DMA"的静止时刻归结：本函数只把请求装填进去，
 * 真正的快照由 drms_acq_boundary_service 在中断静止点完成。
 * 这样边界的样本序号、损失计数都是同一时刻的一致视图。
 *
 * 参数：token 用于把回复关联回发起方（含操作号与代次）。
 * 返回：ACCEPTED 表示已受理；BUSY 表示已有边界在途。 */
DRMS_Result drms_acq_boundary_request(DRMS_Token token)
{
  uint32_t mask;
  if (!drms_acq_running)
    return DRMS_INVALID;
  mask = crit_enter();
  if (boundary_pending.armed || boundary_reply.valid)
  {
    crit_exit(mask);
    return DRMS_BUSY; /* preserve an unanswered boundary until it is consumed */
  }
  boundary_pending.token = token;
  boundary_pending.armed = 1;
  crit_exit(mask);
  return DRMS_ACCEPTED;
}

/* 采集环当前占用的槽位数，供监督者判断积压程度。 */
uint32_t drms_acq_queue_used(void)
{
  return drms_fifo_count(&queue);
}

/* 撤销一个尚未归结的边界请求。已归结的边界不受影响。 */
void drms_acq_boundary_cancel(DRMS_Token token)
{
  uint32_t mask = crit_enter();
  if (boundary_pending.armed && token_match(boundary_pending.token, token))
    boundary_pending.armed = 0;
  if (boundary_reply.valid && token_match(boundary_reply.token, token))
    boundary_reply.valid = 0;
  crit_exit(mask);
}

/* 在中断静止点归结挂起的边界请求。
 *
 * 调用时机：每帧完成之后（此时没有在途传输）。若仍有在途 DMA 则直接返回，
 * 留到下一次静止点处理——绝不在临界区里等 DMA。
 *
 * 快照内容包括：代次、样本序号、原始票据号、累计捕获损失、未知损失纪元，
 * 五者用同一把临界区一起取出，保证互相自洽。 */
void drms_acq_boundary_service(void)
{
  /* 进临界区之前先做一次廉价判断。边界请求很少被装填，但这个函数每帧都跑；
   * 高速档下"关中断—开中断"这一对本身的代价就超过判断，不值得为它付出。 */
  if (!boundary_pending.armed && !busy)
    return;
  uint32_t mask = crit_enter();
  if (!boundary_pending.armed || busy)
  {
    crit_exit(mask);
    return; /* 等待当前 DMA 完成：不在临界区内等待，静止时刻再归结 */
  }
  boundary_reply.token = boundary_pending.token;
  boundary_reply.boundary.acquisition_generation = acquisition_generation;
  boundary_reply.boundary.sample_next = sample_seq_next;
  boundary_reply.boundary.raw_next = raw_ticket_next;
  boundary_reply.boundary.capture_lost_total = capture_lost_total;
  boundary_reply.boundary.unknown_loss_epoch = unknown_loss_epoch;
  boundary_reply.valid = 1;
  boundary_pending.armed = 0;
  crit_exit(mask);
}

/* 取回某次边界请求的结果。
 *
 * 返回 ACCEPTED 表示 out 已填好；BUSY 表示还没归结；其他表示令牌不匹配
 * 或已被取消。 */
DRMS_Result drms_acq_boundary_get(DRMS_Token token, DRMS_CaptureBoundary *out)
{
  uint32_t mask;
  DRMS_Result result;
  if (!out)
    return DRMS_INVALID;
  mask = crit_enter();
  if (!boundary_reply.valid)
  {
    crit_exit(mask);
    return DRMS_EMPTY;
  }
  if (!token_match(boundary_reply.token, token))
  {
    crit_exit(mask);
    return DRMS_STALE;
  }
  *out = boundary_reply.boundary;
  boundary_reply.valid = 0;
  result = DRMS_OK;
  crit_exit(mask);
  return result;
}

/* 片选翻转。直接写 BSRR，不走 HAL_GPIO_WritePin，也去掉了原来那段
 * 32 次 volatile NOP 延时。
 *
 * 那段延时的代价被严重低估：volatile 计数器每轮都要读内存，单次约 150 周期，
 * 而这个函数每帧要调两次，等于吃掉近 2 µs。在 128 kSPS 的 7.81 µs 预算里，
 * 它正好是"闭环刚好差一点"和"丢掉一半帧"的分界线。
 *
 * CS 高电平时间由"解码并投递刚完成那一帧"的耗时自然满足，不需要额外补延时。 */
static void cs(unsigned int high)
{
  if (high)
    ADS_CS_GPIO_Port->BSRR = ADS_CS_Pin;
  else
    ADS_CS_GPIO_Port->BSRR = (uint32_t)ADS_CS_Pin << 16u;
}

/* 阻塞式完成一次 SPI 交换，仅用于启动阶段的寄存器配置。
 *
 * 走 HAL 的轮询模式，超时 20 ms。采集阶段绝不会调用它——那里用的是
 * fast_exchange_start，逐帧开销必须足够低。
 *
 * 参数：command 为要发送的命令字（0 表示只读数据）；response 非空时回填
 * 应答的前两字节。
 * 返回：1 表示交换成功且 CRC 校验通过；0 表示失败。 */
static int exchange(uint16_t command, uint16_t *response)
{
  uint8_t tx[12] = {0}, rx[12] = {0};
  tx[0] = command >> 8;
  tx[1] = command & 255;
  if (frame_size == 12)
  {
    uint16_t crc = drms_crc16(tx, 9);
    tx[9] = crc >> 8;
    tx[10] = crc & 255;
  }
  cs(0);
  HAL_StatusTypeDef status = HAL_SPI_TransmitReceive(&hspi1, tx, rx, (uint16_t)frame_size, 20);
  cs(1);
  if (drms_acq_init_trace_count < 24u)
  {
    uint32_t index = drms_acq_init_trace_count;
    drms_acq_init_trace[index][0] = command | (frame_size << 16) | ((uint32_t)status << 24);
    for (unsigned int i = 0; i < 3u; ++i)
      drms_acq_init_trace[index][i + 1u] = (uint32_t)rx[4u*i] | ((uint32_t)rx[4u*i+1u] << 8) |
          ((uint32_t)rx[4u*i+2u] << 16) | ((uint32_t)rx[4u*i+3u] << 24);
    drms_acq_init_trace_count = index + 1u;
  }
  if (status != HAL_OK || rx[2] != 0)
    return 0;
  if (frame_size == 12 &&
      (rx[11] != 0 || drms_crc16(rx, 9) != (uint16_t)(((uint16_t)rx[9] << 8) | rx[10])))
    return 0;
  *response = (uint16_t)(((uint16_t)rx[0] << 8) | rx[1]);
  return 1;
}

/* 发送一条命令并确认 ADC 逐字回显了它。
 *
 * 用于解锁、唤醒这类"没有数据返回、必须靠回显确认"的命令。
 * 返回：1 表示回显一致。 */
static int command_ack(uint16_t command)
{
  uint16_t ignored, response;
  return exchange(command, &ignored) && exchange(0, &response) && response == command;
}

/* 写一个 ADC 寄存器并校验回读。
 *
 * 写入命令发出后，ADC 要到当前这一帧结束才生效，所以这里再发一次空命令
 * 去取应答。有两处特例：
 *   · 地址 0x0C（D_SYS_CFG）会同时把帧长切成 12，因为 CRC 与定长帧一起启用；
 *   · 地址 0x0F 的全局使能位按手册写 0Fh，但两通道的 A02 回读为 2F03h，
 *     这里放行这个已知差异。
 *
 * 返回：1 表示回读与期望一致（或命中上述特例）。 */
static int write_register(uint8_t address, uint8_t value)
{
  uint16_t ignored, response;
  if (!exchange((uint16_t)(0x4000U | ((uint16_t)address << 8) | value), &ignored))
    return 0;
  /* 这个写入要到它当前这一帧（旧帧）结束时才生效，
   * 所以帧长要在这里就切到 12，否则会按旧长度解析应答。 */
  if (address == 0x0c)
    frame_size = 12;
  if (!exchange(0, &response))
    return 0;
  /* 全局通道使能位按手册写 0Fh（四位全开）。但首板这颗是两通道的 A02，
   * 它只承认自己实际实现了的通道，回读为 2F03h。
   * 所以写入值仍用手册值，只在回读校验上放行这个已知差异。 */
  if (address == 0x0f && value == 0x0f && response == 0x2f03)
    return 1;
  return response == (uint16_t)(0x2000U | ((uint16_t)address << 8) | value);
}

/* 把 SPI 外设恢复成 HAL 期望的空闲形态，让下次启动时用来重配 ADC 的
 * 阻塞式 exchange() 拿到一个干净的复位状态。
 *
 * 快速路径会把 SPE 和 TSIZE 都留在"事务进行中"的样子——这对逐帧重启正合适，
 * 对 HAL_SPI_TransmitReceive 却是错的：那个函数会自己装填传输长度，
 * 从不预期已经有事务在跑。两者撞上的后果是切换采样率时 READY 轮询读不到应答，
 * 启动以 adc_error=1 失败。 */
static void spi_release_to_idle(void)
{
  DMA_Channel_TypeDef *rx_ch = hspi1.hdmarx->Instance;
  DMA_Channel_TypeDef *tx_ch = hspi1.hdmatx->Instance;

  CLEAR_BIT(hspi1.Instance->CFG1, SPI_CFG1_TXDMAEN | SPI_CFG1_RXDMAEN);
  CLEAR_BIT(rx_ch->CCR, DMA_CCR_EN);
  CLEAR_BIT(tx_ch->CCR, DMA_CCR_EN);
  rx_ch->CFCR = DMA_FLAG_TC | DMA_FLAG_HT | DMA_FLAG_DTE | DMA_FLAG_ULE |
                DMA_FLAG_USE | DMA_FLAG_SUSP | DMA_FLAG_TO;
  tx_ch->CFCR = DMA_FLAG_TC | DMA_FLAG_HT | DMA_FLAG_DTE | DMA_FLAG_ULE |
                DMA_FLAG_USE | DMA_FLAG_SUSP | DMA_FLAG_TO;

  __HAL_SPI_DISABLE(&hspi1);
  SET_BIT(hspi1.Instance->IFCR, SPI_IFCR_OVRC | SPI_IFCR_UDRC | SPI_IFCR_EOTC |
                                  SPI_IFCR_TXTFC | SPI_IFCR_SUSPC | SPI_IFCR_MODFC);
  /* 千万不要把 TSIZE 清零。
   * RM0456 明确：CSTART 配上 TSIZE=0 会开启一个"无限事务"。清零后外设就停在
   * 这个模式里，导致重配 ADC 的阻塞式 HAL_SPI_TransmitReceive 在第一次交换
   * 就超时（初始化记录里抓到的是 HAL_TIMEOUT，一次 READY 轮询都没成功）。
   * HAL 每次调用都会自己设定需要的长度，保留上一个值是安全且必要的。 */

  fast_path_active = 0;
  hspi1.State = HAL_SPI_STATE_READY;
  hspi1.ErrorCode = HAL_SPI_ERROR_NONE;
  __HAL_UNLOCK(&hspi1);
}

/* 停止采集并让 ADC 进入安全的断电状态。
 *
 * 顺序：先清 running 与激励，再按"隔离判据"处理在途传输，最后拉低 RESET
 * 并断开模拟电源。断电保持时间见下方注释——给短了救不回停在半帧的 ADC。
 *
 * 可在任意上下文调用，但其中有 HAL_Delay，不要在中断里调用。 */
void drms_acq_stop(void)
{
  if (drms_acq_running)
    ++unknown_loss_epoch; /* 停止后观察到的 DRDY 无法计数：连续性不可证明 */
  drms_acq_running = 0;
  HAL_GPIO_WritePin(CURR_DIS_GPIO_Port, CURR_DIS_Pin, GPIO_PIN_SET);
  if (busy && !abort_unconfirmed)
  {
    /* 隔离判据是"这次传输能不能被证明已经结束"。HAL_SPI_Abort 正是回答这个问题的，
     * 它做不到就让设备停在隔离态，等显式 recover——这与快速路径出现之前的行为一致。
     * 无论结果如何，随后都由 spi_release_to_idle 收拾外设。 */
    if (HAL_SPI_Abort(&hspi1) == HAL_OK)
      busy = 0;
    else
    {
      abort_unconfirmed = 1;
      drms_acq_error = 3;
    }
  }
  spi_release_to_idle();
  busy = 0;
  cs(1);
  /* 先拉低 RESET，再断模拟电源，并且各自保持一段时间。
   * 原来的顺序是两者同时拉低、没有任何延时——对正常停止够用，但清不掉
   * "停在一帧中间"的 ADC：128 kSPS 失败之后，设备会在 STOP/START 之间
   * 反复报数据超时，只有整片 MCU 复位才能恢复。
   * SBAS590E 要求 RESET 低电平至少 800 ns；这里留的余量同时让模拟轨真正放电，
   * 使下一次启动等价于一次上电。 */
  HAL_GPIO_WritePin(ADS_RESET_GPIO_Port, ADS_RESET_Pin, GPIO_PIN_RESET);
  HAL_Delay(2);
  HAL_GPIO_WritePin(ANA_EN_GPIO_Port, ANA_EN_Pin, GPIO_PIN_RESET);
  /* 断电要断够久，让模拟轨真正塌下去。
   * 高速档停在半帧的 ADC（STAT_1 报 F_DRDY，说明输出寄存器一直没被读走）
   * 靠几毫秒的短促断电救不回来：实测后续 START 能成功重新配置，
   * 但再也不产生 DRDY，只有 MCU 复位才清得掉。
   * 这段时延由模拟轨的输出电容主导，所以余量给得比较宽松。 */
  HAL_Delay(50);
  powered = 0;
}

/* 启动采集。
 *
 * 参数：rate 为采样率（必须 ≤ DRMS_ACQ_MAX_RATE）；reference 非 0 表示
 * 切到参考支路（校准用），0 表示样品支路。
 * 返回：1 成功；0 失败（adc_error 已置具体原因）。
 *
 * 完整流程：释放外设 → 校验 SPI 配置 → 断电复位 ADC → 按模式设置开关 →
 * 上电 → 等待建立 → 逐项写寄存器并校验 → 留好快速路径所需的外设形态。
 * 全程用阻塞式 exchange()，所以这段时间不能有采集在跑。 */
int drms_acq_start(uint32_t rate, unsigned int reference)
{
  drms_acq_init_trace_count = 0;
  uint8_t clk2;
  uint16_t ready = 0, ignored;
  /* 拒绝超出能力包线的采样率。
   *
   * 128 kSPS 在这块板上做不到：ADC 会报 F_DRDY（输出寄存器来不及被读走），
   * 而且一旦被推到那个状态，它就彻底停止产生 DRDY——后续 START 能成功重配，
   * 却再也等不到新帧，只有整片 MCU 复位才救得回来。
   *
   * 与其放进去再想办法救，不如在入口拒绝：设备保持可用，调用方拿到明确的
   * cmd_result=2，而不是"回了一句接受、实际什么也没做"的假成功。
   * 完整实测见 firmware/DE-DRMS-Code/README.md。 */
  if (rate > DRMS_ACQ_MAX_RATE)
  {
    /* 别让上一次的超限速率留在 STATUS 里：否则下一条不带参数的 START
     * 会照着它再试一遍。这里把速率归到上限，并把错误码置为 2
     * （速率不被接受），让主机能明确知道请求被拒。 */
    drms_acq_stop();
    drms_acq_rate = DRMS_ACQ_MAX_RATE;
    drms_acq_error = 2;
    return 0;
  }
  if (!drms_rate_register(rate, &clk2) || reference > 1)
    return 0;
  /* 先把外设释放掉，再谈别的。
   * 高速档自行停采时（队列溢出会置 adc_error=6 并清 running）根本不经过
   * drms_acq_stop，于是快速路径的事务状态会残留到下一次启动，
   * 让阻塞式 exchange() 读不到 ADC 的 READY 应答。
   * 在这里无条件收尾，启动就不再依赖"上一次是怎么结束的"。 */
  spi_release_to_idle();
  /* 注意 HAL 的 Size 参数数的是"数据字"而不是字节。
   * 一旦 CubeMX 重新生成把 SPI 改成非 8 bit 数据宽度，阻塞或 DMA 传输就可能
   * 越过 12 字节的帧缓冲写坏内存。所以这里先校验再放行。 */
  if (hspi1.Init.DataSize != SPI_DATASIZE_8BIT || hspi1.Init.Mode != SPI_MODE_MASTER ||
      hspi1.Init.CLKPolarity != SPI_POLARITY_LOW || hspi1.Init.CLKPhase != SPI_PHASE_2EDGE ||
      hspi1.Init.FirstBit != SPI_FIRSTBIT_MSB || hspi1.Init.NSS != SPI_NSS_SOFT)
  {
    drms_acq_stop();
    drms_acq_error = 2;
    return 0;
  }
  drms_acq_stop();
  if (abort_unconfirmed)
    return 0;
  drms_acq_error = 0;
  drms_acq_edges = drms_acq_overruns = drms_acq_queue_drops = 0;
  /* 新采集代次：流计数清零，边界请求/回复一并作废（旧代次边界不得交付）。 */
  sample_seq_next = raw_ticket_next = capture_lost_total = unknown_loss_epoch = 0;
  consumed_ticket = 0;
  drms_capture_time_reset();
  ++acquisition_generation;
  boundary_pending.armed = 0;
  boundary_reply.valid = 0;
  (void)drms_fifo_init(&queue, frames, 4096, sizeof(frames[0]));
  /* 按模式设置开关对。这里的电平映射与直觉相反，很容易搞反：
   * SEL_SENSE 拉低时 K4 接到 F（参考侧），所以**低电平才是校准态**、
   * 高电平才是样品态。
   * 曾经把两路都写反，后果是 MEASURE 实际接通了 R_ref、REF 却只连到空着的
   * 样品支路——表现为参考模式下测量通道满量程、而 Rsense 上几乎没有电流，
   * 校准一个样本都取不到。
   *
   * 两条线必须始终同向变化：SEL_SENSE 高而 SEL_K2 低会让样品与 R_ref
   * 经 X 点并联，这是设计上禁止的状态。 */
  if (reference)
  {
    HAL_GPIO_WritePin(SEL_SENSE_GPIO_Port, SEL_SENSE_Pin, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(SEL_K2_GPIO_Port, SEL_K2_Pin, GPIO_PIN_RESET);
  }
  else
  {
    HAL_GPIO_WritePin(SEL_K2_GPIO_Port, SEL_K2_Pin, GPIO_PIN_SET);
    HAL_GPIO_WritePin(SEL_SENSE_GPIO_Port, SEL_SENSE_Pin, GPIO_PIN_SET);
  }
  drms_acq_reference = reference;
  HAL_GPIO_WritePin(ANA_EN_GPIO_Port, ANA_EN_Pin, GPIO_PIN_SET);
  powered = 1;
  HAL_Delay(10);
  HAL_GPIO_WritePin(ADS_RESET_GPIO_Port, ADS_RESET_Pin, GPIO_PIN_SET);
  HAL_Delay(50);
  frame_size = 3; /* POR: dynamic frame, ADCs off, no CRC; 24-bit strap. */
  uint32_t started = HAL_GetTick();
  do
  {
    if (!exchange(0, &ready))
      break;
    if (ready == 0xff02)
      break;
    HAL_Delay(1);
  } while ((uint32_t)(HAL_GetTick() - started) < 500U);
  if (ready != 0xff02)
  {
    drms_acq_error = 1;
    goto failed;
  }
  /* 寄存器配置的依据（SBAS590E §9.6 / §10.4）：
   *   本板 VNCP 接 AVSS，所以 VNCPEN 必须保持 0（这里即不写该位）。
   *   A_SYS_CFG=0x68：高分辨率模式，保留位 bit5 置 1，内部 2.442 V 基准。
   *   CLK1=0x02：ICLK 分频。
   *   CLK2=0x2n：分频 + 选定的 OSR（n 随采样率变化）。
   *   D_SYS_CFG=0x7f：CRC 覆盖前面所有字节，固定四字帧。
   *
   * 顺序很重要：先把定长帧和 CRC 打开，再写模拟与参考相关的寄存器。 */
  if (!command_ack(0x0655) || !write_register(0x0c, 0x7f) ||
      !write_register(0x0b, 0x68) || !write_register(0x0d, 0x02) || !write_register(0x0e, clk2) ||
      !write_register(0x0f, 0x0f) ||
      !command_ack(0x0033) || !command_ack(0x0555))
  {
    drms_acq_error = 2;
    goto failed;
  }
  HAL_GPIO_WritePin(CURR_DIS_GPIO_Port, CURR_DIS_Pin, GPIO_PIN_RESET);
  /* 首板保守的建立等待，覆盖 sinc3 数字滤波器的群延时与模拟前端恢复。
   * 这段时间内采到的样本一律不标记为有效。 */
  HAL_Delay(100);
  if (!exchange(0, &ignored))
  {
    drms_acq_error = 2;
    goto failed;
  }
  memset(dma_tx, 0, sizeof(dma_tx));
  uint16_t crc = drms_crc16(dma_tx, 9);
  dma_tx[9] = crc >> 8;
  dma_tx[10] = crc & 255;
  drms_acq_rate = rate;
  /* 把外设留在快速路径假设的形态：已使能，且 12 字节帧长已经锁存，
   * 这样每一帧只需要一次 CSTART。
   * SWD 实测过 TSIZE 能跨完成保持，但初始化期间的 exchange() 走 HAL 阻塞模式，
   * 会把它改写掉，所以在空闲时这里必须显式重设一次。 */
  MODIFY_REG(hspi1.Instance->CR2, SPI_CR2_TSIZE, EXCHANGE_BYTES);
  last_completion = HAL_GetTick();
  drms_acq_running = 1;
  return 1;
failed:
  drms_acq_stop();
  return 0;
}

/* DRDY 下降沿中断入口：一帧数据的起点。
 *
 * 每来一次 DRDY 就占一个样本序号（即使这一帧最终丢失，序号缺口本身
 * 就是"这里丢过样"的证据，下游靠它判断连续性）。
 *
 * 若上一帧还没收完（busy 仍为 1），按丢帧计入 overruns 后直接返回；
 * 否则拉低 CS、装填 DMA、置 CSTART，等 GPDMA 完成中断收尾。 */
void drms_acq_drdy(void)
{
  if (!drms_acq_running)
    return;
  uint32_t sequence = drms_acq_edges++;
  ++sample_seq_next; /* 每个 DRDY 都占 sample_seq，丢样保留序号缺口 */
  if (busy)
  {
    ++drms_acq_overruns;
    ++capture_lost_total;
    return;
  }
  busy = 1;
  inflight_sequence = sequence;
  /* 捕获时间戳的取法。
   *
   * 它要进一次临界区再调 HAL_GetTick，实测在这个 ISR 里约 2 µs——
   * 占掉 128 kSPS 整帧预算的四分之一。
   * 高速档的时间轴本来就要靠样本序号重建（capture_time 发布的是块锚点，
   * 不是逐帧时间戳），所以那里改成每 8 帧取一次，中间复用上一个值。
   * 32 kSPS 以下预算宽松，每帧各取各的。 */
  if (drms_acq_rate < 32000u || (sequence & 7u) == 0u)
    cached_capture_us = drms_acq_now_us();
  inflight_capture_us = cached_capture_us;
#if DRMS_ACQ_TIMING_PROBE
  uint32_t t_enter = DWT->CYCCNT;
#endif
  cs(0);
#if DRMS_ACQ_TIMING_PROBE
  uint32_t t_cs = DWT->CYCCNT;
#endif
  fast_path_active = 1;
  if (fast_exchange_start() != 0)
  {
    ++drms_acq_fx_fail;
    fast_path_active = 0;
    cs(1);
    busy = 0;
    ++drms_acq_overruns;
    ++capture_lost_total;
    return;
  }
#if DRMS_ACQ_TIMING_PROBE
  uint32_t t_armed = DWT->CYCCNT;
  /* 周期数换算成微秒（核心 160 MHz，1 µs = 160 周期）。 */
  uint32_t isr_us = (t_cs - t_enter) / 160u;
  uint32_t arm_us = (t_armed - t_cs) / 160u;
  uint32_t tot_us = (t_armed - t_enter) / 160u;
  if (!drms_acq_t_n)
  {
    drms_acq_t_isr_min = drms_acq_t_arm_min = drms_acq_t_tot_min = 0xFFFFFFFFu;
  }
  if (isr_us < drms_acq_t_isr_min) drms_acq_t_isr_min = isr_us;
  if (isr_us > drms_acq_t_isr_max) drms_acq_t_isr_max = isr_us;
  drms_acq_t_isr_sum += isr_us;
  if (arm_us < drms_acq_t_arm_min) drms_acq_t_arm_min = arm_us;
  if (arm_us > drms_acq_t_arm_max) drms_acq_t_arm_max = arm_us;
  drms_acq_t_arm_sum += arm_us;
  if (tot_us < drms_acq_t_tot_min) drms_acq_t_tot_min = tot_us;
  if (tot_us > drms_acq_t_tot_max) drms_acq_t_tot_max = tot_us;
  drms_acq_t_tot_sum += tot_us;
  ++drms_acq_t_n;
#endif
}

/* 把刚完成的一帧投递到采集环，并做相应的记账。
 *
 * HAL 完成回调和快速路径共用这一个函数，保证两条路径的语义完全一致：
 * 一次 DRDY、一帧 12 字节、占用一个环槽位；环满时同样走安全停采。
 *
 * 调用约束：在中断上下文里调用，不得阻塞。 */
static void complete_frame(void)
{
  cs(1);
  if (drms_acq_running)
  {
    DRMS_RawFrame frame;
    memcpy(frame.bytes, dma_rx, sizeof(frame.bytes));
    frame.sequence = inflight_sequence;
    DRMS_Result time_status = DRMS_OK;
    if (raw_ticket_next % DRMS_CAPTURE_BLOCK_TICKS == 0 &&
        drms_fifo_count(&queue) < 4096)
      time_status = drms_capture_time_publish(raw_ticket_next, consumed_ticket,
                                              acquisition_generation, inflight_capture_us);
    if (time_status != DRMS_OK || !drms_fifo_push(&queue, &frame))
    {
      ++drms_acq_queue_drops;
      ++capture_lost_total; /* 入环失败属于捕获损失，同一采样只计一次 */
      ++unknown_loss_epoch; /* 后续 DRDY 计数停止，连续性不可证明 */
      /* 环已经收不下了，必须安全地停下——不能让 CPU 继续被困在 DMA/DRDY
       * 中断里，而监督者又消费不掉积压。
       * 置 adc_error=6 并清 running，同时立刻抑制激励。 */
      drms_acq_error = 6;
      drms_acq_running = 0;
      HAL_GPIO_WritePin(CURR_DIS_GPIO_Port, CURR_DIS_Pin, GPIO_PIN_SET);
    }
    else
      ++raw_ticket_next;
    /* 两个时间戳共用一次系统节拍读取。HAL_GetTick 要走 RTOS 定时器，
     * 而这个位置每完成一帧就执行一次，能省一次就省一次。 */
    uint32_t now_tick = HAL_GetTick();
    drms_acq_last_push_ms = now_tick;
    last_completion = now_tick;
  }
  busy = 0;
  drms_acq_boundary_service(); /* 静止时刻归结挂起的边界请求 */
}

/* HAL 的 SPI 传输完成回调。快速路径不经过这里（它自己处理 GPDMA 中断），
 * 保留它是为了 HAL 路径仍可用作对照。 */
void HAL_SPI_TxRxCpltCallback(SPI_HandleTypeDef *spi)
{
  if (spi != &hspi1)
    return;
  complete_frame();
}

/* 由 GPDMA1_Channel1_IRQHandler 在调用 HAL_DMA_IRQHandler 之前先行调用。
 *
 * 返回 1 表示这次中断属于快速路径、已经处理完毕。此时调用方**不得**再把该通道
 * 交给 HAL——HAL 的状态机里没有这次传输的记录，让它插手只会把状态搞乱。
 * 返回 0 表示不是快速路径的中断，交回 HAL 处理。 */
int drms_acq_fast_dma_irq(void)
{
  ++drms_acq_fx_irq;
  if (!fast_path_active)
    return 0;
  fast_exchange_finish();
  complete_frame();
  ++drms_acq_fx_done;
  return 1;
}

/* HAL 的 SPI 错误回调：溢出、下溢、帧错误或模式错误。
 *
 * 收到即认为本次采集不可信，立即停采并抑制激励，具体收尾留给线程上下文。 */
void HAL_SPI_ErrorCallback(SPI_HandleTypeDef *spi)
{
  if (spi != &hspi1)
    return;
  drms_acq_running = 0;
  drms_acq_error = 3;
  ++unknown_loss_epoch;
  HAL_GPIO_WritePin(CURR_DIS_GPIO_Port, CURR_DIS_Pin, GPIO_PIN_SET);
  cs(1);
  busy = 0;
  /* 这里只做"能立刻做的"：标记停止、抑制激励、拉高 CS。
   * HAL 的中止流程与模拟电源收尾放到线程上下文完成，中断里不做阻塞操作。 */
}

/* 从采集环取一帧，并带回它的捕获时间下界。
 *
 * 若该票号查不到对应的时间锚点，说明时间轴已不可信，按 adc_error=6
 * 安全停采后返回 0。
 *
 * 返回：1 取到一帧；0 环为空或已停采。 */
int drms_acq_pop_timed(DRMS_RawFrame *frame, uint64_t *capture_lower_us)
{
  if (!frame || !capture_lower_us || !queue.capacity)
    return 0;
  uint32_t mask = crit_enter();
  if (!drms_fifo_count(&queue))
  {
    crit_exit(mask);
    return 0;
  }
  if (drms_capture_time_lookup(consumed_ticket, acquisition_generation,
                               capture_lower_us) != DRMS_OK)
  {
    drms_acq_error = 6;
    drms_acq_running = 0;
    HAL_GPIO_WritePin(CURR_DIS_GPIO_Port, CURR_DIS_Pin, GPIO_PIN_SET);
    crit_exit(mask);
    return 0;
  }
  int popped = drms_fifo_pop(&queue, frame);
  if (popped)
    ++consumed_ticket;
  crit_exit(mask);
  return popped;
}

/* 取一帧但不关心捕获时间，内部转调 drms_acq_pop_timed。 */
int drms_acq_pop(DRMS_RawFrame *frame)
{
  uint64_t capture_lower_us;
  return drms_acq_pop_timed(frame, &capture_lower_us);
}

/* 采集监督：由处理线程周期性调用。
 *
 * 两个职责：
 *   1. 200 ms 没有完成过一帧 → 置 adc_error=4（数据超时）；
 *   2. 一旦有 adc_error 且模拟域仍上电 → 执行完整的停止流程。
 *
 * 中断里只负责置错误码，真正的收尾（含延时）放在这里，避免在中断里阻塞。 */
void drms_acq_poll(void)
{
  if (drms_acq_running && (uint32_t)(HAL_GetTick() - last_completion) > 200U)
    drms_acq_error = 4;
  if (drms_acq_error && powered)
    drms_acq_stop();
}

/* ---------------- 资源生命周期后端（T3/R4） ---------------- */

uint32_t drms_acq_is_quiescent(void)
{
  uint32_t mask = crit_enter();
  uint32_t quiet = !busy && !drms_acq_running && !abort_unconfirmed;
  crit_exit(mask);
  return quiet;
}

/* 资源生命周期后端的三个入口，供上层统一裁决采集资源。
 * abort：中止并确认已静止；probe：只查询是否静止；recover：从隔离态恢复。 */
static DRMS_Result acq_backend_abort(void)
{
  if (abort_unconfirmed)
    return DRMS_IO_ERROR;
  drms_acq_stop();
  return drms_acq_is_quiescent() ? DRMS_ACCEPTED : DRMS_IO_ERROR;
}

/* 只查询、不改变任何状态：静止则 ACCEPTED，否则 BUSY。 */
static DRMS_Result acq_backend_probe(void)
{
  return drms_acq_is_quiescent() ? DRMS_ACCEPTED : DRMS_BUSY;
}

/* 从隔离态恢复。
 *
 * 隔离态是"HAL_SPI_Abort 失败、无法证明传输已结束"的结果。恢复时重试一次
 * 中止：成功才清隔离标志并允许重新启动。这是有意保守的——宁可要一次显式
 * 恢复，也不要在 DMA 状态不明时贸然复用通道。
 *
 * 返回：ACCEPTED 已恢复；IO_ERROR 中止仍失败；BUSY 尚未静止。 */
static DRMS_Result acq_backend_recover(void)
{
  if (abort_unconfirmed)
  {
    if (HAL_SPI_Abort(&hspi1) != HAL_OK)
      return DRMS_IO_ERROR;
    uint32_t mask = crit_enter();
    busy = 0;
    abort_unconfirmed = 0;
    crit_exit(mask);
  }
  if (!drms_acq_is_quiescent())
    return DRMS_BUSY;
  drms_acq_error = 0;
  return DRMS_ACCEPTED;
}

static const DRMS_ResourceBackend acq_backend = {
    acq_backend_abort, acq_backend_probe, acq_backend_recover};

const DRMS_ResourceBackend *drms_acq_resource_backend(void)
{
  return &acq_backend;
}
