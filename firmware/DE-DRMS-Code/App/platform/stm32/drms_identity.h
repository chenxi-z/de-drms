#ifndef DRMS_IDENTITY_H
#define DRMS_IDENTITY_H
#include <stddef.h>
#include <stdint.h>

#define DRMS_IDENTITY_LENGTH 29u
#define DRMS_IDENTITY_CAPACITY (DRMS_IDENTITY_LENGTH + 1u)
size_t drms_identity_format(uint32_t word0, uint32_t word1, uint32_t word2,
                            char *out, size_t capacity);
#endif
