#ifndef DRMS_ENTROPY_H
#define DRMS_ENTROPY_H
#include <stdint.h>
/* One boot identifier from the STM32 RNG. Intended as DRMS_CDCEntropy. */
int drms_entropy_boot_id(void *context, uint64_t *random_value);
#endif
