#include "drms_time.h"
#include <string.h>

int drms_time_valid(const DRMS_Time *time)
{
  static const uint8_t days[12] = {31,28,31,30,31,30,31,31,30,31,30,31};
  if (time->year < 2000 || time->year > 2099 || time->month < 1 || time->month > 12 ||
      time->hour > 23 || time->minute > 59 || time->second > 59)
    return 0;
  unsigned int maximum = days[time->month - 1];
  if (time->month == 2 && time->year % 4 == 0)
    ++maximum;
  return time->day >= 1 && time->day <= maximum;
}

int drms_time_parse(const char *iso, DRMS_Time *time)
{
  if (strlen(iso) != 19 || iso[4] != '-' || iso[7] != '-' || iso[10] != 'T' ||
      iso[13] != ':' || iso[16] != ':')
    return 0;
  for (unsigned int i = 0; i < 19; ++i)
    if (i != 4 && i != 7 && i != 10 && i != 13 && i != 16 && (iso[i] < '0' || iso[i] > '9'))
      return 0;
  DRMS_Time candidate = {0};
  candidate.year = (uint16_t)((iso[0]-'0')*1000+(iso[1]-'0')*100+(iso[2]-'0')*10+iso[3]-'0');
  candidate.month = (uint8_t)((iso[5]-'0')*10+iso[6]-'0');
  candidate.day = (uint8_t)((iso[8]-'0')*10+iso[9]-'0');
  candidate.hour = (uint8_t)((iso[11]-'0')*10+iso[12]-'0');
  candidate.minute = (uint8_t)((iso[14]-'0')*10+iso[15]-'0');
  candidate.second = (uint8_t)((iso[17]-'0')*10+iso[18]-'0');
  if (!drms_time_valid(&candidate))
    return 0;
  /* Gregorian weekday, Monday=1 ... Sunday=7, as required by STM32 RTC. */
  static const unsigned int offset[12] = {0,3,2,5,0,3,5,1,4,6,2,4};
  unsigned int year = candidate.year - (candidate.month < 3);
  unsigned int weekday = (year+year/4-year/100+year/400+offset[candidate.month-1]+candidate.day)%7;
  candidate.weekday = (uint8_t)(weekday ? weekday : 7);
  candidate.valid = 1;
  *time = candidate;
  return 1;
}
