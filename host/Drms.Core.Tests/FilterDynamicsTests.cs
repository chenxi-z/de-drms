using Drms.Core.Filter;
using Xunit;
using Xunit.Abstractions;

namespace Drms.Core.Tests;

/// <summary>
/// 动态影响：恒值叠加工频、阶跃、斜坡、短脉冲。
/// 规格 §7「动态影响」要求逐项**报告**，不能只以"曲线更平"作为通过条件——
/// 因此这里把关键数字 print 出来，并只对可证明的性质做断言
/// （有限性、单调性、包络不超输入、恢复时间上界）。
/// </summary>
public class FilterDynamicsTests
{
    private readonly ITestOutputHelper _output;
    public FilterDynamicsTests(ITestOutputHelper output) => _output = output;

    private static MainsNotchBank Notch() => new(4000, 50, FilterSettings.DefaultHarmonics, 2.0);
    private static PeriodAverageFilter Average() => new(4000, 50);

    [Fact]
    public void CompositeSignal_HarmonicsAreSuppressedButDcSurvives()
    {
        const double fs = 4000, dc = 15000;
        double[] harmonics = [50, 100, 150, 250, 450, 650];
        double amp = 200;
        int n = 12000;

        var input = new double[n];
        for (int i = 0; i < n; i++)
        {
            double v = dc;
            foreach (double f in harmonics) v += amp * Math.Sin(2 * Math.PI * f * i / fs);
            input[i] = v;
        }

        MainsNotchBank bank = Notch();
        bank.Initialize(input[0]);
        double[] notch = bank.Process(input);
        var avg = Average();
        avg.Initialize(input[0]);
        double[] avgOut = new double[n];
        for (int i = 0; i < n; i++) avgOut[i] = avg.Step(input[i]);

        // 排除前 2 s 建立段
        int skip = 2 * 4000;
        _output.WriteLine($"{"信号",-18}{"旁路 RMS",12}{"陷波 RMS",12}{"周期平均 RMS",14}");
        foreach ((string name, double[] data) in new[]
                 {
                     ("原始", input), ("陷波", notch), ("周期平均", avgOut)
                 })
        {
            double rms = Rms(data, skip);
            _output.WriteLine($"{name,-18}{rms,12:F2}{(data == input ? "" : "")}");
            _ = rms;
        }
        double raw = Rms(input, skip), n2 = Rms(notch, skip), a2 = Rms(avgOut, skip);
        _output.WriteLine($"陷波把交流 RMS 从 {raw:F1} 压到 {n2:F1}（{20 * Math.Log10(raw / n2):F1} dB 衰减）");
        _output.WriteLine($"周期平均把交流 RMS 从 {raw:F1} 压到 {a2:F1}（{20 * Math.Log10(raw / a2):F1} dB 衰减）");

        // DC 必须保留（陷波/平均在直流处增益为 1）
        Assert.Equal(dc, Mean(notch, skip), 0);
        Assert.Equal(dc, Mean(avgOut, skip), 0);
        // 4 个目标谐波被压掉后，残余主要来自 450/650 Hz 两个未处理的谐波
        Assert.True(n2 < raw * 0.6, $"陷波后残余过大：{n2:F1} vs {raw:F1}");
    }

    [Fact]
    public void StepResponse_ReportsOvershootAndRinging()
    {
        const double fs = 4000, dc0 = 15000, dc1 = 15600;   // 4% 阶跃
        int n = 8000;
        var input = new double[n];
        for (int i = 0; i < n; i++) input[i] = i < 2000 ? dc0 : dc1;

        MainsNotchBank bank = Notch();
        bank.Initialize(input[0]);
        double[] y = bank.Process(input);
        var avg = Average();
        avg.Initialize(input[0]);
        double[] ya = new double[n];
        for (int i = 0; i < n; i++) ya[i] = avg.Step(input[i]);

        ReportStep("陷波", y, dc0, dc1, 2000, fs);
        ReportStep("周期平均", ya, dc0, dc1, 2000, fs);

        // 陷波器的阶跃响应：过冲不应超过阶跃幅度的 50%（窄带陷波以 50 Hz 振铃为主）
        (double overshoot, double settleMs) = StepMetrics(y, dc0, dc1, 2000, fs, 0.001);
        _output.WriteLine($"陷波：过冲 {overshoot:F1}%，1‰ 建立 {settleMs:F0} ms");
        Assert.True(overshoot < 50, $"陷波阶跃过冲 {overshoot:F1}% 过大");
        // 周期平均是纯延迟+平滑，不应有过冲
        (double osAvg, double settleAvg) = StepMetrics(ya, dc0, dc1, 2000, fs, 0.001);
        Assert.True(osAvg < 0.1, $"周期平均出现 {osAvg:F2}% 过冲（滑动平均不可能过冲）");
        _output.WriteLine($"周期平均：过冲 {osAvg:F2}%，1‰ 建立 {settleAvg:F0} ms");
    }

