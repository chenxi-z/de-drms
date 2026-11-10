#ifndef DRMS_CDC_V2_H
#define DRMS_CDC_V2_H
#include "drms_cdc_frame.h"
typedef void (*DRMS_CDCV2Send)(void *context, const uint8_t *data, size_t size, uint32_t priority);
typedef int (*DRMS_CDCV2CanSend)(void *context, uint32_t priority);
typedef struct {
  uint64_t request_id, operation_id, age;
  uint16_t length;
  uint8_t bytes[DRMS_CDC_RAW_MAX];
} DRMS_CDCMutation;
typedef struct {
  DRMS_CDCFrame frame;
  DRMS_CDCSession session;
  uint32_t uid[3];
  uint64_t last_request;
  DRMS_CDCV2Send send;
  DRMS_CDCV2CanSend can_send;
  void *send_context;
  uint8_t raw[DRMS_CDC_RAW_MAX], wire[DRMS_CDC_WIRE_MAX];
  DRMS_CDCMutation mutations[4];
  DRMS_CDCMutation stop_mutation;
  uint64_t mutation_age;
} DRMS_CDCV2;
void drms_cdc_v2_init(DRMS_CDCV2 *ctx, DRMS_CDCEntropy entropy, void *entropy_context,
                      const uint32_t uid[3], DRMS_CDCV2Send send, DRMS_CDCV2CanSend can_send,
                      void *send_context);
void drms_cdc_v2_disconnect(DRMS_CDCV2 *ctx);
void drms_cdc_v2_feed(DRMS_CDCV2 *ctx, uint8_t byte, uint32_t now);
#endif
