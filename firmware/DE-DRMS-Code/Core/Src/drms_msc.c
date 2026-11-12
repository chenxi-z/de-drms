/*****************************************************************************
 * 文件：drms_msc.c
 * 职责：把 TF 卡做成只读 U 盘交给主机——导出、收回、以及期间的读请求中继。
 *
 * 在整机中的位置：
 *   USB 主机 → MSC 类（ux_device_msc.c）→ 本模块 → drms_storage 原始扇区读 → TF 卡
 *
 * 为什么要走这么绕的一圈：
 *   导出 U 盘时必须先让 FileX 关闭文件系统、释放 SD 驱动，再由本模块用
 *   原始扇区读把数据交给主机。绝不能一边让 FileX 写、一边让主机读，
 *   否则双方都在改同一份介质，必然损坏。
 *
 * 状态机（owner_state）：
 *   LOCAL      文件系统在用卡，正常业务状态
 *   EXPORTING  已受理导出请求，正在做交接（关 FileX、释放驱动、初始化原始访问）
 *   EXPORTED   已交给主机，此时只接受原始读
 *   RELEASING  正在收回（等所有在途读退出，再重新挂载 FileX）
 *   QUARANTINED 监督者判定"无法证明静止"，隔离待恢复
 *
 * 读请求的中继机制（重点）：
 *   主机的读请求来自 USBX 线程，但操作介质只能是存储线程的事。
 *   所以这里用"单在途邮箱"：USBX 线程投一个请求进去，然后自旋等待；
 *   存储线程轮询发现后执行，把结果写回，状态置为已完成。
 *   同一时刻只允许一个请求在途，超时也不会释放槽位——只有存储线程
 *   确认收到结果才归还，避免缓冲区被两边同时使用。
 *
 * 只读保证：
 *   写回调在 USB 层直接拒绝（返回 DATA PROTECT），LUN 也声明为只读。
 *   导出期间介质上不会有任何写操作。
 *****************************************************************************/

#include "drms_msc.h"
#include "drms_storage.h"
#include "drms_logging.h"
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
  uint32_t cancel_epoch;
  uint32_t orphaned;
  uint8_t buffer[512] __attribute__((aligned(32)));
} read_mailbox;

static DRMS_MSCWaitHook wait_hook;

/* 初始化导出状态机，回到"介质归文件系统所有"的初始状态。 */
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

/* 注册等待钩子。USBX 线程在等读结果时反复调用它，作用是让出 CPU。
 *
 * 生产环境传进来的是 tx_thread_sleep(1)。测试环境用它来手动驱动存储线程，
 * 这就是单元测试能同步验证这套异步流程的原因。 */
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

/* 当前介质归谁：文件系统、导出中、已交给主机，还是释放中。 */
DRMS_Owner drms_msc_owner(void)
{
  return (DRMS_Owner)__atomic_load_n(&owner_state, __ATOMIC_ACQUIRE);
}

/* 介质健康状况（在位/就绪/故障/缺席），由存储层的事实推导而来。 */
DRMS_Health drms_msc_health(void)
{
  DRMS_Health health;
  drms_storage_snapshot(0, &health);
  return health;
}

/* 导出代次。每次交接与收回都会推进，主机靠它判断"盘还是不是刚才那块"。 */
uint32_t drms_msc_export_generation(void)
{
  return __atomic_load_n(&export_generation, __ATOMIC_ACQUIRE);
}

/* 是否已经可以接受主机的读写（已导出且介质健康）。
 * MSC 的 Status 回调靠它回答"介质就绪吗"。 */
uint32_t drms_msc_media_ready(void)
{
  return drms_msc_owner() == DRMS_OWNER_EXPORTED &&
         drms_msc_health() == DRMS_HEALTH_READY;
}

/* 取介质总扇区数。导出未完成时返回 BUSY，容量为 0 时报 IO_ERROR——
 * 两种情况都不能让主机以为看到了一块有效磁盘。 */
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

/* 最近一次导出相关操作的错误码，供状态查询与诊断。 */
DRMS_Result drms_msc_last_error(void)
{
  return last_error;
}

