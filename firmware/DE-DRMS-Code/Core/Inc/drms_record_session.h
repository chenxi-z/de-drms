#ifndef DRMS_RECORD_SESSION_H
#define DRMS_RECORD_SESSION_H
/* 记录会话内存边界状态机（T2a/C1）。纯逻辑模块：不包含 HAL/RTOS/FileX，
 * 由处理上下文唯一驱动（除 end_get/end_ack 属存储上下文）。
 * 三种位置：sample_seq=观察到的 DRDY 64 位序号；raw_ticket=原始环发布累计；
 * log_ticket=记录环发布累计——三者不可混比。会话窗口 [B,E)：classify 以
 * raw_ticket 定归属，样本区间为 [B.sample_next, E.sample_next)。
 * END 经单槽发布：存储 end_get 取走、end_ack 确认前不得被下一次记录覆盖。 */
#include "drms_architecture_contract.h"

/* 外部状态视图。第一帧记录前必须呈现 STARTING，不得提前报告 RECORDING。 */
typedef enum {
  DRMS_RECORD_IDLE = 0,
  DRMS_RECORD_STARTING = 1,
  DRMS_RECORD_RECORDING = 2,
  DRMS_RECORD_FINALIZING = 3 /* END 已发布，等待存储 ack */
} DRMS_RecordState;

/* 单帧归属裁决（处理循环按此分发）。 */
typedef enum {
  DRMS_RECORD_SKIP = 0,    /* 边界前积压：丢弃，不入记录 */
  DRMS_RECORD_MONITOR = 1, /* 边界后/失败后：仅监测 */
  DRMS_RECORD_RECORD = 2   /* 属于本次记录：入记录环 */
} DRMS_RecordVerdict;

typedef struct {
  uint32_t state;                /* DRMS_RecordState */
  uint32_t barrier;              /* 1 = 处理循环本轮不得 pop 原始环 */
  uint32_t stop_pending;         /* 已请求停止，等待一致末边界 E */
  uint32_t acquisition_generation;
  uint64_t record_id;
  DRMS_Token token;
  uint64_t samples_recorded;
  uint64_t quality_bad;
  uint64_t log_dropped;
  uint64_t capture_lost;         /* E 已到达后的本次增量（运行诊断） */
  uint32_t unknown_loss;         /* 本次存在未知损失 */
  uint32_t end_pending;          /* END 槽占用（未 ack） */
  DRMS_Result end_reason;        /* 已发布 END 的原因 */
} DRMS_RecordSessionSnapshot;

void drms_record_session_init(void);

/* 边界等待期限（START/STOP 共用）。默认 1000 ms；测试可调小。 */
void drms_record_session_configure(uint32_t boundary_wait_ms);

/* 处理上下文：预占成功后开启 STARTING；END 槽未 ack 时拒绝（BUSY）。 */
DRMS_Result drms_record_prepare(DRMS_Token token, uint64_t record_id);

/* 处理上下文：文件就绪且一致边界 B 已捕获后调用。迟到/代次不符拒绝。 */
DRMS_Result drms_record_ready(DRMS_Token token, DRMS_CaptureBoundary begin);

/* 处理上下文：进入停止屏障（等待 E）。屏障期间不 pop 原始环。 */
void drms_record_session_request_stop(void);

/* 处理上下文：一致末边界 E 已捕获后调用；首次生效，重复调用保持首次 E。 */
DRMS_Result drms_record_stop_at(DRMS_Token token, DRMS_CaptureBoundary end_exclusive);

/* 处理上下文：取消本会话（STARTING/记录中皆可），reason 报入 END。 */
void drms_record_session_cancel(DRMS_Token token, DRMS_Result reason);

/* 处理循环查询：true = 屏障期，本轮不得 pop 原始环（定时/取消事件照常处理）。 */
uint32_t drms_record_session_barrier(void);

/* 处理循环：对 pop 出的帧按 raw_ticket 裁决归属。 */
DRMS_RecordVerdict drms_record_session_classify(uint64_t raw_ticket);

/* 处理循环：RECORD 帧回报。frame_seq_low 为帧内低 32 位序号（会话端按锚点
 * 扩展 64 位，跨度不可证明时 LOSS_UNKNOWN 并终止本次记录）；
 * enqueue_ok=0 时计入 log_dropped 并终止本次记录（数据环满规则）。 */
void drms_record_session_note_recorded(uint32_t frame_seq_low, uint32_t quality_bad,
                                       uint32_t enqueue_ok);

/* 处理循环：同步记录环当前发布水位（END 的 ring_end）。 */
void drms_record_session_note_log_ticket(uint64_t ring_end_log_ticket);

/* 处理循环：回报消费水位；推进到 E 后自动发布 END。 */
void drms_record_session_note_consumed(uint64_t next_raw_ticket);

/* 处理循环周期调用（含屏障期）：监督边界等待期限与原始环水位；
 * 超时/环满 → 以 INCOMPLETE/TIMEOUT 收尾，不猜测边界。 */
void drms_record_session_poll(uint64_t now_ms, uint32_t raw_used, uint32_t raw_capacity);

/* 存储上下文：取走已发布 END；无 END 返回 DRMS_EMPTY。 */
DRMS_Result drms_record_end_get(DRMS_End *out);

/* 存储上下文：确认 END 已处理；token 不符返回 STALE；确认后会话回到 IDLE。 */
DRMS_Result drms_record_end_ack(DRMS_Token token, DRMS_Result result);

/* 一致快照（任意上下文只读）。 */
void drms_record_session_get_snapshot(DRMS_RecordSessionSnapshot *out);

#endif /* DRMS_RECORD_SESSION_H */
