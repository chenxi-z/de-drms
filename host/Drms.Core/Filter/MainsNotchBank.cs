using System.Globalization;

namespace Drms.Core.Filter;

/// <summary>
/// 工频谐波陷波器组：若干级 biquad（notch，TDF-II）级联，按样本序号逐点处理。
///
/// 依据：W3C Audio EQ Cookbook 的 notch 类型；
///   Q = f_i / B（近似指定带宽，准确频响以实际系数为准）
///   ω = 2π f_i / fs,  α = sin ω / (2Q)
///   b0 = 1/(1+α), b1 = -2cos ω/(1+α), b2 = b0, a1 = b1, a2 = (1-α)/(1+α)
///
/// 数**值**约定（接入任何 DSP 库前必须核对）：
///   递推 y[n] = b0x[n] + b1x[n-1] + b2x[n-2] − a1y[n-1] − a2y[n-2]，
///   即反馈项是**减** a1y、a2y；部分库用相反符号。
///
/// 线程模型：单线程调用（RAW 读线程或离线分析）。不是线程安全的。
/// </summary>
public sealed class MainsNotchBank
{
    /// <summary>一级 biquad 的归一化系数（a0 恒为 1）。</summary>
    public readonly record struct Stage(
        double CenterHz, double B0, double B1, double B2, double A1, double A2)
    {
        public override string ToString() => string.Create(CultureInfo.InvariantCulture,
            $"f={CenterHz:F3}Hz b0={B0:F15} b1={B1:F15} b2={B2:F15} a1={A1:F15} a2={A2:F15}");
    }

    private readonly Stage[] _stages;
    private readonly double[] _z1;
    private readonly double[] _z2;

    /// <summary>按配置计算系数（仅在配置改变时调用；逐点计算三角函数是不允许的）。</summary>
    public MainsNotchBank(double sampleRateHz, double lineHz, IReadOnlyList<int> multipliers, double bandwidthHz)
    {
        if (sampleRateHz <= 0 || !double.IsFinite(sampleRateHz))
            throw new ArgumentOutOfRangeException(nameof(sampleRateHz));
        if (lineHz <= 0 || !double.IsFinite(lineHz))
            throw new ArgumentOutOfRangeException(nameof(lineHz));
        if (bandwidthHz <= 0 || !double.IsFinite(bandwidthHz))
            throw new ArgumentOutOfRangeException(nameof(bandwidthHz), "B 必须 > 0");
        if (multipliers is null || multipliers.Count == 0)
            throw new ArgumentOutOfRangeException(nameof(multipliers), "至少一级");

        SampleRateHz = sampleRateHz;
        LineHz = lineHz;
        BandwidthHz = bandwidthHz;

        var stages = new Stage[multipliers.Count];
        for (int i = 0; i < multipliers.Count; i++)
        {
            int m = multipliers[i];
            if (m <= 0) throw new ArgumentOutOfRangeException(nameof(multipliers), "谐波倍数必须为正");
            double f = m * lineHz;
            // 边界：0 < f < fs/2（Nyquist 以上无意义，等于 fs/2 会退化）
            if (!(f > 0 && f < sampleRateHz / 2))
                throw new ArgumentOutOfRangeException(nameof(multipliers),
                    $"第 {m} 次谐波 {f:F1} Hz 不在 (0, {sampleRateHz / 2:F0}) 内");
            double q = f / bandwidthHz;
            double w = 2.0 * Math.PI * f / sampleRateHz;
            double alpha = Math.Sin(w) / (2.0 * q);
            double b0 = 1.0 / (1.0 + alpha);
            double b1 = -2.0 * Math.Cos(w) / (1.0 + alpha);
            double a2 = (1.0 - alpha) / (1.0 + alpha);
            stages[i] = new Stage(f, b0, b1, b0, b1, a2);
        }
        _stages = stages;
        _z1 = new double[stages.Length];
        _z2 = new double[stages.Length];
    }

    public double SampleRateHz { get; }
    public double LineHz { get; }
    public double BandwidthHz { get; }
    public IReadOnlyList<Stage> Stages => _stages;
    public int StageCount => _stages.Length;

