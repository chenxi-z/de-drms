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
   * client can detect gaps without relying on request ids.
   *
   * 订阅状态由两个线程共同触碰：接收线程在 SUBSCRIBE/UNSUBSCRIBE/断线时改它，
   * 发送线程在推送时按它判断到期。curve_epoch 是给这种跨线程使用准备的序号——
   * 推送方在编码前记下 epoch，提交结果时如果 epoch 变了，说明订阅在这一瞬间
   * 被撤销或重建，那一帧就作废（清掉订阅后不该还漏出一帧旧数据）。 */
  uint32_t curve_period_ms, curve_subscribed;
  uint64_t curve_sequence, curve_lost;
  uint32_t curve_last_ms;
  uint32_t curve_epoch;
  /* 推送专用的编码缓冲。接收线程的回帧用 raw/wire，两者不能共用：
   * 推送在发送线程里编码，若借用 ctx->wire 会与接收线程的回帧互相踩。 */
  uint8_t curve_wire[DRMS_CDC_WIRE_MAX];
  uint32_t feed_now; /* timestamp of the request being dispatched */
} DRMS_CDCV2;
void drms_cdc_v2_init(DRMS_CDCV2 *ctx, DRMS_CDCEntropy entropy, void *entropy_context,
                      const uint32_t uid[3], DRMS_CDCV2Send send, DRMS_CDCV2CanSend can_send,
                      void *send_context);
void drms_cdc_v2_disconnect(DRMS_CDCV2 *ctx);
void drms_cdc_v2_feed(DRMS_CDCV2 *ctx, uint8_t byte, uint32_t now);
/* Push a CURVE sample when the subscription period has elapsed.
 *
 * 由 CDC 发送线程调用（每 10 ms 一次）。它之所以不能放在接收线程里：
 * 接收线程阻塞在 UX_WAIT_FOREVER 的 read 上，只有主机发来数据才会返回一次；
 * 订阅成功后主机通常不再说话，那样推送就永远轮不到。
 * 本函数从不阻塞，队列满时丢弃并累加 lost。 */
void drms_cdc_v2_publish(DRMS_CDCV2 *ctx, uint32_t now);
/* Stateless: safe for the single TX owner to encode into its own buffer. */
size_t drms_cdc_v2_encode_measurement(uint32_t session, uint64_t sequence, uint64_t lost,
    const DRMS_ApplicationSnapshot *snapshot, uint8_t *wire, size_t capacity);
#endif
