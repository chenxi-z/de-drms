#include "drms_acquisition.h"
#include "drms_measurement.h"
#include "drms_fifo.h"
#include "main.h"
#include "spi.h"
#include <string.h>

static DRMS_RawFrame frames[4096];
static DRMS_FIFO queue;
static uint8_t dma_rx[12] __attribute__((aligned(4)));
static uint8_t dma_tx[12] __attribute__((aligned(4)));
static volatile uint32_t busy, last_completion;
static uint32_t inflight_sequence;
static unsigned int frame_size, powered;
volatile uint32_t drms_acq_running, drms_acq_rate, drms_acq_reference;
volatile uint32_t drms_acq_last_push_ms; /* 最近帧入环时刻（过渡用；T8 换 DRDY 实测） */
volatile uint32_t drms_acq_edges, drms_acq_overruns, drms_acq_queue_drops;
volatile uint32_t drms_acq_error;

/* 64 位流记账（C1）。生产端唯一写者：DRDY ISR / DMA 完成 ISR / 启停路径。
 * 跨上下文一致读取仅在边界快照的短临界区内进行。 */
static uint64_t sample_seq_next, raw_ticket_next, capture_lost_total, unknown_loss_epoch;
static uint32_t acquisition_generation;
static struct { DRMS_Token token; uint32_t armed; } boundary_pending;
static struct { DRMS_Token token; uint32_t valid; DRMS_CaptureBoundary boundary; } boundary_reply;

static uint32_t crit_enter(void)
{
  uint32_t mask = __get_PRIMASK();
  __disable_irq();
  return mask;
}

static void crit_exit(uint32_t mask) { __set_PRIMASK(mask); }

static uint32_t token_match(DRMS_Token a, DRMS_Token b)
{
  return a.operation_id == b.operation_id && a.generation == b.generation;
}

uint32_t drms_acq_generation(void) { return acquisition_generation; }
uint64_t drms_acq_sample_seq_next(void) { return sample_seq_next; }
uint64_t drms_acq_raw_ticket_next(void) { return raw_ticket_next; }
uint64_t drms_acq_capture_lost_total(void) { return capture_lost_total; }
uint64_t drms_acq_unknown_loss_epoch(void) { return unknown_loss_epoch; }

DRMS_Result drms_acq_boundary_request(DRMS_Token token)
{
  uint32_t mask;
  if (!drms_acq_running)
    return DRMS_INVALID;
  mask = crit_enter();
  if (boundary_pending.armed)
  {
    crit_exit(mask);
    return DRMS_BUSY;
  }
  boundary_pending.token = token;
  boundary_pending.armed = 1;
  crit_exit(mask);
  return DRMS_ACCEPTED;
}

uint32_t drms_acq_queue_used(void)
{
  return drms_fifo_count(&queue);
}

void drms_acq_boundary_cancel(DRMS_Token token)
{
  uint32_t mask = crit_enter();
  if (boundary_pending.armed && token_match(boundary_pending.token, token))
    boundary_pending.armed = 0;
  if (boundary_reply.valid && token_match(boundary_reply.token, token))
    boundary_reply.valid = 0;
  crit_exit(mask);
}

void drms_acq_boundary_service(void)
{
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

static void cs(unsigned int high)
{
  HAL_GPIO_WritePin(ADS_CS_GPIO_Port, ADS_CS_Pin, high ? GPIO_PIN_SET : GPIO_PIN_RESET);
  /* Minimum CS-high time and a visible frame boundary, independent of RTOS tick. */
  for (volatile unsigned int i = 0; i < 32; ++i)
    __NOP();
}

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
  if (status != HAL_OK || rx[2] != 0)
    return 0;
  if (frame_size == 12 &&
      (rx[11] != 0 || drms_crc16(rx, 9) != (uint16_t)(((uint16_t)rx[9] << 8) | rx[10])))
    return 0;
  *response = (uint16_t)(((uint16_t)rx[0] << 8) | rx[1]);
  return 1;
}

static int command_ack(uint16_t command)
{
  uint16_t ignored, response;
  return exchange(command, &ignored) && exchange(0, &response) && response == command;
}

