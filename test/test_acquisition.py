"""ADS131A02 register/frame emulator around the real acquisition/DMA code."""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HEADER = r'''
#ifndef MOCK_ACQ_H
#define MOCK_ACQ_H
#include <stdint.h>
#include <stddef.h>
typedef int HAL_StatusTypeDef;
typedef struct { int Instance; struct { unsigned int DataSize,CLKPolarity,CLKPhase,FirstBit,Mode,NSS; } Init; } SPI_HandleTypeDef;
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
#define ADS_CS_GPIO_Port 0
#define ADS_CS_Pin 4
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
MOCK = r'''
#include "main.h"
#include "drms_measurement.h"
#include <string.h>
SPI_HandleTypeDef hspi1={.Instance=1,.Init={SPI_DATASIZE_8BIT,SPI_POLARITY_LOW,SPI_PHASE_2EDGE,SPI_FIRSTBIT_MSB,SPI_MODE_MASTER,SPI_NSS_SOFT}};
void set_spi_size(unsigned int size) { hspi1.Init.DataSize=size; }
unsigned int pins[8],forbidden,wrong_frame,commands[64],command_count,dma_starts;
int bad_ready,bad_crc,dma_error;
static uint32_t ticks;
static uint16_t response=0xff02;
static int fixed,unlocked;
static uint8_t *rx_buffer;
void HAL_GPIO_WritePin(int port,int pin,int state) {
 pins[pin]=state;
 if(!pins[6] && pins[7]) ++forbidden;
 if(pin==2 && !state) { fixed=0;unlocked=0;response=0xff02; }
}
uint32_t HAL_GetTick(void) { return ticks; }
void HAL_Delay(uint32_t ms) { ticks+=ms; }
void advance_ms(uint32_t ms) { ticks+=ms; }
int HAL_SPI_TransmitReceive(SPI_HandleTypeDef *s,uint8_t *tx,uint8_t *rx,uint16_t n,uint32_t timeout) {
 if(n!=(fixed?12:3)) ++wrong_frame;
 if(fixed && drms_crc16(tx,9)!=((tx[9]<<8)|tx[10])) ++wrong_frame;
 memset(rx,0,n);rx[0]=response>>8;rx[1]=response&255;
 if(bad_ready) { rx[0]=0xff;rx[1]=0xff; }
 if(fixed) { uint16_t crc=drms_crc16(rx,9);rx[9]=crc>>8;rx[10]=crc&255;if(bad_crc) rx[3]^=1; }
 uint16_t command=(tx[0]<<8)|tx[1];
 if(command && command_count<64) commands[command_count++]=command;
 if(command==0x0655) {unlocked=1;response=command;}
 else if((command&0xe000)==0x4000) {
   response=command-0x2000;
   if((command&0xff00)==0x4c00) fixed=1;
 } else if(command) response=command;
 else response=unlocked?0x2200:0xff02;
 return 0;
}
int HAL_SPI_TransmitReceive_DMA(SPI_HandleTypeDef *s,uint8_t *tx,uint8_t *rx,uint16_t n) {
 ++dma_starts;rx_buffer=rx;
 if(n!=12 || drms_crc16(tx,9)!=((tx[9]<<8)|tx[10])) ++wrong_frame;
 return dma_error;
}
int HAL_SPI_Abort(SPI_HandleTypeDef *s) { return 0; }
void HAL_SPI_TxRxCpltCallback(SPI_HandleTypeDef *);
void complete_frame(int a,int b) {
 memset(rx_buffer,0,12);rx_buffer[0]=0x22;
 rx_buffer[3]=(a>>16)&255;rx_buffer[4]=(a>>8)&255;rx_buffer[5]=a&255;
 rx_buffer[6]=(b>>16)&255;rx_buffer[7]=(b>>8)&255;rx_buffer[8]=b&255;
 uint16_t crc=drms_crc16(rx_buffer,9);rx_buffer[9]=crc>>8;rx_buffer[10]=crc&255;
 HAL_SPI_TxRxCpltCallback(&hspi1);
}
int pin(unsigned int n) { return pins[n]; }
'''


class Raw(ctypes.Structure):
    _fields_ = [('bytes', ctypes.c_ubyte * 12), ('sequence', ctypes.c_uint32)]


class AcquisitionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        p = Path(cls.tmp.name)
        (p / 'main.h').write_text(HEADER)
        (p / 'spi.h').write_text('#include "main.h"')
        (p / 'mock.c').write_text(MOCK)
        src = ROOT / 'firmware/DE-DRMS-Code/Core'
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Werror=implicit-function-declaration',
                        '-I', str(p), '-I', str(src / 'Inc'),
                        *[str(src / f'Src/drms_{name}.c') for name in ('acquisition', 'measurement', 'fifo')],
                        str(p / 'mock.c'), '-o', str(p / 'acq.so')], check=True)
        cls.lib = ctypes.CDLL(str(p / 'acq.so'))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def value(self, name):
        return ctypes.c_uint.in_dll(self.lib, name)

    def setUp(self):
        self.lib.drms_acq_stop()
        self.lib.set_spi_size(7)
        for name in ('forbidden', 'wrong_frame', 'command_count', 'bad_ready', 'bad_crc', 'dma_error', 'dma_starts'):
            self.value(name).value = 0

    def test_initialization_uses_internal_ref_without_charge_pump_and_checks_acks(self):
        self.assertEqual(self.lib.drms_acq_start(4000, 0), 1)
        commands = list((ctypes.c_uint * 64).in_dll(self.lib, 'commands'))[:self.value('command_count').value]
        self.assertEqual(commands, [0x0655, 0x4c7f, 0x4b68, 0x4d02, 0x4e22, 0x4f0f, 0x0033, 0x0555])
        self.assertEqual(self.value('wrong_frame').value, 0)

    def test_non_byte_spi_configuration_cannot_overrun_frame_buffers(self):
        self.lib.set_spi_size(23)
        self.assertEqual(self.lib.drms_acq_start(4000, 0), 0)
        self.assertEqual(self.value('command_count').value, 0)
        self.assertEqual(self.lib.pin(5), 1)

    def test_spi_busy_edge_is_counted_and_sequence_gap_preserved(self):
        self.assertEqual(self.lib.drms_acq_start(4000, 0), 1)
        self.lib.drms_acq_drdy()
        self.lib.drms_acq_drdy()
        self.lib.complete_frame(1000000, 4000000)
        self.assertEqual(self.value('drms_acq_overruns').value, 1)
        self.lib.drms_acq_drdy()
        self.lib.complete_frame(2000000, 4000000)
        a, b = Raw(), Raw()
        self.assertEqual(self.lib.drms_acq_pop(ctypes.byref(a)), 1)
        self.assertEqual(self.lib.drms_acq_pop(ctypes.byref(b)), 1)
        self.assertEqual((a.sequence, b.sequence), (0, 2))

    def test_switching_never_connects_sample_and_reference_together(self):
        for reference in (0, 1, 0, 1):
            self.assertEqual(self.lib.drms_acq_start(4000, reference), 1)
        self.assertEqual(self.value('forbidden').value, 0)

    def test_bad_ready_or_crc_leaves_excitation_disabled(self):
        for fault in ('bad_ready', 'bad_crc'):
            with self.subTest(fault=fault):
                self.setUp()
                self.value(fault).value = 1
                self.assertEqual(self.lib.drms_acq_start(4000, 0), 0)
                self.assertEqual(self.value('drms_acq_running').value, 0)
                self.assertEqual(self.lib.pin(5), 1)
                self.assertEqual(self.lib.pin(3), 0)

    def test_raw_queue_overload_stops_irq_work_instead_of_starving_supervisor(self):
        self.assertEqual(self.lib.drms_acq_start(128000, 0), 1)
        for _ in range(4097):
            self.lib.drms_acq_drdy()
            self.lib.complete_frame(280000, 4200000)
        self.assertEqual(self.value('drms_acq_queue_drops').value, 1)
        self.assertEqual(self.value('drms_acq_running').value, 0)
        self.assertEqual(self.value('drms_acq_error').value, 6)
        self.assertEqual(self.lib.pin(5), 1)

    def test_missing_drdy_timeout_shuts_down_analog(self):
        self.assertEqual(self.lib.drms_acq_start(4000, 0), 1)
        self.lib.advance_ms(201)
        self.lib.drms_acq_poll()
        self.assertEqual(self.value('drms_acq_running').value, 0)
        self.assertEqual(self.value('drms_acq_error').value, 4)
        self.assertEqual(self.lib.pin(5), 1)


if __name__ == '__main__':
    unittest.main()
