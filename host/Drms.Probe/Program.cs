using Drms.Core.Protocol;
using Drms.Core.Session;
using Drms.Core.Transport;

// 联调工具：对真设备跑一遍握手 + 状态 + 配置 + 记录查询。
// 存在的意义是让协议实现尽早面对真硬件，而不是等界面做完才发现理解错了。

string? port = args.Length > 0 ? args[0] : null;
int period = args.Length > 1 && int.TryParse(args[1], out int p) ? p : 0;

var ports = SerialByteLink.ListPorts();
Console.WriteLine($"可用串口：{(ports.Length == 0 ? "（无）" : string.Join(", ", ports))}");

port ??= ports.FirstOrDefault(x => x == "COM5") ?? ports.FirstOrDefault();
if (port is null)
{
    Console.Error.WriteLine("找不到串口。用法：Drms.Probe <COMx> [订阅周期ms]");
    return 2;
}

Console.WriteLine($"使用 {port} @ 115200，DTR 拉起");
using var link = new SerialByteLink(port);
using var session = new DeviceSession(link);
session.Diagnostic += msg => Console.WriteLine($"  [诊断] {msg}");
session.Start();

try
{
    Console.WriteLine("\n=== HELLO ===");
    HelloReply hello = session.Handshake();
    Console.WriteLine($"  UID        = {hello.UidText}");
    Console.WriteLine($"  Boot       = 0x{hello.Boot:X16}");
    Console.WriteLine($"  Session    = {session.SessionId}");
    Console.WriteLine($"  MaxPayload = {hello.MaxPayload}");
    Console.WriteLine($"  Capabilities = [{string.Join(",", hello.Capabilities)}]");
    Console.WriteLine($"  rate_monitor = [{string.Join(",", hello.RateMonitor)}] （硬编码 4000，不可信）");
    Console.WriteLine($"  rate_record  = [{string.Join(",", hello.RateRecord)}]");

    Console.WriteLine("\n=== GET_STATUS ===");
    StatusReply st = session.GetStatus();
    Console.WriteLine($"  revision      = {st.StatusRevision}");
    Console.WriteLine($"  acquisition   = {st.Acquisition}");
    Console.WriteLine($"  recording     = {st.Recording}");
    Console.WriteLine($"  medium        = {st.Medium}  owner={st.Owner}  maintenance={st.Maintenance}");
    Console.WriteLine($"  generation    = {st.SampleGeneration}  rate={st.Rate} Hz");
    Console.WriteLine($"  fresh         = {st.Fresh}  classification={st.Classification}");
    Console.WriteLine($"  quality       = 0x{st.Quality:X} → {st.QualityFlags}");
    Console.WriteLine($"  fault         = 0x{st.Fault:X} → {st.FaultFlags}");
    Console.WriteLine($"  ohms          = {(st.Ohms.HasValue ? $"{st.Ohms.Value:F3} Ω" : "（未发布）")}");
    Console.WriteLine($"  ratio         = {(st.Ratio.HasValue ? $"{st.Ratio.Value:F6}" : "（未发布）")}");
    Console.WriteLine($"  level         = {(st.Level.HasValue ? st.Level.Value : "（无）")}");
    Console.WriteLine($"  battery       = {(st.BatteryMv.HasValue ? $"{st.BatteryMv.Value} mV" : "（无读数）")}");
    Console.WriteLine($"  media_gen     = {st.MediaGeneration}");
    Console.WriteLine($"  versions      = running={st.RunningVersion} saved={st.SavedVersion} " +
                      $"baseline={st.BaselineVersion} cal={st.CalibrationVersion}");

    Console.WriteLine("\n=== GET_CONFIG ===");
    try
    {
        ConfigReply cfg = session.GetConfig();
        Console.WriteLine($"  running_version={cfg.RunningVersion} saved_version={cfg.SavedVersion}");
        Console.WriteLine($"  settings      = {cfg.Settings.Length} 字节");
        var fields = cfg.Fields;
        foreach (var (tag, name) in new (ushort, string)[]
                 {
                     (Tag.RateHz, "rate_hz"), (Tag.RecordDurationMs, "record_duration_ms"),
                     (Tag.TauUs, "tau_us"), (Tag.WarmupUs, "warmup_us"),
                     (Tag.ConfirmUs, "confirm_us"), (Tag.StaleTimeoutUs, "stale_timeout_us"),
                     (Tag.BaselineMinCount, "baseline_min_count"), (Tag.Alias, "alias"),
                     (Tag.Specimen, "specimen"),
                 })
        {
            if (fields.TryGetValue(tag, out TlvField? f))
                Console.WriteLine($"    {name,-20} = {Describe(f)}");
        }
        if (fields.TryGetValue(Tag.Intervals, out TlvField? iv))
        {
            List<MonitorInterval> list = Messages.ParseIntervals(iv.Value);
            Console.WriteLine($"    intervals ({list.Count} 条):");
            foreach (MonitorInterval one in list)
                Console.WriteLine($"      id={one.Id} level={one.Level} " +
                                  $"[{one.Low:F4}, {one.High:F4}) h={one.Hysteresis:F4} " +
                                  $"closed={one.LastUpperClosed}");
        }
        else
        {
            Console.WriteLine("    intervals = （未配置区间表 → 主图 R/R₀ 不会发布）");
        }
    }
    catch (DeviceException ex)
    {
        Console.WriteLine($"  GET_CONFIG 不可用：{ex.Message} result={ex.Result} reason={ex.Reason}");
        Console.WriteLine("  （出厂空配置时正常：首次完整 APPLY_CONFIG 成功后才可读）");
    }

    if (st.LastRecord.HasValue || st.Record.HasValue)
    {
        ulong id = st.Record ?? st.LastRecord!.Value;
        Console.WriteLine($"\n=== GET_RECORD {id} ===");
        try
        {
            RecordReply rec = session.GetRecord(id);
            Console.WriteLine($"  phase={rec.Phase} result={rec.Result} clean_end={rec.CleanEnd}");
            Console.WriteLine($"  capture_lost={rec.CaptureLost} log_dropped={rec.LogDropped} " +
                              $"unknown_loss={rec.UnknownLoss}");
        }
        catch (DeviceException ex)
        {
            Console.WriteLine($"  查询失败：{ex.Message} result={ex.Result} reason={ex.Reason}");
        }
    }

    if (period > 0)
    {
        Console.WriteLine($"\n=== SUBSCRIBE CURVE period_ms={period} ===");
        int received = 0;
        using var gate = new ManualResetEventSlim(false);
        session.MeasurementReceived += ev =>
        {
            received++;
            Console.WriteLine($"  #{ev.Sequence} mono={ev.MonoUs}µs fresh={ev.Fresh} " +
                              $"cls={ev.Classification} quality=0x{ev.Quality:X} " +
                              $"ohms={(ev.Ohms.HasValue ? ev.Ohms.Value.ToString("F3") : "-")} " +
                              $"ratio={(ev.Ratio.HasValue ? ev.Ratio.Value.ToString("F6") : "-")} " +
                              $"lost={ev.Lost}");
            if (received >= 5) gate.Set();
        };
        uint applied = session.SubscribeCurve((uint)period);
        Console.WriteLine($"  设备实际周期 = {applied} ms");
        gate.Wait(TimeSpan.FromSeconds(12));
        Console.WriteLine($"  共收到 {received} 条");
        if (received == 0)
            Console.WriteLine("  ⚠ 没收到任何 MEAS_EVENT —— 采集可能未运行，或订阅未生效");
    }

    Console.WriteLine("\n联调完成。");
    return 0;
}
catch (DeviceException ex)
{
    Console.Error.WriteLine($"设备通信失败：{ex.Message} result={ex.Result} reason={ex.Reason}");
    return 1;
}
catch (ProtocolException ex)
{
    Console.Error.WriteLine($"协议错误：{ex.Message}");
    return 1;
}

static string Describe(TlvField f)
{
    try
    {
        return f.Value.Length switch
        {
            1 => f.Value[0].ToString(),
            2 => f.AsU16().ToString(),
            4 => f.AsU32().ToString(),
            8 => f.Id is Tag.Ohms or Tag.Ratio or Tag.BaselineMaxCv
                    ? f.AsDouble().ToString("F6")
                    : f.AsU64().ToString(),
            _ => f.Id == Tag.Alias ? f.AsUtf8() : $"{f.Value.Length} 字节",
        };
    }
    catch (ProtocolException)
    {
        return $"（{f.Value.Length} 字节，未能按预期类型解码）";
    }
}
