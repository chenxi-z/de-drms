using System.Buffers.Binary;

namespace Drms.Core.Protocol;

/// <summary>
/// 一帧 CDC v2 消息的解码结果。
///
/// 头部格式（20 字节，<BBHIQHH）：
///   major:u8=2, kind:u8, opcode:u16, session:u32, request_id:u64,
///   payload_length:u16, flags:u16=0
/// 尾部追加 u32 CRC-32（覆盖头部 + 载荷）。
/// </summary>
public sealed class Message
{
    public required byte Major { get; init; }
    public required Kind Kind { get; init; }
    public required ushort Opcode { get; init; }
    public required uint Session { get; init; }
    public required ulong RequestId { get; init; }
    public required ushort Flags { get; init; }
    public required byte[] Payload { get; init; }

    public List<TlvField> Fields { get; init; } = new();

    public Dictionary<ushort, TlvField>? _index;
    public Dictionary<ushort, TlvField> Index => _index ??= TlvReader.Index(Fields);
}

/// <summary>
/// 帧层编解码：COBS + 20 字节头 + 载荷 + CRC-32 + 0x00 分隔符。
///
/// 这一层只管"字节流对不对"，不解释任何业务字段——业务在 <see cref="Messages"/>。
/// </summary>
public static class FrameCodec
{
    /// <summary>把一条消息编码成可直接写入串口的线上字节（含尾部 0x00 分隔符）。</summary>
    public static byte[] Encode(Kind kind, ushort opcode, uint session, ulong requestId,
                                ReadOnlySpan<byte> payload, ushort flags = 0)
    {
        if (payload.Length > Frame.MaxPayload)
            throw new ProtocolException($"载荷 {payload.Length} 字节超过上限 {Frame.MaxPayload}");

        int bodyLength = Frame.HeaderLength + payload.Length + 4;
        var body = new byte[bodyLength];

        body[0] = Frame.MajorVersion;
        body[1] = (byte)kind;
        BinaryPrimitives.WriteUInt16LittleEndian(body.AsSpan(2), opcode);
        BinaryPrimitives.WriteUInt32LittleEndian(body.AsSpan(4), session);
        BinaryPrimitives.WriteUInt64LittleEndian(body.AsSpan(8), requestId);
        BinaryPrimitives.WriteUInt16LittleEndian(body.AsSpan(16), (ushort)payload.Length);
        BinaryPrimitives.WriteUInt16LittleEndian(body.AsSpan(18), flags);
        payload.CopyTo(body.AsSpan(Frame.HeaderLength));

        uint crc = Crc32.Compute(body.AsSpan(0, bodyLength - 4));
        BinaryPrimitives.WriteUInt32LittleEndian(body.AsSpan(bodyLength - 4), crc);

        byte[] encoded = Cobs.Encode(body);
        var wire = new byte[encoded.Length + 1];
        encoded.CopyTo(wire, 0);
        wire[^1] = 0x00;
        return wire;
    }

    /// <summary>
    /// 解码一条线上帧（**不含**尾部分隔符）。任何结构问题都抛 ProtocolException。
    ///
    /// 注意：调用方负责按 0x00 切分帧之后再把每段交进来。
    /// </summary>
    public static Message Decode(ReadOnlySpan<byte> encodedWithoutDelimiter)
    {
        if (!Cobs.TryDecode(encodedWithoutDelimiter, out byte[] body))
            throw new ProtocolException("COBS 解码失败");

        if (body.Length < Frame.HeaderLength + 4)
            throw new ProtocolException($"帧长 {body.Length} 不足最小长度");

        if (body[0] != Frame.MajorVersion)
            throw new ProtocolException($"主版本 {body[0]} 不是 {Frame.MajorVersion}");

        var kind = (Kind)body[1];
        if (kind is not (Kind.Request or Kind.Reply or Kind.Event))
            throw new ProtocolException($"未知 kind {body[1]}");

        ushort opcode = BinaryPrimitives.ReadUInt16LittleEndian(body.AsSpan(2));
        uint session = BinaryPrimitives.ReadUInt32LittleEndian(body.AsSpan(4));
        ulong requestId = BinaryPrimitives.ReadUInt64LittleEndian(body.AsSpan(8));
        ushort payloadLength = BinaryPrimitives.ReadUInt16LittleEndian(body.AsSpan(16));
        ushort flags = BinaryPrimitives.ReadUInt16LittleEndian(body.AsSpan(18));

        if (body.Length != Frame.HeaderLength + payloadLength + 4)
            throw new ProtocolException(
                $"载荷长度字段 {payloadLength} 与实际帧长 {body.Length} 不符");

        if (payloadLength > Frame.MaxPayload)
            throw new ProtocolException($"载荷 {payloadLength} 超过上限");

        if (flags != 0)
            throw new ProtocolException($"flags 必须为 0，实际 {flags}");

        uint expected = BinaryPrimitives.ReadUInt32LittleEndian(body.AsSpan(body.Length - 4));
        uint actual = Crc32.Compute(body.AsSpan(0, body.Length - 4));
        if (expected != actual)
            throw new ProtocolException($"CRC 不符：线上 {expected:X8}，本地 {actual:X8}");

        byte[] payload = body.AsSpan(Frame.HeaderLength, payloadLength).ToArray();
        var message = new Message
        {
            Major = body[0],
            Kind = kind,
            Opcode = opcode,
            Session = session,
            RequestId = requestId,
            Flags = flags,
            Payload = payload,
        };
        message.Fields.AddRange(TlvReader.Parse(payload));
        return message;
    }
}

/// <summary>
/// 串口字节流的分帧器：按 0x00 切分，处理拆包/粘包。
///
/// 协议规定"连续零忽略"、"堆积超界或半帧从首字节起满 1000 ms 仍无分隔符则丢至下一个零"。
/// 这里实现同样的语义，避免脏数据永久卡住接收。
/// </summary>
public sealed class FrameSplitter
{
    private readonly List<byte> _buffer = new();
    private readonly TimeSpan _resyncTimeout;
    private DateTime _firstByteAt = DateTime.MinValue;

    public FrameSplitter(TimeSpan? resyncTimeout = null)
        => _resyncTimeout = resyncTimeout ?? TimeSpan.FromMilliseconds(1000);

    /// <summary>喂入新收到的字节，返回本次能切出的完整帧（不含分隔符）。</summary>
    public List<byte[]> Feed(ReadOnlySpan<byte> data)
    {
        var frames = new List<byte[]>();
        foreach (byte b in data)
        {
            if (b == 0x00)
            {
                if (_buffer.Count > 0)
                {
                    frames.Add(_buffer.ToArray());
                    _buffer.Clear();
                }
                // 连续零：忽略（buffer 已空，无需处理）
                _firstByteAt = DateTime.MinValue;
                continue;
            }

            if (_buffer.Count == 0)
                _firstByteAt = DateTime.UtcNow;

            _buffer.Add(b);

            // 超界：丢弃当前半帧，等下一个分隔符重新同步
            if (_buffer.Count > Frame.MaxWireLength)
            {
                _buffer.Clear();
                _firstByteAt = DateTime.MinValue;
            }
        }
        return frames;
    }

    /// <summary>
    /// 定期调用以丢弃卡住的半帧。返回 true 表示发生过丢弃。
    /// </summary>
    public bool CheckStale()
    {
        if (_buffer.Count > 0 && _firstByteAt != DateTime.MinValue &&
            DateTime.UtcNow - _firstByteAt > _resyncTimeout)
        {
            _buffer.Clear();
            _firstByteAt = DateTime.MinValue;
            return true;
        }
        return false;
    }
}
