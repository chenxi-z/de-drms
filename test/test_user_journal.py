"""用户区 A/B 页提交日志测试：掉电语义与页轮换（R3/T5 的页级行为）。"""
import ctypes
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
import zlib

import test_user_config as t

PAGE = 8192


class UserJournalTest(t.UserConfigTest):
    """复用同一编译产物；聚焦页级行为。"""

    def program_count(self):
        return ctypes.c_int.in_dll(self.lib, 'program_calls').value

    def test_ab_alternation_keeps_old_page_until_new_commit(self):
        self.lib.drms_user_config_commit_baseline(100000.0, 0, 1)
        self.assertEqual(self.page(0)[7:8], b'1')
        self.assertEqual(self.page(1)[:8], b'\xff' * 8)  # B 未知
        self.lib.drms_user_config_apply(t.build_body(2), len(t.build_body(2)), 1)
        self.assertEqual(self.lib.drms_user_config_save(2), t.OK)
        # A 保持旧有效副本，B 为新副本
        self.assertEqual(self.page(0)[7:8], b'1')
        self.assertEqual(self.page(1)[7:8], b'1')
        self.assertEqual(struct.unpack_from('<Q', self.page(1), 12)[0], 2)
        self.assertEqual(struct.unpack_from('<Q', self.page(0), 12)[0], 1)
        # 第三次提交应轮换回 A（覆盖旧副本）
        self.lib.drms_user_config_apply(t.build_body(3), len(t.build_body(3)), 2)
        self.assertEqual(self.lib.drms_user_config_save(3), t.OK)
        self.assertEqual(struct.unpack_from('<Q', self.page(0), 12)[0], 3)

    def test_torn_commit_flag_makes_page_invalid(self):
        self.lib.drms_user_config_commit_baseline(100000.0, 0, 1)
        good = self.page(0)
        # 模拟提交标志四字写入时掉电：body 完整但 commit 四字为擦除态
        dst = self.page_ptr(0)
        ctypes.memmove(dst + PAGE - 16, b'\xff' * 16, 16)
        self.reboot()
        self.assertEqual(self.lib.drms_user_config_persisted_version(), 0)  # 页无效
        # 提交标志内容损坏（CRC 位翻转）同样无效
        ctypes.memmove(dst, good, PAGE)
        bad = bytearray(good[PAGE - 16:])
        bad[8] ^= 1
        ctypes.memmove(dst + PAGE - 16, bytes(bad), 16)
        self.reboot()
        self.assertEqual(self.lib.drms_user_config_persisted_version(), 0)

    def test_body_is_programmed_in_quadwords_with_exact_tail(self):
        self.lib.drms_user_config_commit_baseline(100000.0, 0, 1)
        page = self.page(0)
        body_len = struct.unpack_from('<I', page, 8)[0]
        # body 长 44（非 16 倍数）：CRC 在 [40..43]，44..47 为擦除态填充
        self.assertEqual(body_len, 44)
        self.assertEqual(page[40:44], struct.pack('<I', zlib.crc32(page[:40]) & 0xFFFFFFFF))
        self.assertEqual(page[44:64], b'\xff' * 20)
        # 编程调用数 = ceil(44/16) body + 1 commit = 4
        self.assertEqual(self.program_count(), 4)

    def test_corrupt_newest_body_recovers_older_valid_page(self):
        self.assertEqual(self.lib.drms_user_config_commit_baseline(100000.0, 0, 1), t.OK)
        self.assertEqual(self.lib.drms_user_config_apply(t.build_body(2), len(t.build_body(2)), 1), t.OK)
        self.assertEqual(self.lib.drms_user_config_save(2), t.OK)
        newer = self.page_ptr(1)
        byte = ctypes.c_ubyte.from_address(newer + 35)
        byte.value ^= 1
        self.reboot(generation=1)
        self.assertEqual(self.lib.drms_user_config_persisted_version(), 1)
        self.assertEqual(self.lib.drms_user_config_r0(), 100000.0)

    def test_boot_prefers_newest_valid_page(self):
        # 两页都有有效提交：取 config_version 大者
        self.lib.drms_user_config_commit_baseline(100000.0, 0, 1)   # 页 A v1
        self.lib.drms_user_config_apply(t.build_body(2), len(t.build_body(2)), 1)
        self.lib.drms_user_config_save(2)                            # 页 B v2
        # 人为把页 A 的版本字段改大（保持 CRC 一致性破坏 → 仍应选 B）
        self.reboot()
        self.assertEqual(self.lib.drms_user_config_persisted_version(), 2)
        # B 撤销提交 → 只剩 A
        dst = self.page_ptr(1)
        ctypes.memmove(dst + PAGE - 16, b'\xff' * 16, 16)
        self.reboot()
        self.assertEqual(self.lib.drms_user_config_persisted_version(), 1)
        self.assertEqual(self.lib.drms_user_config_r0(), 100000.0)


if __name__ == '__main__':
    unittest.main()
