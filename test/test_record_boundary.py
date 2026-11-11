"""记录首末边界与完成槽测试：真实 acquisition/record_session/logging 模块联合驱动。

覆盖 C1 一致边界、T2a 三种位置验证与第四次复检启停屏障/损失隔离项。
处理循环逻辑（屏障→分类→记录→回报）按 T7 将采用的方式在测试中重现。
"""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest

from test_acquisition import Raw

ROOT = Path(__file__).resolve().parents[1]

HEADER = r'''
#ifndef MOCK_BOUNDARY_MAIN_H
#define MOCK_BOUNDARY_MAIN_H
#include <stdint.h>
#include <stddef.h>
typedef int HAL_StatusTypeDef;
/* The acquisition fast path programs the GPDMA channels and SPI registers
 * directly, so the stub models them: a channel register block plus SPI
 * registers with real bit positions. */
typedef struct { volatile uint32_t CCR,CBR1,CSAR,CDAR,CSR,CFCR; } DMA_Channel_TypeDef;
typedef struct {
  volatile uint32_t CR1,CR2,CFG1,SR,IFCR;
  volatile uint32_t TXDR,RXDR;
} SPI_TypeDef;
typedef struct { DMA_Channel_TypeDef *Instance; } mock_dma_link_t;
typedef struct {
  SPI_TypeDef *Instance;
  struct { unsigned int DataSize,CLKPolarity,CLKPhase,FirstBit,Mode,NSS; } Init;
  mock_dma_link_t *hdmarx, *hdmatx;
  unsigned long State;
  uint32_t ErrorCode;
} SPI_HandleTypeDef;
typedef struct { volatile uint32_t BSRR; } mock_gpio_t;
typedef struct { volatile uint32_t CYCCNT; } DWT_TypeDef;
extern mock_gpio_t mock_gpio_a;
extern DWT_TypeDef mock_dwt;
#define DWT (&mock_dwt)
#define DMA_CCR_EN 0x00000001UL
#define DMA_CCR_TCIE 0x00000002UL
#define DMA_CCR_HTIE 0x00000004UL
#define DMA_CCR_DTEIE 0x00000008UL
#define SPI_CR1_SPE 0x00000001UL
#define SPI_CR1_CSTART 0x00000200UL
#define SPI_CR2_TSIZE 0x0000FFFFUL
#define SPI_CFG1_TXDMAEN 0x00008000UL
#define SPI_CFG1_RXDMAEN 0x00004000UL
#define SPI_IFCR_OVRC 0x00000040UL
#define SPI_IFCR_UDRC 0x00000020UL
#define SPI_IFCR_EOTC 0x00000008UL
#define SPI_IFCR_TXTFC 0x00000010UL
#define SPI_IFCR_SUSPC 0x00000400UL
#define SPI_IFCR_MODFC 0x00000080UL
#define DMA_FLAG_TC 0x00000001UL
#define DMA_FLAG_HT 0x00000002UL
#define DMA_FLAG_DTE 0x00000004UL
#define DMA_FLAG_ULE 0x00000008UL
#define DMA_FLAG_USE 0x00000010UL
#define DMA_FLAG_SUSP 0x00000020UL
#define DMA_FLAG_TO 0x00000040UL
#define __HAL_SPI_ENABLE(h) ((h)->Instance->CR1 |= SPI_CR1_SPE)
#define __HAL_SPI_DISABLE(h) ((h)->Instance->CR1 &= ~SPI_CR1_SPE)
#define __HAL_SPI_CLEAR_SUSPFLAG(h) ((h)->Instance->IFCR |= SPI_IFCR_SUSPC)
#define __HAL_UNLOCK(h) ((void)0)
#define HAL_SPI_STATE_READY 0x01UL
#define HAL_SPI_STATE_BUSY_TX_RX 0x05UL
#define HAL_SPI_ERROR_NONE 0
#define SET_BIT(r,m) ((r) |= (m))
#define CLEAR_BIT(r,m) ((r) &= ~(m))
#define MODIFY_REG(reg,clr,set) ((reg) = (((reg) & ~(clr)) | (set)))
#define SPI_DATASIZE_8BIT 7
#define SPI_POLARITY_LOW 0
#define SPI_PHASE_2EDGE 1
#define SPI_FIRSTBIT_MSB 0
#define SPI_MODE_MASTER 1
#define SPI_NSS_SOFT 1
extern SPI_HandleTypeDef hspi1;
#define HAL_OK 0
#define GPIO_PIN_RESET 0
#define GPIO_PIN_SET 1
#define ADS_CS_GPIO_Port (&mock_gpio_a)
#define ADS_CS_Pin 0x0020UL
#define CURR_DIS_GPIO_Port 0
#define CURR_DIS_Pin 5
#define ADS_RESET_GPIO_Port 0
#define ADS_RESET_Pin 2
#define ANA_EN_GPIO_Port 0
#define ANA_EN_Pin 3
#define SEL_SENSE_GPIO_Port 0
#define SEL_SENSE_Pin 6
#define SEL_K2_GPIO_Port 0
#define SEL_K2_Pin 7
#define __NOP() ((void)0)
#define __get_PRIMASK() ((uint32_t)0)
#define __disable_irq() ((void)0)
#define __set_PRIMASK(m) ((void)(m))
void HAL_GPIO_WritePin(int,int,int);
uint32_t HAL_GetTick(void);
void HAL_Delay(uint32_t);
int HAL_SPI_TransmitReceive(SPI_HandleTypeDef *,uint8_t *,uint8_t *,uint16_t,uint32_t);
int HAL_SPI_TransmitReceive_DMA(SPI_HandleTypeDef *,uint8_t *,uint8_t *,uint16_t);
int HAL_SPI_Abort(SPI_HandleTypeDef *);
#endif
'''

