/*****************************************************************************
 * 文件：drms_storage.c
 * 职责：TF 介质的事实来源——挂载、拔插观察、容量缓存、原始扇区读。
 *
 * 与其他模块的分工：
 *   drms_msc.c      决定"谁是介质的主人"（文件系统还是 U 盘导出）
 *   drms_logging.c  在文件系统可用时写记录
 *   本文件          只如实报告介质的状态与能力，不做所有权决策
 *
 * 两条访问路径：
 *   常规：FileX 挂载 → 通过文件系统读写（记录、下载都用这条）
 *   导出：FileX 关闭 → 本文件的 raw_read 直接读物理扇区（U 盘导出用）
 * 两条路径互斥，由 drms_msc 的所有权状态保证。
 *
 * 卡检测的特殊处理（务必看 drms_storage_card_present）：
 *   首板的卡座 CD 触点是坏的，插拔都读高电平，因此固件里写死"卡永远在位"。
 *   这带来一串连锁影响，详见该函数的注释。
 *****************************************************************************/

#include "drms_storage.h"
#include "drms_logging.h"
#include "drms_power.h"
#include "drms_msc.h"
#include "app_filex.h"
#include "main.h"

extern FX_MEDIA sdio_disk;
extern uint32_t fx_sd_media_memory[128];
volatile unsigned int drms_storage_mounted;
volatile unsigned int drms_storage_status = FX_IO_ERROR;
static uint32_t capacity_cache; /* 导出容量缓存（挂载成功时刷新） */
static uint32_t media_generation, last_presence, presence_known;

/* 复位所有介质状态到"未挂载、无卡"。启动时调用一次。 */
void drms_storage_init(void)
{
  drms_storage_mounted = 0;
  drms_storage_status = FX_IO_ERROR;
  capacity_cache = media_generation = last_presence = presence_known = 0;
}

/* 观察卡的插拔变化，并在变化时推进介质代次。
 *
 * 代次是一个单调递增的编号：每次插拔或重新识别都会加一。
 * 所有"基于某次识别结果"的请求（打开文件、列举目录）都必须带上代次，
 * 代次不符就说明介质已经换过了，那些结果作废。
 *
 * 卡不在位时清掉容量缓存，避免下次用旧容量去算扇区。 */
void drms_storage_observe(void)
{
  uint32_t present = drms_storage_card_present();
  if ((!presence_known && present) || (presence_known && present != last_presence))
    __atomic_add_fetch(&media_generation, 1u, __ATOMIC_RELEASE);
  presence_known = 1;
  last_presence = present;
  if (!present)
    capacity_cache = 0;
}

/* 当前介质代次，供协议层把请求绑定到某一次介质识别上。 */
uint32_t drms_storage_media_generation(void)
{
  return __atomic_load_n(&media_generation, __ATOMIC_ACQUIRE);
}

/* 释放 SD 驱动。这一步同时复位了 ST 驱动的内部初始化闩锁、
 * 删除它的 DMA 信号量——所以卡被拔掉时也必须能成功执行，
 * 不能被"卡不在了"挡住。 */
static void release_driver(void)
{
  /* 这一步同时复位 ST 驱动的内部初始化闩锁并删除它的 DMA 信号量。
   * 卡被拔掉时也必须能执行成功——清理不能被"卡不在了"挡住。 */
  sdio_disk.fx_media_driver_request = FX_DRIVER_UNINIT;
  fx_stm32_sd_driver(&sdio_disk);
}

/* 把已挂载的状态整体作废：中止 FileX、释放驱动、清容量。
 *
 * 用于"确认介质已经不可信"的场合（拔卡、I/O 反复失败）。
 * 调用后设备处于"未挂载"状态，等下一次 poll 尝试重新挂载。 */
void drms_storage_invalidate(void)
{
  if (drms_storage_mounted)
  {
    drms_storage_mounted = 0;
    (void)fx_media_abort(&sdio_disk);
    release_driver();
  }
  capacity_cache = 0;
  drms_log_removed();
  drms_storage_status = FX_IO_ERROR;
}

