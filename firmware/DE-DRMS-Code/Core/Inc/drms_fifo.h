#ifndef DRMS_FIFO_H
#define DRMS_FIFO_H
#include <stdint.h>

/* Exactly one producer and one consumer; reset only while both are quiescent. */
typedef struct {
  uint32_t head, tail, capacity, stride;
  void *storage;
} DRMS_FIFO;
int drms_fifo_init(DRMS_FIFO *fifo, void *storage, uint32_t capacity, uint32_t stride);
int drms_fifo_push(DRMS_FIFO *fifo, const void *item);
int drms_fifo_pop(DRMS_FIFO *fifo, void *item);
uint32_t drms_fifo_count(const DRMS_FIFO *fifo);
#endif
