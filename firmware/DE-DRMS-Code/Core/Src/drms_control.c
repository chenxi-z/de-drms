/*****************************************************************************
 * 文件：drms_control.c
 * 职责：资源裁决器——决定"此刻谁可以用采集、TF 卡、Flash"。
 *
 * 为什么需要它：
 *   这些硬件资源不能被两条路径同时使用。例如正在记录时不能导出 U 盘，
 *   正在校准时不能改采样率。与其在每个调用点重复判断，不如集中成一层：
 *   任何涉及资源的请求都先来这里排队、申请租约，批准后才真正执行。
 *
 * 三个核心概念：
 *   租约（Lease）    某个操作对一组资源的独占权。操作结束才归还。
 *                    表容量 4，足够覆盖所有不相交组合（见下方说明）。
 *   隔离（Quarantine）资源状态无法证明是干净的时，标记为隔离。
 *                    隔离期间拒绝新请求，直到显式恢复。宁可停摆也不冒险复用。
 *   停止（Stopping）  一个取消屏障。进入停止态后，排队的请求按序收尾，
 *                    期间只允许恢复类操作通过。
 *
 * 并发模型：
 *   · submit 可由任意线程调用，只在极短的 PRIMASK 临界区里入队；
 *   · 状态迁移（批准、归结、释放）只在控制线程里发生；
 *   · get_snapshot 在临界区里整体拷贝，保证读者看到自洽快照。
 *****************************************************************************/

#include "drms_control.h"
#include "main.h"
#include <string.h>

/* 原子资源裁决器实现（T1）。
 * 并发模型：submit 允许多线程，经 PRIMASK 短临界区入队并分配请求元数据；
 * 其余状态迁移只在控制任务上下文发生，临界区仅保护 get_snapshot 的一致复制。
 * 租约表容量按可达并发上界取 4：一个 TF 独占租约 + 一个 ACQ+FLASH 独占租约
 * 已覆盖全部不相交组合（C2 资源矩阵中无第三组不相交集合）。 */
#define DRMS_CONTROL_LEASES 4
#define DRMS_CONTROL_REQUESTS 8
#define DRMS_CONTROL_COMPLETIONS 8
#define DRMS_CONTROL_HISTORY 8

typedef struct {
  uint64_t operation_id;
  uint32_t generation;
  uint32_t resources;
  uint32_t active;
  uint32_t reported;
  uint32_t source;
  uint32_t session;
  uint64_t request_id;
} Lease;

static DRMS_ControlDispatch dispatch_hook;
static Lease leases[DRMS_CONTROL_LEASES];
typedef struct { DRMS_ControlRequest request; uint64_t operation_id; } QueuedRequest;
static QueuedRequest requests[DRMS_CONTROL_REQUESTS];
/* 配置载荷从"受理"一路持有到"分派"，中间只有这一块缓冲。
 *
 * 拷贝时中断是开着的（数据量大，不能在临界区里拷），但用一个"占用"标志
 * 防止别的请求在拷贝期间复用这块内存——所以它是"预占"而不是锁。 */
#define DRMS_CONTROL_CONFIG_MAX 1024u
static uint8_t config_payload[DRMS_CONTROL_CONFIG_MAX];
static uint32_t config_payload_in_use;
static DRMS_ControlCompletion completions[DRMS_CONTROL_COMPLETIONS];
static DRMS_ControlCompletion history[DRMS_CONTROL_HISTORY];
static uint32_t history_head, history_count;
static uint32_t request_head, request_count, request_tail;
static uint32_t completion_head, completion_count;
static uint32_t reserved_mask, quarantined_mask;
static uint32_t stopping, control_generation, snapshot_sequence;
static uint64_t next_operation_id;
static uint64_t next_record_id;
typedef struct { uint64_t record_id, operation_id; DRMS_Result result; uint32_t started; } RecordAdmission;
static RecordAdmission record_admissions[16];
static uint32_t record_admission_next;
static uint64_t requests_accepted, requests_rejected;
static uint64_t completions_overflow, completions_consumed;
static QueuedRequest safe_stop;
static uint32_t safe_stop_phase; /* 0 empty, 1 pending, 2 active */

/* 处于停止态时仍然允许通过的少数操作。
 *
 * 停止的目的是让在途操作收尾，而不是把设备锁死。所以这几类必须放行：
 *   · RESUME_MONITOR：唯一的"解除停止"入口，拦住它就无法恢复；
 *   · MSC_EXPORT / MSC_RELEASE：U 盘导出与交还，它们不碰采集资源，
 *     且操作者常常正是想"停下来导数据"，此时拒绝会让设备没法用。
 *
 * 其他操作（记录、配置、校准）一律拒绝，因为它们都需要占用采集资源。 */
static uint32_t allowed_while_stopped(DRMS_Operation operation)
{
  return operation == DRMS_OP_RESUME_MONITOR || operation == DRMS_OP_MSC_EXPORT ||
         operation == DRMS_OP_MSC_RELEASE;
}

