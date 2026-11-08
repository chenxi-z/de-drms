#ifndef DRMS_TIME_H
#define DRMS_TIME_H
#include <stdint.h>

typedef struct {
  uint16_t year;
  uint8_t month, day, hour, minute, second, weekday, valid;
} DRMS_Time;
int drms_time_parse(const char *iso, DRMS_Time *time);
int drms_time_valid(const DRMS_Time *time);
int drms_time_set(const char *iso);
void drms_time_get(DRMS_Time *time);
void drms_aux_poll(void);
extern volatile uint32_t drms_battery_mv, drms_battery_valid;
#endif
