#ifndef DRMS_COMMAND_H
#define DRMS_COMMAND_H
#include <stdint.h>
enum {
  DRMS_CMD_START=1, DRMS_CMD_STOP, DRMS_CMD_REFERENCE, DRMS_CMD_MEASURE,
  DRMS_CMD_CALIBRATE, DRMS_CMD_SAVE, DRMS_CMD_RECORD, DRMS_CMD_END, DRMS_CMD_TIME
};
typedef struct {
  uint32_t id, value;
  char text[24];
} DRMS_Command;
/* 1 recognized, 0 unknown, -1 invalid argument. No side effects. */
int drms_command_parse(const char *line, DRMS_Command *command);
#endif