/* 进/出临界区。保护的粒度只到"几条赋值"，不用于等待或长流程。 */
static uint32_t crit_enter(void)
{
  uint32_t mask = __get_PRIMASK();
  __disable_irq();
  return mask;
}

/* 退出临界区，恢复进入前的中断屏蔽状态。 */
static void crit_exit(uint32_t mask) { __set_PRIMASK(mask); }

/* 每种操作需要占用哪些资源——整个裁决器的判据都来自这张表。
 *
 * 三种资源：
 *   ACQUISITION_CONFIG  采集配置（改采样率、换样品/参考支路、启停）
 *   RECORD_SESSION      记录会话（同一时刻只能有一个记录在跑）
 *   TF_ACCESS           TF 卡访问（记录写入、U 盘导出、文件下载、文件列举）
 *   FLASH_MAINTENANCE   Flash 维护（保存配置、保存校准）
 *
 * 设计原则：只要两个操作会动到同一份资源，就必须串行，宁可比实际需要更保守。
 * 例如 CALIBRATE 同时占 ACQ+TF+FLASH，因为它要读参考支路、要写校准到 Flash，
 * 而这个过程中不能有记录在写卡。
 *
 * 表里没有列出的操作视为不需要资源（返回 0），可以随时并行执行——
 * 典型的是各类只读查询。 */
uint32_t drms_control_resources_for(DRMS_Operation operation)
{
  switch (operation)
  {
    case DRMS_OP_RECORD: return DRMS_RES_ACQUISITION_CONFIG | DRMS_RES_RECORD_SESSION |
                                DRMS_RES_TF_ACCESS;
    case DRMS_OP_MSC_EXPORT: return DRMS_RES_TF_ACCESS;
    case DRMS_OP_FILE_DOWNLOAD: return DRMS_RES_TF_ACCESS;
    case DRMS_OP_FILE_LIST: return DRMS_RES_TF_ACCESS;
    case DRMS_OP_CONFIG_APPLY: return DRMS_RES_ACQUISITION_CONFIG | DRMS_RES_FLASH_MAINTENANCE;
    case DRMS_OP_BASELINE_R0: return DRMS_RES_ACQUISITION_CONFIG | DRMS_RES_TF_ACCESS |
                                      DRMS_RES_FLASH_MAINTENANCE;
    case DRMS_OP_CALIBRATE: return DRMS_RES_ACQUISITION_CONFIG | DRMS_RES_TF_ACCESS |
                                    DRMS_RES_FLASH_MAINTENANCE;
    case DRMS_OP_CONFIG_SAVE: return DRMS_RES_ACQUISITION_CONFIG | DRMS_RES_TF_ACCESS |
                                      DRMS_RES_FLASH_MAINTENANCE;
    case DRMS_OP_UPDATE: return DRMS_RES_ALL;
    default: return 0;
  }
}

/* 记下一次"操作已结束"的归结。调用方必须已持有临界区（函数名里的 locked）。
 *
 * 同时做两件事：
 *   1. 把结果放进完成队列，等发起方来取；
 *   2. 把结果存进历史环，供事后按操作号查询。
 *
 * 队列满时的策略很关键：丢最旧的一条并计数，**绝不因此阻塞或占用资源**。
 * 因为资源释放在 complete 内部已经做完了，拥塞只影响"通知"，不影响正确性。
 * 而记录受理表会顺带更新：成功则标记 started，失败则记录失败原因。 */
static void push_completion_locked(uint32_t source, uint32_t session, uint64_t request_id,
                                   uint64_t operation_id, DRMS_Result result,
                                   uint32_t quiescent_mask, uint32_t stale)
{
  DRMS_ControlCompletion *slot;
  for (uint32_t i = 0; i < 16u; ++i)
    if (record_admissions[i].operation_id == operation_id && operation_id)
    {
      if (result == DRMS_OK) record_admissions[i].started = 1;
      else record_admissions[i].result = result;
    }
  if (completion_count == DRMS_CONTROL_COMPLETIONS)
  {
    /* 拥塞：丢最旧并计数。资源释放在 complete 内已完成，永不因拥塞占用资源。 */
    ++completions_overflow;
    completion_head = (completion_head + 1U) % DRMS_CONTROL_COMPLETIONS;
    --completion_count;
  }
  slot = &completions[(completion_head + completion_count) % DRMS_CONTROL_COMPLETIONS];
  slot->operation_id = operation_id;
  slot->source = source;
  slot->session = session;
  slot->request_id = request_id;
  slot->result = result;
  slot->quiescent_mask = quiescent_mask;
  slot->stale = stale;
  slot->phase = 2;
  if (operation_id)
  {
    history[history_head] = *slot;
    history_head = (history_head + 1U) % DRMS_CONTROL_HISTORY;
    if (history_count < DRMS_CONTROL_HISTORY)
      ++history_count;
  }
  ++completion_count;
}

