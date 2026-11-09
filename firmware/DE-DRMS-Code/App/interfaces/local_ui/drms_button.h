#ifndef DRMS_BUTTON_H
#define DRMS_BUTTON_H
#include <stdint.h>

typedef enum {
  DRMS_BUTTON_NONE = 0,
  DRMS_BUTTON_SHORT = 1,
  DRMS_BUTTON_LONG = 2
} DRMS_ButtonEvent;

typedef struct {
  uint32_t raw_since;
  uint32_t press_since;
  uint8_t raw, stable, ignore, long_fired;
} DRMS_Button;

void drms_button_init(DRMS_Button *button, uint32_t now, uint8_t pressed);
DRMS_ButtonEvent drms_button_step(DRMS_Button *button, uint32_t now, uint8_t pressed);
#endif
