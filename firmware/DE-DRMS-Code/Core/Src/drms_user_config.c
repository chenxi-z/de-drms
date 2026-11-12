/*****************************************************************************
 * 文件：drms_user_config.c
 * 职责：用户配置与基线 R₀ 的持久化——把"这台仪器该按什么规则工作"存进 Flash，
 *       并在断电重启后原样取回。
 *
 * 存的是什么：
 *   采样率、滤波器时间常数（tau/warmup/confirm）、读数过期阈值、
 *   基线 R₀、判级区间表（每项含上下界、回差、等级、方向）、区间名称。
 *   简言之：除测量数据以外、需要跨重启保留的一切。
 *
 * 为什么要两页交替（A/B）：
 *   Flash 擦除是按扇区进行的，擦写过程中掉电会让整页失效。只用一页的话，
 *   一次掉电就把配置连同旧值一起弄丢。用 A/B 两页交替写入，任何时刻
 *   至少有一页是完整的——写入新值时先擦另一页、写完并校验通过才认它，
 *   失败就回退到旧页。这就是"至少保一份可用配置"的全部意义。
 *
 * 记录格式与提交协议：
 *   每页内容 = 魔数前缀 + schema 版本 + TLV 负载 + CRC32 + 提交标记。
 *   关键在于"提交标记必须最后单独写"：只有在整页内容都写对、CRC 校验通过后，
 *   才写那 16 字节的提交四字组。掉电发生在提交之前，这一页就被视为无效，
 *   自然回退到另一页——不需要额外的日志或事务机制。
 *
 * TLV 负载的组成：
 *   1 号 判级区间表
 *   2 号 监测参数（速率、时间常数、过期阈值、R₀）
 *   0xD701 基线策略（兼容旧版）
 *   0xD702 完整的线上设置（协议下发的原始字节，用于原样回读）
 *   3 号 别名（区间名称）
 *   未知的 TLV 会被**原样保留**而不是丢弃，这样新版固件写入的字段
 *   在旧版固件里跑一轮之后不会被抹掉——前向兼容就靠这一条。
 *
 * 版本管理：
 *   运行版（run_version）和已存版（saved_version）分开记。
 *   协议要求主机在下发配置时带上 expected_version，两者不符就拒绝，
 *   避免"基于过期配置做修改"导致的静默覆盖。
 *
 * 与基线的绑定：
 *   基线 R₀ 与它建立时的采样配置绑定。一旦采样率或滤波参数变了，
 *   旧基线不再成立，必须显式作废（invalidate_baseline），
 *   否则会拿旧基准去判新条件下的数据。
 *****************************************************************************/

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
#define DRMS_USER_TLV_WIRE_SETTINGS 0xD702u

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
/* 事务工作区。只有串行化的配置属主（应用线程）会用它，
 * 所以不需要加锁——同一时刻只可能有一个配置事务在进行。 */
static RunConfig transaction_workspace;
/* 纯 CPU 用的暂存区，放在 SRAM4。
 * 每次使用前都会先写满再读，因此不依赖启动时清零；
 * 也不参与外设 DMA，所以放在这个非 DMA 可达的区段是安全的。 */
static uint8_t transaction_body[DRMS_USER_BODY_MAX] __attribute__((section(".drms_sram4_workspace")));
static uint64_t run_version, persisted_version;
static uint32_t dirty, unsupported_schema, have_config;
static int32_t active_page = -1;
static uint64_t calibration_generation_now;

/* 初始化配置子系统为"空配置"状态。
 *
 * 这里不读 Flash——读取在 drms_user_config_load 里做，由应用层在合适的时机调用。
 * 这样单元测试可以先 init 再手工灌入期望的配置，不必依赖真实介质。
 *
 * active_page = -1 表示"还不知道当前有效页是哪一页"，等 load 时确定。 */
void drms_user_config_init(void)
{
  memset(&run, 0, sizeof(run));
  memset(&transaction_workspace, 0, sizeof(transaction_workspace));
  run_version = persisted_version = 0;
  dirty = unsupported_schema = have_config = 0;
  active_page = -1;
}

