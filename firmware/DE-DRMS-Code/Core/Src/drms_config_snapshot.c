#include "drms_config_snapshot.h"
#include "main.h"
#include <string.h>

typedef struct {
  uint8_t data[DRMS_CONFIG_SNAPSHOT_MAX];
  uint32_t length, readers;
  uint64_t running, saved;
} Slot;
static Slot slots[2];
static uint32_t active = 2u;

void drms_config_snapshot_init(void)
{
  uint32_t mask = __get_PRIMASK();
  __disable_irq();
  memset(slots, 0, sizeof(slots));
  active = 2u;
  __set_PRIMASK(mask);
}

void drms_config_snapshot_invalidate(void)
{
  uint32_t mask = __get_PRIMASK();
  __disable_irq();
  active = 2u;
  __set_PRIMASK(mask);
}

uint32_t drms_config_snapshot_publish(const uint8_t *data, uint32_t length,
                                      uint64_t running, uint64_t saved)
{
  if (!data || !length || length > DRMS_CONFIG_SNAPSHOT_MAX) return 0;
  uint32_t mask = __get_PRIMASK();
  __disable_irq();
  uint32_t next = active == 0u ? 1u : 0u;
  if (slots[next].readers)
  {
    __set_PRIMASK(mask);
    return 0;
  }
  __set_PRIMASK(mask);
  /* This slot is not visible to new readers. Only the single writer may publish. */
  memcpy(slots[next].data, data, length);
  slots[next].length = length;
  slots[next].running = running;
  slots[next].saved = saved;
  mask = __get_PRIMASK();
  __disable_irq();
  active = next;
  __set_PRIMASK(mask);
  return 1;
}

uint32_t drms_config_snapshot_acquire(DRMS_ConfigView *out)
{
  if (!out) return 0;
  memset(out, 0, sizeof(*out));
  out->slot = 2u;
  uint32_t mask = __get_PRIMASK();
  __disable_irq();
  uint32_t index = active;
  if (index >= 2u || slots[index].readers == UINT32_MAX)
  {
    __set_PRIMASK(mask);
    return 0;
  }
  ++slots[index].readers;
  out->data = slots[index].data;
  out->length = slots[index].length;
  out->running = slots[index].running;
  out->saved = slots[index].saved;
  out->slot = index;
  __set_PRIMASK(mask);
  return 1;
}

void drms_config_snapshot_release(DRMS_ConfigView *view)
{
  if (!view || view->slot >= 2u) return;
  uint32_t mask = __get_PRIMASK();
  __disable_irq();
  if (slots[view->slot].readers) --slots[view->slot].readers;
  view->slot = 2u;
  view->data = NULL;
  view->length = 0;
  __set_PRIMASK(mask);
}
