/*****************************************************************************
 * 文件：drms_application.c
 * 职责：应用协调层——把采集、记录、存储、协议、用户交互串成一台仪器的行为。
 *
 * 在整机中的位置（自上而下）：
 *     命令入口（ASCII/CDC 控制台、按键、USB 事件）
 *        ↓  统一成 DRMS_Command 投进 commands 队列
 *     本文件的应用线程（唯一消费者，串行处理）
 *        ↓  资源裁决：drms_control（谁在用 ADC、TF 卡、记录会话）
 *        ↓  记录会话：drms_record_session（起止边界、丢样记账）
 *        ↓  监测管线：drms_filter → classifier → baseline（判级）
 *     采集环 ← drms_acquisition ← DRDY 中断
 *
 * 并发模型（改动前必须理解）：
 *   · 本线程串行处理所有请求，因此状态机不需要为"并发请求"加锁；
 *   · FileX 线程独占 TF 介质，本线程只通过受控接口交接；
 *   · 中断侧只做"推送"——把帧塞进采集环并记数，不做解码与判级。
 *
 * 一次测量要经过的环节：
 *   DRDY → 采集环 → drain_frames 取帧 → 解码（CRC/量程/激励检查）
 *   → 若在记录窗口内则入记录环 → 监测管线算电阻与等级 → 发布快照
 *
 * 关键设计取舍：
 *   · 记录窗口内外的处理不同：窗口内要额外做边界记账与完整性判定，
 *     窗口外只需驱动监测。这条分支是整机最容易被改错的地方。
 *   · 高速档（>32 kSPS）走纯直录：跳过逐帧解码与监测，直接把原始帧写盘，
 *     因为没有足够时间做实时处理。代价是记录期间没有实时读数。
 *   · `r_valid` 只有在"帧有效 + 激励正常 + 电阻可算"三者同时成立时才置 1；
 *     任何一项不满足都必须报 0，不能让过期读数冒充当前值。
 *****************************************************************************/

#include "drms_application.h"
#include "drms_command.h"
#include "drms_architecture_contract.h"
#include "drms_control.h"
#include "drms_record_session.h"
#include "drms_acquisition.h"
#include "drms_measurement.h"
#include "drms_calibration.h"
#include "drms_user_config.h"
#include "drms_config_snapshot.h"
#include "drms_baseline.h"
#include "drms_msc.h"
#include "drms_capture_time.h"
#include "drms_logging.h"
#include "drms_log_codec.h"
#include "drms_storage.h"
#include "drms_file_service.h"
#include "drms_time.h"
#include "drms_usb.h"
#include "drms_boot_identity.h"
#include "drms_runtime.h"
#include "drms_power.h"
#include "../../App/interfaces/local_ui/drms_button.h"
#include "../../App/interfaces/cdc/drms_config_wire.h"
#include "main.h"
#include "tx_api.h"
#include <stdio.h>
#include <string.h>

/* 应用协调层（T7）：控制裁决（T1）→ 记录会话边界（T2a）→ 采样管线（T6）。
 * 本线程（主线程/控制上下文）串行处理请求；FileX 线程独占介质；ISR 只推送。
 * 开机自动监测（默认 4 kSPS），记录仅显式请求；无卡可监测。 */
#define DRMS_APP_DEFAULT_RATE 4000u
#define DRMS_APP_MONITOR_TICK_MS 10u
#define DRMS_APP_CONTEXT_BYTES DRMS_MONITOR_CONTEXT_BYTES

static TX_QUEUE commands;
static ULONG command_memory[16 * (sizeof(DRMS_Command) / sizeof(ULONG))];
static DRMS_Calibration calibration;
static DRMS_Sample latest;
static DRMS_Time clock_snapshot;
static volatile uint32_t ready, stop_requested;
static DRMS_Button measurement_button, power_button;
static uint32_t cal_active, cal_count, cal_result, cal_started, cal_dirty;
static uint32_t protocol_cal_active, protocol_cal_rate, protocol_cal_timeout;
static uint32_t protocol_cal_overruns, protocol_cal_drops, protocol_cal_previous, protocol_cal_have_previous;
static DRMS_Token protocol_cal_token;
static DRMS_Result protocol_cal_result;
static DRMS_Calibration protocol_cal_candidate;
static int64_t voltage_sum, sense_sum;
static double requested_reference;
static uint32_t crc_bad, adc_faults, consecutive_bad;
static uint32_t r_valid, last_cmd, cmd_result, last_aux, last_display;
static int32_t r_milliohms;

/* 记录会话（T2a）与监测管线（T6） */
static _Alignas(8) uint8_t monitor_store[DRMS_APP_CONTEXT_BYTES];
static DRMS_MonitorContext *const monitor = (DRMS_MonitorContext *)monitor_store;
/* 监测输出：只由应用线程（监测的唯一属主）写入，读者在短临界区内整体拷贝。 */
static DRMS_MonitorOutput published_monitor;
static DRMS_ApplicationSnapshot published_status;
static DRMS_ApplicationRecord published_record;
static DRMS_ApplicationRecord record_history[4];
static uint32_t record_history_next, record_history_count;
static uint8_t monitor_levels[DRMS_MONITOR_INTERVALS_MAX];
static uint16_t monitor_interval_ids[DRMS_MONITOR_INTERVALS_MAX];
static uint8_t monitor_level_count;
static uint32_t boot_rate = DRMS_APP_DEFAULT_RATE;
/* 0 = no saved configuration, 1 = usable, 2 = saved configuration incompatible. */
static uint32_t config_state;
static uint64_t monitor_config_version;
static DRMS_Token session_token;
static DRMS_Token session_end_token;
static uint32_t session_end_active;
static uint64_t session_record_id;
static uint32_t session_armed;   /* prepare 已完成，等文件就绪+边界 B */
static uint32_t session_cancelled;
static DRMS_Result session_cancel_reason;
static uint32_t session_footer_requested;
static uint32_t session_duration_ms;
static uint64_t session_started_us;
/* 会话状态：三者的关系是 session_armed → session_active → session_stopping。
 *   armed     已提交开始请求，还在等文件与起始边界
 *   active    记录窗口已生效，帧正在往记录环里走
 *   stopping  已请求结束，正在等结束边界 E
 * 只有窗口真正生效（active）期间采到的帧才属于这次记录。 */
static uint32_t session_stopping;/* request_stop 已发，等 E */
static uint32_t session_active;  /* classify/记录窗口生效中 */
static uint64_t consumed_raw;    /* 消费端 raw_ticket 水位 */
static DRMS_CaptureBoundary begin_boundary;
static uint32_t have_begin;
static DRMS_TimeAnchor nominal_anchor;  /* T7 过渡：以 wall-clock 为锚（板测换 DRDY 实测，见 T8） */
static DRMS_End session_end;
static DRMS_Token msc_token;
static uint32_t msc_active, msc_reported;
static DRMS_Token msc_release_token;
static uint32_t msc_release_active;
static DRMS_Token file_token;
static uint64_t file_open_ticket;
static uint64_t file_close_ticket;
static uint32_t file_active, file_opened;
static uint32_t file_listing;
static uint32_t file_close_pending;
static uint32_t file_revoked_session;
static DRMS_FileReply file_open_reply;
static DRMS_ApplicationFile published_file;
static DRMS_ApplicationFileList published_file_list;
static DRMS_BaselineContext baseline;
static DRMS_Token baseline_token;
static uint64_t baseline_version, baseline_ticket;
static uint32_t baseline_active, baseline_rate, baseline_started, baseline_timeout_ms;
static uint32_t baseline_overruns, baseline_drops, baseline_first_seq, baseline_previous_seq;
static DRMS_Result baseline_failure;
static uint32_t priority_stop_active, priority_stop_started, priority_stop_had_record;
/* 配置编码用的暂存缓冲。只有串行化的应用线程会碰它，因此不需要保护。 */
static uint8_t config_candidate[DRMS_USER_BODY_MAX];
static uint64_t config_view_running, config_view_saved;
static uint32_t config_view_current;
static uint32_t begin(uint32_t rate, uint32_t reference);
static void configure_monitor(uint32_t rate);

/* 发布文件操作的当前视图，供协议层读取。
 *
 * 这类"发布—快照"成对出现，因为读者在别的线程（CDC 接收线程），而写者只有
 * 应用线程。用关中断保护一次结构体拷贝，比引入互斥量更轻。
 * 注意：发布的内容必须是自洽的完整视图，不能让读者看到半更新状态。 */
static void file_publish(const DRMS_ApplicationFile *view)
{
  uint32_t mask = __get_PRIMASK(); __disable_irq();
  published_file = *view;
  __set_PRIMASK(mask);
}
/* 取文件视图的快照。
 * 返回非 0 表示当前有活跃的文件操作；out 为 NULL 时只查询有无。 */
uint32_t drms_application_file_snapshot(DRMS_ApplicationFile *out)
{
  if (!out) return 0;
  uint32_t mask = __get_PRIMASK(); __disable_irq();
  *out = published_file;
  __set_PRIMASK(mask);
  return out->operation != 0;
}
/* 发布文件列表的当前视图，语义同 file_publish。 */
static void file_list_publish(const DRMS_ApplicationFileList *view)
{
  uint32_t mask=__get_PRIMASK(); __disable_irq(); published_file_list=*view; __set_PRIMASK(mask);
}
/* 取文件列表视图的快照；返回值含义同 file_snapshot。 */
uint32_t drms_application_file_list_snapshot(DRMS_ApplicationFileList *out)
{
  if (!out) return 0;
  uint32_t mask=__get_PRIMASK(); __disable_irq(); *out=published_file_list; __set_PRIMASK(mask);
  return out->operation != 0;
}
/* USB 断线时撤销该会话的所有文件操作。
 *
 * 记录一个"已撤销到的会话号"水位：晚到的、属于旧会话的请求会因低于水位
 * 而被拒，避免断线后旧请求把新会话的句柄搅乱。 */
void drms_application_file_disconnect(uint32_t session)
{
  if (!session) return;
  uint32_t mask = __get_PRIMASK(); __disable_irq();
  if (session > file_revoked_session) __atomic_store_n(&file_revoked_session, session, __ATOMIC_RELEASE);
  __set_PRIMASK(mask);
  drms_file_service_disconnect(session);
}
/* 关闭一个文件下载句柄。
 *
 * 只允许关"自己的、进行中的"句柄：会话或操作号不符、或会话已被断线撤销，
 * 一律返回 STALE，避免旧会话的迟到请求动到新会话的资源。
 * 关闭是异步的——真正关文件要等 FileX 线程做完在途 I/O。 */
DRMS_Result drms_application_file_close(uint32_t session, uint64_t operation)
{
  DRMS_ApplicationFile view;
  if (!session || !operation || !drms_application_file_snapshot(&view) ||
      view.session != session || view.operation != operation || view.phase != 1u ||
      session <= __atomic_load_n(&file_revoked_session, __ATOMIC_ACQUIRE)) return DRMS_STALE;
  DRMS_FileRequest request = {.kind = DRMS_FILE_CLOSE, .session = session, .generation = view.generation};
  uint64_t ticket;
  uint32_t mask = __get_PRIMASK(); __disable_irq();
  DRMS_Result result = drms_file_service_submit(&request, &ticket);
  if (result == DRMS_ACCEPTED)
  {
    file_close_ticket = ticket; file_close_pending = 1;
  }
  __set_PRIMASK(mask);
  if (result == DRMS_ACCEPTED && session <= __atomic_load_n(&file_revoked_session, __ATOMIC_ACQUIRE))
    drms_file_service_disconnect(session);
  return result;
}

