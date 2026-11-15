namespace Drms.Core.Protocol;

/// <summary>
/// CRC-32/ISO-HDLC（与 zlib.crc32 同一参数）。
///
/// 为什么手写而不用 System.IO.Hashing.Crc32：后者默认参数是
/// CRC-32/ISO-HDLC 没错，但协议要求"123456789"算出 0xCBF43926 作为
/// 固定校验值，自己实现可以直接把这个值写成测试，不依赖库的默认值是否一致。
/// </summary>
public static class Crc32
{
    public const uint CheckValue123456789 = 0xCBF43926u;

    private const uint Polynomial = 0xEDB88320u;
    private static readonly uint[] Table = BuildTable();

    private static uint[] BuildTable()
    {
        var table = new uint[256];
        for (uint i = 0; i < 256; i++)
        {
            uint crc = i;
            for (int bit = 0; bit < 8; bit++)
                crc = (crc & 1) != 0 ? (crc >> 1) ^ Polynomial : crc >> 1;
            table[i] = crc;
        }
        return table;
    }

    /// <summary>对一个完整缓冲算 CRC-32。</summary>
    public static uint Compute(ReadOnlySpan<byte> data)
    {
        uint crc = 0xFFFFFFFFu;
        foreach (byte b in data)
            crc = (crc >> 8) ^ Table[(crc ^ b) & 0xFF];
        return crc ^ 0xFFFFFFFFu;
    }
}
