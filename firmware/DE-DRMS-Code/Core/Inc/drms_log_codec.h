#ifndef DRMS_LOG_CODEC_H
#define DRMS_LOG_CODEC_H
#include "drms_logging.h"
#include "drms_architecture_contract.h"

/* v1（只读兼容） */
void drms_log_pack_header(uint8_t header[64], const DRMS_LogMetadata *metadata);
void drms_log_pack_record(uint8_t record[16], const DRMS_RawFrame *frame);
void drms_log_pack_footer(uint8_t footer[64], uint32_t records, uint32_t dropped,
                          uint32_t overruns, uint32_t queue_drops, uint32_t stopped);

/* ---- v2（docs/design/2026-11-06-record-v2-format.md，规格冻结） ---- */
/* 全部 pack 函数返回写入字节数；容量不足或参数非法返回 0。
 * 载荷布局为显式小端编码（无 struct 落盘）；每块载荷末 4B 为
 * CRC-32/ISO-HDLC（zlib 参数，见 drms_crc32），覆盖该块前导字节。 */
#define DRMS_LOG_V2_CHUNK_HEADER 1u
#define DRMS_LOG_V2_CHUNK_DATA 2u
#define DRMS_LOG_V2_CHUNK_END 3u

typedef struct {
  uint32_t flags;      /* bit0 = NOMINAL 时间质量 */
  uint32_t rate_hz;
  uint32_t uid_w0, uid_w1, uid_w2; /* 96-bit 出厂 UID */
  uint64_t record_id;
  DRMS_TimeAnchor anchor;
  const uint8_t *config; /* schema1 快照（drms_user_config），可为 NULL */
  uint16_t config_len;
} DRMS_LogV2Meta;

/* Internal v2 integration path. The logger copies metadata and config before
 * returning; only the FileX owner writes the resulting file. */
int drms_log_start_v2(const DRMS_LogV2Meta *metadata);
int drms_log_finish_v2(const DRMS_End *end);

uint32_t drms_log_v2_pack_header(uint8_t *out, uint32_t capacity, const DRMS_LogV2Meta *meta);
uint32_t drms_log_v2_pack_data(uint8_t *out, uint32_t capacity,
                               const DRMS_RawFrame *frames, uint32_t count);
uint32_t drms_log_v2_pack_end(uint8_t *out, uint32_t capacity, const DRMS_End *end);

#endif
