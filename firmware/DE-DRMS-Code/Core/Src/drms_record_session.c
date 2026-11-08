#include "drms_record_session.h"
#include <string.h>

/* 所有状态写入只在处理上下文发生；end_get/end_ack 只由存储上下文调用并
 * 仅触碰 end_pending/end_slot/last_storage_result。64-bit 字段跨上下文读取
 * 走 get_snapshot 的短临界区复制。 */
#define DRMS_RECORD_SPAN_PROVABLE_MAX (1ULL << 31)
#define DRMS_RECORD_BOUNDARY_WAIT_MS_DEFAULT 1000u

typedef enum {
  PH_IDLE = 0,
  PH_START_WAIT = 1, /* prepare 后：等文件就绪 + 一致边界 B；屏障 */
  PH_ACTIVE = 2,     /* B 已定：跳过积压、记录新帧；stop_pending 后进入等待 E 屏障 */
  PH_STOP_WAIT = 3,  /* 请求停止：等一致边界 E；屏障 */
  PH_DRAINING = 4,   /* E 已定：消费到 raw_next==E.raw_next 后发布 END */
  PH_ENDED = 5       /* END 已发布：等存储 ack */
} Phase;

static uint32_t boundary_wait_ms = DRMS_RECORD_BOUNDARY_WAIT_MS_DEFAULT;
static Phase phase;
static DRMS_Token token;
static uint64_t record_id;
static uint32_t acquisition_generation;
static DRMS_CaptureBoundary begin, end_b;
static uint32_t have_begin, have_end, have_frame, stop_pending;
static uint32_t failed, unknown_loss_latched;
static uint64_t deadline_ms, deadline_set;
static uint64_t last_consumed;
static uint64_t last_sample;
static uint64_t samples_recorded, quality_bad, log_dropped;
static uint64_t capture_lost_live;
static uint64_t log_ticket_cached;
static uint32_t end_pending;
static DRMS_Result end_reason;
static DRMS_End end_slot;

static uint32_t token_equal(DRMS_Token a, DRMS_Token b)
{
  return a.operation_id == b.operation_id && a.generation == b.generation;
}

void drms_record_session_init(void)
{
  phase = PH_IDLE;
  memset(&token, 0, sizeof(token));
  record_id = 0;
  acquisition_generation = 0;
  memset(&begin, 0, sizeof(begin));
  memset(&end_b, 0, sizeof(end_b));
  have_begin = have_end = have_frame = stop_pending = 0;
  failed = unknown_loss_latched = 0;
  deadline_ms = deadline_set = 0;
  last_consumed = 0;
  last_sample = 0;
  samples_recorded = quality_bad = log_dropped = 0;
  capture_lost_live = 0;
  log_ticket_cached = 0;
  end_pending = 0;
  end_reason = DRMS_OK;
  memset(&end_slot, 0, sizeof(end_slot));
}

void drms_record_session_configure(uint32_t wait_ms)
{
  boundary_wait_ms = wait_ms ? wait_ms : DRMS_RECORD_BOUNDARY_WAIT_MS_DEFAULT;
}

/* ------------------------------------------------------------------ */
/* END 发布（处理上下文） */
/* ------------------------------------------------------------------ */
static void publish_end(DRMS_Result reason, uint32_t end_known)
{
  uint32_t unknown = unknown_loss_latched;
  memset(&end_slot, 0, sizeof(end_slot));
  if (have_end)
  {
    if (begin.unknown_loss_epoch != end_b.unknown_loss_epoch)
      unknown = 1;
  }
  else if (have_begin)
    unknown = 1; /* 有开始边界而无一致末边界：尾部连续性不可证明（C1） */
  end_slot.token = token;
  end_slot.record_id = record_id;
  end_slot.ring_end = log_ticket_cached;
  end_slot.lost_count = capture_lost_live; /* 兼容诊断，不作跨阶段精确总数 */
  end_slot.first.generation = acquisition_generation;
  end_slot.first.index = have_begin ? begin.sample_next : 0;
  end_slot.end_known = end_known;
  if (end_known)
  {
    /* 未知末边界不写伪精确 end：end_known=false 时 end_exclusive 保持零。 */
    end_slot.end_exclusive.generation = acquisition_generation;
    end_slot.end_exclusive.index = end_b.sample_next;
  }
  end_slot.last_confirmed_position.generation = acquisition_generation;
  end_slot.last_confirmed_position.index = last_sample;
  end_slot.capture_lost = capture_lost_live;
  end_slot.log_dropped = log_dropped;
  end_slot.quality_bad = quality_bad;
  end_slot.unknown_loss = unknown;
  end_slot.storage_error = 0;
  end_slot.reason = reason;
  end_pending = 1;
  end_reason = reason;
  phase = PH_ENDED;
}

