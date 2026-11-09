"""Exercise real USBX MSC callbacks with a minimal USBX and storage double."""
import ctypes
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HEADER = r'''
#include <stdint.h>
typedef void VOID;
typedef unsigned int UINT;
typedef unsigned long ULONG;
typedef unsigned char UCHAR;
typedef struct { ULONG ux_slave_class_storage_media_last_lba; } LUN;
typedef struct { LUN ux_slave_class_storage_lun[1]; } UX_SLAVE_CLASS_STORAGE;
#define UX_SUCCESS 0u
#define UX_ERROR 1u
#define UX_PARAMETER_NOT_USED(x) ((void)(x))
#define UX_SLAVE_CLASS_STORAGE_SENSE_KEY_NOT_READY 2u
#define UX_SLAVE_CLASS_STORAGE_SENSE_KEY_DATA_PROTECT 7u
#define UX_DEVICE_CLASS_STORAGE_SENSE_STATUS(k,c,q) ((k)|((c)<<8)|((q)<<16))
'''
MOCK = r'''
#include <stdint.h>
#include "drms_architecture_contract.h"
uint32_t ready, blocks, cancels;
uint32_t drms_msc_media_ready(void) { return ready; }
DRMS_Result drms_msc_media_info(uint32_t *out) { if(!ready)return DRMS_BUSY;*out=blocks;return DRMS_OK; }
DRMS_Result drms_msc_read(uint32_t lba,uint32_t count,uint8_t *out) { (void)lba;(void)count;(void)out;return DRMS_OK; }
void drms_msc_cancel(void) { ++cancels; }
'''


class Storage(ctypes.Structure):
    _fields_ = [('last_lba', ctypes.c_ulong)]


class MSCUSBBridgeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        path = Path(cls.tmp.name)
        shutil.copyfile(ROOT / 'firmware/DE-DRMS-Code/USBX/App/ux_device_msc.c', path / 'ux_device_msc.c')
        (path / 'ux_device_msc.h').write_text(HEADER)
        (path / 'ux_device_class_storage.h').write_text('/* supplied by the USBX test header */\n')
        (path / 'mock.c').write_text(MOCK)
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Werror=implicit-function-declaration',
                        '-I', str(path), '-I', str(ROOT / 'firmware/DE-DRMS-Code/Core/Inc'),
                        str(path / 'ux_device_msc.c'), str(path / 'mock.c'), '-o', str(path / 'msc.so')], check=True)
        cls.lib = ctypes.CDLL(str(path / 'msc.so'))
        cls.lib.USBD_STORAGE_Status.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong)]
        cls.lib.USBD_STORAGE_Write.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong)]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        for name in ('ready', 'blocks', 'cancels'):
            ctypes.c_uint32.in_dll(self.lib, name).value = 0

    def test_not_ready_and_capacity_follow_current_media(self):
        storage = Storage()
        sense = ctypes.c_ulong()
        self.assertEqual(self.lib.USBD_STORAGE_Status(ctypes.byref(storage), 0, 0, ctypes.byref(sense)), 1)
        self.assertEqual(sense.value & 0xff, 2)
        ctypes.c_uint32.in_dll(self.lib, 'ready').value = 1
        ctypes.c_uint32.in_dll(self.lib, 'blocks').value = 8192
        self.assertEqual(self.lib.USBD_STORAGE_Status(ctypes.byref(storage), 0, 0, ctypes.byref(sense)), 0)
        self.assertEqual(storage.last_lba, 8191)
        ctypes.c_uint32.in_dll(self.lib, 'blocks').value = 2048
        self.assertEqual(self.lib.USBD_STORAGE_Status(ctypes.byref(storage), 0, 0, ctypes.byref(sense)), 0)
        self.assertEqual(storage.last_lba, 2047)

    def test_read_only_reports_write_protection(self):
        sense = ctypes.c_ulong()
        self.assertEqual(self.lib.USBD_STORAGE_Write(None, 0, None, 1, 0, ctypes.byref(sense)), 1)
        self.assertEqual(sense.value & 0xff, 7)

    def test_deactivate_cancels_export(self):
        self.lib.USBD_STORAGE_Deactivate(None)
        self.assertEqual(ctypes.c_uint32.in_dll(self.lib, 'cancels').value, 1)


if __name__ == '__main__':
    unittest.main()