/* 当前是否有记录在写卡——有的话导出请求必须被拒，
 * 因为两者要用同一块介质。 */
uint32_t drms_msc_blocks_recording(void)
{
  return drms_msc_owner() != DRMS_OWNER_LOCAL;
}

/* 申请把卡导出为 U 盘。这只是登记意图，真正的交接在存储线程里做。
 *
 * 拒绝的三种情况：介质已经在别处使用、已有导出/收回请求在处理、
 * 当前正在记录。任何一个成立都返回 BUSY，让主机知道"现在不行"。
 *
 * 注意：这里先把 owner_state 置为 EXPORTING，是为了让并发的第二请求
 * 立刻看到"已经有导出在办"，不必等到存储线程才发现。 */
DRMS_Result drms_msc_request_export(void)
{
  uint32_t mask = crit_enter();
  if (owner_state != DRMS_OWNER_LOCAL || request_export || request_release ||
      __atomic_load_n(&drms_log_state, __ATOMIC_ACQUIRE))
  {
    crit_exit(mask);
    return DRMS_BUSY;
  }
  owner_state = (uint32_t)DRMS_OWNER_EXPORTING;
  last_error = DRMS_OK;
  request_export = 1;
  crit_exit(mask);
  return DRMS_ACCEPTED;
}

/* 申请收回介质（导出结束）。
 *
 * 只有处于导出态或正在导出时才受理。收回是异步的——要等在途读全部退出、
 * 重新挂载文件系统成功，才算真正完成。 */
DRMS_Result drms_msc_request_release(void)
{
  uint32_t mask = crit_enter();
  if (owner_state != DRMS_OWNER_EXPORTED && owner_state != DRMS_OWNER_EXPORTING)
  {
    crit_exit(mask);
    return DRMS_BUSY;
  }
  owner_state = (uint32_t)DRMS_OWNER_RELEASING;
  last_error = DRMS_OK;
  request_release = 1;
  crit_exit(mask);
  return DRMS_ACCEPTED;
}

/* 立即撤销导出（IRQ 安全）。用于 USB 断线、关机、拔卡等场合。
 *
 * 这个函数刻意只做两件事：推进取消纪元、把所有权原子地转到"释放中"。
 * 任何介质操作都留给存储线程——中断上下文里绝不能碰 SD 驱动。 */
void drms_msc_cancel(void)
{
  /* IRQ 安全：仅标志与原子所有权转移，介质操作留给存储线程。 */
  __atomic_add_fetch(&cancel_epoch, 1U, __ATOMIC_ACQ_REL);
  uint32_t mask = crit_enter();
  if (owner_state != DRMS_OWNER_LOCAL)
  {
    if (owner_state == DRMS_OWNER_EXPORTED || owner_state == DRMS_OWNER_EXPORTING)
      owner_state = (uint32_t)DRMS_OWNER_RELEASING;
    request_release = 1;
  }
  crit_exit(mask);
}

/* ---- 交接（仅存储线程） ---- */

static void finish_export_request(void)
{
  if (!drms_storage_card_present())
  {
    request_export = 0;
    owner_state = (uint32_t)DRMS_OWNER_LOCAL;
    last_error = DRMS_IO_ERROR; /* 无卡导出：LOCAL+ABSENT，不开放磁盘 */
    return;
  }
  if (!drms_storage_mounted || drms_storage_status != FX_SUCCESS)
  {
    request_export = 0;
    owner_state = (uint32_t)DRMS_OWNER_LOCAL;
    last_error = DRMS_IO_ERROR;
    return;
  }
  if (!drms_storage_capacity_sectors())
  {
    request_export = 0;
    owner_state = (uint32_t)DRMS_OWNER_LOCAL;
    last_error = DRMS_IO_ERROR; /* 容量查询失败不开放磁盘 */
    return;
  }
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
  __atomic_store_n(&drms_storage_mounted, 0U, __ATOMIC_RELEASE);
  drms_storage_release_driver();
  if (owner_state != DRMS_OWNER_EXPORTING || request_release)
  {
    request_export = 0;
    return; /* disconnect during flush/close: do not enable raw access */
  }
  DRMS_Result raw = drms_storage_begin_raw_access();
  uint32_t mask = crit_enter();
  if (raw != DRMS_OK || owner_state != DRMS_OWNER_EXPORTING || request_release)
  {
    owner_state = (uint32_t)DRMS_OWNER_RELEASING;
    request_release = 1;
    request_export = 0;
    last_error = raw != DRMS_OK ? raw : DRMS_CANCELLED;
    crit_exit(mask);
    return;
  }
  owner_state = (uint32_t)DRMS_OWNER_EXPORTED;
  __atomic_add_fetch(&export_generation, 1U, __ATOMIC_ACQ_REL);
  last_error = DRMS_OK;
  request_export = 0;
  crit_exit(mask);
}

