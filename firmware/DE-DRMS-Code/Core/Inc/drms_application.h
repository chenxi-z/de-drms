#ifndef DRMS_APPLICATION_H
#define DRMS_APPLICATION_H
#include <stddef.h>
void drms_application_init(void);
void drms_application_poll(void);
size_t drms_application_status(char *out, size_t capacity);
/* Console callback: 1 queued, 0 unknown, -1 bad argument, -2 busy. */
int drms_console_dispatch(const char *line);
#endif
