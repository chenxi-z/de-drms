/*****************************************************************************
 * 文件：drms_cdc_v2.c
 * 职责：CDC v2 协议实现——帧解析、请求分派、回复编码、事件推送。
 *
 * 在整机中的位置：
 *   USB CDC 端点 → drms_cdc.c（字节流与收发线程）
 *                    ↓ 逐个字节喂进来
 *                  drms_cdc_frame.c（COBS 解帧 + CRC 校验）
 *                    ↓ 一帧完整的请求
 *                  本文件（解析 TLV、执行业务、组装回复）
 *                    ↓ 通过 send 回调
 *                  发送队列 → USB
 *
 * 一帧的构成：
 *   20 字节定长头（major/kind/opcode/session/request_id/payload_length/flags）
 *   + 若干 TLV 字段
 *   + 4 字节 CRC32
 *   整体先做 COBS 编码，再以 0x00 结束。
 *
 * TLV 的"必填"标记：
 *   tag 最高位（0x8000）表示"接收方必须理解这个字段"。发送方对必填字段置位。
 *   接收方遇到未知且置位的 tag 必须拒绝（返回 UNKNOWN_REQUIRED）；
 *   未知且未置位的按长度跳过。这是协议向前兼容的基础。
 *
 * 会话与幂等：
 *   HELLO 之后才有 session，同一次连接重复 HELLO 返回同一会话。
 *   request_id 在会话内严格递增。同一编号重发相同内容视为重试，直接回原结果；
 *   同编号不同内容则拒绝（REQUEST_ID_REUSED）——否则重试语义会被破坏。
 *
 * 异步操作的表达方式：
 *   很多操作（记录启停、校准、导出、文件下载）不可能在收到请求的瞬间完成。
 *   这里先回 ACCEPTED 并给出 operation 句柄，主机随后用 GET_OPERATION
 *   轮询最终结果。这个模式贯穿整个协议，看懂它才能理解为什么有些请求
 *   只返回一个操作号。
 *
 * 事件推送（SUBSCRIBE）：
 *   订阅是会话级的，断线即清除，重连必须重新订阅。
 *   目前只支持 CURVE（降速后的最新快照），RAW 明确拒绝而不是假装支持——
 *   让主机误以为在收原始流，比直接拒绝更糟。
 *****************************************************************************/

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

/* 编码一帧测量事件（MEAS_EVENT，opcode 130）。
 *
 * 这是 SUBSCRIBE 之后周期性发出去的东西，内容是一次"当前测量的快照"，
 * 而不是原始采样流——全速数据在记录文件里，这里只给实时观察用。
 *
 * 字段的取舍：
 *   必有：sequence（本流内从 1 递增）、mono_us（设备单调时间）、
 *         fresh（读数是否新鲜）、classification（等级）、quality（质量位）、
 *         lost（本次订阅累计漏发条数）
 *   可选：ohms（电阻）、ratio（R/R₀）、level+interval（命中的区间）
 * 可选字段的规则是"无效就整个省略，绝不用 0 顶替"——0 Ω 和"测不出来"
 * 是两件事，主机必须能区分。
 *
 * 细节：double 通过 memcpy 按位重解释成 64 位整数再写出，
 * 不走强制类型转换，避免违反严格别名规则。
 *
 * 返回：编码后的线上字节数；0 表示参数非法或容量不足。
 * 本函数无状态，可以在任意上下文调用。 */
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

/* 周期性推送 CURVE 事件。由 **CDC 发送线程** 每 10 ms 调用一次。
 *
 * 规则：
 *   · 每个订阅周期最多发一条，不到期直接返回，不做忙等；
 *   · 发送队列没空间时**丢弃并计数**，绝不阻塞——实时观察的价值在于"新"，
 *     积压的旧数据没有意义，宁可丢也不要让队列越积越多；
 *   · lost 累计的是"本该发但没发出去"的周期数，主机据此能区分
 *     "设备安静"和"链路卡住了"；
 *   · 编码失败时把 sequence 回退，保证序号连续——宁可重发也不要留缺口。
 *
 * 为什么在发送线程而不是接收线程：
 *   接收线程用 UX_WAIT_FOREVER 阻塞在 cdc_acm_read 上，只有主机发数据才返回。
 *   订阅成功后主机通常就安静了，接收线程于是长期停在 read 里，
 *   跟在它后面的 publish 一次都跑不到（实测 3 秒内所有计数器增量为 0）。
 *   发送线程本来就是 USB 的唯一写入方，且每 10 ms 必醒，放这里最稳。
 *
 * 跨线程安全：
 *   编码用独立的 curve_wire 缓冲，不碰 ctx->wire（那是接收线程回帧用的）。
 *   epoch 在编码前后比对：订阅若在编码期间被撤销/重建，这一帧直接作废，
 *   避免撤销后仍漏出一帧旧订阅的数据。
 *
 * 注意它是快照而非原始流：全速数据在记录文件里，这里只服务于实时观察。 */
