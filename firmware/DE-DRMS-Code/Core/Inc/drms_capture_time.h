#ifndef DRMS_CAPTURE_TIME_H
#define DRMS_CAPTURE_TIME_H
/* 原始环时间侧表（C3）。固定 65×32 B = 2080 B，计入 RAM 预算，不扩充 16 B 原始帧。
 * 每连续 64 个 raw_ticket 构成一块；槽位 = block_id % 65（不是 %64：4096 帧滑动窗
 * 可能同时跨 65 个块，用 65 个槽保证窗口内槽位永不冲突）。
 * 内存序契约：生产者在块首帧成功入环【前】调用 publish（随后的环形发布
 * release 顺带发布侧表项）；消费者 acquire 取得帧【后】、释放环槽【前】调用
 * lookup。满足该协议时同槽读写不可能并发；覆盖资格由 publish 内部用调用方
 * 传入的原始环已消费水位（consumed_raw_next，acquire 读取）判定，不依赖
 * valid 标志。publish/lookup 均只在唯一生产者/唯一消费者上下文分别调用。 */
#include "drms_architecture_contract.h"

#define DRMS_CAPTURE_BLOCK_TICKS 64u
#define DRMS_CAPTURE_TIME_SLOTS 65u

typedef struct {
  uint64_t block_id;              /* 侧表项对应的块号 */
  uint64_t first_capture_mono_us; /* 块首帧 DRDY 时刻的单调时钟读数（µs） */
  uint32_t acquisition_generation;
  uint32_t valid;
  uint8_t reserved[8];
} DRMS_CaptureTimeEntry;

_Static_assert(sizeof(DRMS_CaptureTimeEntry) == 32,
               "capture time side entry must stay 32 bytes");

/* 清空侧表。代次切换顺序：停止生产 → 确认消费者不再使用旧环 → 本函数 →
 * 新代 publish。其他任何场景不得调用。 */
void drms_capture_time_reset(void);

/* 仅生产者：为块 raw_ticket/64 发布时间项。raw_ticket 必须块对齐（块首帧的
 * 发布位置）；consumed_raw_next 为发布前读取的原始环消费水位；若目标槽的
 * 旧项帧未全部消费（consumed_raw_next < 旧块末界）则拒绝覆盖并返回
 * DRMS_IO_ERROR（数据通路故障），不得改写旧时间后继续。 */
DRMS_Result drms_capture_time_publish(uint64_t raw_ticket, uint64_t consumed_raw_next,
                                      uint32_t acquisition_generation, uint64_t drdy_mono_us);

/* 仅消费者：取得帧 raw_ticket 的保守时间下界（其所在块首帧的 DRDY 时刻）。
 * 项无效/已被新块覆盖/代次不匹配返回 DRMS_STALE。 */
DRMS_Result drms_capture_time_lookup(uint64_t raw_ticket, uint32_t acquisition_generation,
                                     uint64_t *lower_bound_us);

/* 侧表固定字节数（2080），供 RAM 预算与测试断言。 */
size_t drms_capture_time_bytes(void);

/* 名义算法时间（C3）：mono_us0 + floor((sample_seq-sample_seq0)*1e6/rate_hz)，
 * 商余分解防溢出。要求 rate_hz>0 且同代 sample_seq>=sample_seq0；
 * 结果只供算法与离线复现，不得与 now_us 比较新鲜度。 */
uint64_t drms_capture_time_nominal_us(const DRMS_TimeAnchor *anchor, uint64_t sample_seq);

#endif /* DRMS_CAPTURE_TIME_H */
