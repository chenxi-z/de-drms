using Drms.Core.Filter;
using Xunit;
using Xunit.Abstractions;

namespace Drms.Core.Tests;

/// <summary>
/// 逐样本滤波链路：三模式、重置条件与建立期。
/// 依据：上位机实现要求 §1（三选项互斥）、§5（重置与建立）、§7.1/§7.6。
/// </summary>
public class SampleFilterChainTests
{
    private readonly ITestOutputHelper _output;
    public SampleFilterChainTests(ITestOutputHelper output) => _output = output;

    private static SampleFilterChain MakeChain(FilterMode mode = FilterMode.MainsNotch,
                                               double fs = 4000, double establish = 2.0)
    {
        var chain = new SampleFilterChain();
        chain.Configure(fs, new FilterSettings(mode, 50, FilterSettings.DefaultHarmonics, 2.0, establish));
        return chain;
    }

    [Fact]
    public void FirstSampleInitialisesToSteadyState()
    {
        SampleFilterChain chain = MakeChain();
        SampleFilterChain.Result r = chain.Process(100, 15300, valid: true);
        Assert.False(r.Reset);
        Assert.True(r.Establishing);
        Assert.Equal(15300, r.Value, 9);      // 首样本即稳态，不产生跳变

        for (ulong i = 101; i < 200; i++)
        {
            SampleFilterChain.Result next = chain.Process(i, 15300, valid: true);
            Assert.True(Math.Abs(next.Value - 15300) / 15300 < 1e-10, $"第 {i} 步偏离 {next.Value - 15300:E3}");
        }
    }

    [Fact]
    public void BypassReturnsInputUnchanged()
    {
        SampleFilterChain chain = MakeChain(FilterMode.Bypass);
        double[] input = [15300, 15301, 15299, 15350, 15200];
        for (ulong i = 0; i < (ulong)input.Length; i++)
        {
            SampleFilterChain.Result r = chain.Process(1000 + i, input[i], valid: true);
            Assert.Equal(input[i], r.Value);
        }
    }

    [Fact]
    public void EstablishmentEndsAfterTheConfiguredWindow()
    {
        SampleFilterChain chain = MakeChain(establish: 0.1);   // 0.1 s = 400 样本
        Assert.True(chain.Process(1, 15000, true).Establishing);
        for (ulong i = 2; i <= 400; i++) chain.Process(i, 15000, true);
        SampleFilterChain.Result after = chain.Process(401, 15000, true);
        Assert.False(after.Establishing);
    }

    [Theory]
    [InlineData("gap")]
    [InlineData("invalid")]
    [InlineData("disorder")]
    public void ResetReasonsAreDetectedAndReported(string kind)
    {
        SampleFilterChain chain = MakeChain(establish: 0.01);
        for (ulong i = 1; i <= 50; i++) chain.Process(i, 15000, true);
        int before = chain.ResetCount;

        ulong next = kind == "disorder" ? 5UL : 52UL;
        bool valid = kind != "invalid";
        SampleFilterChain.Result r = chain.Process(next, 15000, valid);

        Assert.True(r.Reset, $"{kind} 未触发重置");
        Assert.Equal(before + 1, chain.ResetCount);
        Assert.True(r.Establishing);
        Assert.False(string.IsNullOrEmpty(r.ResetReason));
        _output.WriteLine($"{kind}: {r.ResetReason}");

        // 恢复：下一个连续有效样本重新初始化，输出有限值
        SampleFilterChain.Result recovered = chain.Process(next + 1, 15010, true);
        Assert.True(double.IsFinite(recovered.Value));
        Assert.True(recovered.Establishing);
    }

    [Fact]
    public void SequenceGapDoesNotBridgeOldAndNewData()
    {
        SampleFilterChain chain = MakeChain(establish: 0);
        for (ulong i = 1; i <= 10; i++) chain.Process(i, 15000, true);
        // 缺口后直接给一个差异很大的值：若跨缺口拼接，输出会带上旧状态
        SampleFilterChain.Result r = chain.Process(20, 20000, valid: true);
        Assert.True(r.Reset);
        SampleFilterChain.Result next = chain.Process(21, 20000, valid: true);
        Assert.True(Math.Abs(next.Value - 20000) / 20000 < 1e-10);   // 新状态从 x0 重新初始化
    }