/* 初始化裁决器：清空所有表、登记分派钩子。
 *
 * dispatch 是应用层提供的执行入口——裁决器只负责"准不准",真正的动作由它执行。
 * 必须在调度器启动前调用。 */
void drms_control_init(DRMS_ControlDispatch dispatch)
{
  uint32_t mask = crit_enter();
  dispatch_hook = dispatch;
  memset(leases, 0, sizeof(leases));
  memset(requests, 0, sizeof(requests));
  config_payload_in_use = 0;
  memset(completions, 0, sizeof(completions));
  memset(history, 0, sizeof(history));
  memset(&safe_stop, 0, sizeof(safe_stop));
  safe_stop_phase = 0;
  history_head = history_count = 0;
  request_head = request_count = request_tail = 0;
  completion_head = completion_count = 0;
  reserved_mask = quarantined_mask = 0;
  stopping = 0;
  control_generation = 1;
  snapshot_sequence = 0;
  next_operation_id = 1;
  next_record_id = 1;
  memset(record_admissions, 0, sizeof(record_admissions));
  record_admission_next = 0;
  requests_accepted = requests_rejected = 0;
  completions_overflow = completions_consumed = 0;
  crit_exit(mask);
}

/* 按操作号查询状态，主机用它轮询异步操作的进展。
 *
 * 查找顺序是有讲究的，反映操作的生命周期：
 *   1. 安全停止表——它是特殊通道，可能还没走完排队；
 *   2. 历史环——已结束的操作，能查到最终结果；
 *   3. 活跃租约——已批准、正在执行；
 *   4. 请求队列——已受理、还没轮到。
 *
 * 找不到时按编号大小判断：比已分配的最大编号小，说明那条记录已经被挤出保留窗口
 * （返回 STALE，主机应改读卡上文件）；否则是编号本身不存在（INVALID）。 */
DRMS_Result drms_control_get_operation(uint64_t operation_id, DRMS_ControlCompletion *out)
{
  if (!operation_id || !out)
    return DRMS_INVALID;
  uint32_t mask = crit_enter();
  if (safe_stop_phase && safe_stop.operation_id == operation_id)
  {
    memset(out, 0, sizeof(*out));
    out->operation_id = operation_id;
    out->source = safe_stop.request.source;
    out->session = safe_stop.request.session;
    out->request_id = safe_stop.request.request_id;
    out->result = DRMS_ACCEPTED;
    out->phase = safe_stop_phase - 1u;
    crit_exit(mask);
    return DRMS_OK;
  }
  for (uint32_t i = 0; i < history_count; ++i)
  {
    uint32_t index = (history_head + DRMS_CONTROL_HISTORY - 1U - i) % DRMS_CONTROL_HISTORY;
    if (history[index].operation_id == operation_id)
    {
      *out = history[index];
      crit_exit(mask);
      return DRMS_OK;
    }
  }
  for (uint32_t i = 0; i < DRMS_CONTROL_LEASES; ++i)
  {
    Lease *lease = &leases[i];
    if (lease->active && !lease->reported && lease->operation_id == operation_id)
    {
      out->operation_id = operation_id;
      out->source = lease->source;
      out->session = lease->session;
      out->request_id = lease->request_id;
      out->result = DRMS_ACCEPTED;
      out->quiescent_mask = 0;
      out->stale = lease->generation != control_generation;
      out->phase = 1;
      crit_exit(mask);
      return DRMS_OK;
    }
  }
  for (uint32_t i = 0; i < request_count; ++i)
  {
    const QueuedRequest *queued = &requests[(request_tail + i) % DRMS_CONTROL_REQUESTS];
    if (queued->operation_id == operation_id)
    {
      memset(out, 0, sizeof(*out));
      out->operation_id = operation_id;
      out->source = queued->request.source;
      out->session = queued->request.session;
      out->request_id = queued->request.request_id;
      out->result = DRMS_ACCEPTED;
      crit_exit(mask);
      return DRMS_OK;
    }
  }
  DRMS_Result result = operation_id < next_operation_id ? DRMS_STALE : DRMS_INVALID;
  crit_exit(mask);
  return result;
}

/* 提交一个控制请求（不需要拿到操作号的场合）。内部转调带编号的版本。 */
DRMS_Result drms_control_submit(const DRMS_ControlRequest *request)
{
  return drms_control_submit_identified(request, NULL);
}

/* 提交一次安全停止。
 *
 * 安全停止走独立通道而不是普通队列，原因是它必须能"插队"：主机可能刚发了一串
 * 命令，其中某条卡住了，此时停止必须立刻生效，不能排在它们后面等。
 *
 * 同一时刻只允许一个安全停止在途（safe_stop_phase 非 0 即拒绝），
 * 因为重复停止没有意义，且会让状态机难以收敛。
 *
 * 返回：ACCEPTED 已登记；BUSY 已有停止在途；INVALID 参数为空。 */
