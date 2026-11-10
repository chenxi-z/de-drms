#include "drms_boot_identity.h"
#include "main.h"
static uint64_t current;
void drms_boot_identity_publish(uint64_t value)
{
  uint32_t mask = __get_PRIMASK();
  __disable_irq();
  current = value;
  __set_PRIMASK(mask);
}
uint64_t drms_boot_identity_get(void)
{
  uint32_t mask = __get_PRIMASK();
  __disable_irq();
  uint64_t value = current;
  __set_PRIMASK(mask);
  return value;
}