/* 发布记录视图，并顺手维护一小段历史。
 *
 * 协议允许主机按记录号查询"当前或最近几条"记录。这里在发布新视图前，
 * 若上一条已经结束（phase=2）就把它推进环形历史（容量 4 条）。
 * 更早的记录以卡上的文件为准，不再保留在内存里。 */
static void record_publish(const DRMS_ApplicationRecord *view)
{
  uint32_t mask = __get_PRIMASK();
  __disable_irq();
  if (published_record.record && published_record.record != view->record && published_record.phase == 2u)
  {
    record_history[record_history_next] = published_record;
    record_history_next = (record_history_next + 1u) % 4u;
    if (record_history_count < 4u) ++record_history_count;
  }
  published_record = *view;
  __set_PRIMASK(mask);
}

/* 按记录号取记录摘要。
 *
 * id 为 0 时取当前记录。找不到返回 INVALID：可能是编号从未分配，
 * 也可能是已经超出保留窗口，二者对主机而言都是"查不到"，
 * 更早的数据应当去读卡上的文件。 */
DRMS_Result drms_application_record_snapshot(uint64_t id, DRMS_ApplicationRecord *out)
{
  if (!out) return DRMS_INVALID;
  uint32_t mask = __get_PRIMASK();
  __disable_irq();
  *out = published_record;
  if (id && id != out->record)
  {
    for (uint32_t i = 0; i < record_history_count; ++i)
    {
      uint32_t index = (record_history_next + 4u - 1u - i) % 4u;
      if (record_history[index].record == id)
      {
        *out = record_history[index];
        break;
      }
    }
  }
  __set_PRIMASK(mask);
  if (id && id != out->record)
  {
    DRMS_Result result;
    DRMS_Result status = drms_control_record_admission(id, &result);
    if (status == DRMS_OK)
    {
      memset(out, 0, sizeof(*out));
      out->record = id;
      out->result = result;
      out->phase = result == DRMS_ACCEPTED ? 0u : 2u;
      return DRMS_OK;
    }
    return status;
  }
  if (!out->record || (id && id > out->record)) return DRMS_INVALID;
  if (id && id < out->record) return DRMS_STALE;
  return DRMS_OK;
}

/* 小端写入辅助：配置编码统一用无填充小端，与协议一致。
 * 这两个函数只在本文件的配置打包路径里用。 */
static void config_put32(uint8_t *p, uint32_t n)
{
  for (unsigned i = 0; i < 4; ++i) p[i] = (uint8_t)(n >> (8u * i));
}
/* 小端写入一个 double：先按位重解释成 64 位整数，再逐字节展开。
 * 不依赖主机浮点表示以外的东西，与协议规定的无填充小端一致。 */
static void config_put_double(uint8_t *p, double value)
{
  uint64_t bits;
  memcpy(&bits, &value, sizeof(bits));
  for (unsigned i = 0; i < 8; ++i) p[i] = (uint8_t)(bits >> (8u * i));
}

/* 把一个"仅记录用"的校准备注塞进配置块，但不动用户已保存的配置，
 * 也不改 v2 记录块的冻结布局。
 *
 * 做法是在 schema1 里追加一个未知 TLV：读取方按长度跳过它，因此向后兼容；
 * 而需要知道"这条记录是用哪代校准测的"的地方可以解析它。 */
static uint32_t record_config_with_calibration(uint32_t length, uint64_t boot)
{
  if (!length)
  {
    memset(config_candidate, 0, 40);
    memcpy(config_candidate, "DRMSUC01", 8);
    length = 44;
  }
  uint32_t extra = 32u + (boot ? 12u : 0u);
  if (length < 44u || length > sizeof(config_candidate) - extra) return 0;
  uint32_t offset = 40;
  while (offset < length - 4u)
  {
    if (length - 4u - offset < 4u) return 0;
    uint16_t type = (uint16_t)(config_candidate[offset] | ((uint16_t)config_candidate[offset+1] << 8));
    uint16_t size = (uint16_t)(config_candidate[offset+2] | ((uint16_t)config_candidate[offset+3] << 8));
    offset += 4u;
    if (size > length - 4u - offset || type == 0xd703u || type == 0xd704u) return 0;
    offset += size;
  }
  if (offset != length - 4u) return 0;
  config_candidate[offset++] = 0x03; config_candidate[offset++] = 0xd7;
  config_candidate[offset++] = 28; config_candidate[offset++] = 0;
  config_put32(config_candidate+offset, calibration.valid); offset += 4;
  config_put32(config_candidate+offset, calibration.generation); offset += 4;
  config_put32(config_candidate+offset, calibration.rate); offset += 4;
  config_put_double(config_candidate+offset, calibration.scale); offset += 8;
  config_put_double(config_candidate+offset, calibration.reference_ohms); offset += 8;
  if (boot)
  {
    config_candidate[offset++] = 0x04; config_candidate[offset++] = 0xd7;
    config_candidate[offset++] = 8; config_candidate[offset++] = 0;
    for (unsigned i = 0; i < 8; ++i) config_candidate[offset++] = (uint8_t)(boot >> (8u*i));
  }
  config_put32(config_candidate+8, offset + 4u);
  config_put32(config_candidate+offset, drms_crc32(config_candidate, offset));
  return offset + 4u;
}

/* 刷新配置快照。应用线程是配置的唯一写者与发布者，因此这里不需要加锁。
 *
 * 只有当运行版或已存版发生变化时才重新编码，避免每轮都做一次 CRC。
 * 发布失败（读者正持有目标）时把 valid 置 0，留到下一轮重试——
 * 不在这里忙等。 */
static void publish_config_view(void)
{
  uint64_t running = drms_user_config_run_version();
  uint64_t saved = drms_user_config_persisted_version();
  if (config_view_current && running == config_view_running && saved == config_view_saved) return;
  uint32_t n = drms_user_config_get_wire(config_candidate, DRMS_CONFIG_SNAPSHOT_MAX);
  if (!n)
  {
    drms_config_snapshot_invalidate();
    config_view_running = running; config_view_saved = saved; config_view_current = 1;
    return;
  }
  if (!drms_config_snapshot_publish(config_candidate, n, running, saved))
  {
    drms_config_snapshot_invalidate();
    config_view_current = 0; /* a reader pins the target: retry on next poll */
    return;
  }
  config_view_running = running; config_view_saved = saved; config_view_current = 1;
}

/* 从一段 TLV 载荷里按 tag 取出一个 u32。
 * 找不到返回 0。用于解析主机通过 APPLY_CONFIG 下发的配置。 */
static uint32_t config_wire_u32(const uint8_t *payload, size_t length, uint16_t wanted)
{
  size_t offset = 0;
  while (length - offset >= 4u)
  {
    uint16_t tag = (uint16_t)(payload[offset] | ((uint16_t)payload[offset + 1] << 8));
    uint16_t size = (uint16_t)(payload[offset + 2] | ((uint16_t)payload[offset + 3] << 8));
    offset += 4u;
    if (size > length - offset) return 0;
    if ((tag & 0x7fffu) == wanted && size == 4u)
      return (uint32_t)payload[offset] | ((uint32_t)payload[offset+1] << 8) |
             ((uint32_t)payload[offset+2] << 16) | ((uint32_t)payload[offset+3] << 24);
    offset += size;
  }
  return 0;
}

/* 控制台命令入口（ASCII v1）。调用者可以是任意线程，本函数只做解析与入队。
 *
 * 返回：1 已受理（或 STOP 已置标志）；-2 队列满/未就绪/正在关机；
 * 其他值来自 drms_command_parse（0 表示命令不认识）。
 *
 * STOP 特意走独立标志而不进队列：它是取消屏障，必须能插到所有排队命令之前，
 * 否则主机先发一串 START 再发 STOP，STOP 会排在它们后面，起不到"立即停"的作用。 */
int drms_console_dispatch(const char *line)
{
  DRMS_Command command;
  int result = drms_command_parse(line, &command);
  if (result != 1)
    return result;
  if (command.id == DRMS_CMD_STOP)
  {
    __atomic_store_n(&stop_requested, 1U, __ATOMIC_RELEASE);
    return 1;
  }
  if (drms_shutdown_requested || !ready || tx_queue_send(&commands, &command, TX_NO_WAIT) != TX_SUCCESS)
    return -2;
  return 1;
}

/* ---- 控制裁决投递钩子（T1）：reserve 成功后由 poll 调用一次 ---- */


static void session_cancel_local(DRMS_Result reason)
{
  if ((session_armed || session_active) && !session_cancelled)
  {
    /* 文件已经正常收尾并关闭的，不能再被追溯成"取消"——那样会让一份
     * 完整的数据被标成不完整。 */
    if (session_active && session_footer_requested && !drms_log_state)
      return;
    if (session_armed)
      (void)drms_control_report(session_token, reason);
    drms_acq_boundary_cancel(session_token);
    drms_record_session_cancel(session_token, reason);
    drms_log_stop_incomplete();
    session_armed = 0;
    session_active = 1; /* retain ownership until the storage close is confirmed */
    session_stopping = 0;
    session_cancelled = 1;
    session_cancel_reason = reason;
    session_footer_requested = 0;
  }
}

/* 控制请求的实际执行入口。
 *
 * 请求已经过 drms_control 的资源裁决与排队，这里按操作类型分派具体动作。
 * 返回值即该操作的最终结果；需要异步完成的（记录启停、校准、导出）
 * 先返回 ACCEPTED，最终结果稍后通过 drms_control_complete 归结。
 *
 * token 用于把这些异步操作的结果关联回发起方，本函数自身不用它。 */
