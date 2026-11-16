namespace Drms.Core.Filter;

/// <summary>
/// 单周期滑动平均：窗口 = 恰好一个工频周期（fs / fLine 取整），
/// 对 50 Hz 及其所有整数次谐波都是精确零点（梳状），用于和陷波器对比。
///
/// 与陷波器的差异（对比测试要看清）：
///   · 通带形状差（sinc 而不是平顶），低频仍有衰减、存在旁瓣；
///   · 群延迟约为半个周期（20 ms @ 50 Hz / 4 kSPS 下 40 个样本），阶跃响应是斜坡；
///   · 只需一次加/减，算力最低。
/// </summary>
public sealed class PeriodAverageFilter
{
    private readonly double[] _buffer;
    private readonly int _window;
    private int _index;
    private double _sum;
    private bool _primed;

    public PeriodAverageFilter(double sampleRateHz, double lineHz)
    {
        if (!(sampleRateHz > 0) || !(lineHz > 0))
            throw new ArgumentOutOfRangeException(nameof(sampleRateHz));
        _window = Math.Max(1, (int)Math.Round(sampleRateHz / lineHz));
        _buffer = new double[_window];
        SampleRateHz = sampleRateHz;
        LineHz = lineHz;
    }

    public double SampleRateHz { get; }
    public double LineHz { get; }
    /// <summary>窗口样本数（4 kSPS / 50 Hz → 80）。</summary>
    public int Window => _window;
    public string Version => $"period-avg/1 fs={SampleRateHz:F0} line={LineHz:F3} n={_window}";

    /// <summary>用首个有效样本填满窗口（常数输入立即稳态）。</summary>
    public void Initialize(double x0)
    {
        if (!double.IsFinite(x0)) { Reset(); return; }
        Array.Fill(_buffer, x0);
        _sum = x0 * _window;
        _index = 0;
        _primed = true;
    }

    public void Reset()
    {
        Array.Clear(_buffer);
        _sum = 0;
        _index = 0;
        _primed = false;
    }

    public double Step(double x)
    {
        if (!double.IsFinite(x)) return double.NaN;
        if (!_primed) Initialize(x);
        _sum -= _buffer[_index];
        _buffer[_index] = x;
        _sum += x;
        _index = (_index + 1) % _window;
        return _sum / _window;
    }
}