static int write_register(uint8_t address, uint8_t value)
{
  uint16_t ignored, response;
  if (!exchange((uint16_t)(0x4000U | ((uint16_t)address << 8) | value), &ignored))
    return 0;
  /* This write takes effect at the end of its OLD frame. */
  if (address == 0x0c)
    frame_size = 12;
  return exchange(0, &response) &&
      response == (uint16_t)(0x2000U | ((uint16_t)address << 8) | value);
}

void drms_acq_stop(void)
{
  if (drms_acq_running)
    ++unknown_loss_epoch; /* 停止后观察到的 DRDY 无法计数：连续性不可证明 */
  drms_acq_running = 0;
  HAL_GPIO_WritePin(CURR_DIS_GPIO_Port, CURR_DIS_Pin, GPIO_PIN_SET);
  (void)HAL_SPI_Abort(&hspi1);
  busy = 0;
  cs(1);
  HAL_GPIO_WritePin(ADS_RESET_GPIO_Port, ADS_RESET_Pin, GPIO_PIN_RESET);
  HAL_GPIO_WritePin(ANA_EN_GPIO_Port, ANA_EN_Pin, GPIO_PIN_RESET);
  powered = 0;
}

int drms_acq_start(uint32_t rate, unsigned int reference)
{
  uint8_t clk2;
  uint16_t ready = 0, ignored;
  if (!drms_rate_register(rate, &clk2) || reference > 1)
    return 0;
  /* HAL Size counts DATA WORDS, not bytes. Reject incompatible regeneration
     before a blocking/DMA transfer can write past a 12-byte frame buffer. */
  if (hspi1.Init.DataSize != SPI_DATASIZE_8BIT || hspi1.Init.Mode != SPI_MODE_MASTER ||
      hspi1.Init.CLKPolarity != SPI_POLARITY_LOW || hspi1.Init.CLKPhase != SPI_PHASE_2EDGE ||
      hspi1.Init.FirstBit != SPI_FIRSTBIT_MSB || hspi1.Init.NSS != SPI_NSS_SOFT)
  {
    drms_acq_stop();
    drms_acq_error = 2;
    return 0;
  }
  drms_acq_stop();
  drms_acq_error = 0;
  drms_acq_edges = drms_acq_overruns = drms_acq_queue_drops = 0;
  /* 新采集代次：流计数清零，边界请求/回复一并作废（旧代次边界不得交付）。 */
  sample_seq_next = raw_ticket_next = capture_lost_total = unknown_loss_epoch = 0;
  ++acquisition_generation;
  boundary_pending.armed = 0;
  boundary_reply.valid = 0;
  (void)drms_fifo_init(&queue, frames, 4096, sizeof(frames[0]));
  /* Inhibit first. Never pass through forbidden SENSE=0,K2=1, even briefly. */
  if (reference)
  {
    HAL_GPIO_WritePin(SEL_SENSE_GPIO_Port, SEL_SENSE_Pin, GPIO_PIN_SET);
    HAL_GPIO_WritePin(SEL_K2_GPIO_Port, SEL_K2_Pin, GPIO_PIN_SET);
  }
  else
  {
    HAL_GPIO_WritePin(SEL_K2_GPIO_Port, SEL_K2_Pin, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(SEL_SENSE_GPIO_Port, SEL_SENSE_Pin, GPIO_PIN_RESET);
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
  /* SBAS590E §9.6 and §10.4. VNCP tied to AVSS: VNCPEN must remain 0.
     A_SYS_CFG=0x68: high resolution, reserved bit5=1, 2.442 V internal ref.
     CLK1=0x02: /2; CLK2=0x2n: /2 and selected OSR.
     D_SYS_CFG=0x7f: CRC over ALL preceding bytes, fixed four-word frame. */
  /* Enable fixed-frame CRC first, before any analog/reference register write. */
  if (!command_ack(0x0655) || !write_register(0x0c, 0x7f) ||
      !write_register(0x0b, 0x68) || !write_register(0x0d, 0x02) || !write_register(0x0e, clk2) ||
      !write_register(0x0f, 0x0f) ||
      !command_ack(0x0033) || !command_ack(0x0555))
  {
    drms_acq_error = 2;
    goto failed;
  }
  HAL_GPIO_WritePin(CURR_DIS_GPIO_Port, CURR_DIS_Pin, GPIO_PIN_RESET);
  /* Conservative first-board settling, including sinc3 and analog recovery.
     No samples acquired during this interval are labelled valid. */
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
  last_completion = HAL_GetTick();
  drms_acq_running = 1;
  return 1;
failed:
  drms_acq_stop();
  return 0;
}

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
  cs(0);
  if (HAL_SPI_TransmitReceive_DMA(&hspi1, dma_tx, dma_rx, sizeof(dma_rx)) != HAL_OK)
  {
    cs(1);
    busy = 0;
    ++drms_acq_overruns;
    ++capture_lost_total;
  }
}

void HAL_SPI_TxRxCpltCallback(SPI_HandleTypeDef *spi)
{
  if (spi != &hspi1)
    return;
  cs(1);
  if (drms_acq_running)
  {
    DRMS_RawFrame frame;
    memcpy(frame.bytes, dma_rx, sizeof(frame.bytes));
    frame.sequence = inflight_sequence;
    if (!drms_fifo_push(&queue, &frame))
    {
      ++drms_acq_queue_drops;
      ++capture_lost_total; /* 入环失败属于捕获损失，同一采样只计一次 */
      ++unknown_loss_epoch; /* 后续 DRDY 计数停止，连续性不可证明 */
      /* An unverified high rate must fail safely, not keep the CPU trapped in
         DMA/DRDY IRQs while the supervisor can no longer consume its queue. */
      drms_acq_error = 6;
      drms_acq_running = 0;
      HAL_GPIO_WritePin(CURR_DIS_GPIO_Port, CURR_DIS_Pin, GPIO_PIN_SET);
    }
    else
      ++raw_ticket_next;
    drms_acq_last_push_ms = HAL_GetTick();
    last_completion = HAL_GetTick();
  }
  busy = 0;
  drms_acq_boundary_service(); /* 静止时刻归结挂起的边界请求 */
}

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
  /* Supervisor completes the HAL abort and analog shutdown in thread context. */
}

