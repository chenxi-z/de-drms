"""用户配置/R0 事务测试：真实 drms_user_config.c + 可注入 Flash 后端替身。

覆盖 R3/T5：schema1 编码黄金向量、区间/UTF-8/有限性校验、apply/save/
commit_baseline 事务与版本语义、每步掉电注入、同值 NO_CHANGE、未来 schema
保护、校准代次变化使旧 R0 失效。
"""
import ctypes
import re
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]

HEADER = r'''
#ifndef MOCK_UC_H
#define MOCK_UC_H
#include <stdint.h>
#include <stddef.h>
#define __get_PRIMASK() ((uint32_t)0)
#define __disable_irq() ((void)0)
#define __set_PRIMASK(m) ((void)(m))
#endif
'''

OK, ACCEPTED, BUSY, INVALID, STALE = 0, 1, 2, 3, 4
NO_CHANGE, IO_ERROR, TIMEOUT, CANCELLED, INCOMPLETE = 5, 6, 7, 8, 9
QUARANTINED, UNSUPPORTED, EMPTY = 10, 11, 12

PAGE = 8192


class FakeFlash:
    """页后端替身：RAM 页 + 每步掉电注入（begin 之后第 N 步处断电）。"""
    CODE = r'''
#include "drms_user_config.h"
#include <string.h>
static uint8_t pages[2][8192];
static int session, fail_at_step, step;
int last_erased, program_calls, begin_calls;
void fake_reset(void) { memset(pages, 0xFF, sizeof(pages)); session=fail_at_step=step=0;
  last_erased=program_calls=begin_calls=0; }
void fake_set_fail(int n) { fail_at_step=n; step=0; }
uint8_t *fake_page(int p) { return pages[p]; }
int drms_user_backend_begin(void) { ++begin_calls; if (fail_at_step && ++step==fail_at_step) return 0; session=1; return 1; }
void drms_user_backend_end(void) { session=0; }
int drms_user_backend_erase(unsigned int page) { ++step; last_erased=(int)page;
  if (fail_at_step && step==fail_at_step+1) return 0;
  memset(pages[page], 0xFF, 8192); return 1; }
int drms_user_backend_program(unsigned int page, unsigned int offset, const uint8_t q[16]) {
  ++program_calls; ++step;
  if (fail_at_step && step==fail_at_step+1) return 0;
  if (!session || offset+16 > 8192) return 0;
  memcpy(pages[page]+offset, q, 16); return 1; }
int drms_user_backend_read(unsigned int page, unsigned int offset, uint8_t *out, unsigned int len) {
  if (offset+len > 8192) return 0;
  memcpy(out, pages[page]+offset, len); return 1; }
'''


def crc32(b):
    return zlib.crc32(b) & 0xFFFFFFFF


def build_body(version=1, cal_version=0, r0_valid=0, r0=0.0, intervals=(), params=None):
    body = bytearray(b'DRMSUC01')
    body += b'\x00\x00\x00\x00'  # body_len 占位
    body += struct.pack('<Q', version)
    body += struct.pack('<Q', cal_version)
    body += bytes([1 if r0_valid else 0, 0, 0, 0])
    body += struct.pack('<d', r0)
    if intervals:
        tlv = bytearray(struct.pack('<H', len(intervals)))
        for (ident, level, closed, lo, hi, h, name) in intervals:
            nm = name.encode() if isinstance(name, str) else name
            tlv += struct.pack('<HBBdddB', ident, level, 1 if closed else 0, lo, hi, h, len(nm))
            tlv += nm
        body += struct.pack('<HH', 1, len(tlv)) + tlv
    p = params or (4000, 1000, 200000, 50000, 32000)
    body += struct.pack('<HHIQQQQ', 2, 36, *p)
    body[8:12] = struct.pack('<I', len(body) + 4)  # 先定长再算 CRC
    body += struct.pack('<I', crc32(bytes(body)))
    return bytes(body)

