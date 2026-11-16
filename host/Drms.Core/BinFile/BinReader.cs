using System.Buffers.Binary;
using Drms.Core.Protocol;

namespace Drms.Core.BinFile;

/// <summary>
/// BIN v2 记录文件读取器（规格：docs/design/2026-11-06-record-v2-format.md）。
///
/// 与 tools/de_drms_log.py 的 LogReaderV2 **同口径**：
///   · 块 CRC32（zlib 参数）、DATA 长度必须是 16 的倍数；
///   · HEADER 版本/长度/锚点校验，END 与 HEADER 的 record_id/generation 必须一致；
///   · END 之后不得再有字节；缺 END 判"不完整"。
/// 帧有效性判定（crc_ok / format_ok / 激励门限）也与解码器一致，
/// 否则离线基准的均值会与现有工具对不上。
/// </summary>
public static class BinReader
{
    public const ushort ChunkHeader = 1;
    public const ushort ChunkData = 2;
    public const ushort ChunkEnd = 3;

    public sealed record Header(
        int FormatVersion, int RecordSize, uint Flags, uint RateHz,
        uint[] Uid, ulong RecordId, uint Generation, uint AnchorRateHz,
        ulong SampleSeq0, ulong MonoUs0, double? ScaleOhms, double? ReferenceOhms);

    public sealed record End(
        uint Generation, ulong RecordId, ulong RingEnd, ulong LostCount,
        ulong FirstIndex, ulong EndExclusiveIndex, ulong LastConfirmedIndex,
        bool EndKnown, ulong CaptureLost, ulong LogDropped, ulong QualityBad,
        bool UnknownLoss, bool StorageError, uint Reason);

    public sealed record Frame(uint Sequence, int Voltage, int Sense, bool CrcOk, bool FormatOk, bool AdcFault);

    public sealed class Result
    {
        public Header? Header { get; init; }
        public End? End { get; init; }
        public required List<Frame> Frames { get; init; }
        /// <summary>null = 文件完整；否则为不完整/非法原因（与 Python 解码器同类表述）。</summary>
        public string? Error { get; init; }
        public bool Complete => Error is null && End is not null;
        public int DataChunks { get; init; }

        /// <summary>帧是否有效（判定逻辑见 <see cref="RawFrame"/>，与解码器同口径）。</summary>
        public static bool IsValid(in Frame f) => ToRawFrame(f).IsValid;

        /// <summary>按校准系数换算电阻；无校准或无有效帧返回 null。</summary>
        public double? Ohms(in Frame f) => ToRawFrame(f).Ohms(Header?.ScaleOhms);

        private static RawFrame ToRawFrame(in Frame f)
            => new(f.Sequence, f.Voltage, f.Sense, 0, f.CrcOk, f.FormatOk, f.AdcFault);
    }

    /// <summary>读取整个文件（帧全部载入内存；30 s @4 kSPS 约 120k 帧 × 40 B ≈ 5 MB）。</summary>
    public static Result Read(byte[] file)
    {
        var frames = new List<Frame>();
        Header? header = null;
        End? end = null;
        string? error = null;
        int dataChunks = 0;
        int p = 0;

        while (p + 4 <= file.Length)
        {
            ushort type = BinaryPrimitives.ReadUInt16LittleEndian(file.AsSpan(p));
            ushort len = BinaryPrimitives.ReadUInt16LittleEndian(file.AsSpan(p + 2));
            if (p + 4 + len > file.Length) { error = "块载荷被截断"; break; }
            ReadOnlySpan<byte> payload = file.AsSpan(p + 4, len);
            uint crc = BinaryPrimitives.ReadUInt32LittleEndian(payload[^4..]);
            if (Crc32.Compute(payload[..^4]) != crc) { error = "块 CRC 不匹配"; break; }
            ReadOnlySpan<byte> body = payload[..^4];

            if (end is not null) { error = "END 之后仍有字节"; break; }

            if (type == ChunkHeader)
            {
                if (header is not null) { error = "重复 HEADER"; break; }
                header = ParseHeader(body);
                if (header is null) { error = "HEADER 非法"; break; }
            }
            else if (type == ChunkData)
            {
                if (header is null || body.Length == 0 || body.Length % 16 != 0) { error = "DATA 块非法"; break; }
                dataChunks++;
                for (int o = 0; o + 16 <= body.Length; o += 16)
                    frames.Add(ParseFrame(body.Slice(o, 16)));
            }
            else if (type == ChunkEnd)
            {
                if (header is null) { error = "END 出现在 HEADER 之前"; break; }
                end = ParseEnd(body);
                if (end is null) { error = "END 非法"; break; }
                if (end.RecordId != header.RecordId || end.Generation != header.Generation)
                { error = "HEADER/END 身份不一致"; break; }
            }
            else { error = $"未知块类型 {type}"; break; }

            p += 4 + len;
        }

        if (error is null && p < file.Length) error = "尾部残留字节";
        if (error is null && end is null) error = "缺少 END";

        return new Result { Header = header, End = end, Frames = frames, Error = error, DataChunks = dataChunks };
    }

