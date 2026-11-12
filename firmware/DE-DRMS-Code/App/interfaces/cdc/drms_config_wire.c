/*****************************************************************************
 * 文件：drms_config_wire.c
 * 职责：配置的线上编解码——把协议下发的 TLV 转成内部结构，以及反向。
 *
 * 与 drms_user_config 的分工：
 *   本文件只负责"字节 <-> 结构"的转换与格式校验；
 *   持久化、版本管理、基线依赖那些业务规则在 drms_user_config 里。
 *
 * 校验原则：宁可整份拒绝，不做部分接受。配置一旦被部分应用，
 * 现场表现会非常难解释——某个参数生效了、另一个没生效。
 *****************************************************************************/

#include "drms_config_wire.h"
#include "drms_cdc_frame.h"
#include "drms_measurement.h"
#include "drms_user_config.h"
#include <string.h>

static uint16_t get16(const uint8_t *p) { return (uint16_t)(p[0] | (uint16_t)p[1] << 8); }
static uint32_t get32(const uint8_t *p) {
  return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}
static uint64_t get64(const uint8_t *p) {
  uint64_t v = 0; for (unsigned i = 0; i < 8; ++i) v |= (uint64_t)p[i] << (8u*i); return v;
}
static void put16(uint8_t *p, uint16_t v) { p[0] = (uint8_t)v; p[1] = (uint8_t)(v >> 8); }
static void put32(uint8_t *p, uint32_t v) {
  for (unsigned i = 0; i < 4; ++i) p[i] = (uint8_t)(v >> (8u*i));
}
static double get_double(const uint8_t *p) { uint64_t bits = get64(p); double d; memcpy(&d, &bits, 8); return d; }
static int finite_double(double d) { return d == d && d < 1e308 && d > -1e308; }
static int utf8(const uint8_t *s, size_t n) {
  size_t i = 0;
  while (i < n) {
    uint8_t c = s[i]; unsigned more;
    if (!c) return 0;
    if (c < 0x80) more = 0;
    else if (c >= 0xc2 && c <= 0xdf) more = 1;
    else if (c >= 0xe0 && c <= 0xef) more = 2;
    else if (c >= 0xf0 && c <= 0xf4) more = 3;
    else return 0;
    if (more >= n-i) return 0;
    for (unsigned j = 1; j <= more; ++j) if ((s[i+j] & 0xc0) != 0x80) return 0;
    if (more == 2 && ((c == 0xe0 && s[i+1] < 0xa0) || (c == 0xed && s[i+1] >= 0xa0))) return 0;
    if (more == 3 && ((c == 0xf0 && s[i+1] < 0x90) || (c == 0xf4 && s[i+1] >= 0x90))) return 0;
    i += more + 1u;
  }
  return 1;
}

