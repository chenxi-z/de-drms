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

// unstick 模式：SAFE_STOP → RESUME_MONITOR，用"安全停止失效化冲突启动"的语义
// 清理设备侧卡死的异步操作（如断线遗留的 FILE_LIST）。不丢数据，监测短暂中断后恢复。
if (args.Length > 0 && args[0] == "unstick")
{
    return await UnstickAsync(args.Length > 1 ? args[1] : "COM5");
}

// raw 模式：订阅 RAW 全速率原始流（SUBSCRIBE stream=RAW），按批收帧并统计。
// 这是"联机看 4 kSPS 波形"的通路：设备每 60 帧一批（约 15 ms）推送，批内带流内序号，
// 批间用 lost 与帧序号连续性判定缺口。用法：raw <port> <秒数> [k_ohms 可选]
if (args.Length > 0 && args[0] == "raw")
{
    return await RawAsync(args.Length > 1 ? args[1] : "COM5",
                          args.Length > 2 && double.TryParse(args[2], out double sec) ? sec : 10.0,
                          args.Length > 3 && double.TryParse(args[3], out double k) ? k : (double?)null);
}

// msc 模式：显式导出/交还 TF 卡（opcode 48/49）。
// 导出成功后卡以只读 U 盘出现在电脑上；交还前应先在电脑端安全弹出。
// 用法：msc COM9 export   /   msc COM9 release
if (args.Length > 0 && args[0] == "msc")
{
    if (args.Length < 3 || (args[2] != "export" && args[2] != "release"))
    {
        Console.WriteLine("用法: msc <port> export|release");
        return 1;
    }
    return await MscAsync(args[1], args[2] == "export");
}

// getbin 模式：绕过 FILE_LIST，用 GET_STATUS 的 media_generation 直接 FILE_OPEN。
// file_id 从 startId 往下试探（不存在时 OPEN 会以错误终态快速返回）。
// 背景：FILE_LIST 的断线遗留操作在设备侧可能卡死（2026-11-16 实测），此模式是绕行通道。
if (args.Length > 0 && args[0] == "getbin")
{
    return await GetBinAsync(args.Length > 1 ? args[1] : "COM5",
                             args.Length > 2 && uint.TryParse(args[2], out uint sid) ? sid : 60u,
                             args.Length > 3 ? args[3] : null);
}

