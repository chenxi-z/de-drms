using Drms.Core.Protocol;
using Xunit;

namespace Drms.Core.Tests;

/// <summary>
/// RAW_EVENT（opcode 131）解析测试。
///
/// 帧布局与固件 drms_raw_stream.c 的批槽一致：20 B v2 头 + 5 个必填 TLV
/// （data 54 / sequence 62 / sample_generation 21 / sample_index 22 / rate 30 / lost 63）+ CRC。
/// 这里手工构造一个 2 帧的批，逐字段断言解析结果与帧内解码口径。
/// </summary>
public class RawEventTests
{
    /// <summary>按固件同款布局构造一批 RAW_EVENT 的原始帧（不含 COBS）。</summary>
    private static byte[] BuildRawEvent(uint session, ulong sequence, uint generation,
                                        ulong sampleIndex, uint rate, ulong lost,
                                        params (ushort Status, int Voltage, int Sense, uint Seq)[] frames)
    {
        using var ms = new MemoryStream();
        void U16(ushort v) { ms.WriteByte((byte)v); ms.WriteByte((byte)(v >> 8)); }
        void U32(uint v) { for (int i = 0; i < 4; i++) ms.WriteByte((byte)(v >> (8 * i))); }
        void U64(ulong v) { for (int i = 0; i < 8; i++) ms.WriteByte((byte)(v >> (8 * i))); }
        void Tlv(ushort tag, Action body)
        {
            long lenPos = ms.Position;
            U16((ushort)(tag | 0x8000));
            U16(0);
            long start = ms.Position;
            body();
            long end = ms.Position;
            ms.Position = lenPos + 2;
            U16((ushort)(end - start));
            ms.Position = end;
        }

        void Frame(ushort status, int voltage, int sense, uint seq)
        {
            // 12 B ADC：status u16 BE / voltage i24 BE / sense i24 BE / CRC16 BE / 尾 0
            var f = new byte[12];
            f[0] = (byte)(status >> 8); f[1] = (byte)status;
            f[3] = (byte)(voltage >> 16); f[4] = (byte)(voltage >> 8); f[5] = (byte)voltage;
            f[6] = (byte)(sense >> 16); f[7] = (byte)(sense >> 8); f[8] = (byte)sense;
            ushort crc = RawEvent.Crc16Ccitt(f.AsSpan(0, 9));
            f[9] = (byte)(crc >> 8); f[10] = (byte)crc;
            f[11] = 0;
            ms.Write(f);
            for (int i = 0; i < 4; i++) ms.WriteByte((byte)(seq >> (8 * i)));
        }

        ms.WriteByte(2); ms.WriteByte(3);
        U16(131);
        U32(session);
        U64(0);
        U16(0);   // payload_len 占位，最后回填
        U16(0);   // flags
        Tlv(54, () => { foreach (var fr in frames) Frame(fr.Status, fr.Voltage, fr.Sense, fr.Seq); });
        Tlv(62, () => U64(sequence));
        Tlv(21, () => U32(generation));
        Tlv(22, () => U64(sampleIndex));
        Tlv(30, () => U32(rate));
        Tlv(63, () => U64(lost));

        byte[] body = ms.ToArray();
        ushort payloadLen = (ushort)(body.Length - 20);
        body[16] = (byte)payloadLen; body[17] = (byte)(payloadLen >> 8);

        uint crc32 = Crc32.Compute(body);
        var withCrc = new byte[body.Length + 4];
        body.CopyTo(withCrc, 0);
        for (int i = 0; i < 4; i++) withCrc[body.Length + i] = (byte)(crc32 >> (8 * i));
        return withCrc;
    }

    [Fact]
    public void ParsesBatchHeaderAndFrames()
    {
        byte[] raw = BuildRawEvent(0xAABBCCDD, sequence: 7, generation: 2, sampleIndex: 41000,
                                   rate: 4000, lost: 60,
                                   (0x2210, 100, 4000000, 41000u),
                                   (0x2210, -200, 4000001, 41001u));
        Message msg = FrameCodec.Decode(Cobs.Encode(raw));
        Assert.Equal(Kind.Event, msg.Kind);
        Assert.Equal((ushort)131, msg.Opcode);
        Assert.Equal(0xAABBCCDDu, msg.Session);
        Assert.Equal(0UL, msg.RequestId);   // 事件不占请求号

        RawEvent ev = Messages.ParseRawEvent(msg);
        Assert.Equal(7UL, ev.Sequence);
        Assert.Equal(60UL, ev.Lost);
        Assert.Equal(2u, ev.SampleGeneration);
        Assert.Equal(41000UL, ev.SampleIndex);
        Assert.Equal(4000u, ev.Rate);
        Assert.Equal(2, ev.FrameCount);

        var frames = ev.Frames().ToList();
        Assert.Equal(41000u, frames[0].Sequence);
        Assert.Equal(100, frames[0].Voltage);
        Assert.Equal(4000000, frames[0].Sense);
        Assert.True(frames[0].CrcOk);
        Assert.Equal(41001u, frames[1].Sequence);
        Assert.Equal(-200, frames[1].Voltage);   // i24 符号扩展
        Assert.True(frames[1].CrcOk);
    }

    [Fact]
    public void CorruptedFrameFailsCrc()
    {
        byte[] raw = BuildRawEvent(1, sequence: 1, generation: 1, sampleIndex: 0,
                                   rate: 4000, lost: 0, (0x2210, 100, 4000000, 0u));
        Message msg = FrameCodec.Decode(Cobs.Encode(raw));
        RawEvent ev = Messages.ParseRawEvent(msg);
        // Data 是 data TLV 的值（16 B/帧）；改帧内第 5 字节（voltage 低位）破坏 CRC
        ev.Data[4] ^= 0xFF;
        Assert.False(ev.Frames().Single().CrcOk);
    }
}
