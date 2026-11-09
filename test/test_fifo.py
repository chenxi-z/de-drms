"""Real bounded SPSC queue: fullness, wraparound and publication ordering."""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]


class FIFO(ctypes.Structure):
    _fields_ = [('head', ctypes.c_uint32), ('tail', ctypes.c_uint32),
                ('capacity', ctypes.c_uint32), ('stride', ctypes.c_uint32),
                ('storage', ctypes.c_void_p)]


class FIFOTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        lib = Path(cls.tmp.name) / 'fifo.so'
        src = ROOT / 'firmware/DE-DRMS-Code/Core'
        subprocess.run(['cc', '-shared', '-fPIC', '-O2', '-Wall', '-Wextra', '-Werror',
                        '-I', str(src / 'Inc'), str(src / 'Src/drms_fifo.c'),
                        '-o', str(lib)], check=True)
        cls.lib = ctypes.CDLL(str(lib))
        for name in ('push', 'pop'):
            getattr(cls.lib, 'drms_fifo_' + name).argtypes = [ctypes.POINTER(FIFO), ctypes.c_void_p]
        cls.lib.drms_fifo_init.argtypes = [ctypes.POINTER(FIFO), ctypes.c_void_p,
                                          ctypes.c_uint32, ctypes.c_uint32]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.data = (ctypes.c_uint32 * 8)()
        self.queue = FIFO()
        self.assertEqual(self.lib.drms_fifo_init(ctypes.byref(self.queue), self.data, 8, 4), 1)

    def test_full_queue_never_overwrites_unread_sample(self):
        for value in range(8):
            self.assertEqual(self.lib.drms_fifo_push(ctypes.byref(self.queue), ctypes.byref(ctypes.c_uint32(value))), 1)
        self.assertEqual(self.lib.drms_fifo_push(ctypes.byref(self.queue), ctypes.byref(ctypes.c_uint32(99))), 0)
        out = ctypes.c_uint32()
        for value in range(8):
            self.assertEqual(self.lib.drms_fifo_pop(ctypes.byref(self.queue), ctypes.byref(out)), 1)
            self.assertEqual(out.value, value)
        self.assertEqual(self.lib.drms_fifo_pop(ctypes.byref(self.queue), ctypes.byref(out)), 0)

    def test_unsigned_counter_rollover_preserves_order(self):
        self.queue.head = self.queue.tail = 0xfffffffc
        self.test_full_queue_never_overwrites_unread_sample()

    def test_invalid_capacity_is_rejected(self):
        self.assertEqual(self.lib.drms_fifo_init(ctypes.byref(self.queue), self.data, 7, 4), 0)

    def test_one_producer_and_one_consumer(self):
        errors = []

        def produce():
            for value in range(3000):
                item = ctypes.c_uint32(value)
                while not self.lib.drms_fifo_push(ctypes.byref(self.queue), ctypes.byref(item)):
                    pass

        def consume():
            out = ctypes.c_uint32()
            for value in range(3000):
                while not self.lib.drms_fifo_pop(ctypes.byref(self.queue), ctypes.byref(out)):
                    pass
                if out.value != value:
                    errors.append((value, out.value))

        threads = [threading.Thread(target=produce), threading.Thread(target=consume)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)
            self.assertFalse(thread.is_alive())
        self.assertEqual(errors, [])


if __name__ == '__main__':
    unittest.main()
