#ifndef DRMS_BOOT_IDENTITY_H
#define DRMS_BOOT_IDENTITY_H
#include <stdint.h>
/* Single initialization owner publishes the healthy random boot identifier.
 * Zero means unavailable; readers in any thread receive a consistent value. */
void drms_boot_identity_publish(uint64_t value);
uint64_t drms_boot_identity_get(void);
#endif
