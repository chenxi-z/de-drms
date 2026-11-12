/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file    app_filex.c
  * @author  MCD Application Team
  * @brief   FileX applicative file
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */

/* Includes ------------------------------------------------------------------*/
#include "app_filex.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "drms_storage.h"
#include "drms_logging.h"
#include "drms_power.h"
#include "drms_msc.h"
#include "drms_file_backend.h"
#include "drms_file_service.h"

/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* Main thread stack size */
#define FX_APP_THREAD_STACK_SIZE         1024*2
/* Main thread priority */
#define FX_APP_THREAD_PRIO               10
/* USER CODE BEGIN PD */
#undef FX_APP_THREAD_STACK_SIZE
#define FX_APP_THREAD_STACK_SIZE (4U * 1024U)

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
/* Main thread global data structures.  */
TX_THREAD       fx_app_thread;

/* Buffer for FileX FX_MEDIA sector cache.
 *
 * 2026-11-12：从 1 个扇区（512 B）加大到 16 KiB（32 扇区）。
 *
 * 动机是把一次大块写摊到更多扇区上一并提交，减少单扇区往返。
 * **实测结论要如实记录：这一改动没有解决记录吞吐问题。**
 * 在 64 kSPS 场景下，把缓存从 512 B 加到 16 KiB 后，
 * 实测记录吞吐仍在 ~90-160 KB/s 量级，没有数量级改善。
 * 也就是说瓶颈不在 FileX 的缓存大小，而在更下层（SD 传输或
 * 每轮 poll 的固定开销），尚未定位。详见 README 的"待查"一节。
 *
 * 保留这个改动的理由：更大的缓存对多扇区写本身是无害且合理的，
 * 且 16 KiB 在 786 KB SRAM 里占比很小。但**不要**把它当成
 * 64 kSPS 记录问题的修复。 */
#define DRMS_MEDIA_CACHE_SECTORS 32u
ALIGN_32BYTES (uint32_t fx_sd_media_memory[DRMS_MEDIA_CACHE_SECTORS * FX_STM32_SD_DEFAULT_SECTOR_SIZE / sizeof(uint32_t)]);
/* Define FileX global data structures.  */
FX_MEDIA        sdio_disk;

/* USER CODE BEGIN PV */

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/

/* Main thread entry function.  */
void fx_app_thread_entry(ULONG thread_input);

/* USER CODE BEGIN PFP */
static void drms_msc_wait(void) { tx_thread_sleep(1); }
/* USER CODE END PFP */

/**
  * @brief  Application FileX Initialization.
  * @param memory_ptr: memory pointer
  * @retval int
*/
UINT MX_FileX_Init(VOID *memory_ptr)
{
  UINT ret = FX_SUCCESS;
  TX_BYTE_POOL *byte_pool = (TX_BYTE_POOL*)memory_ptr;
  VOID *pointer;

/* USER CODE BEGIN MX_FileX_MEM_POOL */

/* USER CODE END MX_FileX_MEM_POOL */

/* USER CODE BEGIN 0 */

/* USER CODE END 0 */

/*Allocate memory for the main thread's stack*/
  ret = tx_byte_allocate(byte_pool, &pointer, FX_APP_THREAD_STACK_SIZE, TX_NO_WAIT);

/* Check FX_APP_THREAD_STACK_SIZE allocation*/
  if (ret != FX_SUCCESS)
  {
    return TX_POOL_ERROR;
  }

/* Create the main thread.  */
  ret = tx_thread_create(&fx_app_thread, FX_APP_THREAD_NAME, fx_app_thread_entry, 0, pointer, FX_APP_THREAD_STACK_SIZE,
                         FX_APP_THREAD_PRIO, FX_APP_PREEMPTION_THRESHOLD, FX_APP_THREAD_TIME_SLICE, FX_APP_THREAD_AUTO_START);

/* Check main thread creation */
  if (ret != FX_SUCCESS)
  {
    return TX_THREAD_ERROR;
  }

/* USER CODE BEGIN MX_FileX_Init */

/* USER CODE END MX_FileX_Init */

/* Initialize FileX.  */
  fx_system_initialize();

/* USER CODE BEGIN MX_FileX_Init 1*/

/* USER CODE END MX_FileX_Init 1*/

  return ret;
}

/**
 * @brief  Main thread entry.
 * @param thread_input: ULONG user argument used by the thread entry
 * @retval none
*/
 void fx_app_thread_entry(ULONG thread_input)
 {

  UINT sd_status = FX_SUCCESS;

/* USER CODE BEGIN fx_app_thread_entry 0*/
  TX_PARAMETER_NOT_USED(thread_input);
  drms_storage_init();
  drms_log_init();
  drms_file_backend_init();
  drms_file_service_init();
  drms_msc_init();
  drms_msc_set_wait_hook(drms_msc_wait);
  ULONG last_attempt = tx_time_get() - TX_TIMER_TICKS_PER_SECOND;
  for (;;)
  {
    ULONG now = tx_time_get();
    drms_storage_observe();
    if (drms_shutdown_requested)
    {
      drms_msc_cancel();
      drms_file_service_cancel_all();
    }
    drms_msc_service();
    drms_file_service_poll();
    if (drms_shutdown_requested)
    {
      if (drms_storage_mounted)
      {
        drms_storage_poll();
        if (drms_storage_mounted)
          drms_log_poll();
      }
      if (drms_file_service_quiescent())
        (void)drms_storage_prepare_shutdown();
      tx_thread_sleep(1);
      continue;
    }
    drms_storage_shutdown_ready = 0;
    if (drms_storage_mounted || (ULONG)(now - last_attempt) >= TX_TIMER_TICKS_PER_SECOND)
    {
      drms_storage_poll();
      last_attempt = now;
    }
    if (drms_storage_mounted)
      drms_log_poll();
    /* Ten millisecond service cadence, but one second mount retry backoff. */
    tx_thread_sleep(1);
  }
  /* The generated one-shot sample below is intentionally unreachable. */

/* USER CODE END fx_app_thread_entry 0*/

/* Open the SD disk driver */
  sd_status =  fx_media_open(&sdio_disk, FX_SD_VOLUME_NAME, fx_stm32_sd_driver, (VOID *)FX_NULL, (VOID *) fx_sd_media_memory, sizeof(fx_sd_media_memory));

/* Check the media open sd_status */
  if (sd_status != FX_SUCCESS)
  {
     /* USER CODE BEGIN SD DRIVER get info error */
    return;
    /* USER CODE END SD DRIVER get info error */
  }

/* USER CODE BEGIN fx_app_thread_entry 1*/

/* USER CODE END fx_app_thread_entry 1*/
  }

/* USER CODE BEGIN 1 */

/* USER CODE END 1 */