DRMS_Result drms_control_safe_stop_submit(const DRMS_ControlRequest *request, uint64_t *operation_id)
{
  if (operation_id) *operation_id = 0;
  if (!request || !operation_id)
    return DRMS_INVALID;
  uint32_t mask = crit_enter();
  if (safe_stop_phase || !next_operation_id)
  {
    crit_exit(mask);
    return DRMS_BUSY;
  }
  safe_stop.request = *request;
  safe_stop.operation_id = next_operation_id++;
  *operation_id = safe_stop.operation_id;
  safe_stop_phase = 1;
  crit_exit(mask);
  return DRMS_ACCEPTED;
}

/* 由控制线程取走待处理的安全停止请求，把状态从"待办"推进到"执行中"。
 *
 * 返回 1 表示确实取到了一条（调用方应去执行停止动作），0 表示没有待办的。
 * 这个"取走"是原子的，所以同一条停止不会被处理两次。 */
uint32_t drms_control_safe_stop_take(void)
{
  uint32_t mask = crit_enter();
  uint32_t taken = safe_stop_phase == 1u;
  if (taken) safe_stop_phase = 2u;
  crit_exit(mask);
  return taken;
}

/* 安全停止执行完毕，记下最终结果并释放这道通道。
 *
 * 只有在"执行中"状态调用才有效；重复调用返回 INVALID，
 * 这样能防止把同一个停止归结两次。 */
DRMS_Result drms_control_safe_stop_finish(DRMS_Result result)
{
  uint32_t mask = crit_enter();
  if (safe_stop_phase != 2u)
  {
    crit_exit(mask);
    return DRMS_INVALID;
  }
  push_completion_locked(safe_stop.request.source, safe_stop.request.session,
                         safe_stop.request.request_id, safe_stop.operation_id, result, 0, 0);
  safe_stop_phase = 0;
  crit_exit(mask);
  return DRMS_OK;
}

/* 请求入队的实际实现。这是 submit 的最底层，所有提交路径最终都到这里。
 *
 * 在临界区里一次性完成：分配操作号（记录类还分配记录号）、
 * 登记记录受理表、把请求放进队列。任何一步失败都不会留下部分状态。
 *
 * 队列满时返回 BUSY——调用方应重试或让主机稍后再来。 */
static DRMS_Result submit_identified(const DRMS_ControlRequest *request, uint64_t *operation_id, uint64_t *record_id)
{
  uint32_t mask;
  uint32_t owns_payload = 0;
  uint32_t payload_generation = 0;
  QueuedRequest *slot;
  if (operation_id) *operation_id = 0;
  if (record_id) *record_id = 0;
  if (!request || request->operation <= DRMS_OP_NONE || request->operation > DRMS_OP_END_RECORD)
    return DRMS_INVALID;
  if (request->operation == DRMS_OP_CONFIG_APPLY && request->payload_length)
  {
    if (!request->payload || request->payload_length > sizeof(config_payload))
      return DRMS_INVALID;
    mask = crit_enter();
    if (stopping || config_payload_in_use)
    {
      DRMS_Result result = stopping ? DRMS_CANCELLED : DRMS_BUSY;
      crit_exit(mask);
      return result;
    }
    config_payload_in_use = 1;
    payload_generation = control_generation;
    crit_exit(mask);
    memcpy(config_payload, request->payload, request->payload_length);
    owns_payload = 1;
  }
  mask = crit_enter();
  if (owns_payload && payload_generation != control_generation)
  {
    config_payload_in_use = 0;
    crit_exit(mask);
    return DRMS_CANCELLED;
  }
  if (stopping && !allowed_while_stopped(request->operation))
  {
    if (owns_payload) config_payload_in_use = 0;
    crit_exit(mask);
    ++requests_rejected;
    return DRMS_CANCELLED;
  }
  if (request_count == DRMS_CONTROL_REQUESTS || !next_operation_id ||
      (request->operation == DRMS_OP_RECORD && !next_record_id))
  {
    if (owns_payload) config_payload_in_use = 0;
    crit_exit(mask);
    ++requests_rejected;
    return DRMS_BUSY;
  }
  uint32_t admission_index = record_admission_next;
  if (request->operation == DRMS_OP_RECORD)
  {
    uint32_t count = 0;
    while (count < 16u && record_admissions[admission_index].record_id &&
           !record_admissions[admission_index].started &&
           record_admissions[admission_index].result == DRMS_ACCEPTED)
    {
      admission_index = (admission_index + 1u) % 16u;
      ++count;
    }
    if (count == 16u)
    {
      crit_exit(mask);
      ++requests_rejected;
      return DRMS_BUSY;
    }
  }
  slot = &requests[request_head];
  slot->request = *request;
  slot->request.record_id = request->operation == DRMS_OP_RECORD ? next_record_id++ : 0;
  if (record_id) *record_id = slot->request.record_id;
  if (owns_payload) slot->request.payload = config_payload;
  slot->operation_id = next_operation_id++;
  if (slot->request.record_id)
  {
    RecordAdmission *entry = &record_admissions[admission_index];
    entry->record_id = slot->request.record_id;
    entry->operation_id = slot->operation_id;
    entry->result = DRMS_ACCEPTED;
    entry->started = 0;
    record_admission_next = (admission_index + 1u) % 16u;
  }
  if (operation_id) *operation_id = slot->operation_id;
  request_head = (request_head + 1U) % DRMS_CONTROL_REQUESTS;
  ++request_count;
  ++requests_accepted;
  crit_exit(mask);
  return DRMS_ACCEPTED;
}

