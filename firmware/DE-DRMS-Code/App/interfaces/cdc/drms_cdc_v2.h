#ifndef DRMS_CDC_V2_H
#define DRMS_CDC_V2_H
#include "drms_cdc_frame.h"
typedef void (*DRMS_CDCV2Send)(void *context, const uint8_t *data, size_t size);
typedef struct {
  DRMS_CDCFrame frame;
  DRMS_CDCSession session;
  uint32_t uid[3];
  uint64_t last_request;
  DRMS_CDCV2Send send;
  void *send_context;
  uint8_t raw[256], wire[260];
} DRMS_CDCV2;
void drms_cdc_v2_init(DRMS_CDCV2 *ctx, DRMS_CDCEntropy entropy, void *entropy_context,
                      const uint32_t uid[3], DRMS_CDCV2Send send, void *send_context);
void drms_cdc_v2_disconnect(DRMS_CDCV2 *ctx);
void drms_cdc_v2_feed(DRMS_CDCV2 *ctx, uint8_t byte, uint32_t now);
#endif
