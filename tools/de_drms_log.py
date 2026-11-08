#!/usr/bin/env python3
"""Stream DE-DRMS v1 binary logs to CSV and report integrity/loss counters."""
import argparse
import binascii
import csv
import json
import math
from pathlib import Path
import struct
import sys
import zlib

SPEC = json.loads((Path(__file__).resolve().parents[1] / 'shared/protocol/de-drms-v1.json').read_text())
FILE_SPEC = SPEC['file']


def fields(block, definitions):
    return {name: struct.unpack_from('<' + item['format'], block, item['offset'])[0]
            for name, item in definitions.items()}


def check_block(block, definitions, magic):
    if len(block) != 64:
        raise ValueError('incomplete header/footer')
    result = fields(block, definitions)
    if result['magic'] != magic or result['version'] != 1:
        raise ValueError('unsupported file magic/version')
    if result['crc32'] != zlib.crc32(block[:60]):
        raise ValueError('header/footer CRC32 mismatch')
    return result


class LogReader:
    def __init__(self, stream):
        self.stream = stream
        self.header = check_block(stream.read(64), FILE_SPEC['header'], b'DRMS')
        if self.header['header_size'] != 64 or self.header['record_size'] != 16:
            raise ValueError('unsupported header/record size')
        if self.header['rate'] not in SPEC['control']['rates']:
            raise ValueError('unsupported sample rate')
        for name in ('scale_ohms', 'reference_ohms'):
            bounds = FILE_SPEC['header'][name]
            if not math.isfinite(self.header[name]) or not bounds['minimum'] <= self.header[name] <= bounds['maximum']:
                raise ValueError(f'invalid {name}')
        self.footer = None
        self.clean_end = False
        self.records = self.crc_errors = self.sequence_gaps = self.sequence_disorder = 0
        self.format_errors = self.adc_faults = self.valid_samples = 0
        self.partial_bytes = 0

    def __iter__(self):
        first_sequence = previous = None
        elapsed_edges = 0
        while True:
            record = self.stream.read(16)
            if not record:
                return
            if len(record) != 16:
                self.partial_bytes = len(record)
                return
            if record[:4] == b'DEND':
                rest = self.stream.read(48)
                if len(rest) != 48:
                    self.partial_bytes = 16 + len(rest)
                    return
                self.footer = check_block(record + rest, FILE_SPEC['footer'], b'DEND')
                if self.footer['footer_size'] != 64 or self.footer['records'] != (self.records & 0xffffffff):
                    raise ValueError('footer record count/size mismatch')
                if self.stream.read(1):
                    raise ValueError('unexpected bytes after footer')
                self.clean_end = True
                return
            frame = record[:12]
            sequence = struct.unpack_from('<I', record, 12)[0]
            gap = 0
            sequence_error = False
            if first_sequence is None:
                first_sequence = sequence
            elif previous is not None:
                delta = (sequence - previous) & 0xffffffff
                if not delta or delta >= 0x80000000:
                    self.sequence_disorder += 1
                    sequence_error = True
                else:
                    gap = delta - 1
                    elapsed_edges += delta
                    self.sequence_gaps += gap
            previous = sequence
            voltage = int.from_bytes(frame[3:6], 'big', signed=True)
            sense = int.from_bytes(frame[6:9], 'big', signed=True)
            status = int.from_bytes(frame[:2], 'big')
            crc_ok = binascii.crc_hqx(frame[:9], 0xffff) == int.from_bytes(frame[9:11], 'big')
            format_ok = frame[0] == 0x22 and not (frame[1] & 0x80) and frame[2] == 0 and frame[11] == 0
            adc_fault = bool(frame[1] & 0x6f)
            range_error = voltage >= 8388606 or voltage <= -8388607 or sense >= 8388606 or sense <= 4096 or voltage < -4096
            guard = FILE_SPEC['excitation_guard']
            excitation_ok = crc_ok and format_ok and not adc_fault and not range_error and guard['sense_code_min'] <= sense <= guard['sense_code_max'] and voltage + sense <= guard['voltage_plus_sense_code_max']
            valid = crc_ok and format_ok and not adc_fault and not range_error and excitation_ok
            self.records += 1
            self.crc_errors += not crc_ok
            self.format_errors += not format_ok
            self.adc_faults += adc_fault
            self.valid_samples += valid
            yield {
                'sequence': sequence, 'elapsed_s': elapsed_edges / self.header['rate'],
                'voltage_code': voltage, 'sense_code': sense, 'status_hex': f'{status:04X}',
                'crc_ok': int(crc_ok), 'format_ok': int(format_ok), 'adc_fault': int(adc_fault),
                'range_error': int(range_error), 'excitation_ok': int(excitation_ok), 'sequence_gap': gap, 'sequence_error': int(sequence_error),
                'ohms': self.header['scale_ohms'] * voltage / sense if valid else None,
                'calibrated': int(bool(self.header['flags'] & 1))
            }

    def summary(self):
        reported_loss = self.sequence_gaps or self.sequence_disorder or self.crc_errors or self.format_errors or self.adc_faults
        if self.footer:
            reported_loss = reported_loss or any(self.footer[key] for key in ('log_dropped', 'spi_overruns', 'frame_queue_drops'))
        return {'clean_end': self.clean_end, 'no_reported_loss': bool(self.clean_end and not reported_loss),
                'records': self.records, 'valid_samples': self.valid_samples,
                'invalid_samples': self.records - self.valid_samples, 'crc_errors': self.crc_errors,
                'format_errors': self.format_errors, 'adc_faults': self.adc_faults,
                'sequence_gaps': self.sequence_gaps, 'sequence_disorder': self.sequence_disorder,
                'partial_bytes': self.partial_bytes, 'footer': self.footer}


