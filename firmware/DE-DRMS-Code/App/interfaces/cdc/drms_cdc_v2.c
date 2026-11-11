#include "drms_cdc_v2.h"
#include "drms_measurement.h"
#include "drms_control.h"
#include "drms_application.h"
#include "drms_config_snapshot.h"
#include <string.h>

static uint16_t get16(const uint8_t *p) { return (uint16_t)(p[0] | ((uint16_t)p[1] << 8)); }
static uint32_t get32(const uint8_t *p) { return (uint32_t)get16(p) | ((uint32_t)get16(p + 2) << 16); }
static uint64_t get64(const uint8_t *p) { return (uint64_t)get32(p) | ((uint64_t)get32(p + 4) << 32); }
static void put16(uint8_t *p, uint16_t v) { p[0] = (uint8_t)v; p[1] = (uint8_t)(v >> 8); }
static void put32(uint8_t *p, uint32_t v) { put16(p, (uint16_t)v); put16(p + 2, (uint16_t)(v >> 16)); }
static void put64(uint8_t *p, uint64_t v) { put32(p, (uint32_t)v); put32(p + 4, (uint32_t)(v >> 32)); }

static void tlv(uint8_t *raw, size_t *pos, uint16_t tag, const uint8_t *data, uint16_t size)
{
  put16(raw + *pos, tag | 0x8000u); put16(raw + *pos + 2, size); *pos += 4;
  memcpy(raw + *pos, data, size); *pos += size;
}
static void optional_tlv(uint8_t *raw, size_t *pos, uint16_t tag, const uint8_t *data, uint16_t size)
{
  size_t start=*pos; tlv(raw,pos,tag,data,size); put16(raw+start,tag);
}

size_t drms_cdc_v2_encode_measurement(uint32_t session, uint64_t sequence, uint64_t lost,
    const DRMS_ApplicationSnapshot *snapshot, uint8_t *wire, size_t capacity)
{
  if (!session || !sequence || !snapshot || !wire) return 0;
  uint8_t raw[192] = {0}, value[8];
  raw[0] = 2; raw[1] = 3; put16(raw + 2, 130); put32(raw + 4, session);
  size_t pos = 20;
  put64(value, sequence); tlv(raw, &pos, 62, value, 8);
  put64(value, snapshot->mono_us); tlv(raw, &pos, 10, value, 8);
  value[0] = snapshot->fresh; tlv(raw, &pos, 25, value, 1);
  value[0] = snapshot->classification; tlv(raw, &pos, 26, value, 1);
  put32(value, snapshot->quality); tlv(raw, &pos, 29, value, 4);
  if (snapshot->ohms_valid)
  {
    uint64_t bits; memcpy(&bits, &snapshot->ohms, sizeof(bits));
    put64(value, bits); optional_tlv(raw, &pos, 23, value, 8);
  }
  if (snapshot->ratio_valid)
  {
    uint64_t bits; memcpy(&bits, &snapshot->ratio, sizeof(bits));
    put64(value, bits); optional_tlv(raw, &pos, 24, value, 8);
  }
  if (snapshot->level_valid)
  {
    value[0] = snapshot->level; optional_tlv(raw, &pos, 27, value, 1);
    put16(value, snapshot->interval); optional_tlv(raw, &pos, 28, value, 2);
  }
  put64(value, lost); tlv(raw, &pos, 63, value, 8);
  put16(raw + 16, (uint16_t)(pos - 20u));
  put32(raw + pos, drms_crc32(raw, pos)); pos += 4;
  return drms_cdc_frame_encode(raw, pos, wire, capacity);
}

static DRMS_CDCMutation *mutation_slot(DRMS_CDCV2 *ctx)
{
  DRMS_CDCMutation *oldest = NULL;
  for (unsigned i = 0; i < 4; ++i)
  {
    DRMS_CDCMutation *slot = &ctx->mutations[i];
    if (!slot->request_id)
      return slot;
    DRMS_ControlCompletion state;
    if (drms_control_get_operation(slot->operation_id, &state) == DRMS_OK && state.phase != 2u)
      continue; /* never evict an admitted operation that is still running */
    if (!oldest || slot->age < oldest->age)
      oldest = slot;
  }
  return oldest;
}

