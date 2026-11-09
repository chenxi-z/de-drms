"""Real RTC/battery service, with factory/HAL boundaries doubled."""
import ctypes
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from test_time import Time

ROOT = Path(__file__).resolve().parents[1]
HEADER = r'''
#ifndef AUX_MOCK_H
#define AUX_MOCK_H
#include <stdint.h>
typedef int HAL_StatusTypeDef;
typedef struct { int unused; } RTC_HandleTypeDef;
typedef struct { int Instance; } ADC_HandleTypeDef;
typedef struct { uint8_t Year,Month,Date,WeekDay; } RTC_DateTypeDef;
typedef struct { uint8_t Hours,Minutes,Seconds,DayLightSaving,StoreOperation; } RTC_TimeTypeDef;
extern RTC_HandleTypeDef hrtc;
extern ADC_HandleTypeDef hadc1;
#define HAL_OK 0
#define RTC_DAYLIGHTSAVING_NONE 0
#define RTC_STOREOPERATION_RESET 0
#define RTC_BKP_DR0 0
#define RTC_FORMAT_BIN 0
#define ADC_CALIB_OFFSET 0
#define ADC_SINGLE_ENDED 0
#define ADC_RESOLUTION_12B 12
#define __HAL_ADC_CALC_VREFANALOG_VOLTAGE(adc,ref,res) (3300U*1500U/(ref))
#define __HAL_ADC_CALC_DATA_TO_VOLTAGE(adc,vdda,code,res) ((vdda)*(code)/4095U)
void HAL_RTCEx_BKUPWrite(RTC_HandleTypeDef *,int,uint32_t);
uint32_t HAL_RTCEx_BKUPRead(RTC_HandleTypeDef *,int);
int HAL_RTC_SetDate(RTC_HandleTypeDef *,RTC_DateTypeDef *,int);
int HAL_RTC_SetTime(RTC_HandleTypeDef *,RTC_TimeTypeDef *,int);
int HAL_RTC_GetDate(RTC_HandleTypeDef *,RTC_DateTypeDef *,int);
int HAL_RTC_GetTime(RTC_HandleTypeDef *,RTC_TimeTypeDef *,int);
int HAL_ADCEx_Calibration_Start(ADC_HandleTypeDef *,int,int);
int HAL_ADC_Start(ADC_HandleTypeDef *);
int HAL_ADC_Stop(ADC_HandleTypeDef *);
int HAL_ADC_PollForConversion(ADC_HandleTypeDef *,int);
uint32_t HAL_ADC_GetValue(ADC_HandleTypeDef *);
int fx_system_date_set(unsigned int,unsigned int,unsigned int);
int fx_system_time_set(unsigned int,unsigned int,unsigned int);
#endif
'''
MOCK = r'''
#include "main.h"
RTC_HandleTypeDef hrtc;
ADC_HandleTypeDef hadc1;
static RTC_DateTypeDef date;
static RTC_TimeTypeDef time;
uint32_t backup,bat_code=2200,ref_code=1500,date_writes,calendar_updates,calibrations,date_reads,time_reads,stops;
int get_time_error,calibration_error;
static unsigned int rank;
void HAL_RTCEx_BKUPWrite(RTC_HandleTypeDef *h,int r,uint32_t v) { backup=v; }
uint32_t HAL_RTCEx_BKUPRead(RTC_HandleTypeDef *h,int r) { return backup; }
int HAL_RTC_SetDate(RTC_HandleTypeDef *h,RTC_DateTypeDef *d,int f) { date=*d;++date_writes;return 0; }
int HAL_RTC_SetTime(RTC_HandleTypeDef *h,RTC_TimeTypeDef *t,int f) { time=*t;return 0; }
int HAL_RTC_GetDate(RTC_HandleTypeDef *h,RTC_DateTypeDef *d,int f) { *d=date;++date_reads;return 0; }
int HAL_RTC_GetTime(RTC_HandleTypeDef *h,RTC_TimeTypeDef *t,int f) { *t=time;++time_reads;return get_time_error; }
int HAL_ADCEx_Calibration_Start(ADC_HandleTypeDef *h,int a,int b) { ++calibrations;return calibration_error; }
int HAL_ADC_Start(ADC_HandleTypeDef *h) { rank=0;return 0; }
int HAL_ADC_Stop(ADC_HandleTypeDef *h) { ++stops;return 0; }
int HAL_ADC_PollForConversion(ADC_HandleTypeDef *h,int t) { return 0; }
uint32_t HAL_ADC_GetValue(ADC_HandleTypeDef *h) { return rank++?ref_code:bat_code; }
int fx_system_date_set(unsigned int y,unsigned int m,unsigned int d) { ++calendar_updates;return 0; }
int fx_system_time_set(unsigned int h,unsigned int m,unsigned int s) { return 0; }
'''


class AuxTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        p = Path(cls.tmp.name)
        (p / 'main.h').write_text(HEADER)
        for name in ('rtc.h', 'adc.h', 'fx_api.h'):
            (p / name).write_text('#include "main.h"')
        (p / 'mock.c').write_text(MOCK)
        src = ROOT / 'firmware/DE-DRMS-Code/Core'
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Werror=implicit-function-declaration',
                        '-I', str(p), '-I', str(src / 'Inc'), str(src / 'Src/drms_aux.c'),
                        str(src / 'Src/drms_time_codec.c'), str(p / 'mock.c'), '-o', str(p / 'aux.so')], check=True)
        cls.instance = 0

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        type(self).instance += 1
        p = Path(self.tmp.name)
        target = p / f'aux-{self.instance}.so'
        shutil.copyfile(p / 'aux.so', target)
        self.lib = ctypes.CDLL(str(target))
        self.lib.drms_time_set.argtypes = [ctypes.c_char_p]
        self.lib.drms_time_get.argtypes = [ctypes.POINTER(Time)]

    def value(self, name):
        return ctypes.c_uint32.in_dll(self.lib, name)

    def test_unset_rtc_stays_invalid_and_invalid_set_has_no_side_effect(self):
        out = Time()
        self.lib.drms_time_get(ctypes.byref(out))
        self.assertEqual(out.valid, 0)
        self.assertEqual(self.lib.drms_time_set(b'2026-02-30T00:00:00'), 0)
        self.assertEqual(self.value('date_writes').value, 0)
        self.assertEqual(self.lib.drms_time_set(b'2026-11-04T13:14:15'), 1)
        self.lib.drms_time_get(ctypes.byref(out))
        self.assertEqual((out.valid, out.year, out.weekday), (1, 2026, 3))
        self.assertEqual(self.value('calendar_updates').value, 1)

    def test_get_date_still_releases_shadow_latch_when_get_time_fails(self):
        self.lib.drms_time_set(b'2026-11-04T13:14:15')
        self.value('get_time_error').value = 1
        out = Time()
        self.lib.drms_time_get(ctypes.byref(out))
        self.assertEqual(self.value('date_reads').value, 1)
        self.assertEqual(out.valid, 0)

    def test_battery_uses_vref_and_rejects_zero_or_clipped_codes(self):
        self.lib.drms_aux_poll()
        self.assertEqual(self.value('drms_battery_mv').value, 3544)
        self.assertEqual(self.value('drms_battery_valid').value, 1)
        self.value('ref_code').value = 0
        self.lib.drms_aux_poll()
        self.assertEqual(self.value('drms_battery_valid').value, 0)
        self.value('ref_code').value = 1500
        self.value('bat_code').value = 4095
        self.lib.drms_aux_poll()
        self.assertEqual(self.value('drms_battery_valid').value, 0)
        self.assertEqual(self.value('calibrations').value, 1)


if __name__ == '__main__':
    unittest.main()
