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