void drms_cdc_v2_publish(DRMS_CDCV2 *ctx, uint32_t now)
{
  if (!ctx || !ctx->curve_subscribed || !ctx->send || !ctx->session.session)
    return;
  if ((uint32_t)(now - ctx->curve_last_ms) < ctx->curve_period_ms)
    return;
  if (ctx->can_send && !ctx->can_send(ctx->send_context, 0))
  {
    ++ctx->curve_lost;
    ctx->curve_last_ms = now;
    return;
  }
  DRMS_ApplicationSnapshot snapshot;
  if (!drms_application_snapshot(&snapshot))
  {
    ++ctx->curve_lost;
    ctx->curve_last_ms = now;
    return;
  }
  uint32_t epoch = ctx->curve_epoch;
  uint64_t sequence = ctx->curve_sequence + 1u;
  size_t len = drms_cdc_v2_encode_measurement(ctx->session.session, sequence,
      ctx->curve_lost, &snapshot, ctx->curve_wire, sizeof(ctx->curve_wire));
  if (!len)
  {
    ++ctx->curve_lost;
    ctx->curve_last_ms = now;
    return;
  }
  if (epoch != ctx->curve_epoch || !ctx->curve_subscribed)
  {
    /* 编码期间订阅被撤销或重建：这一帧属于已经不存在的订阅，丢弃但不计 lost
     * ——它本来就不该存在，不是链路问题。 */
    return;
  }
  ctx->curve_sequence = sequence;
  ctx->send(ctx->send_context, ctx->curve_wire, len, 0);
  ctx->curve_last_ms = now;
}

/* 为一次"会改变状态的请求"找一个缓存槽位。
 *
 * 槽位用来存放最近几次修改类请求的原始字节与结果，用途是幂等：
 * 主机因超时重发同一个 request_id 时，不必重新执行，直接回放原结果。
 *
 * 淘汰策略：优先用空槽；都满了就选年龄最老的那个。
 * 但**执行中的请求不会被淘汰**（有租约占着的那些），
 * 因为它们的最终结果还没产生，淘汰了就再也查不到了。 */
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