    /// <summary>算法版本标识，写进导出文件元数据。</summary>
    public string Version => string.Create(CultureInfo.InvariantCulture,
        $"mains-notch/1 fs={SampleRateHz:F0} line={LineHz:F3} B={BandwidthHz:F3} n={StageCount}");

    /// <summary>用首个有效样本初始化各级状态（恒定输入的稳态，避免从零启动的大跳变）。</summary>
    public void Initialize(double x0)
    {
        if (!double.IsFinite(x0)) { Reset(); return; }
        for (int i = 0; i < _stages.Length; i++)
        {
            Stage s = _stages[i];
            _z1[i] = (1.0 - s.B0) * x0;
            _z2[i] = (s.B2 - s.A2) * x0;
        }
    }

    /// <summary>清空为全零状态（下一帧前必须先 Initialize，否则会从 0 起振）。</summary>
    public void Reset()
    {
        Array.Clear(_z1);
        Array.Clear(_z2);
    }

    /// <summary>逐点处理。非有限输入返回 NaN 并由调用方决定重置（这里不静默改状态）。</summary>
    public double Step(double x)
    {
        if (!double.IsFinite(x)) return double.NaN;
        double y = x;
        for (int i = 0; i < _stages.Length; i++)
        {
            Stage s = _stages[i];
            double z1 = _z1[i], z2 = _z2[i];
            double outY = s.B0 * y + z1;
            _z1[i] = s.B1 * y - s.A1 * outY + z2;
            _z2[i] = s.B2 * y - s.A2 * outY;
            y = outY;
        }
        return y;
    }

    /// <summary>整块处理（测试与离线分析用；语义与逐点完全一致）。</summary>
    public double[] Process(ReadOnlySpan<double> input)
    {
        var output = new double[input.Length];
        for (int i = 0; i < input.Length; i++) output[i] = Step(input[i]);
        return output;
    }

    /// <summary>极点是否全部严格位于单位圆内（|a2|&lt;1 且 |a1|&lt;1+a2）。</summary>
    public bool IsStable()
    {
        foreach (Stage s in _stages)
        {
            if (!(Math.Abs(s.A2) < 1.0)) return false;
            if (!(Math.Abs(s.A1) < 1.0 + s.A2)) return false;
        }
        return true;
    }

    /// <summary>
    /// 单级在某频率处的幅度响应（测试与报告用）。返回线性幅度（1 = 无衰减）。
    /// 用解析式，不做逐点仿真。
    /// </summary>
    public static double MagnitudeAt(in Stage s, double sampleRateHz, double frequencyHz)
    {
        double w = 2.0 * Math.PI * frequencyHz / sampleRateHz;
        // H(e^{jw}) 的分子/分母（复数）
        var num = new Complex2(s.B0, 0)
            + new Complex2(s.B1, 0) * new Complex2(Math.Cos(w), -Math.Sin(w))
            + new Complex2(s.B2, 0) * new Complex2(Math.Cos(2 * w), -Math.Sin(2 * w));
        var den = new Complex2(1, 0)
            + new Complex2(s.A1, 0) * new Complex2(Math.Cos(w), -Math.Sin(w))
            + new Complex2(s.A2, 0) * new Complex2(Math.Cos(2 * w), -Math.Sin(2 * w));
        return num.Magnitude / den.Magnitude;
    }

    /// <summary>整个级联在某频率处的幅度响应。</summary>
    public double MagnitudeResponse(double frequencyHz)
    {
        double m = 1.0;
        foreach (Stage s in _stages) m *= MagnitudeAt(s, SampleRateHz, frequencyHz);
        return m;
    }

    /// <summary>幅度响应换算成 dB。</summary>
    public double ResponseDb(double frequencyHz) => 20.0 * Math.Log10(MagnitudeResponse(frequencyHz));

    /// <summary>极简复数，避免为此引入 System.Numerics 依赖差异。</summary>
    private readonly record struct Complex2(double Re, double Im)
    {
        public static Complex2 operator +(Complex2 a, Complex2 b) => new(a.Re + b.Re, a.Im + b.Im);
        public static Complex2 operator *(Complex2 a, Complex2 b)
            => new(a.Re * b.Re - a.Im * b.Im, a.Re * b.Im + a.Im * b.Re);
        public double Magnitude => Math.Sqrt(Re * Re + Im * Im);
    }
}