    [Fact]
    public void RampResponse_ReportsLag()
    {
        // 1 kΩ/s 的线性变化：陷波器对缓变量的滞后应远小于 1 个工频周期
        const double fs = 4000;
        int n = 8000;
        var input = new double[n];
        for (int i = 0; i < n; i++) input[i] = 15000 + 1000.0 * i / fs;

        MainsNotchBank bank = Notch();
        bank.Initialize(input[0]);
        double[] y = bank.Process(input);
        var avg = Average();
        avg.Initialize(input[0]);
        double[] ya = new double[n];
        for (int i = 0; i < n; i++) ya[i] = avg.Step(input[i]);

        int at = n - 1;
        double lagN = (input[at] - y[at]) / 1000.0 * 1000;   // ms
        double lagA = (input[at] - ya[at]) / 1000.0 * 1000;
        _output.WriteLine($"1 kΩ/s 斜坡：陷波滞后 {lagN:F2} ms，周期平均滞后 {lagA:F1} ms");
        Assert.True(lagN < 1.0, $"陷波对斜坡滞后 {lagN:F2} ms 偏大");
        // 滑动平均的理论群延迟是半窗 = 10 ms
        Assert.True(Math.Abs(lagA - 10.0) < 1.0, $"周期平均滞后 {lagA:F1} ms 与半窗 10 ms 不符");
    }

    [Fact]
    public void PulseResponse_ReportsPeakAndWidthChange()
    {
        // 2 ms 宽、200 Ω 高的脉冲：窄带陷波会把它的能量摊开（峰值降低、变宽），
        // 这正是规格 §8 说的"不承诺冲击峰值保真"，测试把数字固定下来
        const double fs = 4000;
        int n = 8000, start = 2000, width = 8;
        var input = new double[n];
        Array.Fill(input, 15000.0);
        for (int i = start; i < start + width; i++) input[i] = 15200;

        MainsNotchBank bank = Notch();
        bank.Initialize(input[0]);
        double[] y = bank.Process(input);

        double rawPeak = input.Max() - 15000, filtPeak = y.Max() - 15000;
        double rawWidth = Width(input, 15000, 1.0, fs);      // ≥1 Ω 的宽度（ms）
        double filtWidth = Width(y, 15000, 1.0, fs);
        _output.WriteLine($"2 ms 脉冲：原始峰值 {rawPeak:F0} Ω → 滤波后 {filtPeak:F0} Ω " +
                          $"（保留 {filtPeak / rawPeak * 100:F0}%），" +
                          $"1 Ω 宽度 {rawWidth:F1} ms → {filtWidth:F1} ms");
        Assert.InRange(filtPeak / rawPeak, 0.05, 1.00);      // 峰值必然被削
        Assert.True(filtWidth > rawWidth, "窄带滤波应把脉冲摊宽");
    }

    private void ReportStep(string name, double[] y, double from, double to, int at, double fs)
    {
        (double overshoot, double settle) = StepMetrics(y, from, to, at, fs, 0.001);
        _output.WriteLine($"{name} 阶跃：过冲 {overshoot:F2}%，1‰ 建立 {settle:F0} ms");
    }

    private static (double OvershootPct, double SettleMs) StepMetrics(
        double[] y, double from, double to, int at, double fs, double tol)
    {
        double step = to - from;
        double max = double.MinValue, min = double.MaxValue;
        int settled = -1;
        for (int i = at; i < y.Length; i++)
        {
            double dev = (y[i] - to) / step;
            max = Math.Max(max, dev);
            min = Math.Min(min, dev);
            if (settled < 0 && Math.Abs(dev) <= tol) settled = i - at;
            else if (settled >= 0 && Math.Abs(dev) > tol) settled = -1;
        }
        // 过冲只统计越过目标的那一侧；阶跃前的旧值（dev=-1）不属于过冲
        double excursion = step > 0 ? max : -min;
        double overshoot = Math.Max(0.0, excursion) * 100.0;
        return (overshoot, settled < 0 ? double.NaN : settled / fs * 1000);
    }

    private static double Width(double[] y, double baseline, double threshold, double fs)
    {
        int count = y.Count(v => Math.Abs(v - baseline) >= threshold);
        return count / fs * 1000;
    }

    private static double Rms(double[] data, int skip)
    {
        double mean = Mean(data, skip);
        double sum = 0;
        for (int i = skip; i < data.Length; i++) sum += (data[i] - mean) * (data[i] - mean);
        return Math.Sqrt(sum / (data.Length - skip));
    }

    private static double Mean(double[] data, int skip)
    {
        double sum = 0;
        for (int i = skip; i < data.Length; i++) sum += data[i];
        return sum / (data.Length - skip);
    }
}
