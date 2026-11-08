#ifndef DRMS_CALIBRATION_H
#define DRMS_CALIBRATION_H
#include <stdint.h>

typedef struct {
  double scale;
  double reference_ohms;
  uint32_t generation;
  uint32_t rate;
  uint32_t valid;
} DRMS_Calibration;

void drms_calibration_pack(uint8_t record[64], const DRMS_Calibration *calibration);
int drms_calibration_unpack(const uint8_t record[64], DRMS_Calibration *calibration);
int drms_calibration_newer(uint32_t a, uint32_t b);
void drms_calibration_load(DRMS_Calibration *calibration);
int drms_calibration_save(DRMS_Calibration *calibration);
int drms_calibration_nmi(void);
extern volatile uint32_t drms_calibration_flash_status;
#endif
