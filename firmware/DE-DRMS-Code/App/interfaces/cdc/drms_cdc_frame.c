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