/* 收回介质：确认在途读已退出，然后重新挂载文件系统。
 *
 * 关键守卫：只要读邮箱还有在途请求就返回，不许继续。因为那块缓冲区
 * 可能正被读路径使用，此时重挂载会让 FileX 和原始读同时碰介质。
 *
 * 重挂载可能失败（卡被拔了、卡坏了），失败时保持"不可记录"并如实上报，
 * 不能假装收回成功。 */
static void finish_release(void)
{
  if (__atomic_load_n(&read_mailbox.state, __ATOMIC_ACQUIRE) == 1U)
    return; /* 在途读未归结：不得仅凭状态变量重挂载（缓冲仍由读路径使用） */
  if (!drms_storage_mounted)
    drms_storage_release_driver(); /* 已离开 FileX 后才释放原始驱动 */
  __atomic_add_fetch(&export_generation, 1U, __ATOMIC_ACQ_REL);
  if (!drms_storage_card_present())
    last_error = DRMS_IO_ERROR;
  else
  {
    /* Mount may block/preempt: do not advertise LOCAL or release the TF lease
     * until both the actual mount result and health are published. */
    drms_storage_remount_after_export();
    if (drms_storage_status != FX_SUCCESS)
      last_error = DRMS_IO_ERROR;
  }
  uint32_t mask = crit_enter();
  request_release = 0;
  owner_state = (uint32_t)DRMS_OWNER_LOCAL;
  crit_exit(mask);
}

/* 执行读邮箱里的请求。这是主机的读操作真正落到介质上的地方。
 *
 * 执行前先校验"这次请求还有效吗"：所有权仍是导出态、且代次没变。
 * 任何一项不符（收回、换代、取消），立刻把在途请求作废成失败，
 * 绝不用一块已经不属于导出的介质去回应主机。
 *
 * 逐扇区读并在每步之间检查卡与所有权：读 512 字节可能耗时不短，
 * 期间卡可能被拔掉、导出可能被撤销，只有逐扇区检查才能及时发现。
 * 数据先读到本模块自己的缓冲区，成功之后才复制给 USBX ——
 * 这样失败时不会把半份数据交给主机。 */
static void service_read_mailbox(void)
{
  if (__atomic_load_n(&read_mailbox.state, __ATOMIC_ACQUIRE) != 1U)
    return;
  if (owner_state != DRMS_OWNER_EXPORTED ||
      read_mailbox.generation != export_generation)
  {
    /* 撤销/换代/取消：在途读作废，归结为失败后归还槽 */
    __atomic_store_n(&read_mailbox.state, 3U, __ATOMIC_RELEASE);
    last_error = DRMS_CANCELLED;
    return;
  }
  /* 逐 512B 扇区执行；每步检查卡与所有权，成功后才复制给 USBX 缓冲 */
  uint8_t *out = read_mailbox.buffer;
  for (uint32_t i = 0; i < read_mailbox.blocks; ++i)
  {
    if (!drms_storage_card_present() || owner_state != DRMS_OWNER_EXPORTED)
    {
      __atomic_store_n(&read_mailbox.state, 3U, __ATOMIC_RELEASE);
      last_error = DRMS_IO_ERROR;
      return;
    }
    DRMS_Result result = drms_storage_raw_read(read_mailbox.lba + i, 1,
                                               out + i * 512u);
    if (result != DRMS_OK)
    {
      __atomic_store_n(&read_mailbox.state, 3U, __ATOMIC_RELEASE);
      last_error = result;
      return;
    }
  }
  last_error = DRMS_OK;
  __atomic_store_n(&read_mailbox.state, 2U, __ATOMIC_RELEASE);
}