static DRMS_Result app_dispatch(const DRMS_Token *token, const DRMS_ControlRequest *request)
{
  (void)token;
  last_cmd = (uint32_t)request->operation;
  switch (request->operation)
  {
    case DRMS_OP_SET_UTC:
    {
      char iso[20];
      if (!drms_time_epoch_to_iso(request->expected_version, iso)) return DRMS_INVALID;
      if (!drms_time_set(iso)) return DRMS_IO_ERROR;
      drms_time_get(&clock_snapshot);
      return DRMS_OK;
    }
    case DRMS_OP_RESUME_MONITOR:
    {
      if (drms_shutdown_requested)
        return DRMS_CANCELLED;
      if (session_active || session_armed || drms_log_state || cal_active || baseline_active)
        return DRMS_BUSY;
      if (drms_acq_running)
        return drms_acq_reference ? DRMS_BUSY : DRMS_NO_CHANGE;
      DRMS_ControlSnapshot control;
      drms_control_get_snapshot(&control);
      if ((control.quarantined_mask & DRMS_RES_ACQUISITION_CONFIG) || !drms_acq_is_quiescent())
        return DRMS_QUARANTINED;
      DRMS_Result resumed = drms_control_resume_for(*token);
      if (resumed != DRMS_OK)
        return resumed;
      if (begin(boot_rate, 0) != 0)
      {
        drms_control_stop();
        return DRMS_IO_ERROR;
      }
      return DRMS_OK;
    }
    case DRMS_OP_RECORD:
    {
      if (!drms_acq_running || drms_acq_reference || cal_active)
        return DRMS_INVALID;
      if (drms_msc_blocks_recording())
        return DRMS_BUSY;
      if (!request->record_id)
        return DRMS_INVALID;
      session_record_id = request->record_id;
      session_token = *token;
      DRMS_Result rc = drms_record_prepare(*token, session_record_id);
      if (rc != DRMS_ACCEPTED)
        return rc;
      uint32_t wire_length = drms_user_config_get_wire(config_candidate, sizeof(config_candidate));
      session_duration_ms = wire_length ? config_wire_u32(config_candidate, wire_length, 73u) : 0;
      /* CDC 把 expected_version 当作"是否带时长"的标志：
       * 带了就以它为准，其中 0 是明确表示"手动结束"，不是"用默认值"。
       * ASCII 入口没有这个标志，只能从配置里读默认时长。 */
      if (request->source == DRMS_SOURCE_CDC && request->expected_version == 1u)
        session_duration_ms = request->value;
      session_started_us = 0;
      uint32_t config_length = drms_user_config_export(config_candidate, sizeof(config_candidate));
      uint32_t metadata_only = !config_length;
      config_length = record_config_with_calibration(config_length, drms_boot_identity_get());
      DRMS_LogV2Meta metadata = {
        .flags = 1u | (metadata_only ? 2u : 0u), .rate_hz = drms_acq_rate,
        .uid_w0 = HAL_GetUIDw0(), .uid_w1 = HAL_GetUIDw1(), .uid_w2 = HAL_GetUIDw2(),
        .record_id = session_record_id, .anchor = nominal_anchor,
        .config = config_length ? config_candidate : NULL, .config_len = (uint16_t)config_length};
      if (!config_length || !drms_log_start_v2(&metadata))
      {
        drms_record_session_cancel(*token, DRMS_IO_ERROR);
        (void)drms_record_end_ack(*token, DRMS_IO_ERROR);
        return DRMS_IO_ERROR;
      }
      session_armed = 1;
      session_cancelled = 0;
      session_cancel_reason = DRMS_OK;
      session_footer_requested = 0;
      DRMS_ApplicationRecord view = {.record = session_record_id, .phase = 0, .result = DRMS_ACCEPTED};
      record_publish(&view);
      return DRMS_ACCEPTED; /* 文件就绪+边界 B 在 poll 中归结 */
    }
    case DRMS_OP_END_RECORD:
    {
      if (request->source != DRMS_SOURCE_CDC || !request->session || !request->expected_version)
        return DRMS_INVALID;
      if ((!session_active && !session_armed) || request->expected_version != session_record_id)
        return DRMS_INVALID;
      if (session_end_active || session_stopping || session_cancelled)
        return DRMS_BUSY;
      session_end_token = *token;
      session_end_active = 1;
      if (session_armed)
        session_cancel_local(DRMS_CANCELLED);
      else
      {
        drms_record_session_request_stop();
        session_stopping = 1;
        session_duration_ms = 0;
      }
      return DRMS_ACCEPTED;
    }
    case DRMS_OP_MSC_EXPORT:
    {
      DRMS_Result result = drms_msc_request_export();
      if (result == DRMS_ACCEPTED)
      {
        msc_token = *token;
        msc_active = 1;
        msc_reported = 0;
      }
      return result;
    }
    case DRMS_OP_MSC_RELEASE:
    {
      if (msc_release_active)
        return DRMS_BUSY;
      DRMS_Result result = drms_msc_request_release();
      if (result == DRMS_ACCEPTED)
      {
        msc_release_token = *token;
        msc_release_active = 1;
      }
      return result;
    }
    case DRMS_OP_BASELINE_R0:
    {
      DRMS_BaselinePolicy policy;
      if (!drms_acq_running || drms_acq_reference || cal_active ||
          !drms_user_config_get_baseline_policy(&policy) ||
          drms_user_config_baseline_rate() != drms_acq_rate)
        return DRMS_INVALID;
      if (policy.min_duration_us > 3600000000ULL)
        return DRMS_INVALID;
      uint64_t count_ms = ((uint64_t)policy.min_count * 1000u + drms_acq_rate - 1u) / drms_acq_rate;
      uint64_t duration_ms = (policy.min_duration_us + 999u) / 1000u;
      uint64_t expected_ms = count_ms > duration_ms ? count_ms : duration_ms;
      if (expected_ms > 3600000u)
        return DRMS_INVALID;
      drms_baseline_configure(&baseline, policy.min_count, policy.min_duration_us, policy.max_cv);
      baseline_token = *token;
      baseline_version = drms_user_config_run_version();
      baseline_ticket = drms_acq_raw_ticket_next();
      baseline_rate = drms_acq_rate;
      baseline_started = HAL_GetTick();
      baseline_timeout_ms = (uint32_t)expected_ms + 30000u;
      baseline_overruns = drms_acq_overruns;
      baseline_drops = drms_acq_queue_drops;
      baseline_failure = DRMS_OK;
      baseline_active = 1;
      return DRMS_ACCEPTED;
    }
    case DRMS_OP_CONFIG_SAVE:
    {
      if (request->expected_version != drms_user_config_run_version())
        return DRMS_STALE;
      if (!drms_user_config_dirty())
        return DRMS_NO_CHANGE;
      if (cal_active || drms_acq_reference)
        return DRMS_BUSY;
      uint32_t was_running = drms_acq_running;
      uint32_t rate = drms_acq_rate;
      if (was_running)
        drms_acq_stop();
      if (!drms_acq_is_quiescent())
      {
        (void)drms_control_complete(*token, DRMS_QUARANTINED,
                                    DRMS_RES_TF_ACCESS | DRMS_RES_FLASH_MAINTENANCE);
        return DRMS_ACCEPTED;
      }
      DRMS_Result result = drms_user_config_save(request->expected_version);
      publish_config_view();
      if (was_running && begin(rate, 0) != 0)
      {
        if (!drms_acq_is_quiescent())
        {
          (void)drms_control_complete(*token, DRMS_QUARANTINED,
                                      DRMS_RES_TF_ACCESS | DRMS_RES_FLASH_MAINTENANCE);
          return DRMS_ACCEPTED;
        }
        result = DRMS_IO_ERROR;
      }
      return result;
    }
    case DRMS_OP_CONFIG_APPLY:
    {
      if (!request->payload || !request->payload_length || drms_shutdown_requested)
        return DRMS_INVALID;
      if (cal_active || baseline_active || drms_acq_reference)
        return DRMS_BUSY;
      size_t size = drms_config_wire_to_body(request->payload, request->payload_length,
                                             config_candidate, sizeof(config_candidate));
      if (!size) return DRMS_INVALID;
      DRMS_Result result = drms_user_config_preflight(config_candidate, size, request->expected_version);
      if (result != DRMS_OK) return result;
      uint32_t rate = config_wire_u32(request->payload, request->payload_length, 72u);
      uint32_t was_running = drms_acq_running;
      uint32_t old_rate = was_running ? drms_acq_rate : boot_rate;
      if (was_running) drms_acq_stop();
      if (!drms_acq_is_quiescent())
      {
        (void)drms_control_complete(*token, DRMS_QUARANTINED, DRMS_RES_FLASH_MAINTENANCE);
        return DRMS_ACCEPTED;
      }
      /* 先试跑新速率，成功了才发布配置。
       * 失败时旧配置仍然有效——只要采集后端是静止的，就按旧速率把采集恢复起来，
       * 不能让设备停在一个"配置没改成、采集也没了"的状态。 */
      if (was_running && begin(rate, 0) != 0)
      {
        if (!drms_acq_is_quiescent())
        {
          (void)drms_control_complete(*token, DRMS_QUARANTINED, DRMS_RES_FLASH_MAINTENANCE);
          return DRMS_ACCEPTED;
        }
        if (begin(old_rate, 0) != 0 && !drms_acq_is_quiescent())
        {
          (void)drms_control_complete(*token, DRMS_QUARANTINED, DRMS_RES_FLASH_MAINTENANCE);
          return DRMS_ACCEPTED;
        }
        return DRMS_IO_ERROR;
      }
      result = drms_user_config_apply(config_candidate, size, request->expected_version);
      if (result != DRMS_OK)
      {
        if (was_running)
        {
          drms_acq_stop();
          if (!drms_acq_is_quiescent())
          {
            (void)drms_control_complete(*token, DRMS_QUARANTINED, DRMS_RES_FLASH_MAINTENANCE);
            return DRMS_ACCEPTED;
          }
          if (begin(old_rate, 0) != 0 && !drms_acq_is_quiescent())
          {
            (void)drms_control_complete(*token, DRMS_QUARANTINED, DRMS_RES_FLASH_MAINTENANCE);
            return DRMS_ACCEPTED;
          }
        }
        return result;
      }
      boot_rate = rate;
      config_state = 1;
      configure_monitor(rate);
      publish_config_view();
      return DRMS_OK;
    }
    case DRMS_OP_FILE_DOWNLOAD:
    {
      if (request->source != DRMS_SOURCE_CDC || !request->session || request->expected_version > UINT32_MAX || file_active)
        return DRMS_INVALID;
      if (request->session <= __atomic_load_n(&file_revoked_session, __ATOMIC_ACQUIRE))
        return DRMS_CANCELLED;
      DRMS_FileRequest file = {.kind = DRMS_FILE_OPEN, .session = request->session,
        .generation = (uint32_t)request->expected_version, .file_id = request->value};
      DRMS_Result result = drms_file_service_submit(&file, &file_open_ticket);
      if (result != DRMS_ACCEPTED) return result;
      if (request->session <= __atomic_load_n(&file_revoked_session, __ATOMIC_ACQUIRE))
        drms_file_service_disconnect(request->session);
      file_token = *token; file_active = 1; file_opened = file_listing = 0;
      DRMS_ApplicationFile view = {.operation = token->operation_id, .session = request->session,
        .generation = file.generation, .phase = 0, .result = DRMS_ACCEPTED};
      file_publish(&view);
      return DRMS_ACCEPTED;
    }
    case DRMS_OP_FILE_LIST:
    {
      if (request->source != DRMS_SOURCE_CDC || !request->session || request->expected_version > UINT32_MAX ||
          request->value > 10000u || file_active) return DRMS_INVALID;
      if (request->session <= __atomic_load_n(&file_revoked_session, __ATOMIC_ACQUIRE)) return DRMS_CANCELLED;
      DRMS_FileRequest file={.kind=DRMS_FILE_LIST,.session=request->session,
        .generation=(uint32_t)request->expected_version,.cursor=request->value};
      DRMS_Result result=drms_file_service_submit(&file,&file_open_ticket);
      if (result != DRMS_ACCEPTED) return result;
      if (request->session <= __atomic_load_n(&file_revoked_session, __ATOMIC_ACQUIRE))
        drms_file_service_disconnect(request->session);
      file_token=*token; file_active=1; file_listing=1; file_opened=0;
      DRMS_ApplicationFileList view={.operation=token->operation_id,.session=request->session,
        .generation=file.generation,.cursor=file.cursor,.phase=0,.result=DRMS_ACCEPTED};
      file_list_publish(&view);
      return DRMS_ACCEPTED;
    }
    case DRMS_OP_CALIBRATE:
    {
      if (request->source != DRMS_SOURCE_CDC || !request->session ||
          !drms_acq_running || drms_acq_reference || cal_active || baseline_active ||
          session_active || session_armed || drms_log_state || drms_shutdown_requested)
        return DRMS_INVALID;
      protocol_cal_rate = drms_acq_rate;
      drms_acq_stop();
      if (!drms_acq_is_quiescent())
      {
        (void)drms_control_complete(*token, DRMS_QUARANTINED,
                                    DRMS_RES_TF_ACCESS | DRMS_RES_FLASH_MAINTENANCE);
        return DRMS_ACCEPTED;
      }
      if (begin(protocol_cal_rate, 1) != 0)
      {
        if (drms_acq_is_quiescent()) (void)begin(protocol_cal_rate, 0);
        if (!drms_acq_running && !drms_acq_is_quiescent())
        {
          (void)drms_control_complete(*token, DRMS_QUARANTINED,
                                      DRMS_RES_TF_ACCESS | DRMS_RES_FLASH_MAINTENANCE);
          return DRMS_ACCEPTED;
        }
        return DRMS_IO_ERROR;
      }
      protocol_cal_token = *token;
      protocol_cal_candidate = calibration;
      requested_reference = 100000.0;
      cal_count = 0; cal_result = 100; voltage_sum = sense_sum = 0;
      cal_started = HAL_GetTick();
      protocol_cal_timeout = (uint32_t)(((uint64_t)4096u * 1000u + protocol_cal_rate - 1u) / protocol_cal_rate) + 10000u;
      protocol_cal_overruns = drms_acq_overruns; protocol_cal_drops = drms_acq_queue_drops;
      protocol_cal_have_previous = 0; protocol_cal_result = DRMS_OK;
      protocol_cal_active = cal_active = 1;
      return DRMS_ACCEPTED;
    }
    case DRMS_OP_UPDATE:
      return DRMS_UNSUPPORTED; /* 非本阶段交付操作：明确拒绝而非静默 */
    default:
      return DRMS_INVALID;
  }
}

