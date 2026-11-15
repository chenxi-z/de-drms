using Drms.Core.Config;
using Drms.Core.Protocol;
using Drms.Core.Session;
using Drms.Core.Transport;

// 端到端验证：下发配置 → 建立基线 R0 → 确认 ratio 开始发布。
// 这是"用户要能看到 R/R0 曲线"的最小闭环。

// measure 模式：连续采集若干点做统计，用来判断当前被测物的阻值与稳定性。
if (args.Length > 0 && args[0] == "measure")
{
    return await MeasureAsync(args.Length > 1 ? args[1] : "COM5",
                              args.Length > 2 && int.TryParse(args[2], out int n) ? n : 300);
}

string port = args.Length > 0 ? args[0] : "COM5";
ulong windowUs = args.Length > 1 && ulong.TryParse(args[1], out ulong w) ? w * 1_000_000UL : 10_000_000UL;
// 第 3 个参数可覆盖 CV 限值（%）。默认 0.1%。临时放宽只用于验证软件流程，
// 用它建出的 R0 没有物理意义，不能当测量结果。
double cvLimitPct = args.Length > 2 && double.TryParse(args[2], out double c) ? c : 0.1;

Console.WriteLine($"=== 连接 {port} ===");
using var link = new SerialByteLink(port);
using var session = new DeviceSession(link) { RequestTimeout = TimeSpan.FromSeconds(5) };
session.Diagnostic += m => Console.WriteLine($"  [诊断] {m}");
session.Start();

HelloReply hello = session.Handshake();
Console.WriteLine($"UID={hello.UidText} session={session.SessionId} boot=0x{hello.Boot:X16}");

StatusReply st = session.GetStatus();
Console.WriteLine($"初始: acq={st.Acquisition} rate={st.Rate} fresh={st.Fresh} " +
                  $"baselineVer={st.BaselineVersion} runningVer={st.RunningVersion}");

if (st.Acquisition == Acquisition.Reference)
{
    Console.WriteLine("\n⚠ 设备在 REF 模式（参考支路），建立基线与判级都不可用。");
    Console.WriteLine("  请先把设备切回样品测量（按 MEAS_BTN 或复位），然后重跑。");
    return 3;
}

// ---- 1. 下发完整配置 ----
Console.WriteLine("\n=== 1. 下发配置（区间表 + 基线策略）===");
var bands = new[]
{
    new IntervalBuilder.Band("绿", 0, 1.0, 0.2),
    new IntervalBuilder.Band("黄", 1, 3.0, 0.2),
    new IntervalBuilder.Band("橙", 2, 6.0, 0.2),
    new IntervalBuilder.Band("红", 3, 20.0, 0.2),
};
List<MonitorInterval> intervals = IntervalBuilder.FromPercentBands(bands, out List<string> problems);
if (problems.Count > 0)
{
    Console.WriteLine($"区间生成失败: {string.Join("; ", problems)}");
    return 4;
}
Console.WriteLine($"  区间 {intervals.Count} 条: " +
    string.Join(" ", intervals.Select(i => $"[{i.Low:F4},{i.High:F4})")));

DeviceConfig config = DeviceConfig.ConservativeDefault(intervals, windowUs,
    baselineMaxCv: cvLimitPct / 100.0);
byte[] settings = config.EncodeSettings();
Console.WriteLine($"  settings {settings.Length} 字节, baseline: min_count={config.BaselineMinCount} " +
                  $"min_us={config.BaselineMinUs} max_cv={config.BaselineMaxCv}");

ulong expected = 0;
try { expected = session.GetConfig().RunningVersion; }
catch (DeviceException ex) when (ex.Result == Result.Unsupported) { Console.WriteLine("  （出厂空配置，expected_version=0）"); }

ulong op = session.ApplyConfig(expected, settings);
Console.WriteLine($"  APPLY_CONFIG 受理 op={op}，等待终态…");
OperationReply applyFinal = await OperationWaiter.WaitAsync(session, op, TimeSpan.FromSeconds(20),
    TimeSpan.FromMilliseconds(400), (r, e) => Console.WriteLine($"    {e.TotalSeconds:F1}s phase={r.Phase}"));
Console.WriteLine($"  结果: {applyFinal.Result}" +
                  (applyFinal.Reason.HasValue ? $" / {applyFinal.Reason}" : ""));
if (applyFinal.Result != Result.Ok)
{
    Console.WriteLine("配置下发失败，中止。");
    return 5;
}

// 回读确认
ConfigReply cfg = session.GetConfig();
Console.WriteLine($"  回读: running_version={cfg.RunningVersion} settings={cfg.Settings.Length}B");
var f = cfg.Fields;
if (f.TryGetValue(Tag.Intervals, out TlvField? iv))
{
    var back = Messages.ParseIntervals(iv.Value);
    Console.WriteLine($"  区间回读 {back.Count} 条: " +
        string.Join(" ", back.Select(i => $"[{i.Low:F3},{i.High:F3})L{i.Level}")));
}

// ---- 2. 建立基线 ----
Console.WriteLine($"\n=== 2. 建立基线 R0（窗口 {windowUs / 1_000_000}s）===");
await Task.Delay(1500);
st = session.GetStatus();
Console.WriteLine($"  前置: acq={st.Acquisition} maintenance={st.Maintenance} fresh={st.Fresh}");
List<string> pre = BaselineRunner.CheckPreconditions(st, config.BaselineMinCount);
if (pre.Count > 0)
{
    Console.WriteLine($"  前置不满足: {string.Join("; ", pre)}");
    return 6;
}

