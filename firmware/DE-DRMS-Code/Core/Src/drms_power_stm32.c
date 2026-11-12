/*****************************************************************************
 * 文件：drms_power_stm32.c
 * 职责：电源相关的 MCU 侧驱动——内部 ADC 读电池、软关机与唤醒。
 *
 * 与 drms_power.c 的分工：
 *   那个文件是业务判断（什么时候该关机），
 *   这个文件是具体动作（怎么读电压、怎么进待机）。
 *
 * 待机入口可能被调试器阻止（调试时会保持内核运行），
 * 所以返回码要能区分"进入成功"和"被拒绝"，不能一律当作成功。
 *****************************************************************************/

#include "drms_power.h"
#include "drms_acquisition.h"
#include "drms_logging.h"
#include "main.h"

int drms_power_backend_enter(void)
{
  if (drms_acq_running || drms_log_state || !drms_storage_shutdown_ready)
    return 0;
  uint32_t mask = __get_PRIMASK();
  __disable_irq();
  if (HAL_GPIO_ReadPin(USB_VBUS_N_GPIO_Port, USB_VBUS_N_Pin) == GPIO_PIN_RESET ||
      HAL_GPIO_ReadPin(PWR_BTN_GPIO_Port, PWR_BTN_Pin) == GPIO_PIN_RESET ||
      HAL_GPIO_ReadPin(MEAS_BTN_GPIO_Port, MEAS_BTN_Pin) == GPIO_PIN_RESET)
  {
    __set_PRIMASK(mask);
    return 1;
  }
  /* Retain safe pad bias even with GPIO registers lost in Standby. */
  (void)HAL_PWREx_EnableGPIOPullUp(PWR_GPIO_A, PWR_GPIO_BIT_0 | PWR_GPIO_BIT_4);
  (void)HAL_PWREx_EnableGPIOPullDown(PWR_GPIO_A, PWR_GPIO_BIT_2);
  (void)HAL_PWREx_EnableGPIOPullUp(PWR_GPIO_C, PWR_GPIO_BIT_4 | PWR_GPIO_BIT_5 | PWR_GPIO_BIT_13);
  (void)HAL_PWREx_EnableGPIOPullDown(PWR_GPIO_C, PWR_GPIO_BIT_3);
  HAL_PWREx_EnablePullUpPullDownConfig();
  HAL_PWR_EnableWakeUpPin(PWR_WAKEUP_PIN1_LOW_0); /* PA0 measurement button */
  HAL_PWR_EnableWakeUpPin(PWR_WAKEUP_PIN5_LOW_0); /* PC5 power button */
  HAL_PWR_EnableWakeUpPin(PWR_WAKEUP_PIN2_LOW_1); /* PC13 raw USB presence */
  __HAL_PWR_CLEAR_FLAG(PWR_WAKEUP_FLAG1);
  __HAL_PWR_CLEAR_FLAG(PWR_WAKEUP_FLAG2);
  __HAL_PWR_CLEAR_FLAG(PWR_WAKEUP_FLAG5);
  /* Do not clear an already-active USB/button wake edge and then sleep. */
  if (HAL_GPIO_ReadPin(USB_VBUS_N_GPIO_Port, USB_VBUS_N_Pin) == GPIO_PIN_RESET ||
      HAL_GPIO_ReadPin(PWR_BTN_GPIO_Port, PWR_BTN_Pin) == GPIO_PIN_RESET ||
      HAL_GPIO_ReadPin(MEAS_BTN_GPIO_Port, MEAS_BTN_Pin) == GPIO_PIN_RESET)
  {
    __set_PRIMASK(mask);
    return 1;
  }
  HAL_GPIO_WritePin(LED_GREEN_GPIO_Port, LED_GREEN_Pin, GPIO_PIN_SET);
  HAL_GPIO_WritePin(LED_YELLOW_GPIO_Port, LED_YELLOW_Pin, GPIO_PIN_SET);
  HAL_GPIO_WritePin(LED_ORANGE_GPIO_Port, LED_ORANGE_Pin, GPIO_PIN_SET);
  HAL_GPIO_WritePin(LED_RED_GPIO_Port, LED_RED_Pin, GPIO_PIN_SET);
  HAL_GPIO_WritePin(PWR_LED_GPIO_Port, PWR_LED_Pin, GPIO_PIN_SET);
  enum { IRQ_BANKS = sizeof(NVIC->ISER) / sizeof(NVIC->ISER[0]) };
  uint32_t enabled[IRQ_BANKS], pending[IRQ_BANKS];
  for (unsigned int i = 0; i < IRQ_BANKS; ++i)
  {
    enabled[i] = NVIC->ISER[i];
    pending[i] = NVIC->ISPR[i];
    NVIC->ICER[i] = 0xffffffffU;
    NVIC->ICPR[i] = 0xffffffffU;
  }
  uint32_t systick_control = SysTick->CTRL;
  HAL_SuspendTick();
  SysTick->CTRL = 0;
  SCB->ICSR = SCB_ICSR_PENDSTCLR_Msk | SCB_ICSR_PENDSVCLR_Msk;
  __DSB();
  HAL_PWR_EnterSTANDBYMode();
  /* Debug hardware may prevent deep entry. Restore a usable scheduler instead
     of leaving a live MCU with all interrupts/ticks disabled. */
  SCB->SCR &= ~SCB_SCR_SLEEPDEEP_Msk;
  SysTick->CTRL = systick_control;
  HAL_ResumeTick();
  for (unsigned int i = 0; i < IRQ_BANKS; ++i)
  {
    NVIC->ISER[i] = enabled[i];
    NVIC->ISPR[i] = pending[i];
  }
  __set_PRIMASK(mask);
  return 0;
}
