#ifndef DRMS_CDC_FRAME_H
#define DRMS_CDC_FRAME_H
#include <stddef.h>
#include <stdint.h>

#define DRMS_CDC_RAW_MAX 1048u
#define DRMS_CDC_WIRE_MAX 1054u
#define DRMS_CDC_FRAME_TIMEOUT_MS 1000u

typedef void (*DRMS_CDCFrameHandler)(void *user, const uint8_t *frame, size_t length);
typedef struct {
  uint8_t encoded[DRMS_CDC_WIRE_MAX - 1u];
  uint8_t decoded[DRMS_CDC_RAW_MAX];
  size_t length;
  uint32_t started_ms;
  uint32_t malformed, overflow, timeout, crc_error;
  uint8_t discarding;
} DRMS_CDCFrame;

size_t drms_cdc_frame_size(void);
void drms_cdc_frame_init(DRMS_CDCFrame *ctx);
void drms_cdc_frame_tick(DRMS_CDCFrame *ctx, uint32_t now_ms);
void drms_cdc_frame_feed(DRMS_CDCFrame *ctx, uint8_t byte, uint32_t now_ms,
                         DRMS_CDCFrameHandler handler, void *user);
/* The raw input includes the already-computed CRC. The result includes delimiter. */
size_t drms_cdc_frame_encode(const uint8_t *raw, size_t length, uint8_t *out, size_t capacity);

typedef struct {
  uint16_t id, min_len, max_len;
  uint8_t kind; /* 0 bytes, 1 bool, 2 little-endian finite IEEE754 binary64 */
  uint8_t required;
} DRMS_CDCFieldRule;
typedef struct {
  const uint8_t *value; /* valid only while the input payload remains alive */
  uint16_t length;
} DRMS_CDCFieldView;
/* Validates one message's flat TLV payload. Returns zero only on success.
 * views is indexed by rule; an absent optional field has a null value. */
int drms_cdc_fields_validate(const uint8_t *payload, size_t length,
    const DRMS_CDCFieldRule *rules, size_t rule_count, DRMS_CDCFieldView *views);

typedef struct {
  uint64_t boot;
  uint32_t next_session, session, healthy;
} DRMS_CDCSession;
/* Entropy provider returns success only after its hardware health checks pass. */
typedef int (*DRMS_CDCEntropy)(void *context, uint64_t *random_value);
/* Call exactly once per boot; reconnect uses disconnect, not reinitialization. */
int drms_cdc_session_init(DRMS_CDCSession *state, DRMS_CDCEntropy entropy, void *context);
int drms_cdc_session_hello(DRMS_CDCSession *state, uint32_t request_session,
                           uint64_t request_id, uint32_t *session);
void drms_cdc_session_disconnect(DRMS_CDCSession *state);
#endif
