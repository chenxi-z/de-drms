#include "drms_measurement.h"
#include <math.h>

uint16_t drms_crc16(const uint8_t *bytes, size_t length)
{
  /* CRC-CCITT-FALSE: poly 0x1021, init 0xffff, no reflection/final XOR.
     TI SBAS590E §9.5.1.7; nibble table keeps per-frame work bounded. */
  static const uint16_t table[16] = {
    0x0000,0x1021,0x2042,0x3063,0x4084,0x50a5,0x60c6,0x70e7,
    0x8108,0x9129,0xa14a,0xb16b,0xc18c,0xd1ad,0xe1ce,0xf1ef
  };
  uint16_t crc = 0xffff;
  for (size_t i = 0; i < length; ++i)
  {
    crc = (uint16_t)((crc << 4) ^ table[((crc >> 12) ^ (bytes[i] >> 4)) & 15]);
    crc = (uint16_t)((crc << 4) ^ table[((crc >> 12) ^ bytes[i]) & 15]);
  }
  return crc;
}

uint32_t drms_crc32(const uint8_t *bytes, size_t length)
{
  uint32_t crc = 0xffffffffU;
  for (size_t i = 0; i < length; ++i)
  {
    crc ^= bytes[i];
    for (unsigned int bit = 0; bit < 8; ++bit)
      crc = (crc >> 1) ^ (0xedb88320U & (0U - (crc & 1U)));
  }
  return ~crc;
}

static int32_t signed24(const uint8_t *bytes)
{
  uint32_t value = ((uint32_t)bytes[0] << 16) | ((uint32_t)bytes[1] << 8) | bytes[2];
  /* Subtraction avoids implementation-defined unsigned-to-signed conversion. */
  return value & 0x800000U ? (int32_t)(value & 0x7fffffU) - 0x800000 : (int32_t)value;
}

int drms_decode_frame(const uint8_t frame[12], DRMS_Sample *sample)
{
  sample->voltage = signed24(frame + 3);
  sample->sense = signed24(frame + 6);
  sample->status = (uint16_t)(((uint16_t)frame[0] << 8) | frame[1]);
  sample->flags = 0;
  if (drms_crc16(frame, 9) != (uint16_t)(((uint16_t)frame[9] << 8) | frame[10]))
    sample->flags |= DRMS_SAMPLE_CRC_ERROR;
  if (frame[0] != 0x22 || (frame[1] & 0x80) || frame[2] != 0 || frame[11] != 0)
    sample->flags |= DRMS_SAMPLE_FORMAT_ERROR;
  /* F_ADCIN alone is advisory on this board: AIN2N is intentionally at AVSS,
     below the lowest comparator threshold. Preserve it in the raw status,
     but reject protocol/resync/watchdog/overrun faults and digital saturation. */
  if (frame[1] & 0x6f)
    sample->flags |= DRMS_SAMPLE_ADC_FAULT;
  if (sample->voltage >= 8388606 || sample->voltage <= -8388607 ||
      sample->sense >= 8388606 || sample->sense <= 4096 || sample->voltage < -4096)
    sample->flags |= DRMS_SAMPLE_RANGE_ERROR;
  return sample->flags == 0;
}

int drms_excitation_ok(const DRMS_Sample *sample)
{
  /* First-board sanity guard, not a calibrated current specification:
     VSET=3.3*100/(180+100)=1.178571 V, permit +/-10%; Vref=2.442 V.
     Also reserve 0.5 V compliance below the design's minimum 2.97 V T node. */
  return !sample->flags && sample->sense >= 3643701 && sample->sense <= 4453411 &&
         (int64_t)sample->voltage + sample->sense <= 8484791;
}

int drms_resistance(const DRMS_Sample *sample, double scale, double *ohms)
{
  if (sample->flags || sample->sense <= 4096 || sample->voltage >= 8388606 ||
      sample->voltage < -4096 || !isfinite(scale) || scale <= 0)
    return 0;
  *ohms = scale * (double)sample->voltage / (double)sample->sense;
  return isfinite(*ohms);
}

int drms_reference_scale(int64_t voltage_sum, int64_t sense_sum,
                         double reference_ohms, double *scale)
{
  if (voltage_sum <= 0 || sense_sum <= 0 || reference_ohms <= 0 || !isfinite(reference_ohms))
    return 0;
  double value = reference_ohms * (double)sense_sum / (double)voltage_sum;
  if (!isfinite(value) || value < 100000. || value > 200000.)
    return 0;
  *scale = value;
  return 1;
}

int drms_rate_register(uint32_t rate, uint8_t *clk2)
{
  switch (rate)
  {
    case 1000: *clk2 = 0x20; return 1;
    case 4000: *clk2 = 0x22; return 1;
    case 8000: *clk2 = 0x25; return 1;
    case 16000: *clk2 = 0x28; return 1;
    case 32000: *clk2 = 0x2b; return 1;
    case 64000: *clk2 = 0x2d; return 1;
    case 128000: *clk2 = 0x2f; return 1;
    default: return 0;
  }
}
