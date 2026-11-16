using System.Buffers.Binary;
using Drms.Core.Protocol;
using Drms.Core.Record;
using Xunit;

namespace Drms.Core.Tests;

/// <summary>
/// PC 侧 BIN v2 记录器：格式自查 + 轮转 + 缺口记账。
///
/// 字节口径以 docs/design/2026-11-06-record-v2-format.md 为准；本测试自带的
/// 极简读取器只覆盖本记录器会写出的三种块，完整合规性由
/// tools/de_drms_log.py 在真机文件上做端到端校验。
/// </summary>
public class BinRecorderTests : IDisposable
{
    private readonly string _dir = Path.Combine(Path.GetTempPath(), "drms_rec_" + Guid.NewGuid().ToString("N"));

    public void Dispose()
    {
        try { Directory.Delete(_dir, recursive: true); } catch { /* Windows 句柄延迟释放 */ }
    }

    /// <summary>构 16 B 原始帧：12 B ADC（含正确 CRC）+ u32 序号。</summary>
    private static byte[] Frame(uint sequence, int voltage = 400000, int sense = 4000000)
    {
        var f = new byte[16];
        f[0] = 0x22; f[1] = 0x10; f[2] = 0x00;
        f[3] = (byte)(voltage >> 16); f[4] = (byte)(voltage >> 8); f[5] = (byte)voltage;
        f[6] = (byte)(sense >> 16); f[7] = (byte)(sense >> 8); f[8] = (byte)sense;
        ushort crc = RawEvent.Crc16Ccitt(f.AsSpan(0, 9));
        f[9] = (byte)(crc >> 8); f[10] = (byte)crc;
        f[11] = 0;
        BinaryPrimitives.WriteUInt32LittleEndian(f.AsSpan(12), sequence);
        return f;
    }

    private static List<(ushort Type, byte[] Body)> ReadChunks(byte[] file)
    {
        var chunks = new List<(ushort, byte[])>();
        int p = 0;
        while (p + 4 <= file.Length)
        {
            ushort type = BinaryPrimitives.ReadUInt16LittleEndian(file.AsSpan(p));
            ushort len = BinaryPrimitives.ReadUInt16LittleEndian(file.AsSpan(p + 2));
            var payload = file.AsSpan(p + 4, len).ToArray();
            uint crc = BinaryPrimitives.ReadUInt32LittleEndian(payload.AsSpan(len - 4));
            Assert.Equal(Crc32.Compute(payload.AsSpan(0, len - 4)), crc);
            chunks.Add((type, payload[..(len - 4)]));
            p += 4 + len;
        }
        return chunks;
    }

    [Fact]
    public void WritesValidHeaderDataAndEnd()
    {
        var recorder = new BinRecorder(_dir, "PC", [1, 2, 3], rate: 4000, generation: 7, recordId: 5,
                                       calibrationValid: true, calibrationGeneration: 2,
                                       scaleOhms: 150005.5, referenceOhms: 100000, bootId: 0xDEADBEEF);
        var frames = new List<byte>();
        for (uint i = 0; i < 10; i++) frames.AddRange(Frame(1000 + i));
        recorder.Append(frames.ToArray(), lostTotal: 0);
        recorder.Finish();
        recorder.Dispose();

        var chunks = ReadChunks(File.ReadAllBytes(Path.Combine(_dir, "PC0001.BIN")));
        Assert.Equal([(ushort)1, 2, 3], chunks.Select(c => c.Type));

        byte[] header = chunks[0].Body;
        Assert.Equal(2, BinaryPrimitives.ReadUInt16LittleEndian(header));
        Assert.Equal(16, BinaryPrimitives.ReadUInt16LittleEndian(header.AsSpan(2)));
        Assert.Equal(1u, BinaryPrimitives.ReadUInt32LittleEndian(header.AsSpan(4)));   // NOMINAL
        Assert.Equal(4000u, BinaryPrimitives.ReadUInt32LittleEndian(header.AsSpan(8)));
        Assert.Equal(5UL, BinaryPrimitives.ReadUInt64LittleEndian(header.AsSpan(24))); // record_id
        Assert.Equal(7u, BinaryPrimitives.ReadUInt32LittleEndian(header.AsSpan(32)));  // generation
        Assert.Equal(1000UL, BinaryPrimitives.ReadUInt64LittleEndian(header.AsSpan(40))); // seq0
        ushort configLen = BinaryPrimitives.ReadUInt16LittleEndian(header.AsSpan(56));
        byte[] config = header.AsSpan(58, configLen).ToArray();
        Assert.Equal("DRMSUC01"u8.ToArray(), config[..8]);
        Assert.Equal((uint)config.Length, BinaryPrimitives.ReadUInt32LittleEndian(config.AsSpan(8)));
        // 0xD703 校准 TLV 在偏移 40
        Assert.Equal(0xD703, BinaryPrimitives.ReadUInt16LittleEndian(config.AsSpan(40)));
        Assert.Equal(150005.5, BinaryPrimitives.ReadDoubleLittleEndian(config.AsSpan(56)));

        byte[] data = chunks[1].Body;
        Assert.Equal(10 * 16, data.Length);
        Assert.Equal(1000u, BinaryPrimitives.ReadUInt32LittleEndian(data.AsSpan(12)));
        Assert.Equal(1009u, BinaryPrimitives.ReadUInt32LittleEndian(data.AsSpan(9 * 16 + 12)));

        byte[] end = chunks[2].Body;
        Assert.Equal(83, end.Length);
        Assert.Equal(7u, BinaryPrimitives.ReadUInt32LittleEndian(end));               // generation
        Assert.Equal(1000UL, BinaryPrimitives.ReadUInt64LittleEndian(end.AsSpan(28))); // first
        Assert.Equal(1010UL, BinaryPrimitives.ReadUInt64LittleEndian(end.AsSpan(36))); // end_exclusive
        Assert.Equal(1, end[52]);                                                      // end_known
        Assert.Equal(0u, BinaryPrimitives.ReadUInt32LittleEndian(end.AsSpan(79)));     // reason OK
    }