/* 告知配置层"当前使用的校准是哪一代"。
 *
 * 基线 R₀ 只有在产生它的那一代校准下才有意义。校准一变（重新校准、或从
 * Flash 载入了另一代系数），旧基线立刻作废——不能让它悄悄复活。
 *
 * 注意这里只清 run.r0_valid（内存中的有效标志），不擦 Flash：
 * 已存的数据保留下来供诊断，重启后 load 会再做同样的依赖检查。 */
void drms_user_config_set_calibration_generation(uint64_t generation)
{
  calibration_generation_now = generation;
  /* 基线只在"产生它的那一代校准"下才有意义。
   * 这里只清内存里的有效标志，Flash 中的数据保留供诊断；
   * 重启后 load 会做同样的依赖检查。已作废的 R₀ 不得被复活。 */
  if (run.r0_valid && run.calibration_version != generation)
    run.r0_valid = 0;
}
/* 显式作废基线。用于"采样配置已改变，旧基线不再成立"的场合。
 * 只清有效标志，不删 R₀ 数值本身——界面可能还想显示上一次的值。 */
void drms_user_config_invalidate_baseline(void)
{
  run.r0_valid = 0;
}

/* 以下一组是给其他模块用的访问器，都是直接读内存字段，不需要同步。
 *
 * run_version      当前运行配置的版本号（每次成功应用配置递增）
 * persisted_version 已写入 Flash 的版本号
 * dirty            运行版与已存版不一致（有未保存的改动）
 * r0_valid/r0      基线是否有效、数值多少
 * r0_calibration_version 基线是在哪一代校准下建立的
 * unsupported_schema 载入时发现 schema 版本不认识
 *
 * 版本号分开记的意义：协议用 expected_version 做乐观并发控制，
 * 主机必须知道"我改的是不是最新那份"，否则会静默覆盖别人的修改。 */
uint64_t drms_user_config_run_version(void) { return run_version; }
uint64_t drms_user_config_persisted_version(void) { return persisted_version; }
uint32_t drms_user_config_dirty(void) { return dirty; }
uint32_t drms_user_config_r0_valid(void) { return run.r0_valid; }
double drms_user_config_r0(void) { return run.r0; }
uint64_t drms_user_config_r0_calibration_version(void) { return run.calibration_version; }
uint32_t drms_user_config_unsupported_schema(void) { return unsupported_schema; }

/* NaN 与无穷检查。配置文件里出现非有限值一律视为损坏——绝不能让它进算法。 */
static int finite(double v) { return v == v && v < 1e308 && v > -1e308; }

/* 检查一份监测配置是否落在固件实际支持的范围内。
 *
 * 目前只校验两件：
 *   1. 采样率必须是固件认识的那几档（drms_rate_register 是唯一权威表）；
 *   2. 读数过期阈值不能小于"128000 个采样周期"的下限，
 *      否则刚采到就会被判为过期，界面永远不会显示有效值。
 *
 * 返回 0 表示这份配置不能接受——宁可拒绝，也不要用一份跑不起来的配置启动。 */
static int supported_monitor(const RunConfig *cfg)
{
  uint8_t reg;
  if (!drms_rate_register(cfg->rate_hz, &reg))
    return 0;
  uint64_t min_stale = (128000000ULL + cfg->rate_hz - 1U) / cfg->rate_hz;
  if (min_stale < 10000U)
    min_stale = 10000U;
  return cfg->stale_timeout_us >= min_stale;
}

/* ---- 小端序列化助手 ----
 *
 * Flash 里的字节布局必须与主机架构无关，所以统一按小端、无填充写出
 * （与协议一致）。不用结构体直拷，因为结构体会带编译器插入的对齐空洞，
 * 而这些空洞在不同编译器/版本下可能不同，跨版本读回来就会错位。
 *
 * put* 写、get* 读，get_f64 用按位重解释而不是强制类型转换，
 * 避免违反严格别名规则。 */
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