FX_HEADER = r'''
#ifndef MOCK_BOUNDARY_FX_H
#define MOCK_BOUNDARY_FX_H
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
#endif
'''

MOCK = r'''
#include "main.h"
#include "app_filex.h"
#include "drms_logging.h"
#include "drms_measurement.h"
#include <string.h>
static SPI_TypeDef mock_spi1;
static DMA_Channel_TypeDef mock_rx_ch, mock_tx_ch;
static mock_dma_link_t rx_link={&mock_rx_ch}, tx_link={&mock_tx_ch};
SPI_HandleTypeDef hspi1={.Instance=&mock_spi1,.Init={SPI_DATASIZE_8BIT,SPI_POLARITY_LOW,SPI_PHASE_2EDGE,SPI_FIRSTBIT_MSB,SPI_MODE_MASTER,SPI_NSS_SOFT},.hdmarx=&rx_link,.hdmatx=&tx_link};
DWT_TypeDef mock_dwt;
mock_gpio_t mock_gpio_a;
/* Exposed by the firmware so this host can find the armed receive buffer: the
 * register holds only the low 32 bits of the address on a 64-bit host. */
uint8_t *drms_acq_test_rx_buffer(void);
int drms_acq_fast_dma_irq(void);
FX_MEDIA sdio_disk;
volatile unsigned int drms_storage_mounted=1,drms_storage_status;
uint32_t drms_msc_blocks_recording(void) { return 0; }
uint8_t file_bytes[1048576];
uint32_t written_bytes,writes,closes,flushes,invalidates,creates,fail_at,ticks;
static uint16_t response=0xff02;
static int fixed,unlocked;
static uint8_t *rx_buffer;
unsigned int dma_error,bad_crc;
/* Mirror the old injected DMA-start failure onto the new fast path: arming the
 * receive channel beforehand trips its busy guard, which is the same "capture
 * lost" outcome the HAL stub used to produce. */
void mock_inject_dma_failure(int on) { if(on) mock_rx_ch.CCR|=DMA_CCR_EN; else mock_rx_ch.CCR&=~DMA_CCR_EN; }
void HAL_GPIO_WritePin(int port,int pin,int state) { if(pin==2 && !state){fixed=0;unlocked=0;response=0xff02;} }
uint32_t HAL_GetTick(void) { return ticks; }
void HAL_Delay(uint32_t ms) { ticks+=ms; }
int HAL_SPI_TransmitReceive(SPI_HandleTypeDef *s,uint8_t *tx,uint8_t *rx,uint16_t n,uint32_t t) {
 if(fixed){uint16_t crc=drms_crc16(rx,9);rx[9]=crc>>8;rx[10]=crc&255;}
 memset(rx,0,n);rx[0]=response>>8;rx[1]=response&255;
 uint16_t command=(tx[0]<<8)|tx[1];
 if(command==0x0655){unlocked=1;response=command;}
 else if((command&0xe000)==0x4000){response=command-0x2000;if((command&0xff00)==0x4c00)fixed=1;}
 else if(command)response=command;
 else response=unlocked?0x2200:0xff02;
 if(fixed){uint16_t crc=drms_crc16(rx,9);rx[9]=crc>>8;rx[10]=crc&255;}
 return 0;
}
int HAL_SPI_TransmitReceive_DMA(SPI_HandleTypeDef *s,uint8_t *tx,uint8_t *rx,uint16_t n) {
 if(dma_error) return 1; /* HAL busy → DMA 启动失败 = 捕获损失 */
 rx_buffer=rx;return 0;
}
int HAL_SPI_Abort(SPI_HandleTypeDef *s) { return 0; }
void HAL_SPI_TxRxCpltCallback(SPI_HandleTypeDef *);
/* Simulate a completed exchange: the DMA has filled the buffer the fast path
 * armed, the receive channel reports TC, and the GPDMA1 channel 1 interrupt
 * consumes it. */
void complete_frame(void) {
 uint8_t *dst=drms_acq_test_rx_buffer();
 if(!dst) return;
 memset(dst,0,12);dst[0]=0x22;
 dst[3]=0x1e;dst[4]=0x84;dst[5]=0x80;   /* 2000000 */
 dst[6]=0x40;dst[7]=0x0c;dst[8]=0xe0;   /* 4200000 */
 if(bad_crc) dst[3]^=1;
 else {uint16_t crc=drms_crc16(dst,9);dst[9]=crc>>8;dst[10]=crc&255;}
 mock_rx_ch.CSR|=DMA_FLAG_TC;
 (void)drms_acq_fast_dma_irq();
}
UINT fx_file_create(FX_MEDIA *m,char *name) { ++creates;return 0; }
UINT fx_file_open(FX_MEDIA *m,FX_FILE *f,char *name,UINT mode) { return 0; }
UINT fx_file_write(FX_FILE *f,void *p,ULONG n) {
 ++writes;if(writes==fail_at) return 1;
 if(written_bytes+n>sizeof(file_bytes)) return 1;
 memcpy(file_bytes+written_bytes,p,n);written_bytes+=n;return 0;
}
UINT fx_file_close(FX_FILE *f) { ++closes;return 0; }
UINT fx_media_flush(FX_MEDIA *m) { ++flushes;return 0; }
void drms_storage_invalidate(void) { ++invalidates;drms_storage_mounted=0;drms_log_removed(); }
'''

