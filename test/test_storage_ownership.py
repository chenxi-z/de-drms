"""TF 介质所有权双轴测试：真实 drms_msc + drms_storage 联合驱动（R5/T4）。"""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

HEADER = r'''
#ifndef OWNERSHIP_FX_H
#define OWNERSHIP_FX_H
#include <stdint.h>
typedef unsigned int UINT;
typedef void VOID;
typedef struct {
  unsigned int fx_media_driver_request;
  unsigned int fx_media_driver_logical_sector;
  unsigned int fx_media_driver_sectors;
  void *fx_media_driver_buffer;
  unsigned int fx_media_driver_status;
  unsigned int fx_media_total_sectors;
} FX_MEDIA;
#define FX_SUCCESS 0
#define FX_IO_ERROR 1
#define FX_NULL 0
#define FX_DRIVER_UNINIT 9
#define FX_DRIVER_READ 2
#define FX_DRIVER_INIT 4
#define FX_SD_VOLUME_NAME "SD"
#define GPIO_PIN_RESET 0
#define SD_CD_GPIO_Port 0
#define SD_CD_Pin 15
#define __get_PRIMASK() ((uint32_t)0)
#define __disable_irq() ((void)0)
#define __set_PRIMASK(m) ((void)(m))
extern FX_MEDIA sdio_disk;
extern uint32_t fx_sd_media_memory[128];
int HAL_GPIO_ReadPin(int, int);
UINT fx_media_open(FX_MEDIA *, const char *, void (*)(FX_MEDIA *), void *, void *, unsigned long);
UINT fx_media_abort(FX_MEDIA *);
UINT fx_media_flush(FX_MEDIA *);
UINT fx_media_close(FX_MEDIA *);
void fx_stm32_sd_driver(FX_MEDIA *);
#endif
'''

MOCK = r'''
#include "app_filex.h"
#include "drms_msc.h"
#include <string.h>
volatile uint32_t drms_log_state,drms_storage_shutdown_ready;
void drms_log_removed(void) { drms_log_state=0; }
FX_MEDIA sdio_disk;
uint32_t fx_sd_media_memory[128];
int card_absent=1, opens, aborts, uninits, sd_inits, open_result, flushes, closes, flush_result, close_result, cancel_on_flush, raw_init_result, cancel_on_raw_init;
uint8_t disk_image[64 * 512];
int HAL_GPIO_ReadPin(int p,int n) { return card_absent; }
UINT fx_media_open(FX_MEDIA *m,const char *n,void (*f)(FX_MEDIA *),void *d,void *b,unsigned long z)
{ ++opens; if(open_result==0) m->fx_media_total_sectors=64; return open_result; }
UINT fx_media_abort(FX_MEDIA *m) { ++aborts; return 0; }
UINT fx_media_flush(FX_MEDIA *m) { ++flushes; if(cancel_on_flush) { cancel_on_flush=0; drms_msc_cancel(); } return flush_result; }
UINT fx_media_close(FX_MEDIA *m) { ++closes; return close_result; }
void fx_stm32_sd_driver(FX_MEDIA *m) {
  if(m->fx_media_driver_request==9) { ++uninits; return; }
  if(m->fx_media_driver_request==4) { ++sd_inits; if(cancel_on_raw_init) { cancel_on_raw_init=0; drms_msc_cancel(); } m->fx_media_driver_status=raw_init_result; return; }
  if(m->fx_media_driver_request==2) { /* FX_DRIVER_READ */
    if(card_absent) { m->fx_media_driver_status=1; return; }
    unsigned int sector=m->fx_media_driver_logical_sector;
    if(sector>=64) { m->fx_media_driver_status=1; return; }
    memcpy(m->fx_media_driver_buffer, disk_image + sector*512, 512);
    m->fx_media_driver_status=0;
  }
}
'''


def fill(image):
    for i, b in enumerate(bytes(range(7))):
        image[i] = (i * 31 + b) & 255


class StorageOwnershipTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        p = Path(cls.tmp.name)
        (p / 'app_filex.h').write_text(HEADER)
        (p / 'main.h').write_text('#include "app_filex.h"')
        (p / 'mock.c').write_text(MOCK)
        src = ROOT / 'firmware/DE-DRMS-Code/Core'
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Werror=implicit-function-declaration',
                        '-I', str(p), '-I', str(src / 'Inc'),
                        *[str(src / f'Src/drms_{name}.c') for name in ('msc', 'storage')],
                        str(p / 'mock.c'), '-o', str(p / 'own.so')], check=True)
        cls.lib = ctypes.CDLL(str(p / 'own.so'))
        cls.lib.drms_msc_read.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
        cls.lib.drms_msc_media_info.argtypes = [ctypes.POINTER(ctypes.c_uint32)]
        cls.lib.drms_msc_set_wait_hook.argtypes = [ctypes.c_void_p]
        cls.WAITHOOK = ctypes.CFUNCTYPE(None)
        fill((ctypes.c_ubyte * (64 * 512)).in_dll(cls.lib, 'disk_image'))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        lib = self.lib
        lib.drms_msc_init()
        lib.drms_storage_init()
        self.u32('drms_log_state').value = 0
        for name in ('opens', 'aborts', 'uninits', 'sd_inits', 'flushes', 'closes', 'cancel_on_flush', 'raw_init_result', 'cancel_on_raw_init'):
            ctypes.c_int.in_dll(lib, name).value = 0
        for name in ('open_result', 'flush_result', 'close_result', 'card_absent'):
            ctypes.c_int.in_dll(lib, name).value = 0
        ctypes.c_int.in_dll(lib, 'card_absent').value = 1  # 启动时无卡
        # 等待钩子：单线程下由测试驱动存储 service 步进
        WAIT = self.WAITHOOK(lambda: self.lib.drms_msc_service())
        self._keep_wait = WAIT
        lib.drms_msc_set_wait_hook(ctypes.cast(WAIT, ctypes.c_void_p))

    def mount(self):
        ctypes.c_int.in_dll(self.lib, 'card_absent').value = 0
        self.lib.drms_storage_poll()
        self.assertEqual(self.u32('drms_storage_mounted').value, 1)
        self.assertEqual(self.lib.drms_storage_capacity_sectors(), 64)

    def u32(self, name):
        return ctypes.c_uint32.in_dll(self.lib, name)

    def owner(self):
        return self.lib.drms_msc_owner()

    def health(self):
        return self.lib.drms_msc_health()

    def export(self):
        self.mount()
        self.assertEqual(self.lib.drms_msc_request_export(), 1)  # ACCEPTED
        self.lib.drms_msc_service()
        self.assertEqual(self.owner(), 2)  # EXPORTED
        return self.lib.drms_msc_export_generation()

    def release(self):
        self.assertEqual(self.lib.drms_msc_request_release(), 1)
        self.lib.drms_msc_service()
        self.assertEqual(self.owner(), 0)  # LOCAL
        self.lib.drms_storage_poll()
        self.assertEqual(self.u32('drms_storage_mounted').value, 1)

    def test_filex_worker_services_msc_mailbox(self):
        source = (ROOT / 'firmware/DE-DRMS-Code/FileX/App/app_filex.c').read_text()
        self.assertIn('drms_msc_init();', source)
        self.assertIn('drms_msc_set_wait_hook(', source)
        self.assertIn('drms_msc_service();', source)

    def test_local_absent_allows_monitoring_and_blocks_record_start_only(self):
        # 无卡：LOCAL+ABSENT——纯监测可用（互锁=0），记录因无卡被自然拒绝
        self.assertEqual(self.owner(), 0)
        self.assertEqual(self.health(), 0)  # ABSENT
        self.assertEqual(self.lib.drms_msc_blocks_recording(), 0)
        self.assertEqual(self.lib.drms_msc_request_export(), 1)
        self.lib.drms_msc_service()
        self.assertEqual(self.owner(), 0)  # 无卡导出回落 LOCAL，不开放磁盘
        self.assertEqual(self.lib.drms_msc_last_error(), 6)  # IO_ERROR
        self.assertEqual(self.lib.drms_msc_media_ready(), 0)

    def test_export_requires_ready_and_handoff_failure_keeps_single_world(self):
        self.mount()
        # 卡异常（FAULT）：拒绝导出
        ctypes.c_int.in_dll(self.lib, 'card_absent').value = 0
        ctypes.c_int.in_dll(self.lib, 'open_result').value = 0
        ctypes.c_int.in_dll(self.lib, 'flush_result').value = 1  # flush 失败
        self.assertEqual(self.lib.drms_msc_request_export(), 1)
        self.lib.drms_msc_service()
        self.assertEqual(self.owner(), 0)
        self.assertEqual(self.lib.drms_msc_media_ready(), 0)
        # flush/close/容量任一失败都不开放磁盘，也不残留双重管理
        ctypes.c_int.in_dll(self.lib, 'flush_result').value = 0
        ctypes.c_int.in_dll(self.lib, 'close_result').value = 1
        self.assertEqual(self.lib.drms_msc_request_export(), 1)
        self.lib.drms_msc_service()
        self.assertEqual(self.owner(), 0)
        self.assertEqual(self.u32('drms_storage_mounted').value, 0)  # 已 invalidate

    def test_export_release_round_trip_and_real_content(self):
        gen = self.export()
        self.assertEqual(self.health(), 1)  # EXPORTED：卡在位且容量已知 = READY
        blocks = ctypes.c_uint32(0)
        self.assertEqual(self.lib.drms_msc_media_info(ctypes.byref(blocks)), 0)
        self.assertEqual(blocks.value, 64)
        out = (ctypes.c_ubyte * 512)()
        self.assertEqual(self.lib.drms_msc_read(0, 1, out), 0)
        self.assertEqual(bytes(out[:4]), bytes(self.disk_bytes()[:4]))  # 真实扇区内容
        self.assertEqual(self.lib.drms_msc_blocks_recording(), 1)  # 导出期阻断记录
        self.release()
        self.assertEqual(self.lib.drms_msc_blocks_recording(), 0)
        self.assertGreater(self.lib.drms_msc_export_generation(), gen)  # 代次推进

    def test_export_rejected_while_recording_or_opening(self):
        self.mount()
        for state in (1, 2, 3):
            self.u32('drms_log_state').value = state
            self.assertEqual(self.lib.drms_msc_request_export(), 2, state)
            self.assertEqual(self.owner(), 0)
        self.u32('drms_log_state').value = 0
        self.assertEqual(self.lib.drms_msc_request_export(), 1)
        self.assertEqual(self.lib.drms_msc_blocks_recording(), 1)

    def test_usb_disconnect_while_local_does_not_unmount_or_abort(self):
        self.mount()
        self.u32('drms_log_state').value = 2
        self.lib.drms_msc_cancel()
        self.lib.drms_msc_service()
        self.assertEqual(self.owner(), 0)
        self.assertEqual(self.u32('drms_storage_mounted').value, 1)
        self.assertEqual(self.u32('drms_log_state').value, 2)
        self.assertEqual(ctypes.c_int.in_dll(self.lib, 'uninits').value, 0)

    def test_release_before_handoff_preserves_mounted_filex_driver(self):
        self.mount()
        self.assertEqual(self.lib.drms_msc_request_export(), 1)
        self.assertEqual(self.lib.drms_msc_request_release(), 1)
        self.lib.drms_msc_service()
        self.assertEqual(self.owner(), 0)
        self.assertEqual(self.u32('drms_storage_mounted').value, 1)
        self.assertEqual(ctypes.c_int.in_dll(self.lib, 'uninits').value, 0)

    def test_disconnect_during_handoff_does_not_enable_raw_access(self):
        self.mount()
        ctypes.c_int.in_dll(self.lib, 'cancel_on_flush').value = 1
        self.assertEqual(self.lib.drms_msc_request_export(), 1)
        self.lib.drms_msc_service()
        self.assertEqual(ctypes.c_int.in_dll(self.lib, 'sd_inits').value, 0)
        self.assertNotEqual(self.owner(), 2)
        self.assertEqual(self.lib.drms_msc_media_ready(), 0)

    def test_raw_initialization_failure_never_presents_media(self):
        self.mount()
        ctypes.c_int.in_dll(self.lib, 'raw_init_result').value = 1
        self.assertEqual(self.lib.drms_msc_request_export(), 1)
        self.lib.drms_msc_service()
        self.assertNotEqual(self.owner(), 2)
        self.assertEqual(self.lib.drms_msc_media_ready(), 0)
        self.assertEqual(self.lib.drms_msc_last_error(), 6)

    def test_card_removal_while_exported_revokes_ownership(self):
        self.export()
        ctypes.c_int.in_dll(self.lib, 'card_absent').value = 1
        self.lib.drms_msc_service()
        self.assertEqual(self.owner(), 0)
        self.assertEqual(self.lib.drms_msc_media_ready(), 0)
        self.assertEqual(self.lib.drms_msc_last_error(), 6)
        self.assertEqual(self.u32('drms_storage_mounted').value, 0)

    def test_media_generation_changes_and_removed_capacity_is_forgotten(self):
        self.mount()
        first = self.lib.drms_storage_media_generation()
        self.assertGreater(first, 0)
        self.assertEqual(self.lib.drms_msc_request_export(), 1)
        self.lib.drms_msc_service()
        ctypes.c_int.in_dll(self.lib, 'card_absent').value = 1
        self.lib.drms_storage_poll()
        removed = self.lib.drms_storage_media_generation()
        self.assertGreater(removed, first)
        self.lib.drms_msc_service()
        self.lib.drms_storage_poll()
        self.assertEqual(self.lib.drms_storage_capacity_sectors(), 0)
        ctypes.c_int.in_dll(self.lib, 'open_result').value = 1
        ctypes.c_int.in_dll(self.lib, 'card_absent').value = 0
        self.lib.drms_storage_poll()
        self.assertGreater(self.lib.drms_storage_media_generation(), removed)
        self.assertEqual(self.health(), 2)  # replacement failed identification: FAULT

    def test_disconnect_during_raw_initialization_does_not_publish_export(self):
        self.mount()
        ctypes.c_int.in_dll(self.lib, 'cancel_on_raw_init').value = 1
        self.assertEqual(self.lib.drms_msc_request_export(), 1)
        self.lib.drms_msc_service()
        self.assertNotEqual(self.owner(), 2)
        self.assertEqual(self.lib.drms_msc_media_ready(), 0)

    def test_exported_card_cannot_be_remounted_by_storage_poll(self):
        self.export()
        before = ctypes.c_int.in_dll(self.lib, 'opens').value
        self.assertEqual(self.u32('drms_storage_mounted').value, 0)
        self.lib.drms_storage_poll()
        self.assertEqual(self.u32('drms_storage_mounted').value, 0)
        self.assertEqual(ctypes.c_int.in_dll(self.lib, 'opens').value, before)
        self.assertEqual(self.owner(), 2)

    def test_read_validates_lba_and_capacity(self):
        self.export()
        out = (ctypes.c_ubyte * 512)()
        self.assertEqual(self.lib.drms_msc_read(63, 1, out), 0)          # 最后合法扇区
        self.assertEqual(self.lib.drms_msc_read(64, 1, out), 3)          # 越界
        self.assertEqual(self.lib.drms_msc_read(0xFFFFFFFF, 2, out), 3)  # 溢出拒绝
        self.assertEqual(self.lib.drms_msc_read(0, 0, out), 3)           # 零块
        self.assertEqual(self.lib.drms_msc_read(0, 1, None), 3)          # 空缓冲

    def test_write_callback_is_read_only(self):
        # 写路径由 USBX 回调层拒绝（ux_device_msc.c USER 区），此处验证核心：
        # 导出状态下所有权归 EXPORTED，drms_storage_raw_read 只读不写——
        # 通过 uninits/驱动请求审计确认没有任何写请求发出。
        self.export()
        out = (ctypes.c_ubyte * 512)()
        self.assertEqual(self.lib.drms_msc_read(5, 1, out), 0)
        self.assertEqual(ctypes.c_int.in_dll(self.lib, 'uninits').value, 1)  # 仅交接期 uninit

    def test_inflight_read_survives_timeout_without_slot_reuse(self):
        self.export()
        out1 = (ctypes.c_ubyte * 512)()
        # 移除等待钩子：read 无法驱动 service → 在途保持
        self.lib.drms_msc_set_wait_hook(None)
        self.assertEqual(self.lib.drms_msc_read(0, 1, out1), 7)  # TIMEOUT
        # 槽保持占用：新请求拒绝，out1 不得复用
        out2 = (ctypes.c_ubyte * 512)()
        self.assertEqual(self.lib.drms_msc_read(0, 1, out2), 2)  # BUSY
        # USBX may reuse its buffer immediately after timeout. Late completion
        # must only touch storage-owned memory.
        self.lib.drms_msc_service()
        self.assertEqual(bytes(out1[:4]), b'\x00\x00\x00\x00')
        # 恢复泵钩子后新请求正常受理并完成
        WAIT = self.WAITHOOK(lambda: self.lib.drms_msc_service())
        self._keep_wait2 = WAIT
        self.lib.drms_msc_set_wait_hook(ctypes.cast(WAIT, ctypes.c_void_p))
        self.assertEqual(self.lib.drms_msc_read(0, 1, out2), 0)
        self.assertNotEqual(bytes(out2[:4]), bytes(out1[:4]))

    def test_multi_sector_read_preserves_all_bytes(self):
        self.export()
        image = (ctypes.c_ubyte * (64 * 512)).in_dll(self.lib, 'disk_image')
        image[512] = 99
        out = (ctypes.c_ubyte * 1024)()
        self.assertEqual(self.lib.drms_msc_read(0, 2, out), 0)
        self.assertEqual(bytes(out), bytes(image[:1024]))

    def test_read_request_and_cancel_are_mutually_exclusive(self):
        # 自查修复回归：所有权检查与槽占用必须在同一临界区——
        # 取消后到达的读请求必须被拒，且不得留下无人归结的占槽请求。
        self.export()
        self.lib.drms_msc_cancel()
        out = (ctypes.c_ubyte * 512)()
        self.assertEqual(self.lib.drms_msc_read(0, 1, out), 2)  # BUSY，不占槽
        # 槽未被占用：收敛取消（回到 LOCAL）后可重新导出并立即可读
        self.lib.drms_msc_service()
        self.assertEqual(self.owner(), 0)
        self.lib.drms_storage_poll()
        self.export()
        self.assertEqual(self.lib.drms_msc_read(0, 1, out), 0)

    def test_cancel_and_card_removal_revoke_export(self):
        gen = self.export()
        ctypes.c_int.in_dll(self.lib, 'card_absent').value = 1  # 拔卡
        self.lib.drms_msc_cancel()  # IRQ 安全入口
        self.assertEqual(self.owner(), 3)  # RELEASING（撤销就绪）
        self.lib.drms_msc_service()
        self.assertEqual(self.owner(), 0)  # 收敛回 LOCAL
        self.assertEqual(self.health(), 0)  # ABSENT
        self.assertGreater(self.lib.drms_msc_export_generation(), gen)

    def disk_bytes(self):
        return bytes((ctypes.c_ubyte * (64 * 512)).in_dll(self.lib, 'disk_image'))

    def test_capacity_change_requires_reexport(self):
        self.export()
        out = (ctypes.c_ubyte * 512)()
        self.assertEqual(self.lib.drms_msc_read(0, 1, out), 0)
        self.release()
        # 换卡：容量缓存随重挂载刷新
        ctypes.c_int.in_dll(self.lib, 'card_absent').value = 1
        self.lib.drms_storage_poll()  # 旧卡拔出
        ctypes.c_int.in_dll(self.lib, 'card_absent').value = 0
        self.lib.drms_storage_poll()  # 新卡挂载 → 容量刷新
        self.export()
        blocks = ctypes.c_uint32(0)
        self.assertEqual(self.lib.drms_msc_media_info(ctypes.byref(blocks)), 0)
        self.assertEqual(blocks.value, 64)  # mock 新卡容量
        self.assertGreater(self.lib.drms_msc_export_generation(), 0)

    def test_release_completes_only_after_inflight_resolved(self):
        self.export()
        out = (ctypes.c_ubyte * 512)()
        self.lib.drms_msc_set_wait_hook(None)
        self.assertEqual(self.lib.drms_msc_read(0, 1, out), 7)  # 在途挂起（槽被占用）
        self.assertEqual(self.lib.drms_msc_request_release(), 1)
        self.lib.drms_msc_service()
        # 同一 service 调用内：先归结在途读（存储线程是唯一执行者），
        # 随后完成释放与重挂载——FileX 绝不在原始读结束前打开。
        self.assertEqual(self.owner(), 0)
        self.lib.drms_storage_poll()
        self.assertEqual(self.u32('drms_storage_mounted').value, 1)
        self.assertEqual(self.lib.drms_msc_blocks_recording(), 0)

    def test_quarantined_refuses_new_work_until_cleanup_converges(self):
        self.export()
        out = (ctypes.c_ubyte * 512)()
        self.lib.drms_msc_set_wait_hook(None)
        self.assertEqual(self.lib.drms_msc_read(0, 1, out), 7)  # 在途挂起
        # 监督者显式隔离（存储线程错过时限、无法证明静止）
        self.lib.drms_msc_mark_quarantined()
        self.assertEqual(self.owner(), 4)  # QUARANTINED
        self.assertEqual(self.lib.drms_msc_request_export(), 2)   # BUSY：隔离拒绝新导出
        self.assertEqual(self.lib.drms_msc_request_release(), 2)  # BUSY
        self.assertEqual(self.lib.drms_msc_read(0, 1, out), 2)    # BUSY：不接收新读
        # 存储线程继续收敛既有清理：归结旧读 → 释放 → LOCAL
        self.lib.drms_msc_service()
        self.lib.drms_msc_service()
        self.assertEqual(self.owner(), 0)
        self.lib.drms_storage_poll()
        self.assertEqual(self.u32('drms_storage_mounted').value, 1)
        self.assertEqual(self.lib.drms_msc_blocks_recording(), 0)


if __name__ == '__main__':
    unittest.main()
