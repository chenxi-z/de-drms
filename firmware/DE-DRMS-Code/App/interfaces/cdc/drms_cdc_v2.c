#include "drms_cdc_v2.h"
#include "drms_measurement.h"
#include "drms_control.h"
#include "drms_application.h"
#include <string.h>

static uint16_t get16(const uint8_t *p) { return (uint16_t)(p[0] | ((uint16_t)p[1] << 8)); }
static uint32_t get32(const uint8_t *p) { return (uint32_t)get16(p) | ((uint32_t)get16(p + 2) << 16); }
static uint64_t get64(const uint8_t *p) { return (uint64_t)get32(p) | ((uint64_t)get32(p + 4) << 32); }
static void put16(uint8_t *p, uint16_t v) { p[0] = (uint8_t)v; p[1] = (uint8_t)(v >> 8); }
static void put32(uint8_t *p, uint32_t v) { put16(p, (uint16_t)v); put16(p + 2, (uint16_t)(v >> 16)); }
static void put64(uint8_t *p, uint64_t v) { put32(p, (uint32_t)v); put32(p + 4, (uint32_t)(v >> 32)); }

static void tlv(uint8_t *raw, size_t *pos, uint16_t tag, const uint8_t *data, uint16_t size)
{
  put16(raw + *pos, tag | 0x8000u); put16(raw + *pos + 2, size); *pos += 4;
  memcpy(raw + *pos, data, size); *pos += size;
}

