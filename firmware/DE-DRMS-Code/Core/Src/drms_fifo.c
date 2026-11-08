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
