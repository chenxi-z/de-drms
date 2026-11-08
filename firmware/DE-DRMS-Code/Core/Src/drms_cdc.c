#include "drms_cdc.h"
#include "drms_console.h"
#include "drms_usb.h"
#include "app_usbx_device.h"
#include <string.h>

static UX_SLAVE_CLASS_CDC_ACM *volatile instance;
static volatile ULONG generation;
static TX_THREAD thread;
static ULONG stack[768];

void drms_cdc_activate(void *cdc)
{
  /* This dedicated worker may block. The STM32 DCD leaves endpoints pending
     on software timeout; rearming after it would race late IRQ completion.
     Reset/unplug abort pending requests and wake this worker. */
  ULONG timeout = UX_WAIT_FOREVER;
  (void)ux_device_class_cdc_acm_ioctl(cdc,
      UX_SLAVE_CLASS_CDC_ACM_IOCTL_SET_READ_TIMEOUT, (VOID *)timeout);
  (void)ux_device_class_cdc_acm_ioctl(cdc,
      UX_SLAVE_CLASS_CDC_ACM_IOCTL_SET_WRITE_TIMEOUT, (VOID *)timeout);
  ++generation;
  instance = cdc;
}

void drms_cdc_deactivate(void)
{
  instance = UX_NULL;
  ++generation;
  (void)drms_usb_state_change(UX_DEVICE_RESET);
}

void drms_cdc_parameter_change(void *cdc)
{
  if (!cdc || instance != cdc)
    return;
  ++generation;
  /* With infinite I/O waits, USBX's abort wakes the actual waiter and its
     semaphore is consumed by that request. No timeout/rearm race is introduced. */
  (void)ux_device_class_cdc_acm_ioctl(cdc, UX_SLAVE_CLASS_CDC_ACM_IOCTL_ABORT_PIPE,
                                    (VOID *)UX_SLAVE_CLASS_CDC_ACM_ENDPOINT_RCV);
  (void)ux_device_class_cdc_acm_ioctl(cdc, UX_SLAVE_CLASS_CDC_ACM_IOCTL_ABORT_PIPE,
                                    (VOID *)UX_SLAVE_CLASS_CDC_ACM_ENDPOINT_XMIT);
}

void drms_cdc_poll(void)
{
  static DRMS_Console console;
  static UCHAR input_bytes[64];
  static char response[1024];
  static ULONG previous;
  UX_SLAVE_CLASS_CDC_ACM *cdc = instance;
  ULONG session = generation, actual = 0;
  if (previous != session)
  {
    memset(&console, 0, sizeof(console));
    previous = session;
  }
  if (!cdc || !cdc->ux_slave_class_cdc_acm_data_dtr_state || !drms_usb_can_io())
  {
    memset(&console, 0, sizeof(console));
    return;
  }
  UINT status = ux_device_class_cdc_acm_read(cdc, input_bytes, sizeof(input_bytes), &actual);
  if (session != generation || cdc != instance || !cdc->ux_slave_class_cdc_acm_data_dtr_state)
    return;
  if (status != UX_SUCCESS)
  {
    console.discard = 1;
    return;
  }
  /* A short packet may contain only part of a line. Preserve it until LF. */
  for (ULONG i = 0; i < actual; ++i)
  {
    size_t length = drms_console_feed(&console, input_bytes[i], response, sizeof(response));
    if (length && session == generation && drms_usb_can_io())
    {
      ULONG written;
      (void)ux_device_class_cdc_acm_write(cdc, (UCHAR *)response, (ULONG)length, &written);
    }
  }
}

static void entry(ULONG input)
{
  TX_PARAMETER_NOT_USED(input);
  for (;;)
  {
    drms_cdc_poll();
    tx_thread_sleep(1);
  }
}

unsigned int drms_cdc_start(void)
{
  return tx_thread_create(&thread, "CDC diagnostics", entry, 0, stack, sizeof(stack),
                          11, 11, TX_NO_TIME_SLICE, TX_AUTO_START);
}
