#include "drms_cdc.h"
#include "drms_console.h"
#include "drms_boot_identity.h"
#include "drms_usb.h"
#include "app_usbx_device.h"
#include "main.h"
#include "../../App/interfaces/cdc/drms_cdc_v2.h"
#include "../../App/platform/stm32/drms_entropy.h"
#include <string.h>

static UX_SLAVE_CLASS_CDC_ACM *volatile instance;
static volatile ULONG generation;
static TX_THREAD thread;
static ULONG stack[768];
static TX_THREAD tx_thread;
static ULONG tx_stack[512];
#define CDC_TX_SLOTS 4u
#define CDC_TX_MAX 1054u
typedef struct { ULONG generation; ULONG length; UCHAR bytes[CDC_TX_MAX]; } CDC_TxSlot;
static CDC_TxSlot tx_slots[CDC_TX_SLOTS];
static uint32_t tx_head, tx_tail, tx_count;
static CDC_TxSlot priority_slot;
static uint32_t priority_count;
volatile unsigned int drms_cdc_tx_dropped, drms_cdc_tx_errors;
static DRMS_CDCV2 v2;
static ULONG processing_generation;

static uint32_t tx_has_room(void)
{
  return __atomic_load_n(&tx_count, __ATOMIC_ACQUIRE) < CDC_TX_SLOTS;
}

/* Single producer (RX worker): copy outside the IRQ critical section. The
 * sender cannot touch the slot until count publishes it; in-flight slots stay
 * counted until USBX returns, so neither copy can overwrite an active send. */
static int tx_enqueue(const uint8_t *data, size_t size, ULONG session, uint32_t priority)
{
  if (!data || !size || size > CDC_TX_MAX ||
      (priority ? __atomic_load_n(&priority_count, __ATOMIC_ACQUIRE) : !tx_has_room()))
    return 0;
  CDC_TxSlot *slot = priority ? &priority_slot : &tx_slots[tx_head];
  memcpy(slot->bytes, data, size);
  slot->length = (ULONG)size;
  slot->generation = session;
  uint32_t mask = __get_PRIMASK();
  __disable_irq();
  if (session != generation || !instance || (priority ? priority_count : tx_count >= CDC_TX_SLOTS))
  {
    __set_PRIMASK(mask);
    return 0;
  }
  if (priority)
    __atomic_store_n(&priority_count, 1u, __ATOMIC_RELEASE);
  else
  {
    tx_head = (tx_head + 1u) % CDC_TX_SLOTS;
    __atomic_add_fetch(&tx_count, 1u, __ATOMIC_RELEASE);
  }
  __set_PRIMASK(mask);
  return 1;
}

void drms_cdc_tx_poll(void)
{
  uint32_t priority = __atomic_load_n(&priority_count, __ATOMIC_ACQUIRE);
  if (!priority && !__atomic_load_n(&tx_count, __ATOMIC_ACQUIRE))
    return;
  CDC_TxSlot *slot = priority ? &priority_slot : &tx_slots[tx_tail];
  UX_SLAVE_CLASS_CDC_ACM *cdc = instance;
  ULONG session = generation;
  if (slot->generation == session && cdc && cdc->ux_slave_class_cdc_acm_data_dtr_state)
  {
    if (!drms_usb_can_io())
      return; /* suspension retains a queued reply */
    ULONG written = 0;
    UINT status = ux_device_class_cdc_acm_write(cdc, slot->bytes, slot->length, &written);
    if (status != UX_SUCCESS || written != slot->length)
      __atomic_add_fetch(&drms_cdc_tx_errors, 1u, __ATOMIC_RELAXED);
  }
  uint32_t mask = __get_PRIMASK();
  __disable_irq();
  if (priority)
    __atomic_store_n(&priority_count, 0u, __ATOMIC_RELEASE);
  else
  {
    tx_tail = (tx_tail + 1u) % CDC_TX_SLOTS;
    __atomic_sub_fetch(&tx_count, 1u, __ATOMIC_RELEASE);
  }
  __set_PRIMASK(mask);
}

static int can_send_v2(void *context, uint32_t priority)
{
  (void)context;
  int room = priority ? !__atomic_load_n(&priority_count, __ATOMIC_ACQUIRE) : tx_has_room();
  if (!room) __atomic_add_fetch(&drms_cdc_tx_dropped, 1u, __ATOMIC_RELAXED);
  return room;
}

