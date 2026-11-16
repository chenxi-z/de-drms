namespace Drms.Core.Protocol;

/// <summary>HELLO 回复（opcode 1）。</summary>
public sealed class HelloReply
{
    public required uint[] Uid { get; init; }
    public required ulong Boot { get; init; }
    public required ushort[] Capabilities { get; init; }
    public required ushort MaxPayload { get; init; }
    public required uint[] RateMonitor { get; init; }
    public required uint[] RateRecord { get; init; }

    /// <summary>人读形式：三个 UID 字按八位大写十六进制逐字拼接。</summary>
    public string UidText => string.Concat(Uid.Select(w => w.ToString("X8")));

    public bool Supports(ushort opcode) => Capabilities.Contains(opcode);
}

/// <summary>
/// GET_STATUS 回复（opcode 2）。字段大多可缺省——
/// 协议规定"可选数值无效时省略，不能用零替代"，所以全部用可空类型，
/// 让调用方能区分"设备说这个值无效"和"设备说了个 0"。
/// </summary>
public sealed class StatusReply
{
    public required ulong StatusRevision { get; init; }
    public required ulong MonoUs { get; init; }
    public required Acquisition Acquisition { get; init; }
    public required Recording Recording { get; init; }
    public required Medium Medium { get; init; }
    public required StorageOwner Owner { get; init; }
    public required Maintenance Maintenance { get; init; }
    public required uint SampleGeneration { get; init; }
    public required uint Rate { get; init; }
    public required bool Fresh { get; init; }
    public required Classification Classification { get; init; }
    public required uint Quality { get; init; }
    public required ulong RunningVersion { get; init; }
    public required ulong SavedVersion { get; init; }
    public required ulong BaselineVersion { get; init; }
    public required ulong CalibrationVersion { get; init; }
    public required uint Fault { get; init; }
    public required bool RtcValid { get; init; }
    public required uint MediaGeneration { get; init; }

    public ulong? SampleIndex { get; init; }
    public double? Ohms { get; init; }
    public double? Ratio { get; init; }
    public byte? Level { get; init; }
    public ushort? Interval { get; init; }
    public ulong? Operation { get; init; }
    public ulong? Record { get; init; }
    public ulong? LastRecord { get; init; }
    public ushort? LastResult { get; init; }
    public ushort? BatteryMv { get; init; }

    public QualityFlags QualityFlags => (QualityFlags)Quality;
    public FaultFlags FaultFlags => (FaultFlags)Fault;
}

/// <summary>GET_OPERATION 回复（opcode 3）。</summary>
public sealed class OperationReply
{
    public required ulong Operation { get; init; }
    public required OperationPhase Phase { get; init; }
    public required OperationSource Source { get; init; }
    public required Result Result { get; init; }
    public Reason? Reason { get; init; }
    public ulong? Record { get; init; }
    public ulong? FileSize { get; init; }

    /// <summary>终态判定：只有 FINISHED 才是最终结果，ACCEPTED/ACTIVE 都还在跑。</summary>
    public bool IsFinished => Phase == OperationPhase.Finished;
}

/// <summary>GET_RECORD 回复（opcode 4）。</summary>
public sealed class RecordReply
{
    public required ulong Record { get; init; }
    public required OperationPhase Phase { get; init; }
    public required Result Result { get; init; }
    public required bool CleanEnd { get; init; }
    public required ulong CaptureLost { get; init; }
    public required ulong LogDropped { get; init; }
    public required bool UnknownLoss { get; init; }
}

/// <summary>GET_CONFIG 回复（opcode 32）：一段嵌套 TLV 原始字节 + 两个版本。</summary>
public sealed class ConfigReply
{
    public required byte[] Settings { get; init; }
    public required ulong RunningVersion { get; init; }
    public required ulong SavedVersion { get; init; }

    /// <summary>把 settings 解析成字段表。出厂空配置时设备返回 UNSUPPORTED，不会走到这里。</summary>
    public Dictionary<ushort, TlvField> Fields => _fields ??= TlvReader.Index(TlvReader.Parse(Settings));
    private Dictionary<ushort, TlvField>? _fields;
}

