#include "drms_user_config.h"
#include "drms_measurement.h" /* drms_crc32：CRC-32/ISO-HDLC（zlib 参数） */
#include <string.h>

/* 后端操作（实现 = drms_user_backend.c，Flash；主机测试提供替身）。
 * begin/end 界定一次擦写会话；program 以 16B 四字为粒度。 */
int drms_user_backend_begin(void);
void drms_user_backend_end(void);
int drms_user_backend_erase(unsigned int page); /* page 0=A, 1=B */
int drms_user_backend_program(unsigned int page, unsigned int offset,
                              const uint8_t quadword[16]);
int drms_user_backend_read(unsigned int page, unsigned int offset,
                           uint8_t *out, unsigned int length);

#define DRMS_USER_TLV_INTERVALS 1u
#define DRMS_USER_TLV_PARAMS 2u
#define DRMS_USER_TLV_ALIAS 3u
#define DRMS_USER_TLV_BASELINE_POLICY 0xD701u

static const uint8_t MAGIC_PREFIX[7] = {'D', 'R', 'M', 'S', 'U', 'C', '0'};
static const uint8_t COMMIT_MAGIC[4] = {'U', 'C', 'M', 'T'};
static const uint8_t SCHEMA_VERSION = '1';

typedef struct {
  uint16_t id;
  uint8_t level;
  uint8_t last_upper_closed;
  double lo, hi, h;
  uint8_t name_len;
  uint8_t name[DRMS_USER_NAME_MAX];
} IntervalEntry;

typedef struct {
  uint64_t config_version, calibration_version;
  uint32_t rate_hz;
  uint64_t tau_us, warmup_us, confirm_us, stale_timeout_us;
  uint8_t r0_valid;
  double r0;
  uint8_t interval_count;
  IntervalEntry intervals[DRMS_USER_INTERVALS_MAX];
  uint16_t extra_length;
  uint8_t extra[DRMS_USER_BODY_MAX]; /* retained alias and unrecognized TLVs */
} RunConfig;

static RunConfig run;
static RunConfig staged;
/* Transactions execute only in the serialized configuration owner context. */
static RunConfig transaction_workspace;
static uint8_t transaction_body[DRMS_USER_BODY_MAX];
static uint32_t have_staged;
static uint64_t run_version, persisted_version;
static uint32_t dirty, unsupported_schema, have_config;
static int32_t active_page = -1;
static uint64_t calibration_generation_now;

void drms_user_config_init(void)
{
  memset(&run, 0, sizeof(run));
  memset(&staged, 0, sizeof(staged));
  have_staged = 0;
  run_version = persisted_version = 0;
  dirty = unsupported_schema = have_config = 0;
  active_page = -1;
}

void drms_user_config_set_calibration_generation(uint64_t generation)
{
  calibration_generation_now = generation;
}

uint64_t drms_user_config_run_version(void) { return run_version; }
uint64_t drms_user_config_persisted_version(void) { return persisted_version; }
uint32_t drms_user_config_dirty(void) { return dirty; }
uint32_t drms_user_config_r0_valid(void) { return run.r0_valid; }
double drms_user_config_r0(void) { return run.r0; }
uint64_t drms_user_config_r0_calibration_version(void) { return run.calibration_version; }
uint32_t drms_user_config_unsupported_schema(void) { return unsupported_schema; }

static int finite(double v) { return v == v && v < 1e308 && v > -1e308; }

static void put16(uint8_t *p, uint16_t v) { p[0] = (uint8_t)v; p[1] = (uint8_t)(v >> 8); }

static void put32(uint8_t *p, uint32_t v)
{
  for (unsigned int i = 0; i < 4; ++i)
    p[i] = (uint8_t)(v >> (8u * i));
}

static void put64(uint8_t *p, uint64_t v)
{
  for (unsigned int i = 0; i < 8; ++i)
    p[i] = (uint8_t)(v >> (8u * i));
}

static uint16_t get16(const uint8_t *p) { return (uint16_t)(p[0] | (p[1] << 8)); }

