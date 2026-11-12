/*****************************************************************************
 * 文件：drms_button.c
 * 职责：按键消抖与长短按识别。
 *
 * 判据（首版设计值，可用注入时间验证）：
 *   · 每 10 ms 采样一次电平，稳定 50 ms 才认为状态改变；
 *   · 短按只在释放时产生一次事件；
 *   · 长按满 2 s 产生一次事件，并吞掉本次释放（不重复报短按）；
 *   · 不启用双击——双击会让响应变迟钝，而这里没有需要它的交互。
 *
 * 这是纯状态机，不读 GPIO：调用方把当前电平喂进来。
 * 这样单元测试可以用"推进时间 + 喂电平"完整覆盖所有时序分支。
 *****************************************************************************/

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
