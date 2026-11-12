/*****************************************************************************
 * 文件：drms_classifier.c
 * 职责：按 R/R₀ 落在哪个区间，判定损伤等级——带迟滞与确认时间。
 *
 * 为什么不能只看"落在哪个区间"：
 *   比值正好在边界附近抖动时，等级会来回跳，操作者无法判断到底稳不稳。
 *   这里用两道机制压住抖动：
 *
 *   迟滞（hysteresis）
 *     进入某区间需要一个更高的门槛，退出则用较低门槛。
 *     区间内预留的 h 就是这个回差宽度，具体数值由区间表给出。
 *
 *   确认时间（confirm_us）
 *     新的等级必须先持续满足一段时间才被"确认"，在此之前只作为 candidate 报告。
 *     这样一次噪声尖峰不会立刻把等级推上去。
 *
 * 三个输出字段的含义：
 *   observed  本帧直接算出来的等级（未平滑）
 *   candidate 正在确认中的等级
 *   confirmed 已确认的等级——这是界面应当显示的
 *
 * 未配置区间时一律返回 -1（表示"无等级"），绝不臆造一个默认档位。
 *****************************************************************************/

#include "drms_classifier.h"

void drms_classifier_configure(DRMS_ClassifierContext *ctx, const DRMS_MonitorConfig *config)
{
  if (!ctx || !config)
    return;
  ctx->interval_count = config->interval_count;
  for (unsigned int i = 0; i < config->interval_count && i < DRMS_MONITOR_INTERVALS_MAX; ++i)
    ctx->intervals[i] = config->intervals[i];
  ctx->confirm_us = config->confirm_us;
  drms_classifier_reset(ctx);
}

void drms_classifier_reset(DRMS_ClassifierContext *ctx)
{
  if (!ctx)
    return;
  ctx->confirmed = -1;
  ctx->candidate = -1;
  ctx->candidate_time_us = 0;
}

static int lookup(const DRMS_ClassifierContext *ctx, double ratio)
{
  for (unsigned int i = 0; i < ctx->interval_count; ++i)
  {
    const DRMS_MonitorInterval *iv = &ctx->intervals[i];
    int last = (i + 1u == ctx->interval_count);
    if (ratio >= iv->lo && (ratio < iv->hi || (last && iv->last_upper_closed && ratio == iv->hi)))
      return (int16_t)i;
  }
  return -1;
}

void drms_classifier_step(DRMS_ClassifierContext *ctx, double ratio, uint64_t sample_dt_us,
                          int16_t *state, int16_t *observed, int16_t *candidate,
                          int16_t *confirmed, uint8_t *hysteresis_hold)
{
  *observed = (int16_t)lookup(ctx, ratio);
  *candidate = -1;
  *confirmed = -1;
  *hysteresis_hold = 0;
  /* 已确认区间的回差保持范围 [lo-h, hi+h]；h=0 时严格原端点 */
  if (ctx->confirmed >= 0)
  {
    const DRMS_MonitorInterval *iv = &ctx->intervals[ctx->confirmed];
    double h = iv->h;
    int inside = h > 0.0 ? (ratio >= iv->lo - h && ratio <= iv->hi + h)
                         : (lookup(ctx, ratio) == ctx->confirmed); /* h=0：严格原表映射 */
    if (inside)
    {
      ctx->candidate = -1;
      ctx->candidate_time_us = 0;
      *state = DRMS_MONITOR_CONFIRMED;
      *confirmed = ctx->confirmed;
      *hysteresis_hold = 1;
      return;
    }
    ctx->confirmed = -1; /* 离开保持范围：旧确认转历史，不得继续输出旧正常等级 */
  }
  if (*observed < 0)
  {
    ctx->candidate = -1;
    ctx->candidate_time_us = 0;
    *state = DRMS_MONITOR_UNMAPPED; /* 空隙不冒充正常 */
    return;
  }
  if (ctx->candidate != *observed)
  {
    ctx->candidate = *observed; /* 候选变化（含返回历史区间）：重新计时 */
    ctx->candidate_time_us = 0;
  }
  ctx->candidate_time_us += sample_dt_us;
  if (ctx->candidate_time_us >= ctx->confirm_us || ctx->confirm_us == 0)
  {
    ctx->confirmed = ctx->candidate; /* 连续确认达成（confirm_us=0 当帧确认） */
    ctx->candidate = -1;
    ctx->candidate_time_us = 0;
    *state = DRMS_MONITOR_CONFIRMED;
    *confirmed = ctx->confirmed;
    return;
  }
  *state = DRMS_MONITOR_PENDING;
  *candidate = ctx->candidate;
}
