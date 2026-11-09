"""STM32 RNG backend: bounded and fail-closed against status/clock failures."""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HEADER = r'''
#include <stdint.h>
typedef struct { uint32_t CR, SR, DR, HTCR, NSCR; } RNG_TypeDef;
extern RNG_TypeDef rng;
extern uint32_t clock_ready, clock_enabled, clock_source, tick;
#define RNG (&rng)
#define RNG_CR_NIST_VALUE 0x00F00D00U
#define RNG_HTCR_NIST_VALUE 0xA2B0U
#define RNG_NSCR_NIST_VALUE 0x17CBBU
#define RNG_CR_CONDRST (1U<<30)
#define RNG_CR_RNGEN (1U<<2)
#define RNG_SR_DRDY 1U
#define RNG_SR_CECS (1U<<1)
#define RNG_SR_SECS (1U<<2)
#define RNG_SR_CEIS (1U<<5)
#define RNG_SR_SEIS (1U<<6)
#define RCC_FLAG_HSI48RDY 1
#define RCC_RNGCLKSOURCE_HSI48 0
#define __HAL_RCC_GET_FLAG(x) (clock_ready)
#define __HAL_RCC_RNG_CLK_ENABLE() (clock_enabled=1)
#define __HAL_RCC_RNG_CLK_DISABLE() (clock_enabled=0)
#define __HAL_RCC_RNG_IS_CLK_ENABLED() (clock_enabled)
#define __HAL_RCC_RNG_CONFIG(x) (clock_source=(x))
uint32_t HAL_GetTick(void);
'''
MOCK = r'''
#include "main.h"
RNG_TypeDef rng;
uint32_t clock_ready, clock_enabled, clock_source, tick;
uint32_t HAL_GetTick(void) { return tick++; }
'''

class EntropyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        p = Path(cls.tmp.name)
        (p / 'main.h').write_text(HEADER)
        (p / 'mock.c').write_text(MOCK)
        source = ROOT / 'firmware/DE-DRMS-Code/App/platform/stm32/drms_entropy.c'
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Werror', '-I', str(p),
                        str(source), str(p / 'mock.c'), '-o', str(p / 'entropy.so')], check=True)
        cls.lib = ctypes.CDLL(str(p / 'entropy.so'))
        cls.lib.drms_entropy_boot_id.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint64)]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.regs = (ctypes.c_uint32 * 5).in_dll(self.lib, 'rng')
        for i in range(5): self.regs[i] = 0
        for name in ('clock_ready', 'clock_enabled', 'clock_source', 'tick'):
            ctypes.c_uint32.in_dll(self.lib, name).value = 0

    def test_valid_words_require_ready_clock_and_clean_status(self):
        ctypes.c_uint32.in_dll(self.lib, 'clock_ready').value = 1
        self.regs[1] = 1
        self.regs[2] = 0x12345678
        out = ctypes.c_uint64()
        self.assertEqual(self.lib.drms_entropy_boot_id(None, ctypes.byref(out)), 1)
        self.assertEqual(out.value, 0x1234567812345678)
        self.assertEqual(ctypes.c_uint32.in_dll(self.lib, 'clock_enabled').value, 0)

    def test_errors_and_timeouts_cannot_return_entropy(self):
        out = ctypes.c_uint64(55)
        self.assertEqual(self.lib.drms_entropy_boot_id(None, ctypes.byref(out)), 0)
        ctypes.c_uint32.in_dll(self.lib, 'clock_ready').value = 1
        for status in (0, 2, 4, 32, 64):
            self.regs[1] = status
            self.assertEqual(self.lib.drms_entropy_boot_id(None, ctypes.byref(out)), 0)
            self.assertEqual(out.value, 0)
            self.assertEqual(ctypes.c_uint32.in_dll(self.lib, 'clock_enabled').value, 0)

    def test_busy_rng_is_not_reconfigured_or_disabled(self):
        ctypes.c_uint32.in_dll(self.lib, 'clock_ready').value = 1
        ctypes.c_uint32.in_dll(self.lib, 'clock_enabled').value = 1
        self.regs[0] = 0x1234
        out = ctypes.c_uint64(9)
        self.assertEqual(self.lib.drms_entropy_boot_id(None, ctypes.byref(out)), 0)
        self.assertEqual(out.value, 0)
        self.assertEqual(self.regs[0], 0x1234)
        self.assertEqual(ctypes.c_uint32.in_dll(self.lib, 'clock_enabled').value, 1)
