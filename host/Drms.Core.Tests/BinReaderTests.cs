using Drms.Core.BinFile;
using Drms.Core.Protocol;
using Drms.Core.Record;
using Xunit;

namespace Drms.Core.Tests;

/// <summary>
/// BIN v2 读取器：与写入端往返一致，且 CRC/边界校验按规格生效。
/// 端到端合规性另由 tools/de_drms_log.py 在真实文件上核对（见 README/基准记录）。
/// </summary>
public class BinReaderTests : IDisposable
{
    private readonly string _dir = Path.Combine(Path.GetTempPath(), "drms_read_" + Guid.NewGuid().ToString("N"));

    public void Dispose()
    {
        try { Directory.Delete(_dir, recursive: true); } catch { }
    }

    private static byte[] Frame(uint sequence, int voltage, int sense)
    {
        var f = new byte[16];
        f[0] = 0x22; f[1] = 0x10; f[2] = 0x00;
        f[3] = (byte)(voltage >> 16); f[4] = (byte)(voltage >> 8); f[5] = (byte)voltage;
        f[6] = (byte)(sense >> 16); f[7] = (byte)(sense >> 8); f[8] = (byte)sense;
        ushort crc = RawEvent.Crc16Ccitt(f.AsSpan(0, 9));
        f[9] = (byte)(crc >> 8); f[10] = (byte)crc;
        System.Buffers.Binary.BinaryPrimitives.WriteUInt32LittleEndian(f.AsSpan(12), sequence);
        return f;
    }

    private string WriteFile(int count = 100)
    {
        var recorder = new BinRecorder(_dir, "T", [1, 2, 3], rate: 4000, generation: 2, recordId: 9,
                                       calibrationValid: true, calibrationGeneration: 3,
                                       scaleOhms: 150000, referenceOhms: 100000, bootId: 42);
        var frames = new List<byte>();
        for (uint i = 0; i < count; i++) frames.AddRange(Frame(500 + i, 400000, 4034000));
        recorder.Append(frames.ToArray(), lostTotal: 0);
        recorder.Finish();
        recorder.Dispose();
        return Path.Combine(_dir, "T0001.BIN");
    }

    [Fact]
    public void RoundTripsWithHeaderCalibrationAndFrames()
    {
        BinReader.Result r = BinReader.Read(File.ReadAllBytes(WriteFile()));
        Assert.True(r.Complete, $"读取失败：{r.Error}");
        Assert.Equal(1, r.DataChunks);
        Assert.Equal(100, r.Frames.Count);
        Assert.Equal(4000u, r.Header!.RateHz);
        Assert.Equal(2u, r.Header.Generation);
        Assert.Equal(500UL, r.Header.SampleSeq0);
        Assert.Equal(150000.0, r.Header.ScaleOhms);
        Assert.Equal(100000.0, r.Header.ReferenceOhms);
        Assert.Equal(500u, r.Frames[0].Sequence);
        Assert.True(BinReader.Result.IsValid(r.Frames[0]));
        Assert.Equal(150000.0 * 400000 / 4034000.0, r.Ohms(r.Frames[0])!.Value, 6);
        Assert.Equal(0u, r.End!.Reason);
    }

    [Fact]
    public void TruncatedFileIsIncompleteNotValid()
    {
        byte[] whole = File.ReadAllBytes(WriteFile(20));
        for (int cut = 1; cut < whole.Length; cut += 37)
        {
            var r = BinReader.Read(whole.AsSpan(0, cut).ToArray());
            Assert.False(r.Complete, $"截断到 {cut} B 仍被判完整");
            Assert.False(string.IsNullOrEmpty(r.Error));
        }
    }

    [Fact]
    public void FrameCrcCorruptionIsDetected()
    {
        byte[] file = File.ReadAllBytes(WriteFile(5));
        // 找 DATA 块里的第一个帧，改第 5 字节（voltage 低位）而不改块 CRC → 块 CRC 会先报错
        int dataChunk = IndexOfChunk(file, 2);
        file[dataChunk + 4 + 5] ^= 0xFF;
        var r = BinReader.Read(file);
        Assert.False(r.Complete);
        Assert.Equal("块 CRC 不匹配", r.Error);
    }

    [Fact]
    public void BlockCrcKeepsFrameLevelChecksMeaningful()
    {
        // 重算块 CRC 后，帧级 CRC 应把被改的帧标为无效
        byte[] file = File.ReadAllBytes(WriteFile(5));
        int dataChunk = IndexOfChunk(file, 2);
        ushort len = System.Buffers.Binary.BinaryPrimitives.ReadUInt16LittleEndian(file.AsSpan(dataChunk + 2));
        file[dataChunk + 4 + 5] ^= 0xFF;
        uint crc = Crc32.Compute(file.AsSpan(dataChunk + 4, len - 4));
        System.Buffers.Binary.BinaryPrimitives.WriteUInt32LittleEndian(file.AsSpan(dataChunk + 4 + len - 4), (uint)crc);

        var r = BinReader.Read(file);
        Assert.True(r.Complete, r.Error);
        Assert.False(r.Frames[0].CrcOk);
        Assert.False(BinReader.Result.IsValid(r.Frames[0]));
        Assert.Null(r.Ohms(r.Frames[0]));          // 无效帧不得换算电阻
        Assert.True(BinReader.Result.IsValid(r.Frames[1]));
    }

    private static int IndexOfChunk(byte[] file, ushort type)
    {
        int p = 0;
        while (p + 4 <= file.Length)
        {
            ushort t = System.Buffers.Binary.BinaryPrimitives.ReadUInt16LittleEndian(file.AsSpan(p));
            ushort len = System.Buffers.Binary.BinaryPrimitives.ReadUInt16LittleEndian(file.AsSpan(p + 2));
            if (t == type) return p;
            p += 4 + len;
        }
        throw new InvalidOperationException("找不到指定块");
    }
}