class LogReaderV2:
    """v2 chunked reader（docs/design/2026-11-06-record-v2-format.md）。"""

    CHUNK_HEADER, CHUNK_DATA, CHUNK_END = 1, 2, 3

    def __init__(self, stream):
        self.stream = stream
        self.incomplete_reason = None
        self.error = None
        self.header = self.end = None
        self.data_chunks = self.records = 0
        self.dup_end = trailing = False
        head = stream.read(4)
        stream.seek(0)
        if head == b'DRMS' or head[:2] != b'\x01\x00':
            raise ValueError('not a v2 chunk stream')
        self._parse()

    def _chunk(self):
        head = self.stream.read(4)
        if not head:
            return None
        if len(head) != 4:
            self.incomplete_reason = 'truncated chunk header'
            return None
        ctype, length = struct.unpack('<HH', head)
        payload = self.stream.read(length)
        if len(payload) != length:
            self.incomplete_reason = 'truncated chunk payload'
            return None
        return ctype, payload

    def _parse(self):
        seen_end = False
        while True:
            chunk = self._chunk()
            if chunk is None:
                if self.incomplete_reason:
                    self.error = self.incomplete_reason
                elif not seen_end:
                    self.error = 'missing END chunk'
                return
            ctype, payload = chunk
            if seen_end:
                self.error = 'bytes after END chunk'
                return
            if len(payload) < 4 or struct.unpack_from('<I', payload, len(payload) - 4)[0] != \
                    zlib.crc32(payload[:len(payload) - 4]):
                self.error = 'chunk CRC mismatch'
                return
            body = payload[:len(payload) - 4]
            if ctype == self.CHUNK_HEADER:
                if self.header is not None:
                    self.error = 'duplicate HEADER chunk'
                    return
                self.header = self._parse_header(body)
                if self.header is None:
                    self.error = 'invalid HEADER chunk'
                    return
            elif ctype == self.CHUNK_DATA:
                if self.header is None or len(body) == 0 or len(body) % 16:
                    self.error = 'invalid DATA chunk'
                    return
                self.data_chunks += 1
                self.records += len(body) // 16
            elif ctype == self.CHUNK_END:
                if self.header is None:
                    self.error = 'END before HEADER'
                    return
                self.end = self._parse_end(body)
                if self.end is None:
                    self.error = 'invalid END chunk'
                    return
                seen_end = True
            else:
                self.error = f'unknown chunk type {ctype}'
                return

    def _parse_header(self, body):
        if len(body) < 58:
            return None
        (version, record_size, flags, rate, w0, w1, w2, record_id,
         gen, arate, seq0, mono0, config_len) = struct.unpack_from(
            '<HHIIIIIQIIQQH', body, 0)
        if version != 2 or record_size != 16 or rate == 0 or config_len != len(body) - 58:
            return None
        config = body[58:58 + config_len]
        if config_len and (len(config) < 44 or
                           struct.unpack_from('<I', config, len(config) - 4)[0] !=
                           zlib.crc32(config[:len(config) - 4])):
            return None
        return {'version': version, 'record_size': record_size, 'flags': flags, 'rate': rate,
                'uid': (w0, w1, w2), 'record_id': record_id,
                'anchor': {'generation': gen, 'rate_hz': arate,
                           'sample_seq0': seq0, 'mono_us0': mono0},
                'config': config}

    def _parse_end(self, body):
        if len(body) != 83:
            return None
        (gen, record_id, ring_end, lost, first, end_excl, last_confirmed,
         end_known, capture_lost, log_dropped, quality_bad,
         unknown, storage_error, reason) = struct.unpack_from(
            '<IQQQQQQBQQQBBI', body, 0)
        if not end_known and end_excl != 0:
            return None  # 未知末边界不得携带伪精确值
        return {'acquisition_generation': gen, 'record_id': record_id, 'ring_end': ring_end,
                'lost_count': lost, 'first_index': first, 'end_exclusive_index': end_excl,
                'last_confirmed_index': last_confirmed, 'end_known': bool(end_known),
                'capture_lost': capture_lost, 'log_dropped': log_dropped,
                'quality_bad': quality_bad, 'unknown_loss': bool(unknown),
                'storage_error': bool(storage_error), 'reason': reason}

    def complete(self):
        return self.error is None and self.end is not None

    def summary(self):
        end = self.end or {}
        incomplete = not self.complete() or not end.get('end_known') or \
            end.get('unknown_loss') or end.get('storage_error') or \
            end.get('reason') not in (0, 12) or end.get('capture_lost') or \
            end.get('log_dropped') or end.get('quality_bad')
        return {'complete': self.complete(), 'error': self.error,
                'records': self.records, 'data_chunks': self.data_chunks,
                'header': self.header, 'end': self.end,
                'no_reported_loss': bool(self.complete() and not incomplete)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--csv', type=Path, help='CSV path; defaults to stdout')
    parser.add_argument('--allow-incomplete', action='store_true', help='allow diagnostic recovery of an unclean/lossy prefix')
    args = parser.parse_args()
    output = None
    try:
        if args.csv and (args.csv.resolve() == args.input.resolve() or
                         (args.csv.exists() and args.input.samefile(args.csv))):
            raise ValueError('CSV output must not overwrite the source log')
        with args.input.open('rb') as stream:
            probe = stream.read(8)
            stream.seek(0)
            # v1 以 'DRMS' 魔数开始；v2 为 chunk 流（首块 type=1 HEADER）
            reader = LogReader(stream) if probe[:4] == b'DRMS' else LogReaderV2(stream)
            output = args.csv.open('w', newline='') if args.csv else sys.stdout
            writer = None
            for row in reader:
                if writer is None:
                    writer = csv.DictWriter(output, fieldnames=list(row))
                    writer.writeheader()
                writer.writerow(row)
            summary = reader.summary()
            # Raw magic is bytes; keep the machine-readable summary valid JSON.
            if summary['footer']:
                summary['footer'] = {key: value.decode('ascii') if isinstance(value, bytes) else value
                                     for key, value in summary['footer'].items()}
            print(json.dumps(summary, ensure_ascii=False), file=sys.stderr)
            return 0 if summary['no_reported_loss'] or args.allow_incomplete else 1
    except (OSError, ValueError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 2
    finally:
        if output is not None and output is not sys.stdout:
            output.close()


if __name__ == '__main__':
    raise SystemExit(main())
