/*****************************************************************************
 * 文件：drms_monitor.c
 * 职责：监测管线的组装——把滤波、分级、区间判定串成一个每帧调用一次的处理链。
 *
 * 一条数据流经这里时依次发生：
 *   输入检查（质量位、连续性、代次/版本变化）
 *   → 无效则重置滤波器与分级器，并报告无效原因
 *   → 有效则滤波 → 算 R/R0 → 按区间判级（含迟滞与确认时间）→ 产生输出
 *
 * 设计约束（C6 冻结接口）：
 *   本文件无 I/O、无 RTOS 调用、无堆分配。它是纯计算，
 *   因此既能在真机上跑，也能在主机单元测试里逐帧回放验证。
 *
 * 那个"输入无效就全量重置"的规则是刻意的：
 *   一旦出现缺口或版本变化，之前的滤波状态和确认计时都不再成立。
 *   继续沿用只会让恢复后的判级长时间偏离真值。
 *****************************************************************************/

/* 监测管线公共实现（C6 冻结接口的落地；T1 contract.h 声明）。
 * 处理线程唯一调用 step/tick；内部组合 filter/classifier，无 I/O、无 RTOS、
 * 无堆分配。step 后由调用方执行 tick 并一致复制输出后发布（T7）。 */
#include "drms_architecture_contract.h"
#include "drms_filter.h"
#include "drms_classifier.h"
#include <string.h>

struct DRMS_MonitorContext {
  DRMS_MonitorConfig config;
  uint8_t configured;
  DRMS_FilterContext filter;
  DRMS_ClassifierContext classifier;
  /* 顺序/版本监督 */
  uint8_t have_last;
  uint64_t last_seq;
  uint32_t last_generation;
  uint64_t last_config_version, last_baseline_version;
  /* 最近一次 step 的算法结果（tick 只叠加展示覆盖，不改算法状态） */
  DRMS_MonitorOutput last_output;
  uint8_t have_output; /* INVALID 步之后仍可展示其捕获时间 */
};

/* 调用方（T7）以 DRMS_MONITOR_CONTEXT_BYTES 对齐字节区分配 context。 */
_Static_assert(sizeof(struct DRMS_MonitorContext) <= DRMS_MONITOR_CONTEXT_BYTES,
               "monitor context exceeds published allocation");

static double ratio_of(const DRMS_MonitorContext *ctx, double ohms)
{
  return ohms / ctx->config.r0;
}

static void fill_output(DRMS_MonitorContext *ctx, DRMS_MonitorOutput *out,
                        DRMS_MonitorState state, uint32_t reason, double ratio,
                        int16_t observed, int16_t candidate, int16_t confirmed,
                        uint8_t hysteresis, const DRMS_MonitorInput *in)
{
  memset(out, 0, sizeof(*out));
  out->state = state;
  out->reason = reason;
  out->ratio = ratio;
  out->observed = observed;
  out->candidate = candidate;
  out->confirmed = confirmed;
  out->hysteresis_hold = hysteresis;
  out->capture_lower_bound_us = in ? in->capture_lower_bound_us : ctx->last_output.capture_lower_bound_us;
  out->sample_seq = in ? in->sample_seq : ctx->last_output.sample_seq;
  out->acquisition_generation = in ? in->acquisition_generation : ctx->last_output.acquisition_generation;
  out->config_version = in ? in->config_version : ctx->last_output.config_version;
  out->baseline_version = in ? in->baseline_version : ctx->last_output.baseline_version;
}

void drms_monitor_init(DRMS_MonitorContext *ctx)
{
  memset(ctx, 0, sizeof(*ctx));
  ctx->have_output = 0;
  ctx->classifier.confirmed = -1;
  ctx->classifier.candidate = -1;
  ctx->last_output.confirmed = -1;
  ctx->last_output.candidate = -1;
  ctx->last_output.observed = -1;
}

DRMS_Result drms_monitor_configure(DRMS_MonitorContext *ctx, const DRMS_MonitorConfig *cfg)
{
  if (!ctx || !cfg)
    return DRMS_INVALID;
  if (cfg->rate_hz == 0 || cfg->interval_count > DRMS_MONITOR_INTERVALS_MAX)
    return DRMS_INVALID;
  /* 先全量校验，再原地写入：避免在调用方栈上复制整个 context
   * （主线程栈仅 4 KiB，context≈1.2 KiB）。 */
  for (unsigned int i = 0; i < cfg->interval_count; ++i)
  {
    const DRMS_MonitorInterval *iv = &cfg->intervals[i];
    double lo = iv->lo, hi = iv->hi, h = iv->h;
    if (!(lo < hi) || !(h >= 0.0) || !(2.0 * h < hi - lo))
      return DRMS_INVALID; /* C6 端点/回差约束 */
    if (i && !(lo >= cfg->intervals[i - 1].hi))
      return DRMS_INVALID; /* 有序不重叠 */
  }
  ctx->config = *cfg;
  ctx->configured = 1;
  /* 配置变更：算法状态整体重建（版本变化路径） */
  drms_filter_configure(&ctx->filter, cfg->rate_hz, cfg->tau_us, cfg->warmup_us);
  drms_classifier_configure(&ctx->classifier, cfg);
  ctx->have_last = 0;
  ctx->have_output = 0;
  ctx->last_seq = 0;
  ctx->last_generation = 0;
  ctx->last_config_version = 0;
  ctx->last_baseline_version = 0;
  memset(&ctx->last_output, 0, sizeof(ctx->last_output));
  ctx->last_output.confirmed = -1;
  ctx->last_output.candidate = -1;
  ctx->last_output.observed = -1;
  return DRMS_OK;
}