/* 收到一帧完整请求后的处理入口。
 *
 * 这是整个协议层的核心函数，做的事情按顺序是：
 *   1. 基本校验：主版本为 2、本机随机源健康、flags 为 0；
 *   2. HELLO 特判：只有它能带 session=0，其余请求必须已有有效会话；
 *   3. 会话与编号校验：request_id 必须递增，重复编号走幂等回放；
 *   4. 按 opcode 分派到各业务分支；
 *   5. 组装回复帧（固定头 + result + 各分支的字段 + CRC）。
 *
 * 两个容易忽略的约束：
 *   · 回复缓冲区拿不到就不受理请求，也不消耗编号——否则会出现
 *     "设备说受理了、但结果发不出来"的情况；
 *   · 分派失败时统一返回 UNSUPPORTED，而不是静默丢弃，
 *     让主机能区分"命令不支持"和"链路丢了"。
 *
 * 处理是同步的：这里只做分派与登记，耗时操作都转成异步（返回操作号）。 */
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
  uint32_t have_subscription = 0, subscribed_stream = 0, subscribed_period = 0;
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
      /* opcode 2 = GET_STATUS：取一次逻辑一致的整机状态快照。
       *
       * 没有请求字段。结果来自 drms_application_snapshot，那份快照是在
       * 一个临界区里整体取出的，所以主机拿到的字段互相自洽
       * （不会出现"电阻是新的、记录状态是旧的"）。
       *
       * 主机应当以它为实时性的唯一依据：status_revision 递增说明有新状态，
       * fresh 为 0 说明当前读数已经不是最新的。 */
      else if (opcode == 2u)
      {
        if (drms_cdc_fields_validate(request + 20, payload_len, NULL, 0, NULL))
          result = 3u;
        else if (!drms_application_snapshot(&snapshot))
          result = 2u;
        else
          have_snapshot = 1;
      }
      /* opcode 3 = GET_OPERATION：按操作号查异步操作的进展。
       *
       * 这是"先受理、后查询"模式的核心。绝大多数会改变状态的操作都先回
       * ACCEPTED + 操作号，主机随后用这个接口轮询。phase 表示阶段
       * （0 待办 / 1 执行中 / 2 已结束），result 是已知的最终结果。
       *
       * 查不到时返回 STALE 或 INVALID，两者含义不同：
       *   STALE   编号曾经有效，但已超出保留窗口——去读卡上的文件
       *   INVALID 编号从未分配——可能是主机记错了或连错了会话 */
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
      else if (opcode == 64u || opcode == 65u)
      {
        /* SUBSCRIBE / UNSUBSCRIBE. CURVE only: period_ms > 0 is the pushed
         * interval, RAW (period_ms = 0) is not implemented and is rejected
         * rather than silently accepted, so a client cannot believe it is
         * receiving raw frames. */
        static const DRMS_CDCFieldRule sub_rules[] = {{60,1,1,0,1},{61,4,4,0,1}};
        uint32_t now_stamp = ctx->feed_now;
        static const DRMS_CDCFieldRule unsub_rules[] = {{60,1,1,0,1}};
        DRMS_CDCFieldView fields[2];
        uint32_t stream, period = 0;
        int invalid = drms_cdc_fields_validate(request + 20, payload_len,
            opcode == 64u ? sub_rules : unsub_rules, opcode == 64u ? 2 : 1, fields);
        if (!invalid)
        {
          stream = fields[0].value[0];
          if (opcode == 64u)
            period = get32(fields[1].value);
          if (stream != 0u || (opcode == 64u && (period == 0u || period > 60000u)))
            invalid = 1;
        }
        if (invalid)
          result = DRMS_INVALID;
        else if (opcode == 64u)
        {
          ctx->curve_subscribed = 1;
          ctx->curve_period_ms = period;
          ctx->curve_sequence = 0;
          ctx->curve_lost = 0;
          ctx->curve_last_ms = now_stamp;
          ++ctx->curve_epoch; /* 让正在编码的旧帧作废 */
          result = DRMS_OK;
        }
        else
        {
          ctx->curve_subscribed = 0;
          ctx->curve_period_ms = 0;
          ++ctx->curve_epoch; /* 让正在编码的旧帧作废 */
          result = DRMS_OK;
        }
        subscribed_stream = stream;
        subscribed_period = period;
        have_subscription = 1;
      }
      /* opcode 53 = FILE_LIST：列举卡上的记录文件。
       *
       * 每次只返回一项，用 cursor 翻页（首次传 0）。不持有跨请求的租约，
       * 每次列举都重新申请一次 TF 访问权——这样记录、导出等功能不会被
       * 一个"翻到一半就不动了"的列举长期挡住。
       *
       * 第一次调用总是先返回 BUSY 并启动异步枚举，主机换一个新编号重试，
       * 直到拿到文件条目或空结果。这个"受理后重试"的模式与文件读取一致。
       *
       * media_generation 必须回带：换卡之后旧游标失效，主机应从头开始。 */
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
      /* opcode 51 = FILE_READ：按绝对偏移读一段文件内容（只读）。
       *
       * 约束：一次最多 768 字节；用绝对偏移而不是顺序位置，所以允许重读；
       * offset 等于文件大小时返回空数据并置 eof。
       *
       * 同样是异步的：首次受理返回 BUSY，主机用新编号重试同样的
       * (句柄, 偏移, 长度)，直到拿到数据。上一笔没完成时，换偏移会被拒。 */
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
      /* opcode 32 = GET_CONFIG：取当前完整配置。
       *
       * 出厂空配置、或旧配置缺少完整字段时返回 UNSUPPORTED——
       * 不能给一份"看起来完整、其实缺项"的配置，否则主机保存回去时会覆盖掉
       * 原本存在的设置。只有执行过一次完整的 APPLY_CONFIG 之后才可读。 */
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
      /* 其余都是"会改变状态"的请求，统一走这条路径：
       *
       *   16/17  BEGIN_RECORD / END_RECORD
       *   18/19  SAFE_STOP / RESUME_MONITOR
       *   33/34  APPLY_CONFIG / SAVE_CONFIG
       *   35/36  BUILD_R0 / CALIBRATE
       *   37     SET_UTC
       *   48/49  MSC_EXPORT / MSC_RELEASE
       *   50     FILE_OPEN
       *
       * 共同点：都要先经 drms_control 做资源裁决（会不会和当前记录、
       * 校准、导出冲突），批准后才交给应用层 dispatch 执行，
       * 执行结果通过操作号异步归结。
       *
       * 这里的字段规则是逐条声明的（rules 数组），校验失败直接拒绝——
       * 每种请求必填哪些字段、允许多长，都在规则里写死，不做宽松解释。 */
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
  uint8_t temp[48];
  put16(temp, result); tlv(out, &pos, 1, temp, 2);
  if (opcode == 1u)
  {
    for (unsigned i = 0; i < 3; ++i) put32(temp + i * 4, ctx->uid[i]);
    tlv(out, &pos, 3, temp, 12);
    put64(temp, ctx->session.boot); tlv(out, &pos, 4, temp, 8);
    put16(temp, 1); put16(temp + 2, 2); put16(temp + 4, 3); put16(temp + 6, 4);
    put16(temp + 8, 16); put16(temp + 10, 17); put16(temp + 12, 18); put16(temp + 14, 19);
    put16(temp + 16, 32); put16(temp + 18, 33); put16(temp + 20, 34); put16(temp + 22, 35); put16(temp + 24, 36); put16(temp + 26, 37); put16(temp + 28, 48); put16(temp + 30, 49); put16(temp + 32, 50); put16(temp + 34, 51); put16(temp + 36, 52); put16(temp + 38, 53);
    /* Subscription opcodes belong in the same capability list: a second TLV
     * with tag 5 would be rejected as a duplicate field. */
    put16(temp + 40, 64); put16(temp + 42, 65);
    tlv(out, &pos, 5, temp, 44);
    put16(temp, 1024); tlv(out, &pos, 6, temp, 2);
    put32(temp, 4000); tlv(out, &pos, 7, temp, 4);
    tlv(out, &pos, 8, temp, 4); /* conservative default; physical throughput still requires board tests */
  }
  else if (have_subscription)
  {
    uint8_t sb[1];
    sb[0] = (uint8_t)subscribed_stream;
    tlv(out, &pos, 60, sb, 1);
    if (opcode == 64u)
    {
      put32(temp, subscribed_period);
      tlv(out, &pos, 61, temp, 4);
    }
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

/* 初始化协议上下文。
 *
 * entropy 是启动标识的随机源。每个启动周期生成一个新的 64 位 boot 标识，
 * 主机用 (uid, boot, request_id) 三元组来识别"这是不是同一次上电"。
 * 若随机源不健康，会话不会被启用，设备保持脱机服务并上报诊断——
 * 宁可不出会话，也不要给一个可预测的标识。
 *
 * send / can_send 是发送回调，由 drms_cdc.c 注入，本文件不直接碰 USB。 */
void drms_cdc_v2_init(DRMS_CDCV2 *ctx, DRMS_CDCEntropy entropy, void *entropy_context,
                      const uint32_t uid[3], DRMS_CDCV2Send send, DRMS_CDCV2CanSend can_send,
                      void *send_context)
{
  memset(ctx, 0, sizeof(*ctx));
  if (uid) memcpy(ctx->uid, uid, sizeof(ctx->uid));
  ctx->send = send; ctx->can_send = can_send; ctx->send_context = send_context;
  (void)drms_cdc_session_init(&ctx->session, entropy, entropy_context);
}

/* USB 断线或复位：撤销会话及其所有附属状态。
 *
 * 需要清的东西包括：文件句柄与列举操作、幂等缓存、订阅。
 * 协议规定"断线后旧请求与订阅都不自动重放"——重连必须重新握手、
 * 重新订阅，这样主机看到的状态永远是从自己这一侧建立的，不会有残留。
 *
 * 注意这里不做介质层面的收尾：卡的所有权由 drms_msc 单独管理，
 * 断线不影响正在进行的记录。 */
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
  /* Subscriptions are session-scoped: a reconnect must re-subscribe rather
   * than inherit a stream the new client never asked for. */
  ctx->curve_subscribed = 0;
  ctx->curve_period_ms = 0;
  ctx->curve_sequence = 0;
  ctx->curve_lost = 0;
  ++ctx->curve_epoch; /* 让发送线程手里那一帧作废 */
}

/* 往解帧器里喂一个字节。由 CDC 接收线程逐字节调用。
 *
 * 之所以是逐字节而不是整块：COBS 是"以 0 分隔"的流式编码，
 * 必须按字节扫描才能正确切帧，而且任意拆包/粘包都要能处理。
 * 解帧完成后解帧器会回调 received()。
 *
 * now 用于解帧器的超时逻辑：半帧堆积超过 1000 ms 仍无分隔符就丢弃，
 * 避免一个坏帧把后续所有数据都堵在缓冲区里。 */
void drms_cdc_v2_feed(DRMS_CDCV2 *ctx, uint8_t byte, uint32_t now)
{
  ctx->feed_now = now;
  drms_cdc_frame_feed(&ctx->frame, byte, now, received, ctx);
}