// recdl 模式：短记录 → TF 落盘 → FILE_* 下载到本地。
// 用途：拿 4 kSPS 全速率原始帧。CURVE 订阅只有 100 ms 单帧快照（10 Hz），
// 单帧不滤波且工频在 10 Hz 下混叠，统计会失真；全速率数据以记录文件为准。
if (args.Length > 0 && args[0] == "recdl")
{
    return await RecordDownloadAsync(args.Length > 1 ? args[1] : "COM5",
                                     args.Length > 2 && uint.TryParse(args[2], out uint ms) ? ms : 200u,
                                     args.Length > 3 ? args[3] : null);
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

/// <summary>短记录 + 下载 BIN。回答"4 kSPS 全速率下这电阻多大、稳不稳"。</summary>
static async Task<int> RecordDownloadAsync(string port, uint durationMs, string? outPath)
{
    using var link = new SerialByteLink(port);
    using var session = new DeviceSession(link) { RequestTimeout = TimeSpan.FromSeconds(10) };
    session.Diagnostic += m => Console.WriteLine($"  [诊断] {m}");
    session.Start();
    HelloReply hello = session.Handshake();
    Console.WriteLine($"UID={hello.UidText}");

    StatusReply st = session.GetStatus();
    Console.WriteLine($"acq={st.Acquisition} recording={st.Recording} medium={st.Medium} " +
                      $"owner={st.Owner} rate={st.Rate}");
    if (st.Recording != Recording.Idle) { Console.WriteLine("设备正在记录，先结束再试"); return 2; }
    if (st.Medium != Medium.Ready) { Console.WriteLine($"介质不可用（medium={st.Medium}），记录需要 TF 卡在位"); return 3; }

    // ---- 1. 短记录：duration 到点自动结束，不需要 END_RECORD ----
    // 注意：BEGIN 操作 Ok 只代表"开始边界已确认"；记录跑满 duration 并落盘收尾后
    // GET_RECORD 的 phase 才到 Finished（此前 result=Accepted 是合法的"终态前"值）。
    var (op, record) = session.BeginRecord(durationMs);
    Console.WriteLine($"BEGIN_RECORD 受理 op={op} record={record} duration={durationMs}ms");
    OperationReply final = await OperationWaiter.WaitAsync(session, op, TimeSpan.FromSeconds(30));
    Console.WriteLine($"记录操作终态: {final.Result}");

    RecordReply rec;
    var recDeadline = DateTime.UtcNow + TimeSpan.FromSeconds(15);
    while (true)
    {
        rec = session.GetRecord(record);
        if (rec.Phase == OperationPhase.Finished) break;
        if (DateTime.UtcNow > recDeadline) { Console.WriteLine("等待记录收尾超时"); return 5; }
        await Task.Delay(300);
    }
    Console.WriteLine($"记录摘要: result={rec.Result} clean_end={rec.CleanEnd} " +
                      $"capture_lost={rec.CaptureLost} log_dropped={rec.LogDropped} unknown_loss={rec.UnknownLoss}");
    if (rec.Result != Result.Ok || rec.UnknownLoss || rec.CaptureLost > 0 || rec.LogDropped > 0)
        Console.WriteLine("⚠ 记录不完整，统计仅供参考");

    await Task.Delay(1000);   // 记录收尾刚完成，给存储线程一点释放 TF 租约的时间

    // 文件操作只在存储完全静止时才会收尾（drms_application.c: file_service_control）。
    // 记录未完全空闲时提交文件操作会卡死设备侧单槽状态机（2026-11-16 实测），这里显式挡住。
    st = session.GetStatus();
    if (st.Recording != Recording.Idle)
    {
        Console.WriteLine($"recording={st.Recording}（非 Idle），不提交文件操作，避免卡死文件服务");
        return 6;
    }

    // ---- 2. 列文件，取编号最大（最新）的一个 ----
    uint fileId;
    ulong fileSize;
    uint mediaGen;
    try { (fileId, fileSize, mediaGen) = FileListNewest(session); }
    catch (Exception ex) { Console.WriteLine($"列文件失败: {ex.Message}"); return 4; }
    Console.WriteLine($"最新文件 DRMS{fileId:D4}.BIN，{fileSize} B，mediaGen={mediaGen}");

    // ---- 3. 打开句柄并分块下载 ----
    ulong handle = await FileOpenAsync(session, fileId, mediaGen);
    Console.WriteLine($"FILE_OPEN 完成，句柄={handle}");
    string path = outPath ?? Path.Combine(Path.GetTempPath(), "de-drms-probe", $"DRMS{fileId:D4}.BIN");
    await DownloadAsync(session, handle, fileSize, path);
    return 0;
}

/// <summary>按 768 B 分块读整个句柄并落盘（count 单位是字节，见 drms_cdc_v2.c opcode 51），
/// 最后关句柄（读取在途时 CLOSE 也回 BUSY，同样换号重试）。</summary>
static async Task DownloadAsync(DeviceSession session, ulong handle, ulong fileSize, string path)
{
    var data = new byte[fileSize];
    ulong offset = 0;
    while (offset < fileSize)
    {
        ushort count = (ushort)Math.Min(768, fileSize - offset);
        Message reply = RetryBusy(session, rid => FrameCodec.Encode(Kind.Request, Opcodes.FileRead,
            session.SessionId, rid, new TlvWriter()
                .AddU64(Tag.Operation, handle)
                .AddU64(Tag.Offset, offset)
                .AddU16(Tag.Count, count).ToArray()));
        Result r = Messages.ReadResult(reply);
        if (r != Result.Ok)
            throw new DeviceException($"FILE_READ @ {offset} 失败", r, Messages.ReadReason(reply));
        var f = reply.Index;
        ulong gotOffset = f.Require(Tag.Offset, "offset").AsU64();
        if (gotOffset != offset)
            throw new ProtocolException($"FILE_READ 偏移不匹配：请求 {offset}，回复 {gotOffset}");
        byte[] chunk = f.Require(Tag.Data, "data").Value;
        bool eof = f.Optional(Tag.Eof)?.AsBool() ?? false;
        if (chunk.Length == 0 && !eof) throw new ProtocolException("空数据且无 EOF");
        Buffer.BlockCopy(chunk, 0, data, (int)offset, chunk.Length);
        offset += (ulong)chunk.Length;
        if (eof != (offset >= fileSize))
            throw new ProtocolException($"EOF 标志与文件大小矛盾：eof={eof}，offset={offset}/{fileSize}");
    }

    Message closeReply = RetryBusy(session, rid => FrameCodec.Encode(Kind.Request, Opcodes.FileClose,
        session.SessionId, rid, new TlvWriter().AddU64(Tag.Operation, handle).ToArray()));
    Result closeResult = Messages.ReadResult(closeReply);
    if (closeResult == Result.Accepted)
    {
        ulong closeOp = closeReply.Index.Require(Tag.Operation, "operation").AsU64();
        OperationReply closeFinal = await OperationWaiter.WaitAsync(session, closeOp, TimeSpan.FromSeconds(10));
        closeResult = closeFinal.Result;
    }
    if (closeResult != Result.Ok)
        throw new DeviceException($"FILE_CLOSE 失败", closeResult, Messages.ReadReason(closeReply));

    Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(path))!);
    File.WriteAllBytes(path, data);
    Console.WriteLine($"已下载 {data.Length} B → {path}");
}

