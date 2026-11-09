#include "drms_log_codec.h"
#include "drms_measurement.h"
#include <string.h>

static void put32(uint8_t *out, uint32_t value)
{
  for (unsigned int i = 0; i < 4; ++i)
    out[i] = (uint8_t)(value >> (i * 8));
}

static void put_double(uint8_t *out, double value)
{
  uint64_t bits;
  memcpy(&bits, &value, sizeof(bits));
  put32(out, (uint32_t)bits);
  put32(out + 4, (uint32_t)(bits >> 32));
}

void drms_log_pack_header(uint8_t header[64], const DRMS_LogMetadata *metadata)
{
  memset(header, 0, 64);
  memcpy(header, "DRMS", 4);
  header[4] = 1;
  header[6] = 64;
  header[8] = 16;
  header[10] = (uint8_t)((metadata->calibrated ? 1U : 0U) | (metadata->time_valid ? 2U : 0U));
  put32(header + 12, metadata->rate);
  put32(header + 16, metadata->start_ticks);
  put32(header + 20, metadata->calibration_generation);
  put_double(header + 24, metadata->scale);
  put_double(header + 32, metadata->reference_ohms);
  header[40] = (uint8_t)metadata->year;
  header[41] = (uint8_t)(metadata->year >> 8);
  header[42] = metadata->month;
  header[43] = metadata->day;
  header[44] = metadata->hour;
  header[45] = metadata->minute;
  header[46] = metadata->second;
  put32(header + 48, 150000U);
  put32(header + 52, metadata->serial);
  put32(header + 60, drms_crc32(header, 60));
}

void drms_log_pack_record(uint8_t record[16], const DRMS_RawFrame *frame)
{
  memcpy(record, frame->bytes, 12);
  put32(record + 12, frame->sequence);
}

void drms_log_pack_footer(uint8_t footer[64], uint32_t records, uint32_t dropped,
                           uint32_t overruns, uint32_t queue_drops, uint32_t stopped)
{
  memset(footer, 0, 64);
  memcpy(footer, "DEND", 4);
  footer[4] = 1;
  footer[6] = 64;
  put32(footer + 8, records);
  put32(footer + 12, dropped);
  put32(footer + 16, overruns);
  put32(footer + 20, queue_drops);
  put32(footer + 24, stopped);
  put32(footer + 60, drms_crc32(footer, 60));
}

/* ---------------- v2（规格：docs/design/2026-11-06-record-v2-format.md） ---------------- */

static void put16(uint8_t *out, uint16_t value)
{
  out[0] = (uint8_t)value;
  out[1] = (uint8_t)(value >> 8);
}

static void put64(uint8_t *out, uint64_t value)
{
  for (unsigned int i = 0; i < 8; ++i)
    out[i] = (uint8_t)(value >> (i * 8));
}

static uint32_t pack_chunk(uint8_t *out, uint32_t capacity, uint16_t type,
                           const uint8_t *payload, uint16_t payload_len)
{
  /* payload 已含末 4B CRC；pack_chunk 只补块头并核算容量。 */
  if (!out || !payload || payload_len < 4u || (uint32_t)payload_len + 4u > capacity)
    return 0;
  put16(out, type);
  put16(out + 2, payload_len);
  memcpy(out + 4, payload, payload_len);
  return 4u + payload_len;
}

static uint16_t v2_finish_payload(uint8_t *payload, uint16_t used)
{
  /* 载荷末 4B CRC；返回含 CRC 的载荷长度。 */
  put32(payload + used, drms_crc32(payload, used));
  return (uint16_t)(used + 4u);
}

uint32_t drms_log_v2_pack_header(uint8_t *out, uint32_t capacity, const DRMS_LogV2Meta *meta)
{
  if (!out || !meta || !meta->rate_hz || meta->config_len > 4096u ||
      (meta->config && !meta->config_len) || (!meta->config && meta->config_len))
    return 0;
  uint32_t total = 4u + 58u + meta->config_len + 4u;
  if (capacity < total)
    return 0;
  uint8_t *payload = out + 4;
  put16(out, DRMS_LOG_V2_CHUNK_HEADER);
  put16(out + 2, (uint16_t)(total - 4u));
  memset(payload, 0, 58u);
  put16(payload, 2);
  put16(payload + 2, 16);
  put32(payload + 4, meta->flags);
  put32(payload + 8, meta->rate_hz);
  put32(payload + 12, meta->uid_w0);
  put32(payload + 16, meta->uid_w1);
  put32(payload + 20, meta->uid_w2);
  put64(payload + 24, meta->record_id);
  put32(payload + 32, meta->anchor.acquisition_generation);
  put32(payload + 36, meta->anchor.rate_hz);
  put64(payload + 40, meta->anchor.sample_seq0);
  put64(payload + 48, meta->anchor.mono_us0);
  put16(payload + 56, meta->config_len);
  if (meta->config_len)
    memcpy(payload + 58, meta->config, meta->config_len);
  put32(payload + 58u + meta->config_len,
        drms_crc32(payload, 58u + meta->config_len));
  return total;
}

uint32_t drms_log_v2_pack_data(uint8_t *out, uint32_t capacity,
                               const DRMS_RawFrame *frames, uint32_t count)
{
  if (!out || !frames || !count || count > 256u)
    return 0;
  uint32_t payload_length = count * 16u;
  uint32_t total = 4u + payload_length + 4u;
  if (capacity < total)
    return 0;
  put16(out, DRMS_LOG_V2_CHUNK_DATA);
  put16(out + 2, (uint16_t)(payload_length + 4u));
  for (uint32_t i = 0; i < count; ++i)
  {
    memcpy(out + 4u + i * 16u, frames[i].bytes, 12);
    put32(out + 4u + i * 16u + 12u, frames[i].sequence);
  }
  put32(out + 4u + payload_length, drms_crc32(out + 4u, payload_length));
  return total;
}

uint32_t drms_log_v2_pack_end(uint8_t *out, uint32_t capacity, const DRMS_End *end)
{
  uint8_t payload[88];
  if (!out || !end)
    return 0;
  if (!end->end_known && end->end_exclusive.index != 0)
    return 0; /* 未知末边界不写伪精确值 */
  memset(payload, 0, sizeof(payload));
  put32(payload, end->end_known ? end->end_exclusive.generation : end->first.generation);
  put64(payload + 4, end->record_id);
  put64(payload + 12, end->ring_end);
  put64(payload + 20, end->lost_count);
  put64(payload + 28, end->first.index);
  put64(payload + 36, end->end_known ? end->end_exclusive.index : 0);
  put64(payload + 44, end->last_confirmed_position.index);
  payload[52] = end->end_known ? 1u : 0u;
  put64(payload + 53, end->capture_lost);
  put64(payload + 61, end->log_dropped);
  put64(payload + 69, end->quality_bad);
  payload[77] = end->unknown_loss ? 1u : 0u;
  payload[78] = end->storage_error ? 1u : 0u;
  put32(payload + 79, (uint32_t)end->reason);
  uint16_t used = v2_finish_payload(payload, 83);
  return pack_chunk(out, capacity, DRMS_LOG_V2_CHUNK_END, payload, used);
}