/* 提交请求并取回分配给它的操作号。主机靠这个号后续查询结果。 */
DRMS_Result drms_control_submit_identified(const DRMS_ControlRequest *request, uint64_t *operation_id)
{
  return submit_identified(request, operation_id, NULL);
}

/* 提交一记录开始请求，同时取回操作号与记录号。
 *
 * 记录号在**受理时**就分配，而不是等真正开始写文件才分配。
 * 这样主机一提交就能拿到编号去查询，不必反复轮询"到底开始了没有"。
 * 若这次记录最终没能开始，编号会作废并在受理表里留下失败原因。 */
DRMS_Result drms_control_submit_record(const DRMS_ControlRequest *request, uint64_t *operation_id, uint64_t *record_id)
{
  if (!request || request->operation != DRMS_OP_RECORD || !operation_id || !record_id)
    return DRMS_INVALID;
  return submit_identified(request, operation_id, record_id);
}

/* 查询一个已分配但尚未开始的记录号现在的状态。
 *
 * 三种结果：
 *   OK + result   还在等待开始，result 是当前已知的受理结果；
 *   STALE         已经开始（或者编号已被挤出保留窗口），应改查正式记录；
 *   INVALID       编号从未分配。
 *
 * 这个区分让主机能明确判断"是还没开始，还是已经开始了"。 */
DRMS_Result drms_control_record_admission(uint64_t record_id, DRMS_Result *result)
{
  if (!record_id || !result) return DRMS_INVALID;
  uint32_t mask = crit_enter();
  for (uint32_t i = 0; i < 16u; ++i)
  {
    if (record_admissions[i].record_id == record_id)
    {
      if (record_admissions[i].started)
      {
        crit_exit(mask);
        return DRMS_STALE;
      }
      *result = record_admissions[i].result;
      crit_exit(mask);
      return DRMS_OK;
    }
  }
  DRMS_Result status = record_id < next_record_id ? DRMS_STALE : DRMS_INVALID;
  crit_exit(mask);
  return status;
}

/* 由操作号反查它对应的记录号（没有关联则返回 0）。
 * 主机拿到操作结果时，靠它知道这个结果属于哪条记录。 */
uint64_t drms_control_operation_record(uint64_t operation_id)
{
  if (!operation_id) return 0;
  uint32_t mask = crit_enter();
  uint64_t record_id = 0;
  for (uint32_t i = 0; i < 16u; ++i)
    if (record_admissions[i].operation_id == operation_id)
    {
      record_id = record_admissions[i].record_id;
      break;
    }
  crit_exit(mask);
  return record_id;
}

/* 申请一组资源。这是整套裁决的核心：批准则返回租约，否则说明原因。
 *
 * 参数：
 *   resources       需要的资源位掩码
 *   out             成功时回填令牌（操作号 + 代次）
 *   assigned_id     非 0 表示沿用调用方已经分配好的操作号（提交路径用），
 *                   0 表示现在分配一个新的（直接调用路径用）
 *   allow_empty     允许申请"零资源"，用于纯查询类操作
 *   allow_stopping  允许在停止态通过（见 allowed_while_stopped）
 *
 * 判据全在临界区里一次算完，绝不产生"占了一半"的中间状态：
 *   · 与 reserved_mask 或 quarantined_mask 相交 → BUSY
 *     （隔离态尤其重要：那意味着资源状态不可证明，禁止任何新占用）
 *   · 停止态且不允许通行 → CANCELLED
 *   · 租约表满了 → BUSY
 *
 * UPDATE_EXCLUSIVE 是唯一允许"展开"的位：它本身不能单独持有，
 * 会自动展开成"全部资源"，避免升级动作与别的操作并存。 */
