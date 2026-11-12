/*****************************************************************************
 * 文件：drms_logging.c
 * 职责：把采集到的原始帧写成记录文件——记录环、分批写入、换文件、收尾。
 *
 * 在整机中的位置：
 *   应用线程 → drms_log_enqueue（只入环，很快）→ 记录环(32768 帧)
 *              ↓
 *           本模块的 drms_log_poll（在 FileX 线程里跑）→ 组装成块 → 写卡
 *
 * 为什么分成两段：
 *   写卡是毫秒级的操作，绝不能在采集路径上做。所以入环是"生产者"、
 *   写卡是"消费者"，两者用无锁环解耦。突发的高速数据先堆在环里，
 *   再由 FileX 线程按 32 KiB 一批慢慢写出去。
 *
 * 记录文件的组成：
 *   文件头（设备身份、启动标识、配置快照、校准代次）
 *   → 若干分段（每段有自己的头，约 1 GiB 换一个新文件）
 *   → 文件尾（本文件记录数、丢失计数、结束原因）
 *   没有合法文件尾的文件即视为"不完整"——这是判断数据可信度的唯一依据。
 *
 * 两个版本的格式：
 *   v1 是早期格式；v2 增加了分段与更完整的元数据，当前默认走 v2。
 *   选择由 use_v2 控制，写入路径略有不同。
 *
 * 关键约束：
 *   · 记录环满时丢帧并计数，绝不阻塞——采集不能因为卡慢而停。
 *   · 换文件期间继续收样，不能出现"换文件时丢一段"。
 *   · 正常结束时必须 flush 并写合法的文件尾；被安全停止打断的保持缺尾，
 *     以此标记"这份数据不完整"。
 *****************************************************************************/

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
/* 纯 CPU 用的暂存区，放在 SRAM4。
 * 注意 SDMMC 的 DMA 缓冲永远是主 SRAM 里那块 staging——SRAM4 不能被 DMA 访问。 */
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

/* 初始化记录子系统：复位环、清状态、准备文件名。
 * 必须先于任何其他记录操作调用，且由 FileX 线程在启动时执行一次。 */
void drms_log_init(void)
{
  (void)drms_fifo_init(&queue, records, 32768, sizeof(records[0]));
  drms_log_running = drms_log_state = action = file_open = 0;
  drms_log_records = drms_log_dropped = pending_records = 0;
  log_ticket_next = 0;
  incomplete = 0;
  use_v2 = v2_end_valid = 0;
}

/* 当前已入环的帧数（票据号），供记录会话判断"还有多少没写完"。 */
uint64_t drms_log_ticket_next(void)
{
  return log_ticket_next;
}

/* 开始记录前的公共准备：确认存储可写、环已复位、文件名确定。
 * 返回 1 可以开始；0 表示存储不可用（未挂载或状态异常）。 */
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

/* 以 v1 格式开始一次记录。只有确实开始成功才返回 1。
 *
 * 所谓"开始"只是登记并排队打开文件，真正的文件在 FileX 线程里创建。
 * 调用方拿到返回值后仍应等文件就绪确认，不能假定已经写盘。 */
int drms_log_start(const DRMS_LogMetadata *request)
{
  if (!request || !reserve_start())
    return 0;
  use_v2 = v2_end_valid = 0;
  metadata = *request;
  __atomic_store_n(&action, 1U, __ATOMIC_RELEASE);
  return 1;
}

/* 以 v2 格式开始一次记录（当前默认路径）。
 *
 * v2 比 v1 多了分段能力与更完整的元数据：每段带独立头，
 * 达到约 1 GiB 时自动换新文件，期间不中断收样。 */
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

/* 请求以 v2 格式正常收尾：先记下结束边界，再让 FileX 线程排空并写文件尾。
 *
 * 这里只是"提交收尾请求"，返回 1 表示请求已登记。
 * 真正关文件要等 drms_log_poll 把环排空后才完成。
 * 若这条路径被中断（例如安全停止抢占），文件会缺尾，表现为不完整记录。 */
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