/// <summary>订阅 RAW 全速率流并统计（联机噪声/工频分析的实时版本）。</summary>
static async Task<int> RawAsync(string port, double seconds, double? kOhms)
{
    using var link = new SerialByteLink(port);
    using var session = new DeviceSession(link) { RequestTimeout = TimeSpan.FromSeconds(10) };
    session.Diagnostic += m => Console.WriteLine($"  [诊断] {m}");
    var frames = new List<(uint Seq, int V, int I, bool CrcOk)>();
    var gate = new ManualResetEventSlim(false);
    var deadline = DateTime.UtcNow + TimeSpan.FromSeconds(seconds);
    ulong lastStreamSeq = 0, lostSeen = 0;
    int batches = 0, gapEvents = 0, gappyFrames = 0;
    uint? lastGen = null;
    var lockObj = new object();

    session.RawReceived += ev =>
    {
        lock (lockObj)
        {
            batches++;
            if (lastStreamSeq != 0 && ev.Sequence != lastStreamSeq + 1)
                gapEvents++;
            lastStreamSeq = ev.Sequence;
            if (ev.Lost > lostSeen) { lostSeen = ev.Lost; }
            if (lastGen.HasValue && ev.SampleGeneration != lastGen.Value)
                Console.WriteLine($"  代次变化 {lastGen} → {ev.SampleGeneration}（采集重启，批另起）");
            lastGen = ev.SampleGeneration;
            foreach (var f in ev.Frames())
            {
                if (frames.Count > 0 && f.Sequence != frames[^1].Seq + 1) gappyFrames++;
                frames.Add((f.Sequence, f.Voltage, f.Sense, f.CrcOk));
            }
            if (frames.Count > 0 && DateTime.UtcNow > deadline) gate.Set();
        }
    };
    session.Start();
    HelloReply hello = session.Handshake();
    Console.WriteLine($"UID={hello.UidText}");

    StatusReply st = session.GetStatus();
    Console.WriteLine($"acq={st.Acquisition} rate={st.Rate} fresh={st.Fresh}");

    uint period = session.SubscribeRaw();
    Console.WriteLine($"SUBSCRIBE(RAW) 成功，设备批周期 {period} ms，采集 {seconds} s…");
    await Task.Delay(TimeSpan.FromSeconds(seconds + 1));
    gate.Set();
    session.Unsubscribe(StreamKind.Raw);

    List<(uint Seq, int V, int I, bool CrcOk)> v;
    lock (lockObj) v = frames.ToList();
    if (v.Count < 100) { Console.WriteLine($"只收到 {v.Count} 帧，数据不足"); return 1; }

    double rateMeasured = v.Count / seconds;
    Console.WriteLine();
    Console.WriteLine($"帧数     = {v.Count}  批次 = {batches}  实测速率 ≈ {rateMeasured:F0} 帧/s（标称 {st.Rate}）");
    Console.WriteLine($"帧序号缺口 = {gappyFrames} 帧   批序号跳变 = {gapEvents} 次   lost = {lostSeen}");
    Console.WriteLine($"CRC 坏帧   = {v.Count(f => !f.CrcOk)}");

    // 电压/电流比值的统计（不需要 k 也能看噪声；给 k 则换算成欧姆）
    var ratios = v.Where(f => f.CrcOk && f.I > 4096).Select(f => (double)f.V / f.I).ToList();
    if (ratios.Count < 10) { Console.WriteLine("有效帧太少"); return 1; }
    double mean = ratios.Average();
    double sd = Math.Sqrt(ratios.Sum(x => (x - mean) * (x - mean)) / (ratios.Count - 1));
    double cv = sd / mean * 100;
    Console.WriteLine();
    Console.WriteLine($"V/I 均值 = {mean:F6}   CV = {cv:F4} %  （逐帧全速率）");
    if (kOhms.HasValue)
        Console.WriteLine($"换算电阻 ≈ {mean * kOhms.Value:F1} Ohm（k = {kOhms.Value:F2} Ohm）");

    // 整工频周期盒平均：20 ms = rate/50 帧
    int win = Math.Max(1, (int)Math.Round(st.Rate / 50.0));
    var blocks = new List<double>();
    for (int i = 0; i + win <= ratios.Count; i += win)
        blocks.Add(ratios.GetRange(i, win).Average());
    if (blocks.Count > 1)
    {
        double bm = blocks.Average();
        double bsd = Math.Sqrt(blocks.Sum(x => (x - bm) * (x - bm)) / (blocks.Count - 1));
        Console.WriteLine($"20 ms 盒平均（{win} 帧/块，{blocks.Count} 块）: CV = {bsd / bm * 100:F4} %");
        if (kOhms.HasValue)
            Console.WriteLine($"    → 均值 ≈ {bm * kOhms.Value:F1} Ohm");
    }
    return 0;
}