void drms_monitor_step(DRMS_MonitorContext *ctx, const DRMS_MonitorInput *in,
                       DRMS_MonitorOutput *out)
{
  if (!ctx || !in || !out || !ctx->configured)
  {
    if (out)
    {
      memset(out, 0, sizeof(*out));
      out->confirmed = out->candidate = out->observed = -1;
      out->state = DRMS_MONITOR_UNCONFIGURED;
    }
    return;
  }
  /* 名义样本间隔：每个有效样本都计满（确认计时与建立窗口的统一约定）。 */
  uint64_t dt = ctx->config.rate_hz ? 1000000ull / ctx->config.rate_hz : 0;
  /* --- 无效输入判定（R8/C6：质量/缺口/版本变化） --- */
  uint32_t reason = 0;
  if (in->quality_flags)
    reason |= DRMS_REASON_QUALITY_BAD;
  if (in->ohms != in->ohms || in->ohms > 1e308 || in->ohms < -1e308)
    reason |= DRMS_REASON_NOT_FINITE;
  if (ctx->have_last)
  {
    if (in->acquisition_generation != ctx->last_generation ||
        in->config_version != ctx->last_config_version ||
        in->baseline_version != ctx->last_baseline_version)
      reason |= DRMS_REASON_SAMPLE_GAP; /* 版本/代次变化视同缺口：全部重置 */
    else
    {
      uint64_t delta = in->sample_seq - ctx->last_seq;
      if (delta == 0 || delta > 1)
        reason |= DRMS_REASON_SAMPLE_GAP;
    }
  }
  if (reason)
  {
    /* 无效：取消确认并清除滤波有效状态；恢复需完整建立窗口 */
    drms_filter_reset(&ctx->filter);
    drms_classifier_reset(&ctx->classifier);
    ctx->have_last = 0;
    ctx->last_generation = in->acquisition_generation;
    ctx->last_config_version = in->config_version;
    ctx->last_baseline_version = in->baseline_version;
    ctx->last_seq = in->sample_seq;
    fill_output(ctx, out, DRMS_MONITOR_INVALID, reason, 0.0, -1, -1, -1, 0, in);
    ctx->last_output = *out;
    ctx->have_output = 1;
    return;
  }
  /* --- 有效样本 --- */
  ctx->last_generation = in->acquisition_generation;
  ctx->last_config_version = in->config_version;
  ctx->last_baseline_version = in->baseline_version;
  ctx->last_seq = in->sample_seq;
  ctx->have_last = 1;
  uint32_t warmup_done = 0;
  double filtered = drms_filter_step(&ctx->filter, in->ohms, dt, &warmup_done);
  double ratio = 0.0;
  if (!ctx->config.baseline_valid || ctx->config.r0 <= 0.0)
  {
    /* 无有效基线：不作正常区间判断；滤波继续建立 */
    fill_output(ctx, out, DRMS_MONITOR_INVALID, DRMS_REASON_NO_BASELINE,
                0.0, -1, -1, -1, 0, in);
    ctx->last_output = *out;
    ctx->have_output = 1;
    return;
  }
  ratio = ratio_of(ctx, filtered);
  if (!ctx->filter.valid) /* 建立窗口以连续有效样本时间判定（粘滞标志） */
  {
    int16_t observed = -1, candidate = -1, confirmed = -1;
    fill_output(ctx, out, DRMS_MONITOR_WARMUP, DRMS_REASON_WARMUP,
                ratio, observed, candidate, confirmed, 0, in);
    ctx->last_output = *out;
    ctx->have_output = 1;
    return;
  }
  /* --- 分类（C6 转换表） --- */
  int16_t state = DRMS_MONITOR_UNMAPPED, observed = -1, candidate = -1, confirmed = -1;
  uint8_t hysteresis = 0;
  drms_classifier_step(&ctx->classifier, ratio, dt, &state, &observed,
                       &candidate, &confirmed, &hysteresis);
  if (ctx->config.interval_count == 0)
    state = DRMS_MONITOR_UNCONFIGURED;
  fill_output(ctx, out, state, 0, ratio, observed, candidate, confirmed, hysteresis, in);
  ctx->last_output = *out;
  ctx->have_output = 1;
}

void drms_monitor_tick(DRMS_MonitorContext *ctx, uint64_t now_us, DRMS_MonitorOutput *out)
{
  if (!ctx || !out)
    return;
  *out = ctx->last_output; /* 历史算法状态只读复制 */
  if (!ctx->have_output)
  {
    out->fresh = 0;
    out->freshness_reason = DRMS_FRESH_NO_SAMPLE;
    return;
  }
  /* 无基线/UNCONFIGURED 等算法状态不影响展示新鲜度：电阻显示独立于等级判断 */
  uint64_t lower = ctx->last_output.capture_lower_bound_us;
  if (now_us < lower)
  {
    out->fresh = 0;
    out->freshness_reason = DRMS_FRESH_TIMEBASE_FAULT; /* 不做无符号减法掩盖 */
    return;
  }
  uint64_t age = now_us - lower;
  if (age >= ctx->config.stale_timeout_us)
  {
    out->fresh = 0;
    out->freshness_reason = DRMS_FRESH_STALE;
    return;
  }
  out->fresh = 1; /* 新鲜仅表示展示可用，不代表算法状态有效 */
  out->freshness_reason = 0;
}
