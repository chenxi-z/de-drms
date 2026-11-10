#ifndef DRMS_APPLICATION_H
#define DRMS_APPLICATION_H
#include <stddef.h>
#include <stdint.h>
#include "drms_architecture_contract.h"
typedef struct {
  uint64_t revision, mono_us, running_version, saved_version, baseline_version, calibration_version;
  uint64_t sample_index;
  double ohms, ratio;
  uint32_t rate, generation, media_generation, quality, fault;
  uint8_t acquisition, recording, medium, owner, maintenance, fresh, classification, rtc_valid;
  uint8_t ohms_valid, ratio_valid;
  uint8_t level_valid, level;
  uint16_t interval;
  uint64_t record_id;
  uint32_t record_result;
  uint8_t record_phase;
} DRMS_ApplicationSnapshot;
/* Copies the last supervisor-published, logically consistent status view. */
uint32_t drms_application_snapshot(DRMS_ApplicationSnapshot *out);
typedef struct {
  uint64_t record, capture_lost, log_dropped;
  uint32_t result;
  uint8_t phase, clean_end, unknown_loss;
} DRMS_ApplicationRecord;
/* Current/latest plus four older completed records; id=0 selects latest. */
DRMS_Result drms_application_record_snapshot(uint64_t id, DRMS_ApplicationRecord *out);
typedef struct {
  uint64_t operation, size;
  uint32_t session, generation, phase, result; /* 0 opening, 1 active, 2 closed */
} DRMS_ApplicationFile;
uint32_t drms_application_file_snapshot(DRMS_ApplicationFile *out);
typedef struct {
  uint64_t operation, size;
  uint32_t session, generation, cursor, file_id, next_cursor, phase, result;
} DRMS_ApplicationFileList;
uint32_t drms_application_file_list_snapshot(DRMS_ApplicationFileList *out);
/* Revoke a disconnected CDC session, including opens not yet dispatched. */
void drms_application_file_disconnect(uint32_t session);
DRMS_Result drms_application_file_close(uint32_t session, uint64_t operation);
void drms_application_init(void);
void drms_application_poll(void);
size_t drms_application_status(char *out, size_t capacity);
/* Console callback: 1 queued, 0 unknown, -1 bad argument, -2 busy. */
int drms_console_dispatch(const char *line);
#endif