/* 立即停止记录（不等排空），用于停机流程。
 * 已写出的数据保留，但文件通常缺尾——这是有意的：
 * 缺尾就是"这次记录不完整"的标记。 */
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

/* 以"不完整"为由停止记录。与 drms_log_stop 的区别在于它会显式记录
 * 不完整标志，供后续统计与文件尾判定使用。 */
void drms_log_stop_incomplete(void)
{
  if (drms_log_state)
  {
    v2_end_valid = 0; /* a later failure must never retain a previously clean END */
    __atomic_store_n(&action, 3U, __ATOMIC_RELEASE);
  }
}

/* 把一个原始帧放进记录环。这是采集路径上唯一的调用点。
 *
 * 必须足够快，且**永不阻塞**：环满时直接丢帧并计数，返回 0。
 * 采集宁可丢记录也不能被写卡拖慢——丢了多少由 drms_log_dropped 如实上报。
 *
 * 返回：1 已入环；0 环满或未在记录（两者都只做计数，不报错）。 */
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

/* 处理"记录中途拔卡"：立即停记录、把环里没写出的帧记为丢失、
 * 复位内部状态。已写入的部分保留，文件缺尾。 */
void drms_log_removed(void)
{
  drms_log_running = 0;
  drms_log_status = FX_IO_ERROR;
  (void)__atomic_add_fetch(&drms_log_dropped, drms_fifo_count(&queue) + pending_records, __ATOMIC_RELAXED);
  /* 生产者是优先级更高的主线程，它此刻已经能看到 running=0，不会再往里塞。 */
  (void)drms_fifo_init(&queue, records, 32768, sizeof(records[0]));
  pending_records = file_open = 0;
  log_ticket_next = 0;
  memset(&file, 0, sizeof(file));
  __atomic_store_n(&action, 0U, __ATOMIC_RELEASE);
  __atomic_store_n(&drms_log_state, 0U, __ATOMIC_RELEASE);
}

/* 记录过程中发生 I/O 失败的处理：停止记录并记下底层状态码。
 *
 * 不想在这里反复重试：卡已经坏了，继续试只会拖慢整个系统。
 * 上层看到状态会触发降级，等卡恢复后重新挂载。 */
static void failed(UINT status)
{
  /* I/O 失败之后直接丢弃介质的脏状态，不要反复往一块坏卡上写。
   * 存储层会在后续重试时重新初始化。 */
  drms_log_running = 0;
  drms_storage_invalidate();
  drms_log_status = status;
}

/* 创建并打开一个新的记录文件，写入文件头。
 *
 * continuation 非 0 表示这是"续接"文件——前一个文件已满 1 GiB，
 * 新文件属于同一次记录。两者的头都保留同一份记录元数据，
 * 这样单独拿任何一个文件都能知道它属于哪次试验。
 *
 * 文件名按序号递增，绝不覆盖已有文件。 */
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

/* 记录写入的主循环，由 FileX 线程周期性调用。
 *
 * 三个职责：
 *   1. 处理待办动作（开始/停止/换文件）；
 *   2. 把记录环里的帧攒成最多 32 KiB 的块批量写入，减少写卡次数；
 *   3. 定期 flush，保证掉电时最多只丢最后那一小段。
 *
 * 批量写入是关键：逐帧写会让卡成为瓶颈；攒成 32 KiB 后写入次数下降三个数量级。
 * 攒块用的暂存区在 DMA 可达的主 SRAM 里，不能放在 SRAM4。 */
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
  /* 攒成最多 32 KiB 的块再写。
   * 单生产者单消费者（SPSC）的样本必须在释放槽位之前就拷贝出来，
   * 否则采集侧会立刻把新帧写进同一格。 */
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
    /* 换文件期间保持生产者继续收帧：靠队列去桥接"关旧文件到开新文件"这段延迟。
     * 若队列在此期间真的满了，丢帧会被计数，不会静默吞掉。 */
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
