using Drms.Core.Protocol;
using Xunit;

namespace Drms.Core.Tests;

/// <summary>
/// 用机器定义里的四条线上向量验收帧层。
///
/// 这四条向量是协议方固化下来的权威对照——它们是"我们的编解码和固件一致"
/// 的唯一硬证据，比任何自造用例都可信。逐字节对齐，不做任何宽松比较。
/// 向量数据在 Vectors.g.cs，由脚本从 shared/protocol/de-drms-cdc-v2.json 生成。
/// </summary>
public class ProtocolVectorTests
{
    private static byte[] FromHex(string hex) => Convert.FromHexString(hex);

    [Fact]
    public void Crc32_MatchesTheDocumentedCheckValue()
    {
        // 协议正文：CRC-32/ISO-HDLC，"123456789" 校验值 0xCBF43926
        Assert.Equal(Crc32.CheckValue123456789, Crc32.Compute("123456789"u8));
    }

    [Theory]
    [InlineData(Vectors.HELLO_DECODED, Vectors.HELLO_WIRE)]
    [InlineData(Vectors.READ_OPERATION_DECODED, Vectors.READ_OPERATION_WIRE)]
    [InlineData(Vectors.EXTENSION_254_DECODED, Vectors.EXTENSION_254_WIRE)]
    [InlineData(Vectors.MAXIMUM_PAYLOAD_DECODED, Vectors.MAXIMUM_PAYLOAD_WIRE)]
    public void Vectors_RoundTripThroughCobsAndFrame(string decodedHex, string wireHex)
    {
        byte[] expectedFrame = FromHex(decodedHex);
        byte[] expectedWire = FromHex(wireHex);

        // 1) COBS 编出来的线上字节必须与权威逐字节相同（含尾部 0x00）
        byte[] withDelimiter = [.. Cobs.Encode(expectedFrame), 0x00];
        Assert.Equal(expectedWire, withDelimiter);

        // 2) 解码线上字节必须还原出原始帧
        Assert.True(Cobs.TryDecode(expectedWire.AsSpan(0, expectedWire.Length - 1), out byte[] roundTrip));
        Assert.Equal(expectedFrame, roundTrip);

        // 3) 走完整帧解析：主版本、CRC、载荷长度、TLV 全部要过
        Message message = FrameCodec.Decode(expectedWire.AsSpan(0, expectedWire.Length - 1));
        Assert.Equal(Frame.MajorVersion, message.Major);
        Assert.Equal(0, message.Flags);
    }

    [Fact]
    public void HelloVector_HasExpectedHeader()
    {
        byte[] wire = FromHex(Vectors.HELLO_WIRE);
        Message m = FrameCodec.Decode(wire.AsSpan(0, wire.Length - 1));

        Assert.Equal(Kind.Request, m.Kind);
        Assert.Equal(1, m.Opcode);       // HELLO
        Assert.Equal(0u, m.Session);     // 握手前 session = 0
        Assert.Equal(1ul, m.RequestId);  // 初始 HELLO 固定 request_id = 1
        Assert.Empty(m.Payload);
    }

    [Fact]
    public void ReadOperationVector_ParsesOperationField()
    {
        byte[] wire = FromHex(Vectors.READ_OPERATION_WIRE);
        Message m = FrameCodec.Decode(wire.AsSpan(0, wire.Length - 1));

        Assert.Equal(Kind.Request, m.Kind);
        Assert.Equal(3, m.Opcode);       // GET_OPERATION
        Assert.Equal(1u, m.Session);
        Assert.Equal(2ul, m.RequestId);  // 会话内首个普通请求从 2 起

        TlvField op = m.Index.Require(Tag.Operation, "operation");
        Assert.Equal(1ul, op.AsU64());
        Assert.True(op.IsRequired);
    }

    [Fact]
    public void Extension254Vector_CarriesUnknownOptionalField()
    {
        byte[] wire = FromHex(Vectors.EXTENSION_254_WIRE);
        Message m = FrameCodec.Decode(wire.AsSpan(0, wire.Length - 1));

        // 这条向量专门覆盖两件事：COBS 的 254 字节段边界，以及
        // "未知可选字段按长度跳过"——它用 tag 0x1000（高位置 0 = 可选）
        // 携带 254 字节 0xAB。解析器不得因此报错，也不得当成已知字段。
        Assert.Equal(2, m.Opcode); // GET_STATUS
        TlvField unknown = Assert.Single(m.Fields);
        Assert.Equal(0x1000, unknown.Id);
        Assert.False(unknown.IsRequired);
        Assert.Equal(254, unknown.Value.Length);
        Assert.All(unknown.Value, b => Assert.Equal(0xAB, b));
    }