OK, ACCEPTED, BUSY, INVALID, STALE = 0, 1, 2, 3, 4
NO_CHANGE, IO_ERROR, TIMEOUT, CANCELLED, INCOMPLETE = 5, 6, 7, 8, 9
EMPTY = 12
SKIP, MONITOR, RECORD = 0, 1, 2


class Token(ctypes.Structure):
    _fields_ = [('operation_id', ctypes.c_uint64), ('generation', ctypes.c_uint32)]


class Position(ctypes.Structure):
    _fields_ = [('generation', ctypes.c_uint32), ('index', ctypes.c_uint64)]


class Boundary(ctypes.Structure):
    _fields_ = [('acquisition_generation', ctypes.c_uint32), ('sample_next', ctypes.c_uint64),
                ('raw_next', ctypes.c_uint64), ('capture_lost_total', ctypes.c_uint64),
                ('unknown_loss_epoch', ctypes.c_uint64)]


class End(ctypes.Structure):
    _fields_ = [('token', Token), ('record_id', ctypes.c_uint64), ('ring_end', ctypes.c_uint64),
                ('lost_count', ctypes.c_uint64), ('first', Position),
                ('end_exclusive', Position), ('last_confirmed', Position),
                ('end_known', ctypes.c_bool), ('capture_lost', ctypes.c_uint64),
                ('log_dropped', ctypes.c_uint64), ('quality_bad', ctypes.c_uint64),
                ('unknown_loss', ctypes.c_bool), ('storage_error', ctypes.c_bool),
                ('reason', ctypes.c_int)]


class Metadata(ctypes.Structure):
    _fields_ = [('rate', ctypes.c_uint32), ('calibrated', ctypes.c_uint32),
                ('calibration_generation', ctypes.c_uint32), ('start_ticks', ctypes.c_uint32),
                ('serial', ctypes.c_uint32), ('scale', ctypes.c_double),
                ('reference_ohms', ctypes.c_double), ('year', ctypes.c_uint16),
                *[(name, ctypes.c_ubyte) for name in ('month', 'day', 'hour', 'minute', 'second', 'time_valid')]]


class Sample(ctypes.Structure):
    _fields_ = [('voltage', ctypes.c_int32), ('sense', ctypes.c_int32),
                ('status', ctypes.c_uint16), ('flags', ctypes.c_uint16)]


class Snapshot(ctypes.Structure):
    _fields_ = [('state', ctypes.c_uint32), ('barrier', ctypes.c_uint32),
                ('stop_pending', ctypes.c_uint32), ('acquisition_generation', ctypes.c_uint32),
                ('record_id', ctypes.c_uint64), ('token', Token),
                ('samples_recorded', ctypes.c_uint64), ('quality_bad', ctypes.c_uint64),
                ('log_dropped', ctypes.c_uint64), ('capture_lost', ctypes.c_uint64),
                ('unknown_loss', ctypes.c_uint32), ('end_pending', ctypes.c_uint32),
                ('end_reason', ctypes.c_int)]


class BoundaryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        p = Path(cls.tmp.name)
        (p / 'main.h').write_text(HEADER)
        (p / 'spi.h').write_text('#include "main.h"')
        (p / 'app_filex.h').write_text(FX_HEADER)
        (p / 'mock.c').write_text(MOCK)
        src = ROOT / 'firmware/DE-DRMS-Code/Core'
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Werror=implicit-function-declaration',
                        '-I', str(p), '-I', str(src / 'Inc'),
                        *[str(src / f'Src/drms_{name}.c') for name in
                          ('acquisition', 'record_session', 'logging', 'log_codec', 'fifo', 'measurement', 'capture_time')],
                        str(p / 'mock.c'), '-o', str(p / 'boundary.so')], check=True)
        cls.lib = ctypes.CDLL(str(p / 'boundary.so'))
        lib = cls.lib
        lib.drms_acq_boundary_request.argtypes = [Token]
        lib.drms_acq_boundary_get.argtypes = [Token, ctypes.POINTER(Boundary)]
        lib.drms_record_prepare.argtypes = [Token, ctypes.c_uint64]
        lib.drms_record_ready.argtypes = [Token, Boundary]   # C 按值结构体
        lib.drms_record_stop_at.argtypes = [Token, Boundary]
        lib.drms_record_end_get.argtypes = [ctypes.POINTER(End)]
        lib.drms_record_end_ack.argtypes = [Token, ctypes.c_int]
        lib.drms_record_session_classify.argtypes = [ctypes.c_uint64]
        lib.drms_record_session_note_consumed.argtypes = [ctypes.c_uint64]
        lib.drms_record_session_note_log_ticket.argtypes = [ctypes.c_uint64]
        lib.drms_record_session_poll.argtypes = [ctypes.c_uint64, ctypes.c_uint32, ctypes.c_uint32]
        lib.drms_record_session_note_recorded.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
        lib.drms_log_enqueue.argtypes = [ctypes.POINTER(Raw)]
        lib.drms_log_start.argtypes = [ctypes.POINTER(Metadata)]
        cls.dma_error_cell = ctypes.c_uint.in_dll(lib, 'dma_error')
        cls.bad_crc_cell = ctypes.c_uint.in_dll(lib, 'bad_crc')
        lib.drms_decode_frame.argtypes = [ctypes.POINTER(Raw), ctypes.POINTER(Sample)]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        lib = self.lib
        lib.drms_record_session_init()
        lib.drms_log_init()
        lib.drms_acq_stop()
        lib.drms_acq_start(4000, 0)
        self.loop = Loop(lib)
        self.token_counter = 100
        self.metadata = Metadata(rate=4000, scale=150000., reference_ohms=100000.)

    def u32(self, name):
        return ctypes.c_uint32.in_dll(self.lib, name)

    def snapshot(self):
        snap = Snapshot()
        self.lib.drms_record_session_get_snapshot(ctypes.byref(snap))
        return snap

    def next_token(self):
        self.token_counter += 1
        return Token(self.token_counter, 1)

    def gen(self):
        return self.lib.drms_acq_generation()

    def capture(self):
        token = self.next_token()
        self.assertEqual(self.lib.drms_acq_boundary_request(token), ACCEPTED)
        self.lib.drms_acq_boundary_service()
        out = Boundary()
        result = self.lib.drms_acq_boundary_get(token, ctypes.byref(out))
        return result, out

    def ready_session(self, token):
        """存储就绪（FileX mock）→ 捕获 B → ready。"""
        # 上一会话文件收尾（无文件时为无操作），随后建立新文件
        self.lib.drms_log_stop()
        self.lib.drms_log_poll()
        self.assertEqual(self.lib.drms_log_start(ctypes.byref(self.metadata)), 1)
        self.lib.drms_log_poll()
        self.assertEqual(self.u32('drms_log_running').value, 1)
        result, boundary = self.capture()
        self.assertEqual(result, OK)
        self.assertEqual(self.lib.drms_record_ready(token, boundary), OK)
        return boundary

    def start_record(self):
        """prepare → sync → ready。返回 token。"""
        token = self.next_token()
        self.assertEqual(self.lib.drms_record_prepare(token, self.token_counter), ACCEPTED)
        self.loop.sync()
        boundary = self.ready_session(token)
        return token, boundary

    def stop_record(self, token):
        """request_stop → 捕获 E → stop_at。返回 (E, stop_at 返回值)。"""
        self.lib.drms_record_session_request_stop()
        result, boundary = self.capture()
        self.assertEqual(result, OK)
        rc = self.lib.drms_record_stop_at(token, boundary)
        return boundary, rc

    def end(self):
        out = End()
        result = self.lib.drms_record_end_get(ctypes.byref(out))
        return result, out

    def produce(self, count, lost=False, bad_crc=False):
        for _ in range(count):
            type(self).dma_error_cell.value = 1 if lost else 0
            type(self).bad_crc_cell.value = 1 if bad_crc else 0
            self.lib.mock_inject_dma_failure(1 if lost else 0)
            self.lib.drms_acq_drdy()
            if not lost:
                self.lib.complete_frame()
        type(self).dma_error_cell.value = 0
        type(self).bad_crc_cell.value = 0
        self.lib.mock_inject_dma_failure(0)


class Loop:
    """处理循环替身：屏障→pop→classify→记录/监测→回报（T7 将按此接线）。"""

    def __init__(self, lib):
        self.lib = lib
        self.consumed = 0

    def sync(self):
        # prepare 后向会话同步消费水位（生产循环职责，T7 同此）
        self.lib.drms_record_session_note_consumed(self.consumed)

    def round(self, budget=4096):
        lib = self.lib
        if lib.drms_record_session_barrier():
            return 0
        recorded = 0
        frame = Raw()
        sample = Sample()
        for _ in range(budget):
            if not lib.drms_acq_pop(ctypes.byref(frame)):
                lib.drms_record_session_note_consumed(self.consumed)
                break
            verdict = lib.drms_record_session_classify(self.consumed)
            if verdict == RECORD:
                ok = lib.drms_log_enqueue(ctypes.byref(frame))
                lib.drms_decode_frame(ctypes.byref(frame), ctypes.byref(sample))
                lib.drms_record_session_note_recorded(frame.sequence,
                                                      1 if sample.flags & 1 else 0,
                                                      1 if ok else 0)
                lib.drms_record_session_note_log_ticket(lib.drms_log_ticket_next())
                recorded += 1
            self.consumed += 1
            lib.drms_record_session_note_consumed(self.consumed)
        return recorded


