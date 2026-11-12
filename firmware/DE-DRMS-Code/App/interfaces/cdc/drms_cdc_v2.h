#ifndef DRMS_CDC_V2_H
#define DRMS_CDC_V2_H
#include "drms_cdc_frame.h"
#include "drms_file_service.h"
#include "drms_application.h"
typedef void (*DRMS_CDCV2Send)(void *context, const uint8_t *data, size_t size, uint32_t priority);
typedef int (*DRMS_CDCV2CanSend)(void *context, uint32_t priority);
typedef struct {
  uint64_t request_id, operation_id, record_id, age;
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
  uint64_t file_read_ticket, file_read_operation, file_read_offset;
  uint64_t file_list_operation;
  uint32_t file_list_cursor, file_list_generation;
  uint16_t file_read_count;
  DRMS_FileReply file_read_reply;
  /* Curve subscription (SUBSCRIBE opcode 64). Session-scoped: cleared on
   * disconnect, and the event carries its own sequence starting at 1 so the
   * client can detect gaps without relying on request ids. */
  uint32_t curve_period_ms, curve_subscribed;
  uint64_t curve_sequence, curve_lost;
  uint32_t curve_last_ms;
  uint32_t feed_now; /* timestamp of the request being dispatched */
} DRMS_CDCV2;
void drms_cdc_v2_init(DRMS_CDCV2 *ctx, DRMS_CDCEntropy entropy, void *entropy_context,
                      const uint32_t uid[3], DRMS_CDCV2Send send, DRMS_CDCV2CanSend can_send,
                      void *send_context);
void drms_cdc_v2_disconnect(DRMS_CDCV2 *ctx);
void drms_cdc_v2_feed(DRMS_CDCV2 *ctx, uint8_t byte, uint32_t now);
/* Push a CURVE sample when the subscription period has elapsed. Call from the
 * CDC receive thread; it never blocks and drops with a count when full. */
void drms_cdc_v2_publish(DRMS_CDCV2 *ctx, uint32_t now);
/* Stateless: safe for the single TX owner to encode into its own buffer. */
size_t drms_cdc_v2_encode_measurement(uint32_t session, uint64_t sequence, uint64_t lost,
    const DRMS_ApplicationSnapshot *snapshot, uint8_t *wire, size_t capacity);
#endif
