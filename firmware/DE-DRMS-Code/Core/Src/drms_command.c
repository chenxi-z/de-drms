/*****************************************************************************
 * 文件：drms_command.c
 * 职责：ASCII 命令行的词法与数值解析——把一行文本变成结构化的命令。
 *
 * 解析规则很朴素：空格分隔的 token，第一个是命令名，其余是参数。
 * 但边界处理必须严格：
 *   · 参数个数不符、数值非法、越界，一律整条拒绝，不做部分接受；
 *   · 命令名大小写敏感（协议要求大写），避免与将来的小写扩展冲突。
 *****************************************************************************/

#include "drms_command.h"
#include "drms_measurement.h"
#include "drms_time.h"
#include <string.h>

static int number(const char *text, uint32_t *result)
{
  uint32_t value = 0;
  if (!*text)
    return 0;
  for (; *text; ++text)
  {
    if (*text < '0' || *text > '9' || value > (UINT32_MAX - (uint32_t)(*text - '0')) / 10U)
      return 0;
    value = value * 10U + (uint32_t)(*text - '0');
  }
  *result = value;
  return 1;
}

int drms_command_parse(const char *line, DRMS_Command *command)
{
  DRMS_Command parsed = {0};
  uint8_t ignored;
  if (!strcmp(line, "START") || !strncmp(line, "START ", 6))
  {
    parsed.id = DRMS_CMD_START;
    parsed.value = 4000;
    if (line[5] && !number(line + 6, &parsed.value))
      return -1;
    if (!drms_rate_register(parsed.value, &ignored))
      return -1;
  }
  else if (!strcmp(line, "STOP")) parsed.id = DRMS_CMD_STOP;
  else if (!strcmp(line, "REF")) parsed.id = DRMS_CMD_REFERENCE;
  else if (!strcmp(line, "MEASURE")) parsed.id = DRMS_CMD_MEASURE;
  else if (!strcmp(line, "SAVE")) parsed.id = DRMS_CMD_SAVE;
  else if (!strcmp(line, "RECORD")) parsed.id = DRMS_CMD_RECORD;
  else if (!strcmp(line, "END")) parsed.id = DRMS_CMD_END;
  else if (!strcmp(line, "CAL") || !strncmp(line, "CAL ", 4))
  {
    parsed.id = DRMS_CMD_CALIBRATE;
    parsed.value = 100000000U; /* milliohms; no locale-dependent floats. */
    if (line[3] && !number(line + 4, &parsed.value))
      return -1;
    if (parsed.value < 90000000U || parsed.value > 110000000U)
      return -1;
  }
  else if (!strncmp(line, "TIME ", 5))
  {
    DRMS_Time time;
    if (!drms_time_parse(line + 5, &time))
      return -1;
    parsed.id = DRMS_CMD_TIME;
    memcpy(parsed.text, line + 5, 20);
  }
  else if (!strcmp(line, "TIME"))
    return -1;
  else
    return 0;
  *command = parsed;
  return 1;
}
