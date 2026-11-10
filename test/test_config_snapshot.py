"""Configuration read views remain stable while a writer publishes a new version."""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'firmware/DE-DRMS-Code'

class View(ctypes.Structure):
    _fields_ = [('data', ctypes.c_void_p), ('length', ctypes.c_uint32),
                ('running', ctypes.c_uint64), ('saved', ctypes.c_uint64),
                ('slot', ctypes.c_uint32)]

class ConfigSnapshotTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        p = Path(cls.tmp.name)
        (p / 'main.h').write_text('#include <stdint.h>\n#define __get_PRIMASK() 0u\n#define __disable_irq() ((void)0)\n#define __set_PRIMASK(x) ((void)(x))\n')
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Werror', '-I', str(p),
                        '-I', str(ROOT / 'Core/Inc'),
                        str(ROOT / 'Core/Src/drms_config_snapshot.c'), '-o', str(p/'snapshot.so')], check=True)
        cls.lib = ctypes.CDLL(str(p/'snapshot.so'))
        cls.lib.drms_config_snapshot_publish.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint64, ctypes.c_uint64]
        cls.lib.drms_config_snapshot_acquire.argtypes = [ctypes.POINTER(View)]
        cls.lib.drms_config_snapshot_release.argtypes = [ctypes.POINTER(View)]

    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()

    def setUp(self): self.lib.drms_config_snapshot_init()
    def publish(self, data, running=1, saved=0):
        p = ctypes.create_string_buffer(data)
        return self.lib.drms_config_snapshot_publish(p, len(data), running, saved)
    def acquire(self):
        view = View()
        self.assertEqual(self.lib.drms_config_snapshot_acquire(ctypes.byref(view)), 1)
        return view
    def test_pinned_view_remains_unchanged_and_busy_slot_not_overwritten(self):
        self.assertEqual(self.publish(b'old'), 1)
        old = self.acquire()
        self.assertEqual(self.publish(b'new', 2, 1), 1)
        current = self.acquire()
        self.assertEqual((ctypes.string_at(old.data, old.length), old.running, old.saved), (b'old', 1, 0))
        self.assertEqual((ctypes.string_at(current.data, current.length), current.running, current.saved), (b'new', 2, 1))
        self.assertEqual(self.publish(b'third', 3, 2), 0)
        self.lib.drms_config_snapshot_release(ctypes.byref(old))
        self.assertEqual(self.publish(b'third', 3, 2), 1)
        self.assertEqual(ctypes.string_at(current.data, current.length), b'new')
        self.lib.drms_config_snapshot_release(ctypes.byref(current))
    def test_empty_and_oversize_not_published(self):
        self.assertEqual(self.publish(b''), 0)
        self.assertEqual(self.publish(b'x'*1025), 0)
        self.assertEqual(self.lib.drms_config_snapshot_acquire(ctypes.byref(View())), 0)
    def test_multiple_readers_and_idempotent_release(self):
        self.assertEqual(self.publish(b'one'), 1)
        first, second = self.acquire(), self.acquire()
        self.assertEqual(self.publish(b'two', 2), 1)
        self.lib.drms_config_snapshot_release(ctypes.byref(first))
        self.lib.drms_config_snapshot_release(ctypes.byref(first))
        self.assertEqual(self.publish(b'three', 3), 0)
        self.lib.drms_config_snapshot_release(ctypes.byref(second))
        self.assertEqual(self.publish(b'three', 3), 1)
    def test_invalidation_hides_old_value_without_disturbing_pinned_view(self):
        self.assertEqual(self.publish(b'old'), 1)
        old = self.acquire()
        self.lib.drms_config_snapshot_invalidate()
        self.assertEqual(self.lib.drms_config_snapshot_acquire(ctypes.byref(View())), 0)
        self.assertEqual(ctypes.string_at(old.data, old.length), b'old')
        self.lib.drms_config_snapshot_release(ctypes.byref(old))
        self.assertEqual(self.publish(b'new', 2), 1)