/* TF_ACCESS 的租约要跨越整个导出生命期，而不只是交接那一刻。
 *
 * U 盘导出期间文件系统已经关闭、介质归原始读使用，如果此时把租约放掉，
 * 别的路径（记录、文件下载）就会以为卡空闲而插进来，两头都坏。
 * 只有显式 MSC_RELEASE 完成重挂载后，租约才归还。 */
static void msc_service_control(void)
{
  if (msc_release_active && drms_msc_owner() == DRMS_OWNER_LOCAL)
  {
    DRMS_Result result = drms_msc_last_error();
    if (!drms_storage_mounted && result == DRMS_OK)
      result = DRMS_IO_ERROR;
    (void)drms_control_complete(msc_release_token, result, 0);
    msc_release_active = 0;
  }
  if (!msc_active)
    return;
  DRMS_Owner owner = drms_msc_owner();
  if (owner == DRMS_OWNER_EXPORTED && !msc_reported)
  {
    if (drms_control_report(msc_token, DRMS_OK) == DRMS_OK)
      msc_reported = 1;
  }
  else if (owner == DRMS_OWNER_LOCAL)
  {
    if (msc_reported)
      (void)drms_control_release(msc_token, DRMS_RES_TF_ACCESS);
    else
    {
      DRMS_Result result = drms_msc_last_error();
      (void)drms_control_complete(msc_token,
          result == DRMS_OK ? DRMS_CANCELLED : result, DRMS_RES_TF_ACCESS);
    }
    msc_active = 0;
    msc_reported = 0;
  }
}

/* 历史文件下载同样在 open→read→close 整段期间持有 TF 租约，
 * 原因与导出相同：期间的介质不能被别的路径并发使用。 */
static void file_service_control(void)
{
  if (!file_active) return;
  if (file_listing)
  {
    DRMS_ApplicationFileList list;
    if (!drms_application_file_list_snapshot(&list)) return;
    if (drms_file_service_quarantined())
    {
      list.phase=2; list.result=DRMS_QUARANTINED; file_list_publish(&list);
      (void)drms_control_complete(file_token,DRMS_QUARANTINED,0);
      file_active=file_listing=0; return;
    }
    DRMS_Result state=drms_file_service_take(file_open_ticket,&file_open_reply);
    if (state==DRMS_ACCEPTED || !drms_file_service_quiescent()) return;
    DRMS_Result result=state==DRMS_OK ? file_open_reply.result : DRMS_CANCELLED;
    list.phase=2; list.result=result; list.file_id=file_open_reply.file_id;
    list.size=file_open_reply.size; list.next_cursor=file_open_reply.next_cursor;
    file_list_publish(&list);
    (void)drms_control_complete(file_token,result,DRMS_RES_TF_ACCESS);
    file_active=file_listing=0; return;
  }
  DRMS_ApplicationFile view;
  if (!drms_application_file_snapshot(&view)) return;
  if (drms_file_service_quarantined())
  {
    view.phase = 2; view.result = DRMS_QUARANTINED;
    file_publish(&view);
    (void)drms_control_complete(file_token, DRMS_QUARANTINED, 0);
    file_active = 0;
    return;
  }
  if (!file_opened)
  {
    DRMS_Result state = drms_file_service_take(file_open_ticket, &file_open_reply);
    if (state == DRMS_ACCEPTED) return;
    if (state == DRMS_OK && file_open_reply.result == DRMS_OK)
    {
      view.size = file_open_reply.size; view.phase = 1; view.result = DRMS_OK;
      file_opened = 1;
      file_publish(&view);
      return;
    }
    if (!drms_file_service_quiescent()) return;
    DRMS_Result result = state == DRMS_OK ? file_open_reply.result : DRMS_CANCELLED;
    view.phase = 2; view.result = result; file_publish(&view);
    (void)drms_control_complete(file_token, result, DRMS_RES_TF_ACCESS);
    file_active = 0;
    return;
  }
  uint32_t mask = __get_PRIMASK(); __disable_irq();
  uint32_t closing = file_close_pending;
  uint64_t ticket = file_close_ticket;
  __set_PRIMASK(mask);
  if (closing)
  {
    DRMS_Result state = drms_file_service_take(ticket, &file_open_reply);
    if (state == DRMS_ACCEPTED) return;
    if (!drms_file_service_quiescent()) return;
    DRMS_Result result = state == DRMS_OK ? file_open_reply.result : DRMS_CANCELLED;
    view.phase = 2; view.result = result; file_publish(&view);
    (void)drms_control_complete(file_token, result, DRMS_RES_TF_ACCESS);
    file_active = 0;
    mask = __get_PRIMASK(); __disable_irq(); file_close_pending = 0; __set_PRIMASK(mask);
    return;
  }
  if (drms_file_service_quiescent())
  {
    DRMS_Result result = drms_file_service_last_result();
    view.phase = 2; view.result = result; file_publish(&view);
    (void)drms_control_complete(file_token, result, DRMS_RES_TF_ACCESS);
    file_active = 0;
  }
}

/* ---- 会话边界归结（poll 上下文） ---- */

static void session_service(uint32_t now_ms)
{
  if (session_armed)
  {
    /* R1：文件就绪 → 一致边界 B → ready（同一轮内归结，避免跨轮悬挂） */
    if (drms_log_state == 0)
    {
      session_cancel_local(DRMS_IO_ERROR); /* 文件建立失败/被外部关闭 */
      last_cmd = DRMS_OP_RECORD;
      cmd_result = 5;
      return;
    }
    if (!drms_log_running)
      return; /* 存储线程仍在建文件 */
    if (!drms_acq_running)
    {
      (void)drms_log_stop(); /* 采集已停：无法取得 B，取消本次记录 */
      session_cancel_local(DRMS_INCOMPLETE);
      cmd_result = 5;
      return;
    }
    DRMS_CaptureBoundary b;
    if (drms_acq_boundary_get(session_token, &b) != DRMS_OK)
    {
      (void)drms_acq_boundary_request(session_token);
      drms_acq_boundary_service();
      if (drms_acq_boundary_get(session_token, &b) != DRMS_OK)
        return; /* 下一轮再取 */
    }
    if (drms_record_ready(session_token, b) == DRMS_OK)
    {
      begin_boundary = b;
      have_begin = 1;
      session_armed = 0;
      session_active = 1;
      session_started_us = drms_acq_now_us();
      DRMS_ApplicationRecord view = {.record = session_record_id, .phase = 1, .result = DRMS_ACCEPTED};
      record_publish(&view);
      (void)drms_control_report(session_token, DRMS_OK);
      cmd_result = 0;
    }
    else
    {
      session_cancel_local(DRMS_IO_ERROR);
      cmd_result = 5;
    }
    (void)now_ms;
  }
  if (session_stopping)
  {
    /* 先把已经完成的结束边界 E 消费掉，再发新的请求。
     * 因为两次轮询之间 DMA 回调可能已经发布了 E，而更新的 DRDY 仍在不断到达；
     * 不先取走就会拿着旧的请求去对新的边界。 */
    DRMS_CaptureBoundary e;
    DRMS_Result eg = drms_acq_boundary_get(session_token, &e);
    if (eg != DRMS_OK)
    {
      DRMS_Result erq = drms_acq_boundary_request(session_token);
      if (erq == DRMS_INVALID)
      {
        session_cancel_local(DRMS_INCOMPLETE);
        return;
      }
      drms_acq_boundary_service();
      eg = drms_acq_boundary_get(session_token, &e);
    }
    if (eg == DRMS_OK)
    {
      (void)drms_record_stop_at(session_token, e);
      session_stopping = 0;
    }
  }
}

/* ---- 采样管线：会话分类 + 监测 step ---- */

static uint64_t nominal_us_of(uint64_t sample_seq)
{
  return drms_capture_time_nominal_us(&nominal_anchor, sample_seq);
}

/* 处理一帧：这是整机数据处理的分岔点，改动前务必读完整注释。
 *
 * 一帧进来先按 ticket 问"该不该记录"——记录会话给出三种判决：
 *   记录（落在记录窗口内）／跳过（早于起点）／仅监测（晚于终点或没在记录）。
 *
 * 随后按速率分成两条路：
 *   · 32 kSPS 以上：纯直录。只把原始帧塞进记录环，不解码、不监测、不判级。
 *     因为高速档没有时间做逐帧处理，强行做只会丢帧；数据事后离线分析。
 *     代价是记录期间没有实时读数，且不累计坏帧统计（没做 CRC 校验）。
 *   · 32 kSPS 及以下：完整处理。解码（CRC/量程/激励）→ 边界记账 → 驱动监测管线。
 *
 * 为什么记录窗口内外要分开处理：窗口内要额外做边界与完整性记账
 * （首末样本号、丢样、未知损失），这些在纯监测时不需要，混在一起会让
 * 两条路径互相干扰。
 *
 * 参数：frame 原始帧；ticket 消费端票号（与记录会话的边界对齐）；
 *       capture_lower_us 该帧捕获时间的下界。 */
