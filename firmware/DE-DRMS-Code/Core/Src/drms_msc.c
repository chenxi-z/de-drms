#include "drms_msc.h"
#include "drms_storage.h"
#include "app_filex.h"
#include "main.h"

extern FX_MEDIA sdio_disk; /* 定义在 drms_storage.c（FileX 唯一所有者） */
#include <string.h>

/* 单一介质所有者实现（T4/R5/MSC 设计）。状态写入：service（仅存储线程）、
 * request_*（任意线程，短临界区置请求标志）、cancel（IRQ 安全：仅置位与
 * 所有权原子转移，由存储线程收敛）。读邮箱单在途；超时不释放槽，
 * 归还仅由存储线程的归结（DONE）触发。 */
#define DRMS_MSC_READ_WAIT_ROUNDS 1000u /* 有界等待轮数（配合等待钩子让出） */

static volatile uint32_t owner_state; /* 原子读写；enum 底层类型宽度不确定 */
static DRMS_Result last_error;
static uint32_t export_generation;
static volatile uint32_t request_export, request_release;
static uint32_t cancel_epoch;

static struct {
  uint32_t state; /* 0 空闲, 1 在途, 2 归结-成功, 3 归结-失败 */
  uint32_t lba, blocks, generation;
  uint32_t cancel_epoch; /* 请求发起时的取消纪元：仅此后的取消才作废本请求 */
  uint8_t *out;
} read_mailbox;

static DRMS_MSCWaitHook wait_hook;

void drms_msc_init(void)
{
  owner_state = (uint32_t)DRMS_OWNER_LOCAL;
  last_error = DRMS_OK;
  export_generation = 0;
  request_export = request_release = 0;
  cancel_epoch = 0;
  memset(&read_mailbox, 0, sizeof(read_mailbox));
  wait_hook = 0;
}

void drms_msc_set_wait_hook(DRMS_MSCWaitHook hook)
{
  wait_hook = hook;
}

static uint32_t crit_enter(void)
{
  uint32_t mask = __get_PRIMASK();
  __disable_irq();
  return mask;
}

static void crit_exit(uint32_t mask) { __set_PRIMASK(mask); }

DRMS_Owner drms_msc_owner(void)
{
  return (DRMS_Owner)__atomic_load_n(&owner_state, __ATOMIC_ACQUIRE);
}

DRMS_Health drms_msc_health(void)
{
  DRMS_Health health;
  drms_storage_snapshot(0, &health);
  return health;
}

uint32_t drms_msc_export_generation(void)
{
  return __atomic_load_n(&export_generation, __ATOMIC_ACQUIRE);
}

uint32_t drms_msc_media_ready(void)
{
  return drms_msc_owner() == DRMS_OWNER_EXPORTED &&
         drms_msc_health() == DRMS_HEALTH_READY;
}

DRMS_Result drms_msc_media_info(uint32_t *blocks)
{
  if (!blocks)
    return DRMS_INVALID;
  if (!drms_msc_media_ready())
    return DRMS_BUSY;
  uint32_t capacity = drms_storage_capacity_sectors();
  if (!capacity)
    return DRMS_IO_ERROR;
  *blocks = capacity;
  return DRMS_OK;
}

DRMS_Result drms_msc_last_error(void)
{
  return last_error;
}

uint32_t drms_msc_blocks_recording(void)
{
  return drms_msc_owner() != DRMS_OWNER_LOCAL;
}

DRMS_Result drms_msc_request_export(void)
{
  uint32_t mask = crit_enter();
  if (owner_state != DRMS_OWNER_LOCAL || request_export || request_release)
  {
    crit_exit(mask);
    return DRMS_BUSY;
  }
  request_export = 1;
  crit_exit(mask);
  return DRMS_ACCEPTED;
}