    [Fact]
    public void MaximumPayloadVector_IsExactlyAtLimit()
    {
        byte[] wire = FromHex(Vectors.MAXIMUM_PAYLOAD_WIRE);
        Assert.Equal(Frame.MaxWireLength, wire.Length);  // 线上缓冲上限 1054

        Message m = FrameCodec.Decode(wire.AsSpan(0, wire.Length - 1));
        Assert.Equal(Frame.MaxPayload, m.Payload.Length);
    }

    [Fact]
    public void FrameSplitter_HandlesSplitAndCoalescedFrames()
    {
        byte[] wire = FromHex(Vectors.HELLO_WIRE);
        var splitter = new FrameSplitter();

        // 拆包：逐字节喂入，只在最后一个字节上产出帧
        var produced = new List<byte[]>();
        for (int i = 0; i < wire.Length; i++)
        {
            List<byte[]> chunk = splitter.Feed(wire.AsSpan(i, 1));
            if (i < wire.Length - 1)
                Assert.Empty(chunk);
            produced.AddRange(chunk);
        }
        Assert.Single(produced);
        Assert.Equal(wire.AsSpan(0, wire.Length - 1).ToArray(), produced[0]);

        // 粘包：三帧一次性喂入应切出三帧
        List<byte[]> coalesced = splitter.Feed([.. wire, .. wire, .. wire]);
        Assert.Equal(3, coalesced.Count);
        Assert.Equal(produced[0], coalesced[0]);
    }

    [Fact]
    public void FrameSplitter_IgnoresConsecutiveZeroes()
    {
        byte[] wire = FromHex(Vectors.HELLO_WIRE);
        List<byte[]> frames = new FrameSplitter().Feed([0x00, 0x00, .. wire, 0x00, 0x00]);
        Assert.Single(frames);
    }

    [Fact]
    public void Decode_RejectsCorruptedCrc()
    {
        byte[] wire = FromHex(Vectors.READ_OPERATION_WIRE);
        wire[^2] ^= 0xFF; // 翻转 CRC 的一个字节
        Assert.Throws<ProtocolException>(() => FrameCodec.Decode(wire.AsSpan(0, wire.Length - 1)));
    }

    [Fact]
    public void Decode_RejectsWrongMajorVersion()
    {
        byte[] frame = FromHex(Vectors.HELLO_DECODED);
        frame[0] = 3;
        uint crc = Crc32.Compute(frame.AsSpan(0, frame.Length - 4));
        System.Buffers.Binary.BinaryPrimitives.WriteUInt32LittleEndian(frame.AsSpan(frame.Length - 4), crc);
        byte[] encoded = [.. Cobs.Encode(frame), 0x00];
        Assert.Throws<ProtocolException>(() => FrameCodec.Decode(encoded.AsSpan(0, encoded.Length - 1)));
    }

    [Fact]
    public void Decode_RejectsTruncatedFrame()
    {
        byte[] wire = FromHex(Vectors.READ_OPERATION_WIRE);
        // 去掉最后一个字节（分隔符前的 CRC 尾）
        Assert.Throws<ProtocolException>(() => FrameCodec.Decode(wire.AsSpan(1, wire.Length - 3)));
    }

    [Fact]
    public void Encode_ProducesFrameThatDecodesBack()
    {
        // 自造一条 HELLO 请求，确认编码→解码闭环
        byte[] payload = new TlvWriter().ToArray();
        byte[] wire = FrameCodec.Encode(Kind.Request, 1, 0, 1, payload);
        Message m = FrameCodec.Decode(wire.AsSpan(0, wire.Length - 1));

        Assert.Equal(Kind.Request, m.Kind);
        Assert.Equal(1, m.Opcode);
        Assert.Equal(1ul, m.RequestId);
        Assert.Empty(m.Fields);
    }
}
