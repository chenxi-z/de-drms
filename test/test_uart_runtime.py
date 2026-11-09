"""Actual UART service: RX framing recovery and DMA buffer ownership."""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HEADER = r'''
#ifndef TEST_UART_H
#define TEST_UART_H
#include <stdint.h>
#include <stddef.h>
typedef struct { unsigned int gState; } UART_HandleTypeDef;
extern UART_HandleTypeDef huart1;
#define HAL_OK 0
#define HAL_UART_STATE_READY 0
#define PWR_LED_GPIO_Port 0
#define PWR_LED_Pin 7
#define __DMB() ((void)0)
#define __get_PRIMASK() 0U
#define __disable_irq() ((void)0)
#define __set_PRIMASK(x) ((void)(x))
uint32_t HAL_GetTick(void);
void HAL_GPIO_TogglePin(int,int);
int HAL_UART_Receive_IT(UART_HandleTypeDef *,uint8_t *,uint16_t);
int HAL_UART_Transmit_DMA(UART_HandleTypeDef *,uint8_t *,uint16_t);
void tx_thread_sleep(unsigned long);
#endif
'''
MOCK = r'''
#include "main.h"
#include <string.h>
#include <stdio.h>
UART_HandleTypeDef huart1;
uint8_t *rx_pointer,*dma_pointer;
unsigned int tx_calls,rx_calls,tx_size,rx_result,tx_result,app_polls;
char original[768];
uint32_t HAL_GetTick(void) { return 0; }
void HAL_GPIO_TogglePin(int p,int n) {}
void tx_thread_sleep(unsigned long n) {}
int HAL_UART_Receive_IT(UART_HandleTypeDef *h,uint8_t *p,uint16_t n) { ++rx_calls;rx_pointer=p;return rx_result; }
int HAL_UART_Transmit_DMA(UART_HandleTypeDef *h,uint8_t *p,uint16_t n) {
 ++tx_calls;dma_pointer=p;tx_size=n;memcpy(original,p,n);original[n]=0;return tx_result;
}
void drms_application_init(void) {}
void drms_application_poll(void) { ++app_polls; }
size_t drms_application_status(char *out,size_t n) { return snprintf(out,n,"OK status\r\n"); }
int drms_console_dispatch(const char *line) { return 0; }
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *);
void HAL_UART_TxCpltCallback(UART_HandleTypeDef *);
void HAL_UART_ErrorCallback(UART_HandleTypeDef *);
void inject(const char *text) { while(*text) { *rx_pointer=(uint8_t)*text++;HAL_UART_RxCpltCallback(&huart1); } }
void complete_tx(void) { HAL_UART_TxCpltCallback(&huart1); }
void rx_error(void) { HAL_UART_ErrorCallback(&huart1); }
int dma_unchanged(void) { return !memcmp(original,dma_pointer,tx_size); }
'''


class UARTRuntimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        p = Path(cls.tmp.name)
        (p / 'main.h').write_text(HEADER)
        (p / 'usart.h').write_text('#include "main.h"')
        (p / 'tx_api.h').write_text('#include "main.h"')
        (p / 'mock.c').write_text(MOCK)
        src = ROOT / 'firmware/DE-DRMS-Code/Core'
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Werror=implicit-function-declaration',
                        '-I', str(p), '-I', str(src / 'Inc'),
                        str(src / 'Src/drms_runtime.c'), str(src / 'Src/drms_console.c'),
                        str(p / 'mock.c'), '-o', str(p / 'uart.so')], check=True)
        cls.lib = ctypes.CDLL(str(p / 'uart.so'))
        cls.lib.inject.argtypes = [ctypes.c_char_p]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def value(self, name):
        return ctypes.c_uint.in_dll(self.lib, name)

    def setUp(self):
        for name in ('tx_calls', 'rx_calls', 'rx_result', 'tx_result', 'app_polls'):
            self.value(name).value = 0
        self.lib.drms_runtime_init()

    def send(self, text):
        self.lib.inject(text)
        self.lib.drms_runtime_poll()

    def test_dma_buffer_is_not_reused_until_tx_complete(self):
        self.send(b'PING\n')
        self.assertEqual(self.value('tx_calls').value, 1)
        self.send(b'STATUS\n')
        self.assertEqual(self.value('tx_calls').value, 1)
        self.assertEqual(self.value('drms_uart_tx_dropped').value, 1)
        self.assertEqual(self.lib.dma_unchanged(), 1)
        self.lib.complete_tx()
        self.send(b'STATUS\n')
        self.assertEqual(self.value('tx_calls').value, 2)

    def test_overflow_drops_old_queue_and_requires_new_line_boundary(self):
        self.lib.inject(b'x' * 200)
        self.lib.drms_runtime_poll()
        self.assertGreater(self.value('drms_uart_rx_dropped').value, 0)
        self.assertEqual(self.value('tx_calls').value, 0)
        self.send(b'PING\n')
        self.assertEqual((ctypes.c_char * 768).in_dll(self.lib, 'original').value, b'ERR line\r\n')
        self.lib.complete_tx()
        self.send(b'PING\n')
        self.assertEqual((ctypes.c_char * 768).in_dll(self.lib, 'original').value, b'OK PONG\r\n')

    def test_receive_error_rearms_and_discards_partial_line(self):
        self.send(b'PI')
        self.lib.rx_error()
        self.lib.drms_runtime_poll()
        self.send(b'NG\n')
        self.assertEqual((ctypes.c_char * 768).in_dll(self.lib, 'original').value, b'ERR line\r\n')
        self.assertGreater(self.value('rx_calls').value, 2)

    def test_failed_dma_start_does_not_leave_tx_permanently_busy(self):
        self.value('tx_result').value = 1
        self.send(b'PING\n')
        self.value('tx_result').value = 0
        self.send(b'PING\n')
        self.assertEqual(self.value('tx_calls').value, 2)


if __name__ == '__main__':
    unittest.main()
