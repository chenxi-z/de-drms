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
static DRMS_ControlCompletion completions[DRMS_CONTROL_COMPLETIONS];
static DRMS_ControlCompletion history[DRMS_CONTROL_HISTORY];
static uint32_t history_head, history_count;
static uint32_t request_head, request_count, request_tail;
static uint32_t completion_head, completion_count;
static uint32_t reserved_mask, quarantined_mask;
static uint32_t stopping, control_generation, snapshot_sequence;
static uint64_t next_operation_id;
static uint64_t requests_accepted, requests_rejected;
static uint64_t completions_overflow, completions_consumed;

static uint32_t crit_enter(void)
{
  uint32_t mask = __get_PRIMASK();
  __disable_irq();
  return mask;
}

static void crit_exit(uint32_t mask) { __set_PRIMASK(mask); }

uint32_t drms_control_resources_for(DRMS_Operation operation)
{
  switch (operation)
  {
    case DRMS_OP_RECORD: return DRMS_RES_ACQUISITION_CONFIG | DRMS_RES_RECORD_SESSION |
                                DRMS_RES_TF_ACCESS;
    case DRMS_OP_MSC_EXPORT: return DRMS_RES_TF_ACCESS;
    case DRMS_OP_FILE_DOWNLOAD: return DRMS_RES_TF_ACCESS;
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

static void push_completion_locked(uint32_t source, uint32_t session, uint64_t request_id,
                                   uint64_t operation_id, DRMS_Result result,
                                   uint32_t quiescent_mask, uint32_t stale)
{
  DRMS_ControlCompletion *slot;
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

void drms_control_init(DRMS_ControlDispatch dispatch)
{
  uint32_t mask = crit_enter();
  dispatch_hook = dispatch;
  memset(leases, 0, sizeof(leases));
  memset(requests, 0, sizeof(requests));
  memset(completions, 0, sizeof(completions));
  memset(history, 0, sizeof(history));
  history_head = history_count = 0;
  request_head = request_count = request_tail = 0;
  completion_head = completion_count = 0;
  reserved_mask = quarantined_mask = 0;
  stopping = 0;
  control_generation = 1;
  snapshot_sequence = 0;
  next_operation_id = 1;
  requests_accepted = requests_rejected = 0;
  completions_overflow = completions_consumed = 0;
  crit_exit(mask);
}

DRMS_Result drms_control_get_operation(uint64_t operation_id, DRMS_ControlCompletion *out)
{
  if (!operation_id || !out)
    return DRMS_INVALID;
  uint32_t mask = crit_enter();
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

DRMS_Result drms_control_submit(const DRMS_ControlRequest *request)
{
  return drms_control_submit_identified(request, NULL);
}

DRMS_Result drms_control_submit_identified(const DRMS_ControlRequest *request, uint64_t *operation_id)
{
  uint32_t mask;
  QueuedRequest *slot;
  if (operation_id) *operation_id = 0;
  if (!request || request->operation <= DRMS_OP_NONE || request->operation > DRMS_OP_MSC_RELEASE)
    return DRMS_INVALID;
  mask = crit_enter();
  if (stopping)
  {
    crit_exit(mask);
    ++requests_rejected;
    return DRMS_CANCELLED;
  }
  if (request_count == DRMS_CONTROL_REQUESTS || !next_operation_id)
  {
    crit_exit(mask);
    ++requests_rejected;
    return DRMS_BUSY;
  }
  slot = &requests[request_head];
  slot->request = *request;
  slot->operation_id = next_operation_id++;
  if (operation_id) *operation_id = slot->operation_id;
  request_head = (request_head + 1U) % DRMS_CONTROL_REQUESTS;
  ++request_count;
  ++requests_accepted;
  crit_exit(mask);
  return DRMS_ACCEPTED;
}

static DRMS_Result reserve_assigned(uint32_t resources, DRMS_Token *out, uint64_t assigned_id, uint32_t allow_empty)
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
  if (stopping)
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

DRMS_Result drms_control_reserve(uint32_t resources, DRMS_Token *out)
{
  return reserve_assigned(resources, out, 0, 0);
}

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
    request_tail = (request_tail + 1U) % DRMS_CONTROL_REQUESTS;
    --request_count;
  }
  ++snapshot_sequence;
  crit_exit(mask);
}

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

void drms_control_poll(uint32_t max_requests)
{
  while (max_requests--)
  {
    DRMS_ControlRequest request;
    DRMS_Token token;
    DRMS_Result result;
    uint32_t mask = crit_enter();
    if (!request_count || stopping)
    {
      crit_exit(mask);
      return;
    }
    QueuedRequest queued = requests[request_tail];
    request = queued.request;
    result = reserve_assigned(drms_control_resources_for(request.operation), &token, queued.operation_id,
                              request.operation == DRMS_OP_MSC_RELEASE);
    request_tail = (request_tail + 1U) % DRMS_CONTROL_REQUESTS;
    --request_count;
    if (result != DRMS_ACCEPTED)
    {
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
      (void)drms_control_complete(token, DRMS_UNSUPPORTED, leased);
      continue;
    }
    result = dispatch_hook(&token, &request);
    if (result != DRMS_ACCEPTED)
      /* 投递失败回滚尚未启动的预占：工作从未到达后端，租约整体视为静止。 */
      (void)drms_control_complete(token, result, leased);
  }
}

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
