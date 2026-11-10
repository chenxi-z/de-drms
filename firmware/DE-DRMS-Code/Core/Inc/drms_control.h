#ifndef DRMS_CONTROL_H
#define DRMS_CONTROL_H
/* 原子资源裁决器（T1/C2/C5）。控制上下文私有：reserve/complete/stop/resume/
 * poll/collect 只允许控制任务调用；其他任务只能 submit 与 get_snapshot（只读）。
 * 状态写入上下文：init（启动）、submit（任意线程，短临界区入队）、
 * poll/complete/stop/resume/collect（仅控制任务）。 */
#include "drms_architecture_contract.h"

/* 完成记录：控制任务经 complete 写入完成环；保留操作编号、结果与已确认
 * 静止掩码，并携带请求关联（来源/会话/请求编号）。stale=1 表示该完成属于
 * 旧控制代次，只作清理依据，不得触发新业务。 */
typedef struct {
  uint64_t operation_id;
  uint32_t source;      /* DRMS_RequestSource */
  uint32_t session;
  uint64_t request_id;
  DRMS_Result result;
  uint32_t quiescent_mask;
  uint32_t stale;
  uint32_t phase; /* 0 queued, 1 dispatched, 2 finished */
} DRMS_ControlCompletion;

/* 只读快照（短临界区复制）。last_completion 仅在 completion_count>0 时有效，
 * 为最新一条完成记录；完整历史经 collect（仅控制任务）排空。 */
typedef struct {
  uint32_t snapshot_sequence;
  uint32_t stopping;
  uint32_t generation;
  uint32_t reserved_mask;
  uint32_t quarantined_mask;
  uint32_t leases_active;
  uint32_t requests_queued;
  uint32_t completion_count;
  DRMS_ControlCompletion last_completion;
  uint64_t requests_accepted;
  uint64_t requests_rejected;
  uint64_t completions_overflow;
  uint64_t completions_consumed;
} DRMS_ControlSnapshot;

/* 工作投递钩子：poll 在租约取得成功后调用一次。返回 ACCEPTED 表示业务模块
 * 已接收该操作（最终结果经 complete 归还）；返回其他值则裁决器立即回滚
 * 租约并写完成记录。由 init 一次注入；不得在运行期更换。 */
typedef DRMS_Result (*DRMS_ControlDispatch)(const DRMS_Token *token,
                                            const DRMS_ControlRequest *request);

void drms_control_init(DRMS_ControlDispatch dispatch);

/* 复制请求入有界队列。同步返回：ACCEPTED=已入队、BUSY=队列满、
 * INVALID=请求非法、CANCELLED=停止中拒绝。 */
DRMS_Result drms_control_submit(const DRMS_ControlRequest *request);
/* As above, but returns the boot-scoped operation ID upon queue admission.
 * That ID remains queryable while queued, dispatched, or recently completed. */
DRMS_Result drms_control_submit_identified(const DRMS_ControlRequest *request, uint64_t *operation_id);
/* Dedicated stop latch; independent of normal queue and resource leases. */
DRMS_Result drms_control_safe_stop_submit(const DRMS_ControlRequest *request, uint64_t *operation_id);
uint32_t drms_control_safe_stop_take(void); /* control owner only */
DRMS_Result drms_control_safe_stop_finish(DRMS_Result result); /* control owner only */

/* 控制任务：本轮至多处理 max_requests 条队列请求。每条依次
 * reserve(op_resources) → 失败写完成记录；成功则 dispatch → 拒绝即回滚。 */
void drms_control_poll(uint32_t max_requests);

/* 一次性全量检查并预占资源集合（UPDATE_EXCLUSIVE 自动展开为全部）。
 * 成功返回 ACCEPTED 并写 token；失败 BUSY/INVALID/CANCELLED，无部分占用。
 * 仅控制任务调用。 */
DRMS_Result drms_control_reserve(uint32_t resources, DRMS_Token *out);

/* 先发布操作结果，资源仍保持占用。只允许控制任务调用。 */
DRMS_Result drms_control_report(DRMS_Token token, DRMS_Result result);

/* 已报告结果的租约按已确认静止的资源释放，其余隔离。 */
DRMS_Result drms_control_release(DRMS_Token token, uint32_t quiescent_mask);

/* 按 token 释放租约：quiescent_mask 覆盖的资源归还，未覆盖的转入隔离
 * （保持占用、阻断新所有者，恢复路径见 T3）。写完成记录（含请求关联与
 * quiescent_mask）。代次不匹配返回 STALE 并仅做清理；无此租约返回 INVALID。
 * 仅控制任务调用。 */
DRMS_Result drms_control_complete(DRMS_Token token, DRMS_Result result,
                                  uint32_t quiescent_mask);

/* 安全停止：置 STOPPING、控制代次 +1、队列内请求全部取消并写 CANCELLED
 * 完成记录；重复调用幂等（代次不再递增）。活动租约保持占用，等待各自
 * complete 清理；停止期间 reserve/submit 返回 CANCELLED。仅控制任务调用。 */
void drms_control_stop(void);

/* 解除 STOPPING：要求无活动租约（隔离资源允许保留）。成功返回 OK，否则
 * BUSY。不自动重启任何业务。仅控制任务调用。 */
DRMS_Result drms_control_resume(void);
/* Resume initiated by a zero-resource control operation, excluding its own lease. */
DRMS_Result drms_control_resume_for(DRMS_Token token);

/* 控制任务：从完成环排空至多 max 条完成记录（ oldest first ），返回条数。
 * 普通查询不得调用本函数。 */
uint32_t drms_control_collect(DRMS_ControlCompletion *out, uint32_t max);

/* Query any in-progress operation or the latest eight completed operations.
 * Results do not consume the completion queue. STALE denotes an evicted ID;
 * INVALID denotes an ID not allocated in this boot or a null destination. */
DRMS_Result drms_control_get_operation(uint64_t operation_id, DRMS_ControlCompletion *out);

/* 一致快照（任意上下文，只读）：短临界区复制，不消费完成结果。 */
void drms_control_get_snapshot(DRMS_ControlSnapshot *out);

/* 操作 → 资源集合的唯一定义（含 UPDATE 展开）；纯查询，供测试与审查。 */
uint32_t drms_control_resources_for(DRMS_Operation operation);

#endif /* DRMS_CONTROL_H */
