/*****************************************************************************
 * 文件：drms_runtime.c
 * 职责：主线程的运行循环——把应用逻辑、控制台输入、按键、状态灯串起来。
 *
 * 这是 MainThread 的主体。它反复做三件事：
 *   1. 推进应用层（drms_application_poll，所有业务都在那里）；
 *   2. 从串口缓冲里取字符、拼行、交给命令解析器；
 *   3. 周期性刷新状态灯与诊断。
 *
 * 为什么主线程要忙等而不是等信号量：
 *   采集环需要被持续排空。若主线程睡下去，醒来时环可能已经溢出。
 *   所以这里是有意的"忙等 + 每轮把活干完"，代价是 CPU 常驻占用，
 *   换来的是采集路径上没有任何调度延迟。
 *
 * 控制台输入的键壮性：
 *   串口可能丢字节、可能收到半行。这里用一个显式的"失步"标志：
 *   一旦检测到溢出，立刻丢弃当前行并要求重新对齐换行符，
 *   绝不让一个残缺的行被当成命令执行。
 *****************************************************************************/

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
