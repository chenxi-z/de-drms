"""Transport-independent console, including framing and bounded responses."""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ConsoleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        p = Path(cls.tmp.name)
        (p / 'mock.c').write_text('''#include <stdio.h>
#include <stddef.h>
int drms_console_dispatch(const char *line) { (void)line; return 0; }
size_t drms_console_status(char *out,size_t size) {
  int n=snprintf(out,size,"OK sd=1 usb=0\\r\\n");
  return n<0?0:((size_t)n<size?(size_t)n:size-1);
}
''')
        src = ROOT / 'firmware/DE-DRMS-Code/Core'
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Wextra', '-Werror',
                        '-I', str(src / 'Inc'), str(src / 'Src/drms_console.c'),
                        str(p / 'mock.c'), '-o', str(p / 'console.so')], check=True)
        cls.lib = ctypes.CDLL(str(p / 'console.so'))
        cls.lib.drms_console_feed.argtypes = [ctypes.c_void_p, ctypes.c_ubyte,
                                               ctypes.c_void_p, ctypes.c_size_t]
        cls.lib.drms_console_feed.restype = ctypes.c_size_t

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def feed(self, data, size=256):
        state = ctypes.create_string_buffer(128)
        out = ctypes.create_string_buffer(max(size, 1))
        replies = []
        for byte in data:
            n = self.lib.drms_console_feed(state, byte, out, size)
            self.assertLess(n, max(size, 1))
            if n:
                replies.append(out.raw[:n])
        return replies

    def test_ping_and_status_handle_fragmented_crlf(self):
        self.assertEqual(self.feed(b'PING\r\nSTATUS\n'),
                         [b'OK PONG\r\n', b'OK sd=1 usb=0\r\n'])

    def test_unknown_command_does_not_enable_analog_hardware(self):
        self.assertEqual(self.feed(b'START\n'), [b'ERR unsupported\r\n'])

    def test_overlong_line_is_discarded_and_next_command_recovers(self):
        self.assertEqual(self.feed(b'x' * 200 + b'PING\nPING\n'),
                         [b'ERR line\r\n', b'OK PONG\r\n'])

    def test_embedded_nul_cannot_turn_invalid_line_into_ping(self):
        self.assertEqual(self.feed(b'PING\x00trailer\n'), [b'ERR line\r\n'])

    def test_responses_fit_small_and_zero_capacity_buffers(self):
        self.assertEqual(self.feed(b'PING\n', size=4), [b'OK '])
        self.assertEqual(self.feed(b'PING\n', size=0), [])


if __name__ == '__main__':
    unittest.main()
