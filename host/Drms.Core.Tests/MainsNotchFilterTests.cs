using Drms.Core.Filter;
using Xunit;
using Xunit.Abstractions;

namespace Drms.Core.Tests;

/// <summary>
/// 工频谐波陷波器组：系数、稳定性与频响。
/// 依据：W3C Audio EQ Cookbook notch + 上位机实现要求 §3/§7。
/// </summary>
public class MainsNotchFilterTests
{
    private readonly ITestOutputHelper _output;
    public MainsNotchFilterTests(ITestOutputHelper output) => _output = output;

    private static MainsNotchBank DefaultBank(double fs = 4000, double line = 50, double b = 2)
        => new(fs, line, FilterSettings.DefaultHarmonics, b);

    [Fact]
    public void CoefficientsMatchTheReferenceSample()
    {
        // 规格 §3 的数值核对样例（fs=4000, f=50, B=2）——逐位比对，不做宽松比较
        MainsNotchBank bank = DefaultBank();
        MainsNotchBank.Stage s = bank.Stages[0];
        Assert.Equal(0.998433276559531, s.B0, 15);
        Assert.Equal(-1.990710879956317, s.B1, 15);
        Assert.Equal(0.998433276559531, s.B2, 15);
        Assert.Equal(-1.990710879956317, s.A1, 15);
        Assert.Equal(0.996866553119062, s.A2, 15);
        Assert.Equal(50.0, s.CenterHz, 12);
    }

    [Theory]
    [InlineData(1, 50.0)] [InlineData(2, 100.0)] [InlineData(3, 150.0)] [InlineData(5, 250.0)]
    public void HarmonicCentersFollowTheMultipliers(int multiplier, double expectedHz)
    {
        MainsNotchBank bank = DefaultBank();
        int index = FilterSettings.DefaultHarmonics.ToList().IndexOf(multiplier);
        Assert.True(index >= 0);
        Assert.Equal(expectedHz, bank.Stages[index].CenterHz, 9);
    }

    [Fact]
    public void AllPolesLieStrictlyInsideTheUnitCircle()
    {
        foreach (double fs in new[] { 1000.0, 4000.0, 16000.0 })
        foreach (double b in new[] { 0.5, 2.0, 10.0 })
        {
            MainsNotchBank bank = new(fs, 50, FilterSettings.DefaultHarmonics, b);
            Assert.True(bank.IsStable(), $"fs={fs} B={b} 极点不稳定");
            foreach (MainsNotchBank.Stage s in bank.Stages)
            {
                Assert.True(Math.Abs(s.A2) < 1.0);
                Assert.True(Math.Abs(s.A1) < 1.0 + s.A2);
            }
        }
    }

    [Theory]
    [InlineData(4000.0, 50.0, 2.0)]
    [InlineData(8000.0, 50.0, 2.0)]
    [InlineData(1000.0, 60.0, 1.0)]
    public void ConfigurationBoundsAreEnforced(double fs, double line, double b)
    {
        // 合法：所有谐波都在 (0, fs/2) 内
        _ = new MainsNotchBank(fs, line, [1, 2, 3], b);
        // Nyquist 及以上的谐波必须拒绝
        Assert.Throws<ArgumentOutOfRangeException>(() => new MainsNotchBank(4000, 50, [40], 2));  // 2000 Hz = Nyquist
        Assert.Throws<ArgumentOutOfRangeException>(() => new MainsNotchBank(4000, 50, [41], 2));
        // B 必须 > 0
        Assert.Throws<ArgumentOutOfRangeException>(() => new MainsNotchBank(4000, 50, [1], 0));
        // 倍数必须为正
        Assert.Throws<ArgumentOutOfRangeException>(() => new MainsNotchBank(4000, 50, [0], 2));
    }

    [Fact]
    public void ConstantInputStaysConstantFromTheFirstSample()
    {
        MainsNotchBank bank = DefaultBank();
        bank.Initialize(15300.0);
        for (int i = 0; i < 4000; i++)
        {
            double y = bank.Step(15300.0);
            // 初始化到稳态：只允许浮点累积误差（相对 1e-10 以内），不允许可见跳变
            Assert.True(Math.Abs(y - 15300.0) / 15300.0 < 1e-10, $"第 {i} 步偏离 {y - 15300.0:E3}");
        }
    }

    [Fact]
    public void ZeroStateStartWouldOvershootButInitializeAvoidsIt()
    {
        // 反证：从零状态启动会有建立过程（这条测试固定住"初始化不是可选项"这一事实）
        MainsNotchBank bank = DefaultBank();
        bank.Reset();
        double maxDeviation = 0;
        for (int i = 0; i < 400; i++)
            maxDeviation = Math.Max(maxDeviation, Math.Abs(bank.Step(15300.0) - 15300.0));
        Assert.True(maxDeviation > 1.0, $"零状态启动未体现建立过程（最大偏差 {maxDeviation:F3}）");
    }

