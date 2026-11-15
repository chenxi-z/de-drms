using System.Buffers.Binary;
using System.Text;

namespace Drms.Core.Protocol;

/// <summary>
/// 一个 TLV 字段值。协议规定所有定宽数为小端、无填充。
/// 这里保留原始字节，按需解码——既避免提前误判类型，也让"未知可选字段
/// 按长度跳过"这条规则自然成立。
/// </summary>
public sealed class TlvField(ushort tag, byte[] value)
{
    /// <summary>线上 tag（可能带必填位 0x8000）。</summary>
    public ushort RawTag { get; } = tag;

    /// <summary>去掉必填位的字段号。</summary>
    public ushort Id => Frame.FieldId(RawTag);

    public bool IsRequired => (RawTag & Frame.RequiredTagMask) != 0;

    public byte[] Value { get; } = value;

    public byte AsByte() => Value.Length == 1 ? Value[0] : throw new ProtocolException($"tag {Id}: 期望 u8");
    public bool AsBool() => Value.Length == 1 && Value[0] switch
    {
        0 => false,
        1 => true,
        _ => throw new ProtocolException($"tag {Id}: bool 只接受 0/1"),
    };

    public ushort AsU16() => Value.Length == 2
        ? BinaryPrimitives.ReadUInt16LittleEndian(Value)
        : throw new ProtocolException($"tag {Id}: 期望 u16");

    public uint AsU32() => Value.Length == 4
        ? BinaryPrimitives.ReadUInt32LittleEndian(Value)
        : throw new ProtocolException($"tag {Id}: 期望 u32");

    public ulong AsU64() => Value.Length == 8
        ? BinaryPrimitives.ReadUInt64LittleEndian(Value)
        : throw new ProtocolException($"tag {Id}: 期望 u64");

    public double AsDouble() => Value.Length == 8
        ? BinaryPrimitives.ReadDoubleLittleEndian(Value)
        : throw new ProtocolException($"tag {Id}: 期望 f64");

    /// <summary>u16list：无填充元素串。</summary>
    public ushort[] AsU16List()
    {
        if (Value.Length % 2 != 0)
            throw new ProtocolException($"tag {Id}: u16list 长度非偶数");
        var result = new ushort[Value.Length / 2];
        for (int i = 0; i < result.Length; i++)
            result[i] = BinaryPrimitives.ReadUInt16LittleEndian(Value.AsSpan(i * 2));
        return result;
    }

    /// <summary>u32list：无填充元素串。</summary>
    public uint[] AsU32List()
    {
        if (Value.Length % 4 != 0)
            throw new ProtocolException($"tag {Id}: u32list 长度非 4 倍数");
        var result = new uint[Value.Length / 4];
        for (int i = 0; i < result.Length; i++)
            result[i] = BinaryPrimitives.ReadUInt32LittleEndian(Value.AsSpan(i * 4));
        return result;
    }

    public string AsUtf8() => Encoding.UTF8.GetString(Value);
}

/// <summary>协议层错误。与"设备返回了错误结果"不同——这里表示字节流本身不合法。</summary>
public sealed class ProtocolException(string message) : Exception(message);

/// <summary>
/// TLV 字段号。数值取自 shared/protocol/de-drms-cdc-v2.json 的 fields 段。
/// 名字对应 JSON 里的键，方便逐条核对。
/// </summary>
public static class Tag
{
    public const ushort Result = 1;
    public const ushort Reason = 2;
    public const ushort Uid = 3;
    public const ushort Boot = 4;
    public const ushort Capabilities = 5;
    public const ushort MaxPayload = 6;
    public const ushort RateMonitor = 7;
    public const ushort RateRecord = 8;
    public const ushort StatusRevision = 9;
    public const ushort MonoUs = 10;
    public const ushort Operation = 11;
    public const ushort Record = 12;
    public const ushort Acquisition = 16;
    public const ushort Recording = 17;
    public const ushort Medium = 18;
    public const ushort Owner = 19;
    public const ushort Maintenance = 20;
    public const ushort SampleGeneration = 21;
    public const ushort SampleIndex = 22;
    public const ushort Ohms = 23;
    public const ushort Ratio = 24;
    public const ushort Fresh = 25;
    public const ushort Classification = 26;
    public const ushort Level = 27;
    public const ushort Interval = 28;
    public const ushort Quality = 29;
    public const ushort Rate = 30;
    public const ushort RunningVersion = 31;
    public const ushort SavedVersion = 32;
    public const ushort BaselineVersion = 33;
    public const ushort CalibrationVersion = 34;
    public const ushort Fault = 35;
    public const ushort LastRecord = 36;
    public const ushort LastResult = 37;
    public const ushort CaptureLost = 38;
    public const ushort LogDropped = 39;
    public const ushort UnknownLoss = 40;
    public const ushort CleanEnd = 41;
    public const ushort RtcValid = 42;
    public const ushort BatteryMv = 43;
    public const ushort Source = 44;
    public const ushort Phase = 45;
    public const ushort ExpectedVersion = 48;
    public const ushort Settings = 49;
    public const ushort DurationMs = 50;
    public const ushort UtcS = 51;
    public const ushort Offset = 52;
    public const ushort Count = 53;
    public const ushort Data = 54;
    public const ushort Eof = 55;
    public const ushort FileId = 56;
    public const ushort FileSize = 57;
    public const ushort Cursor = 58;
    public const ushort NextCursor = 59;
    public const ushort Stream = 60;
    public const ushort PeriodMs = 61;
    public const ushort Sequence = 62;
    public const ushort Lost = 63;
    public const ushort EventCode = 64;
    public const ushort RateHz = 72;
    public const ushort RecordDurationMs = 73;
    public const ushort TauUs = 74;
    public const ushort WarmupUs = 75;
    public const ushort ConfirmUs = 76;
    public const ushort StaleTimeoutUs = 77;
    public const ushort Intervals = 78;
    public const ushort Alias = 79;
    public const ushort Specimen = 80;
    public const ushort BaselineMinCount = 81;
    public const ushort BaselineMinUs = 82;
    public const ushort BaselineMaxCv = 83;
    public const ushort IntervalNames = 84;
    public const ushort MediaGeneration = 85;
}

