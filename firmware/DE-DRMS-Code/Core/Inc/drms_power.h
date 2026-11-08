#ifndef DRMS_POWER_H
#define DRMS_POWER_H
#include <stdint.h>
void drms_power_init(void);
void drms_power_poll(void);
/* Target backend enters Standby; only returns on cancellation/debug failure. */
int drms_power_backend_enter(void);
extern volatile uint32_t drms_shutdown_requested, drms_storage_shutdown_ready;
extern volatile uint32_t drms_power_low_battery, drms_power_status;
#endif