/* 关机前的介质收尾：flush 并关闭文件系统。
 *
 * 只有在没有记录在写、且介质不归导出使用时才返回 1（可以关机）。
 * 关闭失败会把整个状态作废——宁可下次开机重新挂载，也不要留一个
 * 半脏的文件系统。
 *
 * 返回：1 已就绪可关机；0 还有事没做完。 */
int drms_storage_prepare_shutdown(void)
{
  if (drms_log_state || drms_msc_owner() != DRMS_OWNER_LOCAL)
    return 0;
  if (drms_storage_mounted)
  {
    UINT status = fx_media_flush(&sdio_disk);
    if (status == FX_SUCCESS)
      status = fx_media_close(&sdio_disk);
    if (status != FX_SUCCESS)
    {
      drms_storage_invalidate();
      drms_storage_status = status;
    }
    else
    {
      drms_storage_mounted = 0;
      drms_storage_status = FX_SUCCESS;
    }
  }
  drms_storage_shutdown_ready = 1;
  return 1;
}

/* 介质维护的主循环，由存储线程周期性调用。
 *
 * 职责：观察插拔、在需要时挂载、挂载失败后退让重试。
 *
 * 两个守卫条件：
 *   · 介质已经被导出给主机时直接返回——此时不能碰文件系统；
 *   · 卡不在位时作废挂载并返回。
 *
 * 挂载成功后刷新容量缓存并推进代次。失败则释放驱动，留待下次重试，
 * 不在原地反复重试把整个线程卡住。 */
void drms_storage_poll(void)
{
  drms_storage_observe();
  if (drms_msc_owner() != DRMS_OWNER_LOCAL)
    return;
  if (!drms_storage_card_present())
  {
    if (drms_storage_mounted)
    {
      /* 物理拔卡之后绝不再写。未落盘的脏数据可能丢失，这是有意的取舍。 */
      drms_storage_invalidate();
    }
    drms_storage_status = FX_IO_ERROR;
    return;
  }
  if (!drms_storage_mounted)
  {
    drms_storage_status = fx_media_open(&sdio_disk, FX_SD_VOLUME_NAME,
        fx_stm32_sd_driver, FX_NULL, fx_sd_media_memory, sizeof(fx_sd_media_memory));
    if (drms_storage_status == FX_SUCCESS)
    {
      drms_storage_mounted = 1;
      /* 导出容量以当前卡为准；换卡/重挂载后刷新，不得沿用旧容量。 */
      capacity_cache = (uint32_t)sdio_disk.fx_media_total_sectors;
      __atomic_add_fetch(&media_generation, 1u, __ATOMIC_RELEASE);
    }
    else
      release_driver();
  }
}

/* ---------------- T4：所有权双轴与原始读 ---------------- */
/* 所有权来源 = drms_msc（介质交接状态机，存储线程唯一写者）；
 * 健康由本文件事实单源推导：卡不在位 → ABSENT；在位但未挂载 → FAULT 或
 * ABSENT（按最近事实）；挂载成功 → READY。旧 mounted/status 继续表达
 * FileX 事实，供既有投影（STATUS 文本）使用，不承担第二状态源。 */
uint32_t drms_storage_capacity_sectors(void)
{
  return capacity_cache;
}

/* 卡是否在位——注意首板这个回答是**策略**而不是测量。
 *
 * 卡座的 CD 触点是坏的（插拔都读高电平），所以固件里写死"永远在位"。
 * 下面所有调用方都继承这个语义：挂载门控、原始访问门控、拔卡撤销导出。
 *
 * 后果必须清楚：
 *   · 拔卡不再被检测。录制中拔卡要等下一次真实 I/O 失败才暴露；
 *   · MSC 导出期间拔卡不会撤销导出；
 *   · 无卡时也会尝试 SD 初始化，表现为挂载失败（sd=0）而不是"无卡"。
 *
 * 详见 main.h 里 DRMS_SD_DIAGNOSTIC_IGNORE_CD 的说明。 */
uint32_t drms_storage_card_present(void)
{
  #if DRMS_SD_DIAGNOSTIC_IGNORE_CD
  return 1;
  #else
  return HAL_GPIO_ReadPin(SD_CD_GPIO_Port, SD_CD_Pin) == GPIO_PIN_RESET;
  #endif
}

