#ifndef DRMS_USB_H
#define DRMS_USB_H

/* USB thread owns init/poll. State notifications may arrive in USB IRQ context. */
unsigned int drms_usb_init(void);
void drms_usb_poll(void);
unsigned int drms_usb_can_io(void);
unsigned int drms_usb_state_change(unsigned long state);
extern volatile unsigned int drms_usb_status;

#endif