static void pipeline_step_frame(const DRMS_RawFrame *frame, uint64_t ticket,
                                uint64_t capture_lower_us)
{
  DRMS_RecordVerdict verdict = session_active
                                   ? drms_record_session_classify(ticket)
                                   : DRMS_RECORD_MONITOR;
  /* 纯直录模式：32 kSPS 以上，逐帧解码与监测放不进帧预算。
   *
   * 此时记录窗口退化成纯粹的捕获：原始帧直接进记录环，别的什么都不做。
   * 代价有三条，都是明知的选择：
   *   1. 记录期间没有实时读数——数据留给事后离线分析；
   *   2. 不累计 quality_bad，因为这里根本没做 CRC 校验；
   *   3. 记录窗口外的监测同样跳过（速率太高时监测也跟不上）。
   * 32 kSPS 及以下不走这条分支，行为与以前完全一致。 */
  if (drms_acq_rate > 32000u)
  {
    if (verdict == DRMS_RECORD_RECORD)
    {
      int ok = drms_log_enqueue(frame);
      drms_record_session_note_recorded(frame->sequence, 0u, ok ? 1u : 0u);
      drms_record_session_note_log_ticket(drms_log_ticket_next());
    }
    return;
  }
  if (verdict == DRMS_RECORD_RECORD)
  {
    int ok = drms_log_enqueue(frame);
    /* 32 位序号由处理端按锚点顺序扩展：monitor 直接用 64 位序号输入 */
    uint64_t sample_seq = frame->sequence;
    if (have_begin)
      sample_seq = begin_boundary.sample_next + (int32_t)(frame->sequence - (uint32_t)begin_boundary.sample_next);
    uint64_t nominal = nominal_us_of(sample_seq);
    uint64_t lower = capture_lower_us;
    DRMS_MonitorInput input = {
      .ohms = 0.0, .capture_us = nominal, .capture_lower_bound_us = lower,
      .sample_seq = sample_seq, .acquisition_generation = drms_acq_generation(),
      .quality_flags = 0, .config_version = monitor_config_version,
      .baseline_version = monitor_config_version};
    DRMS_Sample sample;
    if (drms_decode_frame(frame->bytes, &sample))
    {
      input.quality_flags = sample.flags;
      double ohms;
      if (!sample.flags && drms_excitation_ok(&sample) &&
          drms_resistance(&sample, calibration.scale, &ohms))
        input.ohms = ohms;
      else if (!sample.flags)
        input.quality_flags = DRMS_SAMPLE_RANGE_ERROR;
    }
    else
      input.quality_flags = DRMS_SAMPLE_FORMAT_ERROR;
    drms_record_session_note_recorded(frame->sequence,
                                      input.quality_flags ? 1u : 0u, ok ? 1u : 0u);
    drms_record_session_note_log_ticket(drms_log_ticket_next());
    if (!input.quality_flags)
    {
      DRMS_MonitorOutput out;
      drms_monitor_step(monitor, &input, &out);
    }
    else
    {
      DRMS_MonitorInput bad = input;
      bad.ohms = 0.0;
      DRMS_MonitorOutput out;
      drms_monitor_step(monitor, &bad, &out); /* 质量故障路径：算法重置 */
    }
  }
  else
  {
    /* 监测帧（非记录窗口）：同样驱动监测管线 */
    DRMS_MonitorInput input = {
      .ohms = 0.0, .capture_us = nominal_us_of(frame->sequence),
      .capture_lower_bound_us = capture_lower_us,
      .sample_seq = frame->sequence,
      .acquisition_generation = drms_acq_generation(),
      .quality_flags = 0, .config_version = monitor_config_version,
      .baseline_version = monitor_config_version};
    DRMS_Sample sample;
    if (drms_decode_frame(frame->bytes, &sample))
    {
      input.quality_flags = sample.flags;
      double ohms;
      if (!sample.flags && drms_excitation_ok(&sample) &&
          drms_resistance(&sample, calibration.scale, &ohms))
        input.ohms = ohms;
      else if (!sample.flags)
        input.quality_flags = DRMS_SAMPLE_RANGE_ERROR;
    }
    else
      input.quality_flags = DRMS_SAMPLE_FORMAT_ERROR;
    DRMS_MonitorOutput out;
    drms_monitor_step(monitor, &input, &out);
  }
}

/* 把采集环里积压的帧全部处理掉。
 *
 * 每次调用最多处理 4096 帧（等于环深），避免在积压很多时长时间不让出 CPU。
 * 主循环每轮都会调用，正常情况下每轮只有寥寥几帧。
 *
 * 注意：这里的上限与采集环容量一致不是巧合——它保证一轮就能排空，
 * 不会出现"永远追不上生产者"的情况。 */
static void drain_frames(void)
{
  DRMS_RawFrame frame;
  unsigned int limit = 4096;
  uint64_t capture_lower_us;
  while (limit-- && drms_acq_pop_timed(&frame, &capture_lower_us))
  {
    pipeline_step_frame(&frame, consumed_raw, capture_lower_us);
    if (baseline_active && consumed_raw >= baseline_ticket && baseline_failure == DRMS_OK)
    {
      DRMS_Sample sample;
      double ohms;
      if (!drms_decode_frame(frame.bytes, &sample) || !drms_excitation_ok(&sample) ||
          !drms_resistance(&sample, calibration.scale, &ohms) || ohms <= 0.0 ||
          (baseline.count && frame.sequence != baseline_previous_seq + 1u))
        baseline_failure = DRMS_INCOMPLETE;
      else
      {
        if (!baseline.count)
          baseline_first_seq = frame.sequence;
        uint64_t elapsed = ((uint64_t)(uint32_t)(frame.sequence - baseline_first_seq) * 1000000u) / baseline_rate;
        uint64_t delta = baseline.count ? elapsed - baseline.duration_us : 0;
        drms_baseline_feed(&baseline, ohms, delta);
        baseline_previous_seq = frame.sequence;
      }
    }
    consumed_raw += 1;
    int valid = drms_decode_frame(frame.bytes, &latest);
    (void)valid;
    if (latest.flags & DRMS_SAMPLE_CRC_ERROR)
      ++crc_bad;
    if (latest.flags & DRMS_SAMPLE_ADC_FAULT)
      ++adc_faults;
    if (latest.flags & (DRMS_SAMPLE_CRC_ERROR | DRMS_SAMPLE_FORMAT_ERROR))
      ++consecutive_bad;
    else
      consecutive_bad = 0;
    if (cal_active && protocol_cal_active &&
        (!valid || !drms_excitation_ok(&latest) || latest.flags ||
         (protocol_cal_have_previous && frame.sequence != protocol_cal_previous + 1u)))
    {
      protocol_cal_result = DRMS_INCOMPLETE;
      cal_active = 0;
    }
    if (cal_active && protocol_cal_active)
    {
      protocol_cal_previous = frame.sequence;
      protocol_cal_have_previous = 1;
    }
    if (cal_active && drms_excitation_ok(&latest) &&
        !(latest.flags & (DRMS_SAMPLE_CRC_ERROR | DRMS_SAMPLE_FORMAT_ERROR)))
    {
      voltage_sum += latest.voltage;
      sense_sum += latest.sense;
      if (++cal_count == 4096)
      {
        double scale;
        cal_active = 0;
        if (drms_reference_scale(voltage_sum, sense_sum, requested_reference, &scale))
        {
          DRMS_Calibration *target = protocol_cal_active ? &protocol_cal_candidate : &calibration;
          target->scale = scale;
          target->reference_ohms = requested_reference;
          target->rate = drms_acq_rate;
          target->valid = 1;
          if (!protocol_cal_active)
          {
            drms_user_config_invalidate_baseline();
            cal_dirty = 1;
          }
          cal_result = 0;
        }
        else
        {
          cal_result = 4;
          if (protocol_cal_active) protocol_cal_result = DRMS_INCOMPLETE;
        }
        if (last_cmd == DRMS_CMD_CALIBRATE)
          cmd_result = cal_result;
      }
    }
  }
  if (session_active)
    drms_record_session_note_consumed(consumed_raw);
}

/* 停止采集并做完整收尾：撤销基线、中止记录会话、停采集、排空、停记录。
 *
 * 顺序是有讲究的：
 *   1. 先作废基线（它依赖连续的采集流，停了就没有意义）；
 *   2. 让记录会话进入取消态，避免它在收尾时还往记录环里塞数据；
 *   3. 停采集，再把残留帧排空——这样已采集到的数据不会白丢；
 *   4. 最后关记录文件。
 * r_valid 必须清 0，否则界面会拿着已经不更新的读数当当前值。 */
static void stop_acquisition(void)
{
  if (baseline_active)
  {
    baseline_active = 0;
    drms_acq_stop();
    uint32_t quiet = drms_acq_is_quiescent();
    (void)drms_control_complete(baseline_token, DRMS_CANCELLED,
        DRMS_RES_TF_ACCESS | DRMS_RES_FLASH_MAINTENANCE |
        (quiet ? DRMS_RES_ACQUISITION_CONFIG : 0));
  }
  drms_acq_stop();
  if (cal_active)
    cal_result = 4;
  cal_active = 0;
  session_cancel_local(DRMS_CANCELLED);
  drain_frames();
  drms_log_stop();
  r_valid = 0;
}

/* 按当前采样率配置监测管线。
 *
 * 两种来源：
 *   · 用户保存过监测配置 → 用它，但要检查 rate_hz 是否与当前采样率一致；
 *     不一致说明配置属于别的速率，基线必须作废（基线与采样率绑定）。
 *   · 没保存过 → 用一组保守默认值，只保证滤波与 stale 超时可用，不做判级。
 *
 * stale_timeout 取"128000 个采样周期"，即约 16 秒下限、更长速率下相应缩短，
 * 用来判断"当前读数是否已经不新鲜"。
 *
 * 注意：monitor_level_count 与对应的 level/id 数组在这里刷新，
 * 判级展示依赖它们，配置失败时会清 0（表示没有可用区间）。 */
static void configure_monitor(uint32_t rate)
{
  DRMS_MonitorConfig cfg;
  memset(&cfg, 0, sizeof(cfg));
  if (!drms_user_config_get_monitor(&cfg))
  {
    cfg.rate_hz = rate;
    cfg.stale_timeout_us = (128000000ULL + rate - 1U) / rate;
    if (cfg.stale_timeout_us < 10000U)
      cfg.stale_timeout_us = 10000U;
  }
  else if (cfg.rate_hz != rate)
  {
    /* 基线是属于"保存时那套采样配置"的。速率变了，基线就不再成立，
     * 必须显式作废，免得拿旧基准去判新条件下的数据。 */
    cfg.rate_hz = rate;
    cfg.baseline_valid = false;
    cfg.stale_timeout_us = (128000000ULL + rate - 1U) / rate;
    if (cfg.stale_timeout_us < 10000U)
      cfg.stale_timeout_us = 10000U;
  }
  monitor_level_count = 0;
  if (drms_monitor_configure(monitor, &cfg) == DRMS_OK)
  {
    monitor_level_count = cfg.interval_count;
    for (unsigned int i = 0; i < cfg.interval_count; ++i)
    {
      monitor_levels[i] = cfg.intervals[i].level;
      monitor_interval_ids[i] = cfg.intervals[i].id;
    }
  }
  monitor_config_version = drms_user_config_run_version();
}

/* 启动采集（内部实现，被 START/REF/MEASURE 与开机自动监测调用）。
 *
 * 返回给命令层的错误码：0 成功；3 状态不允许（正在记录或校准中、
 * 或采集资源被隔离）。
 *
 * 启动前会先尝试解除"停止中"状态——上一轮操作必须收尾干净，
 * 否则新采集会和残留清理撞车。 */
static uint32_t begin(uint32_t rate, uint32_t reference)
{
  if (drms_log_state || cal_active)
    return 3;
  DRMS_ControlSnapshot control;
  drms_control_get_snapshot(&control);
  if (control.quarantined_mask & DRMS_RES_ACQUISITION_CONFIG)
    return 3;
  if (control.stopping && drms_control_resume() != DRMS_OK)
    return 3; /* prior operations must finish cleanup before a restart */
  r_valid = 0;
  latest.flags = DRMS_SAMPLE_FORMAT_ERROR;
  crc_bad = adc_faults = consecutive_bad = 0;
  uint32_t ok = drms_acq_start(rate, reference) ? 0 : 2;
  if (!ok)
  {
    configure_monitor(rate);
    consumed_raw = 0; /* the acquisition ring starts a new ticket generation */
    nominal_anchor.acquisition_generation = drms_acq_generation();
    nominal_anchor.rate_hz = rate;
    nominal_anchor.sample_seq0 = drms_acq_sample_seq_next();
    nominal_anchor.mono_us0 = (uint64_t)HAL_GetTick() * 1000u;
  }
  return ok;
}