/* 本次窗口损失与结论（E 在手时调用）。 */
static void finalize_from_boundaries(void)
{
  capture_lost_live = end_b.capture_lost_total - begin.capture_lost_total;
  uint32_t unknown = begin.unknown_loss_epoch != end_b.unknown_loss_epoch;
  DRMS_Result reason;
  if (samples_recorded == 0)
  {
    /* B/E 相等且无损失才 EMPTY；有采样但全丢失为 INCOMPLETE。 */
    reason = (capture_lost_live == 0u && !unknown && begin.sample_next == end_b.sample_next)
                 ? DRMS_EMPTY
                 : DRMS_INCOMPLETE;
  }
  else
    reason = (capture_lost_live || unknown) ? DRMS_INCOMPLETE : DRMS_OK;
  publish_end(reason, 1);
}

/* 失败收尾：无一致末边界 → end_known=false、LOSS_UNKNOWN（C1），
 * 不写伪精确 end；文件内已记录范围由 ring_end 与 last_confirmed 界定。 */
static void fail_session(DRMS_Result reason)
{
  if (phase == PH_ENDED || phase == PH_IDLE)
    return;
  failed = 1;
  stop_pending = 0;
  publish_end(reason, 0);
}

/* ------------------------------------------------------------------ */
/* 会话生命周期（处理上下文） */
/* ------------------------------------------------------------------ */
DRMS_Result drms_record_prepare(DRMS_Token session_token, uint64_t id)
{
  if (phase != PH_IDLE || end_pending)
    return DRMS_BUSY; /* 存储确认前槽不得被下一次记录覆盖 */
  token = session_token;
  record_id = id;
  have_begin = have_end = have_frame = stop_pending = 0;
  failed = unknown_loss_latched = 0;
  deadline_set = 0;
  last_consumed = 0;
  last_sample = 0;
  samples_recorded = quality_bad = log_dropped = 0;
  capture_lost_live = 0;
  log_ticket_cached = 0;
  phase = PH_START_WAIT;
  return DRMS_ACCEPTED;
}

DRMS_Result drms_record_ready(DRMS_Token session_token, DRMS_CaptureBoundary boundary)
{
  if (phase == PH_IDLE || phase == PH_ENDED)
    return DRMS_STALE; /* 迟到 READY：会话已取消/已收尾，不得转为 RECORDING */
  if (phase != PH_START_WAIT || !token_equal(session_token, token))
    return DRMS_STALE;
  begin = boundary;
  have_begin = 1;
  acquisition_generation = boundary.acquisition_generation;
  deadline_set = 0;
  phase = PH_ACTIVE;
  if (stop_pending)
    phase = PH_STOP_WAIT; /* 开始等待期间已请求停止：B 定格后立即等 E */
  return DRMS_OK;
}

void drms_record_session_request_stop(void)
{
  if (phase == PH_ACTIVE || phase == PH_START_WAIT)
  {
    stop_pending = 1;
    if (phase == PH_ACTIVE)
      phase = PH_STOP_WAIT;
    deadline_set = 0;
  }
}

DRMS_Result drms_record_stop_at(DRMS_Token session_token, DRMS_CaptureBoundary end_exclusive)
{
  if (phase == PH_DRAINING)
    return DRMS_NO_CHANGE; /* 重复 STOP 保持首次末边界 */
  if (phase != PH_ACTIVE && phase != PH_STOP_WAIT)
    return DRMS_STALE;
  if (!token_equal(session_token, token))
    return DRMS_STALE;
  if (!have_begin || end_exclusive.acquisition_generation != begin.acquisition_generation)
    return DRMS_STALE; /* 跨 generation 边界拒绝，不修改本次记录 */
  if (end_exclusive.sample_next < begin.sample_next)
    return DRMS_INVALID;
  end_b = end_exclusive;
  have_end = 1;
  stop_pending = 0;
  deadline_set = 0;
  phase = PH_DRAINING;
  capture_lost_live = end_b.capture_lost_total - begin.capture_lost_total;
  if (last_consumed >= end_b.raw_next)
    finalize_from_boundaries(); /* 消费者已越过 E：立即收尾 */
  return DRMS_OK;
}

void drms_record_session_cancel(DRMS_Token session_token, DRMS_Result reason)
{
  if (phase == PH_IDLE || phase == PH_ENDED)
    return;
  if (!token_equal(session_token, token))
    return;
  fail_session(reason == DRMS_OK ? DRMS_CANCELLED : reason);
}

/* ------------------------------------------------------------------ */
/* 数据通路（处理上下文） */
/* ------------------------------------------------------------------ */
uint32_t drms_record_session_barrier(void)
{
  return (phase == PH_START_WAIT && !have_begin) || phase == PH_STOP_WAIT;
}

