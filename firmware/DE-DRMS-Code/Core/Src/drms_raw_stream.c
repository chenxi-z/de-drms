/*****************************************************************************
 * 文件：drms_raw_stream.c
 * 职责：RAW 实时流攒批状态机（见 drms_raw_stream.h 的契约说明）。
 *
 * 批槽布局（pre-COBS 完整 v2 帧，最长 1,040 B；换代冲刷可产生短批，元数据紧随数据）：
 *   [0]      major=2        [1]      kind=3(事件)   [2:4]  opcode=131
 *   [4:8]    session(消费者) [8:16]  request_id=0   [16:18] payload_len（完成时补）
 *   [18:20]  flags=0
 *   [20:24]  data TLV 头（tag 54 必填，len=n×16，完成时补）
 *   [24:24+16n)  n×16 B 原始记录帧（生产者填充）
 *   其后 52 B 元数据 TLV（完成时写）：sequence(62) / sample_generation(21) /
 *   sample_index(22) / rate(30) / lost(63)；末 4 B CRC-32 覆盖其前全部字节。
 * 满批时载荷 1016 ≤ 1024；线上最长 1040+COBS(≤5)+定界符 = 1046。
 *
 * SRAM4 预算：2×1040（双槽）+ 1048（编码缓冲）+ 状态 ≈ 3.2 KiB（区余量 4,072 B）。
 * 缓冲不依赖复位清零：批头在每批开始时整体重写，CRC 每次发送前重算。
 *****************************************************************************/
#include "drms_raw_stream.h"
/* 与 drms_cdc.c 同款相对路径：Core 层引用 App 的帧编码器，Makefile 无需加 -I。 */
#include "../../App/interfaces/cdc/drms_cdc_frame.h"
#include "drms_measurement.h"
#include "main.h"
#include <string.h>

#define RAW_SLOT_BYTES 1040u
#define RAW_WIRE_BYTES 1048u
#define RAW_REQ 0x8000u
#define RAW_META_LEN 52u

enum { MAIL_EMPTY = 0, MAIL_FULL = 1, MAIL_HELD = 2 };

static uint8_t slot[2][RAW_SLOT_BYTES] __attribute__((section(".drms_sram4_workspace")));
static uint8_t wire_buf[RAW_WIRE_BYTES] __attribute__((section(".drms_sram4_workspace")));
/* 共享状态：所有变更在 PRIMASK 短临界区内；subscribed 允许生产者原子读。 */
static uint32_t subscribed __attribute__((section(".drms_sram4_workspace")));
static uint32_t mail_state __attribute__((section(".drms_sram4_workspace")));
static uint32_t mail_idx __attribute__((section(".drms_sram4_workspace")));
static uint32_t stream_epoch __attribute__((section(".drms_sram4_workspace")));
static uint64_t lost_total __attribute__((section(".drms_sram4_workspace")));
static uint64_t stream_sequence __attribute__((section(".drms_sram4_workspace")));
static uint32_t period_ms __attribute__((section(".drms_sram4_workspace")));
/* 生产者私有（仅应用处理线程触碰；订阅重建不改写，靠 subscribed 原子读自愈）。
 * 同样放 SRAM4：主 RAM 门禁只剩个位数字节余量，任何新增主 RAM 静态变量都会超限。
 * SRAM4 是 NOLOAD 不清零，故 reset() 必须显式初始化这三个跨批状态。 */
#define SRAM4 __attribute__((section(".drms_sram4_workspace")))
static uint32_t producing SRAM4, active_idx SRAM4, batch_count SRAM4;
static uint32_t batch_gen SRAM4, batch_rate SRAM4;
static uint64_t batch_first_seq SRAM4;

static uint32_t crit_enter(void) { uint32_t mask = __get_PRIMASK(); __disable_irq(); return mask; }
static void crit_exit(uint32_t mask) { __set_PRIMASK(mask); }

static void put16(uint8_t *p, uint16_t v) { p[0] = (uint8_t)v; p[1] = (uint8_t)(v >> 8); }
static void put32(uint8_t *p, uint32_t v)
{
  p[0] = (uint8_t)v; p[1] = (uint8_t)(v >> 8); p[2] = (uint8_t)(v >> 16); p[3] = (uint8_t)(v >> 24);
}
static void put64(uint8_t *p, uint64_t v)
{
  put32(p, (uint32_t)v); put32(p + 4, (uint32_t)(v >> 32));
}
static void tlv_hdr(uint8_t *p, uint16_t tag, uint16_t length)
{
  put16(p, (uint16_t)(tag | RAW_REQ)); put16(p + 2, length);
}

