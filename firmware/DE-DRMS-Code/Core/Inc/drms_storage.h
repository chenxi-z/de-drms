#ifndef DRMS_STORAGE_H
#define DRMS_STORAGE_H
#include "drms_architecture_contract.h"

/* FileX thread exclusively owns the medium and its lifecycle. */
void drms_storage_init(void);
void drms_storage_poll(void);
/* FileX owner only: abort dirty media, release the HAL driver, allow remount. */
void drms_storage_invalidate(void);
int drms_storage_prepare_shutdown(void);
extern volatile unsigned int drms_storage_mounted;
extern volatile unsigned int drms_storage_status;

/* ---- T4 双轴与原始读（仅存储线程调用，除 snapshot 只读） ---- */
/* 所有权/健康一致快照：所有权来自介质交接状态机，健康由卡在位与挂载事实
 * 单源推导（mounted/status 为其投影，不是第二状态源）。任意上下文可读。 */
void drms_storage_snapshot(DRMS_Owner *owner, DRMS_Health *health);
/* 挂载成功时缓存的卡容量（512B 扇区）；0 = 未知。 */
uint32_t drms_storage_capacity_sectors(void);
/* 导出期初始化原始 SD 访问（FileX 已关闭、驱动已释放后调用一次）。 */
void drms_storage_begin_raw_access(void);
/* 原始扇区读（导出期由 drms_msc_service 调用；与 FileX 共用同一 SD 驱动入口，
 * 二者绝不并发：交接由所有权状态机保证）。 */
DRMS_Result drms_storage_raw_read(uint32_t lba, uint32_t blocks, uint8_t *out);
/* 释放 SD 驱动（复位私有状态，允许重挂载）；FileX 已关闭后由交接流程调用。 */
void drms_storage_release_driver(void);
/* 卡在位事实（CD 引脚）。 */
uint32_t drms_storage_card_present(void);

#endif
