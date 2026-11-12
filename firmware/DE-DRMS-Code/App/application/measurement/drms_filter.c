/*****************************************************************************
 * 文件：drms_filter.c
 * 职责：对电阻读数做一阶低通滤波，并管理"预热建立"过程。
 *
 * 为什么需要滤波：
 *   ADC 的原始读数有噪声。判级看的是 R/R₀ 的微小变化，噪声会直接掩盖信号。
 *   一阶 IIR 够用且极省算力：每帧只有一次乘加。
 *
 * 两个时间常数的分工：
 *   tau      滤波时间常数，决定平滑程度。越大越平稳、响应越慢。
 *   warmup   预热时间，滤波器从零状态开始需要一段时间才能收敛到真值。
 *            这段时间内的输出不可信，必须显式标记以免被当成有效读数。
 *
 * 实现上把 alpha = 1 - exp(-tau/dt) 在配置时算好缓存：
 *   每次调用都算 exp() 太贵，而这个系数只与采样率和 tau 有关。
 *****************************************************************************/

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
