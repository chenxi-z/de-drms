#ifndef DRMS_CLASSIFIER_H
#define DRMS_CLASSIFIER_H
/* 区间映射/回差/确认（T6/C6）。区间表为有序不重叠 [lo,hi)，末项允许闭合上端；
 * 退出回差 h 仅扩展已确认区间的保持范围 [lo-h,hi+h]（h=0 严格端点），
 * 不改变表的物理端点。跨级直接选择目标区间。确认计时以名义样本时间
 * 累计（连续有效样本），候选变化即重新计时，confirm_us=0 当帧确认。 */
#include <stdint.h>
#include "drms_architecture_contract.h"

typedef struct {
  DRMS_MonitorInterval intervals[DRMS_MONITOR_INTERVALS_MAX];
  uint8_t interval_count;
  uint64_t confirm_us;
  int16_t confirmed;        /* -1 = 无 */
  int16_t candidate;        /* -1 = 无 */
  uint64_t candidate_time_us; /* 候选连续有效累计（名义时间） */
} DRMS_ClassifierContext;

void drms_classifier_configure(DRMS_ClassifierContext *ctx, const DRMS_MonitorConfig *config);
void drms_classifier_reset(DRMS_ClassifierContext *ctx);

/* 输入滤波后的 R/R0 比值与名义样本时间步长；结果写入 state/observed/
 * candidate/confirmed/hysteresis_hold（枚举与 -1 约定见 C6）。
 * observed_index 可为 NULL（WARMUP/UNCONFIGURED 等场景）。 */
void drms_classifier_step(DRMS_ClassifierContext *ctx, double ratio, uint64_t sample_dt_us,
                          int16_t *state, int16_t *observed, int16_t *candidate,
                          int16_t *confirmed, uint8_t *hysteresis_hold);

#endif /* DRMS_CLASSIFIER_H */
