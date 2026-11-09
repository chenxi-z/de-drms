"""资源生命周期测试：注入时钟与可控后端驱动真实 drms_resource_lifecycle.c，
另用真实 drms_acquisition.c 验证采集后端的取消/迟到回调/恢复行为。"""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
from test_acquisition import Raw, HEADER as ACQ_HEADER, MOCK as ACQ_MOCK

OK, ACCEPTED, BUSY, INVALID, STALE = 0, 1, 2, 3, 4
NO_CHANGE, IO_ERROR, TIMEOUT, CANCELLED, INCOMPLETE = 5, 6, 7, 8, 9
QUARANTINED, UNSUPPORTED, EMPTY = 10, 11, 12

ACQ, RS, TF, FLASH, UPDATE = 1, 2, 4, 8, 16

IDLE, ACTIVE, CANCELLING, QUIESC, QUARANT = 0, 1, 2, 3, 4


class Token(ctypes.Structure):
    _fields_ = [('operation_id', ctypes.c_uint64), ('generation', ctypes.c_uint32)]


class Snapshot(ctypes.Structure):
    _fields_ = [('snapshot_sequence', ctypes.c_uint32),
                ('state', ctypes.c_uint8 * 5), ('token', Token * 5),
                ('deadline_ms', ctypes.c_uint64 * 5),
                ('abort_attempts', ctypes.c_uint32 * 5),
                ('recover_attempts', ctypes.c_uint32 * 5),
                ('quarantined_events', ctypes.c_uint64), ('timeouts', ctypes.c_uint64)]


class FakeBackend:
    """可控后端：可编程 abort/probe/recover 结果并记录调用序列。"""
    CODE = r'''
#include "drms_resource_lifecycle.h"
int abort_result, probe_result, recover_result;
int abort_calls, probe_calls, recover_calls, release_marker;
DRMS_Result fake_abort(void) { ++abort_calls; return (DRMS_Result)abort_result; }
DRMS_Result fake_probe(void) { ++probe_calls; return (DRMS_Result)probe_result; }
DRMS_Result fake_recover(void) { ++recover_calls; return (DRMS_Result)recover_result; }
'''


class LifecycleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        p = Path(cls.tmp.name)
        (p / 'main.h').write_text(ACQ_HEADER)
        (p / 'backend.c').write_text(FakeBackend.CODE)
        src = ROOT / 'firmware/DE-DRMS-Code/Core'
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Werror=implicit-function-declaration',
                        '-I', str(p), '-I', str(src / 'Inc'),
                        str(src / 'Src/drms_resource_lifecycle.c'), str(p / 'backend.c'),
                        '-o', str(p / 'rlc.so')], check=True)
        cls.lib = ctypes.CDLL(str(p / 'rlc.so'))
        # 后端函数指针：取 fake_* 地址
        cls.abort_ptr = ctypes.cast(cls.lib.fake_abort, ctypes.c_void_p)
        cls.probe_ptr = ctypes.cast(cls.lib.fake_probe, ctypes.c_void_p)
        cls.recover_ptr = ctypes.cast(cls.lib.fake_recover, ctypes.c_void_p)
        cls.Backend = type('Backend', (ctypes.Structure,), {
            '_fields_': [('abort', ctypes.c_void_p), ('probe', ctypes.c_void_p),
                         ('recover', ctypes.c_void_p)]})
        cls.lib.drms_resource_activate.argtypes = [ctypes.c_uint32, Token]
        cls.lib.drms_resource_cancel.argtypes = [ctypes.c_uint32, Token, ctypes.c_uint64]
        cls.lib.drms_resource_quiescent.argtypes = [ctypes.c_uint32, Token]
        cls.lib.drms_resource_release.argtypes = [ctypes.c_uint32, Token]
        cls.lib.drms_resource_recover.argtypes = [ctypes.c_uint32, ctypes.c_uint64]
        cls.lib.drms_resource_configure.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
        cls.lib.drms_resource_tick.argtypes = [ctypes.c_uint64]
        cls.lib.drms_resource_get_snapshot.argtypes = [ctypes.POINTER(Snapshot)]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def install(self, abort=BUSY, probe=BUSY, recover=ACCEPTED):
        ctypes.c_int.in_dll(self.lib, 'abort_result').value = abort
        ctypes.c_int.in_dll(self.lib, 'probe_result').value = probe
        ctypes.c_int.in_dll(self.lib, 'recover_result').value = recover
        backend = self.Backend(self.abort_ptr.value, self.probe_ptr.value, self.recover_ptr.value)
        backends = (self.Backend * 5)(backend, backend, backend, backend, backend)
        self.lib.drms_resource_init(ctypes.cast(backends, ctypes.POINTER(self.Backend)))
        self.lib.drms_resource_configure(ACQ, 100)
        self.lib.drms_resource_configure(RS, 100)
        self.lib.drms_resource_configure(TF, 100)
        self.lib.drms_resource_configure(FLASH, 100)
        self.lib.drms_resource_configure(UPDATE, 100)
        for name in ('abort_calls', 'probe_calls', 'recover_calls'):
            ctypes.c_int.in_dll(self.lib, name).value = 0

    def setUp(self):
        self.install()
        self.token = Token(501, 1)

    def snapshot(self):
        snap = Snapshot()
        self.lib.drms_resource_get_snapshot(ctypes.byref(snap))
        return snap

    def state(self, resource):
        return self.snapshot().state[resource.bit_length() - 1]

    def calls(self, name):
        return ctypes.c_int.in_dll(self.lib, name).value

    def test_active_to_cancelling_to_quiescent(self):
        self.assertEqual(self.lib.drms_resource_activate(ACQ, self.token), ACCEPTED)
        self.assertEqual(self.state(ACQ), ACTIVE)
        # 取消：进入 CANCELLING 并立即做一次有界中止尝试
        self.assertEqual(self.lib.drms_resource_cancel(ACQ, self.token, 0), ACCEPTED)
        self.assertEqual(self.state(ACQ), CANCELLING)
        self.assertEqual(self.calls('abort_calls'), 1)
        # 注入时钟推进 + probe 变为静止 → QUIESCENT
        ctypes.c_int.in_dll(self.lib, 'probe_result').value = ACCEPTED
        self.lib.drms_resource_tick(50)
        self.assertEqual(self.state(ACQ), QUIESC)
        # 所有者确认与归还
        self.assertEqual(self.lib.drms_resource_quiescent(ACQ, self.token), OK)
        self.assertEqual(self.lib.drms_resource_release(ACQ, self.token), OK)
        self.assertEqual(self.state(ACQ), IDLE)
        self.assertEqual(self.snapshot().quarantined_events, 0)

    def test_cancel_with_immediate_quiescence_evidence(self):
        self.assertEqual(self.lib.drms_resource_activate(ACQ, self.token), ACCEPTED)
        ctypes.c_int.in_dll(self.lib, 'abort_result').value = ACCEPTED  # 中止时即确认静止
        self.assertEqual(self.lib.drms_resource_cancel(ACQ, self.token, 0), ACCEPTED)
        self.assertEqual(self.state(ACQ), QUIESC)
        self.assertEqual(self.lib.drms_resource_release(ACQ, self.token), OK)

    def test_timeout_one_attempt_then_quarantined(self):
        self.assertEqual(self.lib.drms_resource_activate(ACQ, self.token), ACCEPTED)
        self.assertEqual(self.lib.drms_resource_cancel(ACQ, self.token, 0), ACCEPTED)
        self.assertEqual(self.state(ACQ), CANCELLING)
        # 期限内 probe 未静止：保持占用
        self.lib.drms_resource_tick(99)
        self.assertEqual(self.state(ACQ), CANCELLING)
        # 到期：一次中止/恢复尝试，仍无法确认 → QUARANTINED
        self.assertEqual(self.lib.drms_resource_cancel(ACQ, self.token, 100), NO_CHANGE)
        self.lib.drms_resource_tick(100)
        self.assertEqual(self.state(ACQ), QUARANT)
        self.assertEqual(self.snapshot().quarantined_events, 1)
        self.assertEqual(self.calls('abort_calls'), 2)  # 取消时 1 次 + 到期 1 次
        # 隔离拒绝新请求，底层缓冲仍占用（不假释放）
        other = Token(502, 1)
        self.assertEqual(self.lib.drms_resource_activate(ACQ, other), BUSY)
        self.assertEqual(self.lib.drms_resource_quiescent(ACQ, other), STALE)
        self.assertEqual(self.lib.drms_resource_release(ACQ, self.token), STALE)

    def test_recover_success_then_reuse(self):
        self.assertEqual(self.lib.drms_resource_activate(ACQ, self.token), ACCEPTED)
        self.assertEqual(self.lib.drms_resource_cancel(ACQ, self.token, 0), ACCEPTED)
        self.lib.drms_resource_tick(100)  # 超时 → QUARANTINED
        self.assertEqual(self.state(ACQ), QUARANT)
        self.assertEqual(self.lib.drms_resource_recover(ACQ, 200), OK)  # 同步完成
        self.assertEqual(self.state(ACQ), IDLE)
        self.assertEqual(self.calls('recover_calls'), 1)
        other = Token(503, 1)
        self.assertEqual(self.lib.drms_resource_activate(ACQ, other), ACCEPTED)

    def test_recover_failure_does_not_loop(self):
        self.assertEqual(self.lib.drms_resource_activate(ACQ, self.token), ACCEPTED)
        self.assertEqual(self.lib.drms_resource_cancel(ACQ, self.token, 0), ACCEPTED)
        self.lib.drms_resource_tick(100)
        self.assertEqual(self.state(ACQ), QUARANT)
        ctypes.c_int.in_dll(self.lib, 'recover_result').value = IO_ERROR
        self.assertEqual(self.lib.drms_resource_recover(ACQ, 200), IO_ERROR)
        self.assertEqual(self.state(ACQ), QUARANT)
        # tick 不自动重试恢复；再次显式 recover 也只加一次
        self.lib.drms_resource_tick(300)
        self.lib.drms_resource_tick(600)
        self.assertEqual(self.calls('recover_calls'), 1)
        self.assertEqual(self.state(ACQ), QUARANT)
        self.assertEqual(self.lib.drms_resource_recover(ACQ, 700), IO_ERROR)
        self.assertEqual(self.calls('recover_calls'), 2)

    def test_stale_token_and_duplicate_cancel(self):
        self.assertEqual(self.lib.drms_resource_activate(ACQ, self.token), ACCEPTED)
        stale = Token(self.token.operation_id + 1, self.token.generation)
        self.assertEqual(self.lib.drms_resource_cancel(ACQ, stale, 0), STALE)
        self.assertEqual(self.state(ACQ), ACTIVE)
        self.assertEqual(self.lib.drms_resource_cancel(ACQ, self.token, 0), ACCEPTED)
        # 重复取消幂等
        self.assertEqual(self.lib.drms_resource_cancel(ACQ, self.token, 10), NO_CHANGE)
        self.assertEqual(self.state(ACQ), CANCELLING)
        # 旧代次确认/归还仅清理语义
        self.assertEqual(self.lib.drms_resource_quiescent(ACQ, stale), STALE)
        self.assertEqual(self.state(ACQ), CANCELLING)

    def test_quiescent_on_active_is_clean_completion(self):
        self.assertEqual(self.lib.drms_resource_activate(RS, self.token), ACCEPTED)
        self.assertEqual(self.lib.drms_resource_quiescent(RS, self.token), OK)
        self.assertEqual(self.state(RS), QUIESC)
        self.assertEqual(self.lib.drms_resource_release(RS, self.token), OK)

    def test_multi_bit_activate_all_or_nothing(self):
        # TF 已占：ACQ|TF 组合申请必须整体失败且不占用 ACQ
        token_tf = Token(600, 1)
        self.assertEqual(self.lib.drms_resource_activate(TF, token_tf), ACCEPTED)
        self.assertEqual(self.lib.drms_resource_activate(ACQ | TF, self.token), BUSY)
        self.assertEqual(self.state(ACQ), IDLE)
        self.assertEqual(self.state(TF), ACTIVE)

    def test_safety_stop_inhibits_first_before_file_finalize(self):
        # 安全停止：采集后端在 cancel() 内立即执行抑制动作；存储收尾可滞后
        self.install(abort=BUSY, probe=BUSY)
        token_a, token_s = Token(700, 1), Token(701, 1)
        self.assertEqual(self.lib.drms_resource_activate(ACQ, token_a), ACCEPTED)
        self.assertEqual(self.lib.drms_resource_activate(TF, token_s), ACCEPTED)
        ctypes.c_int.in_dll(self.lib, 'abort_result').value = ACCEPTED  # 采集后端可立即抑制
        self.assertEqual(self.lib.drms_resource_cancel(ACQ, token_a, 0), ACCEPTED)
        self.assertEqual(self.state(ACQ), QUIESC)   # 抑制完成，不等文件
        self.assertEqual(self.state(TF), ACTIVE)    # 文件收尾仍在进行
        ctypes.c_int.in_dll(self.lib, 'abort_result').value = BUSY  # 存储收尾无法立即确认
        self.assertEqual(self.lib.drms_resource_cancel(TF, token_s, 0), ACCEPTED)
        # 关机总期限到达仍无法确认静止：不得虚报已保存
        self.lib.drms_resource_tick(100)
        self.assertEqual(self.state(TF), QUARANT)
        snap = self.snapshot()
        self.assertNotEqual(snap.state[2], QUIESC)  # 存储未确认静止 → 不能报告保存完成

    def test_missing_backend_rejects_cancel(self):
        backend = self.Backend(self.abort_ptr.value, self.probe_ptr.value, self.recover_ptr.value)
        none_backend = self.Backend(0, 0, 0)  # 全空钩子 = 该资源不支持取消
        backends = (self.Backend * 5)(backend, none_backend, backend, backend, backend)
        self.lib.drms_resource_init(ctypes.cast(backends, ctypes.POINTER(self.Backend)))
        self.lib.drms_resource_configure(RS, 100)
        self.assertEqual(self.lib.drms_resource_activate(RS, self.token), ACCEPTED)
        self.assertEqual(self.lib.drms_resource_cancel(RS, self.token, 0), UNSUPPORTED)
        self.assertEqual(self.state(RS), ACTIVE)