DRMS_Result drms_msc_request_release(void)
{
  uint32_t mask = crit_enter();
  if (owner_state == DRMS_OWNER_LOCAL || owner_state == DRMS_OWNER_QUARANTINED)
  {
    crit_exit(mask);
    return DRMS_BUSY;
  }
  request_release = 1;
  crit_exit(mask);
  return DRMS_ACCEPTED;
}

void drms_msc_cancel(void)
{
  /* IRQ 安全：仅标志与原子所有权转移，介质操作留给存储线程。 */
  __atomic_add_fetch(&cancel_epoch, 1U, __ATOMIC_ACQ_REL);
  uint32_t mask = crit_enter();
  if (owner_state == DRMS_OWNER_EXPORTED || owner_state == DRMS_OWNER_EXPORTING)
    owner_state = (uint32_t)DRMS_OWNER_RELEASING; /* 撤销介质就绪（USB reset/unconfigure/断线） */
  request_release = 1;
  crit_exit(mask);
}

/* ---- 交接（仅存储线程） ---- */

static void finish_export_request(void)
{
  if (!drms_storage_card_present())
  {
    request_export = 0;
    last_error = DRMS_IO_ERROR; /* 无卡导出：LOCAL+ABSENT，不开放磁盘 */
    return;
  }
  if (!drms_storage_mounted || drms_storage_status != FX_SUCCESS)
  {
    request_export = 0;
    last_error = DRMS_IO_ERROR;
    return;
  }
  if (!drms_storage_capacity_sectors())
  {
    request_export = 0;
    last_error = DRMS_IO_ERROR; /* 容量查询失败不开放磁盘 */
    return;
  }
  owner_state = (uint32_t)DRMS_OWNER_EXPORTING;
  UINT status = fx_media_flush(&sdio_disk);
  if (status == FX_SUCCESS)
    status = fx_media_close(&sdio_disk);
  if (status != FX_SUCCESS)
  {
    /* 交接失败：不同时开放 FileX 与原始读取 */
    drms_storage_invalidate();
    owner_state = (uint32_t)DRMS_OWNER_LOCAL;
    last_error = DRMS_IO_ERROR;
    request_export = 0;
    return;
  }
  drms_storage_release_driver();
  drms_storage_begin_raw_access(); /* 原始读所需的 SD 初始化（导出期一次） */
  owner_state = (uint32_t)DRMS_OWNER_EXPORTED;
  __atomic_add_fetch(&export_generation, 1U, __ATOMIC_ACQ_REL);
  last_error = DRMS_OK;
  request_export = 0;
}

static void finish_release(void)
{
  if (read_mailbox.state == 1)
    return; /* 在途读未归结：不得仅凭状态变量重挂载（缓冲仍由读路径使用） */
  drms_storage_release_driver(); /* 原始访问结束；卡可能已拔出，容错 */
  owner_state = (uint32_t)DRMS_OWNER_LOCAL;
  request_release = 0;
  __atomic_add_fetch(&export_generation, 1U, __ATOMIC_ACQ_REL); /* 撤销就绪即换代 */
  if (!drms_storage_card_present())
  {
    last_error = DRMS_IO_ERROR;
    return;
  }
  drms_storage_poll(); /* 重新挂载 FileX；失败保持不可记录并报告 */
  if (drms_storage_status != FX_SUCCESS)
    last_error = DRMS_IO_ERROR;
  else
    last_error = DRMS_OK;
}

static void service_read_mailbox(void)
{
  if (read_mailbox.state != 1)
    return;
  if (owner_state != DRMS_OWNER_EXPORTED ||
      read_mailbox.generation != export_generation)
  {
    /* 撤销/换代/取消：在途读作废，归结为失败后归还槽 */
    read_mailbox.state = 3;
    last_error = DRMS_CANCELLED;
    return;
  }
  /* 逐 512B 扇区执行；每步检查卡与所有权，成功后才复制给 USBX 缓冲 */
  uint8_t *out = read_mailbox.out; /* read() 已校验非空 */
  for (uint32_t i = 0; i < read_mailbox.blocks; ++i)
  {
    if (!drms_storage_card_present() || owner_state != DRMS_OWNER_EXPORTED)
    {
      read_mailbox.state = 3;
      last_error = DRMS_IO_ERROR;
      return;
    }
    DRMS_Result result = drms_storage_raw_read(read_mailbox.lba + i, 1,
                                               out + i * 512u);
    if (result != DRMS_OK)
    {
      read_mailbox.state = 3;
      last_error = result;
      return;
    }
  }
  read_mailbox.state = 2;
  last_error = DRMS_OK;
}