int drms_acq_pop(DRMS_RawFrame *frame)
{
  return queue.capacity ? drms_fifo_pop(&queue, frame) : 0;
}

void drms_acq_poll(void)
{
  if (drms_acq_running && (uint32_t)(HAL_GetTick() - last_completion) > 200U)
    drms_acq_error = 4;
  if (drms_acq_error && powered)
    drms_acq_stop();
}

/* ---------------- 资源生命周期后端（T3/R4） ---------------- */

static DRMS_Result acq_backend_abort(void)
{
  if (!drms_acq_running && !busy)
    return DRMS_ACCEPTED; /* 已静止：无在途 DMA，回调不会再使用旧缓冲 */
  /* 安全动作优先：先抑制激励，再有界中止传输（HAL_Abort 同步返回）。 */
  HAL_GPIO_WritePin(CURR_DIS_GPIO_Port, CURR_DIS_Pin, GPIO_PIN_SET);
  if (drms_acq_running)
    ++unknown_loss_epoch; /* 中止后观察到的 DRDY 无法计数 */
  drms_acq_running = 0;
  HAL_StatusTypeDef status = HAL_SPI_Abort(&hspi1);
  busy = 0;
  cs(1);
  return (status == HAL_OK) ? DRMS_ACCEPTED : DRMS_IO_ERROR;
}

static DRMS_Result acq_backend_probe(void)
{
  return (!busy && !drms_acq_running) ? DRMS_ACCEPTED : DRMS_BUSY;
}

static DRMS_Result acq_backend_recover(void)
{
  /* 清除错误闩锁；重新建立采集走 acq_start（新代次、计数清零）。 */
  drms_acq_error = 0;
  return DRMS_ACCEPTED;
}

static const DRMS_ResourceBackend acq_backend = {
    acq_backend_abort, acq_backend_probe, acq_backend_recover};

const DRMS_ResourceBackend *drms_acq_resource_backend(void)
{
  return &acq_backend;
}