def with_baseline_policy(body, count, duration, max_cv):
    data = bytearray(body[:-4])
    data += struct.pack('<HHIQd', 0xd701, 20, count, duration, max_cv)
    struct.pack_into('<I', data, 8, len(data) + 4)
    return bytes(data) + struct.pack('<I', crc32(data))

class BaselinePolicy(ctypes.Structure):
    _fields_ = [('min_count', ctypes.c_uint32), ('min_duration_us', ctypes.c_uint64),
                ('max_cv', ctypes.c_double)]


class UserConfigTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        p = Path(cls.tmp.name)
        (p / 'main.h').write_text(HEADER)
        (p / 'fake.c').write_text(FakeFlash.CODE)
        src = ROOT / 'firmware/DE-DRMS-Code/Core'
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Werror=implicit-function-declaration',
                        '-I', str(p), '-I', str(src / 'Inc'),
                        str(src / 'Src/drms_user_config.c'), str(src / 'Src/drms_measurement.c'),
                        str(p / 'fake.c'), '-o', str(p / 'uc.so')], check=True)
        cls.lib = ctypes.CDLL(str(p / 'uc.so'))
        cls.lib.drms_user_config_apply.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_uint64]
        cls.lib.drms_user_config_save.argtypes = [ctypes.c_uint64]
        cls.lib.drms_user_config_commit_baseline.argtypes = [ctypes.c_double, ctypes.c_uint64, ctypes.c_uint64]
        cls.lib.fake_page.restype = ctypes.c_void_p
        cls.lib.fake_page.argtypes = [ctypes.c_int]
        cls.lib.drms_user_config_r0.restype = ctypes.c_double
        cls.lib.drms_user_config_run_version.restype = ctypes.c_uint64
        cls.lib.drms_user_config_persisted_version.restype = ctypes.c_uint64
        cls.lib.drms_user_config_r0_calibration_version.restype = ctypes.c_uint64
        cls.lib.drms_user_config_get_baseline_policy.argtypes = [ctypes.POINTER(BaselinePolicy)]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.lib.fake_reset()
        self.lib.drms_user_config_init()
        self.lib.drms_user_config_set_calibration_generation(0)

    def page(self, n):
        dst = self.page_ptr(n)
        return ctypes.string_at(dst, PAGE)

    def page_ptr(self, n):
        return self.lib.fake_page(n)

    def set_fail(self, step):
        self.lib.fake_set_fail(step)

    def test_baseline_policy_validates_and_survives_save_and_reboot(self):
        policy = BaselinePolicy()
        self.assertEqual(self.lib.drms_user_config_get_baseline_policy(ctypes.byref(policy)), 0)
        body = with_baseline_policy(build_body(), 400, 1000000, 0.01)
        self.assertEqual(self.lib.drms_user_config_apply(body, len(body), 0), OK)
        self.assertEqual(self.lib.drms_user_config_get_baseline_policy(ctypes.byref(policy)), 1)
        self.assertEqual((policy.min_count, policy.min_duration_us, policy.max_cv), (400, 1000000, 0.01))
        self.assertEqual(self.lib.drms_user_config_save(1), OK)
        self.reboot()
        self.assertEqual(self.lib.drms_user_config_get_baseline_policy(ctypes.byref(policy)), 1)
        self.assertEqual((policy.min_count, policy.min_duration_us, policy.max_cv), (400, 1000000, 0.01))

    def test_baseline_policy_rejects_invalid_values(self):
        for count, duration, cv in [(0, 1, 0.1), (0, 0, 0.1), (10, 0, -1), (10, 0, float('nan'))]:
            body = with_baseline_policy(build_body(), count, duration, cv)
            self.assertEqual(self.lib.drms_user_config_apply(body, len(body), 0), INVALID)

    def reboot(self, generation=0):
        # 重启 = init + 设定当前校准代次 + load（依赖检查在 load 内执行）
        self.lib.drms_user_config_init()
        self.lib.drms_user_config_set_calibration_generation(generation)
        self.lib.drms_user_config_load()

    def test_save_and_baseline_preserve_alias_and_unknown_fields(self):
        base = bytearray(build_body())[:-4]
        extras = struct.pack('<HH', 3, 5) + b'meter'
        extras += struct.pack('<HH', 1234, 4) + b'\x00\x01\xfe\xff'
        base += extras
        struct.pack_into('<I', base, 8, len(base) + 4)
        body = bytes(base) + struct.pack('<I', crc32(base))
        self.assertEqual(self.lib.drms_user_config_apply(body, len(body), 0), OK)
        self.assertEqual(self.lib.drms_user_config_save(1), OK)
        page = self.page(0)
        self.assertIn(extras, page[:struct.unpack_from('<I', page, 8)[0] - 4])
        self.assertEqual(self.lib.drms_user_config_commit_baseline(10000.0, 1, 0), OK)
        page = self.page(1)
        self.assertIn(extras, page[:struct.unpack_from('<I', page, 8)[0] - 4])

    def test_export_running_snapshot_matches_committed_bytes(self):
        body = build_body(intervals=[(7, 1, True, 0.5, 1.5, 0.0, 'test')],
                          params=(4000, 1000, 200000, 50000, 32000))
        self.assertEqual(self.lib.drms_user_config_apply(body, len(body), 0), OK)
        self.assertEqual(self.lib.drms_user_config_commit_baseline(10000.0, 1, 0), OK)
        output = ctypes.create_string_buffer(4096)
        self.lib.drms_user_config_export.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        self.lib.drms_user_config_export.restype = ctypes.c_uint32
        size = self.lib.drms_user_config_export(output, len(output))
        self.assertGreater(size, 0)
        self.assertEqual(output.raw[:size], self.page(0)[:size])
        self.assertEqual(self.lib.drms_user_config_export(output, 16), 0)

    def test_flash_transaction_stack_fits_application_thread(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'config.o'
            source = ROOT / 'firmware/DE-DRMS-Code/Core'
            subprocess.run(['cc', '-O0', '-fstack-usage', '-I', str(source / 'Inc'),
                            '-c', str(source / 'Src/drms_user_config.c'), '-o', str(output)], check=True)
            usage = output.with_suffix('.su').read_text()
            for name in ('validate_encoded', 'drms_user_config_load',
                         'drms_user_config_save', 'drms_user_config_commit_baseline'):
                match = re.search(r'\b' + name + r'\s+(\d+)\s+', usage)
                self.assertIsNotNone(match, name)
                self.assertLess(int(match.group(1)), 512, name)

    def test_golden_vector_encoding_is_stable(self):
        # 经 commit_baseline 生成一页并核对编码结构（黄金字节向量）
        self.assertEqual(self.lib.drms_user_config_commit_baseline(100000.0, 0, 3), OK)
        page = self.page(0)
        self.assertEqual(page[:7], b'DRMSUC0')
        self.assertEqual(page[7:8], b'1')
        body_len = struct.unpack_from('<I', page, 8)[0]
        self.assertLessEqual(body_len, 4096)
        self.assertEqual(page[7 + 1:8], b'')  # 防御：长度字段起于 8
        self.assertEqual(struct.unpack_from('<Q', page, 12)[0], 1)  # config_version
        self.assertEqual(struct.unpack_from('<Q', page, 20)[0], 3)  # calibration_version
        self.assertEqual(page[28], 1)  # r0_valid
        self.assertEqual(struct.unpack_from('<d', page, 32)[0], 100000.0)
        crc = struct.unpack_from('<I', page, body_len - 4)[0]
        self.assertEqual(crc, crc32(page[:body_len - 4]))
        # 提交四字在页尾
        commit = page[PAGE - 16:PAGE - 16 + 16]
        self.assertEqual(commit[:4], b'UCMT')
        self.assertEqual(struct.unpack_from('<I', commit, 4)[0], body_len)
        self.assertEqual(struct.unpack_from('<I', commit, 8)[0], crc)

    def test_interval_validation_rules(self):
        base = dict(r0_valid=0, r0=0.0)
        good = [(1, 2, False, 0.0, 0.1, 0.01, 'ok')]
        self.assertEqual(self.lib.drms_user_config_apply(build_body(intervals=good), len(build_body(intervals=good)), 0), OK)
        bad_cases = [
            ('零宽', [(1, 1, 0, 0.1, 0.1, 0.0, '')]),
            ('倒序', [(1, 1, 0, 0.2, 0.1, 0.0, '')]),
            ('重叠', [(1, 1, 0, 0.0, 0.2, 0.0, ''), (2, 1, 0, 0.1, 0.3, 0.0, '')]),
            ('乱序', [(1, 1, 0, 0.2, 0.3, 0.0, ''), (2, 1, 0, 0.0, 0.1, 0.0, '')]),
            ('NaN下界', [(1, 1, 0, float('nan'), 0.1, 0.0, '')]),
            ('Inf上界', [(1, 1, 0, 0.0, float('inf'), 0.0, '')]),
            ('回差过半', [(1, 1, 0, 0.0, 0.1, 0.06, '')]),
            ('负回差', [(1, 1, 0, 0.0, 0.1, -0.01, '')]),
            ('超17项', [(i + 1, 1, 0, i * 0.1, i * 0.1 + 0.05, 0.001, '') for i in range(17)]),
            ('名称超长', [(1, 1, 0, 0.0, 0.1, 0.0, 'x' * 49)]),
            ('非法UTF8', [(1, 1, 0, 0.0, 0.1, 0.0, b'\xff\xfe')]),
            ('截断UTF8', [(1, 1, 0, 0.0, 0.1, 0.0, b'\xe4\xb8')]),
            ('代理码UTF8', [(1, 1, 0, 0.0, 0.1, 0.0, b'\xed\xa0\x80')]),
            ('超出Unicode', [(1, 1, 0, 0.0, 0.1, 0.0, b'\xf4\x90\x80\x80')]),
            ('名称含NUL', [(1, 1, 0, 0.0, 0.1, 0.0, b'a\x00b')]),
            ('重复编号', [(1, 1, 0, 0.0, 0.1, 0.0, ''), (1, 2, 0, 0.1, 0.2, 0.0, '')]),
            ('非法等级', [(1, 4, 0, 0.0, 0.1, 0.0, '')]),
            ('非末项闭合', [(1, 1, 1, 0.0, 0.1, 0.0, ''), (2, 1, 0, 0.1, 0.2, 0.0, '')]),
            ('回差吞掉空隙', [(1, 1, 0, 0.0, 1.0, 0.2, ''), (2, 1, 0, 1.3, 2.0, 0.2, '')]),
        ]
        for name, intervals in bad_cases:
            with self.subTest(name):
                self.setUp()
                self.assertEqual(self.lib.drms_user_config_apply(build_body(intervals=intervals), len(build_body(intervals=intervals)), 0),
                                 INVALID)
        # 16 项合法；空表合法（UNCONFIGURED 语义由算法层处理）
        self.setUp()
        ok16 = [(i + 1, 1, 0, i * 0.1, i * 0.1 + 0.05, 0.001, '区间') for i in range(16)]
        self.assertEqual(self.lib.drms_user_config_apply(build_body(intervals=ok16), len(build_body(intervals=ok16)), 0), OK)
        self.setUp()
        self.assertEqual(self.lib.drms_user_config_apply(build_body(intervals=()), len(build_body(intervals=())), 0), OK)
        count = ctypes.c_uint16(0)
        self.assertEqual(self.lib.drms_user_config_get_intervals(ctypes.byref(count), None, None,
                                                                 None, None, None), 0)

    def test_apply_version_and_atomic_validation(self):
        body = build_body(1)
        self.assertEqual(self.lib.drms_user_config_apply(body, len(body), 5), STALE)
        self.assertEqual(self.lib.drms_user_config_apply(body, len(body), 0), OK)
        self.assertEqual(self.lib.drms_user_config_run_version(), 1)

    def test_apply_publishes_one_running_snapshot_before_save(self):
        body = with_baseline_policy(build_body(params=(8000, 0, 0, 0, 16000)), 100, 50000, 0.01)
        self.assertEqual(self.lib.drms_user_config_apply(body, len(body), 0), OK)
        self.assertEqual(self.lib.drms_user_config_dirty(), 1)
        output = ctypes.create_string_buffer(4096)
        length = self.lib.drms_user_config_export(output, len(output))
        self.assertGreater(length, 0)
        data = output.raw[:length]
        self.assertEqual(struct.unpack_from('<Q', data, 12)[0], 1)
        self.assertEqual(struct.unpack_from('<I', data, 44)[0], 8000)
        policy = BaselinePolicy()
        self.assertEqual(self.lib.drms_user_config_get_baseline_policy(ctypes.byref(policy)), 1)
        self.assertEqual((policy.min_count, policy.min_duration_us), (100, 50000))
        self.assertEqual(self.lib.drms_user_config_persisted_version(), 0)
        # CRC 破坏 → 整包拒绝
        broken = bytearray(body)
        broken[-1] ^= 1
        self.assertEqual(self.lib.drms_user_config_apply(bytes(broken), len(broken), 1), INVALID)
        # 运行版本未变（拒绝后不生效）
        self.assertEqual(self.lib.drms_user_config_run_version(), 1)

    def test_duplicate_singleton_tlv_is_rejected_atomically(self):
        body = bytearray(build_body()[:-4])
        body += struct.pack('<HHIQQQQ', 2, 36, 8000, 0, 0, 0, 16000)
        struct.pack_into('<I', body, 8, len(body) + 4)
        encoded = bytes(body) + struct.pack('<I', crc32(body))
        self.assertEqual(self.lib.drms_user_config_apply(encoded, len(encoded), 0), INVALID)
        self.assertEqual(self.lib.drms_user_config_run_version(), 0)

    def test_rejects_unsupported_rate_and_too_short_freshness(self):
        for params in ((12345, 0, 0, 0, 100000), (8000, 0, 0, 0, 15999),
                       (4000, 0, 0, 0, 31999), (128000, 0, 0, 0, 9999)):
            body = build_body(params=params)
            self.assertEqual(self.lib.drms_user_config_apply(body, len(body), 0), INVALID, params)
            self.assertEqual(self.lib.drms_user_config_run_version(), 0)
        for params in ((8000, 0, 0, 0, 16000), (4000, 0, 0, 0, 32000),
                       (128000, 0, 0, 0, 10000)):
            self.setUp()
            body = build_body(params=params)
            self.assertEqual(self.lib.drms_user_config_apply(body, len(body), 0), OK, params)

    def test_save_and_no_change(self):
        self.assertEqual(self.lib.drms_user_config_save(0), NO_CHANGE)  # 无脏数据
        self.assertEqual(self.lib.drms_user_config_apply(build_body(1), len(build_body(1)), 0), OK)
        self.assertEqual(self.lib.drms_user_config_dirty(), 1)
        self.assertEqual(self.lib.drms_user_config_save(1), OK)
        self.assertEqual(self.lib.drms_user_config_dirty(), 0)
        self.assertEqual(self.lib.drms_user_config_persisted_version(), 1)
        # 同值保存不擦写：program 调用数不增
        before = ctypes.c_int.in_dll(self.lib, 'program_calls').value
        self.assertEqual(self.lib.drms_user_config_save(1), NO_CHANGE)
        self.assertEqual(ctypes.c_int.in_dll(self.lib, 'program_calls').value, before)

    def test_power_cut_at_every_step_recovers_old_or_new(self):
        # 一次 apply+save 共约：erase(1) + programs(body/16) + verify读 + commit + verify
        self.assertEqual(self.lib.drms_user_config_apply(build_body(1), len(build_body(1)), 0), OK)
        # 逐个注入点：begin 失败 / erase 失败 / 每个 program 失败 / commit 前 / commit 后
        for step in range(1, 40):
            self.setUp()
            self.assertEqual(self.lib.drms_user_config_apply(build_body(1, 0, 1, 100000.0), len(build_body(1, 0, 1, 100000.0)), 0), OK)
            self.set_fail(step)
            result = self.lib.drms_user_config_save(1)
            self.assertIn(result, (OK, IO_ERROR))
            # 重启恢复（保留 flash）：load 后必须得到完整旧（空）或完整新快照
            self.reboot()
            persisted = self.lib.drms_user_config_persisted_version()
            self.assertIn(persisted, (0, 1), step)
            if persisted == 1:
                self.assertEqual(self.lib.drms_user_config_r0_valid(), 1)
                self.assertEqual(self.lib.drms_user_config_r0(), 100000.0)
            else:
                self.assertEqual(self.lib.drms_user_config_r0_valid(), 0)

    def test_commit_baseline_atomic_and_failure_keeps_old_r0(self):
        self.assertEqual(self.lib.drms_user_config_apply(build_body(1), len(build_body(1)), 0), OK)
        self.assertEqual(self.lib.drms_user_config_commit_baseline(100000.0, 1, 7), OK)
        self.assertEqual(self.lib.drms_user_config_r0_valid(), 1)
        self.assertEqual(self.lib.drms_user_config_r0_calibration_version(), 7)
        self.assertEqual(self.lib.drms_user_config_run_version(), 2)
        self.assertEqual(self.lib.drms_user_config_dirty(), 0)
        # 提交失败：旧 R0 保留、版本不升、未保存状态保留
        self.assertEqual(self.lib.drms_user_config_apply(build_body(2), len(build_body(2)), 2), OK)
        self.set_fail(1)  # begin 失败
        self.assertEqual(self.lib.drms_user_config_commit_baseline(200000.0, 3, 7), IO_ERROR)
        self.assertEqual(self.lib.drms_user_config_r0(), 100000.0)
        self.assertEqual(self.lib.drms_user_config_run_version(), 3)  # 失败不升版本
        self.assertEqual(self.lib.drms_user_config_r0_valid(), 1)
        # 非法 R0
        self.assertEqual(self.lib.drms_user_config_commit_baseline(float('nan'), 3, 7), INVALID)
        self.assertEqual(self.lib.drms_user_config_commit_baseline(0.0, 3, 7), INVALID)

    def test_applied_rate_change_invalidates_prior_baseline_before_save(self):
        self.assertEqual(self.lib.drms_user_config_apply(build_body(), len(build_body()), 0), OK)
        self.assertEqual(self.lib.drms_user_config_commit_baseline(100000.0, 1, 0), OK)
        changed = build_body(params=(8000, 0, 0, 0, 16000))
        self.assertEqual(self.lib.drms_user_config_apply(changed, len(changed), 2), OK)
        self.assertEqual(self.lib.drms_user_config_r0_valid(), 0)
        self.assertEqual(self.lib.drms_user_config_r0(), 100000.0)
        self.assertEqual(self.lib.drms_user_config_dirty(), 1)

    def test_calibration_generation_change_invalidates_r0_on_load(self):
        self.assertEqual(self.lib.drms_user_config_commit_baseline(100000.0, 0, 7), OK)
        # 模拟重启 + 校准代次已推进
        self.reboot(8)
        self.assertEqual(self.lib.drms_user_config_persisted_version(), 1)
        self.assertEqual(self.lib.drms_user_config_r0_valid(), 0)  # 依赖不匹配 → 失效
        self.assertEqual(self.lib.drms_user_config_r0(), 100000.0)  # 旧值保留可诊断
        # 同代次重启：R0 有效
        self.reboot(7)
        self.assertEqual(self.lib.drms_user_config_r0_valid(), 1)

    def test_future_schema_page_is_preserved_and_refuses_overwrite(self):
        # 构造未来 schema 页（版本字节 '9'，结构合法）
        body = bytearray(build_body(1))
        body[7] = ord('9')
        # 重算 CRC 使结构有效
        body[8:12] = struct.pack('<I', len(body))
        body[-4:] = struct.pack('<I', crc32(bytes(body[:-4])))
        self.lib.fake_reset()
        # 直接把页写入 fake flash（模拟出厂带未来 schema）
        self.lib.fake_page.restype = ctypes.c_void_p
        dst = self.page_ptr(0)
        ctypes.memmove(dst, bytes(body), len(body))
        # 提交标志
        commit = b'UCMT' + struct.pack('<II', len(body), crc32(bytes(body[:len(body) - 4]))) + b'\xff' * 4
        ctypes.memmove(dst + PAGE - 16, commit, 16)
        self.lib.drms_user_config_load()
        self.assertEqual(self.lib.drms_user_config_unsupported_schema(), 1)
        self.assertEqual(self.lib.drms_user_config_apply(build_body(1), 84, 0), UNSUPPORTED)
        self.assertEqual(self.lib.drms_user_config_save(0), UNSUPPORTED)
        self.assertEqual(self.lib.drms_user_config_commit_baseline(1.0, 0, 0), UNSUPPORTED)
        # 未来页未被擦除
        self.assertEqual(self.page(0)[7:8], b'9')

    def test_torn_commit_falls_back_to_other_page(self):
        # 页 A 有效提交；页 B 写了一半（无提交标志）→ 载入取 A
        self.assertEqual(self.lib.drms_user_config_commit_baseline(100000.0, 0, 5), OK)
        self.assertEqual(self.lib.drms_user_config_apply(build_body(2), len(build_body(2)), 1), OK)
        self.set_fail(2)  # erase B 后第一步 program 失败 → B 只有 0xFF
        self.assertEqual(self.lib.drms_user_config_save(2), IO_ERROR)
        self.reboot()
        self.assertEqual(self.lib.drms_user_config_persisted_version(), 1)
        self.assertEqual(self.lib.drms_user_config_r0(), 100000.0)
        # 下一次保存应写 B（A 保持为旧有效副本直至新页提交成功）
        self.assertEqual(self.lib.drms_user_config_apply(build_body(3), len(build_body(3)), 1), OK)  # 载入后 v=1
        self.assertEqual(self.lib.drms_user_config_save(2), OK)
        self.reboot()
        self.assertEqual(self.lib.drms_user_config_persisted_version(), 2)

    def test_semantically_corrupt_newer_page_falls_back_to_valid_older_page(self):
        self.assertEqual(self.lib.drms_user_config_commit_baseline(100000.0, 0, 0), OK)
        broken = build_body(version=2, intervals=[(1, 7, False, 0.0, 1.0, 0.0, '')])
        ptr = self.page_ptr(1)
        ctypes.memmove(ptr, broken, len(broken))
        commit = b'UCMT' + struct.pack('<II', len(broken), crc32(broken[:-4])) + b'\xff' * 4
        ctypes.memmove(ptr + PAGE - 16, commit, 16)
        self.reboot()
        self.assertEqual(self.lib.drms_user_config_persisted_version(), 1)
        self.assertEqual(self.lib.drms_user_config_r0(), 100000.0)


if __name__ == '__main__':
    unittest.main()