void drms_raw_stream_reset(void)
{
  uint32_t m = crit_enter();
  subscribed = 0; mail_state = MAIL_EMPTY; mail_idx = 0;
  stream_epoch++; lost_total = 0; stream_sequence = 0; period_ms = 0;
  crit_exit(m);
  producing = 0; active_idx = 0; batch_count = 0;
  batch_gen = 0; batch_rate = 0; batch_first_seq = 0;
}

uint32_t drms_raw_stream_subscribe(uint32_t rate_hz)
{
  if (!rate_hz || rate_hz > DRMS_RAW_RATE_CAP) return 0;
  uint32_t m = crit_enter();
  lost_total = 0;
  stream_sequence = 0;   /* 流内序号随订阅重置，与 CURVE 一致 */
  stream_epoch++;
  subscribed = 1;
  /* 旧的完整批属于旧订阅：直接作废（消费者若还持有 HELD 批，由它按 epoch 收尾）。 */
  if (mail_state == MAIL_FULL) mail_state = MAIL_EMPTY;
  period_ms = (60000u + rate_hz - 1u) / rate_hz;
  crit_exit(m);
  return period_ms;
}

void drms_raw_stream_unsubscribe(void)
{
  uint32_t m = crit_enter();
  subscribed = 0;
  stream_epoch++;
  if (mail_state == MAIL_FULL) mail_state = MAIL_EMPTY;
  crit_exit(m);
}

uint32_t drms_raw_stream_active(void)
{
  return __atomic_load_n(&subscribed, __ATOMIC_ACQUIRE);
}

uint64_t drms_raw_stream_lost(void)
{
  uint32_t m = crit_enter();
  uint64_t lost = lost_total;
  crit_exit(m);
  return lost;
}

uint32_t drms_raw_stream_period_ms(void)
{
  uint32_t m = crit_enter();
  uint32_t period = period_ms;
  crit_exit(m);
  return period;
}

/* 批头重写（生产者独占活动槽，无需加锁）。载荷长度与元数据在完成时按实际帧数补。 */
static void raw_batch_begin(void)
{
  uint8_t *s = slot[active_idx];
  s[0] = 2; s[1] = 3;
  put16(s + 2, 131u);
  put32(s + 4, 0u);          /* 会话号由消费者补 */
  put64(s + 8, 0u);          /* 事件 request_id=0 */
  put16(s + 16, 0u);         /* payload_len：完成时按帧数补 */
  put16(s + 18, 0u);
  tlv_hdr(s + 20, 54u, 0u);  /* data TLV 头：len 完成时补 */
}

/* 批完成：生产者侧。按实际帧数补载荷长度与元数据，再尝试交接邮箱。
 * 邮箱空闲则零拷贝交换，否则整批丢弃并计 lost。 */
static void raw_batch_complete(void)
{
  uint8_t *s = slot[active_idx];
  uint32_t n = batch_count;
  put16(s + 22u, (uint16_t)(n * DRMS_RAW_FRAME_BYTES));
  put16(s + 16u, (uint16_t)(RAW_META_LEN + 4u + n * DRMS_RAW_FRAME_BYTES));
  uint8_t *meta = s + 24u + n * DRMS_RAW_FRAME_BYTES;
  tlv_hdr(meta, 62u, 8u);
  put64(meta + 4u, 0u);                    /* 流内序号：消费者补 */
  tlv_hdr(meta + 12u, 21u, 4u);
  put32(meta + 16u, batch_gen);
  tlv_hdr(meta + 20u, 22u, 8u);
  put64(meta + 24u, batch_first_seq);
  tlv_hdr(meta + 32u, 30u, 4u);
  put32(meta + 36u, batch_rate);
  tlv_hdr(meta + 40u, 63u, 8u);
  put64(meta + 44u, 0u);                   /* lost：消费者快照 */
  put32(meta + RAW_META_LEN, 0u);          /* CRC：消费者重算 */
  uint32_t m = crit_enter();
  if (mail_state == MAIL_EMPTY)
  {
    mail_idx = active_idx;
    mail_state = MAIL_FULL;
    active_idx ^= 1u;
    crit_exit(m);
  }
  else
  {
    lost_total += batch_count;
    crit_exit(m);
  }
  batch_count = 0;
}

