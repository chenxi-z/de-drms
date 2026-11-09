#include "drms_button.h"

#define DEBOUNCE_MS 50u
#define LONG_PRESS_MS 2000u

void drms_button_init(DRMS_Button *button, uint32_t now, uint8_t pressed)
{
  if (!button)
    return;
  button->raw_since = now;
  button->press_since = now;
  button->raw = button->stable = pressed != 0;
  button->ignore = pressed != 0;
  button->long_fired = 0;
}

DRMS_ButtonEvent drms_button_step(DRMS_Button *button, uint32_t now, uint8_t pressed)
{
  if (!button)
    return DRMS_BUTTON_NONE;
  pressed = pressed != 0;
  if (button->raw != pressed)
  {
    button->raw = pressed;
    button->raw_since = now;
  }
  if (button->raw != button->stable && (uint32_t)(now - button->raw_since) >= DEBOUNCE_MS)
  {
    button->stable = button->raw;
    if (button->stable)
    {
      button->press_since = button->raw_since;
      button->long_fired = 0;
    }
    else
    {
      if (button->ignore)
      {
        button->ignore = 0;
        return DRMS_BUTTON_NONE;
      }
      if (!button->long_fired)
      {
        if ((uint32_t)(button->raw_since - button->press_since) >= LONG_PRESS_MS)
          return DRMS_BUTTON_LONG;
        return DRMS_BUTTON_SHORT;
      }
    }
  }
  if (button->stable && button->raw && !button->ignore && !button->long_fired &&
      (uint32_t)(now - button->press_since) >= LONG_PRESS_MS)
  {
    button->long_fired = 1;
    return DRMS_BUTTON_LONG;
  }
  return DRMS_BUTTON_NONE;
}
