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
static DRMS_LogV2Meta v2_metadata;
/* CPU-only scratch. SDMMC DMA always uses staging in main SRAM. */
static uint8_t v2_config[4096] __attribute__((section(".drms_sram4_workspace")));
static DRMS_RawFrame v2_frames[256] __attribute__((section(".drms_sram4_workspace")));
static DRMS_End v2_end;
static uint32_t use_v2, v2_end_valid;
static uint32_t action, file_open, pending_records, filename_index, last_flush, segment_records;
static uint32_t incomplete;
static uint64_t log_ticket_next;
static uint64_t v2_written_total, v2_segment_first, v2_segment_last;
static uint32_t v2_sequence_known, v2_last_low, v2_segment_has_frame;
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
  use_v2 = v2_end_valid = 0;
}

uint64_t drms_log_ticket_next(void)
{
  return log_ticket_next;
}

static int reserve_start(void)
{
  uint32_t mask = __get_PRIMASK();
  __disable_irq();
  if (!drms_storage_mounted || drms_msc_blocks_recording() || drms_log_state)
  {
    __set_PRIMASK(mask);
    return 0;
  }
  __atomic_store_n(&drms_log_state, 1U, __ATOMIC_RELEASE);
  __set_PRIMASK(mask);
  return 1;
}

int drms_log_start(const DRMS_LogMetadata *request)
{
  if (!request || !reserve_start())
    return 0;
  use_v2 = v2_end_valid = 0;
  metadata = *request;
  __atomic_store_n(&action, 1U, __ATOMIC_RELEASE);
  return 1;
}

int drms_log_start_v2(const DRMS_LogV2Meta *request)
{
  if (!request || !request->record_id || !request->rate_hz ||
      request->anchor.acquisition_generation == 0 || request->anchor.rate_hz != request->rate_hz ||
      request->config_len > sizeof(v2_config) || (!!request->config != !!request->config_len) ||
      !reserve_start())
    return 0;
  v2_metadata = *request;
  if (request->config_len)
  {
    memcpy(v2_config, request->config, request->config_len);
    v2_metadata.config = v2_config;
  }
  use_v2 = 1;
  v2_end_valid = 0;
  v2_written_total = 0;
  v2_sequence_known = 1;
  v2_last_low = (uint32_t)request->anchor.sample_seq0;
  v2_segment_last = request->anchor.sample_seq0;
  v2_segment_has_frame = 0;
  __atomic_store_n(&action, 1U, __ATOMIC_RELEASE);
  return 1;
}