class RecordWindowTest(BoundaryTest):
    def test_start_boundary_excludes_backlog_and_records_window(self):
        self.produce(110)
        self.assertEqual(self.loop.round(budget=100), 0)  # 监测期仅消费
        self.assertEqual(self.loop.consumed, 100)
        token, begin = self.start_record()
        self.assertEqual((begin.sample_next, begin.raw_next), (110, 110))
        self.produce(10)  # 110..119
        # 积压 100..109 属 SKIP，不进入记录；110..119 属 RECORD
        self.assertEqual(self.loop.round(), 10)
        end_boundary, rc = self.stop_record(token)
        self.assertEqual(rc, OK)
        self.assertEqual(self.loop.round(), 0)  # 消费已越过 E
        result, out = self.end()
        self.assertEqual(result, OK)
        self.assertEqual((out.first.generation, out.first.index), (self.gen(), 110))
        self.assertEqual((out.end_exclusive.generation, out.end_exclusive.index), (self.gen(), 120))
        self.assertEqual(out.capture_lost, 0)
        self.assertEqual(out.reason, OK)
        self.assertEqual(out.ring_end, 10)
        self.assertEqual(out.end_known, 1)
        self.assertEqual(self.snapshot().state, 3)  # END 已发布：FINALIZING
        # E 后帧只监测
        self.produce(1)
        self.assertEqual(self.loop.round(), 0)
        self.lib.drms_record_end_ack(token, OK)
        self.assertEqual(self.snapshot().state, 0)

    def test_stop_with_unprocessed_frames_records_them_all(self):
        self.produce(100)
        self.loop.round()
        token, begin = self.start_record()
        self.assertEqual(begin.raw_next, 100)
        self.produce(50)  # 100..149 已发布但未消费
        end_boundary, rc = self.stop_record(token)
        self.assertEqual(rc, OK)
        self.assertEqual((end_boundary.raw_next, end_boundary.sample_next), (150, 150))
        # 屏障结束后消费：边界前数据一个不漏
        self.assertEqual(self.loop.round(), 50)
        result, out = self.end()
        self.assertEqual(result, OK)
        self.assertEqual((out.first.index, out.end_exclusive.index), (100, 150))
        self.assertEqual(out.capture_lost, 0)
        self.assertEqual(out.reason, OK)
        self.assertEqual(out.ring_end, 50)

    def test_delayed_stop_boundary_reply_consumer_never_crosses_end(self):
        self.produce(100)
        self.loop.round()
        token, begin = self.start_record()
        self.produce(10)  # 100..109 已发布未消费
        self.lib.drms_record_session_request_stop()
        self.assertEqual(self.snapshot().barrier, 1)
        reply_token = self.next_token()
        self.assertEqual(self.lib.drms_acq_boundary_request(reply_token), ACCEPTED)
        # 延迟回复期间生产者继续（110..114），消费者不得越过最终 E
        self.produce(5)
        self.assertEqual(self.loop.round(), 0)
        self.assertEqual(self.loop.consumed, 100)
        # 第一帧完成回调已自动 service：E = 100..110（含 110）
        boundary = Boundary()
        self.assertEqual(self.lib.drms_acq_boundary_get(reply_token, ctypes.byref(boundary)), OK)
        self.assertEqual(boundary.raw_next, 111)
        self.assertEqual(self.lib.drms_record_stop_at(token, boundary), OK)
        self.assertEqual(self.loop.round(), 11)  # 100..110 全部入记录
        result, out = self.end()
        self.assertEqual((out.first.index, out.end_exclusive.index), (100, 111))
        self.assertEqual(self.loop.consumed, 115)  # E 后 111..114 已消费为监测
        self.produce(4)  # 111..114：E 后仅监测
        self.assertEqual(self.loop.round(), 0)
        result, out2 = self.end()
        self.assertEqual(out2.ring_end, 11)  # END 已冻结，不被 E 后数据修改

    def test_repeated_stop_keeps_first_end_boundary(self):
        self.produce(100)
        self.loop.round()
        token, _ = self.start_record()
        self.produce(5)
        end1, rc = self.stop_record(token)
        self.assertEqual(rc, OK)
        later = Boundary(acquisition_generation=self.gen(), sample_next=500, raw_next=500,
                         capture_lost_total=0, unknown_loss_epoch=0)
        self.assertEqual(self.lib.drms_record_stop_at(token, later), NO_CHANGE)
        self.assertEqual(self.loop.round(), 5)  # 排空到 E 后才发布 END
        result, out = self.end()
        self.assertEqual(result, OK)
        self.assertEqual(out.end_exclusive.index, end1.sample_next)  # 首次 E 保持


