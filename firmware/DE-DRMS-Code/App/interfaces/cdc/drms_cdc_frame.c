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

size_t drms_cdc_frame_size(void) { return sizeof(DRMS_CDCFrame); }

void drms_cdc_frame_init(DRMS_CDCFrame *ctx)
{
  if (ctx)
    memset(ctx, 0, sizeof(*ctx));
}

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
