"""Target Standby preparation: wake routing, late USB cancellation and debug return."""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HEADER = r'''
#include <stdint.h>
typedef struct { volatile uint32_t CTRL; } TestSysTick;
typedef struct { volatile uint32_t ICSR,SCR; } TestSCB;
typedef struct { volatile uint32_t ISER[2],ICER[2],ISPR[2],ICPR[2]; } TestNVIC;
extern TestSysTick systick;
extern TestSCB scb;
extern TestNVIC nvic;
extern unsigned int irq_mask;
#define SysTick (&systick)
#define SCB (&scb)
#define NVIC (&nvic)
#define __get_PRIMASK() irq_mask
#define __disable_irq() (irq_mask=1)
#define __set_PRIMASK(x) (irq_mask=(x))
#define __DSB() ((void)0)
#define SCB_ICSR_PENDSTCLR_Msk 1
#define SCB_ICSR_PENDSVCLR_Msk 2
#define SCB_SCR_SLEEPDEEP_Msk 4
#define GPIO_PIN_RESET 0
#define GPIO_PIN_SET 1
#define USB_VBUS_N_GPIO_Port 0
#define USB_VBUS_N_Pin 13
#define PWR_BTN_GPIO_Port 0
#define PWR_BTN_Pin 5
#define MEAS_BTN_GPIO_Port 0
#define MEAS_BTN_Pin 0
#define LED_GREEN_GPIO_Port 1
#define LED_GREEN_Pin 13
#define LED_YELLOW_GPIO_Port 1
#define LED_YELLOW_Pin 14
#define LED_ORANGE_GPIO_Port 1
#define LED_ORANGE_Pin 15
#define LED_RED_GPIO_Port 0
#define LED_RED_Pin 6
#define PWR_LED_GPIO_Port 0
#define PWR_LED_Pin 7
#define PWR_GPIO_A 0
#define PWR_GPIO_C 2
#define PWR_GPIO_BIT_0 1
#define PWR_GPIO_BIT_2 4
#define PWR_GPIO_BIT_3 8
#define PWR_GPIO_BIT_4 16
#define PWR_GPIO_BIT_5 32
#define PWR_GPIO_BIT_13 8192
#define PWR_WAKEUP_PIN1_LOW_0 1
#define PWR_WAKEUP_PIN2_LOW_1 2
#define PWR_WAKEUP_PIN5_LOW_0 4
#define PWR_WAKEUP_FLAG1 1
#define PWR_WAKEUP_FLAG2 2
#define PWR_WAKEUP_FLAG5 5
#define __HAL_PWR_CLEAR_FLAG(x) clear_wake(x)
int HAL_GPIO_ReadPin(int,int);
void HAL_GPIO_WritePin(int,int,int);
int HAL_PWREx_EnableGPIOPullUp(uint32_t,uint32_t);
int HAL_PWREx_EnableGPIOPullDown(uint32_t,uint32_t);
void HAL_PWREx_EnablePullUpPullDownConfig(void);
void HAL_PWR_EnableWakeUpPin(uint32_t);
void HAL_SuspendTick(void);
void HAL_ResumeTick(void);
void HAL_PWR_EnterSTANDBYMode(void);
void clear_wake(unsigned int);
'''
MOCK = r'''
#include "main.h"
TestSysTick systick;
TestSCB scb;
TestNVIC nvic;
unsigned int irq_mask,usb_low,late_usb,wake_mask,entries,suspended,leds_off,entry_mask,entry_tick;
volatile uint32_t drms_acq_running,drms_log_state,drms_storage_shutdown_ready;
int HAL_GPIO_ReadPin(int p,int n) { return n==13?!usb_low:1; }
void HAL_GPIO_WritePin(int p,int n,int v) { leds_off+=v==1; }
int HAL_PWREx_EnableGPIOPullUp(uint32_t p,uint32_t pins) { return 0; }
int HAL_PWREx_EnableGPIOPullDown(uint32_t p,uint32_t pins) { return 0; }
void HAL_PWREx_EnablePullUpPullDownConfig(void) {}
void HAL_PWR_EnableWakeUpPin(uint32_t pin) { wake_mask|=pin; }
void clear_wake(unsigned int flag) { if(flag==5 && late_usb) usb_low=1; }
void HAL_SuspendTick(void) { suspended=1; }
void HAL_ResumeTick(void) { suspended=0; }
void HAL_PWR_EnterSTANDBYMode(void) { ++entries;scb.SCR|=4;entry_mask=irq_mask;entry_tick=systick.CTRL; }
void reset_state(void) {
 irq_mask=usb_low=late_usb=wake_mask=entries=suspended=leds_off=0;
 drms_acq_running=drms_log_state=0;drms_storage_shutdown_ready=1;
 systick.CTRL=7;scb.SCR=scb.ICSR=0;
 nvic.ISER[0]=0x1234;nvic.ISER[1]=0x5678;nvic.ISPR[0]=1;nvic.ISPR[1]=2;
}
unsigned int restored(void) { return systick.CTRL==7 && !scb.SCR &&
 nvic.ISER[0]==0x1234 && nvic.ISER[1]==0x5678 && nvic.ISPR[0]==1 && nvic.ISPR[1]==2; }
'''


class PowerBackendTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        p = Path(cls.tmp.name)
        (p / 'main.h').write_text(HEADER)
        (p / 'mock.c').write_text(MOCK)
        src = ROOT / 'firmware/DE-DRMS-Code/Core'
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Werror=implicit-function-declaration',
                        '-I', str(p), '-I', str(src / 'Inc'), str(src / 'Src/drms_power_stm32.c'),
                        str(p / 'mock.c'), '-o', str(p / 'backend.so')], check=True)
        cls.lib = ctypes.CDLL(str(p / 'backend.so'))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.lib.reset_state()

    def value(self, name):
        return ctypes.c_uint32.in_dll(self.lib, name)

    def test_wake_pins_and_scheduler_restored_if_debug_prevents_entry(self):
        self.assertEqual(self.lib.drms_power_backend_enter(), 0)
        self.assertEqual(self.value('wake_mask').value, 7)
        self.assertEqual(self.value('entries').value, 1)
        self.assertEqual((self.value('entry_mask').value,self.value('entry_tick').value), (1,0))
        self.assertEqual(self.value('irq_mask').value, 0)
        self.assertEqual(self.value('suspended').value, 0)
        self.assertEqual(self.lib.restored(), 1)

    def test_late_usb_edge_is_not_cleared_then_slept_through(self):
        self.value('late_usb').value = 1
        self.assertEqual(self.lib.drms_power_backend_enter(), 1)
        self.assertEqual(self.value('entries').value, 0)
        self.assertEqual(self.value('irq_mask').value, 0)

    def test_active_acquisition_or_unflushed_storage_blocks_entry(self):
        self.value('drms_acq_running').value = 1
        self.assertEqual(self.lib.drms_power_backend_enter(), 0)
        self.lib.reset_state()
        self.value('drms_storage_shutdown_ready').value = 0
        self.assertEqual(self.lib.drms_power_backend_enter(), 0)
        self.assertEqual(self.value('entries').value, 0)


if __name__ == '__main__':
    unittest.main()
