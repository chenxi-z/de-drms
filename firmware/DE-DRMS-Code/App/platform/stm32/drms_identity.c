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
