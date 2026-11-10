#ifndef DRMS_FILE_SERVICE_H
#define DRMS_FILE_SERVICE_H
#include "drms_architecture_contract.h"
/* The control owner must hold TF_ACCESS from submission until quiescent; for an
 * open handle the same lease remains held across subsequent reads and close.
 * One bounded mailbox, one client session. FileX is touched only by poll. */
typedef enum { DRMS_FILE_LIST=1, DRMS_FILE_OPEN=2, DRMS_FILE_READ=3, DRMS_FILE_CLOSE=4 } DRMS_FileKind;
typedef struct {
  uint32_t kind, session, generation, file_id, cursor;
  uint64_t offset;
  uint16_t count;
} DRMS_FileRequest;
typedef struct {
  uint64_t ticket;
  DRMS_Result result;
  uint32_t file_id, next_cursor;
  uint64_t size, offset;
  uint16_t length;
  uint8_t eof;
  uint8_t data[768];
} DRMS_FileReply;
void drms_file_service_init(void);
DRMS_Result drms_file_service_submit(const DRMS_FileRequest *request, uint64_t *ticket);
/* OK=reply copied, ACCEPTED=still pending, STALE=cancelled/unknown. */
DRMS_Result drms_file_service_take(uint64_t ticket, DRMS_FileReply *out);
/* Any thread: revoke session; actual close happens in storage poll. */
void drms_file_service_disconnect(uint32_t session);
/* Shutdown path: revoke the one current request/handle, if any. */
void drms_file_service_cancel_all(void);
/* Storage owner only; at most one FileX action or one directory probe per call. */
void drms_file_service_poll(void);
uint32_t drms_file_service_quiescent(void);
uint32_t drms_file_service_quarantined(void);
/* Terminal close, read failure or cancellation result; reset by next open. */
DRMS_Result drms_file_service_last_result(void);
/* Storage owner only, after FileX abort and backend invalidation are complete. */
DRMS_Result drms_file_service_after_media_abort(void);
#endif
