#include "drms_runtime.h"
#include "drms_application.h"
#include "drms_console.h"
#include "drms_storage.h"
#include "drms_usb.h"
#include "main.h"
#include "usart.h"
#include "tx_api.h"
#include <string.h>

static uint8_t rx_byte;
static uint8_t rx_ring[128];
static volatile unsigned int rx_head, rx_tail, rx_desynced, rx_ready, tx_busy;
static DRMS_Console console;
static char tx_buffer[1024];
volatile unsigned int drms_uart_rx_dropped, drms_uart_tx_dropped;

size_t drms_console_status(char *out, size_t capacity)
{
  return drms_application_status(out, capacity);
}

static void arm_rx(void)
{
  rx_ready = HAL_UART_Receive_IT(&huart1, &rx_byte, 1) == HAL_OK;
}

void HAL_UART_RxCpltCallback(UART_HandleTypeDef *uart)
{
  unsigned int next;
  if (uart != &huart1)
    return;
  next = (rx_head + 1U) & 127U;
  if (next == rx_tail)
  {
    ++drms_uart_rx_dropped;
    rx_desynced = 1;
  }
  else
  {
    rx_ring[rx_head] = rx_byte;
    __DMB();
    rx_head = next;
  }
  arm_rx();
}

void HAL_UART_TxCpltCallback(UART_HandleTypeDef *uart)
{
  if (uart == &huart1)
    tx_busy = 0;
}

void HAL_UART_ErrorCallback(UART_HandleTypeDef *uart)
{
  if (uart != &huart1)
    return;
  ++drms_uart_rx_dropped;
  rx_desynced = 1;
  rx_ready = 0;
  /* The supervisor rearms RX after HAL has completed its error handling. */
  if (uart->gState == HAL_UART_STATE_READY)
    tx_busy = 0;
}

static uint32_t last_blink;

void drms_runtime_init(void)
{
  rx_head = rx_tail = rx_desynced = rx_ready = tx_busy = 0;
  drms_uart_rx_dropped = drms_uart_tx_dropped = 0;
  memset(&console, 0, sizeof(console));
  last_blink = HAL_GetTick();
  drms_application_init();
  arm_rx();
}

void drms_runtime_poll(void)
{
  static char response[1024];
  drms_application_poll();
  if (!rx_ready)
    arm_rx();
  for (;;)
  {
    size_t length;
    uint8_t byte;
    uint32_t mask = __get_PRIMASK();
    __disable_irq();
    if (rx_desynced)
    {
      /* Discard every pre-overflow byte, then require a NEW line boundary.
         A dropped byte must never turn a damaged line into a control command. */
      console.used = 0;
      console.discard = 1;
      rx_tail = rx_head;
      rx_desynced = 0;
    }
    if (rx_tail == rx_head)
    {
      __set_PRIMASK(mask);
      break;
    }
    byte = rx_ring[rx_tail];
    rx_tail = (rx_tail + 1U) & 127U;
    __set_PRIMASK(mask);
    length = drms_console_feed(&console, byte, response, sizeof(response));
    if (length)
    {
      if (tx_busy)
        ++drms_uart_tx_dropped;
      else
      {
        memcpy(tx_buffer, response, length);
        tx_busy = 1;
        if (HAL_UART_Transmit_DMA(&huart1, (uint8_t *)tx_buffer, (uint16_t)length) != HAL_OK)
        {
          tx_busy = 0;
          ++drms_uart_tx_dropped;
        }
      }
    }
  }
  if ((uint32_t)(HAL_GetTick() - last_blink) >= 500U)
  {
    HAL_GPIO_TogglePin(PWR_LED_GPIO_Port, PWR_LED_Pin);
    last_blink = HAL_GetTick();
  }
}

void drms_runtime_run(void)
{
  drms_runtime_init();
  for (;;)
  {
    drms_runtime_poll();
    tx_thread_sleep(1);
  }
}
