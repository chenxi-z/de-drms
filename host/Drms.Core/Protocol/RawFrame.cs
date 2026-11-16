using System.Buffers.Binary;

namespace Drms.Core.Protocol;

/// <summary>
/// 16 字节原始记录帧（12 B ADC + u32 序号）的解码与有效性判定。
///
/// 口径与 tools/de_drms_log.py、固件 drms_measurement 一致：
///   · 帧 CRC16（CCITT, init 0xFFFF）覆盖前 9 字节；
///   · 格式：status 高字节 0x22、bit7 不清、第 3 字节 0、尾字节 0；
///   · ADC 故障位（status bit1..6）；
///   · 量程与激励门限（shared/protocol/de-drms-v1.json 的 excitation_guard）。
/// 三处（RAW 显示、PC 落盘、离线基准）必须共用这一份，否则统计对不上。
/// </summary>
public readonly record struct RawFrame(
    uint Sequence, int Voltage, int Sense, ushort Status, bool CrcOk, bool FormatOk, bool AdcFault)
{
    public const int SenseCodeMin = 3643701;
    public const int SenseCodeMax = 4453411;
    public const long VoltagePlusSenseMax = 8484791;

    /// <summary>帧是否有效（可用于测量）。</summary>
    public bool IsValid
    {
        get
        {
            if (!CrcOk || !FormatOk || AdcFault) return false;
            if (Voltage >= 8388606 || Voltage <= -8388607) return false;
            if (Sense >= 8388606 || Sense <= 4096) return false;
            if (Voltage < -4096) return false;
            if (Sense < SenseCodeMin || Sense > SenseCodeMax) return false;
            return (long)Voltage + Sense <= VoltagePlusSenseMax;
        }
    }

    /// <summary>按校准系数换算电阻（Ω）；无效帧或系数缺失返回 null。</summary>
    public double? Ohms(double? scaleOhms)
        => scaleOhms is { } k && IsValid && Sense != 0 ? k * Voltage / Sense : null;

    /// <summary>解码一帧 16 B。</summary>
    public static RawFrame Decode(ReadOnlySpan<byte> f)
    {
        ushort status = (ushort)((f[0] << 8) | f[1]);
        int voltage = ((sbyte)f[3] << 16) | (f[4] << 8) | f[5];
        int sense = ((sbyte)f[6] << 16) | (f[7] << 8) | f[8];
        ushort crc = (ushort)((f[9] << 8) | f[10]);
        bool crcOk = RawEvent.Crc16Ccitt(f[..9]) == crc;
        bool formatOk = f[0] == 0x22 && (f[1] & 0x80) == 0 && f[2] == 0 && f[11] == 0;
        bool adcFault = (f[1] & 0x6F) != 0;
        uint sequence = BinaryPrimitives.ReadUInt32LittleEndian(f[12..]);
        return new RawFrame(sequence, voltage, sense, status, crcOk, formatOk, adcFault);
    }
}
