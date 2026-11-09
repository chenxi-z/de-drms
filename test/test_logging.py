"""Real logger with FileX boundary doubles: file framing, flush and failure paths."""
import ctypes
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
import zlib
from test_acquisition import Raw

ROOT = Path(__file__).resolve().parents[1]
HEADER = r'''
#include <stdint.h>
typedef unsigned int UINT;
typedef unsigned long ULONG;
typedef struct { int unused; } FX_MEDIA;
typedef struct { int unused; } FX_FILE;
#define FX_SUCCESS 0
#define FX_IO_ERROR 1
#define FX_ALREADY_CREATED 2
#define FX_OPEN_FOR_WRITE 1
UINT fx_file_create(FX_MEDIA *,char *);
UINT fx_file_open(FX_MEDIA *,FX_FILE *,char *,UINT);
UINT fx_file_write(FX_FILE *,void *,ULONG);
UINT fx_file_close(FX_FILE *);
UINT fx_media_flush(FX_MEDIA *);
uint32_t HAL_GetTick(void);
'''
MOCK = r'''
#include "app_filex.h"
#include "drms_logging.h"
#include <string.h>
FX_MEDIA sdio_disk;
volatile unsigned int drms_storage_mounted=1,drms_storage_status;
volatile uint32_t drms_acq_overruns,drms_acq_queue_drops;
uint8_t file_bytes[1048576];
uint32_t written_bytes,writes,closes,flushes,invalidates,creates,fail_at,ticks;
UINT fx_file_create(FX_MEDIA *m,char *name) { ++creates;return 0; }
UINT fx_file_open(FX_MEDIA *m,FX_FILE *f,char *name,UINT mode) { return 0; }
UINT fx_file_write(FX_FILE *f,void *p,ULONG n) {
 ++writes;if(writes==fail_at) return 1;
 if(written_bytes+n>sizeof(file_bytes)) return 1;
 memcpy(file_bytes+written_bytes,p,n);written_bytes+=n;return 0;
}
UINT fx_file_close(FX_FILE *f) { ++closes;return 0; }
UINT fx_media_flush(FX_MEDIA *m) { ++flushes;return 0; }
uint32_t HAL_GetTick(void) { return ticks; }
void drms_storage_invalidate(void) { ++invalidates;drms_storage_mounted=0;drms_log_removed(); }
'''


class Metadata(ctypes.Structure):
    _fields_ = [('rate', ctypes.c_uint32), ('calibrated', ctypes.c_uint32),
                ('calibration_generation', ctypes.c_uint32), ('start_ticks', ctypes.c_uint32),
                ('serial', ctypes.c_uint32), ('scale', ctypes.c_double),
                ('reference', ctypes.c_double), ('year', ctypes.c_uint16),
                *[(name, ctypes.c_ubyte) for name in ('month', 'day', 'hour', 'minute', 'second', 'time_valid')]]


class LoggingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        p = Path(cls.tmp.name)
        (p / 'app_filex.h').write_text(HEADER)
        (p / 'main.h').write_text('')
        (p / 'mock.c').write_text(MOCK)
        src = ROOT / 'firmware/DE-DRMS-Code/Core'
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Werror=implicit-function-declaration',
                        '-I', str(p), '-I', str(src / 'Inc'),
                        *[str(src / f'Src/drms_{name}.c') for name in ('logging', 'log_codec', 'fifo', 'measurement')],
                        str(p / 'mock.c'), '-o', str(p / 'log.so')], check=True)
        cls.lib = ctypes.CDLL(str(p / 'log.so'))
        cls.lib.drms_log_start.argtypes = [ctypes.POINTER(Metadata)]
        cls.lib.drms_log_enqueue.argtypes = [ctypes.POINTER(Raw)]
        rollover_mock = MOCK.replace('UINT fx_file_close(FX_FILE *f) { ++closes;return 0; }',
            'unsigned int enqueue_on_close;\n'
            'UINT fx_file_close(FX_FILE *f) { ++closes;if(enqueue_on_close) {'
            'enqueue_on_close=0;DRMS_RawFrame frame={.sequence=99};drms_log_enqueue(&frame);}'
            'return 0; }')
        (p / 'roll.c').write_text(rollover_mock)
        subprocess.run(['cc', '-shared', '-fPIC', '-DDRMS_LOG_SEGMENT_RECORDS=2',
                        '-I', str(p), '-I', str(src / 'Inc'),
                        *[str(src / f'Src/drms_{name}.c') for name in ('logging', 'log_codec', 'fifo', 'measurement')],
                        str(p / 'roll.c'), '-o', str(p / 'roll.so')], check=True)
        cls.roll = ctypes.CDLL(str(p / 'roll.so'))
        cls.roll.drms_log_start.argtypes = [ctypes.POINTER(Metadata)]
        cls.roll.drms_log_enqueue.argtypes = [ctypes.POINTER(Raw)]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def value(self, name):
        return ctypes.c_uint32.in_dll(self.lib, name)

    def setUp(self):
        self.lib.drms_log_init()
        for name in ('written_bytes', 'writes', 'closes', 'flushes', 'invalidates', 'creates', 'fail_at', 'ticks'):
            self.value(name).value = 0
        self.value('drms_storage_mounted').value = 1
        self.metadata = Metadata(rate=4000, scale=150000., reference=100000.)

    def start(self):
        self.assertEqual(self.lib.drms_log_start(ctypes.byref(self.metadata)), 1)
        self.lib.drms_log_poll()
        self.assertEqual(self.value('drms_log_running').value, 1)

    def test_header_records_footer_and_normal_stop_flush(self):
        self.start()
        frame = Raw(sequence=123)
        frame.bytes[:] = bytes(range(12))
        self.lib.drms_log_enqueue(ctypes.byref(frame))
        self.lib.drms_log_poll()
        self.lib.drms_log_stop()
        self.lib.drms_log_poll()
        data = bytes((ctypes.c_ubyte * 1048576).in_dll(self.lib, 'file_bytes'))[:self.value('written_bytes').value]
        self.assertEqual(len(data), 144)
        self.assertEqual(data[:4], b'DRMS')
        self.assertEqual(struct.unpack_from('<I', data, 12)[0], 4000)
        self.assertEqual(struct.unpack_from('<d', data, 24)[0], 150000.)
        self.assertEqual(data[64:80], bytes(range(12)) + struct.pack('<I', 123))
        self.assertEqual(data[80:84], b'DEND')
        self.assertEqual(struct.unpack_from('<I', data, 88)[0], 1)
        self.assertEqual(struct.unpack_from('<I', data, 60)[0], zlib.crc32(data[:60]))
        self.assertEqual(struct.unpack_from('<I', data, 140)[0], zlib.crc32(data[80:140]))
        self.assertEqual((self.value('closes').value, self.value('flushes').value), (1, 1))
        self.assertEqual(self.value('drms_log_state').value, 0)

    def test_incomplete_stop_never_writes_clean_footer(self):
        self.start()
        self.lib.drms_log_enqueue(ctypes.byref(Raw(sequence=123)))
        self.lib.drms_log_stop_incomplete()
        self.lib.drms_log_stop()  # a later ordinary stop cannot clear the failure
        self.lib.drms_log_poll()
        data = bytes((ctypes.c_ubyte * 1048576).in_dll(self.lib, 'file_bytes'))[:self.value('written_bytes').value]
        self.assertEqual(len(data), 80)
        self.assertEqual(data[:4], b'DRMS')
        self.assertEqual(self.value('closes').value, 1)
        self.assertEqual(self.value('drms_log_state').value, 0)

    def test_io_failure_degrades_storage_and_counts_unwritten_records(self):
        self.start()
        self.value('fail_at').value = 2
        self.lib.drms_log_enqueue(ctypes.byref(Raw(sequence=1)))
        self.lib.drms_log_poll()
        self.assertEqual(self.value('invalidates').value, 1)
        self.assertEqual(self.value('drms_log_running').value, 0)
        self.assertEqual(self.value('drms_log_dropped').value, 1)

    def test_stop_can_cancel_a_pending_open(self):
        self.assertEqual(self.lib.drms_log_start(ctypes.byref(self.metadata)), 1)
        self.lib.drms_log_stop()
        self.lib.drms_log_poll()
        self.assertEqual(self.value('creates').value, 0)
        self.assertEqual(self.value('drms_log_state').value, 0)

    def test_rollover_preserves_frames_arriving_during_close(self):
        lib = self.roll
        lib.drms_log_init()
        self.assertEqual(lib.drms_log_start(ctypes.byref(self.metadata)), 1)
        lib.drms_log_poll()
        for sequence in (1, 2):
            lib.drms_log_enqueue(ctypes.byref(Raw(sequence=sequence)))
        ctypes.c_uint32.in_dll(lib, 'enqueue_on_close').value = 1
        lib.drms_log_poll()  # closes first segment and opens second
        self.assertEqual(ctypes.c_uint32.in_dll(lib, 'drms_log_running').value, 1)
        self.assertEqual(ctypes.c_uint32.in_dll(lib, 'creates').value, 2)
        lib.drms_log_poll()  # consumes the frame inserted during close
        self.assertEqual(ctypes.c_uint32.in_dll(lib, 'drms_log_records').value, 3)
        lib.drms_log_stop()
        lib.drms_log_poll()
        self.assertEqual(ctypes.c_uint32.in_dll(lib, 'closes').value, 2)
        data = bytes((ctypes.c_ubyte * 1048576).in_dll(lib, 'file_bytes'))
        self.assertEqual(data[160:164], b'DRMS')
        self.assertEqual(struct.unpack_from('<I', data, 236)[0], 99)

    def test_periodic_flush_and_full_queue_are_observable(self):
        self.start()
        frame = Raw()
        for sequence in range(32769):
            frame.sequence = sequence
            self.lib.drms_log_enqueue(ctypes.byref(frame))
        self.assertEqual(self.value('drms_log_dropped').value, 1)
        self.value('ticks').value = 1001
        self.lib.drms_log_poll()
        self.assertEqual(self.value('flushes').value, 1)
        self.assertEqual(self.value('drms_log_records').value, 2048)


if __name__ == '__main__':
    unittest.main()