class AcquisitionBackendTest(unittest.TestCase):
    """真实采集后端：取消=有界中止+激励抑制；迟到回调不得复用旧缓冲。"""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        p = Path(cls.tmp.name)
        (p / 'main.h').write_text(ACQ_HEADER)
        (p / 'spi.h').write_text('#include "main.h"')
        (p / 'mock.c').write_text(
            ACQ_MOCK.replace("int HAL_SPI_Abort(SPI_HandleTypeDef *s) { return 0; }",
                             "int abort_ok_result=0;\nint abort_ok(void) { return abort_ok_result; }\n"
                             "unsigned int abort_calls;\n"
                             "int HAL_SPI_Abort(SPI_HandleTypeDef *s) { ++abort_calls;return abort_ok(); }"))
        src = ROOT / 'firmware/DE-DRMS-Code/Core'
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Werror=implicit-function-declaration',
                        '-I', str(p), '-I', str(src / 'Inc'),
                        *[str(src / f'Src/drms_{name}.c') for name in ('acquisition', 'measurement', 'fifo', 'capture_time')],
                        str(p / 'mock.c'), '-o', str(p / 'acq.so')], check=True)
        cls.lib = ctypes.CDLL(str(p / 'acq.so'))
        cls.lib.drms_acq_start.restype = ctypes.c_int
        cls.lib.drms_acq_resource_backend.restype = ctypes.c_void_p
        cls.lib.abort_ok_result = ctypes.c_int.in_dll(cls.lib, 'abort_ok_result')

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        lib = self.lib
        lib.abort_ok_result.value = 0
        lib.drms_acq_stop()
        self.assertEqual(lib.drms_acq_start(4000, 0), 1)
        self.gen0 = lib.drms_acq_generation()  # 类内多测试共享 lib：代次单调

    def backend(self):
        addr = self.lib.drms_acq_resource_backend()
        return ctypes.cast(addr, ctypes.POINTER(ctypes.c_void_p))

    def u32(self, name):
        return ctypes.c_uint32.in_dll(self.lib, name)

    def test_abort_inhibits_excitation_and_confirms_quiescence(self):
        be = self.backend()
        abort = ctypes.CFUNCTYPE(ctypes.c_int)(be[0])
        probe = ctypes.CFUNCTYPE(ctypes.c_int)(be[1])
        self.assertEqual(probe(), BUSY)  # running → 未静止
        # 在途 DMA：DRDY 已发出未完成
        self.lib.drms_acq_drdy()
        self.assertEqual(abort(), ACCEPTED)
        self.assertEqual(self.lib.pin(5), 1)  # CURR_DIS 抑制先于一切收尾
        self.assertEqual(self.u32('drms_acq_running').value, 0)
        self.assertEqual(probe(), ACCEPTED)

    def test_late_dma_callback_after_abort_cannot_push_old_buffer(self):
        be = self.backend()
        abort = ctypes.CFUNCTYPE(ctypes.c_int)(be[0])
        self.lib.drms_acq_drdy()          # DMA 在途
        self.assertEqual(abort(), ACCEPTED)  # 中止
        before = self.u32('drms_acq_raw_ticket_next').value
        self.lib.complete_frame(280000, 4200000)  # 迟到完成回调
        self.assertEqual(self.u32('drms_acq_raw_ticket_next').value, before)  # 未发布
        self.assertEqual(self.u32('drms_acq_edges').value, 1)  # DRDY 已占号
        self.assertEqual(self.u32('drms_acq_error').value, 0)

    def test_recover_clears_error_for_next_start(self):
        be = self.backend()
        abort = ctypes.CFUNCTYPE(ctypes.c_int)(be[0])
        recover = ctypes.CFUNCTYPE(ctypes.c_int)(be[2])
        self.lib.drms_acq_drdy()
        self.assertEqual(abort(), ACCEPTED)
        self.u32('drms_acq_error').value = 4
        self.assertEqual(recover(), ACCEPTED)
        self.assertEqual(self.u32('drms_acq_error').value, 0)
        # 恢复后可重新启动（新代次 = setUp 代次 + 1）
        self.assertEqual(self.lib.drms_acq_start(4000, 0), 1)
        self.assertEqual(self.lib.drms_acq_generation(), self.gen0 + 1)


if __name__ == '__main__':
    unittest.main()
