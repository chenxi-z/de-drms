/*****************************************************************************
 * 文件：drms_resource_lifecycle.c
 * 职责：资源后端的注册与统一调度——让不同资源（采集、存储、USB）能用同一套接口
 *       被"中止/探测/恢复"。
 *
 * 为什么需要这层抽象：
 *   上层（drms_control）只知道"要停这个东西"，不该关心它是 ADC 还是 SD 卡。
 *   把每种资源的中止/恢复逻辑各自封装成后端，上层就能用统一的方式处理，
 *   而不必为每种资源写一套分支。
 *
 * 三个动作的语义差异很重要：
 *   abort    中止并确认已静止。返回 ACCEPTED 才代表"确实停了"。
 *   probe    只查询是否静止，不改变任何状态。
 *   recover  从隔离态恢复。隔离意味着"无法证明静止"，恢复时要重新验证。
 *
 * 这个"能否证明静止"的区分贯穿整个可靠性设计：
 *   能证明 → 资源可以复用；不能证明 → 隔离，直到显式恢复。
 *****************************************************************************/

#include "drms_resource_lifecycle.h"
#include <string.h>

/* 生命周期模块：不包含 HAL。所有状态写入在控制上下文；snapshot 短临界区复制。
 * 默认期限是未经验证的占位值，仅保证"有界"；真实取值在 T7/T8 依据各后端
 * 已验证的驱动阻塞上限给出（R4：不在此虚构毫秒常数）。 */
#define DRMS_RESOURCE_TIMEOUT_DEFAULT_MS 1000u

static DRMS_ResourceBackend backends[DRMS_RESOURCE_COUNT];
static DRMS_ResourceState states[DRMS_RESOURCE_COUNT];
static DRMS_Token tokens[DRMS_RESOURCE_COUNT];
static uint64_t deadlines_ms[DRMS_RESOURCE_COUNT];
static uint32_t timeouts_ms[DRMS_RESOURCE_COUNT];
static uint32_t abort_attempts[DRMS_RESOURCE_COUNT];
static uint32_t recover_attempts[DRMS_RESOURCE_COUNT];
static uint64_t quarantined_events, timeouts;
static uint32_t snapshot_sequence;

static uint32_t resource_index(uint32_t resource)
{
  for (uint32_t i = 0; i < DRMS_RESOURCE_COUNT; ++i)
  {
    if (resource & (1u << i))
      return i;
  }
  return DRMS_RESOURCE_COUNT;
}

void drms_resource_init(const DRMS_ResourceBackend *table)
{
  if (table)
    memcpy(backends, table, sizeof(backends));
  else
    memset(backends, 0, sizeof(backends));
  memset(states, 0, sizeof(states));
  memset(tokens, 0, sizeof(tokens));
  memset(deadlines_ms, 0, sizeof(deadlines_ms));
  for (uint32_t i = 0; i < DRMS_RESOURCE_COUNT; ++i)
  {
    timeouts_ms[i] = DRMS_RESOURCE_TIMEOUT_DEFAULT_MS;
    abort_attempts[i] = recover_attempts[i] = 0;
  }
  quarantined_events = timeouts = 0;
  snapshot_sequence = 0;
}

void drms_resource_configure(uint32_t resource, uint32_t cancel_timeout_ms)
{
  if (!resource || (resource & (resource - 1u)))
    return;
  uint32_t index = resource_index(resource);
  if (index >= DRMS_RESOURCE_COUNT || !cancel_timeout_ms)
    return;
  timeouts_ms[index] = cancel_timeout_ms;
}

DRMS_Result drms_resource_activate(uint32_t resources, DRMS_Token token)
{
  if (resources & ~(uint32_t)DRMS_RES_ALL || !resources)
    return DRMS_INVALID;
  for (uint32_t i = 0; i < DRMS_RESOURCE_COUNT; ++i)
  {
    if (!(resources & (1u << i)))
      continue;
    if (states[i] != DRMS_RSC_IDLE)
      return DRMS_BUSY; /* 隔离/在途/未归还：拒绝新请求 */
  }
  for (uint32_t i = 0; i < DRMS_RESOURCE_COUNT; ++i)
  {
    if (!(resources & (1u << i)))
      continue;
    states[i] = DRMS_RSC_ACTIVE;
    tokens[i] = token;
  }
  return DRMS_ACCEPTED;
}

