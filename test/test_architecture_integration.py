"""架构集成测试（T7）：开机监测、无卡/坏卡、记录叠加、停止不停止监测、
RAM 预算与缓冲尺寸、模块边界（算法无 HAL/RTOS）。"""
import ctypes
import re
from pathlib import Path
import subprocess
import tempfile
import unittest

import test_application as app
from test_acquisition import HEADER as ACQ_HEADER, MOCK as ACQ_MOCK
from test_calibration_journal import MOCK as CAL_MOCK
from test_logging import HEADER as FX_HEADER, MOCK as FX_MOCK

ROOT = Path(__file__).resolve().parents[1]


class ArchitectureIntegrationTest(unittest.TestCase):
    """复用 test_application 的编译产物（同一次 setUpClass）。"""

    @classmethod
    def setUpClass(cls):
        app.ApplicationTest.setUpClass()
        cls.base = app.ApplicationTest

    @classmethod
    def tearDownClass(cls):
        app.ApplicationTest.tearDownClass()

    def setUp(self):
        type(self).base.instance += 1
        import shutil
        p = Path(type(self).base.tmp.name)
        target = p / f'app-{type(self).base.instance}.so'
        shutil.copyfile(p / 'app.so', target)
        self.lib = ctypes.CDLL(str(target))
        self.lib.drms_console_dispatch.argtypes = [ctypes.c_char_p]
        self.lib.drms_application_status.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
        self.lib.drms_application_status.restype = ctypes.c_size_t
        self.lib.reset_flash()
        self.lib.drms_log_init()
        self.lib.drms_application_init()

    def value(self, name):
        return ctypes.c_uint32.in_dll(self.lib, name)

    def card(self, present):
        ctypes.c_int.in_dll(self.lib, 'sd_card_present').value = 1 if present else 0

    def status(self):
        buffer = ctypes.create_string_buffer(1024)
        length = self.lib.drms_application_status(buffer, len(buffer))
        text = buffer.raw[:length].decode()
        parts = text.split()
        result = {}
        for item in parts[1:]:
            if '=' in item:
                key, _, val = item.partition('=')
                result[key] = int(val)
        return result

    def test_boot_enters_monitoring_without_card(self):
        # 开机自动监测；无卡不阻止（无卡可监测）
        self.assertEqual(self.value('drms_acq_running').value, 1)
        status = self.status()
        self.assertEqual(status['running'], 1)
        self.assertEqual(status['log'], 0)   # 记录默认关闭
        self.assertEqual(status['sd'], 0)    # 未挂载
        self.lib.drms_msc_owner.restype = ctypes.c_int
        self.assertEqual(self.lib.drms_msc_owner(), 0)  # LOCAL

    def test_record_requires_card_and_refused_without_it(self):
        self.card(False)
        self.lib.drms_application_poll()
        self.assertEqual(self.lib.drms_console_dispatch(b'RECORD'), 1)
        self.lib.drms_application_poll()
        # 无卡：不建立文件、不进入记录；监测继续
        self.assertEqual(self.value('drms_log_running').value, 0)
        self.assertEqual(self.value('drms_acq_running').value, 1)

    def test_record_over_monitoring_and_stop_keeps_monitoring(self):
        self.card(True)
        self.lib.drms_storage_poll()
        self.assertEqual(self.value('drms_storage_mounted').value, 1)
        self.assertEqual(self.lib.drms_console_dispatch(b'RECORD'), 1)
        for _ in range(3):
            self.lib.drms_application_poll()
            self.lib.drms_log_poll()
        self.assertEqual(self.status()['log'], 1)
        self.assertEqual(self.status()['running'], 1)
        # 结束记录：监测不停止
        self.assertEqual(self.lib.drms_console_dispatch(b'END'), 1)
        for _ in range(4):
            self.lib.drms_application_poll()
            self.lib.drms_log_poll()
        status = self.status()
        self.assertEqual(status['log'], 0)
        self.assertEqual(status['running'], 1)  # 停止记录 ≠ 停止采集

    def test_two_recordings_can_start_after_each_close(self):
        self.card(True)
        self.lib.drms_storage_poll()
        for _ in range(2):
            self.assertEqual(self.lib.drms_console_dispatch(b'RECORD'), 1)
            for _ in range(3):
                self.lib.drms_application_poll()
                self.lib.drms_log_poll()
            self.assertEqual(self.value('drms_log_running').value, 1)
            self.assertEqual(self.lib.drms_console_dispatch(b'END'), 1)
            for _ in range(4):
                self.lib.drms_application_poll()
                self.lib.drms_log_poll()
            self.assertEqual(self.value('drms_log_state').value, 0)

    def test_cancel_during_file_open_allows_next_recording(self):
        self.card(True)
        self.lib.drms_storage_poll()
        self.assertEqual(self.lib.drms_console_dispatch(b'RECORD'), 1)
        self.lib.drms_application_poll()
        self.assertEqual(self.lib.drms_console_dispatch(b'END'), 1)
        for _ in range(5):
            self.lib.drms_application_poll()
            self.lib.drms_log_poll()
            self.assertEqual(self.value('drms_log_running').value, 0)
        self.assertEqual(self.value('drms_log_state').value, 0)
        self.assertEqual(self.lib.drms_console_dispatch(b'RECORD'), 1)
        for _ in range(4):
            self.lib.drms_application_poll()
            self.lib.drms_log_poll()
        self.assertEqual(self.value('drms_log_running').value, 1)

    def test_open_timeout_cancels_and_allows_next_recording(self):
        self.card(True)
        self.lib.drms_storage_poll()
        self.assertEqual(self.lib.drms_console_dispatch(b'RECORD'), 1)
        self.lib.drms_application_poll()
        for _ in range(11):
            self.lib.advance_ms(100)
            self.lib.drms_acq_drdy()
            self.lib.complete_frame(2800000, 4200000)
            self.lib.drms_application_poll()
        for _ in range(3):
            self.lib.drms_log_poll()
            self.lib.drms_application_poll()
        self.assertEqual(self.value('drms_log_state').value, 0)
        self.assertEqual(self.lib.drms_console_dispatch(b'RECORD'), 1)
        for _ in range(3):
            self.lib.drms_application_poll()
            self.lib.drms_log_poll()
        self.assertEqual(self.value('drms_log_running').value, 1)

    def test_backlog_does_not_make_old_measurement_fresh(self):
        self.lib.drms_acq_drdy()
        self.lib.complete_frame(2800000, 4200000)
        self.lib.advance_ms(100)
        self.lib.drms_acq_drdy()
        self.lib.complete_frame(2800000, 4200000)
        self.lib.drms_application_poll()
        self.assertEqual(self.status()['r_valid'], 0)

    def test_monitor_state_is_unconfigured_without_client_table(self):
        # 未配置区间表/基线：monitor 报 INVALID(无基线)；无表时为 UNCONFIGURED。
        # 两种都绝不冒充正常等级（CONFIRMED）。
        self.lib.advance_ms(10)
        self.lib.drms_application_poll()
        state = self.status()['monitor']
        self.assertIn(state, (0, 2))  # INVALID(无基线) 或 UNCONFIGURED
        self.assertNotEqual(state, 5)  # 绝不是 CONFIRMED

    def test_ram_budget_and_frame_sizes_unchanged(self):
        build = Path('/tmp/de-drms-t7-verify')
        if not build.exists():
            self.skipTest('ARM map not built in this run')
        elfs = list(build.glob('*.map'))
        self.assertTrue(elfs)
        m = elfs[0].read_text(errors='ignore')
        data = int(re.search(r'^\.data\s+0x[0-9a-f]+\s+(0x[0-9a-f]+)', m, re.M).group(1), 16)
        bss = int(re.search(r'^\.bss\s+0x[0-9a-f]+\s+(0x[0-9a-f]+)', m, re.M).group(1), 16)
        self.assertLessEqual(data + bss, 736 * 1024, 'main RAM budget (R6)')
        for name, want in (('frames', 0x10000), ('records', 0x80000), ('staging', 0x8000)):
            found = re.search(r'\.bss\.' + name + r'\s+0x[0-9a-f]+\s+(0x[0-9a-f]+)', m)
            self.assertEqual(int(found.group(1), 16), want, name)

    def test_algorithm_modules_stay_free_of_hal_and_rtos(self):
        allowed = {'drms_architecture_contract.h', 'drms_filter.h', 'drms_classifier.h',
                   'drms_baseline.h', 'stdint.h', 'stddef.h', 'string.h', 'math.h'}
        for name in ('monitor', 'filter', 'classifier', 'baseline'):
            text = (ROOT / f'firmware/DE-DRMS-Code/Core/Src/drms_{name}.c').read_text()
            includes = set(re.findall(r'#include\s+"([^"]+)"', text))
            self.assertLessEqual(includes, allowed, name)
            lowered = text.lower()
            for banned in ('hal_', 'tx_api', 'fx_api', 'ux_api', 'stm32'):
                self.assertNotIn(banned, lowered, f'{name} must not reference {banned}')


if __name__ == '__main__':
    unittest.main()
