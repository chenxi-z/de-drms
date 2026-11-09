"""控制裁决器契约测试：编译真实 drms_control.c，验证原子资源租约、代次与完成槽。

接口冻结自 docs/design/2026-11-06-firmware-architecture-plan.md T1 与 C2/C5；
测试在单线程主机环境运行，PRIMASK 临界区退化为普通顺序代码。
"""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

HEADER = r'''
#ifndef MOCK_CONTROL_MAIN_H
#define MOCK_CONTROL_MAIN_H
#include <stdint.h>
#include <stddef.h>
#define __get_PRIMASK() ((uint32_t)0)
#define __disable_irq() ((void)0)
#define __set_PRIMASK(m) ((void)(m))
#endif
'''

MOCK = r'''
#include "drms_control.h"
static DRMS_Result next_result = DRMS_ACCEPTED;
DRMS_Token op_tokens[16];
int dispatch_calls;
static DRMS_Result test_dispatch(const DRMS_Token *token, const DRMS_ControlRequest *request)
{
  ++dispatch_calls;
  if (request->operation < 16)
    op_tokens[request->operation] = *token;
  return next_result;
}
void test_install(void)
{
  next_result = DRMS_ACCEPTED;
  dispatch_calls = 0;
  drms_control_init(test_dispatch);
}
void set_dispatch_result(int result) { next_result = (DRMS_Result)result; }
DRMS_Token token_of(int operation) { return op_tokens[operation]; }
'''

# DRMS_Result 冻结值（drms_architecture_contract.h）
OK, ACCEPTED, BUSY, INVALID, STALE = 0, 1, 2, 3, 4
NO_CHANGE, IO_ERROR, TIMEOUT, CANCELLED, INCOMPLETE = 5, 6, 7, 8, 9
QUARANTINED, UNSUPPORTED, EMPTY = 10, 11, 12

# 资源位（C2）
ACQ, RS, TF, FLASH, UPDATE_EXCL = 1, 2, 4, 8, 16
ALL = ACQ | RS | TF | FLASH | UPDATE_EXCL

# 业务操作（C2 六类集合展开为 8 种）
RECORD, MSC_EXPORT, DOWNLOAD, CONFIG_APPLY, BASELINE_R0, CALIBRATE, CONFIG_SAVE, UPDATE = range(1, 9)
OP_RESOURCES = {
    RECORD: ACQ | RS | TF,
    MSC_EXPORT: TF,
    DOWNLOAD: TF,
    CONFIG_APPLY: ACQ | FLASH,
    BASELINE_R0: ACQ | TF | FLASH,
    CALIBRATE: ACQ | TF | FLASH,
    CONFIG_SAVE: ACQ | TF | FLASH,
    UPDATE: ALL,
}


class Token(ctypes.Structure):
    _fields_ = [('operation_id', ctypes.c_uint64), ('generation', ctypes.c_uint32)]


class Request(ctypes.Structure):
    _fields_ = [('source', ctypes.c_uint32), ('session', ctypes.c_uint32),
                ('request_id', ctypes.c_uint64), ('operation', ctypes.c_int),
                ('value', ctypes.c_uint32), ('number', ctypes.c_double),
                ('payload', ctypes.c_void_p), ('payload_length', ctypes.c_uint32)]


class Completion(ctypes.Structure):
    _fields_ = [('operation_id', ctypes.c_uint64), ('source', ctypes.c_uint32),
                ('session', ctypes.c_uint32), ('request_id', ctypes.c_uint64),
                ('result', ctypes.c_int), ('quiescent_mask', ctypes.c_uint32),
                ('stale', ctypes.c_uint32)]


class Snapshot(ctypes.Structure):
    _fields_ = [('snapshot_sequence', ctypes.c_uint32), ('stopping', ctypes.c_uint32),
                ('generation', ctypes.c_uint32), ('reserved_mask', ctypes.c_uint32),
                ('quarantined_mask', ctypes.c_uint32), ('leases_active', ctypes.c_uint32),
                ('requests_queued', ctypes.c_uint32), ('completion_count', ctypes.c_uint32),
                ('last_completion', Completion),
                ('requests_accepted', ctypes.c_uint64), ('requests_rejected', ctypes.c_uint64),
                ('completions_overflow', ctypes.c_uint64), ('completions_consumed', ctypes.c_uint64)]


class ControlContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        p = Path(cls.tmp.name)
        (p / 'main.h').write_text(HEADER)
        (p / 'mock.c').write_text(MOCK)
        src = ROOT / 'firmware/DE-DRMS-Code/Core'
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Werror=implicit-function-declaration',
                        '-I', str(p), '-I', str(src / 'Inc'),
                        str(src / 'Src/drms_control.c'), str(p / 'mock.c'),
                        '-o', str(p / 'control.so')], check=True)
        cls.lib = ctypes.CDLL(str(p / 'control.so'))
        cls.lib.token_of.restype = Token
        cls.lib.token_of.argtypes = [ctypes.c_int]
        cls.lib.drms_control_reserve.argtypes = [ctypes.c_uint32, ctypes.POINTER(Token)]
        cls.lib.drms_control_complete.argtypes = [Token, ctypes.c_int, ctypes.c_uint32]
        cls.lib.drms_control_submit.argtypes = [ctypes.POINTER(Request)]
        cls.lib.drms_control_collect.argtypes = [ctypes.POINTER(Completion), ctypes.c_uint32]
        cls.lib.drms_control_get_snapshot.argtypes = [ctypes.POINTER(Snapshot)]
        cls.lib.test_install()
        # 头文件自包含：contract.h 只含标准 C 类型，必须能单独编译
        (p / 'selfcheck.c').write_text('#include "drms_architecture_contract.h"\n'
                                       'int probe;\n')
        subprocess.run(['cc', '-fsyntax-only', '-Wall', '-Werror',
                        '-I', str(src / 'Inc'), str(p / 'selfcheck.c')], check=True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.lib.test_install()
        self.lib.set_dispatch_result(ACCEPTED)

    def value(self, name):
        return ctypes.c_int.in_dll(self.lib, name)

    def token_of(self, operation):
        return self.lib.token_of(operation)

    def snapshot(self):
        snap = Snapshot()
        self.lib.drms_control_get_snapshot(ctypes.byref(snap))
        return snap

    def submit(self, operation, request_id=0):
        request = Request(source=3, session=0, request_id=request_id,
                          operation=operation, value=0, number=0.0,
                          payload=None, payload_length=0)
        return self.lib.drms_control_submit(ctypes.byref(request))

    def collect(self, count=8):
        out = (Completion * count)()
        n = self.lib.drms_control_collect(out, count)
        return [out[i] for i in range(n)]

    def submit_and_poll(self, operation, request_id=0):
        result = self.submit(operation, request_id)
        self.assertEqual(result, ACCEPTED)
        self.lib.drms_control_poll(8)
        return self.token_of(operation)

    def test_report_start_keeps_lease_until_release(self):
        token = self.submit_and_poll(RECORD, request_id=42)
        self.lib.drms_control_report.argtypes = [Token, ctypes.c_int]
        self.assertEqual(self.lib.drms_control_report(token, OK), OK)
        self.assertEqual(self.collect()[0].result, OK)
        self.assertEqual(self.snapshot().reserved_mask, ACQ | RS | TF)
        self.assertEqual(self.lib.drms_control_reserve(TF, ctypes.byref(Token())), BUSY)
        self.assertEqual(self.lib.drms_control_report(token, OK), INVALID)
        self.assertEqual(self.lib.drms_control_release(token, ACQ | RS | TF), OK)
        self.assertEqual(self.snapshot().reserved_mask, 0)
        self.assertEqual(self.collect(), [])

    def test_reserve_is_exclusive_and_all_or_nothing(self):
        token = Token()
        self.assertEqual(self.lib.drms_control_reserve(RS | TF, ctypes.byref(token)), ACCEPTED)
        # 已占资源再申请 → BUSY
        self.assertEqual(self.lib.drms_control_reserve(TF, ctypes.byref(Token())), BUSY)
        # 失败申请不得部分占用：同一批申请中未被持有的 ACQ 仍可单独取得
        token_b = Token()
        self.assertEqual(self.lib.drms_control_reserve(ACQ, ctypes.byref(token_b)), ACCEPTED)
        snap = self.snapshot()
        self.assertEqual(snap.reserved_mask, RS | TF | ACQ)
        self.assertEqual(snap.leases_active, 2)
        # 释放后可重新申请同一资源
        self.assertEqual(self.lib.drms_control_complete(token, OK, RS | TF), OK)
        self.assertEqual(self.lib.drms_control_complete(token_b, OK, ACQ), OK)
        self.assertEqual(self.snapshot().reserved_mask, 0)
        self.assertEqual(self.snapshot().leases_active, 0)

    def test_reserve_rejects_invalid_masks(self):
        self.assertEqual(self.lib.drms_control_reserve(0, ctypes.byref(Token())), INVALID)
        self.assertEqual(self.lib.drms_control_reserve(0x20 | TF, ctypes.byref(Token())), INVALID)
        self.assertEqual(self.lib.drms_control_reserve(0x80000000, ctypes.byref(Token())), INVALID)
        snap = self.snapshot()
        self.assertEqual(snap.reserved_mask, 0)
        self.assertEqual(snap.leases_active, 0)

    def test_dispatch_failure_rolls_back_reservation(self):
        self.lib.set_dispatch_result(IO_ERROR)
        self.assertEqual(self.submit(RECORD, request_id=101), ACCEPTED)
        self.lib.drms_control_poll(8)
        completions = self.collect()
        self.assertEqual(len(completions), 1)
        self.assertEqual(completions[0].request_id, 101)
        self.assertEqual(completions[0].result, IO_ERROR)
        # 回滚即整体静止：完成记录携带全部租约资源为已确认静止掩码
        self.assertEqual(completions[0].quiescent_mask, OP_RESOURCES[RECORD])
        # 回滚后资源完全释放，可再次预占
        snap = self.snapshot()
        self.assertEqual(snap.quarantined_mask, 0)
        self.assertEqual(snap.leases_active, 0)
        self.lib.set_dispatch_result(ACCEPTED)
        self.assertEqual(self.lib.drms_control_reserve(TF, ctypes.byref(Token())), ACCEPTED)

    def test_dispatched_work_holds_resources_until_complete(self):
        token = self.submit_and_poll(MSC_EXPORT, request_id=202)
        self.assertNotEqual(token.operation_id, 0)
        # 已投递：不存在超时自动释放（模拟请求方等待超时后放弃）
        self.assertEqual(self.lib.drms_control_reserve(TF, ctypes.byref(Token())), BUSY)
        self.assertEqual(self.snapshot().leases_active, 1)
        # 不匹配 token 的 complete 不释放
        stale = Token(operation_id=token.operation_id + 1000, generation=token.generation)
        self.assertEqual(self.lib.drms_control_complete(stale, OK, TF), INVALID)
        self.assertEqual(self.snapshot().leases_active, 1)
        # 只有匹配 token 的 complete 释放
        self.assertEqual(self.lib.drms_control_complete(token, OK, TF), OK)
        self.assertEqual(self.snapshot().leases_active, 0)
        self.assertEqual(self.lib.drms_control_reserve(TF, ctypes.byref(Token())), ACCEPTED)

    def test_complete_releases_only_quiescent_and_quarantines_rest(self):
        token = Token()
        self.assertEqual(self.lib.drms_control_reserve(OP_RESOURCES[RECORD],
                                                       ctypes.byref(token)), ACCEPTED)
        # 只确认 ACQ|RS 静止：TF 不得归还，进入隔离
        self.assertEqual(self.lib.drms_control_complete(token, INCOMPLETE, ACQ | RS), OK)
        snap = self.snapshot()
        self.assertEqual(snap.quarantined_mask, TF)
        self.assertEqual(snap.reserved_mask & TF, TF)  # 隔离仍占用，阻断新所有者
        self.assertEqual(self.lib.drms_control_reserve(TF, ctypes.byref(Token())), BUSY)
        # 已确认静止的资源可复用
        self.assertEqual(self.lib.drms_control_reserve(ACQ | RS, ctypes.byref(Token())), ACCEPTED)

    def test_stop_cancels_queued_requests_and_is_idempotent(self):
        self.assertEqual(self.submit(RECORD, request_id=301), ACCEPTED)
        self.assertEqual(self.submit(CONFIG_APPLY, request_id=302), ACCEPTED)
        self.lib.drms_control_stop()
        gen_after_stop = self.snapshot().generation
        # 队列中未处理的请求在 stop 时被取消并给出完成记录
        completions = self.collect()
        self.assertEqual([c.result for c in completions], [CANCELLED, CANCELLED])
        self.assertEqual([c.request_id for c in completions], [301, 302])
        # stop 幂等：代次不变
        self.lib.drms_control_stop()
        self.assertEqual(self.snapshot().generation, gen_after_stop)
        # STOPPING 期间拒绝新请求与预占
        self.assertEqual(self.submit(RECORD, request_id=303), CANCELLED)
        self.assertEqual(self.lib.drms_control_reserve(TF, ctypes.byref(Token())), CANCELLED)

    def test_stale_generation_complete_cleans_without_new_business(self):
        token = Token()
        self.assertEqual(self.lib.drms_control_reserve(TF, ctypes.byref(token)), ACCEPTED)
        gen_before = token.generation
        self.lib.drms_control_stop()
        # 旧代次完成只做清理，返回 STALE，不得启动新业务
        self.assertEqual(self.lib.drms_control_complete(token, OK, TF), STALE)
        snap = self.snapshot()
        self.assertEqual(snap.leases_active, 0)
        self.assertEqual(snap.reserved_mask, 0)
        self.assertGreater(snap.generation, gen_before)
        # 停止期间新预占仍被拒绝
        self.assertEqual(self.lib.drms_control_reserve(TF, ctypes.byref(Token())), CANCELLED)
        # 清理完成后可解除停止，且不自动重启任何业务
        self.assertEqual(self.lib.drms_control_resume(), OK)
        self.assertEqual(self.snapshot().stopping, 0)
        self.assertEqual(self.lib.drms_control_reserve(TF, ctypes.byref(Token())), ACCEPTED)

    def test_resume_requires_all_leases_cleaned(self):
        token = Token()
        self.assertEqual(self.lib.drms_control_reserve(TF, ctypes.byref(token)), ACCEPTED)
        self.lib.drms_control_stop()
        self.assertEqual(self.lib.drms_control_resume(), BUSY)
        self.assertEqual(self.snapshot().stopping, 1)
        self.assertEqual(self.lib.drms_control_complete(token, CANCELLED, TF), STALE)
        self.assertEqual(self.lib.drms_control_resume(), OK)

    def test_completion_overflow_still_queryable(self):
        for _ in range(10):
            token = Token()
            self.assertEqual(self.lib.drms_control_reserve(TF, ctypes.byref(token)), ACCEPTED)
            self.assertEqual(self.lib.drms_control_complete(token, OK, TF), OK)
        snap = self.snapshot()
        self.assertEqual(snap.completions_overflow, 2)
        self.assertEqual(snap.completion_count, 8)  # 最近 8 条可查询
        self.assertEqual(snap.last_completion.quiescent_mask, TF)
        # 拥塞仍可排空查询
        drained = self.collect()
        self.assertEqual(len(drained), 8)
        self.assertEqual(self.snapshot().completion_count, 0)

    def test_query_is_read_only(self):
        token = Token()
        self.assertEqual(self.lib.drms_control_reserve(TF, ctypes.byref(token)), ACCEPTED)
        self.assertEqual(self.lib.drms_control_complete(token, OK, TF), OK)
        first = self.snapshot()
        self.assertEqual(first.completion_count, 1)
        second = self.snapshot()
        self.assertEqual(second.completion_count, 1)  # 查询不吞完成结果
        self.assertEqual(second.last_completion.operation_id, first.last_completion.operation_id)
        drained = self.collect()
        self.assertEqual(len(drained), 1)
        self.assertEqual(self.snapshot().completion_count, 0)

    def test_operation_resource_matrix(self):
        ops = [RECORD, MSC_EXPORT, DOWNLOAD, CONFIG_APPLY,
               BASELINE_R0, CALIBRATE, CONFIG_SAVE, UPDATE]
        for first in ops:
            for second in ops:
                self.setUp()  # 每对独立控制上下文
                token_a = self.submit_and_poll(first)
                self.assertNotEqual(token_a.operation_id, 0)
                # 第二个操作按资源集合相交唯一判定
                self.assertEqual(self.submit(second, request_id=second), ACCEPTED)
                self.lib.drms_control_poll(8)
                if OP_RESOURCES[first] & OP_RESOURCES[second]:
                    # 相交 → BUSY 完成记录，无部分占用，dispatch 未被调用
                    completions = self.collect()
                    self.assertEqual(len(completions), 1, (first, second))
                    self.assertEqual(completions[0].result, BUSY, (first, second))
                    self.assertEqual(completions[0].request_id, second)
                    self.assertEqual(self.value('dispatch_calls').value, 1, (first, second))
                    self.assertEqual(self.snapshot().leases_active, 1, (first, second))
                    # 释放 A 后同集合可再次取得
                    self.lib.drms_control_complete(token_a, OK, OP_RESOURCES[first])
                    token_again = Token()
                    self.assertEqual(
                        self.lib.drms_control_reserve(OP_RESOURCES[second],
                                                      ctypes.byref(token_again)),
                        ACCEPTED, (first, second))
                else:
                    # 不相交 → 两租约并存，second 在途（无完成记录）
                    token_b = self.token_of(second)
                    self.assertNotEqual(token_b.operation_id, 0, (first, second))
                    self.assertEqual(self.value('dispatch_calls').value, 2, (first, second))
                    self.assertEqual(self.collect(), [], (first, second))
                    self.assertEqual(self.snapshot().leases_active, 2, (first, second))
                    self.assertEqual(self.snapshot().reserved_mask,
                                     OP_RESOURCES[first] | OP_RESOURCES[second],
                                     (first, second))
                    # B 仍持有其集合；A 释放后 B 的集合仍不可得
                    self.lib.drms_control_complete(token_a, OK, OP_RESOURCES[first])
                    token_again = Token()
                    self.assertEqual(
                        self.lib.drms_control_reserve(OP_RESOURCES[second],
                                                      ctypes.byref(token_again)),
                        BUSY, (first, second))
                    self.assertEqual(self.lib.drms_control_complete(token_b, OK,
                                                                    OP_RESOURCES[second]), OK)
                    self.assertEqual(self.snapshot().reserved_mask, 0, (first, second))

    def test_resources_for_is_the_single_source_of_the_matrix(self):
        # C2 资源集合唯一定义：矩阵测试与实现共用同一函数，防止两处漂移
        self.lib.drms_control_resources_for.restype = ctypes.c_uint32
        self.lib.drms_control_resources_for.argtypes = [ctypes.c_int]
        for op, expected in OP_RESOURCES.items():
            self.assertEqual(self.lib.drms_control_resources_for(op), expected, op)
        self.assertEqual(self.lib.drms_control_resources_for(0), 0)
        self.assertEqual(self.lib.drms_control_resources_for(9), 0)

    def test_update_exclusive_expands_to_all_resources(self):
        token = Token()
        self.assertEqual(self.lib.drms_control_reserve(UPDATE_EXCL, ctypes.byref(token)), ACCEPTED)
        snap = self.snapshot()
        self.assertEqual(snap.reserved_mask, ALL)  # 自动展开为全部资源
        for bit in (ACQ, RS, TF, FLASH, UPDATE_EXCL):
            self.assertEqual(self.lib.drms_control_reserve(bit, ctypes.byref(Token())), BUSY, bit)

    def test_submit_validation(self):
        self.assertEqual(self.lib.drms_control_submit(None), INVALID)
        request = Request(source=3, session=0, request_id=1, operation=0,
                          value=0, number=0.0, payload=None, payload_length=0)
        self.assertEqual(self.lib.drms_control_submit(ctypes.byref(request)), INVALID)
        request.operation = 9
        self.assertEqual(self.lib.drms_control_submit(ctypes.byref(request)), INVALID)
        self.assertEqual(self.snapshot().requests_queued, 0)


if __name__ == '__main__':
    unittest.main()