DRMS_Result drms_resource_cancel(uint32_t resource, DRMS_Token token, uint64_t now_ms)
{
  if (resource & ~(uint32_t)DRMS_RES_ALL || !resource || (resource & (resource - 1u)))
    return DRMS_INVALID; /* 单资源操作 */
  uint32_t i = resource_index(resource);
  if (i >= DRMS_RESOURCE_COUNT)
    return DRMS_INVALID;
  if (tokens[i].operation_id != token.operation_id ||
      tokens[i].generation != token.generation)
    return DRMS_STALE;
  if (states[i] == DRMS_RSC_CANCELLING || states[i] == DRMS_RSC_QUIESCENT ||
      states[i] == DRMS_RSC_QUARANTINED)
    return DRMS_NO_CHANGE; /* 重复取消幂等 */
  if (states[i] != DRMS_RSC_ACTIVE)
    return DRMS_STALE;
  if (!backends[i].abort)
    return DRMS_UNSUPPORTED; /* 该资源无取消后端，保持 ACTIVE */
  states[i] = DRMS_RSC_CANCELLING;
  deadlines_ms[i] = now_ms + timeouts_ms[i];
  ++abort_attempts[i];
  DRMS_Result result = backends[i].abort(); /* 立即一次有界中止尝试 */
  if (result == DRMS_ACCEPTED)
    states[i] = DRMS_RSC_QUIESCENT; /* 中止时即确认静止证据 */
  return DRMS_ACCEPTED;
}

DRMS_Result drms_resource_quiescent(uint32_t resource, DRMS_Token token)
{
  if (resource & ~(uint32_t)DRMS_RES_ALL || !resource || (resource & (resource - 1u)))
    return DRMS_INVALID;
  uint32_t i = resource_index(resource);
  if (i >= DRMS_RESOURCE_COUNT)
    return DRMS_INVALID;
  if (tokens[i].operation_id != token.operation_id ||
      tokens[i].generation != token.generation)
    return DRMS_STALE;
  if (states[i] != DRMS_RSC_ACTIVE && states[i] != DRMS_RSC_CANCELLING &&
      states[i] != DRMS_RSC_QUIESCENT)
    return DRMS_STALE;
  states[i] = DRMS_RSC_QUIESCENT; /* 已静止时幂等确认 */
  return DRMS_OK;
}

DRMS_Result drms_resource_release(uint32_t resource, DRMS_Token token)
{
  if (resource & ~(uint32_t)DRMS_RES_ALL || !resource || (resource & (resource - 1u)))
    return DRMS_INVALID;
  uint32_t i = resource_index(resource);
  if (i >= DRMS_RESOURCE_COUNT)
    return DRMS_INVALID;
  if (tokens[i].operation_id != token.operation_id ||
      tokens[i].generation != token.generation)
    return DRMS_STALE;
  if (states[i] != DRMS_RSC_QUIESCENT)
    return DRMS_STALE; /* 未证明静止不得归还 */
  states[i] = DRMS_RSC_IDLE;
  tokens[i].operation_id = 0;
  tokens[i].generation = 0;
  return DRMS_OK;
}

DRMS_Result drms_resource_recover(uint32_t resource, uint64_t now_ms)
{
  (void)now_ms;
  if (resource & ~(uint32_t)DRMS_RES_ALL || !resource || (resource & (resource - 1u)))
    return DRMS_INVALID;
  uint32_t i = resource_index(resource);
  if (i >= DRMS_RESOURCE_COUNT)
    return DRMS_INVALID;
  if (states[i] != DRMS_RSC_QUARANTINED)
    return DRMS_STALE;
  if (!backends[i].recover)
    return DRMS_UNSUPPORTED;
  ++recover_attempts[i];
  if (backends[i].recover() != DRMS_ACCEPTED)
    return DRMS_IO_ERROR; /* 保持隔离：失败不循环重启，仅显式重试 */
  states[i] = DRMS_RSC_IDLE;
  tokens[i].operation_id = 0;
  tokens[i].generation = 0;
  return DRMS_OK;
}

void drms_resource_tick(uint64_t now_ms)
{
  for (uint32_t i = 0; i < DRMS_RESOURCE_COUNT; ++i)
  {
    if (states[i] != DRMS_RSC_CANCELLING)
      continue;
    if (backends[i].probe_quiescent &&
        backends[i].probe_quiescent() == DRMS_ACCEPTED)
    {
      states[i] = DRMS_RSC_QUIESCENT;
      continue;
    }
    if ((int64_t)(now_ms - deadlines_ms[i]) < 0)
      continue;
    /* 期限到达：一次有界中止/恢复尝试；仍无法确认 → 隔离并保留固定槽 */
    ++timeouts;
    ++abort_attempts[i];
    DRMS_Result result = backends[i].abort ? backends[i].abort() : DRMS_UNSUPPORTED;
    if (result == DRMS_ACCEPTED)
      states[i] = DRMS_RSC_QUIESCENT;
    else
    {
      states[i] = DRMS_RSC_QUARANTINED;
      ++quarantined_events;
    }
  }
  ++snapshot_sequence;
}

void drms_resource_get_snapshot(DRMS_ResourceSnapshot *out)
{
  if (!out)
    return;
  out->snapshot_sequence = snapshot_sequence;
  for (uint32_t i = 0; i < DRMS_RESOURCE_COUNT; ++i)
  {
    out->state[i] = (uint8_t)states[i];
    out->token[i] = tokens[i];
    out->deadline_ms[i] = deadlines_ms[i];
    out->abort_attempts[i] = abort_attempts[i];
    out->recover_attempts[i] = recover_attempts[i];
  }
  out->quarantined_events = quarantined_events;
  out->timeouts = timeouts;
}
