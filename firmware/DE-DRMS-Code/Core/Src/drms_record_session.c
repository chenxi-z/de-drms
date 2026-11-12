/*****************************************************************************
 * 文件：drms_record_session.c
 * 职责：记录会话——管一次记录的起止边界、丢样记账与完整性判定。
 *
 * 为什么需要单独一层：
 *   "开始记录"和"结束记录"都不是瞬时动作。文件得先创建好，采集侧得先给出
 *   一个一致的边界（哪些帧属于这次记录），中间还有积压要跳过。如果把这些
 *   直接塞进应用线程，状态会散落各处、难以判定完整性。集中到这里之后，
 *   一次记录的生命周期就是一个清晰的状态机。
 *
 * 六阶段状态机（phase）：
 *   PH_IDLE       空闲
 *   PH_START_WAIT 已提交开始，等"文件就绪 + 一致边界 B"——屏障期
 *   PH_ACTIVE     B 已确定：跳过 B 之前的积压，记录 B 之后的新帧
 *   PH_STOP_WAIT  已请求停止，等"一致边界 E"——屏障期
 *   PH_DRAINING   E 已确定：把剩余帧消费到 E 之后发布 END
 *   PH_ENDED      END 已发布，等存储确认收尾
 *
 * 一致边界（DRMS_CaptureBoundary）是整套设计的关键：
 *   它把"采集侧此刻的样本序号、原始票据号、各类丢失计数"打包成一个原子视图。
 *   开始记录时取一次 B、结束时取一次 E，两次之间的帧就是这次记录的完整内容。
 *   没有它就无法回答"这条记录里到底该有哪些帧"，也就无从判定有没有丢样。
 *
 * 完整性怎么判：
 *   · 帧序号必须连续；出现缺口且无法证明缺口有多宽 → 标记未知损失并终止；
 *   · 记录环满导致的丢帧单独计数（log_dropped），与采集侧丢样分开报；
 *   · 只有正常走到 PH_ENDED 且文件写了合法尾，才算完整（clean_end）。
 *
 * 并发模型：状态迁移只在处理线程发生；end_get/end_ack 由存储线程调用，
 * 但只碰各自的字段；64 位字段跨线程读取统一走 get_snapshot 的短临界区。
 *****************************************************************************/

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

/* 判断两个令牌是否指向同一次会话：操作号与代次都相同才算。
 * 代次用于区分"重启后操作号被复用"的情形。 */
static uint32_t token_equal(DRMS_Token a, DRMS_Token b)
{
  return a.operation_id == b.operation_id && a.generation == b.generation;
}

/* 复位会话状态机到空闲态，清空所有记账。
 * 只应在启动时调用一次，或在一个会话彻底收尾之后。 */
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

/* 设置等待一致边界的超时时间（毫秒）。
 * 传 0 表示用默认值 1000 ms。屏障期过长会让启停响应变慢，
 * 过短则可能在采集繁忙时误判失败，默认值是个折中。 */
void drms_record_session_configure(uint32_t wait_ms)
{
  boundary_wait_ms = wait_ms ? wait_ms : DRMS_RECORD_BOUNDARY_WAIT_MS_DEFAULT;
}

/* ------------------------------------------------------------------ */
/* END 发布（处理上下文） */
/* ------------------------------------------------------------------ */

/* 汇总一次记录的结局，形成要对外发布的 END 记录。
 *
 * 这里要回答三个问题：
 *   1. 结束边界是否已知？不知道 E 就无法划定记录的终点；
 *   2. 期间是否出现过"无法证明宽度"的缺口？有就标记 unknown_loss，
 *      因为这时候不能声称数据完整；
 *   3. 采集侧与记录侧的损失分别是多少？两者要分开报，否则无从定位是
 *      采集丢样还是写卡跟不上。
 *
 * unknown_loss 的判据是"开始与结束时的未知损失纪元不同"——
 * 纪元一旦推进，说明中间发生过一次无法界定的中断。 */
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
/* 准备开始一次记录：登记令牌与记录号，进入等待文件与边界的屏障期。
 *
 * 返回 BUSY 的情况值得注意：上一份记录还在等存储确认（end_pending）时，
 * 不允许覆盖那块槽位——否则上一份的结局会被冲掉，主机再也查不到。
 *
 * 这里不创建文件、也不取边界，只做状态登记；真正的启动要等
 * drms_record_ready 拿到一致边界 B 才算成立。 */
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

/* 文件已就绪、并取到一致的开始边界 B——记录从此刻正式生效。
 *
 * 边界 B 决定了"哪些帧属于这次记录"：B 之前采集到的都是积压，要跳过。
 *
 * 两种迟到情形都返回 STALE，不允许把已取消/已收尾的会话重新拉起来：
 *   · 会话已经在 PH_IDLE 或 PH_ENDED；
 *   · 令牌对不上，或当前不在等待状态。
 *
 * 一个细节：如果等 B 的期间操作者已经请求停止（stop_pending），
 * B 定格后不进入 ACTIVE 而是直接进 STOP_WAIT——否则会记进一段
 * 操作者其实已经不要的数据。 */
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

/* 请求停止记录。只置标志，真正的边界 E 要等采集侧给出。
 *
 * 若此时还在等开始边界（PH_START_WAIT），只记下 stop_pending，
 * 等 B 到达后直接转入等 E——这样"刚开就停"也能正确收尾。
 * 若已在记录中，立刻转入 STOP_WAIT。 */
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

