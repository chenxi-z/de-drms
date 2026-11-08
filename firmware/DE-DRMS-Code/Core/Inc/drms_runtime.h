#ifndef DRMS_RUNTIME_H
#define DRMS_RUNTIME_H
void drms_runtime_run(void);
/* Single supervisor owner; split out for production-code host regression. */
void drms_runtime_init(void);
void drms_runtime_poll(void);
extern volatile unsigned int drms_uart_rx_dropped, drms_uart_tx_dropped;
#endif