static DRMS_Result reserve_assigned(uint32_t resources, DRMS_Token *out, uint64_t assigned_id,
                                    uint32_t allow_empty, uint32_t allow_stopping)
{
  uint32_t mask, granted, i;
  Lease *lease = NULL;
  if (out)
  {
    out->operation_id = 0;
    out->generation = 0;
  }
  if (resources & ~(uint32_t)DRMS_RES_ALL)
    return DRMS_INVALID;
  if (resources & DRMS_RES_UPDATE_EXCLUSIVE)
    resources = DRMS_RES_ALL; /* 升级位禁止单独持有，自动展开（C2） */
  if (!resources && !allow_empty)
    return DRMS_INVALID;
  mask = crit_enter();
  if (stopping && !allow_stopping)
  {
    crit_exit(mask);
    return DRMS_CANCELLED;
  }
  /* 一次性全量检查：与已占/已隔离位相交即拒绝，不产生部分占用。 */
  if (resources & (reserved_mask | quarantined_mask))
  {
    crit_exit(mask);
    return DRMS_BUSY;
  }
  for (i = 0; i < DRMS_CONTROL_LEASES; ++i)
  {
    if (!leases[i].active)
    {
      lease = &leases[i];
      break;
    }
  }
  if (!lease)
  {
    crit_exit(mask);
    return DRMS_BUSY;
  }
  if (!assigned_id && !next_operation_id)
  {
    crit_exit(mask);
    return DRMS_BUSY;
  }
  granted = resources;
  lease->operation_id = assigned_id ? assigned_id : next_operation_id++;
  lease->generation = control_generation;
  lease->resources = granted;
  lease->active = 1;
  lease->reported = 0;
  lease->source = DRMS_SOURCE_NONE;
  lease->session = 0;
  lease->request_id = 0;
  reserved_mask |= granted;
  if (out)
  {
    out->operation_id = lease->operation_id;
    out->generation = lease->generation;
  }
  crit_exit(mask);
  return DRMS_ACCEPTED;
}

/* 直接申请资源（调用方自己发起，不经过请求队列）。 */
DRMS_Result drms_control_reserve(uint32_t resources, DRMS_Token *out)
{
  return reserve_assigned(resources, out, 0, 0, 0);
}

/* 报告操作结果，但**不释放资源**。
 *
 * 用于"操作已出结果、但资源还要继续占用一会儿"的场合（例如记录已结束、
 * 但文件还在收尾）。真正归还资源要另调 drms_control_release。
 *
 * 同一租约只能报告一次；重复报告返回 INVALID，代次不符返回 STALE。 */
DRMS_Result drms_control_report(DRMS_Token token, DRMS_Result result)
{
  uint32_t mask = crit_enter();
  for (uint32_t i = 0; i < DRMS_CONTROL_LEASES; ++i)
  {
    Lease *lease = &leases[i];
    if (lease->active && lease->operation_id == token.operation_id &&
        lease->generation == token.generation)
    {
      if (lease->reported || lease->generation != control_generation)
      {
        DRMS_Result status = lease->reported ? DRMS_INVALID : DRMS_STALE;
        crit_exit(mask);
        return status;
      }
      push_completion_locked(lease->source, lease->session, lease->request_id,
                             lease->operation_id, result, 0, 0);
      lease->reported = 1;
      crit_exit(mask);
      return DRMS_OK;
    }
  }
  crit_exit(mask);
  return DRMS_INVALID;
}

/* 归还租约，并据此更新资源状态。这是整个裁决器最关键的一段。
 *
 * quiescent_mask 的含义：调用方**能证明已经静止**的那些资源位。
 * 归还时逐位分流：
 *   · 能证明静止的 → 清掉 reserved 位，资源回到可用；
 *   · 不能证明静止的 → 置进 quarantined，**从此拒绝任何新占用**。
 *
 * 这就是"宁可隔离也不冒险"原则的落地。被隔离的资源只有显式 recover
 * 才能解除，不存在"等一会儿自己好"的可能。
 *
 * 注意必须先 report 再 release：未报告的租约不允许归还，
 * 否则结果会丢失，发起方永远等不到通知。 */
DRMS_Result drms_control_release(DRMS_Token token, uint32_t quiescent_mask)
{
  uint32_t mask = crit_enter();
  for (uint32_t i = 0; i < DRMS_CONTROL_LEASES; ++i)
  {
    Lease *lease = &leases[i];
    if (lease->active && lease->operation_id == token.operation_id &&
        lease->generation == token.generation && lease->reported)
    {
      uint32_t stale = lease->generation != control_generation;
      reserved_mask &= ~(lease->resources & quiescent_mask);
      quarantined_mask |= lease->resources & ~quiescent_mask;
      lease->active = 0;
      crit_exit(mask);
      return stale ? DRMS_STALE : DRMS_OK;
    }
  }
  crit_exit(mask);
  return DRMS_INVALID;
}

/* 归结操作：记结果、按静止证明分流资源、释放租约。一条龙完成。
 *
 * 大多数操作走这条路径，它等价于 report + release，但只进一次临界区。
 *
 * 未确认静止的部分转入隔离并**保持占用**——这部分资源在恢复之前谁都拿不到。
 * 代次不符（旧代次的迟到完成）只允许做清理，不允许启动新业务，
 * 返回 STALE 让调用方知道"这个结果已经过期了"。 */