int drms_log_finish_v2(const DRMS_End *end)
{
  if (!end || !use_v2 || !drms_log_running || end->record_id != v2_metadata.record_id ||
      end->ring_end != log_ticket_next || end->first.generation != v2_metadata.anchor.acquisition_generation ||
      (end->end_known && end->end_exclusive.generation != end->first.generation) ||
      (!end->end_known && end->end_exclusive.index))
    return 0;
  uint32_t mask = __get_PRIMASK();
  __disable_irq();
  v2_end = *end;
  v2_end_valid = 1;
  __atomic_store_n(&action, 4U, __ATOMIC_RELEASE);
  __set_PRIMASK(mask);
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
  {
    v2_end_valid = 0; /* a later failure must never retain a previously clean END */
    __atomic_store_n(&action, 3U, __ATOMIC_RELEASE);
  }
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
  v2_segment_has_frame = 0;
  uint32_t header_size;
  if (use_v2)
  {
    DRMS_LogV2Meta segment_meta = v2_metadata;
    segment_meta.flags = (segment_meta.flags & ~12u) | 4u; /* segmented-file semantics */
    if (continuation) segment_meta.flags |= 8u;
    header_size = drms_log_v2_pack_header(staging, sizeof(staging), &segment_meta);
  }
  else
  {
    drms_log_pack_header(staging, &metadata);
    header_size = 64;
  }
  status = header_size ? fx_file_write(&file, staging, header_size) : FX_IO_ERROR;
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
  else if (request == 2 || request == 3 || request == 4)
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
  pending_records = 0;
  uint32_t output_size = 0;
  if (use_v2)
  {
    while (sizeof(staging) - output_size >= 4104u &&
           segment_records + pending_records < DRMS_LOG_SEGMENT_RECORDS)
    {
      uint32_t count = 0;
      uint32_t remaining = DRMS_LOG_SEGMENT_RECORDS - segment_records - pending_records;
      while (count < 256u && count < remaining && drms_fifo_pop(&queue, &v2_frames[count]))
      {
        uint32_t low = v2_frames[count].sequence;
        uint32_t delta = low - v2_last_low;
        if (delta >= 0x80000000u || (v2_written_total + pending_records + count && !delta))
          v2_sequence_known = 0;
        else if (v2_sequence_known)
          v2_segment_last += delta;
        v2_last_low = low;
        if (!v2_segment_has_frame)
        {
          v2_segment_first = v2_segment_last;
          v2_segment_has_frame = 1;
        }
        ++count;
      }
      if (!count) break;
      uint32_t size = drms_log_v2_pack_data(staging + output_size, sizeof(staging) - output_size,
                                            v2_frames, count);
      if (!size) { failed(FX_IO_ERROR); return; }
      output_size += size;
      pending_records += count;
    }
  }
  else
  {
    DRMS_RawFrame frame;
    while (pending_records < sizeof(staging) / 16U && drms_fifo_pop(&queue, &frame))
    {
      drms_log_pack_record(staging + pending_records * 16U, &frame);
      ++pending_records;
    }
    output_size = pending_records * 16U;
  }
  if (pending_records)
  {
    UINT status = fx_file_write(&file, staging, output_size);
    if (status != FX_SUCCESS)
    {
      failed(status);
      return;
    }
    drms_log_records += pending_records;
    segment_records += pending_records;
    if (use_v2) v2_written_total += pending_records;
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
  unsigned int rollover = use_v2 ?
      (segment_records >= DRMS_LOG_SEGMENT_RECORDS && drms_fifo_count(&queue)) :
      (drms_log_state == 2 && segment_records >= DRMS_LOG_SEGMENT_RECORDS);
  if (rollover || (drms_log_state == 3 && !drms_fifo_count(&queue)))
  {
    uint32_t was_finalizing = drms_log_state == 3;
    /* Keep the producer enabled during a rollover: its queue bridges close/open
       latency, and any full-queue loss is counted rather than silently skipped. */
    if (rollover)
      drms_log_state = 1;
    UINT status = FX_SUCCESS;
    if (use_v2 && rollover)
    {
      DRMS_End partial = {0};
      partial.record_id = v2_metadata.record_id;
      partial.first.generation = v2_metadata.anchor.acquisition_generation;
      partial.first.index = v2_sequence_known && v2_segment_has_frame ? v2_segment_first : 0;
      partial.last_confirmed_position.generation = partial.first.generation;
      partial.last_confirmed_position.index = v2_sequence_known && v2_segment_has_frame ? v2_segment_last : 0;
      partial.ring_end = v2_written_total;
      partial.unknown_loss = true;
      partial.reason = DRMS_INCOMPLETE; /* final session accounting belongs only to the last file */
      uint32_t end_size = drms_log_v2_pack_end(staging, sizeof(staging), &partial);
      status = end_size ? fx_file_write(&file, staging, end_size) : FX_IO_ERROR;
    }
    else if (use_v2 && v2_end_valid)
    {
      uint32_t end_size = drms_log_v2_pack_end(staging, sizeof(staging), &v2_end);
      status = end_size ? fx_file_write(&file, staging, end_size) : FX_IO_ERROR;
    }
    else if (!use_v2 && !incomplete)
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
    {
      if (open_file(1) && was_finalizing)
      {
        drms_log_running = 0;
        drms_log_state = 3;
      }
    }
    else
      __atomic_store_n(&drms_log_state, 0U, __ATOMIC_RELEASE);
  }
}
