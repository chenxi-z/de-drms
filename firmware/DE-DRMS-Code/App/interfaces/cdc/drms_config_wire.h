#ifndef DRMS_CONFIG_WIRE_H
#define DRMS_CONFIG_WIRE_H
#include <stddef.h>
#include <stdint.h>
/* Converts one validated protocol settings object to a configuration snapshot.
 * Returns encoded size, or zero on invalid input or insufficient output space.
 * Input and output must not overlap. Conversion does not publish configuration. */
size_t drms_config_wire_to_body(const uint8_t *settings, size_t length,
                                uint8_t *body, size_t capacity);
#endif
