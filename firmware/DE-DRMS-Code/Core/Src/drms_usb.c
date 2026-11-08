#include "drms_usb.h"
#include "app_usbx_device.h"
#include "main.h"

extern PCD_HandleTypeDef hpcd_USB_OTG_FS;
volatile unsigned int drms_usb_status = UX_ERROR;
static volatile unsigned int attached, configured, suspended;
static unsigned int ready;

unsigned int drms_usb_can_io(void)
{
  return ready && attached && configured && !suspended &&
      HAL_GPIO_ReadPin(USB_VBUS_N_GPIO_Port, USB_VBUS_N_Pin) == GPIO_PIN_RESET;
}

static void update_current(void)
{
  /* Serialize a main-thread update against suspend/reset IRQ revocation. */
  uint32_t mask = __get_PRIMASK();
  __disable_irq();
  /* EN2 is grounded: EN1=0 means USB100, EN1=1 means USB500.
     A 100 mA limit is NOT a charger disable or a USB suspend guarantee. */
  HAL_GPIO_WritePin(BQ_EN_GPIO_Port, BQ_EN_Pin,
      drms_usb_can_io() ? GPIO_PIN_SET : GPIO_PIN_RESET);
  __set_PRIMASK(mask);
}

unsigned int drms_usb_init(void)
{
  ready = attached = configured = suspended = 0;
  update_current();
  drms_usb_status = MX_USBX_Device_Stack_Init();
  if (drms_usb_status != UX_SUCCESS)
    return drms_usb_status;

  /* OTG FS has 320 32-bit FIFO words. EP0 control, EP1 CDC bulk,
     EP2 CDC notification: 128 + 64 + 64 + 32 = 288 words. */
  if (HAL_PCDEx_SetRxFiFo(&hpcd_USB_OTG_FS, 128) != HAL_OK ||
      HAL_PCDEx_SetTxFiFo(&hpcd_USB_OTG_FS, 0, 64) != HAL_OK ||
      HAL_PCDEx_SetTxFiFo(&hpcd_USB_OTG_FS, 1, 64) != HAL_OK ||
      HAL_PCDEx_SetTxFiFo(&hpcd_USB_OTG_FS, 2, 32) != HAL_OK)
    return drms_usb_status = UX_ERROR;

  ready = 1;
  return drms_usb_status = UX_SUCCESS;
}

unsigned int drms_usb_state_change(unsigned long state)
{
  if (state == UX_DCD_STM32_DEVICE_SUSPENDED)
    suspended = 1;
  else if (state == UX_DCD_STM32_DEVICE_RESUMED)
    suspended = 0;
  else if (state == UX_DEVICE_CONFIGURED)
    configured = 1;
  else if (state <= UX_DEVICE_RESET || state == UX_DEVICE_REMOVED ||
           state == UX_DCD_STM32_DEVICE_DISCONNECTED)
    configured = suspended = 0;
  else if (state < UX_DEVICE_CONFIGURED)
    configured = 0;
  update_current();
  return UX_SUCCESS;
}

void drms_usb_poll(void)
{
  if (!ready)
    return;
  if (HAL_GPIO_ReadPin(USB_VBUS_N_GPIO_Port, USB_VBUS_N_Pin) == GPIO_PIN_RESET)
  {
    if (!attached)
    {
      configured = suspended = 0;
      if (HAL_PCD_Start(&hpcd_USB_OTG_FS) == HAL_OK)
      {
        attached = 1;
        drms_usb_status = UX_SUCCESS;
      }
      else
        drms_usb_status = UX_ERROR;
    }
  }
  else
  {
    configured = suspended = 0;
    update_current();
    if (attached)
    {
      if (HAL_PCD_Stop(&hpcd_USB_OTG_FS) != HAL_OK)
      {
        drms_usb_status = UX_ERROR;
        return;
      }
      attached = 0;
      /* VBUS sensing is disabled. HAL Stop alone does not tell USBX about
         unplugging: explicitly abort endpoints and deactivate the class. */
      HAL_PCD_DisconnectCallback(&hpcd_USB_OTG_FS);
      drms_usb_status = UX_SUCCESS;
    }
  }
  update_current();
}
