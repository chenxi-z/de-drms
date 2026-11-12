/*****************************************************************************
 * 文件：drms_user_backend.c
 * 职责：用户配置区的 Flash 物理读写——擦除、按四字编程、回读。
 *
 * 这一层只做最原始的动作，不做任何格式或校验决策。
 * 上层（drms_user_config）决定写什么、写到哪一页、什么时候写提交标记。
 *
 * 几个必须守住的物理约束：
 *   · 擦除以页为单位，编程以 16 字节四字组为单位；
 *   · 已写过的 Flash 位不能单独改回 1，只能靠擦除；
 *   · 编程后必须回读校验——Flash 写入失败不会报错，只会静默写坏。
 *
 * 只接受本器件的默认双 Bank、未交换映射。其他布局直接返回错误，
 * 绝不去改 Option Bytes——那会把设备变砖。
 *****************************************************************************/

#include "drms_user_config.h"
#include "drms_acquisition.h"
#include "drms_logging.h"
#include "drms_msc.h"
#include "main.h"
#include <string.h>

/* 用户数据 A/B 页 Flash 后端（0x080F8000 / 0x080FA000，各 8 KiB）。
 * 与校准后端同模式：不改 option bytes、不猜 bank 布局、不写应用页；
 * 页粒度擦除、16B 四字编程；擦写期间禁 ICACHE。仅维护上下文
 * （控制任务协调）调用；不允许 CDC 线程直接调用。 */
#define USER_BASE (0x08000000U + 992U * 1024U)
#define USER_PAGES 2u
static uint32_t cache_enabled;

int drms_user_backend_begin(void)
{
  if (FLASH_SIZE != 1024U * 1024U || !(FLASH->OPTR & FLASH_OPTR_DUALBANK) ||
      (FLASH->OPTR & FLASH_OPTR_SWAP_BANK) || !drms_acq_is_quiescent() ||
      drms_log_state || drms_msc_blocks_recording())
    return 0;
  cache_enabled = HAL_ICACHE_IsEnabled();
  if (cache_enabled && HAL_ICACHE_Disable() != HAL_OK)
    return 0;
  if (HAL_FLASH_Unlock() != HAL_OK)
  {
    if (cache_enabled)
      (void)HAL_ICACHE_Enable();
    return 0;
  }
  __HAL_FLASH_CLEAR_FLAG(FLASH_FLAG_ALL_ERRORS);
  return 1;
}

void drms_user_backend_end(void)
{
  (void)HAL_FLASH_Lock();
  (void)HAL_ICACHE_Invalidate();
  if (cache_enabled)
    (void)HAL_ICACHE_Enable();
}

int drms_user_backend_erase(unsigned int page)
{
  if (page >= USER_PAGES)
    return 0;
  FLASH_EraseInitTypeDef erase = {0};
  uint32_t error;
  erase.TypeErase = FLASH_TYPEERASE_PAGES;
  erase.Banks = FLASH_BANK_2; /* 用户区位于第二 bank（双 bank 无交换布局） */
  erase.Page = FLASH_PAGE_NB - 4u + page; /* bank 内第 60/61 页 = 0x080F8000/0x080FA000 */
  erase.NbPages = 1u;
  return HAL_FLASHEx_Erase(&erase, &error) == HAL_OK && error == 0xFFFFFFFFu;
}

int drms_user_backend_program(unsigned int page, unsigned int offset,
                              const uint8_t quadword[16])
{
  if (page >= USER_PAGES || offset % 16u || offset >= DRMS_USER_PAGE_SIZE)
    return 0;
  return HAL_FLASH_Program(FLASH_TYPEPROGRAM_QUADWORD,
                           USER_BASE + page * DRMS_USER_PAGE_SIZE + offset,
                           (uint32_t)(uintptr_t)quadword) == HAL_OK;
}

int drms_user_backend_read(unsigned int page, unsigned int offset,
                           uint8_t *out, unsigned int length)
{
  if (page >= USER_PAGES || offset + length > DRMS_USER_PAGE_SIZE)
    return 0;
  const uint8_t *base =
      (const uint8_t *)(uintptr_t)(USER_BASE + page * DRMS_USER_PAGE_SIZE + offset);
  memcpy(out, base, length);
  return 1;
}
