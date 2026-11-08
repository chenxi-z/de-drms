#ifndef DRMS_CALIBRATION_BACKEND_H
#define DRMS_CALIBRATION_BACKEND_H
#include <stdint.h>
int drms_cal_backend_read(unsigned int slot, uint8_t record[64]);
int drms_cal_backend_begin(void);
int drms_cal_backend_erase(unsigned int slot);
int drms_cal_backend_program(unsigned int slot, unsigned int offset, const uint8_t quadword[16]);
void drms_cal_backend_end(void);
#endif
