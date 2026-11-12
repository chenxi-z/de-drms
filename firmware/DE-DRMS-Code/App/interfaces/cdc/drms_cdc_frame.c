/*****************************************************************************
 * 文件：drms_cdc_frame.c
 * 职责：CDC v2 的流层——把字节流切成帧（COBS 解码 + CRC 校验），以及反向编码。
 *
 * 为什么需要 COBS：
 *   USB CDC 是纯字节流，没有消息边界。协议用 0x00 作为帧分隔符，
 *   而帧内容本身可能含 0——COBS（Consistent Overhead Byte Stuffing）
 *   把所有 0 都编码掉，只留结尾那个真正的分隔符，代价是每 254 字节多 1 字节。
 *   这样切帧只需要找 0，不需要任何转义状态机。
 *
 * 本层的三件事：
 *   1. 收字节、找分隔符、COBS 解码、校验长度与 CRC，得到一帧完整请求；
 *   2. 任何拆包/粘包都能正确处理（流式累积，不假设一次收完整帧）；
 *   3. 半帧超时：从首字节算起满 1000 ms 仍无分隔符就丢弃，
 *      防止一个坏帧把后续数据永远堵在缓冲区里。
 *
 * 错误处理原则：
 *   畸形帧、CRC 错误、未知主版本一律**静默丢弃并计数**，不做任何回应。
 *   因为此时连"这是不是本协议的帧"都无法确定，回应反而可能加重混乱。
 *   上层能观察到的是丢弃计数，而不是错误回复。
 *****************************************************************************/

#include "drms_cdc_frame.h"
#include "drms_measurement.h"
#include <string.h>

#define HEADER_SIZE 20u
#define CRC_SIZE 4u

static uint16_t get16(const uint8_t *p)
{
  return (uint16_t)(p[0] | ((uint16_t)p[1] << 8));
}