static uint32_t get32(const uint8_t *p)
{
  return (uint32_t)p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

static uint64_t get64(const uint8_t *p)
{
  uint64_t v = 0;
  for (unsigned int i = 0; i < 8; ++i)
    v |= (uint64_t)p[i] << (8u * i);
  return v;
}

static double get_f64(const uint8_t *p)
{
  uint64_t bits = get64(p);
  double v;
  memcpy(&v, &bits, sizeof(v));
  return v;
}

static void put_f64(uint8_t *p, double v)
{
  uint64_t bits;
  memcpy(&bits, &v, sizeof(bits));
  put64(p, bits);
}

static int utf8_valid(const uint8_t *s, uint32_t length)
{
  uint32_t i = 0;
  while (i < length)
  {
    uint8_t c = s[i];
    uint32_t need;
    if (c < 0x80)
      need = 0;
    else if ((c & 0xE0) == 0xC0 && c >= 0xC2)
      need = 1;
    else if ((c & 0xF0) == 0xE0)
      need = 2;
    else if ((c & 0xF8) == 0xF0 && c <= 0xF4)
      need = 3;
    else
      return 0;
    if (i + need >= length)
      return 0; /* 截断序列 */
    for (uint32_t k = 1; k <= need; ++k)
      if ((s[i + k] & 0xC0) != 0x80)
        return 0;
    if (need == 2 && s[i] == 0xE0 && s[i + 1] < 0xA0)
      return 0; /* 超长编码 */
    if (need == 3 && s[i] == 0xF0 && s[i + 1] < 0x90)
      return 0;
    i += need + 1;
  }
  return 1;
}

#define INTERVAL_FIXED 29u /* id2+level1+flags1+lo8+hi8+h8+name_len1 */

static int validate_intervals(const uint8_t *value, uint32_t length)
{
  if (length < 2)
    return 0;
  uint16_t count = get16(value);
  if (count > DRMS_USER_INTERVALS_MAX)
    return 0;
  uint32_t offset = 2;
  double prev_hi = 0.0;
  int have_prev = 0;
  for (uint16_t i = 0; i < count; ++i)
  {
    if (offset + INTERVAL_FIXED > length)
      return 0;
    const uint8_t *rec = value + offset;
    uint8_t name_len = rec[28];
    if (name_len > DRMS_USER_NAME_MAX || offset + INTERVAL_FIXED + name_len > length)
      return 0;
    if (!utf8_valid(rec + 29, name_len))
      return 0;
    double lo = get_f64(rec + 4), hi = get_f64(rec + 12), h = get_f64(rec + 20);
    if (!finite(lo) || !finite(hi) || !finite(h))
      return 0;
    if (!(lo < hi))
      return 0; /* 禁止零宽/倒序 */
    if (!(h >= 0.0) || !(2.0 * h < hi - lo))
      return 0; /* C6 回差约束 */
    if (have_prev && !(lo >= prev_hi))
      return 0; /* 有序不重叠 */
    prev_hi = hi;
    have_prev = 1;
    offset += INTERVAL_FIXED + name_len;
  }
  return offset == length;
}

static int parse_tlv(const uint8_t *body, uint32_t body_len, RunConfig *cfg)
{
  cfg->interval_count = 0;
  cfg->extra_length = 0;
  uint32_t offset = 40;
  uint32_t baseline_seen = 0;
  while (offset + 4u <= body_len - 4u)
  {
    uint16_t type = get16(body + offset);
    uint16_t len = get16(body + offset + 2);
    if (offset + 4u + len > body_len - 4u)
      return 0;
    const uint8_t *value = body + offset + 4;
    if (type == DRMS_USER_TLV_INTERVALS)
    {
      if (!validate_intervals(value, len))
        return 0;
      uint16_t count = get16(value);
      uint32_t o = 2;
      for (uint16_t i = 0; i < count; ++i)
      {
        const uint8_t *rec = value + o;
        IntervalEntry *e = &cfg->intervals[i];
        e->id = get16(rec);
        e->level = rec[2];
        e->last_upper_closed = rec[3] & 1u;
        e->lo = get_f64(rec + 4);
        e->hi = get_f64(rec + 12);
        e->h = get_f64(rec + 20);
        e->name_len = rec[28];
        memcpy(e->name, rec + 29, e->name_len);
        o += INTERVAL_FIXED + e->name_len;
      }
      cfg->interval_count = (uint8_t)count;
    }
    else if (type == DRMS_USER_TLV_PARAMS)
    {
      if (len != 36u)
        return 0;
      cfg->rate_hz = get32(value);
      cfg->tau_us = get64(value + 4);
      cfg->warmup_us = get64(value + 12);
      cfg->confirm_us = get64(value + 20);
      cfg->stale_timeout_us = get64(value + 28);
      if (!cfg->rate_hz)
        return 0;
    }
    else if (type == DRMS_USER_TLV_ALIAS)
    {
      if (len > 64 || !utf8_valid(value, len))
        return 0;
    }
    else if (type == DRMS_USER_TLV_BASELINE_POLICY)
    {
      if (baseline_seen++ || len != 20u)
        return 0;
      uint32_t count = get32(value);
      uint64_t duration = get64(value + 4);
      double cv = get_f64(value + 12);
      if (!finite(cv) || cv < 0.0 || (!count && (duration || cv != 0.0)))
        return 0;
    }
    if (type != DRMS_USER_TLV_INTERVALS && type != DRMS_USER_TLV_PARAMS)
    {
      uint32_t size = 4u + len;
      if (size > sizeof(cfg->extra) - cfg->extra_length)
        return 0;
      memcpy(cfg->extra + cfg->extra_length, body + offset, size);
      cfg->extra_length += (uint16_t)size;
    }
    offset += 4u + len;
  }
  return offset == body_len - 4u;
}

uint32_t drms_user_config_get_baseline_policy(DRMS_BaselinePolicy *out)
{
  if (!out)
    return 0;
  memset(out, 0, sizeof(*out));
  const RunConfig *cfg = have_staged ? &staged : &run;
  uint32_t offset = 0;
  while (offset + 4u <= cfg->extra_length)
  {
    const uint8_t *entry = cfg->extra + offset;
    uint16_t len = get16(entry + 2);
    if (offset + 4u + len > cfg->extra_length)
      return 0;
    if (get16(entry) == DRMS_USER_TLV_BASELINE_POLICY && len == 20u)
    {
      out->min_count = get32(entry + 4);
      out->min_duration_us = get64(entry + 8);
      out->max_cv = get_f64(entry + 16);
      return out->min_count != 0;
    }
    offset += 4u + len;
  }
  return 0;
}

uint32_t drms_user_config_baseline_rate(void)
{
  return (have_staged ? &staged : &run)->rate_hz;
}

static uint32_t encode_body(const RunConfig *cfg, uint8_t *out, uint32_t capacity)
{
  if (capacity < 84)
    return 0;
  memcpy(out, MAGIC_PREFIX, 7);
  out[7] = SCHEMA_VERSION;
  put32(out + 8, 0); /* body_len 占位，收尾时回填 */
  uint32_t offset = 40;
  put64(out + 12, cfg->config_version);
  put64(out + 20, cfg->calibration_version);
  out[28] = cfg->r0_valid ? 1u : 0u;
  out[29] = out[30] = out[31] = 0;
  put_f64(out + 32, cfg->r0);
  if (cfg->interval_count)
  {
    uint32_t len = 2;
    for (unsigned int i = 0; i < cfg->interval_count; ++i)
      len += INTERVAL_FIXED + cfg->intervals[i].name_len;
    if (offset + 4u + len > capacity - 4u)
      return 0;
    put16(out + offset, DRMS_USER_TLV_INTERVALS);
    put16(out + offset + 2, (uint16_t)len);
    put16(out + offset + 4, cfg->interval_count);
    uint32_t o = offset + 6;
    for (unsigned int i = 0; i < cfg->interval_count; ++i)
    {
      const IntervalEntry *e = &cfg->intervals[i];
      put16(out + o, e->id);
      out[o + 2] = e->level;
      out[o + 3] = e->last_upper_closed ? 1u : 0u;
      put_f64(out + o + 4, e->lo);
      put_f64(out + o + 12, e->hi);
      put_f64(out + o + 20, e->h);
      out[o + 28] = e->name_len;
      memcpy(out + o + 29, e->name, e->name_len);
      o += INTERVAL_FIXED + e->name_len;
    }
    offset += 4u + len;
  }
  if (cfg->rate_hz)
  {
    /* 监测参数是可选段：仅已配置时编码（rate 0 = 未配置，算法层报 UNCONFIGURED） */
    if (offset + 4u + 36u > capacity - 4u)
      return 0;
    put16(out + offset, DRMS_USER_TLV_PARAMS);
    put16(out + offset + 2, 36);
    put32(out + offset + 4, cfg->rate_hz);
    put64(out + offset + 8, cfg->tau_us);
    put64(out + offset + 16, cfg->warmup_us);
    put64(out + offset + 24, cfg->confirm_us);
    put64(out + offset + 32, cfg->stale_timeout_us);
    offset += 40;
  }
  if ((uint32_t)cfg->extra_length > capacity - offset - 4u)
    return 0;
  memcpy(out + offset, cfg->extra, cfg->extra_length);
  offset += cfg->extra_length;
  if (offset + 4u > capacity)
    return 0;
  put32(out + 8, offset + 4u); /* 回填真实总长，CRC 覆盖含长度字段的完整头 */
  put32(out + offset, drms_crc32(out, offset));
  return offset + 4;
}

uint32_t drms_user_config_export(uint8_t *out, uint32_t capacity)
{
  if (!out || !have_config || unsupported_schema)
    return 0;
  return encode_body(&run, out, capacity);
}

static int validate_encoded(const uint8_t *encoded, size_t length, RunConfig *out)
{
  if (length < 44 || length > DRMS_USER_BODY_MAX)
    return 0; /* 长度不要求 4 对齐：TLV 自然长度，页内编程时按块补白 */
  if (memcmp(encoded, MAGIC_PREFIX, 7) != 0 || encoded[7] != SCHEMA_VERSION)
    return 0;
  uint32_t body_len = get32(encoded + 8);
  if (body_len != length)
    return 0;
  if (get32(encoded + length - 4) != drms_crc32(encoded, length - 4))
    return 0;
  RunConfig *cfg = &transaction_workspace;
  memset(cfg, 0, sizeof(*cfg));
  cfg->config_version = get64(encoded + 12);
  cfg->calibration_version = get64(encoded + 20);
  cfg->r0_valid = encoded[28] & 1u;
  cfg->r0 = get_f64(encoded + 32);
  if (cfg->r0_valid && (!finite(cfg->r0) || cfg->r0 <= 0.0))
    return 0;
  if (!parse_tlv(encoded, (uint32_t)length, cfg))
    return 0;
  *out = *cfg;
  return 1;
}

/* ---- 页提交（擦→写→读回→提交标志→读回；任意掉电得完整旧或新页） ---- */

static int page_commit(unsigned int page, const uint8_t *body, uint32_t body_len)
{
  uint8_t quad[16] __attribute__((aligned(16)));
  if (!drms_user_backend_begin())
    return 0;
  int ok = drms_user_backend_erase(page);
  for (uint32_t offset = 0; ok && offset < body_len; offset += 16)
  {
    memset(quad, 0xFF, sizeof(quad));
    uint32_t chunk = body_len - offset < 16 ? body_len - offset : 16;
    memcpy(quad, body + offset, chunk);
    ok = drms_user_backend_program(page, offset, quad);
  }
  if (ok)
  {
    uint8_t verify[16];
    for (uint32_t offset = 0; ok && offset < body_len; offset += 16)
    {
      uint32_t chunk = body_len - offset < 16 ? body_len - offset : 16;
      ok = drms_user_backend_read(page, offset, verify, 16) &&
           !memcmp(verify, body + offset, chunk);
    }
  }
  if (ok)
  {
    memset(quad, 0xFF, sizeof(quad));
    memcpy(quad, COMMIT_MAGIC, 4);
    put32(quad + 4, (uint32_t)body_len);
    put32(quad + 8, drms_crc32(body, body_len - 4));
    ok = drms_user_backend_program(page, DRMS_USER_PAGE_SIZE - 16u, quad);
  }
  if (ok)
  {
    uint8_t verify[16];
    ok = drms_user_backend_read(page, DRMS_USER_PAGE_SIZE - 16u, verify, 16) &&
         !memcmp(verify, quad, 16);
  }
  drms_user_backend_end();
  return ok;
}

/* 页有效性：识别前缀 + 结构长度 + 提交标志 + CRC 一致；
 * schema 版本字节任意（未来 schema 页是"有效但不可解释"）。 */
static int page_probe(unsigned int page, uint64_t *version, uint32_t *body_len)
{
  uint8_t head[40], commit[16], crc_bytes[4];
  if (!drms_user_backend_read(page, 0, head, sizeof(head)))
    return 0;
  if (memcmp(head, MAGIC_PREFIX, 7) != 0)
    return 0;
  uint32_t len = get32(head + 8);
  if (len < 44 || len > DRMS_USER_BODY_MAX)
    return 0;
  if (!drms_user_backend_read(page, DRMS_USER_PAGE_SIZE - 16u, commit, 16))
    return 0;
  if (memcmp(commit, COMMIT_MAGIC, 4) != 0 || get32(commit + 4) != len)
    return 0;
  if (!drms_user_backend_read(page, len - 4u, crc_bytes, 4))
    return 0;
  if (get32(crc_bytes) != get32(commit + 8))
    return 0;
  if (!drms_user_backend_read(page, 0, transaction_body, len) ||
      drms_crc32(transaction_body, len - 4u) != get32(crc_bytes))
    return 0;
  *version = get64(head + 12);
  *body_len = len;
  return 1;
}

void drms_user_config_load(void)
{
  drms_user_config_init();
  uint64_t va, vb;
  uint32_t la, lb;
  int pa = page_probe(0, &va, &la);
  int pb = page_probe(1, &vb, &lb);
  if (!pa && !pb)
    return; /* 出厂默认：UNCONFIGURED，两页可在下次提交时使用 */
  unsigned int best;
  uint64_t version;
  uint32_t len;
  if (pa && pb)
  {
    best = va >= vb ? 0u : 1u;
    version = va >= vb ? va : vb;
    len = va >= vb ? la : lb;
  }
  else
  {
    best = pa ? 0u : 1u;
    version = pa ? va : vb;
    len = pa ? la : lb;
  }
  active_page = (int32_t)best;
  persisted_version = version;
  run_version = version;
  uint8_t *body = transaction_body;
  if (!drms_user_backend_read(best, 0, body, len))
    return;
  if (body[7] != SCHEMA_VERSION)
  {
    /* 未来 schema：保留原始页；普通保存/apply 拒绝覆盖（R3）。 */
    unsupported_schema = 1;
    return;
  }
  if (!validate_encoded(body, len, &run))
    return; /* 提交有效但内容损坏：出厂默认，页保持供诊断 */
  have_config = 1;
  dirty = 0;
  if (run.r0_valid && run.calibration_version != calibration_generation_now)
    run.r0_valid = 0; /* 校准代次变化：旧 R0 依赖不匹配 → 失效（可诊断不可用） */
}

DRMS_Result drms_user_config_apply(const uint8_t *encoded, size_t length,
                                   uint64_t expected_version)
{
  if (!encoded || !length)
    return DRMS_INVALID;
  if (unsupported_schema)
    return DRMS_UNSUPPORTED; /* 未知 schema：普通路径不得覆盖 */
  if (expected_version != run_version)
    return DRMS_STALE;
  if (!validate_encoded(encoded, length, &staged))
    return DRMS_INVALID;
  have_staged = 1;
  ++run_version;
  dirty = 1;
  return DRMS_OK;
}

DRMS_Result drms_user_config_save(uint64_t expected_version)
{
  if (unsupported_schema)
    return DRMS_UNSUPPORTED; /* 未知 schema：拒绝一切普通写路径 */
  if (expected_version != run_version)
    return DRMS_STALE;
  if (!dirty)
    return DRMS_NO_CHANGE;
  RunConfig *out = &transaction_workspace;
  *out = have_staged ? staged : run;
  out->config_version = run_version;
  uint8_t *body = transaction_body;
  uint32_t body_len = encode_body(out, body, sizeof(transaction_body));
  if (!body_len)
    return DRMS_INVALID;
  unsigned int page = active_page == 0 ? 1u : 0u;
  if (!page_commit(page, body, body_len))
    return DRMS_IO_ERROR; /* 旧页未动；未保存标志保留 */
  run = *out;
  have_staged = 0;
  persisted_version = run_version;
  dirty = 0;
  active_page = (int32_t)page;
  have_config = 1;
  return DRMS_OK;
}

DRMS_Result drms_user_config_commit_baseline(double r0, uint64_t expected_version,
                                             uint64_t calibration_version)
{
  if (unsupported_schema)
    return DRMS_UNSUPPORTED;
  if (!finite(r0) || r0 <= 0.0)
    return DRMS_INVALID;
  if (expected_version != run_version)
    return DRMS_STALE;
  RunConfig *out = &transaction_workspace;
  *out = have_staged ? staged : run;
  out->r0 = r0;
  out->r0_valid = 1;
  out->calibration_version = calibration_version;
  out->config_version = run_version + 1u; /* 配置与 R0 一起提交、一起发布 */
  uint8_t *body = transaction_body;
  uint32_t body_len = encode_body(out, body, sizeof(transaction_body));
  if (!body_len)
    return DRMS_INVALID;
  unsigned int page = active_page == 0 ? 1u : 0u;
  if (!page_commit(page, body, body_len))
    return DRMS_IO_ERROR; /* 失败保留旧 R0 与未保存状态 */
  run = *out;
  have_staged = 0;
  run_version = out->config_version;
  persisted_version = run_version;
  dirty = 0;
  active_page = (int32_t)page;
  have_config = 1;
  return DRMS_OK;
}

uint32_t drms_user_config_get_monitor(DRMS_MonitorConfig *out)
{
  uint8_t clk2;
  if (!out || !have_config || !drms_rate_register(run.rate_hz, &clk2))
    return 0;
  uint64_t minimum_stale = (128000000ULL + run.rate_hz - 1U) / run.rate_hz;
  if (minimum_stale < 10000U)
    minimum_stale = 10000U;
  if (run.stale_timeout_us < minimum_stale)
    return 0;
  memset(out, 0, sizeof(*out));
  out->rate_hz = run.rate_hz;
  out->tau_us = run.tau_us;
  out->warmup_us = run.warmup_us;
  out->confirm_us = run.confirm_us;
  out->stale_timeout_us = run.stale_timeout_us;
  out->r0 = run.r0;
  out->baseline_valid = run.r0_valid != 0;
  out->interval_count = run.interval_count;
  for (unsigned int i = 0; i < run.interval_count; ++i)
  {
    out->intervals[i].id = run.intervals[i].id;
    out->intervals[i].level = run.intervals[i].level;
    out->intervals[i].last_upper_closed = run.intervals[i].last_upper_closed != 0;
    out->intervals[i].lo = run.intervals[i].lo;
    out->intervals[i].hi = run.intervals[i].hi;
    out->intervals[i].h = run.intervals[i].h;
  }
  return 1;
}

uint32_t drms_user_config_get_intervals(uint16_t *count, double *lo, double *hi,
                                        double *h, uint16_t *ids, uint8_t *levels)
{
  if (!have_config || !run.interval_count || !count)
    return 0;
  *count = run.interval_count;
  if (lo && hi && h && ids && levels)
  {
    for (unsigned int i = 0; i < run.interval_count; ++i)
    {
      lo[i] = run.intervals[i].lo;
      hi[i] = run.intervals[i].hi;
      h[i] = run.intervals[i].h;
      ids[i] = run.intervals[i].id;
      levels[i] = run.intervals[i].level;
    }
  }
  return 1;
}
