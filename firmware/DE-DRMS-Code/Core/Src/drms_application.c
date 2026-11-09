#include "drms_application.h"
#include "drms_command.h"
#include "drms_architecture_contract.h"
#include "drms_control.h"
#include "drms_record_session.h"
#include "drms_acquisition.h"
#include "drms_measurement.h"
#include "drms_calibration.h"
#include "drms_user_config.h"
#include "drms_msc.h"
#include "drms_capture_time.h"
#include "drms_logging.h"
#include "drms_storage.h"
#include "drms_time.h"
#include "drms_usb.h"
#include "drms_runtime.h"
#include "drms_power.h"
#include "../../App/interfaces/local_ui/drms_button.h"
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
static int64_t voltage_sum, sense_sum;
static double requested_reference;
static uint32_t crc_bad, adc_faults, consecutive_bad;
static uint32_t r_valid, last_cmd, cmd_result, last_aux, last_display;
static int32_t r_milliohms;

/* 记录会话（T2a）与监测管线（T6） */
static _Alignas(8) uint8_t monitor_store[DRMS_APP_CONTEXT_BYTES];
static DRMS_MonitorContext *const monitor = (DRMS_MonitorContext *)monitor_store;
/* Written only by the measurement owner, copied under a short critical section. */
static DRMS_MonitorOutput published_monitor;
static uint8_t monitor_levels[DRMS_MONITOR_INTERVALS_MAX];
static uint8_t monitor_level_count;
static uint32_t boot_rate = DRMS_APP_DEFAULT_RATE;
/* 0 = no saved configuration, 1 = usable, 2 = saved configuration incompatible. */
static uint32_t config_state;
static uint64_t monitor_config_version;
static DRMS_Token session_token;
static uint64_t session_record_id;
static uint64_t next_record_id = 1;
static uint32_t session_armed;   /* prepare 已完成，等文件就绪+边界 B */
static uint32_t session_cancelled;
static uint32_t session_stopping;/* request_stop 已发，等 E */
static uint32_t session_active;  /* classify/记录窗口生效中 */
static uint64_t consumed_raw;    /* 消费端 raw_ticket 水位 */
static DRMS_CaptureBoundary begin_boundary;
static uint32_t have_begin;
static DRMS_TimeAnchor nominal_anchor;  /* T7 过渡：以 wall-clock 为锚（板测换 DRDY 实测，见 T8） */
static DRMS_End session_end;

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
    if (session_armed)
      (void)drms_control_report(session_token, reason);
    drms_acq_boundary_cancel(session_token);
    drms_record_session_cancel(session_token, reason);
    drms_log_stop_incomplete();
    session_armed = 0;
    session_active = 1; /* retain ownership until the storage close is confirmed */
    session_stopping = 0;
    session_cancelled = 1;
  }
}

static DRMS_Result app_dispatch(const DRMS_Token *token, const DRMS_ControlRequest *request)
{
  (void)token;
  last_cmd = (uint32_t)request->operation;
  switch (request->operation)
  {
    case DRMS_OP_RECORD:
    {
      if (!drms_acq_running || drms_acq_reference || cal_active)
        return DRMS_INVALID;
      if (drms_msc_blocks_recording())
        return DRMS_BUSY;
      DRMS_Time time;
      drms_time_get(&time);
      DRMS_LogMetadata metadata = {
        .rate = drms_acq_rate, .calibrated = calibration.valid,
        .calibration_generation = calibration.generation, .start_ticks = HAL_GetTick(),
        .serial = HAL_GetUIDw0() ^ HAL_GetUIDw1() ^ HAL_GetUIDw2(),
        .scale = calibration.scale, .reference_ohms = calibration.reference_ohms,
        .year = time.year, .month = time.month, .day = time.day, .hour = time.hour,
        .minute = time.minute, .second = time.second, .time_valid = time.valid};
      if (!next_record_id)
        return DRMS_INVALID;
      session_record_id = next_record_id++;
      session_token = *token;
      DRMS_Result rc = drms_record_prepare(*token, session_record_id);
      if (rc != DRMS_ACCEPTED)
        return rc;
      if (!drms_log_start(&metadata))
      {
        drms_record_session_cancel(*token, DRMS_IO_ERROR);
        (void)drms_record_end_ack(*token, DRMS_IO_ERROR);
        return DRMS_IO_ERROR;
      }
      session_armed = 1;
      session_cancelled = 0;
      return DRMS_ACCEPTED; /* 文件就绪+边界 B 在 poll 中归结 */
    }
    case DRMS_OP_CONFIG_APPLY:
    case DRMS_OP_BASELINE_R0:
    case DRMS_OP_CONFIG_SAVE:
    case DRMS_OP_MSC_EXPORT:
    case DRMS_OP_FILE_DOWNLOAD:
    case DRMS_OP_CALIBRATE:
    case DRMS_OP_UPDATE:
      return DRMS_UNSUPPORTED; /* 非本阶段交付操作：明确拒绝而非静默 */
    default:
      return DRMS_INVALID;
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
    /* Consume a completed E before issuing another request. A DMA callback
     * can publish E between polls while newer DRDY events continue arriving. */
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

static void pipeline_step_frame(const DRMS_RawFrame *frame, uint64_t ticket,
                                uint64_t capture_lower_us)
{
  DRMS_RecordVerdict verdict = session_active
                                   ? drms_record_session_classify(ticket)
                                   : DRMS_RECORD_MONITOR;
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

static void drain_frames(void)
{
  DRMS_RawFrame frame;
  unsigned int limit = 4096;
  uint64_t capture_lower_us;
  while (limit-- && drms_acq_pop_timed(&frame, &capture_lower_us))
  {
    pipeline_step_frame(&frame, consumed_raw, capture_lower_us);
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
          calibration.scale = scale;
          calibration.reference_ohms = requested_reference;
          calibration.rate = drms_acq_rate;
          calibration.valid = 1;
          cal_dirty = 1;
          cal_result = 0;
        }
        else
          cal_result = 4;
        if (last_cmd == DRMS_CMD_CALIBRATE)
          cmd_result = cal_result;
      }
    }
  }
  if (session_active)
    drms_record_session_note_consumed(consumed_raw);
}