/// <summary>MSC 导出/交还。导出 = FileX 关闭并把卡交给电脑（只读 U 盘）；
/// 交还 = 设备收回并重新挂载。操作都是 ACCEPTED → 轮询终态。</summary>
static async Task<int> MscAsync(string port, bool export)
{
    using var link = new SerialByteLink(port);
    using var session = new DeviceSession(link) { RequestTimeout = TimeSpan.FromSeconds(10) };
    session.Diagnostic += m => Console.WriteLine($"  [诊断] {m}");
    session.Start();
    HelloReply hello = session.Handshake();
    Console.WriteLine($"UID={hello.UidText}");

    StatusReply st = session.GetStatus();
    Console.WriteLine($"recording={st.Recording} medium={st.Medium} owner={st.Owner}");
    if (export && st.Recording != Recording.Idle) { Console.WriteLine("记录进行中，不能导出"); return 2; }

    ulong rid = session.NextRequestId();
    byte[] request = FrameCodec.Encode(Kind.Request, export ? Opcodes.MscExport : Opcodes.MscRelease,
        session.SessionId, rid, []);
    Message reply = session.Transact(request, rid);
    Result r = Messages.ReadResult(reply);
    Console.WriteLine($"{(export ? "MSC_EXPORT" : "MSC_RELEASE")}: {r}");
    if (r != Result.Accepted)
    {
        if (export && r == Result.Ok) { Console.WriteLine("已是导出状态"); return 0; }
        return 3;
    }
    ulong op = reply.Index.Require(Tag.Operation, "operation").AsU64();
    OperationReply final = await OperationWaiter.WaitAsync(session, op, TimeSpan.FromSeconds(30),
        TimeSpan.FromMilliseconds(500),
        (rp, e) => { if ((int)e.TotalSeconds % 5 == 0) Console.WriteLine($"  {e.TotalSeconds:F0}s phase={rp.Phase}"); });
    Console.WriteLine($"终态: {final.Result}" + (final.Reason.HasValue ? $" / {final.Reason}" : ""));
    st = session.GetStatus();
    Console.WriteLine($"现在: owner={st.Owner} medium={st.Medium} recording={st.Recording}");
    return final.Result == Result.Ok ? 0 : 4;
}

