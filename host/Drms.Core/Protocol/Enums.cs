namespace Drms.Core.Protocol;

/// <summary>
/// CDC v2 枚举。数值取自 shared/protocol/de-drms-cdc-v2.json 的 enums 段，
/// **不要**按 C 源码里的顺序推断——协议明确规定枚举不依赖 C 值。
/// </summary>
public static class Frame
{
    public const byte MajorVersion = 2;
    public const int HeaderLength = 20;
    public const int MaxPayload = 1024;
    public const int MaxDecodedLength = 1048;
    public const int MaxWireLength = 1054;

    /// <summary>TLV 头的必填位：置位表示接收者必须理解该字段。</summary>
    public const ushort RequiredTagMask = 0x8000;

    /// <summary>去掉必填位后的字段号。</summary>
    public static ushort FieldId(ushort rawTag) => (ushort)(rawTag & ~RequiredTagMask);
}

public enum Kind : byte
{
    Request = 1,
    Reply = 2,
    Event = 3,
}

public enum Result : ushort
{
    Ok = 0,
    Accepted = 1,   // 仅表示受理，不是完成
    Busy = 2,
    Invalid = 3,
    Stale = 4,
    NoChange = 5,
    IoError = 6,
    Timeout = 7,
    Cancelled = 8,
    Incomplete = 9,
    Quarantined = 10,
    Unsupported = 11,
    Empty = 12,
}

public enum Reason : ushort
{
    None = 0,
    BadField = 1,
    NoMedia = 2,
    ReadOnly = 3,
    WrongState = 4,
    Conflict = 5,
    VersionMismatch = 6,
    Expired = 7,
    RequestIdReused = 8,
    UnknownRequired = 9,
    UnknownOperation = 10,
    Hardware = 11,
    NoSpace = 12,
    NotFound = 13,
}

public enum Acquisition : byte
{
    Stopped = 0,
    Starting = 1,
    Stabilizing = 2,
    Monitor = 3,
    Reference = 4,
    Fault = 5,
}

public enum Recording : byte
{
    Idle = 0,
    Starting = 1,
    Active = 2,
    Closing = 3,
    Failed = 4,
}

public enum Medium : byte
{
    Absent = 0,
    Ready = 1,
    Fault = 2,
}

public enum StorageOwner : byte
{
    Local = 0,
    Exporting = 1,
    Exported = 2,
    Releasing = 3,
    Quarantined = 4,
}

public enum Maintenance : byte
{
    Idle = 0,
    Baseline = 1,
    Calibration = 2,
    ConfigApply = 3,
    ConfigSave = 4,
    Update = 5,
}

public enum Classification : byte
{
    Invalid = 0,
    Warmup = 1,
    Unconfigured = 2,
    Unmapped = 3,
    Pending = 4,
    Confirmed = 5,
}

public enum OperationPhase : byte
{
    Pending = 0,
    Active = 1,
    Finished = 2,
}

public enum OperationSource : byte
{
    System = 0,
    Button = 1,
    Cdc = 2,
    Debug = 3,
}

public enum StreamKind : byte
{
    Curve = 0,
    Raw = 1,
}

/// <summary>quality（tag 29）位定义，见协议正文。</summary>
[Flags]
public enum QualityFlags : uint
{
    None = 0,
    NoValidSample = 1u << 0,
    FrameIntegrity = 1u << 1,
    ExcitationInvalid = 1u << 2,
    SampleGap = 1u << 3,
    BaselineNotApplicable = 1u << 4,
    IntervalTableMissing = 1u << 5,
}

/// <summary>fault（tag 35）位定义。</summary>
[Flags]
public enum FaultFlags : uint
{
    None = 0,
    Acquisition = 1u << 0,
    Storage = 1u << 1,
    Persistence = 1u << 2,
    Timebase = 1u << 3,
    Usb = 1u << 4,
    Isolation = 1u << 5,
}