/// <summary>MEAS_EVENT（opcode 130）：CURVE 订阅推送的快照。</summary>
public sealed class MeasurementEvent
{
    public required ulong Sequence { get; init; }
    public required ulong Lost { get; init; }
    public required ulong MonoUs { get; init; }
    public required bool Fresh { get; init; }
    public required Classification Classification { get; init; }
    public required uint Quality { get; init; }

    public ulong? SampleIndex { get; init; }
    public double? Ohms { get; init; }
    public double? Ratio { get; init; }
    public byte? Level { get; init; }
    public ushort? Interval { get; init; }
}

/// <summary>RAW_EVENT（opcode 131）：RAW 订阅推送的一批原始记录帧。
///
/// Data 是同一代次连续的 16 字节记录（BIN v2 帧布局：12 B ADC + u32 序号），
/// 批间以 Sequence 连续与 Lost 判定缺口；代次变化时设备另起一批。
/// 每帧的 ADC 字段是 12 B 大端：status u16 / voltage i24 / sense i24 / CRC16 / 尾字节，
/// 与 tools/de_drms_log.py 的 LogReader 解码口径一致。</summary>
public sealed class RawEvent
{
    public required ulong Sequence { get; init; }
    public required ulong Lost { get; init; }
    public required uint SampleGeneration { get; init; }
    public required ulong SampleIndex { get; init; }
    public required uint Rate { get; init; }
    public required byte[] Data { get; init; }

    /// <summary>本批帧数（Data 长度 / 16）。</summary>
    public int FrameCount => Data.Length / 16;

    /// <summary>逐帧解析出 (序号, status, voltage, sense, crcOk)。</summary>
    public IEnumerable<(uint Sequence, ushort Status, int Voltage, int Sense, bool CrcOk)> Frames()
    {
        for (int i = 0; i + 16 <= Data.Length; i += 16)
        {
            var f = Data.AsSpan(i, 16);
            ushort status = (ushort)((f[0] << 8) | f[1]);
            int voltage = ((sbyte)f[3] << 16) | (f[4] << 8) | f[5];
            int sense = ((sbyte)f[6] << 16) | (f[7] << 8) | f[8];
            ushort crc = (ushort)((f[9] << 8) | f[10]);
            bool crcOk = Crc16Ccitt(f[..9]) == crc;
            uint seq = System.Buffers.Binary.BinaryPrimitives.ReadUInt32LittleEndian(f[12..]);
            yield return (seq, status, voltage, sense, crcOk);
        }
    }

    /// <summary>ADC 帧 CRC：CRC-16/CCITT 初值 0xFFFF（与固件及 Python 解码器一致）。</summary>
    public static ushort Crc16Ccitt(ReadOnlySpan<byte> bytes)
    {
        ushort crc = 0xFFFF;
        foreach (byte b in bytes)
        {
            crc ^= (ushort)(b << 8);
            for (int bit = 0; bit < 8; bit++)
                crc = (crc & 0x8000) != 0 ? (ushort)((crc << 1) ^ 0x1021) : (ushort)(crc << 1);
        }
        return crc;
    }
}

/// <summary>区间表条目（config tag 78 的 30 字节元素）。lo/hi 单位是 R/R₀。</summary>
public sealed class MonitorInterval
{
    public required double Low { get; init; }
    public required double High { get; init; }
    public required double Hysteresis { get; init; }
    public required ushort Id { get; init; }
    public required byte Level { get; init; }

    /// <summary>末区间上界是否闭合。默认不闭合，与协议 reserved 位无关。</summary>
    public bool LastUpperClosed { get; init; }

    /// <summary>方向：0 无 / 1 下降 / 2 上升。默认 0。</summary>
    public byte Direction { get; init; }
}

