"""Host regression for actual SD startup code; mocks HAL, never accesses hardware.

Run: python3 -m unittest discover -s test -p 'test_sd_startup.py'
The harness compiles the production sdmmc.c, including its error paths.
"""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

HEADER = r'''
#include <stdint.h>
typedef int HAL_StatusTypeDef;
typedef struct { int ClockEdge,ClockPowerSave,BusWide,HardwareFlowControl,ClockDiv; } SD_Init;
typedef struct { int Instance; SD_Init Init; } SD_HandleTypeDef;
typedef struct { int Pin,Mode,Pull,Speed,Alternate; } GPIO_InitTypeDef;
typedef struct { int PeriphClockSelection,IclkClockSelection,SdmmcClockSelection; } RCC_PeriphCLKInitTypeDef;
#define HAL_OK 0
#define HAL_ERROR 1
#define GPIO_PIN_RESET 0
#define SD_CD_GPIO_Port 1
#define SD_CD_Pin 32768
#define SDMMC1 1
#define SDMMC_CLOCK_EDGE_RISING 0
#define SDMMC_CLOCK_POWER_SAVE_DISABLE 0
#define SDMMC_BUS_WIDE_4B 4
#define SDMMC_HARDWARE_FLOW_CONTROL_DISABLE 0
#define RCC_PERIPHCLK_SDMMC 1
#define RCC_PERIPHCLK_CLK48 2
#define RCC_CLK48CLKSOURCE_HSI48 0
#define RCC_SDMMCCLKSOURCE_CLK48 0
#define GPIO_PIN_2 4
#define GPIO_PIN_8 256
#define GPIO_PIN_9 512
#define GPIO_PIN_10 1024
#define GPIO_PIN_11 2048
#define GPIO_PIN_12 4096
#define GPIO_MODE_AF_PP 0
#define GPIO_NOPULL 0
#define GPIO_SPEED_FREQ_HIGH 0
#define GPIO_AF12_SDMMC1 12
#define GPIOC 1
#define GPIOD 2
#define SDMMC1_IRQn 1
#define __HAL_RCC_SDMMC1_CLK_ENABLE() ((void)0)
#define __HAL_RCC_GPIOC_CLK_ENABLE() ((void)0)
#define __HAL_RCC_GPIOD_CLK_ENABLE() ((void)0)
#define __HAL_RCC_SDMMC1_CLK_DISABLE() ((void)0)
extern int card_absent,init_result,init_calls,deinit_calls,fatal_calls;
int HAL_GPIO_ReadPin(int port,int pin);
int HAL_SD_Init(SD_HandleTypeDef *h);
int HAL_SD_DeInit(SD_HandleTypeDef *h);
int HAL_RCCEx_PeriphCLKConfig(RCC_PeriphCLKInitTypeDef *p);
void HAL_GPIO_Init(int port,GPIO_InitTypeDef *p);
void HAL_GPIO_DeInit(int port,int pins);
void HAL_NVIC_SetPriority(int irq,int priority,int sub);
void HAL_NVIC_EnableIRQ(int irq);
void HAL_NVIC_DisableIRQ(int irq);
void Error_Handler(void);
'''
MOCK = r'''
#include "sdmmc.h"
int card_absent,init_result,init_calls,deinit_calls,fatal_calls;
int HAL_GPIO_ReadPin(int p,int n) { return card_absent; }
int HAL_SD_Init(SD_HandleTypeDef *h) { ++init_calls; return init_result; }
int HAL_SD_DeInit(SD_HandleTypeDef *h) { ++deinit_calls; return 0; }
int HAL_RCCEx_PeriphCLKConfig(RCC_PeriphCLKInitTypeDef *p) { return 0; }
void HAL_GPIO_Init(int p,GPIO_InitTypeDef *s) {}
void HAL_GPIO_DeInit(int p,int n) {}
void HAL_NVIC_SetPriority(int i,int p,int s) {}
void HAL_NVIC_EnableIRQ(int i) {}
void HAL_NVIC_DisableIRQ(int i) {}
void Error_Handler(void) { ++fatal_calls; }
'''


class SDStartupTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        p = Path(cls.tmp.name)
        (p / 'sdmmc.h').write_text(HEADER)
        (p / 'mock.c').write_text(MOCK)
        subprocess.run(['cc', '-shared', '-fPIC', '-Werror=implicit-function-declaration',
                        '-I', str(p), str(ROOT / 'firmware/DE-DRM/Core/Src/sdmmc.c'),
                        str(p / 'mock.c'), '-o', str(p / 'sd.so')], check=True)
        cls.lib = ctypes.CDLL(str(p / 'sd.so'))
        cls.lib.MX_SDMMC1_SD_Init.restype = None

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def value(self, name):
        return ctypes.c_int.in_dll(self.lib, name)

    def setUp(self):
        for name in ('card_absent', 'init_result', 'init_calls', 'deinit_calls', 'fatal_calls'):
            self.value(name).value = 0

    def test_absent_card_never_calls_hal_or_reports_success(self):
        # Previous successful status must not leak into a later absent-card attempt.
        self.lib.MX_SDMMC1_SD_Init()
        self.value('init_calls').value = 0
        self.value('card_absent').value = 1
        self.lib.MX_SDMMC1_SD_Init()
        self.assertEqual(self.value('init_calls').value, 0)
        self.assertNotEqual(self.value('sd_init_status').value, 0)
        self.assertEqual(self.value('fatal_calls').value, 0)

    def test_bad_card_cleans_up_and_returns_error_without_fatal_halt(self):
        for error in (1, 2, 3):  # HAL_ERROR, HAL_BUSY, HAL_TIMEOUT
            with self.subTest(error=error):
                self.setUp()
                self.value('init_result').value = error
                self.lib.MX_SDMMC1_SD_Init()
                self.assertEqual(self.value('sd_init_status').value, error)
                self.assertEqual(self.value('deinit_calls').value, 1)
                self.assertEqual(self.value('fatal_calls').value, 0)

    def test_healthy_card_can_initialize_after_failed_attempt(self):
        self.value('init_result').value = 1
        self.lib.MX_SDMMC1_SD_Init()
        self.value('init_result').value = 0
        self.lib.MX_SDMMC1_SD_Init()
        self.assertEqual(self.value('sd_init_status').value, 0)
        self.assertEqual(self.value('init_calls').value, 2)
        self.assertEqual(self.value('deinit_calls').value, 1)
        self.assertEqual(self.value('fatal_calls').value, 0)


if __name__ == '__main__':
    unittest.main()