/// <summary>TLV 列表的读写。写出时统一置必填位（协议要求发送方对必填字段置位）。</summary>
public sealed class TlvWriter
{
    private readonly List<byte> _buffer = new();

    public int Length => _buffer.Count;

    public TlvWriter Add(ushort tag, ReadOnlySpan<byte> value, bool required = true)
    {
        ushort raw = required ? (ushort)(tag | Frame.RequiredTagMask) : tag;
        Span<byte> head = stackalloc byte[4];
        BinaryPrimitives.WriteUInt16LittleEndian(head, raw);
        BinaryPrimitives.WriteUInt16LittleEndian(head[2..], (ushort)value.Length);
        _buffer.AddRange(head.ToArray());
        _buffer.AddRange(value.ToArray());
        return this;
    }

    public TlvWriter AddU8(ushort tag, byte value, bool required = true)
        => Add(tag, [value], required);

    public TlvWriter AddBool(ushort tag, bool value, bool required = true)
        => Add(tag, new[] { value ? (byte)1 : (byte)0 }, required);

    public TlvWriter AddU16(ushort tag, ushort value, bool required = true)
    {
        Span<byte> b = stackalloc byte[2];
        BinaryPrimitives.WriteUInt16LittleEndian(b, value);
        return Add(tag, b, required);
    }

    public TlvWriter AddU32(ushort tag, uint value, bool required = true)
    {
        Span<byte> b = stackalloc byte[4];
        BinaryPrimitives.WriteUInt32LittleEndian(b, value);
        return Add(tag, b, required);
    }

    public TlvWriter AddU64(ushort tag, ulong value, bool required = true)
    {
        Span<byte> b = stackalloc byte[8];
        BinaryPrimitives.WriteUInt64LittleEndian(b, value);
        return Add(tag, b, required);
    }

    public TlvWriter AddF64(ushort tag, double value, bool required = true)
    {
        Span<byte> b = stackalloc byte[8];
        BinaryPrimitives.WriteDoubleLittleEndian(b, value);
        return Add(tag, b, required);
    }

    public TlvWriter AddRaw(ushort tag, byte[] value, bool required = true)
        => Add(tag, value, required);

    public byte[] ToArray() => _buffer.ToArray();
}

/// <summary>TLV 解析。拒绝重复字段、长度越界与超量字段数。</summary>
public static class TlvReader
{
    private const int MaxTopLevelFields = 64;

    public static List<TlvField> Parse(ReadOnlySpan<byte> payload)
    {
        var fields = new List<TlvField>();
        var seen = new HashSet<ushort>();
        int position = 0;

        while (position < payload.Length)
        {
            if (position + 4 > payload.Length)
                throw new ProtocolException("TLV 头被截断");

            ushort rawTag = BinaryPrimitives.ReadUInt16LittleEndian(payload[position..]);
            ushort length = BinaryPrimitives.ReadUInt16LittleEndian(payload[(position + 2)..]);
            position += 4;

            if (position + length > payload.Length)
                throw new ProtocolException("TLV 值超出载荷");

            ushort id = Frame.FieldId(rawTag);
            if (!seen.Add(id))
                throw new ProtocolException($"字段 {id} 重复出现");

            fields.Add(new TlvField(rawTag, payload.Slice(position, length).ToArray()));
            position += length;

            if (fields.Count > MaxTopLevelFields)
                throw new ProtocolException("顶层字段超过 64 个");
        }

        return fields;
    }

    /// <summary>按字段号建索引，未出现的字段不回退到默认值。</summary>
    public static Dictionary<ushort, TlvField> Index(IEnumerable<TlvField> fields)
        => fields.ToDictionary(f => f.Id);

    /// <summary>取必填字段；缺失即协议错误。</summary>
    public static TlvField Require(this Dictionary<ushort, TlvField> map, ushort tag, string name)
        => map.TryGetValue(tag, out var f) ? f : throw new ProtocolException($"缺少必填字段 {name}({tag})");

    /// <summary>取可选字段。</summary>
    public static TlvField? Optional(this Dictionary<ushort, TlvField> map, ushort tag)
        => map.TryGetValue(tag, out var f) ? f : null;
}
