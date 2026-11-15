namespace Drms.Core.Protocol;

/// <summary>
/// 标准 COBS（Consistent Overhead Byte Stuffing）编解码。
///
/// 为什么需要：CDC 是字节流，没有帧边界。COBS 保证编码结果里不含 0x00，
/// 于是 0x00 就可以当帧分隔符——这既给出了确定的分帧方式，又让载荷里的
/// 任意字节（包括 0）都能原样传输，不必转义。
///
/// 编码规则：每段最多 254 字节，段前放"本段长度 + 1"。段长不足 254 时
/// 末尾那个隐含的 0 由长度码表达；恰好 254 字节的段后面必须补一个 0x01
/// 表示"下一段为空"，否则解码端无法区分"段用完了"和"后面还有数据"。
/// </summary>
public static class Cobs
{
    /// <summary>
    /// 编码为不含 0x00 的字节串（**不含**尾部分隔符；调用方自行追加）。
    /// </summary>
    public static byte[] Encode(ReadOnlySpan<byte> input)
    {
        // 最坏情况：每 254 字节多一个长度码，所以 n + n/254 + 1。
        var output = new List<byte>(input.Length + input.Length / 254 + 2);

        int index = 0;
        while (index < input.Length)
        {
            // 找本段里第一个 0x00，或到 254 字节上限。
            int codeIndex = output.Count;
            output.Add(0); // 占位，稍后回填长度码

            int code = 1;
            while (index < input.Length && code <= 254)
            {
                byte b = input[index++];
                if (b == 0)
                    break;
                output.Add(b);
                code++;
            }

            output[codeIndex] = (byte)code;

            // 读到 0x00 时循环已经跳过它，长度码就是"到 0 之前有几个字节 + 1"，
            // 解码端据此还原那个 0。
        }

        // 输入为空时也必须产出一个合法的空帧（只有一个长度码 0x01）。
        if (output.Count == 0)
            output.Add(0x01);

        return output.ToArray();
    }

    /// <summary>
    /// 解码一段不含 0x00 的字节（**不含**分隔符）。格式非法时返回 false。
    /// </summary>
    public static bool TryDecode(ReadOnlySpan<byte> encoded, out byte[] decoded)
    {
        decoded = [];
        if (encoded.Length == 0)
            return false;

        var output = new List<byte>(encoded.Length);

        int position = 0;
        while (position < encoded.Length)
        {
            int code = encoded[position++];
            if (code == 0)
                return false; // 0x00 不该出现在编码结果内部

            // 去掉长度码本身，本段应携带 code-1 个字节。
            int payload = code - 1;
            if (position + payload > encoded.Length)
                return false; // 长度码声明的内容超出缓冲

            for (int i = 0; i < payload; i++)
                output.Add(encoded[position++]);

            // code < 255 表示这一段的结尾原本是一个 0x00；
            // 只有"还有后续段"时才需要补回那个 0。
            if (code < 0xFF && position < encoded.Length)
                output.Add(0);
        }

        decoded = output.ToArray();
        return true;
    }
}