// 实时统计：订阅曲线，同时喂给累加器
var acc = new BaselineAccumulator(config.BaselineMinCount, config.BaselineMinUs, config.BaselineMaxCv);
session.MeasurementReceived += ev =>
{
    if (!ev.Fresh || (ev.Quality & 1u) != 0 || !ev.Ohms.HasValue) return;
    acc.Feed(ev.Ohms.Value, BaselineAccumulator.SampleDtUs(st.Rate));
    if (acc.Count % 20 == 0)
        Console.WriteLine($"    [{acc.DurationUs / 1_000_000.0:F1}s] 样本={acc.Count} " +
                          $"均值={acc.Mean / 1000:F4}kOhm CV={(double.IsNaN(acc.Cv) ? 0 : acc.Cv * 100):F4}% " +
                          $"稳定={acc.IsStable}");
};
session.SubscribeCurve(100);

ulong baselineOp = session.BuildR0();
Console.WriteLine($"  BUILD_R0 受理 op={baselineOp}");
OperationReply baselineFinal = await OperationWaiter.WaitAsync(session, baselineOp,
    TimeSpan.FromMicroseconds(windowUs) + TimeSpan.FromSeconds(45),
    TimeSpan.FromMilliseconds(500),
    (r, e) => { if ((int)e.TotalSeconds % 5 == 0) Console.WriteLine($"    {e.TotalSeconds:F0}s phase={r.Phase}"); });
Console.WriteLine($"  基线结果: {baselineFinal.Result}" +
                  (baselineFinal.Reason.HasValue ? $" / {baselineFinal.Reason}" : ""));
Console.WriteLine($"  界面侧统计: 样本={acc.Count} 均值={acc.Mean / 1000:F4}kOhm " +
                  $"CV={(double.IsNaN(acc.Cv) ? 0 : acc.Cv * 100):F4}% 稳定={acc.IsStable}");

// ---- 3. 确认 ratio 开始发布 ----
Console.WriteLine("\n=== 3. 确认 R/R0 已发布 ===");
for (int i = 0; i < 6; i++)
{
    await Task.Delay(1000);
    st = session.GetStatus();
    Console.WriteLine($"  t+{i + 1}s: class={st.Classification} fresh={st.Fresh} " +
        $"ohms={(st.Ohms.HasValue ? st.Ohms.Value.ToString("F1") : "-")} " +
        $"ratio={(st.Ratio.HasValue ? st.Ratio.Value.ToString("F6") : "未发布")} " +
        $"level={(st.Level?.ToString() ?? "-")} baselineVer={st.BaselineVersion}");
}

return 0;

/// <summary>连续采集并统计。用来回答"这个电阻多大、稳不稳"。</summary>
static async Task<int> MeasureAsync(string port, int points)
{
    using var link = new SerialByteLink(port);
    using var session = new DeviceSession(link) { RequestTimeout = TimeSpan.FromSeconds(5) };
    session.MeasurementReceived += _ => { };
    session.Start();
    HelloReply hello = session.Handshake();
    Console.WriteLine($"UID={hello.UidText}");

    StatusReply st = session.GetStatus();
    Console.WriteLine($"acq={st.Acquisition} rate={st.Rate} fresh={st.Fresh} " +
                      $"ohms={(st.Ohms.HasValue ? st.Ohms.Value.ToString("F3") : "-")}");

    var values = new List<double>();
    var gate = new ManualResetEventSlim(false);
    session.MeasurementReceived += ev =>
    {
        if (ev.Ohms.HasValue && ev.Fresh && (ev.Quality & 1u) == 0)
            lock (values) values.Add(ev.Ohms.Value);
        if (values.Count >= points) gate.Set();
    };
    session.SubscribeCurve(100);
    Console.WriteLine($"订阅 100 ms/点，目标 {points} 点…");
    gate.Wait(TimeSpan.FromSeconds(120));

    double[] v;
    lock (values) v = values.ToArray();
    if (v.Length < 10) { Console.WriteLine($"只收到 {v.Length} 点，数据不足"); return 1; }

    double mean = v.Average();
    double sd = Math.Sqrt(v.Sum(x => (x - mean) * (x - mean)) / (v.Length - 1));
    Console.WriteLine();
    Console.WriteLine($"点数   = {v.Length}");
    Console.WriteLine($"均值   = {mean:F4} Ohm  ({mean / 1000:F6} kOhm)");
    Console.WriteLine($"标准差 = {sd:F4} Ohm");
    Console.WriteLine($"CV     = {sd / mean * 100:F4} %");
    Console.WriteLine($"最小   = {v.Min():F4} Ohm");
    Console.WriteLine($"最大   = {v.Max():F4} Ohm");
    Console.WriteLine($"峰峰   = {v.Max() - v.Min():F4} Ohm");

    // 换算成 ADC 码，判断是不是量化/噪声地板在限制
    const double FullScale = 2.442;
    const double Codes24 = 8388608.0;
    double sampleCodes = mean / 150000.0 * (1.2 / FullScale * Codes24);
    Console.WriteLine();
    Console.WriteLine($"推算 signal = {mean * 8e-6 * 1e6:F1} uV (8 uA x R)");
    Console.WriteLine($"推算 sample = {sampleCodes:F0} 码（满量程 {Codes24:F0}，占 {sampleCodes / Codes24 * 100:F3}%）");
    Console.WriteLine($"1 码对应约 {150000.0 / (1.2 / FullScale * Codes24):F4} Ohm");
    return 0;
}