class SessionLifecycleTest(BoundaryTest):
    def test_starting_cancel_publishes_end_and_late_ready_is_stale(self):
        token = self.next_token()
        self.assertEqual(self.lib.drms_record_prepare(token, 7), ACCEPTED)
        self.lib.drms_record_session_cancel(token, CANCELLED)
        result, out = self.end()
        self.assertEqual(result, OK)
        self.assertEqual(out.reason, CANCELLED)
        self.assertEqual(out.end_known, 0)
        self.assertEqual(out.record_id, 7)
        # 迟到 READY 不得转为 RECORDING
        boundary = Boundary(acquisition_generation=self.gen(), sample_next=10, raw_next=10,
                            capture_lost_total=0, unknown_loss_epoch=0)
        self.assertEqual(self.lib.drms_record_ready(token, boundary), STALE)
        self.assertEqual(self.snapshot().state, 3)  # FINALIZING
        self.lib.drms_record_end_ack(token, OK)
        self.assertEqual(self.snapshot().state, 0)

    def test_two_consecutive_sessions_with_fresh_tokens(self):
        token1, _ = self.start_record()  # 空采集起点：B1=(0,0)
        self.produce(5)
        self.loop.round()
        end_boundary, rc = self.stop_record(token1)
        self.assertEqual(rc, OK)
        self.loop.round()
        result, out1 = self.end()
        self.assertEqual(out1.record_id, 101)
        # 未 ack 前不得开启下一次记录
        token2 = self.next_token()
        self.assertEqual(self.lib.drms_record_prepare(token2, 202), BUSY)
        self.assertEqual(self.lib.drms_record_end_ack(token1, OK), OK)
        self.assertEqual(self.lib.drms_record_prepare(token2, 202), ACCEPTED)
        self.assertEqual(self.lib.drms_record_end_ack(token1, OK), EMPTY)  # 槽已释放
        self.loop.sync()
        self.ready_session(token2)
        self.produce(3)
        self.loop.round()
        end2, rc = self.stop_record(token2)
        self.assertEqual(rc, OK)
        self.loop.round()
        result, out2 = self.end()
        self.assertEqual(out2.record_id, 202)
        # 会话2窗口 = 会话1之后的连续 raw 流位置 [5,8)
        self.assertEqual((out2.first.index, out2.end_exclusive.index), (5, 8))

    def test_end_slot_requires_matching_ack(self):
        out = End()
        self.assertEqual(self.lib.drms_record_end_get(ctypes.byref(out)), EMPTY)
        token, _ = self.start_record()
        self.produce(3)
        self.loop.round()
        _, rc = self.stop_record(token)
        self.assertEqual(rc, OK)
        self.loop.round()
        self.assertEqual(self.lib.drms_record_end_get(None), INVALID)
        result, out = self.end()
        self.assertEqual(result, OK)
        wrong = Token(out.token.operation_id + 1, out.token.generation)
        self.assertEqual(self.lib.drms_record_end_ack(wrong, OK), STALE)
        self.assertEqual(self.snapshot().end_pending, 1)
        self.assertEqual(self.lib.drms_record_end_ack(token, OK), OK)
        self.assertEqual(self.snapshot().end_pending, 0)


