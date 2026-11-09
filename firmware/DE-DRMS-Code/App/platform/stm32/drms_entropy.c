#include "drms_entropy.h"
#include "main.h"

/* RM0456 ch. 48 and AN4230: NIST configuration for the 48 MHz source.
 * This backend owns only RNG; it must not change HSI48 shared by USB/SDMMC.
 * Fail closed on clock, seed or hardware timeout rather than invent entropy. */
#define DRMS_RNG_ERRORS (RNG_SR_CECS | RNG_SR_SECS | RNG_SR_CEIS | RNG_SR_SEIS)
#define DRMS_RNG_TIMEOUT_MS 25u
#define DRMS_RNG_POLL_LIMIT 200000u

static int wait_bits(uint32_t mask, uint32_t want_set)
{
  uint32_t started = HAL_GetTick();
  for (uint32_t i = 0; i < DRMS_RNG_POLL_LIMIT; ++i)
  {
    if (RNG->SR & DRMS_RNG_ERRORS)
      return 0;
    if (!!(RNG->CR & mask) == !!want_set)
      return 1;
    if ((uint32_t)(HAL_GetTick() - started) >= DRMS_RNG_TIMEOUT_MS)
      return 0;
  }
  return 0;
}

static int read_word(uint32_t *out)
{
  uint32_t started = HAL_GetTick();
  for (uint32_t i = 0; i < DRMS_RNG_POLL_LIMIT; ++i)
  {
    uint32_t status = RNG->SR;
    if (status & DRMS_RNG_ERRORS)
      return 0;
    if (status & RNG_SR_DRDY)
    {
      uint32_t value = RNG->DR;
      if (RNG->SR & DRMS_RNG_ERRORS)
        return 0;
      *out = value;
      return 1;
    }
    if ((uint32_t)(HAL_GetTick() - started) >= DRMS_RNG_TIMEOUT_MS)
      return 0;
  }
  return 0;
}

int drms_entropy_boot_id(void *context, uint64_t *random_value)
{
  (void)context;
  if (!random_value)
    return 0;
  *random_value = 0;
  if (!__HAL_RCC_GET_FLAG(RCC_FLAG_HSI48RDY) || __HAL_RCC_RNG_IS_CLK_ENABLED())
    return 0;
  __HAL_RCC_RNG_CONFIG(RCC_RNGCLKSOURCE_HSI48);
  __HAL_RCC_RNG_CLK_ENABLE();
  RNG->CR = RNG_CR_NIST_VALUE | RNG_CR_CONDRST;
  RNG->HTCR = RNG_HTCR_NIST_VALUE;
  RNG->NSCR = RNG_NSCR_NIST_VALUE;
  RNG->CR &= ~RNG_CR_CONDRST;
  uint32_t a = 0, b = 0;
  int ok = wait_bits(RNG_CR_CONDRST, 0);
  if (ok)
  {
    RNG->CR |= RNG_CR_RNGEN;
    ok = read_word(&a) && read_word(&b);
  }
  RNG->CR &= ~RNG_CR_RNGEN;
  __HAL_RCC_RNG_CLK_DISABLE();
  if (!ok)
    return 0;
  *random_value = (uint64_t)a | ((uint64_t)b << 32);
  return *random_value != 0;
}