/* 导出状态机的推进函数，由存储线程周期性调用。
 *
 * 三件事按序做：
 *   1. 拔卡检测：已导出但卡不在了，立即撤销（不能等主机自己发现）；
 *   2. 处理待办的导出请求（做交接）；
 *   3. 执行读邮箱；最后处理收回。
 *
 * 顺序不能随意调整：先处理导出再处理读，否则读请求会打到一个还没交接完的介质上。 */
void drms_msc_service(void)
{
  if (owner_state == DRMS_OWNER_EXPORTED && !drms_storage_card_present())
    drms_msc_cancel(); /* 拔卡立即撤销导出，并由本线程收敛原始访问 */
  /* 取消已在 drms_msc_cancel 内把所有权原子转为 RELEASING；
   * 这里不再依据全局取消纪元判定，否则新一次导出会被旧纪元反复打回。 */
  if (request_export && owner_state == DRMS_OWNER_EXPORTING)
    finish_export_request();
  else if (request_export && owner_state != DRMS_OWNER_EXPORTING)
    request_export = 0;
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
  for (uint32_t sector = 0; sector < blocks; ++sector)
  {
    uint32_t mask = crit_enter();
    if ((DRMS_Owner)owner_state != DRMS_OWNER_EXPORTED)
    {
      crit_exit(mask);
      return DRMS_BUSY;
    }
    uint32_t capacity = drms_storage_capacity_sectors();
    if (!capacity || blocks > capacity || lba > capacity - blocks)
    {
      crit_exit(mask);
      return DRMS_INVALID;
    }
    uint32_t current = __atomic_load_n(&read_mailbox.state, __ATOMIC_ACQUIRE);
    if (read_mailbox.orphaned && (current == 2U || current == 3U))
    {
      __atomic_store_n(&read_mailbox.state, 0U, __ATOMIC_RELEASE);
      current = 0;
    }
    if (current != 0)
    {
      crit_exit(mask);
      return DRMS_BUSY;
    }
    read_mailbox.lba = lba + sector;
    read_mailbox.blocks = 1;
    read_mailbox.generation = export_generation;
    read_mailbox.cancel_epoch = cancel_epoch;
    read_mailbox.orphaned = 0;
    __atomic_store_n(&read_mailbox.state, 1U, __ATOMIC_RELEASE);
    crit_exit(mask);
    for (uint32_t round = 0; round < DRMS_MSC_READ_WAIT_ROUNDS; ++round)
    {
      if (__atomic_load_n(&read_mailbox.state, __ATOMIC_ACQUIRE) >= 2)
        break;
      if (wait_hook)
        wait_hook();
    }
    mask = crit_enter();
    uint32_t state = __atomic_load_n(&read_mailbox.state, __ATOMIC_ACQUIRE);
    if (state == 1)
    {
      read_mailbox.orphaned = 1;
      crit_exit(mask);
      return DRMS_TIMEOUT;
    }
    if (state != 2 || owner_state != DRMS_OWNER_EXPORTED ||
        read_mailbox.generation != export_generation ||
        read_mailbox.cancel_epoch != cancel_epoch)
    {
      if (state == 2 || state == 3)
        __atomic_store_n(&read_mailbox.state, 0U, __ATOMIC_RELEASE);
      crit_exit(mask);
      return DRMS_IO_ERROR;
    }
    __atomic_store_n(&read_mailbox.state, 4U, __ATOMIC_RELEASE); /* buffer is being copied */
    crit_exit(mask);
    memcpy(out + (size_t)sector * sizeof(read_mailbox.buffer), read_mailbox.buffer,
           sizeof(read_mailbox.buffer));
    mask = crit_enter();
    __atomic_store_n(&read_mailbox.state, 0U, __ATOMIC_RELEASE);
    crit_exit(mask);
  }
  return DRMS_OK;
}
