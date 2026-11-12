/*****************************************************************************
 * 文件：drms_baseline.c
 * 职责：统计基线 R0——把一段连续有效读数归约成一个参考值。
 *
 * R0 是什么：
 *   试件在未损伤状态下的电阻。判级看的是 R/R0 的相对变化，
 *   所以 R0 的准确与否直接决定判级是否正确。
 *
 * 为什么不简单取平均：
 *   需要同时给出"中心值"和"离散程度"。只有离散度足够小，
 *   才能说这段数据足以作为基线——读数本身在飘的时候，
 *   平均值再准也没有意义。所以这里用均值 + 标准差同时评估。
 *
 * 建立过程为什么由上层驱动：
 *   基线只能在不换路、不丢样、速率不变的条件下建立。
 *   这些条件与采集状态强相关，本文件只负责纯计算，
 *   条件判断留给 drms_application 的 baseline_service。
 *   这样本文件可以脱离硬件单独测试。
 *****************************************************************************/

#include "drms_baseline.h"
#include <math.h>

void drms_baseline_configure(DRMS_BaselineContext *ctx, uint32_t min_count,
                             uint64_t min_duration_us, double stability_rel)
{
  if (!ctx)
    return;
  ctx->min_count = min_count;
  ctx->min_duration_us = min_duration_us;
  ctx->stability_rel = stability_rel;
  drms_baseline_reset(ctx);
}

void drms_baseline_reset(DRMS_BaselineContext *ctx)
{
  if (!ctx)
    return;
  ctx->count = 0;
  ctx->duration_us = 0;
  ctx->mean = ctx->m2 = 0.0;
}

void drms_baseline_feed(DRMS_BaselineContext *ctx, double ohms, uint64_t sample_dt_us)
{
  if (!ctx || ohms != ohms || ohms > 1e308 || ohms < -1e308)
    return; /* 非有限值不入统计 */
  ctx->count += 1;
  ctx->duration_us += sample_dt_us;
  double delta = ohms - ctx->mean;
  ctx->mean += delta / (double)ctx->count;
  ctx->m2 += delta * (ohms - ctx->mean);
}

int drms_baseline_candidate(const DRMS_BaselineContext *ctx, double *mean, double *stddev)
{
  if (!ctx)
    return 0; /* NOT_READY */
  if (!ctx->min_count || ctx->stability_rel < 0.0)
    return 2; /* UNCONFIGURED：无合格参数 */
  if (ctx->count < ctx->min_count || ctx->duration_us < ctx->min_duration_us)
    return 0;
  double variance = ctx->count > 1 ? ctx->m2 / (double)(ctx->count - 1) : 0.0;
  double sd = sqrt(variance);
  if (mean)
    *mean = ctx->mean;
  if (stddev)
    *stddev = sd;
  if (ctx->mean > 0.0 && sd / ctx->mean > ctx->stability_rel)
    return 0; /* 未达稳定限值 */
  return 1; /* OK */
}
