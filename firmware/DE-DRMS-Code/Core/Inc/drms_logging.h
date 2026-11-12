#ifndef DRMS_LOGGING_H
#define DRMS_LOGGING_H
#include "drms_acquisition.h"
#include <stdint.h>

typedef struct {
  uint32_t rate, calibrated, calibration_generation, start_ticks, serial;
  double scale, reference_ohms;
  uint16_t year;
  uint8_t month, day, hour, minute, second, time_valid;
} DRMS_LogMetadata;

/* Main thread submits start/stop and samples; FileX thread alone polls/removes. */
void drms_log_init(void);
int drms_log_start(const DRMS_LogMetadata *metadata);
void drms_log_stop(void);
/* Drain and close without a clean footer when record completeness is unknown. */
void drms_log_stop_incomplete(void);
/* 返回 1=已入环；0=未运行或记录环满（模块内计全局诊断 drms_log_dropped，
 * 处理端另按返回值计入本次会话 log_dropped 并触发 C1 停止追加规则）。 */
int drms_log_enqueue(const DRMS_RawFrame *frame);
void drms_log_poll(void);
/* FileX thread: a full streaming batch is queued (small tails need a deadline). */
uint32_t drms_log_batch_ready(void);
void drms_log_removed(void);
/* 记录环 64 位发布水位（log_ticket）：END.ring_end 与存储消费边界。 */
uint64_t drms_log_ticket_next(void);
extern volatile uint32_t drms_log_running, drms_log_state, drms_log_status;
extern volatile uint32_t drms_log_records, drms_log_dropped;
extern char drms_log_filename[16];
#endif