/* 基线建立的推进与收尾。
 *
 * 基线 R₀ 是判级的参考点，必须在"采集连续、无丢样、无换路"的前提下统计。
 * 因此任何一项异常都会让本次建立失败：
 *   · 采集停了、采样率变了、切到了参考支路；
 *   · 丢帧计数（overruns / queue_drops）比开始时增加了。
 * 超时也算失败，避免无限期挂着。
 *
 * 成功时才真正替换基线；失败一律保留原值——宁可让操作者重试，
 * 也不能用一个"看起来成立"的坏基线去判级。 */
static void baseline_service(uint32_t now)
{
  if (!baseline_active)
    return;
  if (!drms_acq_running || drms_acq_rate != baseline_rate || drms_acq_reference ||
      drms_acq_overruns != baseline_overruns || drms_acq_queue_drops != baseline_drops)
    baseline_failure = DRMS_INCOMPLETE;
  if ((uint32_t)(now - baseline_started) >= baseline_timeout_ms)
    baseline_failure = DRMS_TIMEOUT;
  double mean, deviation;
  int candidate = drms_baseline_candidate(&baseline, &mean, &deviation);
  if (baseline_failure == DRMS_OK && candidate != 1)
    return;
  DRMS_Result result = baseline_failure;
  uint32_t quiet_mask = DRMS_RES_ACQUISITION_CONFIG | DRMS_RES_TF_ACCESS |
                        DRMS_RES_FLASH_MAINTENANCE;
  baseline_active = 0;
  if (!drms_acq_running && !drms_acq_is_quiescent())
  {
    result = DRMS_QUARANTINED;
    quiet_mask &= ~DRMS_RES_ACQUISITION_CONFIG;
  }
  if (result == DRMS_OK)
  {
    drms_acq_stop();
    if (!drms_acq_is_quiescent())
    {
      result = DRMS_QUARANTINED;
      quiet_mask &= ~DRMS_RES_ACQUISITION_CONFIG;
    }
    else
    {
      result = drms_user_config_commit_baseline(mean, baseline_version, calibration.generation);
      publish_config_view();
      if (begin(baseline_rate, 0) != 0 && result == DRMS_OK)
        result = DRMS_IO_ERROR;
    }
  }
  (void)drms_control_complete(baseline_token, result, quiet_mask);
  cmd_result = result == DRMS_OK ? 0 : 1;
}

/* 参考校准（协议触发的 CALIBRATE）的推进与收尾。
 *
 * 校准采 4096 个连续有效样本算比例系数 k，所以前提与建基线类似：
 * 采集要在跑、必须在参考支路、采样率没变、丢样计数没增加。
 * 任一条件破坏即判失败，绝不把残缺数据当系数用。
 *
 * 成功后还要落盘（drms_calibration_save）。若"系数已写进去但恢复采集失败"，
 * 结果报 IO_ERROR 但新系数实际已生效——调用方应去查设备状态，
 * 不能假设 IO_ERROR 就一定意味着系数没变。 */
static void protocol_cal_service(uint32_t now)
{
  if (!protocol_cal_active) return;
  DRMS_ControlSnapshot control;
  drms_control_get_snapshot(&control);
  if (control.stopping || drms_shutdown_requested)
    protocol_cal_result = DRMS_CANCELLED;
  else if (!drms_acq_running || !drms_acq_reference || drms_acq_rate != protocol_cal_rate ||
           drms_acq_overruns != protocol_cal_overruns || drms_acq_queue_drops != protocol_cal_drops)
    protocol_cal_result = DRMS_INCOMPLETE;
  else if ((uint32_t)(now - cal_started) >= protocol_cal_timeout)
    protocol_cal_result = DRMS_TIMEOUT;
  if (cal_active && protocol_cal_result == DRMS_OK) return;
  cal_active = 0;
  drms_acq_stop();
  uint32_t quiet_mask = DRMS_RES_TF_ACCESS | DRMS_RES_FLASH_MAINTENANCE;
  if (!drms_acq_is_quiescent())
    protocol_cal_result = DRMS_QUARANTINED;
  else
  {
    quiet_mask |= DRMS_RES_ACQUISITION_CONFIG;
    if (protocol_cal_result == DRMS_OK)
    {
      if (!drms_calibration_save(&protocol_cal_candidate)) protocol_cal_result = DRMS_IO_ERROR;
      else
      {
        calibration = protocol_cal_candidate;
        cal_dirty = 0;
        drms_user_config_set_calibration_generation(calibration.generation);
        drms_user_config_invalidate_baseline();
        publish_config_view();
      }
    }
    if (!control.stopping && !drms_shutdown_requested && begin(protocol_cal_rate, 0) != 0)
    {
      protocol_cal_result = DRMS_IO_ERROR;
      if (!drms_acq_is_quiescent())
      {
        protocol_cal_result = DRMS_QUARANTINED;
        quiet_mask &= ~DRMS_RES_ACQUISITION_CONFIG;
      }
    }
  }
  cal_result = protocol_cal_result == DRMS_OK ? 0 : 4;
  protocol_cal_active = 0;
  (void)drms_control_complete(protocol_cal_token, protocol_cal_result, quiet_mask);
}

/* 执行一条已经排到队首的命令。
 *
 * 这里是所有业务动作的唯一落地点：ASCII 控制台、CDC v2、按键最终都汇到
 * commands 队列，由这个函数串行执行，所以状态机不需要为并发加锁。
 *
 * 每条命令执行完都会写 last_cmd / cmd_result，主机靠这两个字段判断
 * "命令受理了吗、结果是什么"。注意 cmd_result=100 表示"已受理、结果待定"，
 * 不是失败码。 */
static void execute(const DRMS_Command *command)
{
  last_cmd = command->id;
  cmd_result = 0;
  if (cal_active || baseline_active)
  {
    cmd_result = 3;
    return;
  }
  /* 命令分派的约定：
   *   cmd_result = 0     成功
   *   cmd_result = 1     状态不允许（例如记录中不允许换路）
   *   cmd_result = 100   已受理，最终结果待异步归结
   *   cmd_result = 2..7  具体失败原因（见协议文档）
   * 主机应当先看 cmd_result 再看别的字段，不要把 100 当成失败。 */
  switch (command->id)
  {
    /* 三条启动类命令共用 begin()，区别只在支路与速率：
     *   START [rate]  按指定或默认速率进样品模式
     *   REF           切到参考支路（校准用），速率沿用当前值
     *   MEASURE       切回样品支路，速率沿用当前值
     * 之所以用"当前速率"而不是默认值，是为了让 REF/MEASURE 不打断
     * 操作者正在用的采样率。 */
    case DRMS_CMD_START: cmd_result = begin(command->value, 0); break;
    case DRMS_CMD_REFERENCE: cmd_result = begin(drms_acq_rate ? drms_acq_rate : DRMS_APP_DEFAULT_RATE, 1); break;
    case DRMS_CMD_MEASURE: cmd_result = begin(drms_acq_rate ? drms_acq_rate : DRMS_APP_DEFAULT_RATE, 0); break;
    case DRMS_CMD_CALIBRATE:
      if (!drms_acq_running || !drms_acq_reference || drms_log_state)
        cmd_result = 1;
      else
      {
        requested_reference = command->value / 1000.;
        cal_count = 0;
        cal_result = cmd_result = 100;
        voltage_sum = sense_sum = 0;
        cal_started = HAL_GetTick();
        cal_active = 1;
      }
      break;
    /* 保存校准系数到 Flash。
     * 三个前置条件缺一不可：必须在停采状态、没有记录在写、且已经 calibrate 过。
     * 之所以要求停采，是因为写 Flash 会长时间占用总线，与采集抢带宽。 */
    case DRMS_CMD_SAVE:
      if (drms_acq_running || drms_log_state || !calibration.valid)
        cmd_result = 1;
      else if (!drms_calibration_save(&calibration))
        cmd_result = 6;
      else
      {
        cal_dirty = 0;
        drms_user_config_set_calibration_generation(calibration.generation);
      }
      break;
    /* 开始记录。这里走控制裁决而不是直接调用，因为它需要同时占用
     * 采集配置、记录会话和 TF 卡三种资源，必须先问"现在能用吗"。
     * 返回 100 表示已受理，最终结果（文件是否真的建起来）要等会话归结。 */
    case DRMS_CMD_RECORD:
    {
      DRMS_ControlRequest request = {
        .source = DRMS_SOURCE_CONSOLE, .session = 0,
        .request_id = HAL_GetTick(), .operation = DRMS_OP_RECORD};
      DRMS_Result result = drms_control_submit(&request);
      cmd_result = result == DRMS_ACCEPTED ? 100 : 1; /* 受理后经会话归结 */
      break;
    }
    case DRMS_CMD_END:
      if (session_active || session_armed)
      {
        if (session_armed)
          session_cancel_local(DRMS_CANCELLED);
        else
        {
          drms_record_session_request_stop();
          session_stopping = 1;
          session_duration_ms = 0;
        }
        cmd_result = 100;
      }
      else
        (void)drms_log_stop();
      break;
    /* 设置 RTC 的 UTC 时间。参数是 ISO-8601 字符串。
     * 时间只影响记录文件里写的时间戳，不参与任何测量计算，
     * 所以即使没设置也能正常测量——只是 rtc_valid 会是 0。 */
    case DRMS_CMD_TIME:
      cmd_result = drms_time_set(command->text) ? 0 : 7;
      drms_time_get(&clock_snapshot);
      break;
    default: cmd_result = 1; break;
  }
}

/* 应用层初始化：建命令队列、复位所有状态机、首次发布配置视图。
 *
 * 必须在调度器启动前、且其他模块的 init 之后调用（它依赖采集、记录、
 * 存储、控制几个子系统已经就绪）。 */
void drms_application_init(void)
{
  memset(&published_record, 0, sizeof(published_record));
  memset(&published_file, 0, sizeof(published_file));
  memset(&published_file_list, 0, sizeof(published_file_list));
  file_active = file_opened = file_close_pending = file_listing = 0;
  file_revoked_session = 0;
  memset(record_history, 0, sizeof(record_history));
  record_history_next = record_history_count = 0;
  drms_config_snapshot_init();
  config_view_current = 0;
  memset(&published_status, 0, sizeof(published_status));
  _Static_assert(sizeof(DRMS_Command) % sizeof(ULONG) == 0, "Queue word alignment");
  ready = tx_queue_create(&commands, "instrument commands", sizeof(DRMS_Command) / sizeof(ULONG),
                          command_memory, sizeof(command_memory)) == TX_SUCCESS;
  drms_calibration_load(&calibration);
  latest.flags = DRMS_SAMPLE_FORMAT_ERROR;
  uint32_t button_now = HAL_GetTick();
  drms_button_init(&measurement_button, button_now,
                   HAL_GPIO_ReadPin(MEAS_BTN_GPIO_Port, MEAS_BTN_Pin) == GPIO_PIN_RESET);
  drms_button_init(&power_button, button_now,
                   HAL_GPIO_ReadPin(PWR_BTN_GPIO_Port, PWR_BTN_Pin) == GPIO_PIN_RESET);
  last_aux = HAL_GetTick() - 1000U;
  drms_power_init();
  /* T5：用户配置/R0 恢复 + 校准代次注入 */
  drms_user_config_init();
  drms_user_config_set_calibration_generation(calibration.generation);
  drms_user_config_load();
  drms_monitor_init(monitor);
  DRMS_MonitorConfig saved;
  if (drms_user_config_get_monitor(&saved))
  {
    boot_rate = saved.rate_hz;
    config_state = 1;
  }
  else
  {
    boot_rate = DRMS_APP_DEFAULT_RATE;
    config_state = (drms_user_config_persisted_version() ||
                    drms_user_config_unsupported_schema()) ? 2U : 0U;
  }
  configure_monitor(boot_rate);
  drms_monitor_tick(monitor, drms_acq_now_us(), &published_monitor);
  /* T1：控制裁决接管业务请求投递 */
  drms_record_session_init();
  drms_control_init(app_dispatch);
  msc_active = msc_reported = msc_release_active = 0;
  baseline_active = 0;
  protocol_cal_active = 0;
  session_end_active = 0;
  priority_stop_active = 0;
  /* T7：开机自动监测（显式记录仍需请求）；失败保持可调度与诊断 */
  if (!drms_acq_running)
    (void)begin(boot_rate, 0);
  publish_config_view();
}