static uint32_t get32(const uint8_t *p)
{
  return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
         ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

/* 解帧上下文的大小，供调用方分配内存（避免把内部结构暴露出去）。 */
size_t drms_cdc_frame_size(void) { return sizeof(DRMS_CDCFrame); }

/* 复位解帧器到"等待新帧"状态。断线、复位后都要调用。 */
void drms_cdc_frame_init(DRMS_CDCFrame *ctx)
{
  if (ctx)
    memset(ctx, 0, sizeof(*ctx));
}

/* 对一个完整缓冲做 COBS 解码、长度检查与 CRC 校验。
 *
 * 三道关卡的顺序是有意的：先解码（否则连长度都无从谈起），
 * 再查长度范围，最后验 CRC。CRC 放最后是因为它最贵，
 * 前面能提前否掉的就不必算了。
 *
 * 返回 0 表示这一帧不可用（畸形、超长或 CRC 错），调用方丢弃即可。 */
static size_t decode(DRMS_CDCFrame *ctx)
{
  size_t input = 0, output = 0;
  while (input < ctx->length)
  {
    uint8_t code = ctx->encoded[input++];
    size_t count = (size_t)code - 1u;
    if (!code || count > ctx->length - input || count > DRMS_CDC_RAW_MAX - output)
      return 0;
    memcpy(ctx->decoded + output, ctx->encoded + input, count);
    input += count;
    output += count;
    if (code != 255u && input < ctx->length)
    {
      if (output == DRMS_CDC_RAW_MAX)
        return 0;
      ctx->decoded[output++] = 0;
    }
  }
  return output;
}

/* 半帧超时检查，由上层周期性调用。
 *
 * 若缓冲里已经堆了数据、但超过 1000 ms 还没有遇到分隔符，就整段丢弃。
 * 没有这一步，一个被截断的帧会让后面所有正常帧都排在它后面永远出不去。 */
void drms_cdc_frame_tick(DRMS_CDCFrame *ctx, uint32_t now_ms)
{
  if (ctx && ctx->length &&
      (uint32_t)(now_ms - ctx->started_ms) >= DRMS_CDC_FRAME_TIMEOUT_MS)
  {
    ++ctx->timeout;
    ctx->length = 0;
    ctx->discarding = 1;
  }
}

/* 喂入一个字节。这是流式解帧的主体。
 *
 * 逐字节处理的原因：USB CDC 不保证一次读到的就是完整帧，
 * 可能半个帧、也可能好几个帧粘在一起，只有按字节扫描才能覆盖所有情况。
 *
 * 遇到 0 就意味着一帧结束：取出缓冲、解码校验，成功则回调 on_frame。
 * 连续多个 0 直接忽略（COBS 允许，且线路上可能有多余分隔符）。
 *
 * 参数：on_frame 是上层回调，收到一帧完整请求时调用；user 原样传回。 */
void drms_cdc_frame_feed(DRMS_CDCFrame *ctx, uint8_t byte, uint32_t now_ms,
                         DRMS_CDCFrameHandler handler, void *user)
{
  if (!ctx)
    return;
  drms_cdc_frame_tick(ctx, now_ms);
  if (byte == 0)
  {
    if (ctx->discarding)
    {
      ctx->discarding = 0;
      ctx->length = 0;
      return;
    }
    if (!ctx->length)
      return;
    size_t length = decode(ctx);
    ctx->length = 0;
    if (length < HEADER_SIZE + CRC_SIZE || ctx->decoded[0] != 2u ||
        ctx->decoded[1] < 1u || ctx->decoded[1] > 3u ||
        get16(ctx->decoded + 16) != length - HEADER_SIZE - CRC_SIZE)
    {
      ++ctx->malformed;
      return;
    }
    if (get32(ctx->decoded + length - CRC_SIZE) != drms_crc32(ctx->decoded, length - CRC_SIZE))
    {
      ++ctx->crc_error;
      return;
    }
    if (handler)
      handler(user, ctx->decoded, length);
    return;
  }
  if (ctx->discarding)
    return;
  if (!ctx->length)
    ctx->started_ms = now_ms;
  if (ctx->length == sizeof(ctx->encoded))
  {
    ++ctx->overflow;
    ctx->length = 0;
    ctx->discarding = 1;
    return;
  }
  ctx->encoded[ctx->length++] = byte;
}

/* 把一帧原始内容做 COBS 编码并追加分隔符，得到可以直接上线的字节。
 *
 * 容量不足时返回 0，绝不输出半个帧——半个帧在线上会破坏后续所有帧的同步。
 * 返回值为实际的线上长度。 */
size_t drms_cdc_frame_encode(const uint8_t *raw, size_t length, uint8_t *out, size_t capacity)
{
  if (!raw || !out || length > DRMS_CDC_RAW_MAX || capacity < 2u)
    return 0;
  size_t code_index = 0, output = 1;
  uint8_t code = 1;
  for (size_t i = 0; i < length; ++i)
  {
    if (!raw[i])
    {
      out[code_index] = code;
      if (output >= capacity)
        return 0;
      code_index = output++;
      code = 1;
    }
    else
    {
      if (output >= capacity)
        return 0;
      out[output++] = raw[i];
      if (++code == 255u)
      {
        out[code_index] = code;
        if (output >= capacity)
          return 0;
        code_index = output++;
        code = 1;
      }
    }
  }
  out[code_index] = code;
  if (output >= capacity)
    return 0;
  out[output++] = 0;
  return output;
}

static int known_field(uint16_t id)
{
  return (id >= 1u && id <= 12u) || (id >= 16u && id <= 45u) ||
         (id >= 48u && id <= 64u) || (id >= 72u && id <= 85u);
}

int drms_cdc_fields_validate(const uint8_t *payload, size_t length,
    const DRMS_CDCFieldRule *rules, size_t rule_count, DRMS_CDCFieldView *views)
{
  DRMS_CDCFieldView found[64] = {{0}};
  uint64_t seen = 0;
  size_t offset = 0, fields = 0;
  if ((!payload && length) || rule_count > 64u || (rule_count && (!rules || !views)) || length > 1024u)
    return 1;
  for (size_t i = 0; i < rule_count; ++i)
  {
    if (!rules[i].id || rules[i].id > 0x7fffu || rules[i].min_len > rules[i].max_len ||
        rules[i].kind > 2u || rules[i].required > 1u)
      return 1;
    for (size_t j = 0; j < i; ++j)
      if (rules[j].id == rules[i].id)
        return 1;
  }
  while (offset < length)
  {
    if (++fields > 64u || length - offset < 4u)
      return 1;
    uint16_t tag = get16(payload + offset), id = tag & 0x7fffu;
    uint16_t size = get16(payload + offset + 2u);
    offset += 4u;
    if (!id || size > length - offset)
      return 1;
    size_t index = 0;
    while (index < rule_count && rules[index].id != id)
      ++index;
    if (index == rule_count)
    {
      if ((tag & 0x8000u) || known_field(id))
        return 1;
    }
    else
    {
      const DRMS_CDCFieldRule *rule = &rules[index];
      if ((seen & (UINT64_C(1) << index)) || size < rule->min_len || size > rule->max_len ||
          (rule->required && !(tag & 0x8000u)))
        return 1;
      if ((rule->kind == 1u && (size != 1u || payload[offset] > 1u)) ||
          (rule->kind == 2u && (size != 8u || (get32(payload + offset + 4u) & 0x7ff00000u) == 0x7ff00000u)))
        return 1;
      seen |= UINT64_C(1) << index;
      found[index].value = payload + offset;
      found[index].length = size;
    }
    offset += size;
  }
  for (size_t i = 0; i < rule_count; ++i)
    if (rules[i].required && !(seen & (UINT64_C(1) << i)))
      return 1;
  if (rule_count)
    memcpy(views, found, rule_count * sizeof(*views));
  return 0;
}

int drms_cdc_session_init(DRMS_CDCSession *state, DRMS_CDCEntropy entropy, void *context)
{
  if (!state)
    return 1;
  memset(state, 0, sizeof(*state));
  uint64_t boot = 0;
  if (!entropy || !entropy(context, &boot) || !boot)
    return 1;
  state->boot = boot;
  state->next_session = 1u;
  state->healthy = 1u;
  return 0;
}

int drms_cdc_session_hello(DRMS_CDCSession *state, uint32_t request_session,
                           uint64_t request_id, uint32_t *session)
{
  if (!state || !session || !state->healthy || request_session || request_id != 1u)
    return 1;
  if (!state->session)
  {
    if (!state->next_session)
      return 1;
    state->session = state->next_session++;
  }
  *session = state->session;
  return 0;
}

void drms_cdc_session_disconnect(DRMS_CDCSession *state)
{
  if (state)
    state->session = 0;
}
