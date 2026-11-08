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
