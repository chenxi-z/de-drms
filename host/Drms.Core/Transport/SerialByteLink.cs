using System.IO.Ports;
using System.Threading;

namespace Drms.Core.Transport;

/// <summary>
/// 基于 System.IO.Ports 的串口链路。
///
/// 为什么用 System.IO.Ports 而不是原生 Win32 封装：开发在 Ubuntu、交付在
/// Windows，托管实现让两侧共用同一份代码。代价是 DTR 必须显式拉起——
/// 固件只有在 DTR 有效后才接受 HELLO，这一条是最容易踩的坑。
/// </summary>
public sealed class SerialByteLink : IByteLink
{
    private readonly SerialPort _port;
    private readonly object _lock = new();

    public SerialByteLink(string portName, int baudRate = 115200)
    {
        _port = new SerialPort(portName, baudRate, Parity.None, 8, StopBits.One)
        {
            ReadTimeout = 100,
            WriteTimeout = 1000,
            Handshake = Handshake.None,
            DtrEnable = true,   // 固件要求 DTR 有效才接受 HELLO
            RtsEnable = true,
        };
        _port.Open();
    }

    public bool IsOpen => _port.IsOpen;

    /// <summary>设备路径，便于日志里指认。</summary>
    public string PortName => _port.PortName;

    public void Write(ReadOnlySpan<byte> data)
    {
        lock (_lock)
        {
            byte[] buffer = data.ToArray();
            _port.Write(buffer, 0, buffer.Length);
        }
    }

    public byte[] Read(TimeSpan timeout)
    {
        var deadline = DateTime.UtcNow + timeout;
        var collected = new List<byte>();

        while (DateTime.UtcNow < deadline)
        {
            try
            {
                int available = _port.BytesToRead;
                if (available > 0)
                {
                    var buffer = new byte[available];
                    int read = _port.Read(buffer, 0, available);
                    if (read > 0)
                        collected.AddRange(buffer.AsSpan(0, read).ToArray());
                    continue;
                }
            }
            catch (TimeoutException)
            {
                // 正常：串口没有新数据
            }

            if (collected.Count > 0)
                break; // 已经拿到一些就不再等满整个超时
            Thread.Sleep(2);
        }

        return collected.ToArray();
    }

    /// <summary>列出本机串口名。界面用它给用户选。</summary>
    public static string[] ListPorts() => SerialPort.GetPortNames().OrderBy(p => p).ToArray();

    public void Dispose()
    {
        lock (_lock)
        {
            try
            {
                if (_port.IsOpen)
                    _port.Close();
            }
            catch (IOException)
            {
                // 拔线时关闭可能抛；这里没有补救动作，忽略即可。
            }
            _port.Dispose();
        }
    }
}