    private static Header? ParseHeader(ReadOnlySpan<byte> body)
    {
        if (body.Length < 58) return null;
        int version = BinaryPrimitives.ReadUInt16LittleEndian(body);
        int recordSize = BinaryPrimitives.ReadUInt16LittleEndian(body[2..]);
        uint flags = BinaryPrimitives.ReadUInt32LittleEndian(body[4..]);
        uint rate = BinaryPrimitives.ReadUInt32LittleEndian(body[8..]);
        var uid = new uint[3];
        for (int i = 0; i < 3; i++) uid[i] = BinaryPrimitives.ReadUInt32LittleEndian(body[(12 + 4 * i)..]);
        ulong recordId = BinaryPrimitives.ReadUInt64LittleEndian(body[24..]);
        uint generation = BinaryPrimitives.ReadUInt32LittleEndian(body[32..]);
        uint anchorRate = BinaryPrimitives.ReadUInt32LittleEndian(body[36..]);
        ulong seq0 = BinaryPrimitives.ReadUInt64LittleEndian(body[40..]);
        ulong mono0 = BinaryPrimitives.ReadUInt64LittleEndian(body[48..]);
        ushort configLen = BinaryPrimitives.ReadUInt16LittleEndian(body[56..]);
        if (version != 2 || recordSize != 16 || rate == 0 || anchorRate != rate) return null;
        if (configLen != body.Length - 58) return null;

        double? scale = null, reference = null;
        ReadOnlySpan<byte> config = body[58..];
        if (configLen > 0 && config.Length >= 44 && config[..8].SequenceEqual("DRMSUC01"u8))
        {
            int offset = 40;
            while (offset + 4 <= config.Length - 4)
            {
                ushort kind = BinaryPrimitives.ReadUInt16LittleEndian(config[offset..]);
                ushort size = BinaryPrimitives.ReadUInt16LittleEndian(config[(offset + 2)..]);
                offset += 4;
                if (offset + size > config.Length - 4) return null;
                if (kind == 0xD703 && size == 28)
                {
                    double s = BinaryPrimitives.ReadDoubleLittleEndian(config[(offset + 12)..]);
                    double r = BinaryPrimitives.ReadDoubleLittleEndian(config[(offset + 20)..]);
                    if (double.IsFinite(s) && s > 0 && double.IsFinite(r) && r > 0)
                    { scale = s; reference = r; }
                }
                offset += size;
            }
        }

        return new Header(version, recordSize, flags, rate, uid, recordId, generation, anchorRate,
                          seq0, mono0, scale, reference);
    }

    private static Frame ParseFrame(ReadOnlySpan<byte> f)
    {
        RawFrame r = RawFrame.Decode(f);
        return new Frame(r.Sequence, r.Voltage, r.Sense, r.CrcOk, r.FormatOk, r.AdcFault);
    }

    private static End? ParseEnd(ReadOnlySpan<byte> body)
    {
        if (body.Length != 83) return null;
        uint generation = BinaryPrimitives.ReadUInt32LittleEndian(body);
        ulong recordId = BinaryPrimitives.ReadUInt64LittleEndian(body[4..]);
        ulong ringEnd = BinaryPrimitives.ReadUInt64LittleEndian(body[12..]);
        ulong lost = BinaryPrimitives.ReadUInt64LittleEndian(body[20..]);
        ulong first = BinaryPrimitives.ReadUInt64LittleEndian(body[28..]);
        ulong endExclusive = BinaryPrimitives.ReadUInt64LittleEndian(body[36..]);
        ulong lastConfirmed = BinaryPrimitives.ReadUInt64LittleEndian(body[44..]);
        bool endKnown = body[52] != 0;
        ulong captureLost = BinaryPrimitives.ReadUInt64LittleEndian(body[53..]);
        ulong logDropped = BinaryPrimitives.ReadUInt64LittleEndian(body[61..]);
        ulong qualityBad = BinaryPrimitives.ReadUInt64LittleEndian(body[69..]);
        bool unknownLoss = body[77] != 0;
        bool storageError = body[78] != 0;
        uint reason = BinaryPrimitives.ReadUInt32LittleEndian(body[79..]);
        if (!endKnown && endExclusive != 0) return null;   // 未知末边界不得带伪精确值
        return new End(generation, recordId, ringEnd, lost, first, endExclusive, lastConfirmed,
                       endKnown, captureLost, logDropped, qualityBad, unknownLoss, storageError, reason);
    }
}
