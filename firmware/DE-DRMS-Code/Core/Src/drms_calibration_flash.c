/*****************************************************************************
 * 文件：drms_calibration_flash.c
 * 职责：把参考校准系数存进 Flash，以及掉电后取回。
 *
 * 与用户配置（drms_user_config）同一套思路：
 *   两页交替写、写完校验、最后单独写提交标记。
 *   这样擦写过程中掉电不会把唯一一份系数弄丢——
 *   坏掉的那页因缺提交标记而被判无效，自动回退到另一页。
 *
 * 存的内容：
 *   系数 k、参考电阻名义值、建立时的采样率、代次、CRC。
 *   其中"代次"用于判断基线与校准的依赖关系——基线只在自己那一代校准下有效。
 *
 * 与运行态的关系：
 *   保存成功不代表运行态已切换；载入失败则必须退回"未校准"而不是用旧值冒充。
 *****************************************************************************/

#include "drms_calibration.h"
#include "drms_calibration_backend.h"
#include "drms_acquisition.h"
#include "drms_logging.h"
#include "drms_msc.h"
#include "main.h"

#define CAL_BASE (0x08000000U + 1008U * 1024U)
static uint32_t cache_enabled;
static volatile uint32_t reading_address, read_fault;

static int supported(void)
{
  /* Do not change option bytes, guess a bank layout, or write application pages.
     Factory dual-bank, no-swap U575RG is the supported persistence layout. */
  return FLASH_SIZE == 1024U * 1024U &&
      (FLASH->OPTR & FLASH_OPTR_DUALBANK) && !(FLASH->OPTR & FLASH_OPTR_SWAP_BANK);
}

int drms_calibration_nmi(void)
{
  uint32_t ecc = FLASH->ECCR;
  if (reading_address && (ecc & FLASH_ECCR_ECCD) && (ecc & FLASH_ECCR_BK_ECC) &&
      !(ecc & FLASH_ECCR_SYSF_ECC) &&
      ((ecc & FLASH_ECCR_ADDR_ECC) & ~15U) ==
      ((reading_address - 0x08000000U - FLASH_BANK_SIZE) & ~15U))
  {
    /* A torn settings quadword is invalid data, not a reason to lose the older
       slot. All unrelated NMIs retain the application's fatal handler. */
    read_fault = 1;
    __HAL_FLASH_CLEAR_FLAG(FLASH_FLAG_ECCD);
    return 1;
  }
  return 0;
}

int drms_cal_backend_read(unsigned int slot, uint8_t record[64])
{
  if (slot > 1 || !supported())
  {
    drms_calibration_flash_status = 1;
    return 0;
  }
  uint32_t address = CAL_BASE + slot * FLASH_PAGE_SIZE;
  uint32_t mask = __get_PRIMASK();
  __disable_irq();
  read_fault = 0;
  /* Read commit first; avoid accessing potentially torn body quadwords unless
     a complete commit exists. Individual loads are scoped for ECC recovery. */
  for (unsigned int word = 0; word < 16; ++word)
  {
    unsigned int index = word < 4 ? word + 12 : word - 4;
    reading_address = address + index * 4U;
    uint32_t value = *(volatile const uint32_t *)(uintptr_t)reading_address;
    reading_address = 0;
    for (unsigned int byte = 0; byte < 4; ++byte)
      record[index * 4U + byte] = (uint8_t)(value >> (byte * 8U));
    if (read_fault)
      break;
    if (word == 3)
    {
      static const uint8_t commit[16] = "DRMSCALCOMMIT1";
      unsigned int valid = 1;
      for (unsigned int i = 0; i < 16; ++i)
        if (record[48 + i] != commit[i])
          valid = 0;
      if (!valid)
      {
        __set_PRIMASK(mask);
        return 0;
      }
    }
  }
  __set_PRIMASK(mask);
  return !read_fault;
}

int drms_cal_backend_begin(void)
{
  if (!supported() || !drms_acq_is_quiescent() || drms_log_state ||
      drms_msc_blocks_recording())
  {
    drms_calibration_flash_status = 1;
    return 0;
  }
  cache_enabled = HAL_ICACHE_IsEnabled();
  if (cache_enabled && HAL_ICACHE_Disable() != HAL_OK)
  {
    drms_calibration_flash_status = 2;
    return 0;
  }
  if (HAL_FLASH_Unlock() != HAL_OK)
  {
    if (cache_enabled)
      (void)HAL_ICACHE_Enable();
    drms_calibration_flash_status = 2;
    return 0;
  }
  __HAL_FLASH_CLEAR_FLAG(FLASH_FLAG_ALL_ERRORS);
  return 1;
}

int drms_cal_backend_erase(unsigned int slot)
{
  FLASH_EraseInitTypeDef erase = {0};
  uint32_t error;
  if (slot > 1)
    return 0;
  erase.TypeErase = FLASH_TYPEERASE_PAGES;
  erase.Banks = FLASH_BANK_2;
  erase.Page = FLASH_PAGE_NB - 2U + slot;
  erase.NbPages = 1;
  return HAL_FLASHEx_Erase(&erase, &error) == HAL_OK;
}

int drms_cal_backend_program(unsigned int slot, unsigned int offset, const uint8_t quadword[16])
{
  if (slot > 1 || offset > 48 || (offset & 15U))
    return 0;
  return HAL_FLASH_Program(FLASH_TYPEPROGRAM_QUADWORD, CAL_BASE + slot * FLASH_PAGE_SIZE + offset,
                           (uint32_t)(uintptr_t)quadword) == HAL_OK;
}

void drms_cal_backend_end(void)
{
  (void)HAL_FLASH_Lock();
  (void)HAL_ICACHE_Invalidate();
  if (cache_enabled)
    (void)HAL_ICACHE_Enable();
}
