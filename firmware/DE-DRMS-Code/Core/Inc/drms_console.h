#ifndef DRMS_CONSOLE_H
#define DRMS_CONSOLE_H
#include <stddef.h>

typedef struct {
  char line[64];
  unsigned int used;
  unsigned int discard;
} DRMS_Console;

/* One zero-initialized context per transport. Never executes truncated lines. */
size_t drms_console_feed(DRMS_Console *console, unsigned char byte,
                         char *out, size_t capacity);
size_t drms_console_status(char *out, size_t capacity);
int drms_console_dispatch(const char *line);

#endif
