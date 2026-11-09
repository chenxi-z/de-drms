#ifndef DRMS_APPLICATION_H
#define DRMS_APPLICATION_H
#include <stddef.h>
#include <stdint.h>
typedef struct {
  uint64_t revision, mono_us, running_version, saved_version, baseline_version, calibration_version;
  uint64_t sample_index;
  double ohms, ratio;
  uint32_t rate, generation, media_generation, quality, fault;
  uint8_t acquisition, recording, medium, owner, maintenance, fresh, classification, rtc_valid;
  uint8_t ohms_valid, ratio_valid;
  uint8_t level_valid, level;
  uint16_t interval;
} DRMS_ApplicationSnapshot;
/* Copies the last supervisor-published, logically consistent status view. */
uint32_t drms_application_snapshot(DRMS_ApplicationSnapshot *out);
void drms_application_init(void);
void drms_application_poll(void);
size_t drms_application_status(char *out, size_t capacity);
/* Console callback: 1 queued, 0 unknown, -1 bad argument, -2 busy. */
int drms_console_dispatch(const char *line);
#endif
