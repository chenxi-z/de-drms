/*****************************************************************************
 * 文件：drms_fifo.c
 * 职责：单生产者单消费者（SPSC）无锁环形队列——采集环、记录环的基础。
 *
 * 为什么不用互斥量：
 *   生产者跑在中断里，消费者跑在线程里。中断里拿不到互斥量，也不能等。
 *   SPSC 场景下只要保证"生产者只写 head、消费者只写 tail"，
 *   再用原子操作配合内存序就能完全无锁，且不会丢数据。
 *
 * 内存序的取值理由：
 *   head/tail 用 release 写、acquire 读，保证元素内容在读者看到索引更新之前
 *   就已经写完。这是无锁队列正确性的关键，不是可以省略的优化。
 *
 * 容量约定：
 *   容量必须是 2 的幂，索引用位与代替取模——在中断里能省下除法的时间。
 *****************************************************************************/

#include "drms_fifo.h"
#include <string.h>

int drms_fifo_init(DRMS_FIFO *fifo, void *storage, uint32_t capacity, uint32_t stride)
{
  if (!storage || !stride || !capacity || (capacity & (capacity - 1U)) || capacity > 0x40000000U)
    return 0;
  fifo->storage = storage;
  fifo->capacity = capacity;
  fifo->stride = stride;
  fifo->head = fifo->tail = 0;
  return 1;
}

int drms_fifo_push(DRMS_FIFO *fifo, const void *item)
{
  uint32_t head = __atomic_load_n(&fifo->head, __ATOMIC_RELAXED);
  uint32_t tail = __atomic_load_n(&fifo->tail, __ATOMIC_ACQUIRE);
  if ((uint32_t)(head - tail) >= fifo->capacity)
    return 0;
  memcpy((uint8_t *)fifo->storage + (head & (fifo->capacity - 1U)) * fifo->stride, item, fifo->stride);
  __atomic_store_n(&fifo->head, head + 1U, __ATOMIC_RELEASE);
  return 1;
}

int drms_fifo_pop(DRMS_FIFO *fifo, void *item)
{
  uint32_t tail = __atomic_load_n(&fifo->tail, __ATOMIC_RELAXED);
  uint32_t head = __atomic_load_n(&fifo->head, __ATOMIC_ACQUIRE);
  if (tail == head)
    return 0;
  memcpy(item, (uint8_t *)fifo->storage + (tail & (fifo->capacity - 1U)) * fifo->stride, fifo->stride);
  __atomic_store_n(&fifo->tail, tail + 1U, __ATOMIC_RELEASE);
  return 1;
}

uint32_t drms_fifo_count(const DRMS_FIFO *fifo)
{
  uint32_t tail = __atomic_load_n(&fifo->tail, __ATOMIC_ACQUIRE);
  uint32_t head = __atomic_load_n(&fifo->head, __ATOMIC_ACQUIRE);
  return head - tail;
}
