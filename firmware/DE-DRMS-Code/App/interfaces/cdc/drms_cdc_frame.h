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
#endif
