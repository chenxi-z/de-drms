import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Command(ctypes.Structure):
    _fields_ = [('id', ctypes.c_uint32), ('value', ctypes.c_uint32), ('text', ctypes.c_char * 24)]


class CommandTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        src = ROOT / 'firmware/DE-DRMS-Code/Core'
        lib = Path(cls.tmp.name) / 'cmd.so'
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Wextra', '-Werror',
                        '-I', str(src / 'Inc'),
                        *[str(src / f'Src/drms_{name}.c') for name in ('command', 'time_codec', 'measurement')],
                        '-o', str(lib)], check=True)
        cls.lib = ctypes.CDLL(str(lib))
        cls.lib.drms_command_parse.argtypes = [ctypes.c_char_p, ctypes.POINTER(Command)]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_valid_commands(self):
        for line, ident, value in ((b'START', 1, 4000), (b'START 128000', 1, 128000),
                                   (b'STOP', 2, 0), (b'REF', 3, 0), (b'MEASURE', 4, 0),
                                   (b'CAL', 5, 100000000), (b'CAL 100001234', 5, 100001234),
                                   (b'SAVE', 6, 0), (b'RECORD', 7, 0), (b'END', 8, 0)):
            with self.subTest(line=line):
                out = Command()
                self.assertEqual(self.lib.drms_command_parse(line, ctypes.byref(out)), 1)
                self.assertEqual((out.id, out.value), (ident, value))

    def test_bad_arguments_cannot_be_truncated_or_overflowed(self):
        for line in (b'START 0', b'START 4000junk', b'START 99999999999999', b'START -4000',
                     b'CAL nan', b'CAL 0', b'CAL 100000000 0', b'TIME 2026-02-30T00:00:00'):
            with self.subTest(line=line):
                self.assertEqual(self.lib.drms_command_parse(line, ctypes.byref(Command())), -1)
        self.assertEqual(self.lib.drms_command_parse(b'ZERO', ctypes.byref(Command())), 0)
        self.assertEqual(self.lib.drms_command_parse(b'STARTER', ctypes.byref(Command())), 0)

    def test_time_is_validated_before_hardware_write(self):
        out = Command()
        self.assertEqual(self.lib.drms_command_parse(b'TIME 2026-11-04T13:14:15', ctypes.byref(out)), 1)
        self.assertEqual(out.text, b'2026-11-04T13:14:15')


if __name__ == '__main__':
    unittest.main()
