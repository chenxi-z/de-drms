#include "drms_filter.h"
#include <math.h>

void drms_filter_configure(DRMS_FilterContext *ctx, uint32_t rate_hz, uint64_t tau_us,
                           uint64_t warmup_us)
{
  if (!ctx)
    return;
  ctx->y = 0.0;
  ctx->primed = 0;
  ctx->valid = 0;
  ctx->warmup_accum_us = 0;
  ctx->warmup_target_us = warmup_us;
  if (!tau_us || !rate_hz)
  {
    ctx->alpha = 0.0; /* 旁路 */
    return;
  }
  double dt_us = 1000000.0 / (double)rate_hz;
  ctx->alpha = 1.0 - exp(-(double)tau_us / dt_us); /* configure 时一次算好并缓存 */
}

void drms_filter_reset(DRMS_FilterContext *ctx)
{
  if (!ctx)
    return;
  ctx->y = 0.0;
  ctx->primed = 0;
  ctx->valid = 0;
  ctx->warmup_accum_us = 0;
}

double drms_filter_step(DRMS_FilterContext *ctx, double x, uint64_t sample_dt_us,
                        uint32_t *warmup_done)
{
  if (warmup_done)
    *warmup_done = 0;
  if (!ctx)
    return x;
  if (!ctx->primed)
  {
    ctx->y = x; /* 首样本初始化 */
    ctx->primed = 1;
  }
  else if (ctx->alpha)
    ctx->y += ctx->alpha * (x - ctx->y);
  else
    ctx->y = x; /* 旁路 */
  ctx->warmup_accum_us += sample_dt_us;
  if (!ctx->valid && ctx->warmup_accum_us >= ctx->warmup_target_us)
  {
    ctx->valid = 1;
    if (warmup_done)
      *warmup_done = 1;
  }
  return ctx->y;
}
