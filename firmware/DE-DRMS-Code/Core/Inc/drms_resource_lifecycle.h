#ifndef DRMS_RESOURCE_LIFECYCLE_H
#define DRMS_RESOURCE_LIFECYCLE_H
/* 资源生命周期（T3/R4/C5）：IDLE → ACTIVE → CANCELLING → QUIESCENT；
 * 超时一次有界中止/恢复尝试后仍无法确认静止 → QUARANTINED（保持占用）。
 * 生命周期模块不包含 HAL：硬件后端经钩子表注入，各自提供有界
 * abort / 静止证据 probe / 有界 recover 的显式结果；
 * "静止证据"由后端定义并在注释中写明来源（不允许以软件 busy=0 冒充）。
 * 所有调用仅限控制上下文（get_snapshot 只读除外）。 */
#include "drms_architecture_contract.h"

#define DRMS_RESOURCE_COUNT 5 /* 资源位总数 */

typedef enum {
  DRMS_RSC_IDLE = 0,
  DRMS_RSC_ACTIVE = 1,      /* 业务持有（token 匹配） */
  DRMS_RSC_CANCELLING = 2,  /* 取消中：等静止证据或期限 */
  DRMS_RSC_QUIESCENT = 3,   /* 静止已确认：可归还 */
  DRMS_RSC_QUARANTINED = 4  /* 无法证明静止：隔离，不接收新工作 */
} DRMS_ResourceState;

typedef struct {
  /* 有界中止。返回 ACCEPTED=已停止且静止证据成立；BUSY=已请求停止待再确认；
   * 其他=中止失败（等待期限路径处理）。不得无界等待。 */
  DRMS_Result (*abort)(void);
  /* 静止证据查询。ACCEPTED=外设停止且回调不再使用旧缓冲；BUSY=未静止。 */
  DRMS_Result (*probe_quiescent)(void);
  /* 有界恢复（仅 QUARANTINED 后由控制显式调用）。ACCEPTED=回到可用。 */
  DRMS_Result (*recover)(void);
} DRMS_ResourceBackend;

void drms_resource_init(const DRMS_ResourceBackend *backends /* [DRMS_RESOURCE_COUNT]，NULL 表项=该资源不支持取消 */);

/* 取消总期限（ms）。默认占位值未经验证：实测定值在 T7/T8 依据后端
 * 驱动阻塞上限给出；测试注入时钟并配置小超时。 */
void drms_resource_configure(uint32_t resource, uint32_t cancel_timeout_ms);

/* 控制取得租约后登记激活（多位于一次调用内全部成功或全部失败）。 */
DRMS_Result drms_resource_activate(uint32_t resources, DRMS_Token token);

/* 取消：ACTIVE+CANCELLED 语义入口。进入 CANCELLING 并立即做一次有界中止
 * 尝试；立即可确认静止则直接 QUIESCENT。token 不符/状态不符返回 STALE；
 * 重复取消返回 NO_CHANGE。 */
DRMS_Result drms_resource_cancel(uint32_t resource, DRMS_Token token, uint64_t now_ms);

/* 所有者确认静止（token 匹配）：ACTIVE/CANCELLING → QUIESCENT。 */
DRMS_Result drms_resource_quiescent(uint32_t resource, DRMS_Token token);

/* 归还：QUIESCENT → IDLE（缓冲交还）。仅静止后允许。 */
DRMS_Result drms_resource_release(uint32_t resource, DRMS_Token token);

/* 隔离后的一次性有界恢复尝试；失败保持 QUARANTINED，不自动重试。 */
DRMS_Result drms_resource_recover(uint32_t resource, uint64_t now_ms);

/* 控制任务周期调用：CANCELLING 资源查静止证据；到期执行一次
 * 中止/恢复尝试，仍无法确认 → QUARANTINED。 */
void drms_resource_tick(uint64_t now_ms);

typedef struct {
  uint32_t snapshot_sequence;
  uint8_t state[DRMS_RESOURCE_COUNT];   /* DRMS_ResourceState */
  DRMS_Token token[DRMS_RESOURCE_COUNT];
  uint64_t deadline_ms[DRMS_RESOURCE_COUNT];
  uint32_t abort_attempts[DRMS_RESOURCE_COUNT];
  uint32_t recover_attempts[DRMS_RESOURCE_COUNT];
  uint64_t quarantined_events;
  uint64_t timeouts;
} DRMS_ResourceSnapshot;

void drms_resource_get_snapshot(DRMS_ResourceSnapshot *out);

#endif /* DRMS_RESOURCE_LIFECYCLE_H */
