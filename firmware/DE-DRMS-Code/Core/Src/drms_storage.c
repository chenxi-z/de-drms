#include "drms_storage.h"
#include "drms_logging.h"
#include "drms_power.h"
#include "drms_msc.h"
#include "app_filex.h"
#include "main.h"

extern FX_MEDIA sdio_disk;
extern uint32_t fx_sd_media_memory[128];
volatile unsigned int drms_storage_mounted;
volatile unsigned int drms_storage_status = FX_IO_ERROR;
static uint32_t capacity_cache; /* 导出容量缓存（挂载成功时刷新） */

void drms_storage_init(void)
{
  drms_storage_mounted = 0;
  drms_storage_status = FX_IO_ERROR;
}

static void release_driver(void)
{
  /* This also resets the ST driver's private initialization latch and deletes
     its DMA semaphores. A removed card must not prevent this request. */
  sdio_disk.fx_media_driver_request = FX_DRIVER_UNINIT;
  fx_stm32_sd_driver(&sdio_disk);
}

void drms_storage_invalidate(void)
{
  if (drms_storage_mounted)
  {
    drms_storage_mounted = 0;
    (void)fx_media_abort(&sdio_disk);
    release_driver();
  }
  capacity_cache = 0;
  drms_log_removed();
  drms_storage_status = FX_IO_ERROR;
}

int drms_storage_prepare_shutdown(void)
{
  if (drms_log_state || drms_msc_owner() != DRMS_OWNER_LOCAL)
    return 0;
  if (drms_storage_mounted)
  {
    UINT status = fx_media_flush(&sdio_disk);
    if (status == FX_SUCCESS)
      status = fx_media_close(&sdio_disk);
    if (status != FX_SUCCESS)
    {
      drms_storage_invalidate();
      drms_storage_status = status;
    }
    else
    {
      drms_storage_mounted = 0;
      drms_storage_status = FX_SUCCESS;
    }
  }
  drms_storage_shutdown_ready = 1;
  return 1;
}

void drms_storage_poll(void)
{
  if (drms_msc_owner() != DRMS_OWNER_LOCAL)
    return;
  if (HAL_GPIO_ReadPin(SD_CD_GPIO_Port, SD_CD_Pin) != GPIO_PIN_RESET)
  {
    if (drms_storage_mounted)
    {
      /* No writes after physical removal. Dirty data may be lost. */
      drms_storage_invalidate();
    }
    drms_storage_status = FX_IO_ERROR;
    return;
  }
  if (!drms_storage_mounted)
  {
    drms_storage_status = fx_media_open(&sdio_disk, FX_SD_VOLUME_NAME,
        fx_stm32_sd_driver, FX_NULL, fx_sd_media_memory, sizeof(fx_sd_media_memory));
    if (drms_storage_status == FX_SUCCESS)
    {
      drms_storage_mounted = 1;
      /* 导出容量以当前卡为准；换卡/重挂载后刷新，不得沿用旧容量。 */
      capacity_cache = (uint32_t)sdio_disk.fx_media_total_sectors;
    }
    else
      release_driver();
  }
}

/* ---------------- T4：所有权双轴与原始读 ---------------- */
/* 所有权来源 = drms_msc（介质交接状态机，存储线程唯一写者）；
 * 健康由本文件事实单源推导：卡不在位 → ABSENT；在位但未挂载 → FAULT 或
 * ABSENT（按最近事实）；挂载成功 → READY。旧 mounted/status 继续表达
 * FileX 事实，供既有投影（STATUS 文本）使用，不承担第二状态源。 */
uint32_t drms_storage_capacity_sectors(void)
{
  return capacity_cache;
}

uint32_t drms_storage_card_present(void)
{
  return HAL_GPIO_ReadPin(SD_CD_GPIO_Port, SD_CD_Pin) == GPIO_PIN_RESET;
}

void drms_storage_release_driver(void)
{
  release_driver();
}

/* 导出期初始化原始 SD 访问（FileX 已关闭、驱动已释放）。 */
DRMS_Result drms_storage_begin_raw_access(void)
{
  sdio_disk.fx_media_driver_request = FX_DRIVER_INIT;
  sdio_disk.fx_media_driver_status = FX_IO_ERROR; /* 驱动写回真实结果 */
  fx_stm32_sd_driver(&sdio_disk);
  return sdio_disk.fx_media_driver_status == FX_SUCCESS ? DRMS_OK : DRMS_IO_ERROR;
}

DRMS_Result drms_storage_raw_read(uint32_t lba, uint32_t blocks, uint8_t *out)
{
  if (!drms_storage_card_present())
    return DRMS_IO_ERROR;
  sdio_disk.fx_media_driver_request = FX_DRIVER_READ;
  sdio_disk.fx_media_driver_logical_sector = lba;
  sdio_disk.fx_media_driver_sectors = blocks;
  sdio_disk.fx_media_driver_buffer = out;
  fx_stm32_sd_driver(&sdio_disk);
  if (sdio_disk.fx_media_driver_status != FX_SUCCESS)
    return DRMS_IO_ERROR;
  return DRMS_OK;
}

void drms_storage_snapshot(DRMS_Owner *owner, DRMS_Health *health)
{
  DRMS_Owner local_owner = drms_msc_owner();
  DRMS_Health local_health;
  uint32_t present = drms_storage_card_present();
  if (!present)
    local_health = DRMS_HEALTH_ABSENT;
  else if ((drms_storage_mounted && drms_storage_status == FX_SUCCESS) ||
           capacity_cache)
    local_health = DRMS_HEALTH_READY; /* 已获知卡容量（含导出期 FileX 关闭） */
  else
    local_health = DRMS_HEALTH_FAULT;
  if (owner)
    *owner = local_owner;
  if (health)
    *health = local_health;
}