/// <summary>
/// 业务消息的编解码。所有数值单位以协议正文为准（µs、mΩ 之外的都按字段名）。
///
/// 这一层只做"字段 ↔ 类型"的映射，不做业务判断——例如不替调用方决定
/// ACCEPTED 算不算成功，也不把旧的等级当成当前等级。
/// </summary>
public static class Messages
{
    // ---- 请求构造 ----

    public static byte[] HelloRequest(ulong requestId) =>
        FrameCodec.Encode(Kind.Request, Opcodes.Hello, 0, requestId, []);

    public static byte[] GetStatusRequest(uint session, ulong requestId) =>
        FrameCodec.Encode(Kind.Request, Opcodes.GetStatus, session, requestId, []);

    public static byte[] GetOperationRequest(uint session, ulong requestId, ulong operation) =>
        FrameCodec.Encode(Kind.Request, Opcodes.GetOperation, session, requestId,
            new TlvWriter().AddU64(Tag.Operation, operation).ToArray());

    public static byte[] GetRecordRequest(uint session, ulong requestId, ulong record) =>
        FrameCodec.Encode(Kind.Request, Opcodes.GetRecord, session, requestId,
            new TlvWriter().AddU64(Tag.Record, record).ToArray());

    /// <summary>BEGIN_RECORD。durationMs 为 null 表示用当前配置，0 表示手动结束。</summary>
    public static byte[] BeginRecordRequest(uint session, ulong requestId, uint? durationMs = null)
    {
        var tlv = new TlvWriter();
        if (durationMs.HasValue)
            tlv.AddU32(Tag.DurationMs, durationMs.Value);
        return FrameCodec.Encode(Kind.Request, Opcodes.BeginRecord, session, requestId, tlv.ToArray());
    }

    public static byte[] EndRecordRequest(uint session, ulong requestId, ulong record) =>
        FrameCodec.Encode(Kind.Request, Opcodes.EndRecord, session, requestId,
            new TlvWriter().AddU64(Tag.Record, record).ToArray());

    public static byte[] SafeStopRequest(uint session, ulong requestId) =>
        FrameCodec.Encode(Kind.Request, Opcodes.SafeStop, session, requestId, []);

    public static byte[] ResumeMonitorRequest(uint session, ulong requestId) =>
        FrameCodec.Encode(Kind.Request, Opcodes.ResumeMonitor, session, requestId, []);

    public static byte[] GetConfigRequest(uint session, ulong requestId) =>
        FrameCodec.Encode(Kind.Request, Opcodes.GetConfig, session, requestId, []);

    public static byte[] BuildR0Request(uint session, ulong requestId) =>
        FrameCodec.Encode(Kind.Request, Opcodes.BuildR0, session, requestId, []);

    public static byte[] CalibrateRequest(uint session, ulong requestId) =>
        FrameCodec.Encode(Kind.Request, Opcodes.Calibrate, session, requestId, []);

    public static byte[] SubscribeCurveRequest(uint session, ulong requestId, uint periodMs) =>
        FrameCodec.Encode(Kind.Request, Opcodes.Subscribe, session, requestId,
            new TlvWriter().AddU8(Tag.Stream, (byte)StreamKind.Curve)
                           .AddU32(Tag.PeriodMs, periodMs).ToArray());

    /// <summary>SUBSCRIBE stream=RAW：period_ms 固定 0（分块由设备批大小决定）。
    /// 设备按当前采样率验证带宽：超档位返回 INVALID，不静默降级。</summary>
    public static byte[] SubscribeRawRequest(uint session, ulong requestId) =>
        FrameCodec.Encode(Kind.Request, Opcodes.Subscribe, session, requestId,
            new TlvWriter().AddU8(Tag.Stream, (byte)StreamKind.Raw)
                           .AddU32(Tag.PeriodMs, 0).ToArray());

    public static byte[] UnsubscribeRequest(uint session, ulong requestId, StreamKind stream) =>
        FrameCodec.Encode(Kind.Request, Opcodes.Unsubscribe, session, requestId,
            new TlvWriter().AddU8(Tag.Stream, (byte)stream).ToArray());