size_t drms_config_wire_to_body(const uint8_t *settings, size_t length, uint8_t *body, size_t cap) {
  static const DRMS_CDCFieldRule rules[] = {
    {72,4,4,0,1}, {73,4,4,0,1}, {74,8,8,0,1}, {75,8,8,0,1},
    {76,8,8,0,1}, {77,8,8,0,1}, {78,0,480,0,1}, {79,0,32,0,1},
    {80,0,32,0,1}, {81,4,4,0,1}, {82,8,8,0,1}, {83,8,8,2,1},
    {84,0,304,0,0}
  };
  DRMS_CDCFieldView f[sizeof(rules)/sizeof(rules[0])];
  const uint8_t *names[DRMS_USER_INTERVALS_MAX] = {0};
  uint8_t name_len[DRMS_USER_INTERVALS_MAX] = {0};
  if (!settings || !body || cap < 44 || cap > DRMS_USER_BODY_MAX ||
      drms_cdc_fields_validate(settings, length, rules, sizeof(rules)/sizeof(rules[0]), f)) return 0;
  if (!utf8(f[7].value, f[7].length) || !utf8(f[8].value, f[8].length) || f[6].length % 30u) return 0;
  unsigned count = f[6].length / 30u;
  uint8_t reg; uint32_t rate = get32(f[0].value);
  if (count > DRMS_USER_INTERVALS_MAX || !drms_rate_register(rate, &reg)) return 0;
  uint64_t stale = (128000000ULL + rate - 1u)/rate;
  if (stale < 10000u) stale = 10000u;
  if (get64(f[5].value) < stale) return 0;
  double cv = get_double(f[11].value);
  if (!finite_double(cv) || cv < 0 || (!get32(f[9].value) && (get64(f[10].value) || cv != 0))) return 0;
  double prev_hi = 0, prev_h = 0;
  for (unsigned i = 0; i < count; ++i) {
    const uint8_t *p = f[6].value + i*30u;
    double lo = get_double(p), hi = get_double(p+8), h = get_double(p+16);
    if (p[26] > 3 || p[27] > 1 || (p[27] && i+1 != count) || p[28] > 2 || p[29] ||
        !finite_double(lo) || !finite_double(hi) || !finite_double(h) || !(lo < hi) ||
        !(h >= 0 && 2*h < hi-lo) || (i && (!(lo >= prev_hi) || (lo > prev_hi && !(prev_h+h < lo-prev_hi))))) return 0;
    for (unsigned j = 0; j < i; ++j) if (get16(f[6].value+j*30u+24) == get16(p+24)) return 0;
    prev_hi = hi; prev_h = h;
  }
  if (f[12].value) {
    size_t n = 0;
    while (n < f[12].length) {
      if (f[12].length-n < 3) return 0;
      uint16_t id = get16(f[12].value+n); uint8_t len = f[12].value[n+2]; n += 3;
      if (len > 16 || len > f[12].length-n || !utf8(f[12].value+n, len)) return 0;
      unsigned i = 0; while (i < count && get16(f[6].value+i*30u+24) != id) ++i;
      if (i == count || names[i]) return 0;
      names[i] = f[12].value+n; name_len[i] = len; n += len;
    }
  }
  size_t interval_size = 2;
  for (unsigned i = 0; i < count; ++i) interval_size += 29u + name_len[i];
  size_t total = 40u + (count ? 4u+interval_size : 0u) + 40u + 4u+f[7].length + 24u + 4u+length + 4u;
  if (total > cap || total > DRMS_USER_BODY_MAX) return 0;
  memset(body, 0, 40); memcpy(body, "DRMSUC01", 8); put32(body+8, (uint32_t)total);
  size_t o = 40;
  if (count) {
    put16(body+o, 1); put16(body+o+2, (uint16_t)interval_size); put16(body+o+4, (uint16_t)count); o += 6;
    for (unsigned i = 0; i < count; ++i) {
      const uint8_t *p = f[6].value+i*30u;
      memcpy(body+o, p+24, 2); body[o+2] = p[26]; body[o+3] = p[27];
      memcpy(body+o+4, p, 24); body[o+28] = name_len[i];
      if (name_len[i]) memcpy(body+o+29, names[i], name_len[i]);
      o += 29u+name_len[i];
    }
  }
  put16(body+o, 2); put16(body+o+2, 36); o += 4;
  memcpy(body+o, f[0].value, 4); o += 4;
  for (unsigned i = 2; i <= 5; ++i) { memcpy(body+o, f[i].value, 8); o += 8; }
  put16(body+o, 3); put16(body+o+2, f[7].length); o += 4; memcpy(body+o, f[7].value, f[7].length); o += f[7].length;
  put16(body+o, 0xd701); put16(body+o+2, 20); o += 4;
  memcpy(body+o, f[9].value, 4); memcpy(body+o+4, f[10].value, 8); memcpy(body+o+12, f[11].value, 8); o += 20;
  /* Preserve all wire-only values and unknown optional extensions. */
  put16(body+o, 0xd702); put16(body+o+2, (uint16_t)length); o += 4; memcpy(body+o, settings, length); o += length;
  put32(body+o, drms_crc32(body, o)); o += 4;
  return o == total ? o : 0;
}