    [Fact]
    public void BlockAndPointProcessingAreIdentical()
    {
        double[] input = new double[4000];
        var rng = new Random(1234);
        for (int i = 0; i < input.Length; i++)
            input[i] = 15000 + 100 * Math.Sin(2 * Math.PI * 3 * i / 4000.0) + rng.NextDouble() - 0.5;

        MainsNotchBank block = DefaultBank();
        block.Initialize(input[0]);
        double[] whole = block.Process(input);

        MainsNotchBank point = DefaultBank();
        point.Initialize(input[0]);
        var piecewise = new double[input.Length];
        int pos = 0;
        // 随机包长切分：验证"状态跨包保留、按序号逐点执行"
        while (pos < input.Length)
        {
            int len = Math.Min(rng.Next(1, 400), input.Length - pos);
            for (int i = 0; i < len; i++) piecewise[pos + i] = point.Step(input[pos + i]);
            pos += len;
        }
        Assert.Equal(whole, piecewise);
    }

    [Fact]
    public void CenterFrequencyIsDeeplyAttenuated()
    {
        foreach (int multiplier in FilterSettings.DefaultHarmonics)
        {
            double f = multiplier * 50.0;
            MainsNotchBank bank = DefaultBank();
            double fs = 4000, amplitude = 1000;
            // 稳态幅度：先跑 2 s 建立，再取随后 1 s 的 RMS
            bank.Initialize(amplitude * Math.Sin(0));
            double peak = 0;
            int settle = (int)(2 * fs);
            for (int i = 0; i < settle + 4000; i++)
            {
                double y = bank.Step(amplitude * Math.Sin(2 * Math.PI * f * i / fs));
                if (i >= settle) peak = Math.Max(peak, Math.Abs(y));
            }
            double attenDb = 20 * Math.Log10(amplitude / Math.Max(peak, 1e-12));
            _output.WriteLine($"{f,6:F0} Hz 峰值衰减 {attenDb,7:F1} dB");
            Assert.True(attenDb >= 40, $"{f} Hz 衰减只有 {attenDb:F1} dB（要求 ≥40 dB）");
        }
    }

    [Theory]
    [InlineData(0.05)] [InlineData(-0.05)]
    [InlineData(0.1)] [InlineData(-0.1)]
    [InlineData(0.5)] [InlineData(-0.5)]
    public void OffCenterAttenuationIsReported(double offsetHz)
    {
        double fs = 4000, f = 50 + offsetHz, amplitude = 1000;
        MainsNotchBank bank = DefaultBank();
        double analytic = -20 * Math.Log10(bank.MagnitudeResponse(f));   // 正值 = 衰减 dB
        bank.Initialize(0);
        double peak = 0;
        int settle = (int)(3 * fs);
        for (int i = 0; i < settle + 4000; i++)
        {
            double y = bank.Step(amplitude * Math.Sin(2 * Math.PI * f * i / fs));
            if (i >= settle) peak = Math.Max(peak, Math.Abs(y));
        }
        double empirical = 20 * Math.Log10(amplitude / Math.Max(peak, 1e-12));
        _output.WriteLine($"偏移 {offsetHz:+0.00;-0.00} Hz：解析衰减 {analytic:F1} dB，实测衰减 {empirical:F1} dB");
        // 解析与实测应一致到 1 dB 以内（实测受 4 s 观测窗限制）
        Assert.True(Math.Abs(analytic - empirical) < 1.0,
            $"解析 {analytic:F2} dB 与实测 {empirical:F2} dB 相差过大");
        // 偏移越大衰减越弱：0.05 Hz 仍应显著，0.5 Hz 明显变弱
        Assert.True(analytic > 3.0, $"偏移 {offsetHz} Hz 时几乎无衰减（{analytic:F1} dB）");
    }

    [Fact]
    public void NonFiniteInputDoesNotPoisonState()
    {
        MainsNotchBank bank = DefaultBank();
        bank.Initialize(15000);
        Assert.True(double.IsNaN(bank.Step(double.NaN)));
        // 状态未被 NaN 污染：重新初始化后仍能正常输出
        bank.Initialize(15000);
        Assert.Equal(15000, bank.Step(15000), 9);
    }

    [Fact]
    public void BroadbandNoiseIsLargelyPreserved()
    {
        // 陷波器不应把非工频成分一起砍掉：3 Hz 正弦应基本无衰减
        MainsNotchBank bank = DefaultBank();
        double amplitude = 1000, fs = 4000, f = 3;
        bank.Initialize(0);
        double peak = 0;
        int settle = (int)(2 * fs);
        for (int i = 0; i < settle + 4000; i++)
        {
            double y = bank.Step(amplitude * Math.Sin(2 * Math.PI * f * i / fs));
            if (i >= settle) peak = Math.Max(peak, Math.Abs(y));
        }
        double gainDb = 20 * Math.Log10(peak / amplitude);
        _output.WriteLine($"3 Hz 通带增益 {gainDb:F2} dB");
        Assert.True(gainDb > -0.5, $"3 Hz 被衰减了 {gainDb:F2} dB（陷波器不应压通带）");
    }
}
