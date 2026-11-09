#ifndef DRMS_BASELINE_H
#define DRMS_BASELINE_H
/* R0 建立的流式统计（T6/R7）：有效电阻样本的均值/方差/计数/时长。
 * 质量规则参数显式输入；无合格参数 → UNCONFIGURED。输出候选不直接保存，
 * 提交由控制模块协调（commit_baseline）。 */
#include <stdint.h>

typedef struct {
  uint32_t min_count;        /* 最少样本数；0 = 未配置 */
  uint64_t min_duration_us;  /* 最短覆盖时长（名义时间） */
  double stability_rel;      /* 样本标准差/均值 上限（如 0.001）；<0 = 未配置 */
  /* 流式统计 */
  uint64_t count;
  uint64_t duration_us;
  double mean, m2;           /* Welford */
} DRMS_BaselineContext;

void drms_baseline_configure(DRMS_BaselineContext *ctx, uint32_t min_count,
                             uint64_t min_duration_us, double stability_rel);
void drms_baseline_reset(DRMS_BaselineContext *ctx);
void drms_baseline_feed(DRMS_BaselineContext *ctx, double ohms, uint64_t sample_dt_us);

/* 候选评估：OK=给出 mean/stddev（调用方可再叠加稳定性判断之外的策略）；
 * NOT_READY=样本不足；UNCONFIGURED=未配置合格参数。 */
int drms_baseline_candidate(const DRMS_BaselineContext *ctx, double *mean, double *stddev);

#endif /* DRMS_BASELINE_H */
