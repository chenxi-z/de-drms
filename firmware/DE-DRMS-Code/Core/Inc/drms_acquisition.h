#ifndef DRMS_ACQUISITION_H
#define DRMS_ACQUISITION_H
#include <stdint.h>
#include "drms_architecture_contract.h"
#include "drms_resource_lifecycle.h"

typedef struct {
  uint8_t bytes[12];
  uint32_t sequence;
} DRMS_RawFrame;

/* Supervisor owns start/stop/pop/poll. EXTI/SPI callbacks only enqueue frames. */
int drms_acq_start(uint32_t rate, unsigned int reference);
void drms_acq_stop(void);
uint32_t drms_acq_is_quiescent(void);
void drms_acq_poll(void);
void drms_acq_drdy(void);
/* Called first from GPDMA1_Channel1_IRQHandler. Returns non-zero when the
 * acquisition fast path owned this transfer and already completed it, in which
 * case the caller must not also run HAL_DMA_IRQHandler on that channel. */
int drms_acq_fast_dma_irq(void);
int drms_acq_pop(DRMS_RawFrame *frame);
int drms_acq_pop_timed(DRMS_RawFrame *frame, uint64_t *capture_lower_us);
uint64_t drms_acq_now_us(void);
extern volatile uint32_t drms_acq_running, drms_acq_rate, drms_acq_reference;
extern volatile uint32_t drms_acq_edges, drms_acq_overruns, drms_acq_queue_drops;
extern volatile uint32_t drms_acq_last_push_ms;
extern volatile uint32_t drms_acq_error;

/* 一致边界（C1/T2a）。采集模块串行执行边界请求：service 只在无在途 DMA 的
 * 静止时刻快照（等待发生在临界区外，不屏蔽中断等 DMA）；快照包含代次与
 * 全部损失计数，边界前观察到的 DRDY 已归结为已发布帧或明确损失。 */
DRMS_Result drms_acq_boundary_request(DRMS_Token token);
void drms_acq_boundary_cancel(DRMS_Token token);
uint32_t drms_acq_queue_used(void);
void drms_acq_boundary_service(void); /* 静止时刻调用；DMA 完成路径亦调用 */
DRMS_Result drms_acq_boundary_get(DRMS_Token token, DRMS_CaptureBoundary *out);

/* 64 位流计数（生产端唯一写者；跨上下文读取仅用于监督/快照）。 */
uint32_t drms_acq_generation(void);
uint64_t drms_acq_sample_seq_next(void); /* 观察到的 DRDY 总数（丢样占号） */
uint64_t drms_acq_raw_ticket_next(void); /* 成功发布到原始环的帧总数 */
uint64_t drms_acq_capture_lost_total(void);
uint64_t drms_acq_unknown_loss_epoch(void);

/* 资源生命周期后端（T3/R4）：abort = 先抑制激励再有界中止 SPI 传输；
 * 静止证据 = 无在途 DMA 且采集已停止（HAL_Abort 返回后完成回调不再触碰
 * 旧缓冲）；recover = 清除错误闩锁，重新启动由 acq_start 建立新代次。 */
const DRMS_ResourceBackend *drms_acq_resource_backend(void);
#endif
