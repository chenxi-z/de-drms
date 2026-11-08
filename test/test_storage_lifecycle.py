"""Exercise actual storage service with a fake removable medium."""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HEADER = r'''
#include <stdint.h>
typedef unsigned int UINT;
typedef void VOID;
typedef struct {
  unsigned int fx_media_driver_request;
  unsigned int fx_media_driver_logical_sector;
  unsigned int fx_media_driver_sectors;
  void *fx_media_driver_buffer;
  unsigned int fx_media_driver_status;
  unsigned int fx_media_total_sectors;
} FX_MEDIA;
#define FX_SUCCESS 0
#define FX_IO_ERROR 1
#define FX_NULL 0
#define FX_DRIVER_UNINIT 9
#define FX_DRIVER_INIT 4
#define FX_DRIVER_READ 2
#define FX_SD_VOLUME_NAME "SD"
#define GPIO_PIN_RESET 0
#define SD_CD_GPIO_Port 0
#define SD_CD_Pin 15
#define __get_PRIMASK() ((uint32_t)0)
#define __disable_irq() ((void)0)
#define __set_PRIMASK(m) ((void)(m))
extern FX_MEDIA sdio_disk;
extern uint32_t fx_sd_media_memory[128];
int HAL_GPIO_ReadPin(int, int);
UINT fx_media_open(FX_MEDIA *, const char *, void (*)(FX_MEDIA *), void *, void *, unsigned long);
UINT fx_media_abort(FX_MEDIA *);
UINT fx_media_flush(FX_MEDIA *);
UINT fx_media_close(FX_MEDIA *);
void fx_stm32_sd_driver(FX_MEDIA *);
'''
MOCK = r'''
#include "app_filex.h"
volatile uint32_t drms_log_state,drms_storage_shutdown_ready;
void drms_log_removed(void) { drms_log_state=0; }
FX_MEDIA sdio_disk;
uint32_t fx_sd_media_memory[128];
int card_absent=1, opens, aborts, uninits, open_result,flushes,closes;
int HAL_GPIO_ReadPin(int p,int n) { return card_absent; }
UINT fx_media_open(FX_MEDIA *m,const char *n,void (*f)(FX_MEDIA *),void *d,void *b,unsigned long z)
{ ++opens; return open_result; }
UINT fx_media_abort(FX_MEDIA *m) { ++aborts; return 0; }
UINT fx_media_flush(FX_MEDIA *m) { ++flushes;return 0; }
UINT fx_media_close(FX_MEDIA *m) { ++closes;return 0; }
void fx_stm32_sd_driver(FX_MEDIA *m) { if(m->fx_media_driver_request==FX_DRIVER_UNINIT) ++uninits; }
'''


class StorageLifecycleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        p = Path(cls.tmp.name)
        (p / 'app_filex.h').write_text(HEADER)
        (p / 'main.h').write_text('')
        (p / 'mock.c').write_text(MOCK)
        src = ROOT / 'firmware/DE-DRMS-Code/Core'
        subprocess.run(['cc', '-shared', '-fPIC', '-Werror=implicit-function-declaration',
                        '-I', str(p), '-I', str(src / 'Inc'),
                        *[str(src / f'Src/drms_{name}.c') for name in ('msc', 'storage')],
                        str(p / 'mock.c'),
                        '-o', str(p / 'storage.so')], check=True)
        cls.lib = ctypes.CDLL(str(p / 'storage.so'))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def value(self, name):
        return ctypes.c_uint.in_dll(self.lib, name)

    def setUp(self):
        self.lib.drms_storage_init()
        for name in ('opens', 'aborts', 'uninits', 'open_result', 'flushes', 'closes', 'drms_log_state', 'drms_storage_shutdown_ready'):
            self.value(name).value = 0
        self.value('card_absent').value = 1

    def test_missing_card_is_not_mounted(self):
        self.lib.drms_storage_poll()
        self.assertEqual(self.value('opens').value, 0)
        self.assertEqual(self.value('drms_storage_mounted').value, 0)

    def test_mount_failure_releases_driver_then_recovers(self):
        self.value('card_absent').value = 0
        self.value('open_result').value = 1
        self.lib.drms_storage_poll()
        self.assertEqual(self.value('uninits').value, 1)
        self.assertEqual(self.value('drms_storage_mounted').value, 0)
        self.value('open_result').value = 0
        self.lib.drms_storage_poll()
        self.assertEqual(self.value('drms_storage_mounted').value, 1)

    def test_shutdown_waits_for_log_close_then_flushes_and_closes_media(self):
        self.value('card_absent').value = 0
        self.lib.drms_storage_poll()
        self.value('drms_log_state').value = 3
        self.assertEqual(self.lib.drms_storage_prepare_shutdown(), 0)
        self.assertEqual(self.value('flushes').value, 0)
        self.value('drms_log_state').value = 0
        self.assertEqual(self.lib.drms_storage_prepare_shutdown(), 1)
        self.assertEqual((self.value('flushes').value,self.value('closes').value), (1,1))
        self.assertEqual(self.value('drms_storage_mounted').value, 0)
        self.assertEqual(self.value('drms_storage_shutdown_ready').value, 1)

    def test_removal_aborts_without_flushing_absent_card_and_reinserts(self):
        self.value('card_absent').value = 0
        self.lib.drms_storage_poll()
        self.lib.drms_storage_poll()
        self.assertEqual(self.value('opens').value, 1)
        self.value('card_absent').value = 1
        self.lib.drms_storage_poll()
        self.assertEqual(self.value('aborts').value, 1)
        self.assertEqual(self.value('uninits').value, 1)
        self.assertEqual(self.value('drms_storage_mounted').value, 0)
        self.value('card_absent').value = 0
        self.lib.drms_storage_poll()
        self.assertEqual(self.value('opens').value, 2)


if __name__ == '__main__':
    unittest.main()