static void received(void *user, const uint8_t *request, size_t length)
{
  DRMS_CDCV2 *ctx = user;
  if (request[1] != 1u || !ctx->session.healthy)
    return;
  uint16_t opcode = get16(request + 2), payload_len = get16(request + 16);
  uint32_t priority = opcode == 18u;
  if (ctx->can_send && !ctx->can_send(ctx->send_context, priority))
    return; /* no reply capacity: do not admit or consume the request */
  uint32_t session = get32(request + 4);
  uint64_t id = get64(request + 8);
  uint16_t result = 0;
  DRMS_ControlCompletion operation;
  uint32_t have_operation = 0;
  DRMS_ApplicationSnapshot snapshot;
  uint32_t have_snapshot = 0;
  DRMS_ApplicationRecord record;
  uint32_t have_record = 0;
  uint32_t have_file_data = 0;
  DRMS_ApplicationFileList file_list;
  uint32_t have_file_list = 0;
  DRMS_ConfigView config_view;
  uint32_t have_config = 0;
  uint64_t accepted_operation = 0;
  uint64_t accepted_record = 0;
  if (opcode == 1u)
  {
    if (get16(request + 18) ||
        drms_cdc_fields_validate(request + 20, payload_len, NULL, 0, NULL) ||
        drms_cdc_session_hello(&ctx->session, session, id, &session))
      return;
    if (!ctx->last_request) ctx->last_request = 1;
  }
  else
  {
    if (!ctx->session.session || session != ctx->session.session || id < 2u)
      return;
    if (id <= ctx->last_request)
    {
      result = 4;
      if (ctx->stop_mutation.request_id == id)
      {
        if (ctx->stop_mutation.length == length && !memcmp(ctx->stop_mutation.bytes, request, length))
        {
          result = DRMS_ACCEPTED;
          accepted_operation = ctx->stop_mutation.operation_id;
        }
        else result = DRMS_INVALID;
      }
      for (unsigned i = 0; i < 4; ++i)
      {
        DRMS_CDCMutation *slot = &ctx->mutations[i];
        if (slot->request_id == id)
        {
          if (slot->length == length && !memcmp(slot->bytes, request, length))
          {
            result = DRMS_ACCEPTED;
            accepted_operation = slot->operation_id;
            accepted_record = slot->record_id;
          }
          else
            result = DRMS_INVALID;
          break;
        }
      }
    }
    else
    {
      ctx->last_request = id;
      if (get16(request + 18))
        result = 3u;
      else if (opcode == 2u)
      {
        if (drms_cdc_fields_validate(request + 20, payload_len, NULL, 0, NULL))
          result = 3u;
        else if (!drms_application_snapshot(&snapshot))
          result = 2u;
        else
          have_snapshot = 1;
      }
      else if (opcode == 3u)
      {
        static const DRMS_CDCFieldRule rules[] = {{11, 8, 8, 0, 1}};
        DRMS_CDCFieldView fields[1];
        if (drms_cdc_fields_validate(request + 20, payload_len, rules, 1, fields))
          result = 3u;
        else
        {
          DRMS_Result query = drms_control_get_operation(get64(fields[0].value), &operation);
          if (query != DRMS_OK)
            result = (uint16_t)query;
          else
          {
            result = (uint16_t)operation.result;
            have_operation = 1;
          }
        }
      }
      else if (opcode == 4u)
      {
        static const DRMS_CDCFieldRule rules[] = {{12, 8, 8, 0, 1}};
        DRMS_CDCFieldView fields[1];
        if (drms_cdc_fields_validate(request + 20, payload_len, rules, 1, fields) || !get64(fields[0].value))
          result = DRMS_INVALID;
        else
        {
          DRMS_Result query = drms_application_record_snapshot(get64(fields[0].value), &record);
          result = (uint16_t)query;
          if (query == DRMS_OK) { result = (uint16_t)record.result; have_record = 1; }
        }
      }
      else if (opcode == 53u)
      {
        static const DRMS_CDCFieldRule rules[]={{58,4,4,0,1}};
        DRMS_CDCFieldView fields[1];
        if (drms_cdc_fields_validate(request+20,payload_len,rules,1,fields)) result=DRMS_INVALID;
        else
        {
          uint32_t cursor=get32(fields[0].value);
          if (cursor>10000u) result=DRMS_INVALID;
          else if (ctx->file_list_operation && cursor!=ctx->file_list_cursor) result=DRMS_BUSY;
          else if (!ctx->file_list_operation)
          {
            DRMS_ApplicationSnapshot current;
            if (!drms_application_snapshot(&current)) result=DRMS_BUSY;
            else
            {
              DRMS_ControlRequest submission={.source=DRMS_SOURCE_CDC,.session=session,.request_id=id,
                .operation=DRMS_OP_FILE_LIST,.value=cursor,.expected_version=current.media_generation};
              uint64_t op=0;
              DRMS_Result status=drms_control_submit_identified(&submission,&op);
              if (status==DRMS_ACCEPTED)
              {
                ctx->file_list_operation=op; ctx->file_list_cursor=cursor;
                ctx->file_list_generation=current.media_generation; result=DRMS_BUSY;
              }
              else result=(uint16_t)status;
            }
          }
          else if (drms_application_file_list_snapshot(&file_list) &&
                   file_list.operation==ctx->file_list_operation && file_list.session==session)
          {
            if (file_list.phase!=2u) result=DRMS_BUSY;
            else
            {
              ctx->file_list_operation=0;
              if (file_list.generation!=ctx->file_list_generation || file_list.cursor!=cursor)
                result=DRMS_STALE;
              else if (file_list.result==DRMS_OK || file_list.result==DRMS_EMPTY)
                { result=DRMS_OK; have_file_list=1; }
              else result=(uint16_t)file_list.result;
            }
          }
          else
          {
            DRMS_ControlCompletion status;
            DRMS_Result query=drms_control_get_operation(ctx->file_list_operation,&status);
            if (query==DRMS_OK && status.phase!=2u) result=DRMS_BUSY;
            else { result=query==DRMS_OK ? (uint16_t)status.result : (uint16_t)query; ctx->file_list_operation=0; }
          }
        }
      }
      else if (opcode == 51u)
      {
        static const DRMS_CDCFieldRule rules[] = {{11,8,8,0,1},{52,8,8,0,1},{53,2,2,0,1}};
        DRMS_CDCFieldView fields[3];
        if (drms_cdc_fields_validate(request+20,payload_len,rules,3,fields)) result=DRMS_INVALID;
        else
        {
          uint64_t handle=get64(fields[0].value), offset=get64(fields[1].value);
          uint16_t count=get16(fields[2].value);
          DRMS_ApplicationFile view;
          if (!handle || !count || count>768u) result=DRMS_INVALID;
          else if (!drms_application_file_snapshot(&view) || view.phase!=1u ||
                   view.session!=session || view.operation!=handle) result=DRMS_STALE;
          else if (offset>view.size) result=DRMS_INVALID;
          else if (ctx->file_read_ticket && (ctx->file_read_operation!=handle ||
                   ctx->file_read_offset!=offset || ctx->file_read_count!=count)) result=DRMS_BUSY;
          else if (!ctx->file_read_ticket)
          {
            DRMS_FileRequest item={.kind=DRMS_FILE_READ,.session=session,.generation=view.generation,
                                   .offset=offset,.count=count};
            uint64_t ticket=0;
            DRMS_Result status=drms_file_service_submit(&item,&ticket);
            if (status==DRMS_ACCEPTED)
            {
              ctx->file_read_ticket=ticket; ctx->file_read_operation=handle;
              ctx->file_read_offset=offset; ctx->file_read_count=count; result=DRMS_BUSY;
            }
            else result=(uint16_t)status;
          }
          else
          {
            DRMS_Result status=drms_file_service_take(ctx->file_read_ticket,&ctx->file_read_reply);
            if (status==DRMS_ACCEPTED) result=DRMS_BUSY;
            else
            {
              ctx->file_read_ticket=0;
              result=status==DRMS_OK ? (uint16_t)ctx->file_read_reply.result : (uint16_t)status;
              if (result==DRMS_OK)
              {
                uint64_t remain = view.size - offset;
                uint16_t expected = remain < count ? (uint16_t)remain : count;
                if (ctx->file_read_reply.offset!=offset || ctx->file_read_reply.length!=expected ||
                    ctx->file_read_reply.eof!=(uint8_t)(offset+expected==view.size))
                  result=DRMS_IO_ERROR;
                else have_file_data=1;
              }
            }
          }
        }
      }
      else if (opcode == 52u)
      {
        static const DRMS_CDCFieldRule rules[] = {{11, 8, 8, 0, 1}};
        DRMS_CDCFieldView fields[1];
        if (drms_cdc_fields_validate(request + 20, payload_len, rules, 1, fields) || !get64(fields[0].value))
          result = DRMS_INVALID;
        else
        {
          DRMS_CDCMutation *slot = mutation_slot(ctx);
          if (!slot) result = DRMS_BUSY;
          else
          {
            uint64_t handle = get64(fields[0].value);
            if (ctx->file_read_ticket && ctx->file_read_operation != handle)
              result=DRMS_STALE;
            else if (ctx->file_read_ticket)
            {
              DRMS_Result pending=drms_file_service_take(ctx->file_read_ticket,&ctx->file_read_reply);
              if (pending==DRMS_ACCEPTED) result=DRMS_BUSY;
              else { ctx->file_read_ticket=0; result=pending==DRMS_OK ? (uint16_t)ctx->file_read_reply.result : (uint16_t)pending; }
            }
            if (result==DRMS_OK) result = (uint16_t)drms_application_file_close(session, handle);
            if (result == DRMS_ACCEPTED)
            {
              accepted_operation = handle;
              slot->request_id = id; slot->operation_id = handle;
              slot->age = ++ctx->mutation_age; slot->length = (uint16_t)length;
              memcpy(slot->bytes, request, length);
            }
          }
        }
      }
      else if (opcode == 32u)
      {
        if (drms_cdc_fields_validate(request + 20, payload_len, NULL, 0, NULL))
          result = DRMS_INVALID;
        else if (!drms_config_snapshot_acquire(&config_view))
          result = DRMS_UNSUPPORTED;
        else if (config_view.length > 990u)
        {
          drms_config_snapshot_release(&config_view);
          result = DRMS_UNSUPPORTED; /* complete response must fit one frame */
        }
        else
          have_config = 1;
      }
      else if (opcode == 16u || opcode == 17u || opcode == 18u || opcode == 19u || opcode == 33u || opcode == 34u || opcode == 35u || opcode == 36u || opcode == 37u || opcode == 48u || opcode == 49u || opcode == 50u)
      {
        static const DRMS_CDCFieldRule version_rule[] = {{48, 8, 8, 0, 1}};
        /* GET_CONFIG needs 34 payload bytes for result, TLV headers and versions. */
        static const DRMS_CDCFieldRule apply_rules[] = {{48, 8, 8, 0, 1}, {49, 1, 990, 0, 1}};
        static const DRMS_CDCFieldRule open_rules[] = {{56, 4, 4, 0, 1}, {85, 4, 4, 0, 1}};
        static const DRMS_CDCFieldRule utc_rules[] = {{51, 8, 8, 0, 1}};
        static const DRMS_CDCFieldRule record_rules[] = {{50, 4, 4, 0, 0}};
        static const DRMS_CDCFieldRule end_rules[] = {{12, 8, 8, 0, 1}};
        DRMS_CDCFieldView version_field[2];
        int invalid = opcode == 16u ? drms_cdc_fields_validate(request + 20, payload_len, record_rules, 1, version_field) :
            opcode == 17u ? drms_cdc_fields_validate(request + 20, payload_len, end_rules, 1, version_field) : opcode == 33u ?
            drms_cdc_fields_validate(request + 20, payload_len, apply_rules, 2, version_field) :
            opcode == 50u ? drms_cdc_fields_validate(request + 20, payload_len, open_rules, 2, version_field) :
            opcode == 37u ? drms_cdc_fields_validate(request + 20, payload_len, utc_rules, 1, version_field) :
            opcode == 34u ? drms_cdc_fields_validate(request + 20, payload_len, version_rule, 1, version_field) :
                           drms_cdc_fields_validate(request + 20, payload_len, NULL, 0, NULL);
        if (invalid || (opcode == 17u && !get64(version_field[0].value)))
          result = DRMS_INVALID;
        else
        {
          DRMS_CDCMutation *slot = opcode == 18u ? &ctx->stop_mutation : mutation_slot(ctx);
          if (!slot)
            result = DRMS_BUSY;
          else
          {
            DRMS_ControlRequest submission = {
              .source = DRMS_SOURCE_CDC, .session = session, .request_id = id,
              .operation = opcode == 16u ? DRMS_OP_RECORD :
                           opcode == 17u ? DRMS_OP_END_RECORD :
                           opcode == 18u ? DRMS_OP_NONE :
                           opcode == 19u ? DRMS_OP_RESUME_MONITOR :
                           opcode == 33u ? DRMS_OP_CONFIG_APPLY :
                           opcode == 34u ? DRMS_OP_CONFIG_SAVE :
                           opcode == 35u ? DRMS_OP_BASELINE_R0 :
                           opcode == 36u ? DRMS_OP_CALIBRATE :
                           opcode == 37u ? DRMS_OP_SET_UTC :
                           opcode == 50u ? DRMS_OP_FILE_DOWNLOAD :
                           opcode == 48u ? DRMS_OP_MSC_EXPORT : DRMS_OP_MSC_RELEASE};
            if (opcode == 16u && version_field[0].value)
            {
              submission.value = get32(version_field[0].value);
              submission.expected_version = 1;
            }
            if (opcode == 17u) submission.expected_version = get64(version_field[0].value);
            if (opcode == 33u || opcode == 34u || opcode == 37u)
              submission.expected_version = get64(version_field[0].value);
            if (opcode == 33u)
            {
              submission.payload = version_field[1].value;
              submission.payload_length = version_field[1].length;
            }
            if (opcode == 50u)
            {
              submission.value = get32(version_field[0].value);
              submission.expected_version = get32(version_field[1].value);
            }
            result = (uint16_t)(opcode == 16u ?
                drms_control_submit_record(&submission, &accepted_operation, &accepted_record) : opcode == 18u ?
                drms_control_safe_stop_submit(&submission, &accepted_operation) :
                drms_control_submit_identified(&submission, &accepted_operation));
            if (result == DRMS_ACCEPTED)
            {
              if (opcode == 17u) accepted_record = submission.expected_version;
              slot->request_id = id;
              slot->operation_id = accepted_operation;
              slot->record_id = accepted_record;
              slot->age = ++ctx->mutation_age;
              slot->length = (uint16_t)length;
              memcpy(slot->bytes, request, length);
            }
          }
        }
      }
      else result = 11u; /* UNSUPPORTED */
    }
  }
  uint8_t *out = ctx->raw;
  memset(out, 0, 20);
  out[0] = 2; out[1] = 2; put16(out + 2, opcode); put32(out + 4, session); put64(out + 8, id);
  size_t pos = 20;
  uint8_t temp[40];
  put16(temp, result); tlv(out, &pos, 1, temp, 2);
  if (opcode == 1u)
  {
    for (unsigned i = 0; i < 3; ++i) put32(temp + i * 4, ctx->uid[i]);
    tlv(out, &pos, 3, temp, 12);
    put64(temp, ctx->session.boot); tlv(out, &pos, 4, temp, 8);
    put16(temp, 1); put16(temp + 2, 2); put16(temp + 4, 3); put16(temp + 6, 4);
    put16(temp + 8, 16); put16(temp + 10, 17); put16(temp + 12, 18); put16(temp + 14, 19);
    put16(temp + 16, 32); put16(temp + 18, 33); put16(temp + 20, 34); put16(temp + 22, 35); put16(temp + 24, 36); put16(temp + 26, 37); put16(temp + 28, 48); put16(temp + 30, 49); put16(temp + 32, 50); put16(temp + 34, 51); put16(temp + 36, 52); put16(temp + 38, 53); tlv(out, &pos, 5, temp, 40);
    put16(temp, 1024); tlv(out, &pos, 6, temp, 2);
    put32(temp, 4000); tlv(out, &pos, 7, temp, 4);
    tlv(out, &pos, 8, temp, 4); /* conservative default; physical throughput still requires board tests */
  }
  else if (accepted_operation)
  {
    put64(temp, accepted_operation); tlv(out, &pos, 11, temp, 8);
    if (accepted_record) { put64(temp, accepted_record); tlv(out, &pos, 12, temp, 8); }
  }
  else if (have_config)
  {
    tlv(out, &pos, 49, config_view.data, (uint16_t)config_view.length);
    put64(temp, config_view.running); tlv(out, &pos, 31, temp, 8);
    put64(temp, config_view.saved); tlv(out, &pos, 32, temp, 8);
    drms_config_snapshot_release(&config_view);
  }
  else if (have_record)
  {
    put64(temp, record.record); tlv(out, &pos, 12, temp, 8);
    temp[0] = record.phase; tlv(out, &pos, 45, temp, 1);
    temp[0] = record.clean_end; tlv(out, &pos, 41, temp, 1);
    put64(temp, record.capture_lost); tlv(out, &pos, 38, temp, 8);
    put64(temp, record.log_dropped); tlv(out, &pos, 39, temp, 8);
    temp[0] = record.unknown_loss; tlv(out, &pos, 40, temp, 1);
  }
  else if (have_file_data)
  {
    put64(temp, ctx->file_read_operation); tlv(out, &pos, 11, temp, 8);
    put64(temp, ctx->file_read_offset); tlv(out, &pos, 52, temp, 8);
    tlv(out, &pos, 54, ctx->file_read_reply.data, ctx->file_read_reply.length);
    temp[0]=ctx->file_read_reply.eof; tlv(out, &pos, 55, temp, 1);
  }
  else if (have_file_list)
  {
    put32(temp,file_list.generation); tlv(out,&pos,85,temp,4);
    if (file_list.result==DRMS_OK)
    {
      put32(temp,file_list.file_id); optional_tlv(out,&pos,56,temp,4);
      put64(temp,file_list.size); optional_tlv(out,&pos,57,temp,8);
      if (file_list.next_cursor<10000u)
      { put32(temp,file_list.next_cursor); optional_tlv(out,&pos,59,temp,4); }
    }
  }
  else if (have_snapshot)
  {
#define T8(tag, value) do { temp[0] = (uint8_t)(value); tlv(out, &pos, tag, temp, 1); } while (0)
#define T32(tag, value) do { put32(temp, value); tlv(out, &pos, tag, temp, 4); } while (0)
#define T64(tag, value) do { put64(temp, value); tlv(out, &pos, tag, temp, 8); } while (0)
    T64(9, snapshot.revision); T64(10, snapshot.mono_us);
    T8(16, snapshot.acquisition); T8(17, snapshot.recording); T8(18, snapshot.medium);
    T8(19, snapshot.owner); T8(20, snapshot.maintenance); T32(21, snapshot.generation);
    T32(30, snapshot.rate); T8(25, snapshot.fresh); T8(26, snapshot.classification);
    T32(29, snapshot.quality); T64(31, snapshot.running_version); T64(32, snapshot.saved_version);
    T64(33, snapshot.baseline_version); T64(34, snapshot.calibration_version);
    T32(35, snapshot.fault); T8(42, snapshot.rtc_valid); T32(85, snapshot.media_generation);
    if (snapshot.record_id)
    {
      if (snapshot.record_phase != 2u) T64(12, snapshot.record_id);
      else { T64(36, snapshot.record_id); put16(temp, (uint16_t)snapshot.record_result); tlv(out, &pos, 37, temp, 2); }
    }
    if (snapshot.fresh) T64(22, snapshot.sample_index);
    if (snapshot.ohms_valid)
    {
      uint64_t bits; memcpy(&bits, &snapshot.ohms, sizeof(bits)); T64(23, bits);
    }
    if (snapshot.ratio_valid)
    {
      uint64_t bits; memcpy(&bits, &snapshot.ratio, sizeof(bits)); T64(24, bits);
    }
    if (snapshot.level_valid)
    {
      T8(27, snapshot.level);
      put16(temp, snapshot.interval); tlv(out, &pos, 28, temp, 2);
    }
#undef T8
#undef T32
#undef T64
  }
  else if (have_operation)
  {
    put64(temp, operation.operation_id); tlv(out, &pos, 11, temp, 8);
    temp[0] = (uint8_t)operation.phase;
    tlv(out, &pos, 45, temp, 1);
    temp[0] = operation.source == DRMS_SOURCE_BUTTON ? 1u :
              operation.source == DRMS_SOURCE_CDC ? 2u :
              operation.source == DRMS_SOURCE_CONSOLE ? 3u : 0u;
    tlv(out, &pos, 44, temp, 1);
    uint64_t related_record = drms_control_operation_record(operation.operation_id);
    if (related_record)
    {
      put64(temp, related_record); optional_tlv(out, &pos, 12, temp, 8);
    }
    DRMS_ApplicationFile file;
    if (operation.phase == 1u && drms_application_file_snapshot(&file) && file.phase == 1u &&
        file.session == session && file.operation == operation.operation_id)
    {
      size_t field_start = pos;
      put64(temp, file.size); tlv(out, &pos, 57, temp, 8);
      put16(out + field_start, 57); /* optional extension for older clients */
    }
  }
  put16(out + 16, (uint16_t)(pos - 20u));
  put32(out + pos, drms_crc32(out, pos)); pos += 4;
  size_t encoded = drms_cdc_frame_encode(out, pos, ctx->wire, sizeof(ctx->wire));
  if (encoded && ctx->send) ctx->send(ctx->send_context, ctx->wire, encoded, priority);
}

