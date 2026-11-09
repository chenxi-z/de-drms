"""Flash maintenance must not run while acquisition or TF ownership is unsafe."""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HEADER = r'''
#include <stdint.h>
typedef struct { uint32_t OPTR; } FlashRegisters;
extern FlashRegisters mock_flash;
#define FLASH (&mock_flash)
#define FLASH_SIZE (1024u * 1024u)
#define FLASH_OPTR_DUALBANK 1u
#define FLASH_OPTR_SWAP_BANK 2u
#define FLASH_BANK_2 2u
#define FLASH_PAGE_NB 64u
#define FLASH_TYPEERASE_PAGES 1u
#define FLASH_TYPEPROGRAM_QUADWORD 2u
#define FLASH_FLAG_ALL_ERRORS 0u
#define HAL_OK 0
#define __HAL_FLASH_CLEAR_FLAG(x) ((void)(x))
typedef struct { uint32_t TypeErase, Banks, Page, NbPages; } FLASH_EraseInitTypeDef;
uint32_t HAL_ICACHE_IsEnabled(void);
int HAL_ICACHE_Disable(void);
int HAL_ICACHE_Enable(void);
void HAL_ICACHE_Invalidate(void);
int HAL_FLASH_Unlock(void);
int HAL_FLASH_Lock(void);
int HAL_FLASHEx_Erase(FLASH_EraseInitTypeDef *, uint32_t *);
int HAL_FLASH_Program(uint32_t, uint32_t, uint32_t);
'''
MOCK = r'''
#include "main.h"
FlashRegisters mock_flash = {1};
unsigned int quiet=1, msc_busy, unlocks;
volatile uint32_t drms_log_state;
uint32_t drms_acq_is_quiescent(void) { return quiet; }
uint32_t drms_msc_blocks_recording(void) { return msc_busy; }
uint32_t HAL_ICACHE_IsEnabled(void) { return 0; }
int HAL_ICACHE_Disable(void) { return 0; }
int HAL_ICACHE_Enable(void) { return 0; }
void HAL_ICACHE_Invalidate(void) {}
int HAL_FLASH_Unlock(void) { ++unlocks; return 0; }
int HAL_FLASH_Lock(void) { return 0; }
int HAL_FLASHEx_Erase(FLASH_EraseInitTypeDef *e, uint32_t *err) { (void)e;*err=0xffffffffu;return 0; }
int HAL_FLASH_Program(uint32_t a, uint32_t b, uint32_t c) { (void)a;(void)b;(void)c;return 0; }
'''


class UserBackendTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        directory = Path(cls.tmp.name)
        (directory / 'main.h').write_text(HEADER)
        (directory / 'mock.c').write_text(MOCK)
        source = ROOT / 'firmware/DE-DRMS-Code/Core'
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Werror', '-I', str(directory),
                        '-I', str(source / 'Inc'), str(source / 'Src/drms_user_backend.c'),
                        str(directory / 'mock.c'), '-o', str(directory / 'backend.so')], check=True)
        cls.lib = ctypes.CDLL(str(directory / 'backend.so'))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def value(self, name):
        return ctypes.c_uint32.in_dll(self.lib, name)

    def setUp(self):
        self.value('quiet').value = 1
        self.value('msc_busy').value = 0
        self.value('drms_log_state').value = 0
        self.value('unlocks').value = 0
        self.value('mock_flash').value = 1

    def test_unsafe_owners_and_layout_do_not_unlock_flash(self):
        for name, unsafe in (('quiet', 0), ('msc_busy', 1), ('drms_log_state', 1), ('mock_flash', 3)):
            self.setUp()
            self.value(name).value = unsafe
            self.assertEqual(self.lib.drms_user_backend_begin(), 0, name)
            self.assertEqual(self.value('unlocks').value, 0, name)
        self.setUp()
        self.assertEqual(self.lib.drms_user_backend_begin(), 1)
        self.assertEqual(self.value('unlocks').value, 1)


if __name__ == '__main__':
    unittest.main()