    /// <summary>APPLY_CONFIG：settings 是一段嵌套 TLV，期望版本用于并发保护。</summary>
    public static byte[] ApplyConfigRequest(uint session, ulong requestId,
                                            ulong expectedVersion, byte[] settings)
        => FrameCodec.Encode(Kind.Request, Opcodes.ApplyConfig, session, requestId,
            new TlvWriter().AddU64(Tag.ExpectedVersion, expectedVersion)
                           .AddRaw(Tag.Settings, settings).ToArray());

    public static byte[] SaveConfigRequest(uint session, ulong requestId, ulong expectedVersion) =>
        FrameCodec.Encode(Kind.Request, Opcodes.SaveConfig, session, requestId,
            new TlvWriter().AddU64(Tag.ExpectedVersion, expectedVersion).ToArray());

    // ---- 回复解析 ----

    /// <summary>所有回复都带 result。取不到就是协议错误。</summary>
    public static Result ReadResult(Message message)
        => (Result)message.Index.Require(Tag.Result, "result").AsU16();

    public static Reason? ReadReason(Message message)
        => message.Index.Optional(Tag.Reason) is { } f ? (Reason)f.AsU16() : null;

    public static HelloReply ParseHello(Message message)
    {
        var f = message.Index;
        return new HelloReply
        {
            Uid = f.Require(Tag.Uid, "uid").AsU32List(),
            Boot = f.Require(Tag.Boot, "boot").AsU64(),
            Capabilities = f.Require(Tag.Capabilities, "capabilities").AsU16List(),
            MaxPayload = f.Require(Tag.MaxPayload, "max_payload").AsU16(),
            RateMonitor = f.Require(Tag.RateMonitor, "rate_monitor").AsU32List(),
            RateRecord = f.Require(Tag.RateRecord, "rate_record").AsU32List(),
        };
    }

    public static StatusReply ParseStatus(Message message)
    {
        var f = message.Index;
        return new StatusReply
        {
            StatusRevision = f.Require(Tag.StatusRevision, "status_revision").AsU64(),
            MonoUs = f.Require(Tag.MonoUs, "mono_us").AsU64(),
            Acquisition = (Acquisition)f.Require(Tag.Acquisition, "acquisition").AsByte(),
            Recording = (Recording)f.Require(Tag.Recording, "recording").AsByte(),
            Medium = (Medium)f.Require(Tag.Medium, "medium").AsByte(),
            Owner = (StorageOwner)f.Require(Tag.Owner, "owner").AsByte(),
            Maintenance = (Maintenance)f.Require(Tag.Maintenance, "maintenance").AsByte(),
            SampleGeneration = f.Require(Tag.SampleGeneration, "sample_generation").AsU32(),
            Rate = f.Require(Tag.Rate, "rate").AsU32(),
            Fresh = f.Require(Tag.Fresh, "fresh").AsBool(),
            Classification = (Classification)f.Require(Tag.Classification, "classification").AsByte(),
            Quality = f.Require(Tag.Quality, "quality").AsU32(),
            RunningVersion = f.Require(Tag.RunningVersion, "running_version").AsU64(),
            SavedVersion = f.Require(Tag.SavedVersion, "saved_version").AsU64(),
            BaselineVersion = f.Require(Tag.BaselineVersion, "baseline_version").AsU64(),
            CalibrationVersion = f.Require(Tag.CalibrationVersion, "calibration_version").AsU64(),
            Fault = f.Require(Tag.Fault, "fault").AsU32(),
            RtcValid = f.Require(Tag.RtcValid, "rtc_valid").AsBool(),
            MediaGeneration = f.Require(Tag.MediaGeneration, "media_generation").AsU32(),
            SampleIndex = f.Optional(Tag.SampleIndex)?.AsU64(),
            Ohms = f.Optional(Tag.Ohms)?.AsDouble(),
            Ratio = f.Optional(Tag.Ratio)?.AsDouble(),
            Level = f.Optional(Tag.Level)?.AsByte(),
            Interval = f.Optional(Tag.Interval)?.AsU16(),
            Operation = f.Optional(Tag.Operation)?.AsU64(),
            Record = f.Optional(Tag.Record)?.AsU64(),
            LastRecord = f.Optional(Tag.LastRecord)?.AsU64(),
            LastResult = f.Optional(Tag.LastResult)?.AsU16(),
            BatteryMv = f.Optional(Tag.BatteryMv)?.AsU16(),
        };
    }

