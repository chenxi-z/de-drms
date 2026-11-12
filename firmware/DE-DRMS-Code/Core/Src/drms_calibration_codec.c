/*****************************************************************************
 * 文件：drms_calibration_codec.c
 * 职责：校准记录的编码与校验——把系数、参考值、代次打成一块可持久化的字节。
 *
 * 与 calibration_flash 的分工：
 *   本文件只管格式（怎么排字节、CRC 怎么算）；
 *   flash 那个文件负责"写到哪、怎么保证掉电安全"。
 *   分开的好处是格式可以脱离硬件单独测试。
 *
 * 校验失败一律返回失败，不做"尽量恢复"——错误的校准系数比没有系数更危险，
 * 它会让所有读数看起来正常但系统性偏移。
 *****************************************************************************/

#include "drms_calibration.h"
#include "drms_measurement.h"
#include <math.h>
#include <string.h>

static const uint8_t commit[16] = "DRMSCALCOMMIT1";

static void put32(uint8_t *out, uint32_t value)
{
  for (unsigned int i = 0; i < 4; ++i)
    out[i] = (uint8_t)(value >> (i * 8));
}

static uint32_t get32(const uint8_t *in)
{
  return (uint32_t)in[0] | ((uint32_t)in[1] << 8) | ((uint32_t)in[2] << 16) | ((uint32_t)in[3] << 24);
}

static void put_double(uint8_t *out, double value)
{
  uint64_t bits;
  _Static_assert(sizeof(double) == 8, "Calibration requires IEEE754 binary64");
  memcpy(&bits, &value, sizeof(bits));
  put32(out, (uint32_t)bits);
  put32(out + 4, (uint32_t)(bits >> 32));
}

static double get_double(const uint8_t *in)
{
  uint64_t bits = get32(in) | ((uint64_t)get32(in + 4) << 32);
  double value;
  memcpy(&value, &bits, sizeof(value));
  return value;
}

void drms_calibration_pack(uint8_t record[64], const DRMS_Calibration *calibration)
{
  memset(record, 0, 64);
  memcpy(record, "DCAL", 4);
  record[4] = 1;
  record[6] = 64;
  put32(record + 8, calibration->generation);
  put32(record + 12, calibration->valid);
  put_double(record + 16, calibration->scale);
  put_double(record + 24, calibration->reference_ohms);
  put32(record + 32, calibration->rate);
  put32(record + 40, drms_crc32(record, 40));
  memcpy(record + 48, commit, 16);
}

int drms_calibration_unpack(const uint8_t record[64], DRMS_Calibration *calibration)
{
  uint8_t ignored;
  if (memcmp(record, "DCAL", 4) || record[4] != 1 || record[5] != 0 ||
      record[6] != 64 || record[7] != 0 || memcmp(record + 48, commit, 16) ||
      get32(record + 40) != drms_crc32(record, 40) || get32(record + 44) != 0)
    return 0;
  DRMS_Calibration candidate = {
    .generation = get32(record + 8), .valid = get32(record + 12),
    .scale = get_double(record + 16), .reference_ohms = get_double(record + 24),
    .rate = get32(record + 32)
  };
  if (candidate.valid != 1 || !isfinite(candidate.scale) || candidate.scale < 100000. ||
      candidate.scale > 200000. || !isfinite(candidate.reference_ohms) ||
      candidate.reference_ohms < 90000. || candidate.reference_ohms > 110000. ||
      !drms_rate_register(candidate.rate, &ignored))
    return 0;
  *calibration = candidate;
  return 1;
}

int drms_calibration_newer(uint32_t a, uint32_t b)
{
  return a != b && (uint32_t)(a - b) < 0x80000000U;
}
