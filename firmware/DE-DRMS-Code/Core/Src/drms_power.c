#include "drms_power.h"
#include "drms_application.h"
#include "drms_time.h"
#include "main.h"

volatile uint32_t drms_shutdown_requested, drms_storage_shutdown_ready;
volatile uint32_t drms_power_low_battery, drms_power_status;
static uint32_t holding, ignore_until_release, held_since, released_since, last_battery, low_readings;

void drms_power_init(void)
{
  drms_shutdown_requested = drms_storage_shutdown_ready = 0;
  drms_power_status = drms_power_low_battery = low_readings = holding = 0;
  held_since = released_since = last_battery = HAL_GetTick();
  ignore_until_release = HAL_GPIO_ReadPin(PWR_BTN_GPIO_Port, PWR_BTN_Pin) == GPIO_PIN_RESET;
}

static void request_shutdown(void)
{
  if (drms_shutdown_requested)
    return;
  drms_storage_shutdown_ready = 0;
  __atomic_store_n(&drms_shutdown_requested, 1U, __ATOMIC_RELEASE);
  drms_power_status = 1;
  (void)drms_console_dispatch("STOP");
}

void drms_power_poll(void)
{
  uint32_t now = HAL_GetTick();
  unsigned int usb = HAL_GPIO_ReadPin(USB_VBUS_N_GPIO_Port, USB_VBUS_N_Pin) == GPIO_PIN_RESET;
  unsigned int external = HAL_GPIO_ReadPin(BQ_PG_GPIO_Port, BQ_PG_Pin) == GPIO_PIN_RESET;
  unsigned int pressed = HAL_GPIO_ReadPin(PWR_BTN_GPIO_Port, PWR_BTN_Pin) == GPIO_PIN_RESET;
  if (usb || external || !drms_battery_valid)
    low_readings = drms_power_low_battery = 0;
  if ((uint32_t)(now - last_battery) >= 1000U)
  {
    last_battery = now;
    if (!usb && !external && drms_battery_valid)
    {
      drms_power_low_battery = drms_battery_mv <= 3650;
      if (drms_battery_mv <= 3500)
      {
        if (low_readings < 5)
          ++low_readings;
        if (low_readings >= 5)
          request_shutdown();
      }
      else
        low_readings = 0;
    }
  }
  if (!pressed)
  {
    if (holding)
      released_since = now;
    holding = ignore_until_release = 0;
  }
  else
  {
    released_since = now;
    if (!holding)
    {
      holding = 1;
      held_since = now;
    }
    if (!ignore_until_release && !usb && (uint32_t)(now - held_since) >= 2000U)
      request_shutdown();
  }
  if (usb)
  {
    __atomic_store_n(&drms_shutdown_requested, 0U, __ATOMIC_RELEASE);
    drms_power_status = 0;
  }
  else if (drms_shutdown_requested && drms_storage_shutdown_ready && !pressed &&
           (uint32_t)(now - released_since) >= 50U)
  {
    int canceled = drms_power_backend_enter();
    /* A successful Standby wakes through reset and never reaches this point. */
    __atomic_store_n(&drms_shutdown_requested, 0U, __ATOMIC_RELEASE);
    drms_power_status = canceled == 1 ? 0 : 2;
  }
}