/// <summary>绕过 FILE_LIST 的下载：从 startId 往下试探 FILE_OPEN，
/// 第一个能打开的就是（接近）最新的文件。</summary>
static async Task<int> GetBinAsync(string port, uint startId, string? outPath)
{
    using var link = new SerialByteLink(port);
    using var session = new DeviceSession(link) { RequestTimeout = TimeSpan.FromSeconds(10) };
    session.Diagnostic += m => Console.WriteLine($"  [诊断] {m}");
    session.Start();
    HelloReply hello = session.Handshake();
    Console.WriteLine($"UID={hello.UidText}");

    StatusReply st = session.GetStatus();
    uint mediaGen = st.MediaGeneration;
    Console.WriteLine($"mediaGen={mediaGen} recording={st.Recording} medium={st.Medium}");
    if (st.Medium != Medium.Ready) { Console.WriteLine("介质不可用"); return 3; }

    for (uint id = startId; ; id--)
    {
        Message reply;
        try
        {
            reply = RetryBusy(session, rid => FrameCodec.Encode(Kind.Request, Opcodes.FileOpen,
                session.SessionId, rid, new TlvWriter()
                    .AddU32(Tag.FileId, id)
                    .AddU32(Tag.MediaGeneration, mediaGen).ToArray()), maxTries: 10);
        }
        catch (DeviceException ex)
        {
            Console.WriteLine($"试探 DRMS{id:D4} 时重试超限：{ex.Message}");
            return 4;
        }
        Result r = Messages.ReadResult(reply);
        if (r != Result.Accepted)
        {
            Console.WriteLine($"DRMS{id:D4}: OPEN 回复 {r}，继续往下试探");
            if (id == 0) { Console.WriteLine("已试探到 0，没有可打开的文件"); return 5; }
            continue;
        }
        ulong op = reply.Index.Require(Tag.Operation, "operation").AsU64();
        OperationReply final = await OperationWaiter.WaitAsync(session, op, TimeSpan.FromSeconds(10));
        if (final.Result != Result.Ok)
        {
            Console.WriteLine($"DRMS{id:D4}: 打开终态 {final.Result}，继续往下试探");
            if (id == 0) { Console.WriteLine("已试探到 0，没有可打开的文件"); return 5; }
            continue;
        }

        ulong handle = final.Operation;
        ulong fileSize = final.FileSize ?? 0;
        Console.WriteLine($"打开成功：DRMS{id:D4}.BIN，{fileSize} B，句柄={handle}");
        string path = outPath ?? Path.Combine(Path.GetTempPath(), "de-drms-probe", $"DRMS{id:D4}.BIN");
        await DownloadAsync(session, handle, fileSize, path);
        return 0;
    }
}

/// <summary>SAFE_STOP + RESUME_MONITOR：让设备失效化冲突的旧异步操作后恢复监测。</summary>
static async Task<int> UnstickAsync(string port)
{
    using var link = new SerialByteLink(port);
    using var session = new DeviceSession(link) { RequestTimeout = TimeSpan.FromSeconds(10) };
    session.Diagnostic += m => Console.WriteLine($"  [诊断] {m}");
    session.Start();
    HelloReply hello = session.Handshake();
    Console.WriteLine($"UID={hello.UidText} session={session.SessionId}");

    StatusReply st = session.GetStatus();
    Console.WriteLine($"清理前: acq={st.Acquisition} recording={st.Recording} medium={st.Medium}");

    ulong rid = session.NextRequestId();
    Message stopReply = session.Transact(Messages.SafeStopRequest(session.SessionId, rid), rid);
    Result stopResult = Messages.ReadResult(stopReply);
    Console.WriteLine($"SAFE_STOP: {stopResult}");
    if (stopResult == Result.Accepted)
    {
        ulong op = stopReply.Index.Require(Tag.Operation, "operation").AsU64();
        OperationReply final = await OperationWaiter.WaitAsync(session, op, TimeSpan.FromSeconds(15));
        Console.WriteLine($"SAFE_STOP 终态: {final.Result}");
    }

    await Task.Delay(1500);

    rid = session.NextRequestId();
    Message resumeReply = session.Transact(Messages.ResumeMonitorRequest(session.SessionId, rid), rid);
    Result resumeResult = Messages.ReadResult(resumeReply);
    Console.WriteLine($"RESUME_MONITOR: {resumeResult}");
    if (resumeResult == Result.Accepted)
    {
        ulong op = resumeReply.Index.Require(Tag.Operation, "operation").AsU64();
        OperationReply final = await OperationWaiter.WaitAsync(session, op, TimeSpan.FromSeconds(15));
        Console.WriteLine($"RESUME_MONITOR 终态: {final.Result}");
    }

    await Task.Delay(1500);
    st = session.GetStatus();
    Console.WriteLine($"恢复后: acq={st.Acquisition} recording={st.Recording} medium={st.Medium} " +
                      $"fresh={st.Fresh} ohms={(st.Ohms.HasValue ? st.Ohms.Value.ToString("F1") : "-")}");
    return 0;
}

