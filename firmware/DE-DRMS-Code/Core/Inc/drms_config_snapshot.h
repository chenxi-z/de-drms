#ifndef DRMS_CONFIG_SNAPSHOT_H
#define DRMS_CONFIG_SNAPSHOT_H
#include <stdint.h>
/* Read-only pinned view; do not copy it, release it exactly once. */
typedef struct {
  const uint8_t *data;
  uint32_t length;
  uint64_t running, saved;
  uint32_t slot;
} DRMS_ConfigView;
#define DRMS_CONFIG_SNAPSHOT_MAX 1024u
void drms_config_snapshot_init(void);
/* Hide an unavailable configuration while preserving already pinned views. */
void drms_config_snapshot_invalidate(void);
/* Single writer. Returns 0 if the inactive slot is still pinned; caller retries.
 * Data is copied with interrupts enabled, then published atomically. */
uint32_t drms_config_snapshot_publish(const uint8_t *data, uint32_t length,
                                      uint64_t running, uint64_t saved);
/* Any thread may pin the latest complete view, then release after copying it. */
uint32_t drms_config_snapshot_acquire(DRMS_ConfigView *out);
void drms_config_snapshot_release(DRMS_ConfigView *view);
#endif
