#ifndef DRMS_FILE_BACKEND_H
#define DRMS_FILE_BACKEND_H
#include "drms_architecture_contract.h"
/* FileX owner only. Caller must hold the TF_ACCESS lease for the entire open
 * lifetime; this module also checks medium, session and generation defensively.
 * It never accepts a path from the host. */
void drms_file_backend_init(void);
/* Probe at most one numbered file per call: OK=found, ACCEPTED=advance cursor,
 * EMPTY=end. Caller yields between calls and holds a short TF_ACCESS lease. */
DRMS_Result drms_file_backend_list_step(uint32_t cursor, uint32_t media_generation,
                                        uint32_t *file_id, uint64_t *size, uint32_t *next_cursor);
DRMS_Result drms_file_backend_open(uint32_t file_id, uint32_t session, uint32_t media_generation,
                                   uint64_t *size);
DRMS_Result drms_file_backend_read(uint32_t session, uint32_t media_generation, uint64_t offset,
                                   uint16_t count, uint8_t *out, uint16_t *actual, uint8_t *eof);
DRMS_Result drms_file_backend_close(uint32_t session, uint32_t media_generation);
/* Storage owner invokes only after abort/unmount on removal or quarantine;
 * this clears stale FileX state without touching an invalid medium. */
void drms_file_backend_invalidate(void);
#endif
