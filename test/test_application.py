"""Supervisor integration: real command, ADC, calibration and logging modules.

Only HAL/ThreadX/FileX/Flash/RTC boundaries are doubled. No physical board is used.
"""
import ctypes
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from test_acquisition import HEADER as ACQ_HEADER, MOCK as ACQ_MOCK
from test_logging import HEADER as FX_HEADER, MOCK as FX_MOCK
from test_calibration_journal import MOCK as CAL_MOCK
from test_user_config import build_body, with_baseline_policy
from test_config_wire import settings, tlv
from test_config_snapshot import View
import struct

ROOT = Path(__file__).resolve().parents[1]

class ControlRequest(ctypes.Structure):
    _fields_ = [('source', ctypes.c_uint32), ('session', ctypes.c_uint32),
                ('request_id', ctypes.c_uint64), ('operation', ctypes.c_int),
                ('value', ctypes.c_uint32), ('number', ctypes.c_double),
                ('payload', ctypes.c_void_p), ('payload_length', ctypes.c_uint32),
                ('expected_version', ctypes.c_uint64)]

class Token(ctypes.Structure):
    _fields_ = [('operation_id', ctypes.c_uint64), ('generation', ctypes.c_uint32)]

class StatusSnapshot(ctypes.Structure):
    _fields_ = [('revision', ctypes.c_uint64), ('mono_us', ctypes.c_uint64),
                ('running_version', ctypes.c_uint64), ('saved_version', ctypes.c_uint64),
                ('baseline_version', ctypes.c_uint64), ('calibration_version', ctypes.c_uint64),
                ('sample_index', ctypes.c_uint64), ('ohms', ctypes.c_double), ('ratio', ctypes.c_double),
                ('rate', ctypes.c_uint32), ('generation', ctypes.c_uint32),
                ('media_generation', ctypes.c_uint32), ('quality', ctypes.c_uint32), ('fault', ctypes.c_uint32),
                ('acquisition', ctypes.c_uint8), ('recording', ctypes.c_uint8), ('medium', ctypes.c_uint8),
                ('owner', ctypes.c_uint8), ('maintenance', ctypes.c_uint8), ('fresh', ctypes.c_uint8),
                ('classification', ctypes.c_uint8), ('rtc_valid', ctypes.c_uint8),
                ('ohms_valid', ctypes.c_uint8), ('ratio_valid', ctypes.c_uint8),
                ('level_valid', ctypes.c_uint8), ('level', ctypes.c_uint8), ('interval', ctypes.c_uint16)]
TX_HEADER = r'''
#ifndef TEST_TX_H
#define TEST_TX_H
typedef unsigned int UINT;
typedef unsigned long ULONG;
typedef struct { unsigned int head,tail,count;unsigned char messages[16][32]; } TX_QUEUE;
#define TX_NO_WAIT 0
#define TX_SUCCESS 0
UINT tx_queue_create(TX_QUEUE *,char *,UINT,void *,ULONG);
UINT tx_queue_send(TX_QUEUE *,void *,ULONG);
UINT tx_queue_receive(TX_QUEUE *,void *,ULONG);
UINT tx_queue_flush(TX_QUEUE *);
#endif
'''
APP_MOCK = r'''
#include "tx_api.h"
#include "drms_time.h"
#include <string.h>
volatile unsigned int drms_usb_status,drms_uart_rx_dropped,drms_uart_tx_dropped;
volatile uint32_t drms_battery_mv=3700,drms_battery_valid=1;
static DRMS_Time clock_value;
void drms_aux_poll(void) {}
unsigned int drms_usb_can_io(void) { return 0; }
int sd_card_present, measure_down, power_down;
int HAL_GPIO_ReadPin(int p,int n) {
  return n==18 ? (sd_card_present ? 0 : 1) : n==13 ? !measure_down : n==14 ? !power_down : 1;
}
int drms_power_backend_enter(void) { return 0; }
void drms_time_get(DRMS_Time *t) { *t=clock_value; }
int drms_time_set(const char *text) { return drms_time_parse(text,&clock_value); }
uint32_t HAL_GetUIDw0(void) { return 1; }
uint32_t HAL_GetUIDw1(void) { return 2; }
uint32_t HAL_GetUIDw2(void) { return 3; }
UINT tx_queue_create(TX_QUEUE *q,char *n,UINT z,void *m,ULONG size) { memset(q,0,sizeof(*q));return z*sizeof(ULONG)==32?0:1; }
UINT tx_queue_send(TX_QUEUE *q,void *item,ULONG wait) {
 if(q->count==16) return 1;
 memcpy(q->messages[q->head],item,32);q->head=(q->head+1)%16;++q->count;return 0;
}
UINT tx_queue_receive(TX_QUEUE *q,void *item,ULONG wait) {
 if(!q->count) return 1;
 memcpy(item,q->messages[q->tail],32);q->tail=(q->tail+1)%16;--q->count;return 0;
}
UINT tx_queue_flush(TX_QUEUE *q) { q->head=q->tail=q->count=0;return 0; }
/* 用户区 Flash 后端替身：RAM 页（真后端直写 0x080F8000，主机不可执行） */
static uint8_t user_pages[2][8192];
int fail_user_write;
int drms_user_backend_begin(void) { return !fail_user_write; }
void drms_user_backend_end(void) {}
int drms_user_backend_erase(unsigned int page) { memset(user_pages[page],0xFF,8192); return 1; }
int drms_user_backend_program(unsigned int page, unsigned int offset, const uint8_t q[16]) {
  if (offset+16 > 8192) return 0;
  memcpy(user_pages[page]+offset, q, 16); return 1; }
int drms_user_backend_read(unsigned int page, unsigned int offset, uint8_t *out, unsigned int len) {
  if (offset+len > 8192) return 0;
  memcpy(out, user_pages[page]+offset, len); return 1; }
int HAL_ICACHE_IsEnabled(void) { return 0; }
int HAL_ICACHE_Disable(void) { return 0; }
int HAL_ICACHE_Enable(void) { return 0; }
void HAL_ICACHE_Invalidate(void) {}
int HAL_FLASH_Unlock(void) { return 0; }
int HAL_FLASH_Lock(void) { return 0; }
int HAL_FLASHEx_Erase(void *e, uint32_t *err) { *err = 0xFFFFFFFFu; return 0; }
int HAL_FLASH_Program(int type, uint32_t addr, uint32_t data) { return 0; }
void __HAL_FLASH_CLEAR_FLAG(uint32_t f) {}
'''


class ApplicationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        p = Path(cls.tmp.name)
        extra = r'''
#define LED_GREEN_GPIO_Port 0
#define LED_GREEN_Pin 8
#define LED_YELLOW_GPIO_Port 0
#define LED_YELLOW_Pin 9
#define LED_ORANGE_GPIO_Port 0
#define LED_ORANGE_Pin 10
#define LED_RED_GPIO_Port 0
#define LED_RED_Pin 11
#define ADS_DRDY_Pin 12
#define MEAS_BTN_Pin 13
#define MEAS_BTN_GPIO_Port 0
#define PWR_BTN_Pin 14
#define PWR_BTN_GPIO_Port 0
#define USB_VBUS_N_GPIO_Port 0
#define USB_VBUS_N_Pin 15
#define BQ_PG_GPIO_Port 0
#define BQ_PG_Pin 16
#define BQ_CHG_GPIO_Port 0
#define BQ_CHG_Pin 17
int HAL_GPIO_ReadPin(int,int);
#define SD_CD_GPIO_Port 0
#define SD_CD_Pin 18
typedef struct { unsigned int TypeErase, Banks, Page, NbPages; } FLASH_EraseInitTypeDef;
#define FLASH_TYPEERASE_PAGES 1
#define FLASH_BANK_2 2u
#define FLASH_PAGE_NB 64u
#define FLASH_TYPEPROGRAM_QUADWORD 2u
#define FLASH_FLAG_ALL_ERRORS 0u
int HAL_ICACHE_IsEnabled(void);
int HAL_ICACHE_Disable(void);
int HAL_ICACHE_Enable(void);
void HAL_ICACHE_Invalidate(void);
int HAL_FLASH_Unlock(void);
int HAL_FLASH_Lock(void);
int HAL_FLASHEx_Erase(void *e, uint32_t *err);
int HAL_FLASH_Program(int type, uint32_t addr, uint32_t data);
void __HAL_FLASH_CLEAR_FLAG(uint32_t f);
#define FLASH_FLAG_ALL_ERRORS 0u
#define __alignas(x)
#define __get_PRIMASK() 0U
#define __disable_irq() ((void)0)
#define __set_PRIMASK(x) ((void)(x))
uint32_t HAL_GetUIDw0(void);
uint32_t HAL_GetUIDw1(void);
uint32_t HAL_GetUIDw2(void);
'''
        (p / 'main.h').write_text('#ifndef APP_MAIN_H\n#define APP_MAIN_H\n'
                                  + ACQ_HEADER + extra + '\n#endif\n')
        (p / 'spi.h').write_text('#include "main.h"')
        fxh = FX_HEADER.replace(
            'typedef struct { int unused; } FX_MEDIA;',
            'typedef struct { unsigned int fx_media_driver_request;\n'
            '    unsigned int fx_media_driver_logical_sector;\n'
            '    unsigned int fx_media_driver_sectors;\n'
            '    void *fx_media_driver_buffer;\n'
            '    unsigned int fx_media_driver_status;\n'
            '    unsigned int fx_media_total_sectors; } FX_MEDIA;')
        fxh = fxh.replace('#define FX_IO_ERROR 1',
            '#define FX_IO_ERROR 1\n'
            '#define FX_DRIVER_UNINIT 9\n#define FX_DRIVER_INIT 4\n'
            '#define FX_NULL 0\n'
            '#define FX_SD_VOLUME_NAME "SD"\n'
            'UINT fx_media_open(FX_MEDIA *, const char *, void (*)(FX_MEDIA *), void *, void *, unsigned long);')
        fxh = fxh.replace('UINT fx_media_flush(FX_MEDIA *);',
            'UINT fx_media_flush(FX_MEDIA *);\n'
            'UINT fx_media_close(FX_MEDIA *);\n'
            'UINT fx_media_abort(FX_MEDIA *);\n'
            'void fx_stm32_sd_driver(FX_MEDIA *);\n'
            '#define FX_DRIVER_READ 2')
        (p / 'app_filex.h').write_text('#ifndef TEST_FX_H\n#define TEST_FX_H\n' + fxh + '\n#endif\n')
        (p / 'tx_api.h').write_text(TX_HEADER)
        fx = FX_MOCK.replace('volatile uint32_t drms_acq_overruns,drms_acq_queue_drops;', '')
        fx = fx.replace('uint32_t drms_msc_blocks_recording(void) { return mock_msc_blocked; }', '')
        fx = fx.replace('uint32_t HAL_GetTick(void) { return ticks; }', '')
        fx = fx.replace('ticks;', 'unused_log_ticks;')
        fx += '\n/* SD 驱动替身：UNINIT 计数，读请求按卡状态返回 */\n'
        fx += 'unsigned int sd_uninits;\n'
        fx += 'uint32_t fx_sd_media_memory[128];\n'
        fx += 'FX_MEDIA sdio_disk;\n'
        fx += 'unsigned int fx_flushes, fx_closes, fx_abort_calls, fx_open_result;\n'
        fx += 'UINT fx_media_close(FX_MEDIA *m) { ++fx_closes; return 0; }\n'
        fx += 'UINT fx_media_abort(FX_MEDIA *m) { ++fx_abort_calls; return 0; }\n'
        fx += 'UINT fx_media_open(FX_MEDIA *m, const char *n, void (*f)(FX_MEDIA *), void *d, void *b, unsigned long z) { m->fx_media_total_sectors = 64; return 0; }\n'
        fx += 'void fx_stm32_sd_driver(FX_MEDIA *m) { if (m->fx_media_driver_request==9) ++sd_uninits; if (m->fx_media_driver_request==4) m->fx_media_driver_status=0; }\n'
        # storage.c 已真编译：剥离 mock 中的介质状态定义（保留计数器）
        fx = fx.replace('volatile unsigned int drms_storage_mounted=1,drms_storage_status;\n',
                        'extern volatile unsigned int drms_storage_mounted,drms_storage_status;\n')
        fx = fx.replace('void drms_storage_invalidate(void) { ++invalidates;drms_storage_mounted=0;drms_log_removed(); }',
                        '')  # 真实 storage.c 提供定义；计数器归集成测试
        mock = ACQ_MOCK.replace('pins[8]', 'pins[16]')
        mock = mock.replace('int HAL_SPI_Abort(SPI_HandleTypeDef *s) { return 0; }',
                            'int abort_failure; int HAL_SPI_Abort(SPI_HandleTypeDef *s) { return abort_failure; }')
        (p / 'mock.c').write_text(mock + fx + CAL_MOCK + APP_MOCK)
        src = ROOT / 'firmware/DE-DRMS-Code/Core'
        names = ('application', 'command', 'acquisition', 'measurement', 'fifo', 'logging',
                 'log_codec', 'calibration_codec', 'calibration_journal', 'time_codec', 'power',
                 'control', 'record_session', 'monitor', 'filter', 'classifier', 'baseline', 'capture_time',
                 'user_config', 'config_snapshot', 'msc', 'storage')
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Werror=implicit-function-declaration',
                        '-I', str(p), '-I', str(src / 'Inc'),
                        *[str((src.parent / 'App/application/measurement' if name in ('monitor', 'filter', 'classifier', 'baseline') else src / 'Src') / f'drms_{name}.c') for name in names],
                        str(src.parent / 'App/interfaces/local_ui/drms_button.c'),
                        str(src.parent / 'App/interfaces/cdc/drms_config_wire.c'),
                        str(src.parent / 'App/interfaces/cdc/drms_cdc_frame.c'),
                        str(p / 'mock.c'), '-lm', '-o', str(p / 'app.so')], check=True)
        cls.instance = 0

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        type(self).instance += 1
        p = Path(self.tmp.name)
        target = p / f'app-{self.instance}.so'
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

    def insert_card(self):
        ctypes.c_int.in_dll(self.lib, 'sd_card_present').value = 1
        self.lib.drms_storage_poll()
        self.assertEqual(self.value('drms_storage_mounted').value, 1)

    def test_msc_export_retains_tf_lease_until_release(self):
        self.insert_card()
        request = ControlRequest(source=3, request_id=42, operation=2)
        self.assertEqual(self.lib.drms_control_submit(ctypes.byref(request)), 1)
        self.lib.drms_application_poll()
        self.assertEqual(self.lib.drms_msc_owner(), 1)
        self.lib.drms_msc_service()
        self.lib.drms_application_poll()
        self.assertEqual(self.lib.drms_msc_owner(), 2)
        token = Token()
        self.assertEqual(self.lib.drms_control_reserve(4, ctypes.byref(token)), 2)
        release = ControlRequest(source=3, request_id=43, operation=9)
        release_id = ctypes.c_uint64()
        self.lib.drms_control_submit_identified.argtypes = [ctypes.POINTER(ControlRequest), ctypes.POINTER(ctypes.c_uint64)]
        self.assertEqual(self.lib.drms_control_submit_identified(ctypes.byref(release), ctypes.byref(release_id)), 1)
        self.lib.drms_application_poll()
        self.assertEqual(self.lib.drms_msc_owner(), 3)
        self.lib.drms_msc_service()
        self.lib.drms_application_poll()
        self.assertEqual(self.lib.drms_control_reserve(4, ctypes.byref(token)), 1)
        self.lib.drms_control_complete(token, 0, 4)

    def test_msc_release_reports_remount_failure(self):
        self.insert_card()
        export = ControlRequest(source=3, request_id=42, operation=2)
        self.assertEqual(self.lib.drms_control_submit(ctypes.byref(export)), 1)
        self.lib.drms_application_poll()
        self.lib.drms_msc_service()
        self.lib.drms_application_poll()
        ctypes.c_int.in_dll(self.lib, 'sd_card_present').value = 0
        release = ControlRequest(source=3, request_id=44, operation=9)
        operation_id = ctypes.c_uint64()
        self.lib.drms_control_submit_identified.argtypes = [ctypes.POINTER(ControlRequest), ctypes.POINTER(ctypes.c_uint64)]
        self.assertEqual(self.lib.drms_control_submit_identified(ctypes.byref(release), ctypes.byref(operation_id)), 1)
        self.lib.drms_application_poll()
        self.lib.drms_msc_service()
        self.lib.drms_application_poll()
        from test_control_contract import Completion
        self.lib.drms_control_get_operation.argtypes = [ctypes.c_uint64, ctypes.POINTER(Completion)]
        result = Completion()
        self.assertEqual(self.lib.drms_control_get_operation(operation_id.value, ctypes.byref(result)), 0)
        self.assertEqual((result.result, result.phase), (6, 2))

    def test_msc_export_failure_releases_tf_lease(self):
        request = ControlRequest(source=3, request_id=43, operation=2)
        self.assertEqual(self.lib.drms_control_submit(ctypes.byref(request)), 1)
        self.lib.drms_application_poll()
        self.lib.drms_msc_service()
        self.lib.drms_application_poll()
        self.assertEqual(self.lib.drms_msc_last_error(), 6)
        token = Token()
        self.assertEqual(self.lib.drms_control_reserve(4, ctypes.byref(token)), 1)
        self.lib.drms_control_complete(token, 0, 4)

    def test_save_config_stops_safely_persists_and_resumes(self):
        body = build_body(params=(4000, 0, 0, 0, 32000))
        self.lib.drms_user_config_apply.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_uint64]
        self.assertEqual(self.lib.drms_user_config_apply(body, len(body), 0), 0)
        request = ControlRequest(source=3, request_id=80, operation=7, expected_version=1)
        ident = ctypes.c_uint64()
        self.lib.drms_control_submit_identified.argtypes = [ctypes.POINTER(ControlRequest), ctypes.POINTER(ctypes.c_uint64)]
        self.assertEqual(self.lib.drms_control_submit_identified(ctypes.byref(request), ctypes.byref(ident)), 1)
        self.lib.drms_application_poll()
        from test_control_contract import Completion
        result = Completion()
        self.lib.drms_control_get_operation.argtypes = [ctypes.c_uint64, ctypes.POINTER(Completion)]
        self.assertEqual(self.lib.drms_control_get_operation(ident.value, ctypes.byref(result)), 0)
        self.assertEqual((result.result, result.phase), (0, 2))
        self.assertEqual(self.lib.drms_user_config_persisted_version(), 1)
        self.assertEqual(self.value('drms_acq_running').value, 1)

    def test_apply_config_updates_rate_and_rejects_stale_without_stopping(self):
        self.assertEqual(self.value('drms_acq_running').value, 1)
        payload = settings().replace(tlv(72, struct.pack('<I', 4000)), tlv(72, struct.pack('<I', 8000)))
        source = ctypes.create_string_buffer(payload)
        request = ControlRequest(source=3, request_id=80, operation=4,
                                 payload=ctypes.addressof(source), payload_length=len(payload), expected_version=0)
        ident = ctypes.c_uint64()
        self.lib.drms_control_submit_identified.argtypes = [ctypes.POINTER(ControlRequest), ctypes.POINTER(ctypes.c_uint64)]
        self.assertEqual(self.lib.drms_control_submit_identified(ctypes.byref(request), ctypes.byref(ident)), 1)
        self.lib.drms_application_poll()
        from test_control_contract import Completion
        result = Completion()
        self.lib.drms_control_get_operation.argtypes = [ctypes.c_uint64, ctypes.POINTER(Completion)]
        self.assertEqual(self.lib.drms_control_get_operation(ident.value, ctypes.byref(result)), 0)
        self.assertEqual((result.result, result.phase), (0, 2))
        self.assertEqual(self.value('drms_acq_rate').value, 8000)
        self.assertEqual(self.lib.drms_user_config_run_version(), 1)
        self.lib.drms_config_snapshot_acquire.argtypes = [ctypes.POINTER(View)]
        self.lib.drms_config_snapshot_release.argtypes = [ctypes.POINTER(View)]
        view = View()
        self.assertEqual(self.lib.drms_config_snapshot_acquire(ctypes.byref(view)), 1)
        self.assertEqual((ctypes.string_at(view.data, view.length), view.running, view.saved), (payload, 1, 0))
        self.lib.drms_config_snapshot_release(ctypes.byref(view))
        self.assertEqual(self.lib.drms_control_submit_identified(ctypes.byref(request), ctypes.byref(ident)), 1)
        self.lib.drms_application_poll()
        self.assertEqual(self.lib.drms_control_get_operation(ident.value, ctypes.byref(result)), 0)
        self.assertEqual(result.result, 4)
        self.assertEqual((self.value('drms_acq_rate').value, self.value('drms_acq_running').value), (8000, 1))
        save = ControlRequest(source=3, request_id=81, operation=7, expected_version=1)
        self.assertEqual(self.lib.drms_control_submit_identified(ctypes.byref(save), ctypes.byref(ident)), 1)
        self.lib.drms_application_poll()
        self.assertEqual(self.lib.drms_control_get_operation(ident.value, ctypes.byref(result)), 0)
        self.assertEqual(result.result, 0)
        self.assertEqual(self.lib.drms_config_snapshot_acquire(ctypes.byref(view)), 1)
        self.assertEqual((ctypes.string_at(view.data, view.length), view.running, view.saved), (payload, 1, 1))
        self.lib.drms_config_snapshot_release(ctypes.byref(view))

    def test_apply_failed_restart_does_not_publish_candidate(self):
        payload = settings()
        source = ctypes.create_string_buffer(payload)
        request = ControlRequest(source=3, request_id=81, operation=4,
                                 payload=ctypes.addressof(source), payload_length=len(payload), expected_version=0)
        operation = ctypes.c_uint64()
        self.lib.drms_control_submit_identified.argtypes = [ctypes.POINTER(ControlRequest), ctypes.POINTER(ctypes.c_uint64)]
        self.lib.set_spi_size(23)
        self.assertEqual(self.lib.drms_control_submit_identified(ctypes.byref(request), ctypes.byref(operation)), 1)
        self.lib.drms_application_poll()
        from test_control_contract import Completion
        result = Completion()
        self.lib.drms_control_get_operation.argtypes = [ctypes.c_uint64, ctypes.POINTER(Completion)]
        self.assertEqual(self.lib.drms_control_get_operation(operation.value, ctypes.byref(result)), 0)
        self.assertEqual(result.result, 6)
        self.assertEqual(self.lib.drms_user_config_run_version(), 0)
        self.assertEqual(self.value('drms_acq_running').value, 0)

    def test_save_config_version_mismatch_does_not_interrupt_sampling(self):
        generation = self.lib.drms_acq_generation()
        request = ControlRequest(source=3, request_id=81, operation=7, expected_version=99)
        ident = ctypes.c_uint64()
        self.lib.drms_control_submit_identified.argtypes = [ctypes.POINTER(ControlRequest), ctypes.POINTER(ctypes.c_uint64)]
        self.assertEqual(self.lib.drms_control_submit_identified(ctypes.byref(request), ctypes.byref(ident)), 1)
        self.lib.drms_application_poll()
        from test_control_contract import Completion
        result = Completion()
        self.lib.drms_control_get_operation.argtypes = [ctypes.c_uint64, ctypes.POINTER(Completion)]
        self.assertEqual(self.lib.drms_control_get_operation(ident.value, ctypes.byref(result)), 0)
        self.assertEqual(result.result, 4)
        self.assertEqual(self.lib.drms_acq_generation(), generation)
        self.assertEqual(self.value('drms_acq_running').value, 1)

    def test_save_config_failure_preserves_dirty_config_and_resumes(self):
        body = build_body(params=(4000, 0, 0, 0, 32000))
        self.lib.drms_user_config_apply.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_uint64]
        self.assertEqual(self.lib.drms_user_config_apply(body, len(body), 0), 0)
        ctypes.c_int.in_dll(self.lib, 'fail_user_write').value = 1
        request = ControlRequest(source=3, request_id=82, operation=7, expected_version=1)
        ident = ctypes.c_uint64()
        self.lib.drms_control_submit_identified.argtypes = [ctypes.POINTER(ControlRequest), ctypes.POINTER(ctypes.c_uint64)]
        self.assertEqual(self.lib.drms_control_submit_identified(ctypes.byref(request), ctypes.byref(ident)), 1)
        self.lib.drms_application_poll()
        from test_control_contract import Completion
        result = Completion()
        self.lib.drms_control_get_operation.argtypes = [ctypes.c_uint64, ctypes.POINTER(Completion)]
        self.assertEqual(self.lib.drms_control_get_operation(ident.value, ctypes.byref(result)), 0)
        self.assertEqual(result.result, 6)
        self.assertEqual(self.lib.drms_user_config_dirty(), 1)
        self.assertEqual(self.lib.drms_user_config_persisted_version(), 0)
        self.assertEqual(self.value('drms_acq_running').value, 1)

    def test_save_config_quarantines_unconfirmed_dma_abort(self):
        body = build_body(params=(4000, 0, 0, 0, 32000))
        self.lib.drms_user_config_apply.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_uint64]
        self.assertEqual(self.lib.drms_user_config_apply(body, len(body), 0), 0)
        self.lib.drms_acq_drdy()
        ctypes.c_int.in_dll(self.lib, 'abort_failure').value = 1
        request = ControlRequest(source=3, request_id=83, operation=7, expected_version=1)
        ident = ctypes.c_uint64()
        self.lib.drms_control_submit_identified.argtypes = [ctypes.POINTER(ControlRequest), ctypes.POINTER(ctypes.c_uint64)]
        self.assertEqual(self.lib.drms_control_submit_identified(ctypes.byref(request), ctypes.byref(ident)), 1)
        self.lib.drms_application_poll()
        from test_control_contract import Completion, Snapshot
        result, snapshot = Completion(), Snapshot()
        self.lib.drms_control_get_operation.argtypes = [ctypes.c_uint64, ctypes.POINTER(Completion)]
        self.assertEqual(self.lib.drms_control_get_operation(ident.value, ctypes.byref(result)), 0)
        self.assertEqual(result.result, 10)
        self.lib.drms_control_get_snapshot(ctypes.byref(snapshot))
        self.assertNotEqual(snapshot.quarantined_mask & 1, 0)
        self.assertEqual(self.lib.drms_user_config_persisted_version(), 0)

    def test_baseline_build_without_card_persists_and_resumes_monitor(self):
        body = with_baseline_policy(build_body(params=(4000, 0, 0, 0, 32000)), 4, 750, 0.01)
        self.lib.drms_user_config_apply.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_uint64]
        self.assertEqual(self.lib.drms_user_config_apply(body, len(body), 0), 0)
        request = ControlRequest(source=1, request_id=100, operation=5)
        self.assertEqual(self.lib.drms_control_submit(ctypes.byref(request)), 1)
        self.lib.drms_application_poll()
        self.frames(4, 280000, 4200000)
        self.lib.drms_user_config_r0.restype = ctypes.c_double
        self.assertAlmostEqual(self.lib.drms_user_config_r0(), 10000.0, places=2)
        self.assertEqual(self.lib.drms_user_config_r0_valid(), 1)
        self.assertEqual(self.value('drms_acq_running').value, 1)
        self.assertEqual(self.value('drms_log_state').value, 0)

    def test_baseline_rejects_bad_sample_without_replacing_old_value(self):
        body = with_baseline_policy(build_body(r0_valid=1, r0=12345.0,
            params=(4000, 0, 0, 0, 32000)), 3, 500, 0.01)
        self.lib.drms_user_config_apply.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_uint64]
        self.assertEqual(self.lib.drms_user_config_apply(body, len(body), 0), 0)
        self.assertEqual(self.lib.drms_user_config_save(1), 0)
        request = ControlRequest(source=1, request_id=101, operation=5)
        self.assertEqual(self.lib.drms_control_submit(ctypes.byref(request)), 1)
        self.lib.drms_application_poll()
        self.frames(1, 280000, 4200000)
        self.frames(1, 280000, 0)
        self.lib.drms_user_config_r0.restype = ctypes.c_double
        self.assertEqual(self.lib.drms_user_config_r0(), 12345.0)
        self.assertEqual(self.value('drms_acq_running').value, 1)

    def test_baseline_write_failure_retains_old_value_and_resumes(self):
        body = with_baseline_policy(build_body(r0_valid=1, r0=12345.0,
            params=(4000, 0, 0, 0, 32000)), 3, 500, 0.01)
        self.lib.drms_user_config_apply.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_uint64]
        self.assertEqual(self.lib.drms_user_config_apply(body, len(body), 0), 0)
        self.assertEqual(self.lib.drms_user_config_save(1), 0)
        ctypes.c_int.in_dll(self.lib, 'fail_user_write').value = 1
        request = ControlRequest(source=1, request_id=102, operation=5)
        self.assertEqual(self.lib.drms_control_submit(ctypes.byref(request)), 1)
        self.lib.drms_application_poll()
        self.frames(3, 280000, 4200000)
        self.lib.drms_user_config_r0.restype = ctypes.c_double
        self.assertEqual(self.lib.drms_user_config_r0(), 12345.0)
        self.assertEqual(self.value('drms_acq_running').value, 1)

    def test_baseline_rejects_staged_rate_different_from_sampling(self):
        body = with_baseline_policy(build_body(params=(8000, 0, 0, 0, 16000)), 3, 250, 0.01)
        self.lib.drms_user_config_apply.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_uint64]
        self.assertEqual(self.lib.drms_user_config_apply(body, len(body), 0), 0)
        request = ControlRequest(source=1, request_id=103, operation=5)
        self.assertEqual(self.lib.drms_control_submit(ctypes.byref(request)), 1)
        self.lib.drms_application_poll()
        self.frames(4, 280000, 4200000)
        self.assertEqual(self.lib.drms_user_config_r0_valid(), 0)

    def command(self, line):
        self.assertEqual(self.lib.drms_console_dispatch(line.encode()), 1)
        self.lib.drms_application_poll()

    def status(self):
        buffer = ctypes.create_string_buffer(1024)
        length = self.lib.drms_application_status(buffer, len(buffer))
        self.assertLess(length, 1023)
        return {key: int(value) for key, value in (word.split('=') for word in buffer.value.decode().split()[1:])}

    def frames(self, count, a, b):
        for i in range(count):
            self.lib.drms_acq_drdy()
            self.lib.complete_frame(a, b)
            if i % 128 == 127:
                self.lib.drms_application_poll()
        self.lib.drms_application_poll()

    def test_stop_cancels_queued_start_before_it_can_enable_excitation(self):
        # T7：开机自动监测；START 排队后被 STOP 取消，激励不得再使能
        self.assertEqual(self.lib.drms_console_dispatch(b'START'), 1)
        self.assertEqual(self.lib.drms_console_dispatch(b'STOP'), 1)
        self.lib.drms_application_poll()
        self.assertEqual(self.value('drms_acq_running').value, 0)
        self.assertGreater(self.value('command_count').value, 0)  # 开机监测已发过命令
        self.assertEqual(self.lib.pin(5), 1)  # 激励抑制

    def test_stop_cancels_control_queue_and_prevents_later_export(self):
        self.insert_card()
        request = ControlRequest(source=3, request_id=91, operation=2)
        operation = ctypes.c_uint64()
        self.lib.drms_control_submit_identified.argtypes = [ctypes.POINTER(ControlRequest), ctypes.POINTER(ctypes.c_uint64)]
        self.assertEqual(self.lib.drms_control_submit_identified(ctypes.byref(request), ctypes.byref(operation)), 1)
        self.assertEqual(self.lib.drms_console_dispatch(b'STOP'), 1)
        self.lib.drms_application_poll()
        self.lib.drms_application_poll()
        self.lib.drms_msc_service()
        self.assertEqual(self.lib.drms_msc_owner(), 0)
        from test_control_contract import Completion
        result = Completion()
        self.lib.drms_control_get_operation.argtypes = [ctypes.c_uint64, ctypes.POINTER(Completion)]
        self.assertEqual(self.lib.drms_control_get_operation(operation.value, ctypes.byref(result)), 0)
        self.assertEqual(result.result, 8)

    def test_monitor_can_restart_after_safe_stop(self):
        self.command('STOP')
        self.assertEqual(self.value('drms_acq_running').value, 0)
        self.command('START')
        self.assertEqual(self.value('drms_acq_running').value, 1)

    def test_remote_resume_restarts_only_monitoring_after_stop(self):
        self.command('STOP')
        request = ControlRequest(source=3, request_id=94, operation=10)
        operation = ctypes.c_uint64()
        self.lib.drms_control_submit_identified.argtypes = [ctypes.POINTER(ControlRequest), ctypes.POINTER(ctypes.c_uint64)]
        self.assertEqual(self.lib.drms_control_submit_identified(ctypes.byref(request), ctypes.byref(operation)), 1)
        self.lib.drms_application_poll()
        from test_control_contract import Completion
        result = Completion()
        self.lib.drms_control_get_operation.argtypes = [ctypes.c_uint64, ctypes.POINTER(Completion)]
        self.assertEqual(self.lib.drms_control_get_operation(operation.value, ctypes.byref(result)), 0)
        self.assertEqual((result.result, result.phase), (0, 2))
        self.assertEqual(self.value('drms_acq_running').value, 1)
        self.assertEqual(self.value('drms_log_state').value, 0)

    def test_remote_resume_does_not_bypass_incomplete_record_cleanup(self):
        self.insert_card()
        self.command('RECORD')
        self.lib.drms_log_poll(); self.lib.drms_application_poll(); self.lib.drms_log_poll()
        self.command('STOP')
        request = ControlRequest(source=3, request_id=95, operation=10)
        ident = ctypes.c_uint64()
        self.lib.drms_control_submit_identified.argtypes = [ctypes.POINTER(ControlRequest), ctypes.POINTER(ctypes.c_uint64)]
        self.assertEqual(self.lib.drms_control_submit_identified(ctypes.byref(request), ctypes.byref(ident)), 1)
        self.lib.drms_application_poll()
        from test_control_contract import Completion
        result = Completion()
        self.lib.drms_control_get_operation.argtypes = [ctypes.c_uint64, ctypes.POINTER(Completion)]
        self.assertEqual(self.lib.drms_control_get_operation(ident.value, ctypes.byref(result)), 0)
        self.assertEqual(result.result, 2)
        self.assertEqual(self.value('drms_acq_running').value, 0)

    def test_stop_record_waits_for_storage_cleanup_before_restart(self):
        self.insert_card()
        self.command('RECORD')
        self.lib.drms_log_poll()
        self.lib.drms_application_poll()
        self.lib.drms_log_poll()
        self.assertEqual(self.value('drms_log_running').value, 1)
        self.command('STOP')
        self.assertEqual(self.value('drms_acq_running').value, 0)
        self.command('START')
        self.assertEqual(self.value('drms_acq_running').value, 0)
        self.lib.drms_log_poll()
        self.lib.drms_application_poll()
        self.command('START')
        self.assertEqual(self.value('drms_acq_running').value, 1)

    def test_priority_stop_waits_for_record_close_before_completion(self):
        self.insert_card()
        self.command('RECORD')
        self.lib.drms_log_poll()
        self.lib.drms_application_poll()
        self.lib.drms_log_poll()
        request = ControlRequest(source=3, request_id=92)
        operation = ctypes.c_uint64()
        self.lib.drms_control_safe_stop_submit.argtypes = [ctypes.POINTER(ControlRequest), ctypes.POINTER(ctypes.c_uint64)]
        self.assertEqual(self.lib.drms_control_safe_stop_submit(ctypes.byref(request), ctypes.byref(operation)), 1)
        self.lib.drms_application_poll()
        from test_control_contract import Completion
        result = Completion()
        self.lib.drms_control_get_operation.argtypes = [ctypes.c_uint64, ctypes.POINTER(Completion)]
        self.assertEqual(self.lib.drms_control_get_operation(operation.value, ctypes.byref(result)), 0)
        self.assertEqual((result.result, result.phase), (1, 1))
        self.lib.drms_log_poll()
        self.lib.drms_application_poll()
        self.assertEqual(self.lib.drms_control_get_operation(operation.value, ctypes.byref(result)), 0)
        self.assertEqual((result.result, result.phase), (0, 2))
        self.assertEqual(self.value('drms_acq_running').value, 0)

    def test_priority_stop_timeout_keeps_stop_barrier_and_record_lease(self):
        self.insert_card()
        self.command('RECORD')
        self.lib.drms_log_poll()
        self.lib.drms_application_poll()
        self.lib.drms_log_poll()
        request = ControlRequest(source=3, request_id=93)
        operation = ctypes.c_uint64()
        self.lib.drms_control_safe_stop_submit.argtypes = [ctypes.POINTER(ControlRequest), ctypes.POINTER(ctypes.c_uint64)]
        self.assertEqual(self.lib.drms_control_safe_stop_submit(ctypes.byref(request), ctypes.byref(operation)), 1)
        self.lib.drms_application_poll()
        self.lib.advance_ms(5001)
        self.lib.drms_application_poll()
        from test_control_contract import Completion, Snapshot
        result, snapshot = Completion(), Snapshot()
        self.lib.drms_control_get_operation.argtypes = [ctypes.c_uint64, ctypes.POINTER(Completion)]
        self.assertEqual(self.lib.drms_control_get_operation(operation.value, ctypes.byref(result)), 0)
        self.assertEqual((result.result, result.phase), (7, 2))
        self.lib.drms_control_get_snapshot(ctypes.byref(snapshot))
        self.assertEqual(snapshot.stopping, 1)
        self.assertNotEqual(snapshot.reserved_mask & 4, 0)

    def test_status_reads_published_monitor_without_advancing_it(self):
        self.frames(5, 280000, 4200000)
        before = self.status()
        self.assertEqual(before['fresh'], 1)
        self.lib.advance_ms(40)
        self.assertEqual(self.status()['fresh'], 1)
        self.lib.drms_application_poll()
        self.assertEqual(self.status()['fresh'], 0)

    def test_structured_status_is_published_once_per_poll_and_marks_stale(self):
        snap = StatusSnapshot()
        self.lib.drms_application_poll()
        self.assertEqual(self.lib.drms_application_snapshot(ctypes.byref(snap)), 1)
        self.assertEqual((snap.acquisition, snap.recording, snap.medium, snap.owner), (3, 0, 0, 0))
        first = snap.revision
        self.frames(3, 280000, 4200000)
        self.assertEqual(self.lib.drms_application_snapshot(ctypes.byref(snap)), 1)
        self.assertGreater(snap.revision, first)
        self.assertEqual((snap.fresh, snap.ohms_valid), (1, 1))
        self.assertAlmostEqual(snap.ohms, 10000.0, places=2)
        self.lib.advance_ms(101)
        self.lib.drms_application_poll()
        self.lib.drms_application_snapshot(ctypes.byref(snap))
        self.assertEqual((snap.fresh, snap.ohms_valid), (0, 0))

    def test_no_baseline_does_not_show_normal_level(self):
        self.lib.advance_ms(1100)
        self.frames(1, 280000, 4200000)
        self.assertEqual(self.status()['r_valid'], 1)
        self.assertEqual(self.status()['monitor'], 0)
        self.assertEqual([self.lib.pin(pin) for pin in (8, 9, 10, 11)], [1, 1, 1, 1])

    def test_reboot_restores_baseline_and_interval_mapping(self):
        body = build_body(intervals=[(7, 2, True, 0.5, 1.0, 0.0, 'test')],
                          params=(4000, 0, 0, 0, 32000))
        self.lib.drms_user_config_apply.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_uint64]
        self.lib.drms_user_config_commit_baseline.argtypes = [ctypes.c_double, ctypes.c_uint64, ctypes.c_uint64]
        self.assertEqual(self.lib.drms_user_config_apply(body, len(body), 0), 0)
        self.assertEqual(self.lib.drms_user_config_commit_baseline(10000.0, 1, 0), 0)
        self.lib.drms_acq_stop()
        self.lib.drms_application_init()
        self.lib.advance_ms(100)
        self.frames(3, 280000, 4200000)
        status = self.status()
        self.assertEqual(status['monitor'], 5)
        self.assertEqual(status['fresh'], 1)
        self.assertEqual([self.lib.pin(pin) for pin in (8, 9, 10, 11)], [1, 1, 0, 1])
        snap = StatusSnapshot()
        self.assertEqual(self.lib.drms_application_snapshot(ctypes.byref(snap)), 1)
        self.assertEqual((snap.level_valid, snap.level, snap.interval), (1, 2, 7))

    def test_restored_sample_rate_and_baseline_dependency(self):
        body = build_body(intervals=[(7, 2, True, 0.5, 1.5, 0.0, 'test')],
                          params=(8000, 0, 0, 0, 16000))
        self.lib.drms_user_config_apply.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_uint64]
        self.lib.drms_user_config_commit_baseline.argtypes = [ctypes.c_double, ctypes.c_uint64, ctypes.c_uint64]
        self.assertEqual(self.lib.drms_user_config_apply(body, len(body), 0), 0)
        self.assertEqual(self.lib.drms_user_config_commit_baseline(10000.0, 1, 99), 0)
        self.lib.drms_acq_stop()
        self.lib.drms_application_init()
        self.assertEqual(self.status()['rate'], 8000)
        self.frames(3, 280000, 4200000)
        self.assertNotEqual(self.status()['monitor'], 5)

    def test_invalid_staleness_uses_safe_default_without_baseline(self):
        body = build_body(intervals=[(7, 2, True, 0.5, 1.5, 0.0, 'test')],
                          params=(8000, 0, 0, 0, 10000))
        self.lib.drms_user_config_apply.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_uint64]
        self.lib.drms_user_config_commit_baseline.argtypes = [ctypes.c_double, ctypes.c_uint64, ctypes.c_uint64]
        self.assertEqual(self.lib.drms_user_config_apply(body, len(body), 0), 3)
        self.lib.drms_acq_stop()
        self.lib.drms_application_init()
        self.assertEqual(self.status()['rate'], 4000)
        self.assertEqual(self.status()['config_state'], 0)
        self.frames(3, 280000, 4200000)
        self.assertNotEqual(self.status()['monitor'], 5)

    def test_nominal_resistance_and_record_mode_interlock(self):
        # T7/C3：开机已在监测；帧即时处理 → 新鲜；101ms 无 DRDY → 过期失效
        self.insert_card()
        self.frames(5, 280000, 4200000)
        self.lib.drms_application_poll()
        status = self.status()
        self.assertEqual((status['r_valid'], status['r_mohm'], status['cal']), (1, 10000000, 0))
        self.lib.advance_ms(101)
        self.lib.drms_application_poll()
        self.assertEqual(self.status()['r_valid'], 0)  # 采样停滞 → 展示失效
        self.command('RECORD')
        self.lib.drms_log_poll()
        self.lib.drms_application_poll()  # 会话就绪：文件+一致边界 B
        self.lib.drms_log_poll()
        self.assertEqual((self.value('drms_log_running').value,
                          self.value('drms_log_state').value), (1, 2))
        self.command('REF')
        self.assertEqual(self.status()['cmd_result'], 3)
        self.assertEqual(self.value('drms_acq_reference').value, 0)
        self.frames(5, 280000, 4200000)
        self.command('STOP')
        self.lib.drms_log_poll()
        self.assertEqual((self.value('drms_log_state').value, self.value('closes').value), (0, 1))

    def press_measure(self):
        ctypes.c_int.in_dll(self.lib, 'measure_down').value = 1
        self.lib.drms_application_poll()
        self.lib.advance_ms(50)
        self.lib.drms_application_poll()
        ctypes.c_int.in_dll(self.lib, 'measure_down').value = 0
        self.lib.drms_application_poll()
        self.lib.advance_ms(50)
        self.lib.drms_application_poll()

    def test_measurement_long_press_does_not_start_recording(self):
        self.insert_card()
        ctypes.c_int.in_dll(self.lib, 'measure_down').value = 1
        self.lib.drms_application_poll()
        for _ in range(21):
            self.lib.advance_ms(100)
            self.frames(1, 280000, 4200000)
        ctypes.c_int.in_dll(self.lib, 'measure_down').value = 0
        self.lib.drms_application_poll()
        self.lib.advance_ms(50)
        self.lib.drms_application_poll()
        self.lib.drms_log_poll()
        self.assertEqual(self.value('drms_log_state').value, 0)

    def test_button_held_on_boot_is_ignored_until_release(self):
        self.insert_card()
        ctypes.c_int.in_dll(self.lib, 'measure_down').value = 1
        self.lib.drms_application_init()
        for _ in range(21):
            self.lib.advance_ms(100)
            self.frames(1, 280000, 4200000)
        ctypes.c_int.in_dll(self.lib, 'measure_down').value = 0
        self.lib.drms_application_poll()
        self.lib.advance_ms(50)
        self.lib.drms_application_poll()
        self.lib.drms_log_poll()
        self.assertEqual(self.value('drms_log_state').value, 0)

    def test_power_short_waits_for_debounced_release(self):
        ctypes.c_int.in_dll(self.lib, 'power_down').value = 1
        self.lib.drms_application_poll()
        self.lib.advance_ms(50)
        self.lib.drms_application_poll()
        self.assertEqual(self.value('drms_acq_running').value, 1)
        ctypes.c_int.in_dll(self.lib, 'power_down').value = 0
        self.lib.drms_application_poll()
        self.lib.advance_ms(50)
        self.lib.drms_application_poll()
        self.assertEqual(self.value('drms_acq_running').value, 0)

    def test_measurement_button_starts_and_stops_recording(self):
        # T7：记录叠加在监测之上——按键开始/结束记录，监测不停止
        self.insert_card()
        self.press_measure()
        self.lib.drms_log_poll()
        self.lib.drms_application_poll()  # 会话归结：文件就绪+边界 B
        self.lib.drms_log_poll()
        self.assertEqual((self.status()['running'],self.status()['log']), (1,1))
        # 两次按键间隔须 ≥250 ms 去抖；期间持续有 DRDY（否则 200 ms 看门狗停采）
        for _ in range(3):
            self.lib.advance_ms(100)
            self.frames(2, 280000, 4200000)  # 累计 300 ms > 250 ms 去抖门限
        self.press_measure()
        # 停机收尾：E → END → 存储排空写卡 → 会话 ack（各轮交替推进）
        for _ in range(4):
            self.lib.drms_application_poll()
            self.lib.drms_log_poll()
        self.assertEqual((self.status()['running'],self.status()['log_state']), (1,0))

    def test_calibration_with_collapsed_current_times_out_as_calibration_failure(self):
        self.command('REF')
        self.command('CAL')
        for _ in range(101):
            self.lib.advance_ms(100)
            self.frames(1, 2000000, 3000000)  # valid SPI, but excitation below the guard
        status = self.status()
        self.assertEqual((status['cal_active'],status['cal_result'],status['cmd_result']), (0,4,4))

    def test_reference_calibration_and_save_require_stopped_acquisition(self):
        self.command('REF')
        self.command('CAL 100000000')
        self.frames(4096, 2800000, 4200000)
        status = self.status()
        self.assertEqual((status['cal'], status['cal_count'], status['cal_result'], status['cal_dirty']), (1, 4096, 0, 1))
        self.command('SAVE')
        self.assertEqual(self.status()['cmd_result'], 1)
        self.assertEqual(self.value('programs').value, 0)
        self.command('STOP')
        self.command('SAVE')
        self.assertEqual(self.status()['cmd_result'], 0)
        self.assertEqual(self.value('programs').value, 4)
        self.assertEqual(self.status()['cal_dirty'], 0)


if __name__ == '__main__':
    unittest.main()
