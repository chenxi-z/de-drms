/*****************************************************************************
 * 文件：drms_file_service.c
 * 职责：历史文件访问服务——把"打开/读取/关闭"请求排成队，交给 FileX 线程执行。
 *
 * 为什么要单独一层：
 *   文件操作必须在 FileX 线程里做（介质只有一个属主），
 *   而请求来自 CDC 线程。这里用请求/票据机制做跨线程交接：
 *   调用方提交请求拿到票据，FileX 线程执行后用票据取回结果。
 *
 * 租约（lease）：
 *   一次下载会话期间持续持有 TF_ACCESS，不是逐次读取才申请。
 *   否则读取途中别的路径可能插进来用卡，两边的文件位置会互相打乱。
 *
 * 断线处理：
 *   会话断开时把所有未完成的请求取消掉，并把"已撤销到的会话号"记下来。
 *   晚到的、属于旧会话的请求会因低于水位而被拒——
 *   这样旧客户端的残请求不会动到新客户端的资源。
 *****************************************************************************/

#include "drms_file_service.h"
#include "drms_file_backend.h"
#include "main.h"
#include <string.h>

/* 0 empty, 1 queued, 2 executing, 3 done, 4 reply copy in progress. */
static uint32_t state, revoked, quarantined, owner_session, owner_generation;
static uint64_t next_ticket;
static DRMS_Result last_result;
static DRMS_FileRequest input;
static DRMS_FileReply reply;
static uint32_t lock(void) { uint32_t mask=__get_PRIMASK(); __disable_irq(); return mask; }
static void unlock(uint32_t mask) { __set_PRIMASK(mask); }

void drms_file_service_init(void)
{
  uint32_t m=lock(); state=revoked=quarantined=owner_session=owner_generation=0;
  next_ticket=1; last_result=DRMS_OK; memset(&input,0,sizeof(input)); memset(&reply,0,sizeof(reply)); unlock(m);
}
DRMS_Result drms_file_service_submit(const DRMS_FileRequest *r, uint64_t *ticket)
{
  if (!r || !ticket || !r->session || r->kind < DRMS_FILE_LIST || r->kind > DRMS_FILE_CLOSE ||
      (r->kind == DRMS_FILE_READ && (!r->count || r->count > 768u))) return DRMS_INVALID;
  *ticket=0;
  uint32_t m=lock();
  if (quarantined) { unlock(m); return DRMS_QUARANTINED; }
  if (state || revoked || !next_ticket) { unlock(m); return DRMS_BUSY; }
  if ((r->kind == DRMS_FILE_OPEN || r->kind == DRMS_FILE_LIST) && owner_session)
    { unlock(m); return DRMS_BUSY; }
  if ((r->kind == DRMS_FILE_READ || r->kind == DRMS_FILE_CLOSE) &&
      (!owner_session || r->session != owner_session || r->generation != owner_generation))
    { unlock(m); return DRMS_STALE; }
  input=*r; reply.ticket=next_ticket++; *ticket=reply.ticket; state=1; unlock(m); return DRMS_ACCEPTED;
}
DRMS_Result drms_file_service_take(uint64_t ticket, DRMS_FileReply *out)
{
  if (!ticket || !out) return DRMS_INVALID;
  uint32_t m=lock();
  if (!state || reply.ticket != ticket || revoked) { unlock(m); return DRMS_STALE; }
  if (state != 3) { unlock(m); return DRMS_ACCEPTED; }
  state=4; unlock(m);
  memcpy(out,&reply,sizeof(*out)); /* large copy with interrupts enabled */
  m=lock(); uint32_t cancelled=revoked; state=0; unlock(m);
  return cancelled ? DRMS_STALE : DRMS_OK;
}
void drms_file_service_disconnect(uint32_t session)
{
  if (!session) return;
  uint32_t m=lock();
  if ((state && input.session == session) || owner_session == session) revoked=1;
  unlock(m);
}
void drms_file_service_cancel_all(void)
{
  uint32_t m=lock();
  if (state || owner_session) revoked=1;
  unlock(m);
}
uint32_t drms_file_service_quiescent(void)
{
  uint32_t m=lock(); uint32_t result=!state && !revoked && !owner_session && !quarantined; unlock(m); return result;
}
uint32_t drms_file_service_quarantined(void)
{
  uint32_t m=lock(); uint32_t result=quarantined; unlock(m); return result;
}
DRMS_Result drms_file_service_last_result(void)
{
  uint32_t m=lock(); DRMS_Result result=last_result; unlock(m); return result;
}
DRMS_Result drms_file_service_after_media_abort(void)
{
  uint32_t m=lock();
  if (state == 2 || state == 4) { unlock(m); return DRMS_BUSY; }
  state=revoked=quarantined=owner_session=owner_generation=0;
  unlock(m); return DRMS_OK;
}
void drms_file_service_poll(void)
{
  uint32_t m=lock();
  if (quarantined || state == 2 || state == 4) { unlock(m); return; }
  if (revoked)
  {
    if (state == 1 || state == 3) state=0;
    uint32_t session=owner_session, generation=owner_generation;
    state=2; unlock(m);
    DRMS_Result result=session ? drms_file_backend_close(session,generation) : DRMS_OK;
    m=lock();
    if (result == DRMS_BUSY) { state=0; unlock(m); return; }
    if (result != DRMS_OK) { quarantined=1; last_result=DRMS_QUARANTINED; }
    else { owner_session=owner_generation=0; revoked=0; last_result=DRMS_CANCELLED; }
    state=0; unlock(m); return;
  }
  if (state != 1) { unlock(m); return; }
  state=2; DRMS_FileRequest r=input; unlock(m);
  DRMS_Result result;
  reply.file_id=reply.next_cursor=0; reply.size=0; reply.offset=r.offset; reply.length=0; reply.eof=0;
  switch (r.kind)
  {
    case DRMS_FILE_LIST:
      result=drms_file_backend_list_step(r.cursor,r.generation,&reply.file_id,&reply.size,&reply.next_cursor); break;
    case DRMS_FILE_OPEN:
      result=drms_file_backend_open(r.file_id,r.session,r.generation,&reply.size); break;
    case DRMS_FILE_READ:
      result=drms_file_backend_read(r.session,r.generation,r.offset,r.count,reply.data,&reply.length,&reply.eof); break;
    default:
      result=drms_file_backend_close(r.session,r.generation); break;
  }
  m=lock();
  if (r.kind == DRMS_FILE_OPEN && result == DRMS_OK) { owner_session=r.session; owner_generation=r.generation; last_result=DRMS_OK; }
  if (r.kind == DRMS_FILE_CLOSE && result == DRMS_OK) { owner_session=owner_generation=0; last_result=DRMS_OK; }
  if (r.kind == DRMS_FILE_READ && result == DRMS_IO_ERROR) { owner_session=owner_generation=0; last_result=DRMS_IO_ERROR; }
  if (result == DRMS_QUARANTINED || (owner_session && result == DRMS_STALE)) quarantined=1;
  if (revoked) { state=0; unlock(m); drms_file_service_poll(); return; }
  if (r.kind == DRMS_FILE_LIST && result == DRMS_ACCEPTED) { input.cursor=reply.next_cursor; state=1; unlock(m); return; }
  reply.result=result; state=3; unlock(m);
}