void drms_cdc_v2_init(DRMS_CDCV2 *ctx, DRMS_CDCEntropy entropy, void *entropy_context,
                      const uint32_t uid[3], DRMS_CDCV2Send send, DRMS_CDCV2CanSend can_send,
                      void *send_context)
{
  memset(ctx, 0, sizeof(*ctx));
  if (uid) memcpy(ctx->uid, uid, sizeof(ctx->uid));
  ctx->send = send; ctx->can_send = can_send; ctx->send_context = send_context;
  (void)drms_cdc_session_init(&ctx->session, entropy, entropy_context);
}

void drms_cdc_v2_disconnect(DRMS_CDCV2 *ctx)
{
  if (ctx->session.session) drms_application_file_disconnect(ctx->session.session);
  ctx->file_read_ticket=0;
  ctx->file_list_operation=0;
  drms_cdc_session_disconnect(&ctx->session);
  drms_cdc_frame_init(&ctx->frame);
  ctx->last_request = 0;
  memset(ctx->mutations, 0, sizeof(ctx->mutations));
  memset(&ctx->stop_mutation, 0, sizeof(ctx->stop_mutation));
  ctx->mutation_age = 0;
}

void drms_cdc_v2_feed(DRMS_CDCV2 *ctx, uint8_t byte, uint32_t now)
{
  drms_cdc_frame_feed(&ctx->frame, byte, now, received, ctx);
}
