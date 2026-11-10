#include "drms_file_backend.h"
#include "drms_storage.h"
#include "drms_logging.h"
#include "drms_msc.h"
#include "app_filex.h"
#include <stdio.h>
#include <string.h>

extern FX_MEDIA sdio_disk;
static FX_FILE file;
static uint32_t is_open, owner_session, owner_generation;
static uint64_t file_size;

void drms_file_backend_init(void) { memset(&file, 0, sizeof(file)); is_open = owner_session = owner_generation = 0; file_size = 0; }
void drms_file_backend_invalidate(void) { drms_file_backend_init(); }
static uint32_t ready(void) { return drms_storage_mounted && drms_msc_owner() == DRMS_OWNER_LOCAL && !drms_log_state; }

DRMS_Result drms_file_backend_list_step(uint32_t cursor, uint32_t generation,
                                        uint32_t *id, uint64_t *size, uint32_t *next)
{
  if (!id || !size || !next) return DRMS_INVALID;
  if (generation != drms_storage_media_generation()) return DRMS_STALE;
  if (is_open || !ready()) return DRMS_BUSY;
  if (cursor >= 10000u) return DRMS_EMPTY;
  char name[16]; FX_FILE candidate;
  (void)snprintf(name, sizeof(name), "DRMS%04lu.BIN", (unsigned long)cursor);
  memset(&candidate, 0, sizeof(candidate));
  UINT status = fx_file_open(&sdio_disk, &candidate, name, FX_OPEN_FOR_READ);
  *next = cursor + 1u;
  if (status == FX_NOT_FOUND) return DRMS_ACCEPTED;
  if (status != FX_SUCCESS) return DRMS_IO_ERROR;
  uint64_t length = (uint64_t)candidate.fx_file_current_file_size;
  if (fx_file_close(&candidate) != FX_SUCCESS) return DRMS_IO_ERROR;
  *id = cursor; *size = length;
  return DRMS_OK;
}

DRMS_Result drms_file_backend_open(uint32_t id, uint32_t session, uint32_t generation, uint64_t *size)
{
  if (!size || !session || id >= 10000u) return DRMS_INVALID;
  *size = 0;
  if (generation != drms_storage_media_generation()) return DRMS_STALE;
  if (is_open || !ready()) return DRMS_BUSY;
  char name[16];
  (void)snprintf(name, sizeof(name), "DRMS%04lu.BIN", (unsigned long)id);
  memset(&file, 0, sizeof(file));
  UINT status = fx_file_open(&sdio_disk, &file, name, FX_OPEN_FOR_READ);
  if (status == FX_NOT_FOUND) return DRMS_INVALID;
  if (status != FX_SUCCESS) return DRMS_IO_ERROR;
  is_open = 1; owner_session = session; owner_generation = generation;
  file_size = (uint64_t)file.fx_file_current_file_size;
  *size = file_size;
  return DRMS_OK;
}

DRMS_Result drms_file_backend_read(uint32_t session, uint32_t generation, uint64_t offset,
                                   uint16_t count, uint8_t *out, uint16_t *actual, uint8_t *eof)
{
  if (!out || !actual || !eof || !count || count > 768u) return DRMS_INVALID;
  *actual = 0; *eof = 0;
  if (!is_open || session != owner_session || generation != owner_generation) return DRMS_STALE;
  if (generation != drms_storage_media_generation()) { drms_file_backend_invalidate(); return DRMS_STALE; }
  if (!ready()) return DRMS_BUSY;
  if (offset > file_size) return DRMS_INVALID;
  uint64_t remaining = file_size - offset;
  ULONG wanted = (ULONG)(remaining < count ? remaining : count);
  if (!wanted) { *eof = 1; return DRMS_OK; }
  ULONG got = 0;
  if (fx_file_extended_seek(&file, (ULONG64)offset) != FX_SUCCESS ||
      fx_file_read(&file, out, wanted, &got) != FX_SUCCESS || got != wanted)
  {
    (void)fx_file_close(&file);
    drms_file_backend_invalidate();
    return DRMS_IO_ERROR;
  }
  *actual = (uint16_t)got;
  *eof = offset + got == file_size;
  return DRMS_OK;
}

DRMS_Result drms_file_backend_close(uint32_t session, uint32_t generation)
{
  if (!is_open || session != owner_session || generation != owner_generation) return DRMS_STALE;
  if (generation != drms_storage_media_generation()) { drms_file_backend_invalidate(); return DRMS_STALE; }
  if (!ready()) return DRMS_BUSY;
  UINT status = fx_file_close(&file);
  drms_file_backend_invalidate();
  return status == FX_SUCCESS ? DRMS_OK : DRMS_IO_ERROR;
}
