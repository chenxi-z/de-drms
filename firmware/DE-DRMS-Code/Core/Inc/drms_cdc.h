#ifndef DRMS_CDC_H
#define DRMS_CDC_H
unsigned int drms_cdc_start(void);
/* Only the dedicated CDC worker may poll; reset/unplug abort blocked I/O. */
void drms_cdc_poll(void);
void drms_cdc_activate(void *instance);
void drms_cdc_deactivate(void);
void drms_cdc_parameter_change(void *instance);
#endif
