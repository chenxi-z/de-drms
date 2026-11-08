#include "drms_capture_time.h"
#include <string.h>

static DRMS_CaptureTimeEntry table[DRMS_CAPTURE_TIME_SLOTS];

void drms_capture_time_reset(void)
{
  memset(table, 0, sizeof(table));
}

DRMS_Result drms_capture_time_publish(uint64_t raw_ticket, uint64_t consumed_raw_next,
                                      uint32_t acquisition_generation, uint64_t drdy_mono_us)
{
  uint64_t block;
  uint32_t slot;
  DRMS_CaptureTimeEntry *entry;
  if (raw_ticket % DRMS_CAPTURE_BLOCK_TICKS != 0u)
    return DRMS_INVALID;
  block = raw_ticket / DRMS_CAPTURE_BLOCK_TICKS;
  slot = (uint32_t)(block % DRMS_CAPTURE_TIME_SLOTS);
  entry = &table[slot];
  if (entry->valid)
  {
    if (entry->acquisition_generation != acquisition_generation)
    {
      /* 旧代项未被 reset 就出现新代发布：协议违规，不得覆盖旧时间。 */
      return DRMS_STALE;
    }
    if (entry->block_id != block)
    {
      /* 覆盖资格：旧块的每一帧都必须已被消费。 */
      uint64_t old_block_end = entry->block_id * DRMS_CAPTURE_BLOCK_TICKS +
                               DRMS_CAPTURE_BLOCK_TICKS;
      if (consumed_raw_next < old_block_end)
        return DRMS_IO_ERROR; /* 数据通路故障：不满足即不能覆盖旧时间后继续 */
    }
  }
  entry->block_id = block;
  entry->first_capture_mono_us = drdy_mono_us;
  entry->acquisition_generation = acquisition_generation;
  entry->valid = 1u;
  return DRMS_OK;
}

DRMS_Result drms_capture_time_lookup(uint64_t raw_ticket, uint32_t acquisition_generation,
                                     uint64_t *lower_bound_us)
{
  uint64_t block;
  uint32_t slot;
  const DRMS_CaptureTimeEntry *entry;
  if (!lower_bound_us)
    return DRMS_INVALID;
  block = raw_ticket / DRMS_CAPTURE_BLOCK_TICKS;
  slot = (uint32_t)(block % DRMS_CAPTURE_TIME_SLOTS);
  entry = &table[slot];
  if (!entry->valid || entry->block_id != block ||
      entry->acquisition_generation != acquisition_generation)
    return DRMS_STALE;
  *lower_bound_us = entry->first_capture_mono_us;
  return DRMS_OK;
}

size_t drms_capture_time_bytes(void)
{
  return sizeof(table);
}

uint64_t drms_capture_time_nominal_us(const DRMS_TimeAnchor *anchor, uint64_t sample_seq)
{
  uint64_t delta = sample_seq - anchor->sample_seq0; /* 无符号回绕安全 */
  uint64_t whole_blocks = delta / anchor->rate_hz;
  uint64_t remainder = delta % anchor->rate_hz;
  /* 商余分解：whole_blocks*1e6 在整个 64 位范围内不溢出（rate>=1 时
   * whole_blocks <= delta），remainder*1e6 < rate*1e6 <= 1.28e11 亦安全。 */
  return anchor->mono_us0 + whole_blocks * 1000000ULL +
         (remainder * 1000000ULL) / anchor->rate_hz;
}