void drms_msc_service(void)
{
  /* 取消已在 drms_msc_cancel 内把所有权原子转为 RELEASING；
   * 这里不再依据全局取消纪元判定，否则新一次导出会被旧纪元反复打回。 */
  if (request_export && owner_state == DRMS_OWNER_LOCAL)
    finish_export_request();
  service_read_mailbox();
  if (request_release || owner_state == DRMS_OWNER_RELEASING ||
      owner_state == DRMS_OWNER_QUARANTINED)
    finish_release(); /* 隔离后仍由存储线程收敛清理，完成后回 LOCAL */
}

/* 监督者入口（T7 看门狗/超时监督）：存储线程错过时限、无法证明在途读
 * 静止时显式隔离。隔离期间拒绝新请求；service 继续收敛既有清理。 */
void drms_msc_mark_quarantined(void)
{
  if (owner_state == DRMS_OWNER_EXPORTED || owner_state == DRMS_OWNER_EXPORTING ||
      owner_state == DRMS_OWNER_RELEASING)
  {
    owner_state = (uint32_t)DRMS_OWNER_QUARANTINED;
    last_error = DRMS_TIMEOUT;
    request_release = 1;
  }
}

/* ---- USBX 同步读（仅 USBX 线程） ---- */

DRMS_Result drms_msc_read(uint32_t lba, uint32_t blocks, uint8_t *out)
{
  if (!out || !blocks)
    return DRMS_INVALID;
  uint32_t mask = crit_enter();
  /* 所有权检查必须在临界区内与槽占用同时完成：否则 cancel（IRQ 入口）
   * 可在检查与置位之间把所有权转走，留下一个永不归结的占槽请求。 */
  if ((DRMS_Owner)owner_state != DRMS_OWNER_EXPORTED)
  {
    crit_exit(mask);
    return DRMS_BUSY; /* 未导出/释放中/隔离：NOT READY */
  }
  uint32_t capacity = drms_storage_capacity_sectors();
  if (!capacity || blocks > capacity ||
      lba > capacity - blocks) /* 减法校验拒绝溢出/越界 */
  {
    crit_exit(mask);
    return DRMS_INVALID;
  }
  if (read_mailbox.state == 1)
  {
    crit_exit(mask);
    return DRMS_BUSY; /* 上一笔尚未归结（含超时情形）：槽不可复用 */
  }
  read_mailbox.state = 1;
  read_mailbox.lba = lba;
  read_mailbox.blocks = blocks;
  read_mailbox.generation = export_generation;
  read_mailbox.cancel_epoch = cancel_epoch;
  read_mailbox.out = out;
  crit_exit(mask);
  for (uint32_t round = 0; round < DRMS_MSC_READ_WAIT_ROUNDS; ++round)
  {
    if (read_mailbox.state >= 2)
      break;
    if (wait_hook)
      wait_hook();
  }
  mask = crit_enter();
  uint32_t state = read_mailbox.state;
  DRMS_Result outcome = DRMS_OK;
  if (state == 3)
    outcome = DRMS_IO_ERROR;
  if (state >= 2)
    read_mailbox.state = 0; /* 已归结：清槽归还 */
  crit_exit(mask);
  if (state >= 2)
    return outcome; /* 成功或失败都由本次调用观察并归还 */
  return DRMS_TIMEOUT; /* 未归结：槽保持占用，out 不得复用 */
}