static void stop_acquisition(void)
{
  drms_acq_stop();
  if (cal_active)
    cal_result = 4;
  cal_active = 0;
  session_cancel_local(DRMS_CANCELLED);
  drain_frames();
  drms_log_stop();
  r_valid = 0;
}

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
    /* The baseline belongs to the saved sampling configuration. */
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
      monitor_levels[i] = cfg.intervals[i].level;
  }
  monitor_config_version = drms_user_config_run_version();
}

static uint32_t begin(uint32_t rate, uint32_t reference)
{
  if (drms_log_state || cal_active)
    return 3;
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

static void execute(const DRMS_Command *command)
{
  last_cmd = command->id;
  cmd_result = 0;
  if (cal_active)
  {
    cmd_result = 3;
    return;
  }
  switch (command->id)
  {
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
    case DRMS_CMD_SAVE:
      if (drms_acq_running || drms_log_state || !calibration.valid)
        cmd_result = 1;
      else if (!drms_calibration_save(&calibration))
        cmd_result = 6;
      else
        cal_dirty = 0;
      break;
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
        }
        cmd_result = 100;
      }
      else
        (void)drms_log_stop();
      break;
    case DRMS_CMD_TIME:
      cmd_result = drms_time_set(command->text) ? 0 : 7;
      drms_time_get(&clock_snapshot);
      break;
    default: cmd_result = 1; break;
  }
}

void drms_application_init(void)
{
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
  /* T7：开机自动监测（显式记录仍需请求）；失败保持可调度与诊断 */
  if (!drms_acq_running)
    (void)begin(boot_rate, 0);
}

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
  if (__atomic_exchange_n(&stop_requested, 0U, __ATOMIC_ACQ_REL))
  {
    /* STOP 是取消屏障：旧排队 START 不得重新使能 */
    if (ready)
      (void)tx_queue_flush(&commands);
    stop_acquisition();
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
    DRMS_ControlCompletion completions[4];
    uint32_t n = drms_control_collect(completions, 4);
    for (uint32_t i = 0; i < n; ++i)
    {
      if (completions[i].result != DRMS_OK && completions[i].result != DRMS_ACCEPTED)
        cmd_result = 1;
    }
  }
  drms_record_session_poll(now, drms_acq_queue_used(), 4096);
  if (session_armed || session_active)
  {
    DRMS_End pending;
    if (drms_record_end_get(&pending) == DRMS_OK &&
        (pending.reason == DRMS_TIMEOUT ||
         (pending.reason == DRMS_INCOMPLETE && (session_armed || session_stopping))))
      session_cancel_local(pending.reason);
  }
  session_service(now);
  if (!drms_record_session_barrier())
    drain_frames();
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
        if (end.reason != DRMS_OK && end.reason != DRMS_EMPTY)
          drms_log_stop_incomplete();
        else
          drms_log_stop();
      }
      if (!drms_log_running && drms_log_state == 0)
      {
        DRMS_Result storage_result = drms_log_status ? DRMS_IO_ERROR : DRMS_OK;
        (void)drms_record_end_ack(end.token, storage_result);
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
  if (consecutive_bad >= 32)
    drms_acq_error = 5;
  drms_acq_poll();
  if (!drms_acq_running)
  {
    r_valid = 0;
    session_cancel_local(DRMS_IO_ERROR);
  }
  if (cal_active && (uint32_t)(now - cal_started) > 10000U)
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
}

void HAL_GPIO_EXTI_Falling_Callback(uint16_t pin)
{
  if (pin == ADS_DRDY_Pin)
    drms_acq_drdy();
}

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
    monitor_state, monitor_fresh, config_state};
  int32_t resistance = r_milliohms;
  __set_PRIMASK(mask);
  int n = snprintf(out, capacity,
    "OK ready=%lu running=%lu mode=%lu rate=%lu r_valid=%lu r_mohm=%ld cal=%lu cal_dirty=%lu cal_active=%lu cal_count=%lu cal_result=%lu "
    "adc_error=%lu edges=%lu spi_overrun=%lu frame_drop=%lu crc_bad=%lu adc_fault=%lu sd=%lu sd_status=%lu "
    "log=%lu log_state=%lu log_status=%lu records=%lu log_drop=%lu bat_mv=%lu bat_valid=%lu last_cmd=%lu cmd_result=%lu "
    "flash_status=%lu uart_rx_drop=%lu uart_tx_drop=%lu usb_status=%lu cal_generation=%lu excitation_ok=%lu "
    "rtc_valid=%lu utc_date=%lu utc_time=%lu vbus=%lu bq_pg=%lu bq_chg=%lu usb_io=%lu "
    "shutdown=%lu power_status=%lu low_battery=%lu monitor=%lu fresh=%lu config_state=%lu\r\n",
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
    (unsigned long)values[44],(unsigned long)values[45]);
  return n < 0 ? 0 : ((size_t)n < capacity ? (size_t)n : capacity - 1);
}