DRMS_RecordVerdict drms_record_session_classify(uint64_t raw_ticket)
{
  if (phase == PH_ACTIVE)
    return raw_ticket < begin.raw_next ? DRMS_RECORD_SKIP : DRMS_RECORD_RECORD;
  if (phase == PH_DRAINING)
  {
    if (raw_ticket < begin.raw_next)
      return DRMS_RECORD_SKIP;
    return raw_ticket < end_b.raw_next ? DRMS_RECORD_RECORD : DRMS_RECORD_MONITOR;
  }
  return DRMS_RECORD_MONITOR; /* 屏障期/失败后/空闲：仅监测 */
}

void drms_record_session_note_recorded(uint32_t frame_seq_low, uint32_t bad,
                                       uint32_t enqueue_ok)
{
  if (phase != PH_ACTIVE && phase != PH_DRAINING)
    return;
  if (bad)
    ++quality_bad; /* CRC 坏帧已发布：独立计数，不重复计 capture_lost */
  /* 32 位序号按锚点顺序扩展；跨度不可证明 → LOSS_UNKNOWN 并终止本次记录。 */
  uint64_t anchor = have_frame ? last_sample : begin.sample_next;
  uint32_t distance = (uint32_t)(frame_seq_low - (uint32_t)anchor);
  if (have_frame && distance == 0u)
  {
    unknown_loss_latched = 1;
    fail_session(DRMS_INCOMPLETE);
    return;
  }
  if (distance >= (uint32_t)DRMS_RECORD_SPAN_PROVABLE_MAX)
  {
    unknown_loss_latched = 1;
    fail_session(DRMS_INCOMPLETE);
    return;
  }
  uint64_t extended = anchor + distance;
  if (!have_frame && extended < begin.sample_next)
  { /* 锚点前样本不得记录；保守判通路故障 */
    unknown_loss_latched = 1;
    fail_session(DRMS_INCOMPLETE);
    return;
  }
  last_sample = extended;
  have_frame = 1;
  ++samples_recorded;
  if (!enqueue_ok)
  {
    ++log_dropped; /* 记录环满：停止追加，失败 END（C1） */
    fail_session(DRMS_INCOMPLETE);
  }
}

void drms_record_session_note_log_ticket(uint64_t ring_end_log_ticket)
{
  log_ticket_cached = ring_end_log_ticket;
}

void drms_record_session_note_consumed(uint64_t next_raw_ticket)
{
  last_consumed = next_raw_ticket;
  if (phase == PH_DRAINING && next_raw_ticket >= end_b.raw_next)
    finalize_from_boundaries();
}

void drms_record_session_poll(uint64_t now_ms, uint32_t raw_used, uint32_t raw_capacity)
{
  if (phase != PH_START_WAIT && phase != PH_STOP_WAIT)
    return;
  if (!deadline_set)
  {
    deadline_ms = now_ms + boundary_wait_ms;
    deadline_set = 1;
    return;
  }
  if (raw_capacity && raw_used >= raw_capacity)
  {
    fail_session(DRMS_INCOMPLETE); /* 原始环满：不猜测边界 */
    return;
  }
  if ((int64_t)(now_ms - deadline_ms) >= 0)
    fail_session(DRMS_TIMEOUT); /* 边界等待期限到达：不生成伪边界 */
}

/* ------------------------------------------------------------------ */
/* 完成槽（存储上下文） */
/* ------------------------------------------------------------------ */
DRMS_Result drms_record_end_get(DRMS_End *out)
{
  if (!end_pending)
    return DRMS_EMPTY;
  if (!out)
    return DRMS_INVALID;
  *out = end_slot;
  return DRMS_OK;
}

DRMS_Result drms_record_end_ack(DRMS_Token session_token, DRMS_Result result)
{
  (void)result; /* 存储最终结果经控制完成通道上报；此处仅确认释放 */
  if (!end_pending)
    return DRMS_EMPTY;
  if (!token_equal(session_token, end_slot.token))
    return DRMS_STALE;
  end_pending = 0;
  phase = PH_IDLE;
  return DRMS_OK;
}

void drms_record_session_get_snapshot(DRMS_RecordSessionSnapshot *out)
{
  if (!out)
    return;
  uint32_t state;
  if (phase == PH_IDLE)
    state = DRMS_RECORD_IDLE;
  else if (phase == PH_ENDED)
    state = DRMS_RECORD_FINALIZING;
  else
    state = have_frame ? DRMS_RECORD_RECORDING : DRMS_RECORD_STARTING;
  out->state = state;
  out->barrier = drms_record_session_barrier();
  out->stop_pending = stop_pending;
  out->acquisition_generation = acquisition_generation;
  out->record_id = record_id;
  out->token = token;
  out->samples_recorded = samples_recorded;
  out->quality_bad = quality_bad;
  out->log_dropped = log_dropped;
  out->capture_lost = capture_lost_live;
  out->unknown_loss = unknown_loss_latched ||
                      (have_begin && have_end &&
                       begin.unknown_loss_epoch != end_b.unknown_loss_epoch);
  out->end_pending = end_pending;
  out->end_reason = end_reason;
}
