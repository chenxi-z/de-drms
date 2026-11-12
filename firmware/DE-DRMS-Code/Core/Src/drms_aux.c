/*****************************************************************************
 * 文件：drms_aux.c
 * 职责：辅助外设——状态灯与内部 ADC（电池电压、VREFINT）。
 *
 * 状态灯：
 *   五颗灯用不同颜色/闪烁表达"待机/监测/记录/故障"等状态。
 *   灯效是低优先级的：主循环有空才刷新，绝不因为它影响采集或记录。
 *
 * 内部 ADC 的用途：
 *   读电池电压（经分压）与 VREFINT。VREFINT 用来校正基准漂移——
 *   内部基准本身会随温度变化，不校正的话电池电压读数会有系统性偏差。
 *
 * 采样时间的硬性要求：
 *   读 VREFINT 需要足够长的采样时间（≥320 周期 @16 MHz，依据手册
 *   tS_vrefint = 12.65 µs typ）。采太短读出来是错的，而且错得很隐蔽——
 *   所以这一项不能按"差不多就行"来设。
 *****************************************************************************/

#include "drms_time.h"
#include "main.h"
#include "rtc.h"
#include "adc.h"
#include "fx_api.h"

#define RTC_VALID_MAGIC 0x44524d53U
volatile uint32_t drms_battery_mv, drms_battery_valid;
static unsigned int adc_calibrated;

int drms_time_set(const char *iso)
{
  DRMS_Time parsed;
  if (!drms_time_parse(iso, &parsed))
    return 0;
  RTC_DateTypeDef date = {0};
  RTC_TimeTypeDef time = {0};
  date.Year = (uint8_t)(parsed.year - 2000);
  date.Month = parsed.month;
  date.Date = parsed.day;
  date.WeekDay = parsed.weekday;
  time.Hours = parsed.hour;
  time.Minutes = parsed.minute;
  time.Seconds = parsed.second;
  time.DayLightSaving = RTC_DAYLIGHTSAVING_NONE;
  time.StoreOperation = RTC_STOREOPERATION_RESET;
  HAL_RTCEx_BKUPWrite(&hrtc, RTC_BKP_DR0, 0);
  if (HAL_RTC_SetDate(&hrtc, &date, RTC_FORMAT_BIN) != HAL_OK ||
      HAL_RTC_SetTime(&hrtc, &time, RTC_FORMAT_BIN) != HAL_OK)
    return 0;
  HAL_RTCEx_BKUPWrite(&hrtc, RTC_BKP_DR0, RTC_VALID_MAGIC);
  /* A RECORD immediately after TIME must not inherit a stale FAT timestamp. */
  (void)fx_system_date_set(parsed.year, parsed.month, parsed.day);
  (void)fx_system_time_set(parsed.hour, parsed.minute, parsed.second);
  return 1;
}

void drms_time_get(DRMS_Time *result)
{
  *result = (DRMS_Time){0};
  if (HAL_RTCEx_BKUPRead(&hrtc, RTC_BKP_DR0) != RTC_VALID_MAGIC)
    return;
  RTC_TimeTypeDef time;
  RTC_DateTypeDef date;
  HAL_StatusTypeDef time_status = HAL_RTC_GetTime(&hrtc, &time, RTC_FORMAT_BIN);
  /* Always read date after time to release RTC shadow-register locking. */
  HAL_StatusTypeDef date_status = HAL_RTC_GetDate(&hrtc, &date, RTC_FORMAT_BIN);
  if (time_status != HAL_OK || date_status != HAL_OK)
    return;
  *result = (DRMS_Time){.year=(uint16_t)(2000+date.Year), .month=date.Month, .day=date.Date,
                      .hour=time.Hours, .minute=time.Minutes, .second=time.Seconds, .weekday=date.WeekDay};
  result->valid = (uint8_t)drms_time_valid(result);
}

void drms_aux_poll(void)
{
  DRMS_Time time;
  drms_time_get(&time);
  if (time.valid)
  {
    (void)fx_system_date_set(time.year, time.month, time.day);
    (void)fx_system_time_set(time.hour, time.minute, time.second);
  }
  drms_battery_valid = 0;
  if (!adc_calibrated)
  {
    if (HAL_ADCEx_Calibration_Start(&hadc1, ADC_CALIB_OFFSET, ADC_SINGLE_ENDED) != HAL_OK)
      return;
    adc_calibrated = 1;
  }
  if (HAL_ADC_Start(&hadc1) != HAL_OK)
    return;
  uint32_t battery = 0, reference = 0;
  if (HAL_ADC_PollForConversion(&hadc1, 5) == HAL_OK)
  {
    battery = HAL_ADC_GetValue(&hadc1);
    if (HAL_ADC_PollForConversion(&hadc1, 5) == HAL_OK)
      reference = HAL_ADC_GetValue(&hadc1);
  }
  (void)HAL_ADC_Stop(&hadc1);
  if (!reference || reference > 4095 || battery >= 4095)
    return;
  uint32_t vdda = __HAL_ADC_CALC_VREFANALOG_VOLTAGE(hadc1.Instance, reference, ADC_RESOLUTION_12B);
  if (vdda < 1600 || vdda > 3600)
    return;
  uint32_t millivolts = 2U * __HAL_ADC_CALC_DATA_TO_VOLTAGE(hadc1.Instance, vdda, battery, ADC_RESOLUTION_12B);
  if (millivolts >= 1000 && millivolts <= 5000)
  {
    drms_battery_mv = millivolts;
    drms_battery_valid = 1;
  }
}
