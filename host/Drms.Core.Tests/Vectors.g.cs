namespace Drms.Core.Tests;

/// <summary>
/// 机器定义 shared/protocol/de-drms-cdc-v2.json 的四条线上向量。
/// 由脚本从 JSON 直接生成，避免手抄长 hex 出错；改协议时重新生成本文件。
/// </summary>
public static class Vectors
{
    public const string HELLO_DECODED =
        "0201010000000000010000000000000000000000d7970e66";
    public const string HELLO_WIRE =
        "040201010101010102010101010101010101010105d7970e6600";

    public const string READ_OPERATION_DECODED =
        "020103000100000002000000000000000c0000000b800800010000000000000050a62bcd";
    public const string READ_OPERATION_WIRE =
        "04020103020101010202010101010101020c0101040b800802010101010101010550a62bcd00";

    public const string EXTENSION_254_DECODED =
        "02010200010000000300000000000000020100000010fe00abababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababab120e96ec";
    public const string EXTENSION_254_WIRE =
        "0402010202010101020301010101010103020101010310feffababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "ababababababababababababababababababababababababababababab05120e96ec00";

    public const string MAXIMUM_PAYLOAD_DECODED =
        "02010200010000000300000000000000000400000010fc03abababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "ababababababababababababababababababababababababababababababababababababababababababababa1362b51";
    public const string MAXIMUM_PAYLOAD_WIRE =
        "040201020201010102030101010101010102040101ff10fc03ababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "ababababababababababababababababababababababababababffababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababffabababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "ababababababababababababababababababababababababababababababababababababffababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "abababababababababababababababababababababababababababababababababababababababababababababababababab" +
        "ababababababababababababababababababababababababababababababababababababababababab0cabababababababa1" +
        "362b5100";

}