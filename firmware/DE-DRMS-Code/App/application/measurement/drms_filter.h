#ifndef DRMS_FILTER_H
#define DRMS_FILTER_H
/* 流式一阶 IIR（T6/C6）：y += alpha*(x-y)；alpha=1-exp(-dt/tau)，tau=0 旁路。
 * dt 取配置采样间隔（1/rate_hz），alpha 在 configure 时一次计算缓存，
 * 不在每帧重复 exp。首样本 y=x。内部状态显式 context，调用方不得直读。 */
#include <stdint.h>

typedef struct {
  double alpha;            /* 0 = 旁路 */
  double y;                /* 滤波输出 */
  uint8_t primed;          /* 首样本已初始化 */
  uint8_t valid;           /* 建立窗口已覆盖且未被故障打断 */
  uint64_t warmup_accum_us;/* 已累计连续有效样本时间（名义） */
  uint64_t warmup_target_us;
} DRMS_FilterContext;

void drms_filter_configure(DRMS_FilterContext *ctx, uint32_t rate_hz, uint64_t tau_us,
                           uint64_t warmup_us);
void drms_filter_reset(DRMS_FilterContext *ctx);
/* 喂入一个有效样本：返回滤波输出；*warmup_done 置 1 表示建立窗口已达成。
 * 无 I/O、无堆分配。 */
double drms_filter_step(DRMS_FilterContext *ctx, double x, uint64_t sample_dt_us,
                        uint32_t *warmup_done);

#endif /* DRMS_FILTER_H */