DRMS_Result drms_control_complete(DRMS_Token token, DRMS_Result result,
                                  uint32_t quiescent_mask)
{
  uint32_t mask, stale = 0;
  Lease *lease = NULL;
  for (uint32_t i = 0; i < DRMS_CONTROL_LEASES; ++i)
  {
    if (leases[i].active && leases[i].operation_id == token.operation_id)
    {
      lease = &leases[i];
      break;
    }
  }
  if (!lease)
    return DRMS_INVALID;
  if (lease->generation != control_generation)
    stale = 1; /* 旧代次完成：只允许清理，不得启动新业务（R2） */
  mask = crit_enter();
  {
    /* 已确认静止部分归还；未确认部分转入隔离并保持占用（R4），恢复路径见 T3。 */
    reserved_mask &= ~(lease->resources & quiescent_mask);
    quarantined_mask |= lease->resources & ~quiescent_mask;
    push_completion_locked(lease->source, lease->session, lease->request_id,
                           lease->operation_id, result, quiescent_mask, stale);
    lease->active = 0;
  }
  crit_exit(mask);
  return stale ? DRMS_STALE : DRMS_OK;
}

/* 进入停止态：置位屏障、推进代次、取消所有已排队请求。
 *
 * 三个动作各有作用：
 *   · stopping=1        之后的新请求在 reserve 阶段就被拒；
 *   · 代次 +1           让所有在途操作意识到自己已经过期；
 *   · 清空请求队列      没轮到的请求一律按 CANCELLED 归结，不留悬案。
 *
 * 幂等：已经在停止态时直接返回，不重复推进代次——否则在途操作的代次
 * 会被推两次，收尾判定会乱。 */
void drms_control_stop(void)
{
  uint32_t mask = crit_enter();
  if (stopping)
  {
    crit_exit(mask);
    return; /* 幂等：代次不重复递增 */
  }
  stopping = 1;
  ++control_generation;
  /* 已排队请求全部取消；拥塞由完成环溢出计数承担。 */
  while (request_count)
  {
    QueuedRequest *queued = &requests[request_tail];
    DRMS_ControlRequest *request = &queued->request;
    push_completion_locked(request->source, request->session, request->request_id,
                           queued->operation_id, DRMS_CANCELLED, 0, 0);
    if (request->payload == config_payload) config_payload_in_use = 0;
    request_tail = (request_tail + 1U) % DRMS_CONTROL_REQUESTS;
    --request_count;
  }
  ++snapshot_sequence;
  crit_exit(mask);
}

/* 解除停止态。
 *
 * 前提条件很严格：所有租约必须已经释放（清理完成），否则返回 BUSY。
 * 这是有意为之——停止的意义就是让在途操作收尾，没收拾干净就恢复，
 * 等于把脏状态带进新一轮操作。 */
DRMS_Result drms_control_resume(void)
{
  uint32_t mask;
  for (uint32_t i = 0; i < DRMS_CONTROL_LEASES; ++i)
  {
    if (leases[i].active)
      return DRMS_BUSY; /* 清理未完成不得解除停止（R2） */
  }
  mask = crit_enter();
  if (!stopping)
  {
    crit_exit(mask);
    return DRMS_OK;
  }
  if (request_count)
  {
    crit_exit(mask);
    return DRMS_BUSY;
  }
  stopping = 0;
  ++snapshot_sequence;
  crit_exit(mask);
  return DRMS_OK;
}

/* 由某个持零资源租约的请求来解除停止。
 *
 * 与 drms_control_resume 的区别：这里要求"除自己之外没有任何活跃租约"，
 * 并校验令牌。用于 RESUME_MONITOR 这类"以请求形式触发恢复"的路径。
 *
 * 返回：OK 已恢复；BUSY 还有别的租约或队列没清空；INVALID 令牌对不上。 */
DRMS_Result drms_control_resume_for(DRMS_Token token)
{
  uint32_t mask = crit_enter();
  uint32_t found = 0;
  for (uint32_t i = 0; i < DRMS_CONTROL_LEASES; ++i)
  {
    Lease *lease = &leases[i];
    if (!lease->active) continue;
    if (lease->operation_id == token.operation_id && lease->generation == token.generation && !lease->resources)
      found = 1;
    else
    {
      crit_exit(mask);
      return DRMS_BUSY;
    }
  }
  if (!found || request_count)
  {
    crit_exit(mask);
    return found ? DRMS_BUSY : DRMS_INVALID;
  }
  stopping = 0;
  ++snapshot_sequence;
  crit_exit(mask);
  return DRMS_OK;
}

/* 控制线程的主推进函数：从请求队列头取出请求，申请资源，然后分派执行。
 *
 * max_requests 限制本轮最多处理几条，避免队列堆积时一次占住太久——
 * 主线程还要做别的事（排空采集、推进记录）。
 *
 * 处理一条请求的完整动作：
 *   1. 看停止态是否放行（只有少数操作能过）；
 *   2. 申请该操作需要的资源（失败则立即把 BUSY/CANCELLED 归结回去）；
 *   3. 成功则调用应用层注册的 dispatch_hook 真正执行；
 *   4. 执行完的归结由操作自己决定何时做（可能与执行异步）。
 *
 * 注意：请求在取出时就从队列里摘掉了，所以即使资源申请失败也不会被反复取出——
 * 失败会立刻作为结果通知发起方，不会让请求在队列里空转。 */
