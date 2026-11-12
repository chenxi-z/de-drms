/*****************************************************************************
 * 文件：drms_calibration_journal.c
 * 职责：校准记录的代次管理——判断哪一份是最新的、哪一份还能用。
 *
 * 两页交替写入时，重启后要回答"哪一页是新的"。答案靠代次编号，
 * 而不是写入位置或时间戳——代次是单调的，位置不是。
 *
 * 还要处理一种情况：新页写入后校验失败。此时不能简单丢掉，
 * 而要回到旧页并用它的代次——否则会出现"代次倒退"，
 * 让上层以为校准被重置了。
 *****************************************************************************/

#include "drms_calibration.h"
#include "drms_calibration_backend.h"
#include <string.h>

static int active_slot = -1;
volatile uint32_t drms_calibration_flash_status;

void drms_calibration_load(DRMS_Calibration *calibration)
{
  uint8_t record[64];
  DRMS_Calibration candidate;
  *calibration = (DRMS_Calibration){.scale=150000., .reference_ohms=100000., .rate=4000};
  active_slot = -1;
  for (unsigned int slot = 0; slot < 2; ++slot)
  {
    if (drms_cal_backend_read(slot, record) && drms_calibration_unpack(record, &candidate) &&
        (active_slot < 0 || drms_calibration_newer(candidate.generation, calibration->generation)))
    {
      *calibration = candidate;
      active_slot = (int)slot;
    }
  }
}

int drms_calibration_save(DRMS_Calibration *calibration)
{
  uint8_t record[64] __attribute__((aligned(16)));
  uint8_t verify[64];
  DRMS_Calibration next = *calibration, decoded;
  unsigned int slot = active_slot == 0 ? 1 : 0;
  next.generation = calibration->generation + 1U;
  drms_calibration_pack(record, &next);
  if (!drms_calibration_unpack(record, &decoded) || !drms_cal_backend_begin())
    return 0;
  int success = drms_cal_backend_erase(slot);
  /* Never erase the active slot. Commit occupies the final, separate quadword. */
  for (unsigned int offset = 0; success && offset < 64; offset += 16)
    success = drms_cal_backend_program(slot, offset, record + offset);
  if (success)
    success = drms_cal_backend_read(slot, verify) && !memcmp(record, verify, 64) &&
              drms_calibration_unpack(verify, &decoded);
  drms_cal_backend_end();
  if (!success)
  {
    drms_calibration_flash_status = 2;
    return 0;
  }
  active_slot = (int)slot;
  *calibration = next;
  drms_calibration_flash_status = 0;
  return 1;
}