    [Fact]
    public void RotationProducesIndependentCompleteFiles()
    {
        var recorder = new BinRecorder(_dir, "PC", [1, 2, 3], rate: 4000, generation: 1, recordId: 1,
                                       rotateBytes: 4096);
        var frames = new List<byte>();
        for (uint i = 0; i < 600; i++) frames.AddRange(Frame(100 + i));   // 9600 B → 至少两个文件
        recorder.Append(frames.ToArray(), lostTotal: 0);
        recorder.Finish();
        recorder.Dispose();

        var files = Directory.GetFiles(_dir).OrderBy(f => f).ToArray();
        Assert.True(files.Length >= 2, $"轮转未发生：{files.Length} 个文件");
        ulong previousEnd = 0;
        ulong total = 0;
        foreach (string file in files)
        {
            var chunks = ReadChunks(File.ReadAllBytes(file));
            Assert.Equal((ushort)1, chunks[0].Type);                       // 每个文件都有自己的 HEADER
            Assert.Equal((ushort)3, chunks[^1].Type);                      // 与 END
            byte[] end = chunks[^1].Body;
            ulong first = BinaryPrimitives.ReadUInt64LittleEndian(end.AsSpan(28));
            ulong endExclusive = BinaryPrimitives.ReadUInt64LittleEndian(end.AsSpan(36));
            Assert.Equal(0u, BinaryPrimitives.ReadUInt32LittleEndian(end.AsSpan(79)));  // reason OK
            if (previousEnd != 0) Assert.Equal(previousEnd, first);         // 跨文件序号连续
            previousEnd = endExclusive;
            total += endExclusive - first;
        }
        Assert.Equal(600UL, total);
    }

    [Fact]
    public void SequenceGapAndLostMarkIncomplete()
    {
        var recorder = new BinRecorder(_dir, "PC", [1, 2, 3], rate: 4000, generation: 1, recordId: 1);
        var frames = new List<byte>();
        frames.AddRange(Frame(100));
        frames.AddRange(Frame(101));
        frames.AddRange(Frame(105));        // 缺 102..104：缺口 3
        recorder.Append(frames.ToArray(), lostTotal: 60);   // 设备上报 lost 60
        recorder.Finish();
        recorder.Dispose();

        var chunks = ReadChunks(File.ReadAllBytes(Path.Combine(_dir, "PC0001.BIN")));
        byte[] end = chunks[^1].Body;
        Assert.Equal(63UL, BinaryPrimitives.ReadUInt64LittleEndian(end.AsSpan(53)));  // capture_lost
        Assert.Equal(60UL, BinaryPrimitives.ReadUInt64LittleEndian(end.AsSpan(61)));  // log_dropped
        Assert.Equal(1, end[77]);                                                      // unknown_loss
        Assert.Equal(9u, BinaryPrimitives.ReadUInt32LittleEndian(end.AsSpan(79)));     // INCOMPLETE
    }
}
