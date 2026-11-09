"""Actual FileX HAL glue must tolerate CD bouncing before first initialization."""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HEADER = r'''
#ifndef MOCK_SD_H
#define MOCK_SD_H
#include <stdint.h>
typedef int INT;
typedef unsigned int UINT;
typedef int TX_SEMAPHORE;
typedef struct { int Instance; } SD_HandleTypeDef;
#define FX_STM32_SD_INIT 1
#define HAL_OK 0
#define HAL_ERROR 1
#define HAL_SD_CARD_TRANSFER 4
#define SDMMC1 1
#define UNUSED(x) ((void)(x))
#define __HAL_RCC_SDMMC1_FORCE_RESET() reset_controller()
#define __HAL_RCC_SDMMC1_RELEASE_RESET() ((void)0)
void reset_controller(void);
extern SD_HandleTypeDef hsd1;
extern int sd_init_status;
void MX_SDMMC1_SD_Init(void);
int HAL_SD_DeInit(SD_HandleTypeDef *);
int HAL_SD_GetCardState(SD_HandleTypeDef *);
int HAL_SD_ReadBlocks_DMA(SD_HandleTypeDef *,uint8_t *,UINT,UINT);
int HAL_SD_WriteBlocks_DMA(SD_HandleTypeDef *,uint8_t *,UINT,UINT);
int tx_semaphore_put(TX_SEMAPHORE *);
#endif
'''
MOCK = r'''
#include "sdmmc.h"
SD_HandleTypeDef hsd1;
int sd_init_status=1,deinits,card_queries,dma_active,deinit_with_dma;
void reset_controller(void) { dma_active=0; }
void MX_SDMMC1_SD_Init(void) {}
int HAL_SD_DeInit(SD_HandleTypeDef *h) { ++deinits;if(dma_active) ++deinit_with_dma; return 0; }
int HAL_SD_GetCardState(SD_HandleTypeDef *h) { ++card_queries; return 4; }
int HAL_SD_ReadBlocks_DMA(SD_HandleTypeDef *h,uint8_t *b,UINT s,UINT n) { return 0; }
int HAL_SD_WriteBlocks_DMA(SD_HandleTypeDef *h,uint8_t *b,UINT s,UINT n) { return 0; }
int tx_semaphore_put(TX_SEMAPHORE *s) { return 0; }
void set_instance(int n) { hsd1.Instance=n; }
'''


class SDGlueTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        p = Path(cls.tmp.name)
        for name in ('fx_stm32_sd_driver.h', 'sdmmc.h'):
            (p / name).write_text(HEADER)
        (p / 'mock.c').write_text(MOCK)
        # Copy just this source to let mocks replace its sibling generated header.
        src = ROOT / 'firmware/DE-DRMS-Code/FileX/Target/fx_stm32_sd_driver_glue.c'
        (p / 'glue.c').write_text(src.read_text())
        subprocess.run(['cc', '-shared', '-fPIC', '-Werror=implicit-function-declaration',
                        '-I', str(p), str(p / 'glue.c'), str(p / 'mock.c'),
                        '-o', str(p / 'glue.so')], check=True)
        cls.lib = ctypes.CDLL(str(p / 'glue.so'))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def value(self, name):
        return ctypes.c_int.in_dll(self.lib, name)

    def setUp(self):
        self.lib.set_instance(0)
        for name in ('deinits', 'card_queries', 'dma_active', 'deinit_with_dma'):
            self.value(name).value = 0
        self.value('sd_init_status').value = 1

    def test_cleanup_before_first_init_does_not_dereference_null_instance(self):
        self.assertEqual(self.lib.fx_stm32_sd_deinit(0), 0)
        self.assertEqual(self.value('deinits').value, 0)

    def test_uninitialized_card_status_does_not_access_peripheral(self):
        self.assertNotEqual(self.lib.fx_stm32_sd_get_status(0), 0)
        self.assertEqual(self.value('card_queries').value, 0)

    def test_failed_transfer_is_quiesced_before_deinit_and_semaphore_deletion(self):
        self.lib.set_instance(1)
        self.value('dma_active').value = 1
        self.lib.fx_stm32_sd_deinit(0)
        self.assertEqual(self.value('deinit_with_dma').value, 0)
        self.assertEqual(self.value('dma_active').value, 0)

    def test_normal_deinit_revokes_success_status(self):
        self.lib.set_instance(1)
        self.value('sd_init_status').value = 0
        self.assertEqual(self.lib.fx_stm32_sd_deinit(0), 0)
        self.assertEqual(self.value('deinits').value, 1)
        self.assertNotEqual(self.value('sd_init_status').value, 0)


if __name__ == '__main__':
    unittest.main()