    public static OperationReply ParseOperation(Message message)
    {
        var f = message.Index;
        return new OperationReply
        {
            Operation = f.Require(Tag.Operation, "operation").AsU64(),
            Phase = (OperationPhase)f.Require(Tag.Phase, "phase").AsByte(),
            Source = (OperationSource)f.Require(Tag.Source, "source").AsByte(),
            Result = (Result)f.Require(Tag.Result, "result").AsU16(),
            Reason = ReadReason(message),
            Record = f.Optional(Tag.Record)?.AsU64(),
            FileSize = f.Optional(Tag.FileSize)?.AsU64(),
        };
    }

    public static RecordReply ParseRecord(Message message)
    {
        var f = message.Index;
        return new RecordReply
        {
            Record = f.Require(Tag.Record, "record").AsU64(),
            Phase = (OperationPhase)f.Require(Tag.Phase, "phase").AsByte(),
            Result = (Result)f.Require(Tag.Result, "result").AsU16(),
            CleanEnd = f.Require(Tag.CleanEnd, "clean_end").AsBool(),
            CaptureLost = f.Require(Tag.CaptureLost, "capture_lost").AsU64(),
            LogDropped = f.Require(Tag.LogDropped, "log_dropped").AsU64(),
            UnknownLoss = f.Require(Tag.UnknownLoss, "unknown_loss").AsBool(),
        };
    }

    public static ConfigReply ParseConfig(Message message)
    {
        var f = message.Index;
        return new ConfigReply
        {
            Settings = f.Require(Tag.Settings, "settings").Value,
            RunningVersion = f.Require(Tag.RunningVersion, "running_version").AsU64(),
            SavedVersion = f.Require(Tag.SavedVersion, "saved_version").AsU64(),
        };
    }

    /// <summary>BEGIN_RECORD / END_RECORD 的成功回复：operation + record。</summary>
    public static (ulong Operation, ulong Record) ParseOperationAndRecord(Message message)
    {
        var f = message.Index;
        return (f.Require(Tag.Operation, "operation").AsU64(),
                f.Require(Tag.Record, "record").AsU64());
    }

    public static MeasurementEvent ParseMeasurementEvent(Message message)
    {
        var f = message.Index;
        return new MeasurementEvent
        {
            Sequence = f.Require(Tag.Sequence, "sequence").AsU64(),
            Lost = f.Require(Tag.Lost, "lost").AsU64(),
            MonoUs = f.Require(Tag.MonoUs, "mono_us").AsU64(),
            Fresh = f.Require(Tag.Fresh, "fresh").AsBool(),
            Classification = (Classification)f.Require(Tag.Classification, "classification").AsByte(),
            Quality = f.Require(Tag.Quality, "quality").AsU32(),
            SampleIndex = f.Optional(Tag.SampleIndex)?.AsU64(),
            Ohms = f.Optional(Tag.Ohms)?.AsDouble(),
            Ratio = f.Optional(Tag.Ratio)?.AsDouble(),
            Level = f.Optional(Tag.Level)?.AsByte(),
            Interval = f.Optional(Tag.Interval)?.AsU16(),
        };
    }

    public static RawEvent ParseRawEvent(Message message)
    {
        var f = message.Index;
        return new RawEvent
        {
            Sequence = f.Require(Tag.Sequence, "sequence").AsU64(),
            Lost = f.Require(Tag.Lost, "lost").AsU64(),
            SampleGeneration = f.Require(Tag.SampleGeneration, "sample_generation").AsU32(),
            SampleIndex = f.Require(Tag.SampleIndex, "sample_index").AsU64(),
            Rate = f.Require(Tag.Rate, "rate").AsU32(),
            Data = f.Require(Tag.Data, "data").Value,
        };
    }

