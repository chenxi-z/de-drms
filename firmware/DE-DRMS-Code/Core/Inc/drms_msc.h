#ifndef DRMS_MSC_H
#define DRMS_MSC_H
/* TF 介质所有权（T4/R5/MSC 设计）。存储线程是唯一状态切换者：所有介质操作
 * （FileX flush/close、原始读、重挂载）只在 drms_msc_service() 内执行，
 * 该函数仅存储线程调用。USBX 线程经 drms_msc_read 同步提交有界读请求；
 * IRQ 上下文只允许 drms_msc_cancel（仅投递标志，不做介质操作）。
 * 所有权 = DRMS_Owner（LOCAL/EXPORTING/EXPORTED/RELEASING/QUARANTINED），
 * 健康 = DRMS_Health（ABSENT/READY/FAULT），经 drms_storage_snapshot 一致读取；
 * 旧 mounted/status 字段只是事实投影，不是第二状态源。 */
#include "drms_architecture_contract.h"

void drms_msc_init(void);

/* 任意任务上下文。ACCEPTED=已受理（存储线程稍后执行）；BUSY=转换中/已导出；
 * 前置不满足由 service 复核后回落并记录错误。 */
DRMS_Result drms_msc_request_export(void);
DRMS_Result drms_msc_request_release(void);

/* 记录入口互锁：所有权非 LOCAL 期间阻断一切新记录入口（含本机按键）。 */
uint32_t drms_msc_blocks_recording(void);

/* USBX 线程同步读：有界等待；超时后请求槽保持占用直至存储线程归结，
 * 调用方不得复用 out 缓冲。等待期间反复调用注入的等待钩子（生产=让出调度，
 * 测试=驱动 service 步进）。 */
DRMS_Result drms_msc_read(uint32_t lba, uint32_t blocks, uint8_t *out);

/* IRQ/USB 事件安全：撤销介质就绪并请求释放；不做任何介质操作。 */
void drms_msc_cancel(void);

/* 监督者入口（T7）：存储线程错过时限、无法证明在途读静止时显式隔离。
 * 隔离拒绝新请求；service 继续收敛既有清理，完成后回 LOCAL。 */
void drms_msc_mark_quarantined(void);

/* 仅存储线程。消费导出/释放请求、执行交接与在途读。 */
void drms_msc_service(void);

/* 等待钩子（由集成方在 init 后设置一次）：drms_msc_read 每轮有界等待间调用。 */
typedef void (*DRMS_MSCWaitHook)(void);
void drms_msc_set_wait_hook(DRMS_MSCWaitHook hook);

/* 只读投影（任意上下文；经短临界区）。 */
DRMS_Owner drms_msc_owner(void);
DRMS_Health drms_msc_health(void);
uint32_t drms_msc_export_generation(void);
uint32_t drms_msc_media_ready(void);              /* EXPORTED 且健康 READY */
DRMS_Result drms_msc_media_info(uint32_t *blocks); /* 容量（512B 扇区），仅就绪时有效 */
DRMS_Result drms_msc_last_error(void);

#endif /* DRMS_MSC_H */
