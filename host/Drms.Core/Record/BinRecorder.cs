using System.Buffers.Binary;
using Drms.Core.Protocol;

namespace Drms.Core.Record;

/// <summary>
/// 把 RAW 实时流在 PC 侧落盘成 **BIN v2 记录文件**（与设备写出的格式逐字节同构）。
///
/// 为什么不在 PC 侧另造格式：
///   · 16 B/帧，CSV 会大 3 倍（4 kSPS ≈ 230 MB/h vs ~700 MB/h）；
///   · <c>tools/de_drms_log.py</c> 与将来的历史回放能直接读，不用第二套解析器。
///
/// 与设备记录的区别（都如实体现，不伪装）：
///   · 时间锚点 <c>mono_us0</c> 设备不通过 RAW 下发，写 0；时间轴以样本序号 × 1/rate 重建
///     （读取器就是这么算 elapsed 的，不依赖 mono_us0）；
///   · 丢帧只可能来自 USB（主机卡顿/拔线），表现为帧序号缺口与设备上报的 <c>lost</c>，
///     写入 END 的 capture_lost / unknown_loss 并置 reason=INCOMPLETE；
///   · 每个轮转文件是一条**独立完整记录**（自己的 record_id 与 END），不依赖分段规则；
///     序号跨文件连续，拼起来仍可校验连续性。
///
/// 线程模型：单线程调用（RAW 事件回调或专用循环），内部不锁。
/// </summary>
public sealed class BinRecorder : IDisposable
{
    private const int ChunkFrames = 256;      // 设备同款上限（u16 长度：16×256+4=4100）
    private const int HeaderFixed = 58;

    private readonly string _directory;
    private readonly string _prefix;
    private readonly long _rotateBytes;
    private readonly uint[] _uid;
    private readonly uint _rate;
    private readonly uint _generation;
    private readonly uint _calibrationGeneration;
    private readonly bool _calibrationValid;
    private readonly double _scaleOhms;
    private readonly double _referenceOhms;
    private readonly ulong _bootId;

    private FileStream? _stream;
    private byte[] _pending = new byte[ChunkFrames * 16];
    private int _pendingCount;
    private uint _recordId;
    private ulong _firstIndex;
    private ulong _lastIndex;
    private ulong _framesWritten;
    private ulong _framesThisFile;
    private ulong _gaps;            // 帧序号缺口累计（本文件）
    private ulong _crcBad;         // 帧 CRC 坏帧（本文件）
    private ulong _lostReported;   // 设备侧 lost 增量（本文件）
    private ulong _lastLostTotal;  // 设备累计 lost（跨文件跟踪）
    private uint? _lastSequence;   // 32 位原始序号（跨文件跟踪）
    private bool _hasSequence;
    private int _fileIndex;
    private bool _closed;
    private bool _headerWritten;

    /// <summary>已写入的总帧数与当前文件路径，供上层显示。</summary>
    public ulong FramesWritten => _framesWritten;
    public string? CurrentPath { get; private set; }
    public int FilesCreated => _fileIndex;

    /// <param name="directory">输出目录（不存在会创建）。</param>
    /// <param name="prefix">文件名前缀，产物为 <c>{prefix}{序号:D4}.BIN</c>。</param>
    /// <param name="rotateBytes">单文件上限，达到后收尾并新开一个（0 = 不轮转）。</param>
    public BinRecorder(string directory, string prefix, uint[] uid, uint rate, uint generation,
                       uint recordId, long rotateBytes = 1L << 30,
                       bool calibrationValid = false, uint calibrationGeneration = 0,
                       double scaleOhms = 0, double referenceOhms = 0, ulong bootId = 0)
    {
        _directory = directory;
        _prefix = prefix;
        _uid = uid;
        _rate = rate;
        _generation = generation;
        _recordId = recordId;
        _rotateBytes = rotateBytes;
        _calibrationValid = calibrationValid;
        _calibrationGeneration = calibrationGeneration;
        _scaleOhms = scaleOhms;
        _referenceOhms = referenceOhms;
        _bootId = bootId;
        Directory.CreateDirectory(directory);
    }