static void send_v2(void *context, const uint8_t *data, size_t size, uint32_t priority)
{
  (void)context;
  UX_SLAVE_CLASS_CDC_ACM *cdc = instance;
  if (cdc && generation == processing_generation && cdc->ux_slave_class_cdc_acm_data_dtr_state && drms_usb_can_io())
  {
    (void)tx_enqueue(data, size, processing_generation, priority);
  }
}

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
  static unsigned int mode; /* 0 boundary, 1 ASCII, 2 COBS, 3 discard COBS */
  UX_SLAVE_CLASS_CDC_ACM *cdc = instance;
  ULONG session = generation, actual = 0;
  if (previous != session)
  {
    memset(&console, 0, sizeof(console));
    drms_cdc_v2_disconnect(&v2);
    mode = 0;
    previous = session;
  }
  if (!cdc || !cdc->ux_slave_class_cdc_acm_data_dtr_state)
  {
    memset(&console, 0, sizeof(console));
    drms_cdc_v2_disconnect(&v2);
    mode = 0;
    return;
  }
  if (!drms_usb_can_io())
    return; /* USB suspend is not a disconnect; keep the session. */
  UINT status = ux_device_class_cdc_acm_read(cdc, input_bytes, sizeof(input_bytes), &actual);
  if (session != generation || cdc != instance || !cdc->ux_slave_class_cdc_acm_data_dtr_state)
    return;
  if (status != UX_SUCCESS)
  {
    if (mode == 2u || mode == 3u)
    {
      drms_cdc_frame_init(&v2.frame);
      mode = 3u;
    }
    else
      console.discard = 1;
    return;
  }
  /* A short packet may contain only part of a line. Preserve it until LF. */
  for (ULONG i = 0; i < actual; ++i)
  {
    UCHAR byte = input_bytes[i];
    if (mode == 3u)
    {
      if (!byte) mode = 0;
      continue;
    }
    if (!mode)
    {
      if (!byte) continue;
      mode = (byte >= 3u && byte <= 5u) ? 2u : 1u;
    }
    if (mode == 2u)
    {
      processing_generation = session;
      drms_cdc_v2_feed(&v2, byte, HAL_GetTick());
      if (!byte) mode = 0;
      continue;
    }
    if (byte == '\n' && !tx_has_room())
    {
      memset(&console, 0, sizeof(console));
      __atomic_add_fetch(&drms_cdc_tx_dropped, 1u, __ATOMIC_RELAXED);
      mode = 0;
      continue;
    }
    size_t length = drms_console_feed(&console, byte, response, sizeof(response));
    if (byte == '\n') mode = 0;
    if (length && session == generation && drms_usb_can_io())
    {
      (void)tx_enqueue((const uint8_t *)response, length, session, 0);
    }
  }
}

static void tx_entry(ULONG input)
{
  TX_PARAMETER_NOT_USED(input);
  for (;;)
  {
    drms_cdc_tx_poll();
    tx_thread_sleep(1);
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
  uint32_t uid[3] = {HAL_GetUIDw0(), HAL_GetUIDw1(), HAL_GetUIDw2()};
  tx_head = tx_tail = tx_count = priority_count = 0;
  drms_cdc_tx_dropped = drms_cdc_tx_errors = 0;
  drms_cdc_v2_init(&v2, drms_entropy_boot_id, NULL, uid, send_v2, can_send_v2, NULL);
  drms_boot_identity_publish(v2.session.healthy ? v2.session.boot : 0);
  UINT status = tx_thread_create(&tx_thread, "CDC sender", tx_entry, 0, tx_stack, sizeof(tx_stack),
                                 12, 12, TX_NO_TIME_SLICE, TX_AUTO_START);
  if (status != TX_SUCCESS)
    return status;
  status = tx_thread_create(&thread, "CDC receiver", entry, 0, stack, sizeof(stack),
                            11, 11, TX_NO_TIME_SLICE, TX_AUTO_START);
  if (status != TX_SUCCESS)
  {
    (void)tx_thread_terminate(&tx_thread);
    (void)tx_thread_delete(&tx_thread);
  }
  return status;
}
