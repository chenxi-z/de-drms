#ifndef DRMS_MEASUREMENT_H
#define DRMS_MEASUREMENT_H
#include <stddef.h>
#include <stdint.h>

#define DRMS_SAMPLE_CRC_ERROR 1U
#define DRMS_SAMPLE_FORMAT_ERROR 2U
#define DRMS_SAMPLE_ADC_FAULT 4U
#define DRMS_SAMPLE_RANGE_ERROR 8U

typedef struct {
  int32_t voltage;
  int32_t sense;
  uint16_t status;
  uint16_t flags;
} DRMS_Sample;

uint16_t drms_crc16(const uint8_t *bytes, size_t length);
uint32_t drms_crc32(const uint8_t *bytes, size_t length);
int drms_decode_frame(const uint8_t frame[12], DRMS_Sample *sample);
int drms_excitation_ok(const DRMS_Sample *sample);
int drms_resistance(const DRMS_Sample *sample, double scale, double *ohms);
int drms_reference_scale(int64_t voltage_sum, int64_t sense_sum,
                         double reference_ohms, double *scale);
/* Clock 16.384 MHz / 2 / 2 = 4.096 MHz; HRM=1, VNCPEN=0. */
int drms_rate_register(uint32_t samples_per_second, uint8_t *clk2);

#endif
