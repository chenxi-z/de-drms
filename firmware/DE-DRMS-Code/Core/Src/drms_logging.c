#include "drms_logging.h"
#include "drms_log_codec.h"
#include "drms_fifo.h"
#include "drms_storage.h"
#include "drms_msc.h"
#include "app_filex.h"
#include "main.h"
#include <stdio.h>
#include <string.h>

#ifndef DRMS_LOG_SEGMENT_RECORDS
#define DRMS_LOG_SEGMENT_RECORDS ((1024U * 1024U * 1024U - 128U) / 16U)
#endif
extern FX_MEDIA sdio_disk;
static FX_FILE file;
static DRMS_RawFrame records[32768];
static DRMS_FIFO queue;
static uint8_t staging[32768] __attribute__((aligned(32)));
static DRMS_LogMetadata metadata;
static uint32_t action, file_open, pending_records, filename_index, last_flush, segment_records;
static uint32_t incomplete;
static uint64_t log_ticket_next;
volatile uint32_t drms_log_running, drms_log_state, drms_log_status;
volatile uint32_t drms_log_records, drms_log_dropped;
char drms_log_filename[16];

void drms_log_init(void)
{
  (void)drms_fifo_init(&queue, records, 32768, sizeof(records[0]));
  drms_log_running = drms_log_state = action = file_open = 0;
  drms_log_records = drms_log_dropped = pending_records = 0;
  log_ticket_next = 0;
  incomplete = 0;
}

uint64_t drms_log_ticket_next(void)
{
  return log_ticket_next;
}

int drms_log_start(const DRMS_LogMetadata *request)
{
  if (!request)
    return 0;
  uint32_t mask = __get_PRIMASK();
  __disable_irq();
  if (!drms_storage_mounted || drms_msc_blocks_recording() || drms_log_state)
  {
    __set_PRIMASK(mask);
    return 0;
  }
  __atomic_store_n(&drms_log_state, 1U, __ATOMIC_RELEASE);
  __set_PRIMASK(mask);
  metadata = *request;
  __atomic_store_n(&action, 1U, __ATOMIC_RELEASE);
  return 1;
}

void drms_log_stop(void)
{
  if (drms_log_state)
  {
    uint32_t pending = __atomic_load_n(&action, __ATOMIC_ACQUIRE);
    while (pending != 3U &&
           !__atomic_compare_exchange_n(&action, &pending, 2U, 0,
                                        __ATOMIC_RELEASE, __ATOMIC_ACQUIRE))
      ;
  }
}

void drms_log_stop_incomplete(void)
{
  if (drms_log_state)
    __atomic_store_n(&action, 3U, __ATOMIC_RELEASE);
}

int drms_log_enqueue(const DRMS_RawFrame *frame)
{
  if (!drms_log_running || !drms_fifo_push(&queue, frame))
  {
    /* 全局诊断计数保留；会话级 log_dropped 由处理端按返回值另计（C1）。 */
    (void)__atomic_add_fetch(&drms_log_dropped, 1U, __ATOMIC_RELAXED);
    return 0;
  }
  ++log_ticket_next;
  return 1;
}

void drms_log_removed(void)
{
  drms_log_running = 0;
  drms_log_status = FX_IO_ERROR;
  (void)__atomic_add_fetch(&drms_log_dropped, drms_fifo_count(&queue) + pending_records, __ATOMIC_RELAXED);
  /* Producer is the higher-priority main thread and now sees running=0. */
  (void)drms_fifo_init(&queue, records, 32768, sizeof(records[0]));
  pending_records = file_open = 0;
  log_ticket_next = 0;
  memset(&file, 0, sizeof(file));
  __atomic_store_n(&action, 0U, __ATOMIC_RELEASE);
  __atomic_store_n(&drms_log_state, 0U, __ATOMIC_RELEASE);
}

static void failed(UINT status)
{
  /* Discard the media's dirty state after I/O failure instead of repeatedly
     issuing writes to a broken card. Storage will reinitialize on retry. */
  drms_log_running = 0;
  drms_storage_invalidate();
  drms_log_status = status;
}