class BoundarySemanticsTest(BoundaryTest):
    def test_loss_attribution_100_to_109_with_missing_102(self):
        self.produce(100)
        self.loop.round()
        token, begin = self.start_record()
        self.assertEqual((begin.capture_lost_total, begin.sample_next), (0, 100))
        self.produce(2)            # 100,101
        self.produce(1, lost=True)  # 102 未读出：raw_ticket 不增加
        self.produce(6)            # 103..108
        self.produce(1, bad_crc=True)  # 109：CRC 坏帧已发布
        self.assertEqual(self.loop.round(), 9)
        self.assertEqual(self.snapshot().quality_bad, 1)  # 独立计数
        end_boundary, rc = self.stop_record(token)
        self.assertEqual(rc, OK)
        # 三种位置分别断言：sample 跨 10、raw 跨 9、log 9
        self.assertEqual(end_boundary.sample_next - begin.sample_next, 10)
        self.assertEqual(end_boundary.raw_next - begin.raw_next, 9)
        result, out = self.end()
        self.assertEqual(out.capture_lost, 1)   # 坏帧不重复计 capture_lost
        self.assertEqual(out.quality_bad, 1)
        self.assertEqual(out.reason, INCOMPLETE)
        self.assertEqual(out.first.index, 100)
        self.assertEqual(out.end_exclusive.index, 110)
        # E 后丢样不修改已冻结 END
        self.produce(2, lost=True)
        result, out2 = self.end()
        self.assertEqual(out2.capture_lost, 1)
        self.assertEqual(out2.quality_bad, 1)
        self.assertEqual(out2.reason, INCOMPLETE)

    def test_pre_start_loss_not_attributed_to_session(self):
        self.produce(7, lost=True)  # 监测期损失
        self.produce(93)
        self.assertEqual(self.lib.drms_acq_capture_lost_total(), 7)
        self.loop.round()
        token, begin = self.start_record()
        self.assertEqual(begin.capture_lost_total, 7)
        self.produce(10)
        self.loop.round()
        end_boundary, rc = self.stop_record(token)
        self.assertEqual(rc, OK)
        self.assertEqual(end_boundary.capture_lost_total, 7)  # B=7, E=7
        result, out = self.end()
        self.assertEqual(out.capture_lost, 0)
        self.assertEqual(out.reason, OK)

    def test_loss_inside_window_attributed_by_boundary_delta(self):
        self.produce(100)
        self.loop.round()
        token, begin = self.start_record()
        self.produce(2, lost=True)  # B=7 之后两个未读出
        self.produce(8)
        self.loop.round()
        end_boundary, rc = self.stop_record(token)
        self.assertEqual(rc, OK)
        self.assertEqual(end_boundary.capture_lost_total, 2)  # B=0, E=2
        self.assertEqual(self.snapshot().samples_recorded, 8)
        result, out = self.end()
        self.assertEqual(out.capture_lost, 2)
        self.assertEqual(out.reason, INCOMPLETE)

    def test_empty_record_rules(self):
        # B==E 且无损失 → EMPTY
        self.produce(100)
        self.loop.round()
        token, begin = self.start_record()
        self.lib.drms_record_session_request_stop()
        end_boundary = Boundary(acquisition_generation=self.gen(), sample_next=100,
                                raw_next=100, capture_lost_total=0, unknown_loss_epoch=0)
        self.assertEqual(self.lib.drms_record_stop_at(token, end_boundary), OK)
        result, out = self.end()
        self.assertEqual(result, OK)
        self.assertEqual(out.reason, EMPTY)
        self.assertEqual(out.first.index, out.end_exclusive.index)
        self.lib.drms_record_end_ack(token, OK)
        # 有采样但全部丢失 → INCOMPLETE
        self.setUp()
        self.produce(100)
        self.loop.round()
        token, begin = self.start_record()
        self.produce(3, lost=True)
        end_boundary, rc = self.stop_record(token)
        self.assertEqual(rc, OK)
        result, out = self.end()
        self.assertEqual(out.reason, INCOMPLETE)
        self.assertEqual(out.capture_lost, 3)
        self.assertEqual(out.end_exclusive.index, 103)

    def test_first_frame_missing_does_not_move_begin(self):
        self.produce(100)
        self.loop.round()
        token, begin = self.start_record()
        self.produce(2, lost=True)  # 首两帧缺失
        self.produce(3)             # 102..104
        self.loop.round()
        end_boundary, rc = self.stop_record(token)
        self.assertEqual(rc, OK)
        result, out = self.end()
        self.assertEqual(out.first.index, 100)  # 不得移动 B 伪装成功
        self.assertEqual(out.capture_lost, 2)
        self.assertEqual(out.reason, INCOMPLETE)
        self.assertEqual(out.last_confirmed.index, 104)

    def test_inflight_dma_resolved_before_boundary(self):
        self.lib.drms_acq_drdy()  # DMA 在途
        token = self.next_token()
        self.assertEqual(self.lib.drms_acq_boundary_request(token), ACCEPTED)
        self.lib.drms_acq_boundary_service()  # busy → 不发布
        out = Boundary()
        self.assertEqual(self.lib.drms_acq_boundary_get(token, ctypes.byref(out)), EMPTY)
        self.lib.complete_frame()  # 归结后在静止时刻发布
        self.assertEqual(self.lib.drms_acq_boundary_get(token, ctypes.byref(out)), OK)
        self.assertEqual(out.raw_next, 1)
        self.assertEqual(out.sample_next, 1)

    def test_boundary_generation_mismatch_rejected_then_timeout(self):
        self.lib.drms_record_session_configure(100)
        self.produce(100)
        self.loop.round()
        token, begin = self.start_record()
        self.produce(3)
        self.loop.round()
        self.lib.drms_record_session_request_stop()
        self.produce(2)
        result, end_boundary = self.capture()
        end_boundary.acquisition_generation = 2  # 跨代次边界
        self.assertEqual(self.lib.drms_record_stop_at(token, end_boundary), STALE)
        self.assertEqual(self.snapshot().barrier, 1)  # 屏障未解除，等待继续
        # 等待期限到达：不猜测边界，INCOMPLETE 收尾（TIMEOUT 原因）
        self.lib.drms_record_session_poll(0, 5, 4096)
        self.lib.drms_record_session_poll(100, 5, 4096)
        snap = self.snapshot()
        self.assertEqual(snap.state, 3)
        result, out = self.end()
        self.assertEqual(out.reason, TIMEOUT)
        self.assertEqual(out.end_known, 0)
        self.assertEqual(out.last_confirmed.index, 102)
        # 迟到回复只能清理，不重新开放记录入口
        good = Boundary(acquisition_generation=1, sample_next=105, raw_next=105,
                        capture_lost_total=0, unknown_loss_epoch=0)
        self.assertEqual(self.lib.drms_record_ready(token, good), STALE)
        self.lib.drms_record_end_ack(token, OK)

    def test_boundary_wait_timeout_at_start(self):
        self.lib.drms_record_session_configure(50)
        token = self.next_token()
        self.assertEqual(self.lib.drms_record_prepare(token, 1), ACCEPTED)
        self.lib.drms_record_session_poll(0, 0, 4096)   # 设定截止
        self.lib.drms_record_session_poll(49, 0, 4096)  # 仍等待
        self.assertEqual(self.snapshot().state, 1)      # STARTING
        self.lib.drms_record_session_poll(50, 0, 4096)  # 期限到达
        result, out = self.end()
        self.assertEqual(out.reason, TIMEOUT)
        self.assertEqual(out.end_known, 0)
        boundary = Boundary(acquisition_generation=1, sample_next=1, raw_next=1,
                            capture_lost_total=0, unknown_loss_epoch=0)
        self.assertEqual(self.lib.drms_record_ready(token, boundary), STALE)

    def test_raw_ring_full_during_barrier_fails_record(self):
        self.produce(100)
        self.loop.round()
        token, begin = self.start_record()
        self.lib.drms_record_session_request_stop()
        self.lib.drms_record_session_poll(0, 0, 4096)
        # 屏障期间不消费，生产者灌满原始环（4096）
        produced_drops = False
        for _ in range(4200):
            self.lib.drms_acq_drdy()
            self.lib.complete_frame()
            if self.u32('drms_acq_queue_drops').value:
                produced_drops = True
                break
        self.assertTrue(produced_drops)
        used = self.lib.drms_acq_raw_ticket_next() - self.loop.consumed
        self.lib.drms_record_session_poll(1, used, 4096)
        result, out = self.end()
        self.assertEqual(out.reason, INCOMPLETE)
        self.assertEqual(out.end_known, 0)  # 未取得一致 E：不写伪精确末边界
        self.assertEqual(out.unknown_loss, 1)  # 尾部连续性不可证明