void drms_control_poll(uint32_t max_requests)
{
  while (max_requests--)
  {
    DRMS_ControlRequest request;
    DRMS_Token token;
    DRMS_Result result;
    uint32_t mask = crit_enter();
    if (!request_count || (stopping && !allowed_while_stopped(requests[request_tail].request.operation)))
    {
      crit_exit(mask);
      return;
    }
    QueuedRequest queued = requests[request_tail];
    request = queued.request;
    result = reserve_assigned(drms_control_resources_for(request.operation), &token, queued.operation_id,
                              request.operation == DRMS_OP_MSC_RELEASE || request.operation == DRMS_OP_RESUME_MONITOR ||
                              request.operation == DRMS_OP_SET_UTC || request.operation == DRMS_OP_END_RECORD,
                              allowed_while_stopped(request.operation));
    request_tail = (request_tail + 1U) % DRMS_CONTROL_REQUESTS;
    --request_count;
    if (result != DRMS_ACCEPTED)
    {
      if (request.payload == config_payload) config_payload_in_use = 0;
      push_completion_locked(request.source, request.session, request.request_id,
                             queued.operation_id, result, 0, 0);
      crit_exit(mask);
      continue;
    }
    /* 租约登记请求关联，complete 时随完成记录带回。 */
    uint32_t leased = 0;
    for (uint32_t i = 0; i < DRMS_CONTROL_LEASES; ++i)
    {
      if (leases[i].active && leases[i].operation_id == token.operation_id)
      {
        leases[i].source = request.source;
        leases[i].session = request.session;
        leases[i].request_id = request.request_id;
        leased = leases[i].resources;
        break;
      }
    }
    crit_exit(mask);
    if (!dispatch_hook)
    {
      mask = crit_enter();
      if (request.payload == config_payload) config_payload_in_use = 0;
      crit_exit(mask);
      (void)drms_control_complete(token, DRMS_UNSUPPORTED, leased);
      continue;
    }
    result = dispatch_hook(&token, &request);
    mask = crit_enter();
    if (request.payload == config_payload) config_payload_in_use = 0;
    crit_exit(mask);
    if (result != DRMS_ACCEPTED)
      /* 投递失败回滚尚未启动的预占：工作从未到达后端，租约整体视为静止。 */
      (void)drms_control_complete(token, result, leased);
  }
}

/* 从完成队列取走最多 max 条通知。out 为 NULL 时只消费不拷贝（用于丢弃）。
 *
 * 返回实际取走的条数。发起方靠它拿到最终结果；如果一直不取，
 * 队列满后会丢最旧的（见 push_completion_locked）。 */
uint32_t drms_control_collect(DRMS_ControlCompletion *out, uint32_t max)
{
  uint32_t mask = crit_enter();
  uint32_t n = 0;
  while (n < max && completion_count)
  {
    if (out)
      out[n] = completions[completion_head];
    completion_head = (completion_head + 1U) % DRMS_CONTROL_COMPLETIONS;
    --completion_count;
    ++completions_consumed;
    ++n;
  }
  crit_exit(mask);
  return n;
}

/* 取一份自洽的裁决器状态快照，供业务层判断"现在能不能做事"。
 *
 * 全部字段在同一临界区内取出：若是分几次读，就可能出现"看到停止位为 0、
 * 但代次已经变了"这种自相矛盾的组合，据此做的判断会错。
 *
 * 其中 quarantined_mask 最需要关注——非 0 意味着有资源处于隔离态，
 * 相关操作在此清掉之前都不可能成功。 */
void drms_control_get_snapshot(DRMS_ControlSnapshot *out)
{
  if (!out)
    return;
  uint32_t mask = crit_enter();
  uint32_t active = 0;
  for (uint32_t i = 0; i < DRMS_CONTROL_LEASES; ++i)
    active += leases[i].active ? 1u : 0u;
  out->snapshot_sequence = snapshot_sequence;
  out->stopping = stopping;
  out->generation = control_generation;
  out->reserved_mask = reserved_mask;
  out->quarantined_mask = quarantined_mask;
  out->leases_active = active;
  out->requests_queued = request_count;
  out->completion_count = completion_count;
  if (completion_count)
    out->last_completion = completions[(completion_head + completion_count - 1U) %
                                       DRMS_CONTROL_COMPLETIONS];
  else
    memset(&out->last_completion, 0, sizeof(out->last_completion));
  out->requests_accepted = requests_accepted;
  out->requests_rejected = requests_rejected;
  out->completions_overflow = completions_overflow;
  out->completions_consumed = completions_consumed;
  ++snapshot_sequence;
  crit_exit(mask);
}