    /// <summary>喂入一批 RAW 帧（每帧 16 B：12 B ADC + u32 序号，小端）。</summary>
    public void Append(ReadOnlySpan<byte> frames, ulong lostTotal)
    {
        if (_closed) throw new InvalidOperationException("记录器已关闭");
        for (int offset = 0; offset + 16 <= frames.Length; offset += 16)
        {
            ReadOnlySpan<byte> frame = frames.Slice(offset, 16);
            uint sequence = BinaryPrimitives.ReadUInt32LittleEndian(frame[12..]);

            if (_framesThisFile == 0)
            {
                /* 首帧到达才建文件：HEADER 的时间锚点必须是真实的起始序号。 */
                if (_stream is null) OpenFile(_generation);
                _firstIndex = sequence;
                if (!_headerWritten) { WriteHeader(_generation); _headerWritten = true; }
            }

            if (_hasSequence)
            {
                uint delta = sequence - _lastSequence!.Value;
                if (delta == 0 || delta >= 0x80000000u) _gaps++;      // 乱序/重复按一次缺口记
                else _gaps += delta - 1;
            }
            _hasSequence = true;
            _lastSequence = sequence;
            _lastIndex = sequence;

            if (!RawEventCrcOk(frame)) _crcBad++;
            frame.CopyTo(_pending.AsSpan(_pendingCount * 16));
            _pendingCount++;
            _framesWritten++;
            _framesThisFile++;
            if (_pendingCount == ChunkFrames) FlushChunk();
            /* 轮转在块边界判定：当前块已落盘且文件到量 → 收尾，下一帧自然开新文件。 */
            if (_rotateBytes > 0 && _pendingCount == 0 && _stream is { } s && s.Length >= _rotateBytes)
                CloseFile(reason: 0, unknownLoss: false);
        }
        /* 设备累计 lost 的增量归属当前文件（放循环后：文件可能在本批中途才建立）。 */
        if (lostTotal > _lastLostTotal)
        {
            _lostReported += lostTotal - _lastLostTotal;
            _lastLostTotal = lostTotal;
        }
    }

    /// <summary>正常收尾：写完当前块与 END。可重复调用（幂等）。</summary>
    public void Finish()
    {
        if (_closed) return;
        FlushChunk();
        bool lossy = _gaps > 0 || _lostReported > 0 || _crcBad > 0;
        CloseFile(reason: lossy ? 9u : 0u, unknownLoss: _lostReported > 0 || _gaps > 0);
        _closed = true;
    }

    public void Dispose()
    {
        // 未 Finish 就退出：直接关文件，不留伪 END —— 读取器会判"不完整"，这是如实的。
        if (!_closed)
        {
            FlushChunk();
            _stream?.Flush();
            _stream?.Dispose();
            _stream = null;
            _closed = true;
        }
    }

    private static bool RawEventCrcOk(ReadOnlySpan<byte> frame)
    {
        ushort crc = (ushort)((frame[9] << 8) | frame[10]);
        return RawEvent.Crc16Ccitt(frame[..9]) == crc;
    }

    private void OpenFile(uint generation)
    {
        _fileIndex++;
        string path = Path.Combine(_directory, $"{_prefix}{_fileIndex:D4}.BIN");
        CurrentPath = path;
        _stream = new FileStream(path, FileMode.Create, FileAccess.Write, FileShare.Read, 1 << 16);
        _framesThisFile = 0;
        _gaps = 0;
        _crcBad = 0;
        _lostReported = 0;
        _headerWritten = false;
    }

    private void WriteHeader(uint generation)
    {
        byte[] config = BuildConfig();
        var payload = new byte[HeaderFixed + config.Length + 4];
        int p = 0;
        void U16(ushort v) { payload[p++] = (byte)v; payload[p++] = (byte)(v >> 8); }
        void U32(uint v) { for (int i = 0; i < 4; i++) payload[p++] = (byte)(v >> (8 * i)); }
        void U64(ulong v) { for (int i = 0; i < 8; i++) payload[p++] = (byte)(v >> (8 * i)); }

        U16(2);                       // format_version
        U16(16);                      // record_size
        U32(1);                       // flags：bit0 = NOMINAL 时间质量
        U32(_rate);                   // rate_hz
        U32(_uid[0]); U32(_uid[1]); U32(_uid[2]);
        U64(_recordId);
        U32(generation);              // anchor_generation
        U32(_rate);                   // anchor_rate_hz（= rate_hz，冗余校验）
        U64(_firstIndex);             // anchor_sample_seq0
        U64(0);                       // anchor_mono_us0：设备不通过 RAW 下发，如实写 0
        U16((ushort)config.Length);
        config.CopyTo(payload, p);
        p += config.Length;
        uint crc = Crc32.Compute(payload.AsSpan(0, p));
        for (int i = 0; i < 4; i++) payload[p++] = (byte)(crc >> (8 * i));
        WriteChunk(1, payload);
    }

