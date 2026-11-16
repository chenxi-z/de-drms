#ifndef DRMS_RAW_STREAM_H
#define DRMS_RAW_STREAM_H
#include <stddef.h>
#include <stdint.h>

/* RAW 实时流（SUBSCRIBE stream=RAW，period_ms=0）的攒批状态机。
 *
 * 协议依据：shared/protocol/de-drms-cdc-v2.json 的 RAW_EVENT（opcode 131）——
 * "RAW data 为同一代次连续的 16 字节记录；缺口或换代另起帧"，
 * "lost 为本次订阅累计未交付条目数（曲线点或原始帧）"。
 *
 * 设计要点（与本仓架构约束的对应关系）：
 *   · 生产者是应用处理线程（drms_application 的 drain_frames 逐帧喂入），
 *     USB 不是采集环的第二消费者——这里只是处理路径上的一个镜像汇。
 *   · 消费者是 CDC 发送线程（drms_cdc_v2_publish_raw → publish）。
 *   · 订阅控制来自 CDC 接收线程（SUBSCRIBE/UNSUBSCRIBE/断线）。
 *   · 缓冲全部在 SRAM4（.drms_sram4_workspace）：主 RAM 门禁只剩 16 B，
 *     任何新增静态分配都必须去 SRAM4。USB 发送走 CPU 拷贝，无 DMA 约束。
 *
 * 攒批模型（"随来随走"）：
 *   · 一批 = DRMS_RAW_BATCH_FRAMES 帧（60×16 B = 960 B，顶满协议载荷上限
 *     1024 B 减去 RAW_EVENT 全部必填字段的 TLV 开销）；
 *   · 4 kSPS 下每 15 ms 攒满即发，发送期间下一批继续攒，流水无空转；
 *   · 采集代次变化立即冲刷当前批（批不跨代次）；
 *   · 批完成时邮箱（单槽）空闲则指针交换、零拷贝交接；邮箱被上一批占住
 *     （发送慢/主机停收）则整批丢弃并计 lost——实时流的旧数据没有等待价值，
 *     客户端用帧内 32 位序号与 lost 检测缺口。
 *
 * 线程安全：
 *   · 生产者独占"活动槽"的填充区，逐帧只做原子读 subscribed；
 *   · 邮箱状态/lost/epoch 的变更都在 PRIMASK 短临界区内；
 *   · 消费者取批置 HELD，用完置 EMPTY；订阅重建只清 FULL（HELD 由持有者收尾），
 *     epoch 变化让在途编码作废，避免旧订阅漏帧。 */
#define DRMS_RAW_BATCH_FRAMES 60u
#define DRMS_RAW_FRAME_BYTES  16u
/* 订阅时的速率档上限（FS bulk + 10 ms 发送节拍实测约束，4 kSPS≈70 kB/s）。
 * 超档位订阅被拒绝；订阅后换到更高档位不自动退订，超预算的批会丢弃并计 lost。 */
#define DRMS_RAW_RATE_CAP 16000u

/* 订阅。rate_hz 为当前采集速率（0 或超 DRMS_RAW_RATE_CAP 拒绝）。
 * 返回实际批周期（毫秒，向上取整），拒绝返回 0（映射 INVALID）。 */
uint32_t drms_raw_stream_subscribe(uint32_t rate_hz);

/* 撤销订阅（UNSUBSCRIBE 与断线共用）。未发出的完整批直接作废。 */
void drms_raw_stream_unsubscribe(void);

uint32_t drms_raw_stream_active(void);
uint64_t drms_raw_stream_lost(void);
uint32_t drms_raw_stream_period_ms(void);

/* 上电初始化。SRAM4 是 NOLOAD 区，不依赖零初始化，必须显式调用一次。 */
void drms_raw_stream_reset(void);

/* 生产者：镜像一帧原始记录（16 B，BIN v2 帧布局：12 B ADC + u32 序号）。
 * generation/sequence 用于批首的 sample_generation/sample_index 字段与换代冲刷。
 * 订阅未激活时立即返回。 */
void drms_raw_stream_feed(uint32_t generation, uint32_t sequence, uint32_t rate_hz,
                          const void *frame);

/* 消费者：取走就绪的一批，补齐会话号/流内序号/lost/CRC 后编码为完整线上帧
 * （COBS + 定界符）并经 send 发出。返回本批帧数（0 = 无批或未投递）。
 * send 返回 0 视为未投递并计入 lost。wire 缓冲容量须 ≥1046 B。 */
unsigned drms_raw_stream_publish(uint32_t session,
                                 int (*send)(void *context, const uint8_t *data,
                                             size_t size, uint32_t priority),
                                 void *send_context,
                                 int (*can_send)(void *context, uint32_t priority),
                                 void *cansend_context);
#endif
