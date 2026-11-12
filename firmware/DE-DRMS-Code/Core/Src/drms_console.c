/*****************************************************************************
 * 文件：drms_console.c
 * 职责：ASCII 命令行的拼装与边界处理——把零散字节攒成一行完整的命令。
 *
 * 三条硬性规则：
 *   1. 每行最多 63 字节，超长整行丢弃并进入失步状态；
 *   2. 遇到溢出后必须重新对齐换行符，不把残缺内容的尾部当新命令；
 *   3. 用 LF 结束，兼容 CRLF（CR 直接忽略）。
 *
 * 为什么"失步"要显式建模：
 *   串口丢一个字节，"START 64000" 可能变成 "TART 64000"。
 *   若不做失步处理，这种残行会被当成合法命令去解析，
 *   产生难以追查的怪异行为。宁可整行丢弃也不执行可疑输入。
 *****************************************************************************/

#include "drms_console.h"
#include <string.h>

static size_t reply(char *out, size_t capacity, const char *text)
{
  size_t length = strlen(text);
  if (!capacity)
    return 0;
  if (length >= capacity)
    length = capacity - 1;
  memcpy(out, text, length);
  out[length] = 0;
  return length;
}

size_t drms_console_feed(DRMS_Console *console, unsigned char byte,
                         char *out, size_t capacity)
{
  size_t length = 0;
  if (byte == '\r')
    return 0;
  if (byte != '\n')
  {
    if (byte < 32 || byte > 126 || console->used >= sizeof(console->line) - 1)
      console->discard = 1;
    if (!console->discard)
      console->line[console->used++] = (char)byte;
    return 0;
  }
  console->line[console->used] = 0;
  if (console->discard)
    length = reply(out, capacity, "ERR line\r\n");
  else if (!console->used)
    length = 0;
  else if (!strcmp(console->line, "PING"))
    length = reply(out, capacity, "OK PONG\r\n");
  else if (!strcmp(console->line, "STATUS"))
    length = drms_console_status(out, capacity);
  else if (!strcmp(console->line, "HELP"))
    length = reply(out, capacity, "OK PING STATUS HELP START [rate] STOP REF MEASURE CAL [Rref_mohm] SAVE RECORD END TIME YYYY-MM-DDTHH:MM:SS\r\n");
  else
  {
    int status = drms_console_dispatch(console->line);
    length = reply(out, capacity, status == 1 ? "OK queued\r\n" :
        status == -1 ? "ERR argument\r\n" : status == -2 ? "ERR busy\r\n" : "ERR unsupported\r\n");
  }
  console->used = console->discard = 0;
  return length;
}