/* 校验一段字节是否是合法 UTF-8（区间名称用）。
 *
 * 只做最基本的结构校验：合法的多字节序列、不出现被截断的尾字节。
 * 不检查 Unicode 码点是否被分配——区间名称是给人看的短标签，
 * 这里的目标是"不要存进一段会导致显示乱码的字节"，不是做严格的字符集验证。 */
static int utf8_valid(const uint8_t *s, uint32_t length)
{
  uint32_t i = 0;
  while (i < length)
  {
    uint8_t c = s[i];
    uint32_t need;
    if (!c)
      return 0;
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
    if (need == 2 && s[i] == 0xED && s[i + 1] >= 0xA0)
      return 0; /* UTF-16 surrogate code points are not UTF-8 scalar values */
    if (need == 3 && s[i] == 0xF0 && s[i + 1] < 0x90)
      return 0;
    if (need == 3 && s[i] == 0xF4 && s[i + 1] >= 0x90)
      return 0;
    i += need + 1;
  }
  return 1;
}

#define INTERVAL_FIXED 29u /* id2+level1+flags1+lo8+hi8+h8+name_len1 */

/* 校验判级区间表的合法性。
 *
 * 每条区间的硬性约束（来自架构文档 C6）：
 *   · 下界必须小于上界；
 *   · 回差 h 必须为正，且 2h 要严格小于区间宽度——否则迟滞区会吃掉整个区间，
 *     等级会在两点之间来回跳；
 *   · 区间之间必须有序且不重叠（后一项的下界不小于前一项的上界）。
 *
 * 这些不是"建议"而是 correctness 的前提：违反任何一条，判级结果都没有意义，
 * 所以宁可在入口把整份配置拒掉。
 *
 * 返回 1 合法；0 表示这份区间表不可用。 */
static int validate_intervals(const uint8_t *value, uint32_t length)
{
  if (length < 2)
    return 0;
  uint16_t count = get16(value);
  if (count > DRMS_USER_INTERVALS_MAX)
    return 0;
  uint32_t offset = 2;
  double prev_hi = 0.0;
  double prev_h = 0.0;
  uint16_t ids[DRMS_USER_INTERVALS_MAX];
  int have_prev = 0;
  for (uint16_t i = 0; i < count; ++i)
  {
    if (offset + INTERVAL_FIXED > length)
      return 0;
    const uint8_t *rec = value + offset;
    uint16_t id = get16(rec);
    if (rec[2] > 3u || (rec[3] & ~1u) || ((rec[3] & 1u) && i + 1u != count))
      return 0;
    for (uint16_t j = 0; j < i; ++j)
      if (ids[j] == id)
        return 0;
    ids[i] = id;
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
    if (have_prev && lo > prev_hi && !(prev_h + h < lo - prev_hi))
      return 0; /* 两侧回差不得吞没整个空隙 */
    prev_hi = hi;
    prev_h = h;
    have_prev = 1;
    offset += INTERVAL_FIXED + name_len;
  }
  return offset == length;
}

/* 解析一整块 TLV 负载：把已知字段填进 cfg，未知字段原样留存。
 *
 * 这是配置格式的核心解析器，三个要点：
 *
 *   · 未知 TLV 不丢弃，而是整段拷进 cfg->extra。这是前向兼容的关键——
 *     新版固件写入的字段，在旧版固件上跑过一轮之后仍然存在，
 *     不会因为"旧版不认识"就被抹掉。
 *
 *   · 每个已知字段都要校验：重复出现、长度不符、内容非法，一律整份拒绝。
 *     不做"跳过坏的、保留好的"这种部分接受——配置要么完整生效要么不生效。
 *
 *   · 解析结束必须确认负载恰好用完，多出或短缺的字节都说明数据已损坏。
 *
 * 返回 1 解析成功；0 表示这份负载不可用。 */
