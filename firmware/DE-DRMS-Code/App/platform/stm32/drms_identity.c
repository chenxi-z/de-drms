/*****************************************************************************
 * 文件：drms_identity.c
 * 职责：把芯片唯一 ID（96 位）格式化成可读的设备序列号。
 *
 * 输出形如 "DRMS-XXXXXXXXXXXXXXXXXXXXXXXX"（三段各 8 位十六进制）。
 * 纯函数、无硬件依赖——输入就是三个 32 位字，便于单独测试。
 *
 * 用芯片 UID 而不是自定义序列号：这样任何一块板子都能自动获得
 * 唯一标识，不需要产线烧号。
 *****************************************************************************/

#include "drms_identity.h"
#include <string.h>

size_t drms_identity_format(uint32_t word0, uint32_t word1, uint32_t word2,
                            char *out, size_t capacity)
{
  static const char digits[] = "0123456789ABCDEF";
  const uint32_t words[3] = {word0, word1, word2};
  if (!out || capacity < DRMS_IDENTITY_CAPACITY)
    return 0;
  memcpy(out, "DRMS-", 5);
  for (unsigned int word = 0; word < 3; ++word)
  {
    for (unsigned int digit = 0; digit < 8; ++digit)
      out[5 + word * 8 + digit] = digits[(words[word] >> (28 - digit * 4)) & 15u];
  }
  out[DRMS_IDENTITY_LENGTH] = '\0';
  return DRMS_IDENTITY_LENGTH;
}