/// <summary>BUSY-受理重试：FILE_LIST/FILE_READ 首轮回 BUSY 表示已受理，
/// 按协议换新 request_id 重发同样内容，直到结果不再是 BUSY。
/// 单次超时也按可重试处理（协议允许主机超时后换号重试）。</summary>
static Message RetryBusy(DeviceSession session, Func<ulong, byte[]> build, int maxTries = 120)
{
    for (int i = 0; i < maxTries; i++)
    {
        ulong rid = session.NextRequestId();
        Message reply;
        try
        {
            reply = session.Transact(build(rid), rid);
        }
        catch (DeviceException) when (i < maxTries - 1)
        {
            continue;   // 超时：该编号已消耗，换号重试
        }
        if (Messages.ReadResult(reply) != Result.Busy) return reply;
        Thread.Sleep(50);
    }
    throw new DeviceException("设备持续 BUSY/无回复，重试超限");
}

/// <summary>翻 FILE_LIST 到最后一个条目（记录文件编号递增，最后 = 最新）。</summary>
static (uint Id, ulong Size, uint MediaGen) FileListNewest(DeviceSession session)
{
    uint lastId = 0;
    ulong lastSize = 0;
    uint gen = 0;
    bool any = false;
    uint cursor = 0;
    while (cursor <= 10000u)
    {
        Message reply = RetryBusy(session, rid => FrameCodec.Encode(Kind.Request, Opcodes.FileList,
            session.SessionId, rid, new TlvWriter().AddU32(Tag.Cursor, cursor).ToArray()));
        Result r = Messages.ReadResult(reply);
        if (r != Result.Ok)
            throw new DeviceException($"FILE_LIST cursor={cursor} 失败", r, Messages.ReadReason(reply));
        var f = reply.Index;
        gen = f.Require(Tag.MediaGeneration, "media_generation").AsU32();
        if (f.Optional(Tag.FileId) is not { } idF) break;      // 候选号不存在 → 结束
        lastId = idF.AsU32();
        any = true;
        lastSize = f.Optional(Tag.FileSize)?.AsU64() ?? 0;
        if (f.Optional(Tag.NextCursor) is not { } nextF) break; // 无 next_cursor = 结束
        cursor = nextF.AsU32();
    }
    if (!any) throw new DeviceException("卡上没有记录文件");
    return (lastId, lastSize, gen);
}

/// <summary>FILE_OPEN：受理后轮询到 FINISHED，成功即句柄已建立（句柄 = operation 号）。</summary>
static async Task<ulong> FileOpenAsync(DeviceSession session, uint fileId, uint mediaGen)
{
    Message reply = RetryBusy(session, rid => FrameCodec.Encode(Kind.Request, Opcodes.FileOpen,
        session.SessionId, rid, new TlvWriter()
            .AddU32(Tag.FileId, fileId)
            .AddU32(Tag.MediaGeneration, mediaGen).ToArray()));
    Result r = Messages.ReadResult(reply);
    if (r != Result.Accepted)
        throw new DeviceException("FILE_OPEN 未被受理", r, Messages.ReadReason(reply));
    ulong op = reply.Index.Require(Tag.Operation, "operation").AsU64();
    OperationReply final = await OperationWaiter.WaitAsync(session, op, TimeSpan.FromSeconds(10));
    if (final.Result != Result.Ok)
        throw new DeviceException($"FILE_OPEN 终态非 OK：{final.Result}");
    return final.Operation;
}