class SequenceExtensionTest(BoundaryTest):
    def inject_session(self, first_sample):
        token = self.next_token()
        self.assertEqual(self.lib.drms_record_prepare(token, 1), ACCEPTED)
        begin = Boundary(acquisition_generation=1, sample_next=first_sample, raw_next=0,
                         capture_lost_total=0, unknown_loss_epoch=0)
        self.assertEqual(self.lib.drms_record_ready(token, begin), OK)
        return token

    def finish_with_last(self, token, end_sample, raw_next):
        self.lib.drms_record_session_request_stop()
        end_boundary = Boundary(acquisition_generation=1, sample_next=end_sample,
                                raw_next=raw_next, capture_lost_total=0,
                                unknown_loss_epoch=0)
        self.assertEqual(self.lib.drms_record_stop_at(token, end_boundary), OK)
        self.lib.drms_record_session_note_consumed(raw_next)
        result, out = self.end()
        return result, out

    def test_low_32bit_sequence_wraparound_extends_in_order(self):
        token = self.inject_session(0xFFFFFFFE)
        self.lib.drms_record_session_note_recorded(0xFFFFFFFF, 0, 1)
        self.lib.drms_record_session_note_recorded(0x00000000, 0, 1)
        result, out = self.finish_with_last(token, 0x100000001, 2)
        self.assertEqual(result, OK)
        self.assertEqual(out.first.index, 0xFFFFFFFE)
        self.assertEqual(out.last_confirmed.index, 0x100000000)
        self.assertEqual(out.end_exclusive.index, 0x100000001)
        self.assertEqual(out.unknown_loss, 0)

    def test_unprovable_span_marks_unknown_loss_and_ends_record(self):
        token = self.inject_session(0)
        self.lib.drms_record_session_note_recorded(1, 0, 1)
        # 下一帧低 32 位序号 implying ≥2^31 距离：不可证明
        self.lib.drms_record_session_note_recorded(0x80000001, 0, 1)
        snap = self.snapshot()
        self.assertEqual(snap.unknown_loss, 1)
        self.assertEqual(snap.state, 3)  # 已收尾
        result, out = self.end()
        self.assertEqual(out.reason, INCOMPLETE)
        self.assertEqual(out.unknown_loss, 1)
        self.assertEqual(out.last_confirmed.index, 1)

    def test_duplicate_sequence_rejected(self):
        token = self.inject_session(0)
        self.lib.drms_record_session_note_recorded(0, 0, 1)
        self.lib.drms_record_session_note_recorded(0, 0, 1)  # 序号重复 = 通路故障
        result, out = self.end()
        self.assertEqual(out.reason, INCOMPLETE)
        self.assertEqual(out.unknown_loss, 1)


class RecordRingFullTest(BoundaryTest):
    def test_log_ring_full_stops_appending_and_publishes_incomplete_end(self):
        self.produce(100)
        self.loop.round()
        token, begin = self.start_record()
        recorded = 0
        failed_seen = False
        for _ in range(32769):
            self.produce(1)
            recorded += self.loop.round(64)
            if self.snapshot().log_dropped:
                failed_seen = True
                break
        self.assertTrue(failed_seen)
        self.assertEqual(self.snapshot().log_dropped, 1)
        result, out = self.end()
        self.assertEqual(result, OK)
        self.assertEqual(out.reason, INCOMPLETE)
        self.assertEqual(out.log_dropped, 1)
        self.assertEqual(out.end_known, 0)  # 数据环满失败：无一致 E
        # 失败后只监测，不再追加
        self.produce(1)
        self.assertEqual(self.loop.round(), 0)
        result, out2 = self.end()
        self.assertEqual(out2.log_dropped, 1)


if __name__ == '__main__':
    unittest.main()