/* 应用主循环，由主线程反复调用。每轮做四件事：
 *
 *   1. 电源与按键扫描：把按键事件翻译成请求（短按测量键=记录叠加在监测之上，
 *      长按=建立基线 R₀，短按电源键=安全停采）。
 *   2. 处理优先级最高的事件：安全停止与关机请求先于一切普通命令。
 *   3. 按序执行命令队列里的命令，并把每条的受理与结果写进 last_cmd/cmd_result。
 *   4. 推进各个周期性子服务：排空采集帧、记录会话、基线、校准、MSC 与文件服务。
 *
 * 这个函数不能阻塞——它是主线程唯一的推进点，一旦卡住，采集环会溢出、
 * 记录会断流。任何需要等待的操作都必须异步化（交给 FileX 线程或分轮次完成）。 */
void drms_application_poll(void)
{
  drms_power_poll();
  uint32_t now = HAL_GetTick();
  DRMS_ButtonEvent power_event = drms_button_step(&power_button, now,
      HAL_GPIO_ReadPin(PWR_BTN_GPIO_Port, PWR_BTN_Pin) == GPIO_PIN_RESET);
  DRMS_ButtonEvent measurement_event = drms_button_step(&measurement_button, now,
      HAL_GPIO_ReadPin(MEAS_BTN_GPIO_Port, MEAS_BTN_Pin) == GPIO_PIN_RESET);
  if (power_event != DRMS_BUTTON_NONE)
  {
    if (power_event == DRMS_BUTTON_SHORT)
      __atomic_store_n(&stop_requested, 1U, __ATOMIC_RELEASE);
  }
  else if (!drms_shutdown_requested && measurement_event == DRMS_BUTTON_LONG)
  {
    DRMS_ControlRequest request = {
      .source = DRMS_SOURCE_BUTTON, .operation = DRMS_OP_BASELINE_R0};
    cmd_result = drms_control_submit(&request) == DRMS_ACCEPTED ? 100 : 1;
    last_cmd = DRMS_OP_BASELINE_R0;
  }
  else if (!drms_shutdown_requested && measurement_event == DRMS_BUTTON_SHORT)
  {
    if (session_active || session_armed)
    {
      if (session_armed)
        session_cancel_local(DRMS_CANCELLED);
      else
      {
        drms_record_session_request_stop();
        session_stopping = 1;
        session_duration_ms = 0;
      }
      last_cmd = DRMS_CMD_END;
    }
    else if (drms_acq_running && !drms_acq_reference)
    {
      DRMS_ControlRequest request = {
        .source = DRMS_SOURCE_BUTTON, .operation = DRMS_OP_RECORD};
      cmd_result = drms_control_submit(&request) == DRMS_ACCEPTED ? 100 : 1;
      last_cmd = DRMS_CMD_RECORD;
    }
    else
    {
      last_cmd = DRMS_CMD_START;
      cmd_result = begin(boot_rate, 0);
    }
  }
  /* 安全停止优先于一切普通命令。
   *
   * 它走独立通道（drms_control_safe_stop_take）而不是命令队列，
   * 就是为了能插队：主机可能刚发了一串请求，其中某条卡住了，
   * 此时停止必须立刻生效，不能排在它们后面等。
   *
   * 记录下"停止时是否正在记录"，决定了收尾时要不要等文件关闭。 */
  uint32_t priority_stop = drms_control_safe_stop_take();
  uint32_t local_stop = __atomic_exchange_n(&stop_requested, 0U, __ATOMIC_ACQ_REL);
  if (priority_stop || local_stop)
  {
    if (priority_stop)
    {
      priority_stop_active = 1;
      priority_stop_started = now;
      priority_stop_had_record = session_active || session_armed || drms_log_state;
    }
    /* STOP 是取消屏障：旧排队 START 不得重新使能 */
    if (ready)
      (void)tx_queue_flush(&commands);
    stop_acquisition();
    drms_msc_cancel();
    drms_file_service_cancel_all();
    drms_control_stop(); /* cancel admitted-but-not-yet-dispatched operations */
    last_cmd = DRMS_CMD_STOP;
    cmd_result = 0;
  }
  else if (ready)
  {
    DRMS_Command command;
    while (tx_queue_receive(&commands, &command, TX_NO_WAIT) == TX_SUCCESS)
      execute(&command);
    /* 控制裁决：队列请求 → reserve → dispatch；完成槽由本上下文消费 */
    drms_control_poll(4);
    msc_service_control();
    DRMS_ControlCompletion completions[4];
    uint32_t n = drms_control_collect(completions, 4);
    for (uint32_t i = 0; i < n; ++i)
    {
      if (completions[i].result != DRMS_OK && completions[i].result != DRMS_ACCEPTED)
        cmd_result = 1;
    }
  }
  drms_record_session_poll(now, drms_acq_queue_used(), 4096);
  file_service_control();
  if (session_armed || session_active)
  {
    DRMS_End pending;
    if (drms_record_end_get(&pending) == DRMS_OK &&
        (pending.reason == DRMS_TIMEOUT ||
         (pending.reason == DRMS_INCOMPLETE && (session_armed || session_stopping))))
      session_cancel_local(pending.reason);
  }
  session_service(now);
  if (session_active && !session_cancelled && !session_stopping && session_duration_ms &&
      drms_acq_now_us() - session_started_us >= (uint64_t)session_duration_ms * 1000u)
  {
    drms_record_session_request_stop();
    session_stopping = 1;
    session_duration_ms = 0; /* Issue a single stop request. */
  }
  /* 屏障期内不要排空采集环——会话正在等一个一致边界，
   * 此时把帧取走会让边界的样本序号与实际处理的帧对不上。
   * 等边界定下来（barrier 变 0）再继续消费。 */
  /* File creation precedes the BEGIN boundary request. These samples are
   * monitoring-only and may be consumed; waiting for SD must not fill raw RAM.
   * Once the file is ready, retain the actual boundary barrier unchanged. */
  if (!drms_record_session_barrier() || (session_armed && !drms_log_running))
    drain_frames();
  /* 基线与校准都是长流程（数秒到几十秒），每轮推进一点点，
   * 绝不在一次调用里等它们完成——否则整机的响应会卡住。 */
  baseline_service(now);
  protocol_cal_service(HAL_GetTick());
  if (session_active)
  {
    /* END 已发布（会话收尾）：等存储把记录环排空并关闭文件后 ack，
     * 会话回到 IDLE；ET 后帧只监测（classify 返回 MONITOR） */
    DRMS_End end;
    if (drms_record_end_get(&end) == DRMS_OK)
    {
      session_end = end;
      /* END 已发布：请求存储停止追加并排空到 ring_end 后关文件（C1） */
      if (drms_log_running)
      {
        if (session_cancelled || !drms_log_finish_v2(&end))
          drms_log_stop_incomplete();
        else
          session_footer_requested = 1;
      }
      if (!drms_log_running && drms_log_state == 0)
      {
        DRMS_Result storage_result = drms_log_status ? DRMS_IO_ERROR : DRMS_OK;
        DRMS_ApplicationRecord view = {
          .record = end.record_id, .phase = 2,
          .result = storage_result != DRMS_OK ? storage_result : session_cancelled ? session_cancel_reason :
                    (!session_footer_requested && (end.reason == DRMS_OK || end.reason == DRMS_EMPTY) ? DRMS_INCOMPLETE : end.reason),
          .clean_end = session_footer_requested && storage_result == DRMS_OK,
          .capture_lost = end.capture_lost, .log_dropped = end.log_dropped,
          .unknown_loss = end.unknown_loss || !session_footer_requested};
        record_publish(&view);
        (void)drms_record_end_ack(end.token, storage_result);
        if (session_end_active)
        {
          (void)drms_control_complete(session_end_token, (DRMS_Result)view.result, 0);
          session_end_active = 0;
        }
        if (storage_result != DRMS_OK)
          cmd_result = 5;
        (void)drms_control_release(end.token,
                                   DRMS_RES_ACQUISITION_CONFIG |
                                   DRMS_RES_RECORD_SESSION | DRMS_RES_TF_ACCESS);
        session_active = 0;
        session_stopping = 0;
        session_cancelled = 0;
        have_begin = 0;
      }
    }
  }
  if (priority_stop_active)
  {
    if (drms_acq_is_quiescent() && !session_active && !session_armed &&
        !drms_log_state && !msc_active && !msc_release_active && !file_active && !protocol_cal_active &&
        drms_msc_owner() == DRMS_OWNER_LOCAL)
    {
      DRMS_Result result = priority_stop_had_record && drms_log_status ? DRMS_IO_ERROR : DRMS_OK;
      (void)drms_control_safe_stop_finish(result);
      priority_stop_active = 0;
    }
    else if ((uint32_t)(now - priority_stop_started) >= 5000u)
    {
      /* 超时仍未静止：停止态继续保持，已占用的资源租约**不释放**。
       * 这与"能证明传输停下来才复用"的原则一致——隔离优先于勉强继续。 */
      (void)drms_control_safe_stop_finish(DRMS_TIMEOUT);
      priority_stop_active = 0;
    }
  }
  if (consecutive_bad >= 32)
    drms_acq_error = 5;
  drms_acq_poll();
  if (!drms_acq_running)
  {
    r_valid = 0;
    session_cancel_local(DRMS_IO_ERROR);
  }
  if (cal_active && !protocol_cal_active && (uint32_t)(now - cal_started) > 10000U)
  {
    stop_acquisition();
    cmd_result = 4;
  }
  else if (!drms_acq_running && (drms_log_running || cal_active))
  {
    stop_acquisition();
    cmd_result = 2;
  }
  if ((uint32_t)(now - last_aux) >= 1000U)
  {
    drms_aux_poll();
    drms_time_get(&clock_snapshot);
    last_aux = now;
  }
  /* 监测新鲜度：每 10ms tick（C3：无独立 DRDY 也必须过期失效） */
  {
    DRMS_MonitorOutput fresh;
    drms_monitor_tick(monitor, drms_acq_now_us(), &fresh);
    if (!drms_acq_running)
    {
      fresh.fresh = false;
      fresh.freshness_reason |= DRMS_FRESH_NO_SAMPLE;
    }
    uint32_t valid = 0;
    int32_t resistance = r_milliohms;
    if (drms_acq_running && fresh.fresh && drms_excitation_ok(&latest))
    {
      double ohms;
      valid = drms_resistance(&latest, calibration.scale, &ohms) &&
              ohms > -2147483. && ohms < 2147483.;
      if (valid)
        resistance = (int32_t)(ohms * 1000.);
    }
    uint32_t mask = __get_PRIMASK();
    __disable_irq();
    published_monitor = fresh;
    r_valid = valid;
    r_milliohms = resistance;
    __set_PRIMASK(mask);
  }
  if ((uint32_t)(now - last_display) >= 10U)
  {
    uint32_t lights = 0;
    uint32_t phase = now % 2000U;
    if (drms_acq_error || (drms_log_status && drms_log_records))
      lights = (now / 250U) % 2U ? 0x0fU : 0U;
    else if (drms_acq_running && !drms_acq_reference && published_monitor.fresh &&
             published_monitor.state == DRMS_MONITOR_CONFIRMED &&
             published_monitor.confirmed >= 0 &&
             (uint16_t)published_monitor.confirmed < monitor_level_count &&
             monitor_levels[published_monitor.confirmed] < 4U)
      lights = 1U << monitor_levels[published_monitor.confirmed];
    else if (published_monitor.fresh && published_monitor.state == DRMS_MONITOR_PENDING)
      lights = now % 1000U < 100U ? 0x0fU : 0U;
    else if (phase < 100U || (phase >= 200U && phase < 300U))
      lights = 0x0fU;
    HAL_GPIO_WritePin(LED_GREEN_GPIO_Port, LED_GREEN_Pin,
                      (lights & 1U) ? GPIO_PIN_RESET : GPIO_PIN_SET);
    HAL_GPIO_WritePin(LED_YELLOW_GPIO_Port, LED_YELLOW_Pin,
                      (lights & 2U) ? GPIO_PIN_RESET : GPIO_PIN_SET);
    HAL_GPIO_WritePin(LED_ORANGE_GPIO_Port, LED_ORANGE_Pin,
                      (lights & 4U) ? GPIO_PIN_RESET : GPIO_PIN_SET);
    HAL_GPIO_WritePin(LED_RED_GPIO_Port, LED_RED_Pin,
                      (lights & 8U) ? GPIO_PIN_RESET : GPIO_PIN_SET);
    last_display = now;
  }
  {
    DRMS_ApplicationSnapshot next;
    memset(&next, 0, sizeof(next));
    uint32_t mask = __get_PRIMASK();
    __disable_irq();
    DRMS_Owner owner;
    DRMS_Health health;
    drms_storage_snapshot(&owner, &health);
    next.revision = published_status.revision + 1u;
    next.mono_us = drms_acq_now_us();
    next.running_version = monitor_config_version;
    next.saved_version = drms_user_config_persisted_version();
    next.baseline_version = drms_user_config_r0_valid() ? monitor_config_version : 0;
    next.calibration_version = calibration.valid ? calibration.generation : 0;
    next.sample_index = published_monitor.sample_seq;
    int32_t measured_milliohms = r_milliohms;
    next.ratio = published_monitor.ratio;
    next.rate = drms_acq_rate;
    next.generation = drms_acq_generation();
    next.media_generation = drms_storage_media_generation();
    next.acquisition = drms_acq_error ? 5u : !drms_acq_running ? 0u :
                       drms_acq_reference ? 4u : 3u;
    next.recording = session_armed ? 1u : session_stopping ? 3u : session_active ? 2u : 0u;
    next.record_id = published_record.record;
    next.record_phase = published_record.phase;
    next.record_result = published_record.result;
    next.medium = (uint8_t)health;
    next.owner = (uint8_t)owner;
    next.maintenance = baseline_active ? 1u : cal_active ? 2u : 0u;
    next.fresh = published_monitor.fresh ? 1u : 0u;
    next.classification = (uint8_t)published_monitor.state;
    next.rtc_valid = clock_snapshot.valid ? 1u : 0u;
    next.ohms_valid = r_valid ? 1u : 0u;
    next.ratio_valid = next.fresh && published_monitor.state >= DRMS_MONITOR_UNMAPPED;
    if (next.fresh && published_monitor.state == DRMS_MONITOR_CONFIRMED &&
        published_monitor.confirmed >= 0 && (uint16_t)published_monitor.confirmed < monitor_level_count)
    {
      next.level_valid = 1;
      next.level = monitor_levels[published_monitor.confirmed];
      next.interval = monitor_interval_ids[published_monitor.confirmed];
    }
    if (!next.fresh) next.quality |= 1u << 0;
    if (published_monitor.reason & DRMS_REASON_QUALITY_BAD) next.quality |= 1u << 1;
    if (!drms_excitation_ok(&latest)) next.quality |= 1u << 2;
    if (published_monitor.reason & DRMS_REASON_SAMPLE_GAP) next.quality |= 1u << 3;
    if (published_monitor.reason & DRMS_REASON_NO_BASELINE) next.quality |= 1u << 4;
    if (published_monitor.reason & DRMS_REASON_UNCONFIGURED) next.quality |= 1u << 5;
    if (drms_acq_error) next.fault |= 1u << 0;
    if (health == DRMS_HEALTH_FAULT) next.fault |= 1u << 1;
    if (published_monitor.freshness_reason & DRMS_FRESH_TIMEBASE_FAULT) next.fault |= 1u << 3;
    if (drms_usb_status) next.fault |= 1u << 4;
    if (owner == DRMS_OWNER_QUARANTINED) next.fault |= 1u << 5;
    __set_PRIMASK(mask);
    next.ohms = (double)measured_milliohms / 1000.0;
    mask = __get_PRIMASK();
    __disable_irq();
    published_status = next;
    __set_PRIMASK(mask);
  }
  publish_config_view();
}