/* 拿到一致的结束边界 E，记录进入排空阶段。
 *
 * 校验相当严格，每一步失败都返回 STALE 而不修改本次记录：
 *   · 代次必须与开始时一致——跨代次说明采集重启过，边界不可比；
 *   · E 的样本序号不能早于 B，否则边界是乱的。
 *
 * 重复停止返回 NO_CHANGE 而非报错：保持首次的末边界，
 * 不让后到的停止把记录的终点往后推。 */
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

/* 取消本次记录会话（操作者主动取消，或采集侧出故障）。
 * 取消同样走失败收尾：没有合法末边界，因此文件会缺尾。 */
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
/* 是否处于屏障期——即正在等一致边界（B 或 E）。
 *
 * 屏障期内不应做别的记录相关动作，调用方据此让出这一轮。
 * 名义上很短（等采集在一个静止点给出边界），但采集繁忙时可能要等一会儿。 */
uint32_t drms_record_session_barrier(void)
{
  return (phase == PH_START_WAIT && !have_begin) || phase == PH_STOP_WAIT;
}

/* 判定一个帧该归到哪一类——这是记录窗口的核心判据，每帧都要问一次。
 *
 * 三种结果：
 *   SKIP    早于开始边界 B 的积压，不记录（也不监测，因为已经过去了）
 *   RECORD  落在 [B, E) 窗口内，要记录
 *   MONITOR 窗口之外、或当前根本没在记录，只需驱动监测
 *
 * 排空阶段（PH_DRAINING）特意把窗口上界也拿来判断：E 之后的帧虽然人已经不记录了，
 * 但还要驱动监测，所以返回 MONITOR 而不是 SKIP。
 *
 * 屏障期、失败后、空闲态一律返回 MONITOR——此时没有任何帧属于记录。 */
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

/* 登记"这一帧已经处理过"，并据此判断记录是否还能保持完整。
 *
 * 这是整条记录链路里最需要小心的一处，因为它决定了最终那份数据能不能信。
 *
 * 序号扩展的难点：采集侧给的是 32 位序号，会回绕。这里以一个锚点
 * （上一帧的 64 位序号，或起始边界）为基准做距离推算，把 32 位扩展成 64 位。
 * 前提是"两帧之间的跨度足够小、可以证明"——一旦跨度大到无法排除回绕歧义，
 * 就不能猜，只能判定损失未知并终止。
 *
 * 四种必须终止的情形：
 *   1. 序号重复（distance == 0）：同一帧被处理两次，说明记账已经乱了；
 *   2. 跨度过大（≥ 2^31）：无法证明是前进还是回绕了一整圈；
 *   3. 首帧早于起始边界：边界与数据不一致，通路有问题；
 *   4. 入环失败（enqueue_ok 为 0）：记录环满，后面的数据必然缺失。
 *
 * 终止后就把 unknown_loss_latched 立起来，最终发布的 END 会带上这个标记，
 * 文件保持缺尾。宁可让操作者知道"这次不完整"，也不能给一份看似完整的坏数据。
 *
 * 参数：frame_seq_low 采集侧的 32 位帧序号；bad 该帧是否 CRC 坏；
 *       enqueue_ok 是否成功放进记录环。 */
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

/* 登记消费进度。排空阶段一旦追到结束边界 E，就可以收尾了。
 *
 * 这个"追上了才收尾"的判断很重要：它保证 E 之前的所有帧都已经被处理过，
 * 不会出现"标了结束但还有帧没写进去"的情况。 */
void drms_record_session_note_consumed(uint64_t next_raw_ticket)
{
  last_consumed = next_raw_ticket;
  if (phase == PH_DRAINING && next_raw_ticket >= end_b.raw_next)
    finalize_from_boundaries();
}

/* 屏障期的超时监督。只在等边界（B 或 E）时有意义。
 *
 * 两种放弃等待的情形：
 *   1. 原始环已经满了——说明消费端跟不上，等下去也不会有结果，
 *      而且这时候硬猜一个边界只会得到错的数据；
 *   2. 等待超过期限——同样不生成"伪边界"。
 *
 * 两次都走失败收尾（文件缺尾），而不是硬给一个看起来合理的边界。
 * 第一次调用只登记截止时刻，不判超时，避免把进入的瞬间算作超时。 */
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
/* 存储侧取走待处理的 END 记录。返回 EMPTY 表示当前没有待确认的收尾。
 * 取走后 END 仍留在槽里，直到 ack 才真正放行——这样存储处理失败时可以重试。 */
DRMS_Result drms_record_end_get(DRMS_End *out)
{
  if (!end_pending)
    return DRMS_EMPTY;
  if (!out)
    return DRMS_INVALID;
  *out = end_slot;
  return DRMS_OK;
}

/* 存储侧确认收尾完成，会话回到空闲态，槽位可被下一次记录使用。
 *
 * 令牌校验防止"旧的 END 确认"把新会话关掉。这里的 result 参数仅作记录，
 * 真正的结果已经通过控制完成通道上报过了。 */
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

/* 生成对外的会话状态快照，供协议查询与界面显示。
 *
 * 六个内部阶段被归并成四个对外状态——操作者不需要知道"在等开始边界"和
 * "在等结束边界"的区别，只需要知道"正在启动/正在记录/正在收尾/空闲"。
 * 屏障标志单独给出，用于界面提示"正在切换，请稍候"。 */
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
