"""Device identity format shared by USB and protocol code."""
import ctypes
from pathlib import Path
import subprocess
import re
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DeviceIdentityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        out = Path(cls.tmp.name) / 'identity.so'
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Werror',
                        str(ROOT / 'firmware/DE-DRMS-Code/App/platform/stm32/drms_identity.c'),
                        '-o', str(out)], check=True)
        cls.lib = ctypes.CDLL(str(out))
        cls.lib.drms_identity_format.argtypes = [ctypes.c_uint32, ctypes.c_uint32,
                                                  ctypes.c_uint32, ctypes.c_void_p, ctypes.c_size_t]
        cls.lib.drms_identity_format.restype = ctypes.c_size_t

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_three_full_words_and_leading_zeroes(self):
        output = ctypes.create_string_buffer(30)
        length = self.lib.drms_identity_format(1, 0xabcdef01, 0xf0000002, output, len(output))
        self.assertEqual(length, 29)
        self.assertEqual(output.value, b'DRMS-00000001ABCDEF01F0000002')

    def test_usb_string_framework_uses_the_formatted_identity(self):
        source = (ROOT / 'firmware/DE-DRMS-Code/USBX/App/ux_device_descriptors.c').read_text()
        def function(name):
            match = re.search(r'(?:uint8_t \*|static void |static uint8_t )' + name +
                              r'\([^;]*?\)\s*\{.*?^\}', source, re.M | re.S)
            self.assertIsNotNone(match, name)
            return match.group(0)
        preamble = r"""
#include <stdint.h>
#include <string.h>
#include "drms_identity.h"
typedef unsigned long ULONG;
#define USBD_LANGID_STRING 0x0409
#define USBD_IDX_MFC_STR 1
#define USBD_IDX_PRODUCT_STR 2
#define USBD_IDX_SERIAL_STR 3
#define USBD_MANUFACTURER_STRING "STMicroelectronics"
#define USBD_PRODUCT_STRING "DE-DRMS DC Meter"
#define USBD_SERIAL_NUMBER "DE-DRMS001"
#define USBD_STRING_FRAMEWORK_MAX_LENGTH 256
uint8_t USBD_string_framework[USBD_STRING_FRAMEWORK_MAX_LENGTH];
uint32_t HAL_GetUIDw0(void) { return 1; }
uint32_t HAL_GetUIDw1(void) { return 0xabcdef01; }
uint32_t HAL_GetUIDw2(void) { return 0xf0000002; }
static void USBD_Desc_GetString(uint8_t *, uint8_t *, uint16_t *);
static uint8_t USBD_Desc_GetLen(uint8_t *);
"""
        tmp = Path(self.tmp.name)
        extracted = tmp / 'descriptor.c'
        extracted.write_text(preamble + function('USBD_Desc_GetString') +
                             function('USBD_Desc_GetLen') + function('USBD_Get_String_Framework'))
        out = tmp / 'descriptor.so'
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Werror',
                        '-I', str(ROOT / 'firmware/DE-DRMS-Code/App/platform/stm32'),
                        str(extracted),
                        str(ROOT / 'firmware/DE-DRMS-Code/App/platform/stm32/drms_identity.c'),
                        '-o', str(out)], check=True)
        lib = ctypes.CDLL(str(out))
        lib.USBD_Get_String_Framework.argtypes = [ctypes.POINTER(ctypes.c_ulong)]
        lib.USBD_Get_String_Framework.restype = ctypes.POINTER(ctypes.c_ubyte)
        length = ctypes.c_ulong()
        data = lib.USBD_Get_String_Framework(ctypes.byref(length))
        framework = bytes(data[:length.value])
        serial = b'DRMS-00000001ABCDEF01F0000002'
        self.assertTrue(framework.endswith(b'\x09\x04\x03' + bytes([len(serial)]) + serial))

    def test_capacity_is_checked_before_writing(self):
        output = ctypes.create_string_buffer(b'unchanged', 29)
        self.assertEqual(self.lib.drms_identity_format(1, 2, 3, output, len(output)), 0)
        self.assertEqual(output.value, b'unchanged')


if __name__ == '__main__':
    unittest.main()
