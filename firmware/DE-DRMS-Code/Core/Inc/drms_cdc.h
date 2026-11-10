#ifndef DRMS_CDC_H
#define DRMS_CDC_H
unsigned int drms_cdc_start(void);
/* Only the dedicated CDC worker may poll; reset/unplug abort blocked I/O. */
void drms_cdc_poll(void);
/* Only the dedicated sender may poll; one packet stays owned until write ends. */
void drms_cdc_tx_poll(void);
extern volatile unsigned int drms_cdc_tx_dropped, drms_cdc_tx_errors;
void drms_cdc_activate(void *instance);
void drms_cdc_deactivate(void);
void drms_cdc_parameter_change(void *instance);
#endif