static int parse_tlv(const uint8_t *body, uint32_t body_len, RunConfig *cfg)
{
  cfg->interval_count = 0;
  cfg->extra_length = 0;
  uint32_t offset = 40;
  uint32_t baseline_seen = 0;
  uint32_t singleton_seen = 0;
  while (offset + 4u <= body_len - 4u)
  {
    uint16_t type = get16(body + offset);
    uint16_t len = get16(body + offset + 2);
    if (type >= DRMS_USER_TLV_INTERVALS && type <= DRMS_USER_TLV_ALIAS)
    {
      uint32_t bit = 1u << (type - 1u);
      if (singleton_seen & bit)
        return 0;
      singleton_seen |= bit;
    }
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

/* 取出基线策略（建立 R₀ 所需的最少样本数、稳定容限等）。
 * 返回 0 表示当前配置里没有这份信息。 */
uint32_t drms_user_config_get_baseline_policy(DRMS_BaselinePolicy *out)
{
  if (!out)
    return 0;
  memset(out, 0, sizeof(*out));
  const RunConfig *cfg = &run;
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

/* 基线建立时使用的采样率。用于判断"当前速率是否还和基线匹配"。 */
uint32_t drms_user_config_baseline_rate(void)
{
  return run.rate_hz;
}

/* 把运行配置编码成 TLV 负载。
 *
 * 编码顺序即写入顺序：区间表 → 监测参数 → 基线策略 → 线上设置原文 → 别名。
 * extra 里留存的未知 TLV 会原样附在最后，保证"读进来什么、写出去还是什么"。
 *
 * 容量不足时返回 0 而不是截断——截断的配置比没有配置更危险。 */
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

/* 导出一份完整的配置块（含魔数、版本、CRC），用于写入 Flash。
 * 返回写出的字节数；0 表示容量不足。 */
uint32_t drms_user_config_export(uint8_t *out, uint32_t capacity)
{
  if (!out || !have_config || unsupported_schema)
    return 0;
  return encode_body(&run, out, capacity);
}

/* 取"线上格式"的配置——即原样存下协议下发的那份字节。
 *
 * 与 export 的区别：export 是给 Flash 用的（带魔数和提交协议），
 * 这个是给 GET_CONFIG 回复用的，主机看到的必须和它当初下发的一致。
 *
 * 没有保存过配置时返回 0。 */
uint32_t drms_user_config_get_wire(uint8_t *out, uint32_t capacity)
{
  if (!out || !have_config || unsupported_schema) return 0;
  const uint8_t *value = NULL;
  uint32_t size = 0, offset = 0;
  while (offset + 4u <= run.extra_length)
  {
    uint16_t type = get16(run.extra + offset);
    uint16_t len = get16(run.extra + offset + 2u);
    offset += 4u;
    if (len > run.extra_length - offset) return 0;
    if (type == DRMS_USER_TLV_WIRE_SETTINGS)
    {
      if (value || !len || len > 1024u) return 0;
      value = run.extra + offset;
      size = len;
    }
    offset += len;
  }
  if (offset != run.extra_length || !value || size > capacity) return 0;
  memcpy(out, value, size);
  return size;
}

/* 校验一份完整的配置块并解析成 RunConfig。
 *
 * 逐层验证，任何一层不过就整份拒绝：
 *   1. 长度、魔数前缀、schema 版本；
 *   2. CRC32（覆盖头部与负载）；
 *   3. TLV 结构（由 parse_tlv 完成）；
 *   4. 语义约束（采样率受支持、区间表自洽、时间常数有序等）。
 *
 * 这是所有"从外部进来的配置"的唯一入口——无论是从 Flash 读的还是协议下发的，
 * 都必须先过这里。返回 1 表示可用，0 表示这份数据不能信。 */
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

/* 从 Flash 载入配置。这是 A/B 两页机制的读取侧。
 *
 * 流程：
 *   1. 探测两页各自是否有效（魔数、CRC、提交标记齐全才算有效）；
 *   2. 两页都有效时选版本号更大的那页——版本号就是"新旧"的唯一依据；
 *   3. 只有一页有效就用它；两页都无效说明是出厂状态或数据已损坏，保持空配置；
 *   4. 载入后再检查基线与校准代次的依赖关系，不匹配就把基线作废。
 *
 * 关键：**绝不因为一页坏掉就说"没有配置"**。只要另一页还能读，配置就还在——
 * 这正是双页设计的目的。
 *
 * 载入失败不报错、也不擦除任何东西：坏数据留着供诊断，
 * 下次保存时会自然覆盖到另一页。 */
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
  uint8_t *body = transaction_body;
  for (unsigned attempt = 0; attempt < 2; ++attempt)
  {
    if (drms_user_backend_read(best, 0, body, len))
    {
      if (body[7] != SCHEMA_VERSION)
      {
        /* 就算回退，也不要去擦除一份"提交过但 schema 不认识"的数据。
         * 它可能是新版固件写的，当前固件只是读不懂——擦掉就等于把用户的配置销毁了。 */
        active_page = (int32_t)best;
        persisted_version = run_version = version;
        unsupported_schema = 1;
        return;
      }
      if (validate_encoded(body, len, &run))
      {
        active_page = (int32_t)best;
        persisted_version = run_version = version;
        have_config = 1;
        dirty = 0;
        if (run.r0_valid && run.calibration_version != calibration_generation_now)
          run.r0_valid = 0;
        return;
      }
    }
    /* CRC 正确不等于配置可用——语义校验可能不过（例如区间表自相矛盾）。
     * 这时先去看另一页：那边可能存着一份更旧但完全可用的配置。
     * 只有两页都不可用时才放弃。 */
    if ((best == 0 && pb) || (best == 1 && pa))
    {
      best ^= 1u;
      version = best ? vb : va;
      len = best ? lb : la;
    }
    else
      break;
  }
  /* 两页都通不过校验：不发布任何版本号，保持"无配置"状态。
   * 宁可让设备回到出厂默认，也不能把一份坏配置当成有效配置用。 */
}

/* 校验一份"准备应用"的配置，并在通过时写进候选结构。
 *
 * 与 validate_encoded 的区别：这里额外做业务层检查（例如 R₀ 与采样率的一致性），
 * 并且不改动运行态——只有真正 apply 之后才生效。
 *
 * 做成两步是为了支持"先试跑再提交"：应用层可以先用它验一遍，
 * 确认能跑起来再正式切换。 */
static DRMS_Result validate_candidate(const uint8_t *encoded, size_t length,
                                      uint64_t expected_version, RunConfig *candidate)
{
  if (!encoded || !length)
    return DRMS_INVALID;
  if (unsupported_schema)
    return DRMS_UNSUPPORTED; /* 未知 schema：普通路径不得覆盖 */
  if (expected_version != run_version)
    return DRMS_STALE;
  if (run_version == UINT64_MAX)
    return DRMS_INVALID;
  if (!validate_encoded(encoded, length, candidate))
    return DRMS_INVALID;
  if (!supported_monitor(candidate))
    return DRMS_INVALID;
  return DRMS_OK;
}

/* 预检：只验证这份配置能不能用，不改变任何状态。
 * 供上游在真正下发之前先问一句"这份配置行不行"。 */
DRMS_Result drms_user_config_preflight(const uint8_t *encoded, size_t length,
                                       uint64_t expected_version)
{
  return validate_candidate(encoded, length, expected_version, &transaction_workspace);
}

/* 应用一份配置：校验通过后写入运行态，并把版本号推进。
 *
 * 这里只改内存，不碰 Flash——"应用"和"保存"是两个独立动作，
 * 主机可以先应用、观察效果，满意了再保存。这样试错不需要反复擦写 Flash。
 *
 * expected_version 用作乐观并发控制：与当前运行版不符则拒绝，
 * 防止基于过期配置做修改而静默覆盖别人的改动。 */
DRMS_Result drms_user_config_apply(const uint8_t *encoded, size_t length,
                                   uint64_t expected_version)
{
  RunConfig *candidate = &transaction_workspace;
  DRMS_Result result = validate_candidate(encoded, length, expected_version, candidate);
  if (result != DRMS_OK)
    return result;
  /* 普通设置更新不得把现有基线悄悄抹掉。
   *
   * 具体做法：如果新配置里没带基线（candidate->r0_valid 为 0），
   * 就把旧基线数值原样保留下来，只是可能因为速率变化而失效。
   * 这样界面仍能显示"上一次的基线是多少"，而有效与否由依赖检查决定。
   *
   * 要真正建立新基线，只有 commit_baseline 这一条路径——
   * 不允许改个设置就顺带把基线换了。 */
  if (run.r0_valid && !candidate->r0_valid)
  {
    candidate->r0 = run.r0;
    candidate->calibration_version = run.calibration_version;
    candidate->r0_valid = candidate->rate_hz == run.rate_hz;
  }
  ++run_version;
  candidate->config_version = run_version;
  run = *candidate;
  have_config = 1;
  dirty = 1;
  return DRMS_OK;
}

/* 把当前运行配置写入 Flash。这是 A/B 两页机制的写入侧。
 *
 * 顺序极其关键，掉电安全性全靠它：
 *   1. 选"当前没在用"的那一页（避免擦掉唯一可用的数据）；
 *   2. 擦除该页；
 *   3. 写入全部内容（魔数 + 版本 + TLV + CRC）；
 *   4. 逐字节回读校验；
 *   5. **最后**才写提交四字组。
 *
 * 提交标记单独最后写，是整套机制的核心：只要它不在，这一页就被视为无效，
 * 读取方自然回退到另一页。因此"擦到一半掉电""写到一半掉电""校验不过"
 * 都不会损坏已有配置——最多是这次保存失败。
 *
 * 写入成功后推进 persisted_version，并把 dirty 清掉。 */
DRMS_Result drms_user_config_save(uint64_t expected_version)
{
  if (unsupported_schema)
    return DRMS_UNSUPPORTED; /* 未知 schema：拒绝一切普通写路径 */
  if (expected_version != run_version)
    return DRMS_STALE;
  if (!dirty)
    return DRMS_NO_CHANGE;
  RunConfig *out = &transaction_workspace;
  *out = run;
  out->config_version = run_version;
  uint8_t *body = transaction_body;
  uint32_t body_len = encode_body(out, body, sizeof(transaction_body));
  if (!body_len)
    return DRMS_INVALID;
  unsigned int page = active_page == 0 ? 1u : 0u;
  if (!page_commit(page, body, body_len))
    return DRMS_IO_ERROR; /* 旧页未动；未保存标志保留 */
  run = *out;
  persisted_version = run_version;
  dirty = 0;
  active_page = (int32_t)page;
  have_config = 1;
  return DRMS_OK;
}

/* 提交一条新的基线 R₀。
 *
 * 与普通配置保存的区别：基线要记下"它是在哪一代校准、哪个采样率下建立的"。
 * 这两个信息就是它日后能否继续使用的判据——任何一项不匹配，基线即失效。
 *
 * expected_version 同样用于并发控制：建立基线的过程要花几秒到几十秒，
 * 期间配置可能已被改动，那时这条基线就不该再写进去了。 */
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
  *out = run;
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
  run_version = out->config_version;
  persisted_version = run_version;
  dirty = 0;
  active_page = (int32_t)page;
  have_config = 1;
  return DRMS_OK;
}

/* 取出监测配置，转换成监测管线需要的格式。
 *
 * 返回 0 表示当前没有可用的监测配置（出厂状态），调用方应使用默认值。
 * 有配置但内容不支持（例如速率不在固件支持范围内）时也返回 0，
 * 让上层退回默认值而不是带着一份跑不起来的配置启动。 */
uint32_t drms_user_config_get_monitor(DRMS_MonitorConfig *out)
{
  if (!out || !have_config || !supported_monitor(&run))
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

/* 取出判级区间表，按数组形式给出（供界面或协议列举）。
 * 返回写入的条目数；0 表示没有配置区间。 */
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