/* 取一份自洽的整机快照，供 CDC v2 的 GET_STATUS 使用。
 *
 * 所有字段在同一把临界区里取出，保证主机看到的是同一时刻的状态，
 * 而不是"电阻是新的、记录状态是旧的"这种拼接结果。
 * 返回非 0 表示快照有效。 */
uint32_t drms_application_snapshot(DRMS_ApplicationSnapshot *out)
{
  if (!out) return 0;
  uint32_t mask = __get_PRIMASK();
  __disable_irq();
  *out = published_status;
  __set_PRIMASK(mask);
  return out->revision != 0;
}

/* 外部中断的下降沿回调。
 *
 * 目前只有 DRDY 走这里——它是采集的节拍源，回调里只做最轻的启动动作，
 * 解码与判级都留给线程。按键用的是轮询而非中断，所以不在这里处理。 */
void HAL_GPIO_EXTI_Falling_Callback(uint16_t pin)
{
  if (pin == ADS_DRDY_Pin)
    drms_acq_drdy();
}

/* 生成 ASCII v1 的 STATUS 回复文本。
 *
 * 这是人读与调试用的输出，字段名一旦发布就不能随意改名——上位机和脚本
 * 都按这些键名解析。新增字段只能追加在后面。
 *
 * 返回：写入的字节数；容量不足时返回 0，调用方应给足缓冲。 */
size_t drms_application_status(char *out, size_t capacity)
{
  if (!capacity)
    return 0;
  uint32_t mask = __get_PRIMASK();
  __disable_irq();
  DRMS_MonitorOutput snapshot = published_monitor;
  uint32_t monitor_state = snapshot.state, monitor_fresh = snapshot.fresh;
  uint32_t values[] = {ready, drms_acq_running, drms_acq_reference, drms_acq_rate, r_valid,
    calibration.valid, cal_dirty, cal_active, cal_count, cal_result, drms_acq_error,
    drms_acq_edges, drms_acq_overruns, drms_acq_queue_drops, crc_bad, adc_faults,
    drms_storage_mounted, drms_storage_status, drms_log_running, drms_log_state,
    drms_log_status, drms_log_records, drms_log_dropped, drms_battery_mv, drms_battery_valid,
    last_cmd, cmd_result, drms_calibration_flash_status, drms_uart_rx_dropped, drms_uart_tx_dropped,
    drms_usb_status, calibration.generation, (uint32_t)drms_excitation_ok(&latest), clock_snapshot.valid,
    (uint32_t)clock_snapshot.year*10000U+(uint32_t)clock_snapshot.month*100U+clock_snapshot.day,
    (uint32_t)clock_snapshot.hour*10000U+(uint32_t)clock_snapshot.minute*100U+clock_snapshot.second,
    HAL_GPIO_ReadPin(USB_VBUS_N_GPIO_Port, USB_VBUS_N_Pin) == GPIO_PIN_RESET,
    HAL_GPIO_ReadPin(BQ_PG_GPIO_Port, BQ_PG_Pin) == GPIO_PIN_RESET,
    HAL_GPIO_ReadPin(BQ_CHG_GPIO_Port, BQ_CHG_Pin) == GPIO_PIN_RESET, drms_usb_can_io(),
    drms_shutdown_requested, drms_power_status, drms_power_low_battery,
    monitor_state, monitor_fresh, config_state, published_record.result,
    published_record.phase, published_record.clean_end, published_record.unknown_loss};
  int32_t resistance = r_milliohms;
  __set_PRIMASK(mask);
  int n = snprintf(out, capacity,
    "OK ready=%lu running=%lu mode=%lu rate=%lu r_valid=%lu r_mohm=%ld cal=%lu cal_dirty=%lu cal_active=%lu cal_count=%lu cal_result=%lu "
    "adc_error=%lu edges=%lu spi_overrun=%lu frame_drop=%lu crc_bad=%lu adc_fault=%lu sd=%lu sd_status=%lu "
    "log=%lu log_state=%lu log_status=%lu records=%lu log_drop=%lu bat_mv=%lu bat_valid=%lu last_cmd=%lu cmd_result=%lu "
    "flash_status=%lu uart_rx_drop=%lu uart_tx_drop=%lu usb_status=%lu cal_generation=%lu excitation_ok=%lu "
    "rtc_valid=%lu utc_date=%lu utc_time=%lu vbus=%lu bq_pg=%lu bq_chg=%lu usb_io=%lu "
    "shutdown=%lu power_status=%lu low_battery=%lu monitor=%lu fresh=%lu config_state=%lu "
    "record_result=%lu record_phase=%lu record_clean_end=%lu record_unknown_loss=%lu\r\n",
    (unsigned long)values[0],(unsigned long)values[1],(unsigned long)values[2],(unsigned long)values[3],
    (unsigned long)values[4],(long)resistance,(unsigned long)values[5],(unsigned long)values[6],
    (unsigned long)values[7],(unsigned long)values[8],(unsigned long)values[9],(unsigned long)values[10],
    (unsigned long)values[11],(unsigned long)values[12],(unsigned long)values[13],(unsigned long)values[14],
    (unsigned long)values[15],(unsigned long)values[16],(unsigned long)values[17],(unsigned long)values[18],
    (unsigned long)values[19],(unsigned long)values[20],(unsigned long)values[21],(unsigned long)values[22],
    (unsigned long)values[23],(unsigned long)values[24],(unsigned long)values[25],(unsigned long)values[26],
    (unsigned long)values[27],(unsigned long)values[28],(unsigned long)values[29],(unsigned long)values[30],
    (unsigned long)values[31],(unsigned long)values[32],(unsigned long)values[33],(unsigned long)values[34],
    (unsigned long)values[35],(unsigned long)values[36],(unsigned long)values[37],(unsigned long)values[38],
    (unsigned long)values[39],(unsigned long)values[40],(unsigned long)values[41],
    (unsigned long)values[42],(unsigned long)values[43],
    (unsigned long)values[44],(unsigned long)values[45],
    (unsigned long)values[46],(unsigned long)values[47],
    (unsigned long)values[48],(unsigned long)values[49]);
  return n < 0 ? 0 : ((size_t)n < capacity ? (size_t)n : capacity - 1);
}