static void received(void *user, const uint8_t *request, size_t length)
{
  (void)length;
  DRMS_CDCV2 *ctx = user;
  if (request[1] != 1u || !ctx->session.healthy)
    return;
  uint16_t opcode = get16(request + 2), payload_len = get16(request + 16);
  uint32_t session = get32(request + 4);
  uint64_t id = get64(request + 8);
  uint16_t result = 0;
  DRMS_ControlCompletion operation;
  uint32_t have_operation = 0;
  DRMS_ApplicationSnapshot snapshot;
  uint32_t have_snapshot = 0;
  if (opcode == 1u)
  {
    if (get16(request + 18) ||
        drms_cdc_fields_validate(request + 20, payload_len, NULL, 0, NULL) ||
        drms_cdc_session_hello(&ctx->session, session, id, &session))
      return;
    if (!ctx->last_request) ctx->last_request = 1;
  }
  else
  {
    if (!ctx->session.session || session != ctx->session.session || id < 2u)
      return;
    if (id <= ctx->last_request)
      result = 4; /* stale: this minimal read-only implementation caches no requests */
    else
    {
      ctx->last_request = id;
      if (get16(request + 18))
        result = 3u;
      else if (opcode == 2u)
      {
        if (drms_cdc_fields_validate(request + 20, payload_len, NULL, 0, NULL))
          result = 3u;
        else if (!drms_application_snapshot(&snapshot))
          result = 2u;
        else
          have_snapshot = 1;
      }
      else if (opcode == 3u)
      {
        static const DRMS_CDCFieldRule rules[] = {{11, 8, 8, 0, 1}};
        DRMS_CDCFieldView fields[1];
        if (drms_cdc_fields_validate(request + 20, payload_len, rules, 1, fields))
          result = 3u;
        else
        {
          DRMS_Result query = drms_control_get_operation(get64(fields[0].value), &operation);
          if (query != DRMS_OK)
            result = (uint16_t)query;
          else
          {
            result = (uint16_t)operation.result;
            have_operation = 1;
          }
        }
      }
      else result = 11u; /* UNSUPPORTED */
    }
  }
  uint8_t *out = ctx->raw;
  memset(out, 0, 20);
  out[0] = 2; out[1] = 2; put16(out + 2, opcode); put32(out + 4, session); put64(out + 8, id);
  size_t pos = 20;
  uint8_t temp[32];
  put16(temp, result); tlv(out, &pos, 1, temp, 2);
  if (opcode == 1u)
  {
    for (unsigned i = 0; i < 3; ++i) put32(temp + i * 4, ctx->uid[i]);
    tlv(out, &pos, 3, temp, 12);
    put64(temp, ctx->session.boot); tlv(out, &pos, 4, temp, 8);
    put16(temp, 1); put16(temp + 2, 2); put16(temp + 4, 3); tlv(out, &pos, 5, temp, 6);
    put16(temp, 1024); tlv(out, &pos, 6, temp, 2);
    put32(temp, 4000); tlv(out, &pos, 7, temp, 4);
    tlv(out, &pos, 8, temp, 0); /* no recording capability is exposed yet */
  }
  else if (have_snapshot)
  {
#define T8(tag, value) do { temp[0] = (uint8_t)(value); tlv(out, &pos, tag, temp, 1); } while (0)
#define T32(tag, value) do { put32(temp, value); tlv(out, &pos, tag, temp, 4); } while (0)
#define T64(tag, value) do { put64(temp, value); tlv(out, &pos, tag, temp, 8); } while (0)
    T64(9, snapshot.revision); T64(10, snapshot.mono_us);
    T8(16, snapshot.acquisition); T8(17, snapshot.recording); T8(18, snapshot.medium);
    T8(19, snapshot.owner); T8(20, snapshot.maintenance); T32(21, snapshot.generation);
    T32(30, snapshot.rate); T8(25, snapshot.fresh); T8(26, snapshot.classification);
    T32(29, snapshot.quality); T64(31, snapshot.running_version); T64(32, snapshot.saved_version);
    T64(33, snapshot.baseline_version); T64(34, snapshot.calibration_version);
    T32(35, snapshot.fault); T8(42, snapshot.rtc_valid); T32(85, snapshot.media_generation);
    if (snapshot.fresh) T64(22, snapshot.sample_index);
    if (snapshot.ohms_valid)
    {
      uint64_t bits; memcpy(&bits, &snapshot.ohms, sizeof(bits)); T64(23, bits);
    }
    if (snapshot.ratio_valid)
    {
      uint64_t bits; memcpy(&bits, &snapshot.ratio, sizeof(bits)); T64(24, bits);
    }
    if (snapshot.level_valid)
    {
      T8(27, snapshot.level);
      put16(temp, snapshot.interval); tlv(out, &pos, 28, temp, 2);
    }
#undef T8
#undef T32
#undef T64
  }
  else if (have_operation)
  {
    put64(temp, operation.operation_id); tlv(out, &pos, 11, temp, 8);
    temp[0] = operation.result == DRMS_ACCEPTED ? 1u : 2u;
    tlv(out, &pos, 45, temp, 1);
    temp[0] = operation.source == DRMS_SOURCE_BUTTON ? 1u :
              operation.source == DRMS_SOURCE_CDC ? 2u :
              operation.source == DRMS_SOURCE_CONSOLE ? 3u : 0u;
    tlv(out, &pos, 44, temp, 1);
  }
  put16(out + 16, (uint16_t)(pos - 20u));
  put32(out + pos, drms_crc32(out, pos)); pos += 4;
  size_t encoded = drms_cdc_frame_encode(out, pos, ctx->wire, sizeof(ctx->wire));
  if (encoded && ctx->send) ctx->send(ctx->send_context, ctx->wire, encoded);
}

void drms_cdc_v2_init(DRMS_CDCV2 *ctx, DRMS_CDCEntropy entropy, void *entropy_context,
                      const uint32_t uid[3], DRMS_CDCV2Send send, void *send_context)
{
  memset(ctx, 0, sizeof(*ctx));
  if (uid) memcpy(ctx->uid, uid, sizeof(ctx->uid));
  ctx->send = send; ctx->send_context = send_context;
  (void)drms_cdc_session_init(&ctx->session, entropy, entropy_context);
}

void drms_cdc_v2_disconnect(DRMS_CDCV2 *ctx)
{
  drms_cdc_session_disconnect(&ctx->session);
  drms_cdc_frame_init(&ctx->frame);
  ctx->last_request = 0;
}

void drms_cdc_v2_feed(DRMS_CDCV2 *ctx, uint8_t byte, uint32_t now)
{
  drms_cdc_frame_feed(&ctx->frame, byte, now, received, ctx);
}