    /// <summary>schema1 外壳 + 只含记录元数据 TLV（0xD703 校准、0xD704 启动标识）。</summary>
    private byte[] BuildConfig()
    {
        var body = new List<byte>();
        body.AddRange("DRMSUC01"u8.ToArray());
        var tlvs = new List<byte>();
        if (_calibrationValid && _scaleOhms > 0 && _referenceOhms > 0)
        {
            byte[] t = new byte[32];
            BinaryPrimitives.WriteUInt16LittleEndian(t.AsSpan(0), 0xD703);
            BinaryPrimitives.WriteUInt16LittleEndian(t.AsSpan(2), 28);
            BinaryPrimitives.WriteUInt32LittleEndian(t.AsSpan(4), _calibrationValid ? 1u : 0u);
            BinaryPrimitives.WriteUInt32LittleEndian(t.AsSpan(8), _calibrationGeneration);
            BinaryPrimitives.WriteUInt32LittleEndian(t.AsSpan(12), _rate);
            BinaryPrimitives.WriteDoubleLittleEndian(t.AsSpan(16), _scaleOhms);
            BinaryPrimitives.WriteDoubleLittleEndian(t.AsSpan(24), _referenceOhms);
            tlvs.AddRange(t);
        }
        if (_bootId != 0)
        {
            byte[] t = new byte[12];
            BinaryPrimitives.WriteUInt16LittleEndian(t.AsSpan(0), 0xD704);
            BinaryPrimitives.WriteUInt16LittleEndian(t.AsSpan(2), 8);
            BinaryPrimitives.WriteUInt64LittleEndian(t.AsSpan(4), _bootId);
            tlvs.AddRange(t);
        }
        uint total = (uint)(8 + 4 + 28 + tlvs.Count + 4);   // magic + len + 头余量 + TLV + CRC
        Span<byte> lenBytes = stackalloc byte[4];
        BinaryPrimitives.WriteUInt32LittleEndian(lenBytes, total);
        body.AddRange(lenBytes.ToArray());
        body.AddRange(new byte[28]);                         // 12..39：schema/版本等，读取器不校验
        body.AddRange(tlvs);
        uint crc = Crc32.Compute(body.ToArray());
        Span<byte> crcBytes = stackalloc byte[4];
        BinaryPrimitives.WriteUInt32LittleEndian(crcBytes, crc);
        body.AddRange(crcBytes.ToArray());
        return body.ToArray();
    }

    private void FlushChunk()
    {
        if (_pendingCount == 0 || _stream is null) return;
        int bytes = _pendingCount * 16;
        var payload = new byte[bytes + 4];
        _pending.AsSpan(0, bytes).CopyTo(payload);
        uint crc = Crc32.Compute(payload.AsSpan(0, bytes));
        BinaryPrimitives.WriteUInt32LittleEndian(payload.AsSpan(bytes), crc);
        WriteChunk(2, payload);
        _pendingCount = 0;
    }

    private void WriteChunk(ushort type, byte[] payload)
    {
        if (_stream is null) return;
        Span<byte> head = stackalloc byte[4];
        BinaryPrimitives.WriteUInt16LittleEndian(head, type);
        BinaryPrimitives.WriteUInt16LittleEndian(head[2..], (ushort)payload.Length);
        _stream.Write(head);
        _stream.Write(payload);
    }

    /// <summary>写 END 并关文件。reason 0=OK / 9=INCOMPLETE。</summary>
    private void CloseFile(uint reason, bool unknownLoss)
    {
        if (_stream is null) return;
        if (_framesThisFile == 0)
        {
            /* 没有帧就没有 HEADER（延迟到首帧写），此时写 END 会变成"END before HEADER"；
             * 直接丢弃空文件，不让读取器看到一个自相矛盾的文件。 */
            _stream.Dispose();
            _stream = null;
            File.Delete(CurrentPath!);
            return;
        }
        var payload = new byte[83 + 4];
        int p = 0;
        void U8(byte v) => payload[p++] = v;
        void U32(uint v) { for (int i = 0; i < 4; i++) payload[p++] = (byte)(v >> (8 * i)); }
        void U64(ulong v) { for (int i = 0; i < 8; i++) payload[p++] = (byte)(v >> (8 * i)); }

        U32(_generation);
        U64(_recordId);
        U64(_framesThisFile);          // ring_end：本文件帧数（log_ticket 类比）
        U64(_lostReported);            // lost_count：兼容诊断，不跨阶段相加
        U64(_framesThisFile == 0 ? 0 : _firstIndex);
        U64(_framesThisFile == 0 ? 0 : _lastIndex + 1);
        U64(_framesThisFile == 0 ? 0 : _lastIndex);
        U8(1);                         // end_known
        U64(_gaps + _lostReported);    // capture_lost
        U64(_lostReported);            // log_dropped（USB 侧未交付）
        U64(_crcBad);                  // quality_bad
        U8(unknownLoss ? (byte)1 : (byte)0);
        U8(0);                         // storage_error
        U32(_framesThisFile == 0 ? 12u : reason);
        uint crc = Crc32.Compute(payload.AsSpan(0, p));
        for (int i = 0; i < 4; i++) payload[p++] = (byte)(crc >> (8 * i));
        WriteChunk(3, payload);
        _stream.Flush();
        _stream.Dispose();
        _stream = null;
        _recordId++;
        _framesThisFile = 0;   /* 下一帧触发 OpenFile：轮转出的新文件必须有独立 HEADER */
    }
}
