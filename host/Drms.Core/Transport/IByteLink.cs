namespace Drms.Core.Transport;

/// <summary>
/// 字节链路抽象。抽出这一层是为了两件事：
///   1. 单测可以用假链路跑完整会话逻辑，不需要真设备；
///   2. 将来真要换传输（比如网络代理）时不必改会话层。
/// </summary>
public interface IByteLink : IDisposable
{
    /// <summary>链路是否已打开。</summary>
    bool IsOpen { get; }

    /// <summary>写入一段字节。必须把全部字节送出去，否则抛异常。</summary>
    void Write(ReadOnlySpan<byte> data);

    /// <summary>
    /// 阻塞读取，最多等待 <paramref name="timeout"/>。超时返回空数组（不是异常）。
    /// </summary>
    byte[] Read(TimeSpan timeout);
}