void drms_raw_stream_feed(uint32_t generation, uint32_t sequence, uint32_t rate_hz,
                          const void *frame)
{
  if (!__atomic_load_n(&subscribed, __ATOMIC_ACQUIRE))
  {
    producing = 0;   /* 撤销订阅后残批就地作废，不计 lost */
    return;
  }
  /* batch_count==0 表示活动槽刚因完成/换代而交换，批头必须整体重写。 */
  if (!producing)
  {
    producing = 1;
    batch_count = 0;
    batch_gen = generation;
    batch_first_seq = sequence;
    batch_rate = rate_hz;
    raw_batch_begin();
  }
  else if (generation != batch_gen)
  {
    /* 换代：当前批立即冲刷（批不跨代次），本帧开启新批。 */
    raw_batch_complete();
    batch_gen = generation;
    batch_first_seq = sequence;
    batch_rate = rate_hz;
    raw_batch_begin();
  }
  else if (batch_count == 0)
  {
    batch_gen = generation;
    batch_first_seq = sequence;
    batch_rate = rate_hz;
    raw_batch_begin();
  }
  memcpy(slot[active_idx] + 24u + 16u * batch_count, frame, DRMS_RAW_FRAME_BYTES);
  batch_count++;
  if (batch_count >= DRMS_RAW_BATCH_FRAMES)
    raw_batch_complete();
}

unsigned drms_raw_stream_publish(uint32_t session,
                                 int (*send)(void *context, const uint8_t *data,
                                             size_t size, uint32_t priority),
                                 void *send_context,
                                 int (*can_send)(void *context, uint32_t priority),
                                 void *cansend_context)
{
  uint8_t *s;
  uint32_t my_epoch;
  uint32_t m = crit_enter();
  if (!subscribed || mail_state != MAIL_FULL)
  {
    crit_exit(m);
    return 0;
  }
  s = slot[mail_idx];
  mail_state = MAIL_HELD;
  my_epoch = stream_epoch;
  crit_exit(m);

  /* 发送队列无空间：批留槽重试（延时不计 lost——尚未"未交付"）。
   * 订阅此刻若被重建，epoch 不等，后面统一按作废路径收尾。 */
  if (can_send && !can_send(cansend_context, 0))
  {
    m = crit_enter();
    if (stream_epoch == my_epoch && mail_state == MAIL_HELD)
      mail_state = MAIL_FULL;
    crit_exit(m);
    return 0;
  }

  m = crit_enter();
  uint64_t sequence = ++stream_sequence;
  crit_exit(m);
  put32(s + 4, session);
  /* 元数据紧随数据（换代冲刷会产生短批）：payload_len 定位动态偏移。 */
  uint32_t payload_len = (uint32_t)s[16] | ((uint32_t)s[17] << 8);
  uint32_t meta_off = 20u + payload_len - RAW_META_LEN;
  uint32_t frames = payload_len >= RAW_META_LEN + 4u
                        ? (payload_len - RAW_META_LEN - 4u) / DRMS_RAW_FRAME_BYTES : 0u;
  put64(s + meta_off + 4u, sequence);
  m = crit_enter();
  uint64_t lost_now = lost_total;
  uint32_t go = subscribed && stream_epoch == my_epoch;
  crit_exit(m);
  put64(s + meta_off + 44u, lost_now);
  uint32_t raw_len = 20u + payload_len + 4u;
  put32(s + meta_off + RAW_META_LEN, drms_crc32(s, meta_off + RAW_META_LEN));
  size_t wire_len = drms_cdc_frame_encode(s, raw_len, wire_buf, sizeof(wire_buf));

  m = crit_enter();
  go = go && subscribed && stream_epoch == my_epoch;
  crit_exit(m);
  if (go && send)
    go = send(send_context, wire_buf, wire_len, 0) ? 1u : 0u;
  if (!go)
  {
    /* 编码期间订阅被重建（该批不属于任何在途订阅，不计 lost），
     * 或发送未投递（F-3 语义：计入 lost）。 */
    m = crit_enter();
    if (stream_epoch == my_epoch)
      lost_total += frames;
    crit_exit(m);
  }
  m = crit_enter();
  if (mail_state == MAIL_HELD)
    mail_state = MAIL_EMPTY;
  crit_exit(m);
  return go ? frames : 0u;
}