    [Fact]
    public void RateChangeRebuildsCoefficientsAndResets()
    {
        SampleFilterChain chain = MakeChain();
        for (ulong i = 1; i <= 100; i++) chain.Process(i, 15000, true);
        int before = chain.ResetCount;
        chain.Configure(8000, new FilterSettings(FilterMode.MainsNotch, 50, FilterSettings.DefaultHarmonics, 2.0, 2.0));
        Assert.Equal(before + 1, chain.ResetCount);
        Assert.Equal(8000, chain.SampleRateHz);
        // 8 kSPS 下系数按新 fs 重算：解析频响在 50 Hz 处必须仍然很深
        var probe = new MainsNotchBank(8000, 50, FilterSettings.DefaultHarmonics, 2.0);
        Assert.True(probe.ResponseDb(50) < -40);
        SampleFilterChain.Result r = chain.Process(1, 15000, true);   // 新采集代次从序号 1 重新开始
        Assert.False(r.Reset);
        Assert.True(r.Establishing);
    }

    [Fact]
    public void ModeChangeIsMutuallyExclusiveAndResets()
    {
        SampleFilterChain chain = MakeChain(FilterMode.MainsNotch);
        for (ulong i = 1; i <= 100; i++) chain.Process(i, 15000, true);
        chain.Configure(4000, new FilterSettings(FilterMode.PeriodAverage, 50, FilterSettings.DefaultHarmonics, 2.0, 2.0));
        Assert.Equal(FilterMode.PeriodAverage, chain.Mode);
        Assert.Contains("周期平均", chain.Describe());
        SampleFilterChain.Result r = chain.Process(1, 15000, true);
        Assert.True(Math.Abs(r.Value - 15000) / 15000 < 1e-10);
    }

    [Fact]
    public void MainsToneIsRemovedFromTheChainOutput()
    {
        SampleFilterChain chain = MakeChain(establish: 1.0);
        double fs = 4000, amp = 500;
        double peak = 0;
        for (ulong i = 0; i < 4 * 4000; i++)
        {
            double x = 15300 + amp * Math.Sin(2 * Math.PI * 50 * i / fs);
            SampleFilterChain.Result r = chain.Process(1000 + i, x, true);
            if (!r.Establishing) peak = Math.Max(peak, Math.Abs(r.Value - 15300));
        }
        double atten = 20 * Math.Log10(amp / Math.Max(peak, 1e-12));
        _output.WriteLine($"链路级 50 Hz 衰减 {atten:F1} dB（建立期后）");
        Assert.True(atten >= 40);
    }

    [Fact]
    public void PeriodAverageRemovesLineFrequency()
    {
        var avg = new PeriodAverageFilter(4000, 50);
        Assert.Equal(80, avg.Window);
        avg.Initialize(1000);
        double peak = 0;
        for (int i = 0; i < 8000; i++)
        {
            double y = avg.Step(1000 + 100 * Math.Sin(2 * Math.PI * 50 * i / 4000.0));
            if (i > 800) peak = Math.Max(peak, Math.Abs(y - 1000));
        }
        Assert.True(peak < 0.01, $"周期平均对 50 Hz 的残余 {peak:F4}");
    }

    [Fact]
    public void PeriodAverageStepResponseIsARamp()
    {
        // 滑动平均对阶跃的响应是长度为一个周期的斜坡（群延迟半周期）
        var avg = new PeriodAverageFilter(4000, 50);
        avg.Initialize(0);
        var values = new List<double>();
        for (int i = 0; i < 160; i++) values.Add(avg.Step(100));
        Assert.Equal(100.0 * 40 / 80, values[39], 6);   // 半窗处约 50
        Assert.Equal(100.0, values[159], 6);            // 一窗后到达
    }

    [Fact]
    public void NaNFromFilterMarksReset()
    {
        SampleFilterChain chain = MakeChain(establish: 0.01);
        for (ulong i = 1; i <= 10; i++) chain.Process(i, 15000, true);
        SampleFilterChain.Result r = chain.Process(11, double.NaN, valid: true);
        Assert.True(r.Reset);
        Assert.True(double.IsNaN(r.Value));
        Assert.False(string.IsNullOrEmpty(r.ResetReason));
    }
}