/* 对外暴露的驱动释放入口，供导出交接流程调用。 */
void drms_storage_release_driver(void)
{
  release_driver();
}

/* 导出期初始化原始 SD 访问（FileX 已关闭、驱动已释放）。 */
DRMS_Result drms_storage_begin_raw_access(void)
{
  sdio_disk.fx_media_driver_request = FX_DRIVER_INIT;
  sdio_disk.fx_media_driver_status = FX_IO_ERROR; /* 驱动写回真实结果 */
  fx_stm32_sd_driver(&sdio_disk);
  return sdio_disk.fx_media_driver_status == FX_SUCCESS ? DRMS_OK : DRMS_IO_ERROR;
}

/* 原始扇区读——仅供 U 盘导出使用。调用前提：FileX 已关闭、驱动已释放。
 *
 * 这里有一个极易踩错的地方：FileX 的 SD 驱动会自动把 hidden_sectors
 * （本板是 2048，即 1 MiB 分区偏移）加到它收到的每个扇区号上。这对
 * 文件系统内部的读写是正确的，但对"主机按整盘寻址"的 U 盘访问是错的——
 * 主机要 LBA 0（MBR），驱动却去读分区的第一个扇区，于是分区表读不出来。
 *
 * 解决办法是预先减去这个偏移，让驱动加回去之后正好落在主机要的位置上。
 * 用无符号回绕保证 LBA 小于偏移时也能算对。
 *
 * 返回：OK 读成功；IO_ERROR 卡不在位或驱动报错。 */
DRMS_Result drms_storage_raw_read(uint32_t lba, uint32_t blocks, uint8_t *out)
{
  if (!drms_storage_card_present())
    return DRMS_IO_ERROR;
  /* 关键细节：FileX 的 SD 驱动会给它收到的每个扇区号自动加上
   * fx_media_hidden_sectors（见 fx_stm32_sd_driver.c 的 FX_DRIVER_READ 分支）。
   * 那是分区卷的隐藏扇区数，本板为 2048（1 MiB）。
   *
   * 这对文件系统内部的读写是对的，但 MSC 是"按整盘寻址"：
   * 主机要 LBA 0（MBR），绝不能被平移到分区卷的第一个扇区去。
   * 所以这里先把这个偏移减掉，让驱动加回去之后正好落在 lba 上。
   * 用无符号回绕，保证 lba 小于偏移时也能算对。
   *
   * 不做这一步的后果就是"容量能看到、分区表读不出来"——
   * 正是最初 U 盘打不开的根因。 */
  sdio_disk.fx_media_driver_request = FX_DRIVER_READ;
  sdio_disk.fx_media_driver_logical_sector = lba - sdio_disk.fx_media_hidden_sectors;
  sdio_disk.fx_media_driver_sectors = blocks;
  sdio_disk.fx_media_driver_buffer = out;
  fx_stm32_sd_driver(&sdio_disk);
  if (sdio_disk.fx_media_driver_status != FX_SUCCESS)
    return DRMS_IO_ERROR;
  return DRMS_OK;
}

/* 推导并返回介质的双重状态：所有权与健康度。
 *
 * 健康度完全是推出来的，不单独存一份，避免出现两份互相矛盾的状态：
 *   卡不在位            → ABSENT
 *   有容量缓存或已挂载  → READY（导出期间 FileX 虽已关闭，容量仍在）
 *   其余                → FAULT
 *
 * 所有权直接取自 drms_msc，本文件不做决策。 */
void drms_storage_snapshot(DRMS_Owner *owner, DRMS_Health *health)
{
  DRMS_Owner local_owner = drms_msc_owner();
  DRMS_Health local_health;
  uint32_t present = drms_storage_card_present();
  if (!present)
    local_health = DRMS_HEALTH_ABSENT;
  else if ((drms_storage_mounted && drms_storage_status == FX_SUCCESS) ||
           capacity_cache)
    local_health = DRMS_HEALTH_READY; /* 已获知卡容量（含导出期 FileX 关闭） */
  else
    local_health = DRMS_HEALTH_FAULT;
  if (owner)
    *owner = local_owner;
  if (health)
    *health = local_health;
}