static int open_file(unsigned int continuation)
{
  UINT status = FX_ALREADY_CREATED;
  for (; filename_index < 10000 && status == FX_ALREADY_CREATED; ++filename_index)
  {
    (void)snprintf(drms_log_filename, sizeof(drms_log_filename), "DRMS%04u.BIN", (unsigned int)(filename_index % 10000U));
    status = fx_file_create(&sdio_disk, drms_log_filename);
  }
  if (status != FX_SUCCESS)
  {
    failed(status);
    return 0;
  }
  memset(&file, 0, sizeof(file));
  status = fx_file_open(&sdio_disk, &file, drms_log_filename, FX_OPEN_FOR_WRITE);
  if (status != FX_SUCCESS)
  {
    failed(status);
    return 0;
  }
  file_open = 1;
  if (!continuation)
  {
    incomplete = 0;
    (void)drms_fifo_init(&queue, records, 32768, sizeof(records[0]));
    pending_records = drms_log_records = drms_log_dropped = 0;
    log_ticket_next = 0;
  }
  segment_records = 0;
  drms_log_pack_header(staging, &metadata);
  status = fx_file_write(&file, staging, 64);
  if (status != FX_SUCCESS)
  {
    failed(status);
    return 0;
  }
  last_flush = HAL_GetTick();
  drms_log_status = FX_SUCCESS;
  drms_log_state = 2;
  drms_log_running = 1;
  return 1;
}

void drms_log_poll(void)
{
  uint32_t request = __atomic_exchange_n(&action, 0U, __ATOMIC_ACQ_REL);
  if (request == 1)
  {
    if (!drms_storage_mounted)
    {
      drms_log_removed();
      return;
    }
    if (!open_file(0))
      return;
  }
  else if (request == 2 || request == 3)
  {
    if (request == 3)
      incomplete = 1;
    drms_log_running = 0;
    drms_log_state = 3;
    if (!file_open)
    {
      drms_log_state = 0;
      return;
    }
  }
  if (!file_open || !drms_storage_mounted)
    return;
  /* Batch up to 32 KiB. SPSC samples are copied before releasing their slots. */
  DRMS_RawFrame frame;
  pending_records = 0;
  while (pending_records < sizeof(staging) / 16U && drms_fifo_pop(&queue, &frame))
  {
    drms_log_pack_record(staging + pending_records * 16U, &frame);
    ++pending_records;
  }
  if (pending_records)
  {
    UINT status = fx_file_write(&file, staging, pending_records * 16U);
    if (status != FX_SUCCESS)
    {
      failed(status);
      return;
    }
    drms_log_records += pending_records;
    segment_records += pending_records;
    pending_records = 0;
  }
  if (drms_log_state == 2 && (uint32_t)(HAL_GetTick() - last_flush) >= 1000U)
  {
    UINT status = fx_media_flush(&sdio_disk);
    if (status != FX_SUCCESS)
    {
      failed(status);
      return;
    }
    last_flush = HAL_GetTick();
  }
  unsigned int rollover = drms_log_state == 2 && segment_records >= DRMS_LOG_SEGMENT_RECORDS;
  if (rollover || (drms_log_state == 3 && !drms_fifo_count(&queue)))
  {
    /* Keep the producer enabled during a rollover: its queue bridges close/open
       latency, and any full-queue loss is counted rather than silently skipped. */
    if (rollover)
      drms_log_state = 1;
    UINT status = FX_SUCCESS;
    if (!incomplete)
    {
      drms_log_pack_footer(staging, segment_records, drms_log_dropped,
                           drms_acq_overruns, drms_acq_queue_drops, HAL_GetTick());
      status = fx_file_write(&file, staging, 64);
    }
    if (status == FX_SUCCESS)
      status = fx_file_close(&file);
    if (status == FX_SUCCESS)
      status = fx_media_flush(&sdio_disk);
    if (status != FX_SUCCESS)
    {
      failed(status);
      return;
    }
    file_open = 0;
    drms_log_status = FX_SUCCESS;
    if (rollover)
      (void)open_file(1);
    else
      __atomic_store_n(&drms_log_state, 0U, __ATOMIC_RELEASE);
  }
}
