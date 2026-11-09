"""Cover the ST FileX driver's cleanup after removal, using its actual source."""
import ctypes
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
DRIVER = ROOT / 'firmware/DE-DRMS-Code/Middlewares/ST/filex/common/drivers/fx_stm32_sd_driver.c'
HEADER = r'''
#include <stdint.h>
#include <string.h>
typedef unsigned int UINT;
typedef unsigned long ULONG;
typedef unsigned char UCHAR;
typedef int INT;
typedef void VOID;
typedef struct {
 UINT fx_media_driver_request,fx_media_driver_status,fx_media_driver_sectors;
 ULONG fx_media_driver_logical_sector,fx_media_hidden_sectors;
 UCHAR *fx_media_driver_buffer;
} FX_MEDIA;
#define FX_SUCCESS 0
#define FX_IO_ERROR 1
#define FX_BUFFER_ERROR 2
#define FX_DRIVER_INIT 1
#define FX_DRIVER_UNINIT 2
#define FX_DRIVER_ABORT 3
#define FX_DRIVER_READ 4
#define FX_DRIVER_WRITE 5
#define FX_DRIVER_FLUSH 6
#define FX_DRIVER_BOOT_READ 7
#define FX_DRIVER_BOOT_WRITE 8
#define FX_STM32_SD_INIT 1
#define FX_STM32_SD_DMA_API 0
#define FX_STM32_SD_CACHE_MAINTENANCE 0
#define FX_STM32_SD_DEFAULT_SECTOR_SIZE 512
#define FX_STM32_SD_DEFAULT_TIMEOUT 3
#define FX_STM32_SD_INSTANCE 0
#define FX_STM32_SD_CURRENT_TIME() fake_time()
unsigned int fake_time(void);
int fx_stm32_sd_get_status(UINT);
int fx_stm32_sd_init(UINT);
int fx_stm32_sd_deinit(UINT);
int fx_stm32_sd_read_blocks(UINT,UINT *,UINT,UINT);
int fx_stm32_sd_write_blocks(UINT,UINT *,UINT,UINT);
void tx_thread_sleep(ULONG);
#define _fx_utility_memory_copy(a,b,n) memcpy(b,a,n)
'''
MOCK = r'''
#include "fx_stm32_sd_driver.h"
int busy,init_calls,deinit_calls,deinit_result,sleeps;
static unsigned int ticks;
unsigned int fake_time(void) { return ticks++; }
int fx_stm32_sd_get_status(UINT n) { return busy; }
int fx_stm32_sd_init(UINT n) { ++init_calls; return 0; }
int fx_stm32_sd_deinit(UINT n) { ++deinit_calls; return deinit_result; }
int fx_stm32_sd_read_blocks(UINT a,UINT *b,UINT c,UINT d) { return 0; }
int fx_stm32_sd_write_blocks(UINT a,UINT *b,UINT c,UINT d) { return 0; }
void tx_thread_sleep(ULONG n) { ++sleeps; }
UINT _fx_partition_offset_calculate(void *a,UINT b,ULONG *c,ULONG *d) { *c=0; return 0; }
void fx_stm32_sd_driver(FX_MEDIA *);
int request(UINT op) { FX_MEDIA media={0};media.fx_media_driver_request=op;fx_stm32_sd_driver(&media);return media.fx_media_driver_status; }
'''


class SDDriverRecoveryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        p = Path(cls.tmp.name)
        hooks = set(re.findall(r'\b(FX_STM32_SD_(?:PRE|POST|READ|WRITE)\w*)\(', DRIVER.read_text()))
        header = HEADER + ''.join(f'\n#define {hook}(...) ((void)0)' for hook in hooks)
        (p / 'fx_stm32_sd_driver.h').write_text(header)
        (p / 'mock.c').write_text(MOCK)
        subprocess.run(['cc', '-shared', '-fPIC', '-Werror=implicit-function-declaration',
                        '-I', str(p), str(DRIVER), str(p / 'mock.c'),
                        '-o', str(p / 'driver.so')], check=True)
        cls.lib = ctypes.CDLL(str(p / 'driver.so'))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def value(self, name):
        return ctypes.c_int.in_dll(self.lib, name)

    def setUp(self):
        self.value('busy').value = 0
        self.value('deinit_result').value = 0
        self.lib.request(2)
        for name in ('init_calls', 'deinit_calls', 'sleeps'):
            self.value(name).value = 0
        self.assertEqual(self.lib.request(1), 0)

    def test_removed_card_does_not_block_abort_or_uninit(self):
        self.value('busy').value = 1
        self.assertEqual(self.lib.request(3), 0)
        self.assertEqual(self.lib.request(2), 0)
        self.assertEqual(self.value('deinit_calls').value, 1)
        self.assertEqual(self.value('sleeps').value, 0)
        self.value('busy').value = 0
        self.assertEqual(self.lib.request(1), 0)
        self.assertEqual(self.value('init_calls').value, 2)

    def test_failed_deinit_still_invalidates_old_initialization(self):
        self.value('deinit_result').value = 1
        self.assertNotEqual(self.lib.request(2), 0)
        self.value('deinit_result').value = 0
        self.assertEqual(self.lib.request(1), 0)
        self.assertEqual(self.value('init_calls').value, 2)

    def test_busy_card_wait_yields_cpu(self):
        self.value('busy').value = 1
        self.assertNotEqual(self.lib.request(4), 0)
        self.assertGreater(self.value('sleeps').value, 0)


if __name__ == '__main__':
    unittest.main()