    // ---- 配置快照里的区间表 ----

    /// <summary>
    /// 解析 config 里的区县表（tag 78）。每条 30 字节：
    /// lo,f64 hi,f64 h,f64 id,u16 level,u8 last_upper_closed,bool direction,u8 reserved,u8
    /// </summary>
    public static List<MonitorInterval> ParseIntervals(byte[] raw)
    {
        const int EntrySize = 30;
        if (raw.Length % EntrySize != 0)
            throw new ProtocolException($"区间表长度 {raw.Length} 非 {EntrySize} 的倍数");

        var result = new List<MonitorInterval>(raw.Length / EntrySize);
        for (int offset = 0; offset < raw.Length; offset += EntrySize)
        {
            var span = raw.AsSpan(offset, EntrySize);
            result.Add(new MonitorInterval
            {
                Low = System.Buffers.Binary.BinaryPrimitives.ReadDoubleLittleEndian(span),
                High = System.Buffers.Binary.BinaryPrimitives.ReadDoubleLittleEndian(span[8..]),
                Hysteresis = System.Buffers.Binary.BinaryPrimitives.ReadDoubleLittleEndian(span[16..]),
                Id = System.Buffers.Binary.BinaryPrimitives.ReadUInt16LittleEndian(span[24..]),
                Level = span[26],
                LastUpperClosed = span[27] != 0,
                Direction = span[28],
            });
        }
        return result;
    }

    /// <summary>把区间表编码回 30 字节条目串，供 APPLY_CONFIG 使用。</summary>
    public static byte[] EncodeIntervals(IEnumerable<MonitorInterval> intervals)
    {
        var buffer = new List<byte>();
        Span<byte> entry = stackalloc byte[30]; // 在循环外分配，避免堆栈随条目数增长
        foreach (var it in intervals)
        {
            entry.Clear();
            System.Buffers.Binary.BinaryPrimitives.WriteDoubleLittleEndian(entry, it.Low);
            System.Buffers.Binary.BinaryPrimitives.WriteDoubleLittleEndian(entry[8..], it.High);
            System.Buffers.Binary.BinaryPrimitives.WriteDoubleLittleEndian(entry[16..], it.Hysteresis);
            System.Buffers.Binary.BinaryPrimitives.WriteUInt16LittleEndian(entry[24..], it.Id);
            entry[26] = it.Level;
            entry[27] = (byte)(it.LastUpperClosed ? 1 : 0);
            entry[28] = it.Direction;
            // entry[29] reserved = 0
            buffer.AddRange(entry.ToArray());
        }
        return buffer.ToArray();
    }
}

/// <summary>请求 opcode。数值取自机器定义。</summary>
public static class Opcodes
{
    public const ushort Hello = 1;
    public const ushort GetStatus = 2;
    public const ushort GetOperation = 3;
    public const ushort GetRecord = 4;
    public const ushort BeginRecord = 16;
    public const ushort EndRecord = 17;
    public const ushort SafeStop = 18;
    public const ushort ResumeMonitor = 19;
    public const ushort GetConfig = 32;
    public const ushort ApplyConfig = 33;
    public const ushort SaveConfig = 34;
    public const ushort BuildR0 = 35;
    public const ushort Calibrate = 36;
    public const ushort SetUtc = 37;
    public const ushort MscExport = 48;
    public const ushort MscRelease = 49;
    public const ushort FileOpen = 50;
    public const ushort FileRead = 51;
    public const ushort FileClose = 52;
    public const ushort FileList = 53;
    public const ushort Subscribe = 64;
    public const ushort Unsubscribe = 65;
    public const ushort OpEvent = 128;
    public const ushort FaultEvent = 129;
    public const ushort MeasEvent = 130;
    public const ushort RawEvent = 131;
}
