using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using Drms.Core.Config;
using Drms.Core.Protocol;
using Drms.Core.Session;
using Drms.Core.Transport;

namespace Drms.Gui;

/// <summary>
/// 一个曲线采样点。联机曲线的时间轴用设备上报的 mono_us（发布时刻），
/// 不是采样时刻——协议 §4.1 明确这一点，界面上也照实标注。
/// </summary>
public sealed record CurvePoint(double Seconds, double? Ohms, double? Ratio, ulong Sequence);

/// <summary>
/// 主窗口的状态与动作。刻意做成"很薄的壳"：
/// 所有协议细节都在 Drms.Core，这里只负责串起 UI 与设备、并把结果转成人能读的文字。
///
/// 为什么不用 ReactiveUI/CommunityToolkit：首版只有十几个属性，
/// 手写 INotifyPropertyChanged 比引入框架更少意外；将来要换也只需重写这一层。
/// </summary>
public sealed class MainViewModel : INotifyPropertyChanged
{
    private DeviceSession? _session;
    private Timer? _pollTimer;
    private DateTime _startedAt = DateTime.UtcNow;
    private ulong _lastSequence;

    public event PropertyChangedEventHandler? PropertyChanged;

    // ---- 连接 ----

    public ObservableCollection<string> Ports { get; } = new();

    private string? _selectedPort;
    public string? SelectedPort
    {
        get => _selectedPort;
        set { if (Set(ref _selectedPort, value)) Notify(nameof(CanConnect)); }
    }

    private bool _connected;
    public bool Connected
    {
        get => _connected;
        private set { if (Set(ref _connected, value)) { Notify(nameof(CanConnect)); Notify(nameof(ConnectionText)); } }
    }

    public bool CanConnect => !Connected && SelectedPort is not null;
    public string ConnectionText => Connected ? $"已连接 {SelectedPort}" : "未连接";

    private string _statusMessage = "选择串口后点“连接”。设备需要 USB 线，DTR 会自动拉起。";
    public string StatusMessage
    {
        get => _statusMessage;
        private set => Set(ref _statusMessage, value);
    }

    // ---- 设备身份 ----

    private string _deviceUid = "—";
    public string DeviceUid { get => _deviceUid; private set => Set(ref _deviceUid, value); }

    // ---- 实时读数 ----

    private string _ohmsText = "—";
    public string OhmsText { get => _ohmsText; private set => Set(ref _ohmsText, value); }

    private string _ratioText = "—";
    public string RatioText { get => _ratioText; private set => Set(ref _ratioText, value); }

    private string _levelText = "—";
    public string LevelText { get => _levelText; private set => Set(ref _levelText, value); }

    private string _classificationText = "—";
    public string ClassificationText { get => _classificationText; private set => Set(ref _classificationText, value); }

    private string _acquisitionText = "—";
    public string AcquisitionText { get => _acquisitionText; private set => Set(ref _acquisitionText, value); }

    private string _recordingText = "—";
    public string RecordingText { get => _recordingText; private set => Set(ref _recordingText, value); }

    private string _mediumText = "—";
    public string MediumText { get => _mediumText; private set => Set(ref _mediumText, value); }

    private string _batteryText = "—";
    public string BatteryText { get => _batteryText; private set => Set(ref _batteryText, value); }

    private string _freshText = "—";
    public string FreshText { get => _freshText; private set => Set(ref _freshText, value); }

    private string _qualityText = "—";
    public string QualityText { get => _qualityText; private set => Set(ref _qualityText, value); }

    // ---- 曲线数据 ----

    /// <summary>联机曲线点。界面绑这个集合，最大保留一小时（10 Hz → 36000 点）。</summary>
    public ObservableCollection<CurvePoint> Points { get; } = new();

    private const int MaxPoints = 36000;

    /// <summary>配置与基线面板。</summary>
    public ConfigViewModel Config { get; } = new();

    /// <summary>最近一次 GET_STATUS 快照，供前置检查与按钮可用性判断。</summary>
    private StatusReply? _lastStatus;

    /// <summary>建立基线时的实时统计；未建立时为 null。</summary>
    private BaselineAccumulator? _baselineAccumulator;
    private CancellationTokenSource? _baselineCts;

    /// <summary>设备当前配置里的 baseline_min_count；null 表示读不到（出厂空配置）。</summary>
    private uint? _baselinePolicyCount;

    /// <summary>R₀ 建立成功后拿到并显示的基线版本号。</summary>
    private string _r0Text = "—";
    public string R0Text { get => _r0Text; private set => Set(ref _r0Text, value); }

    private string _r0StatusText = "未建立";
    public string R0StatusText { get => _r0StatusText; private set => Set(ref _r0StatusText, value); }

    // ---- 动作 ----

    public void RefreshPorts()
    {
        Ports.Clear();
        foreach (string p in SerialByteLink.ListPorts())
            Ports.Add(p);
        SelectedPort = Ports.FirstOrDefault(x => x == "COM5") ?? Ports.FirstOrDefault();
    }

    public async Task ConnectAsync()
    {
        if (SelectedPort is null)
            return;

        StatusMessage = $"正在打开 {SelectedPort} …";
        try
        {
            IByteLink link = new SerialByteLink(SelectedPort);
            var session = new DeviceSession(link);
            session.Diagnostic += msg => StatusMessage = $"诊断：{msg}";
            session.MeasurementReceived += OnMeasurement;
            session.Start();

            // 握手是阻塞的（等回复），丢到线程池避免卡 UI
            HelloReply hello = await Task.Run(session.Handshake);

            _session = session;
            _startedAt = DateTime.UtcNow;
            DeviceUid = hello.UidText;
            Connected = true;
            StatusMessage = $"握手成功：session={session.SessionId}，能力 {hello.Capabilities.Length} 项";

            await RefreshStatusAsync();

            // 订阅曲线：200 ms 一个点。协议允许 100 ms 起，200 对显示更稳。
            try
            {
                uint applied = await Task.Run(() => session.SubscribeCurve(200));
                StatusMessage = $"已连接并订阅曲线（{applied} ms/点）";
            }
            catch (DeviceException ex)
            {
                StatusMessage = $"已连接，但订阅失败：{ex.Message}（仍可看状态）";
            }

            // 1 Hz 轮询 GET_STATUS：协议 §8 要求并行轮询，因为 MEAS_EVENT 缺 rate/generation
            _pollTimer = new Timer(_ => _ = RefreshStatusAsync(), null, 1000, 1000);
        }
        catch (Exception ex) when (ex is DeviceException or ProtocolException or IOException or UnauthorizedAccessException)
        {
            StatusMessage = $"连接失败：{ex.Message}";
            _session?.Dispose();
            _session = null;
        }
    }

    public void Disconnect()
    {
        _pollTimer?.Dispose();
        _pollTimer = null;
        _session?.Dispose();
        _session = null;
        Connected = false;
        StatusMessage = "已断开";
    }

    private async Task RefreshStatusAsync()
    {
        DeviceSession? session = _session;
        if (session is null)
            return;

        try
        {
            StatusReply st = await Task.Run(session.GetStatus);
            ApplyStatus(st);
        }
        catch (Exception ex)
        {
            StatusMessage = $"状态读取失败：{ex.Message}";
        }
    }

    private void ApplyStatus(StatusReply st)
    {
        _lastStatus = st;
        OhmsText = st.Ohms.HasValue ? $"{st.Ohms.Value / 1000.0:F3} kOhm" : "未发布";
        RatioText = st.Ratio.HasValue ? st.Ratio.Value.ToString("F6") : "未发布";
        LevelText = st.Level.HasValue ? $"等级 {st.Level.Value}" : "无";
        ClassificationText = DescribeClassification(st.Classification);
        AcquisitionText = st.Acquisition.ToString();
        RecordingText = st.Recording.ToString();
        MediumText = $"{st.Medium} / {st.Owner}";
        BatteryText = st.BatteryMv.HasValue ? $"{st.BatteryMv.Value} mV" : "无读数";
        FreshText = st.Fresh ? "新鲜" : "过期";
        QualityText = st.Quality == 0 ? "无" : st.QualityFlags.ToString();

        R0StatusText = st.BaselineVersion == 0
            ? "未建立"
            : $"版本 {st.BaselineVersion}";

        CheckBaselinePreconditions(st);
    }

    /// <summary>
    /// 每次都重算前置条件：用户可能切到 REF 模式、开始记录、或采集停了，
    /// 这些都会让 BUILD_R0 被固件拒绝。把原因实时写在面板上，
    /// 比让按钮神秘变灰更有用。
    /// </summary>
    private void CheckBaselinePreconditions(StatusReply st)
    {
        if (Config.Baseline.Running)
            return;

        uint? policyCount = _baselinePolicyCount;
        List<string> problems = BaselineRunner.CheckPreconditions(st, policyCount);
        Config.Baseline.PreconditionText = problems.Count == 0
            ? ""
            : string.Join("；", problems);
    }

    private void OnMeasurement(MeasurementEvent ev)
    {
        // 序号跳变说明有缺口——按协议 §5 要断线，不能连线。
        if (ev.Sequence != _lastSequence + 1 && _lastSequence != 0)
        {
            // 用一个"断点"占位：NaN 让 ScottPlot 把线断开
            Points.Add(new CurvePoint((ev.MonoUs / 1e6), null, null, ev.Sequence));
        }
        _lastSequence = ev.Sequence;

        double seconds = ev.MonoUs / 1e6;

        // 主副图各自判断有没有值：ohms 只要采集有效，ratio 还要基线与区间表。
        Points.Add(new CurvePoint(seconds, ev.Ohms, ev.Ratio, ev.Sequence));

        if (Points.Count > MaxPoints)
            Points.RemoveAt(0);

        if (ev.Ohms.HasValue)
            OhmsText = $"{ev.Ohms.Value / 1000.0:F3} kOhm";
        if (ev.Ratio.HasValue)
            RatioText = ev.Ratio.Value.ToString("F6");
        ClassificationText = DescribeClassification(ev.Classification);

        FeedBaselineProgress(ev);
    }

    /// <summary>
    /// 把 CURVE 事件喂给基线统计器。
    ///
    /// 只统计"有效"样本：设备侧建立基线时也只累加无故障帧，
    /// 若这里把无效帧算进去，界面显示的均值就会与设备最终写入的 R₀ 不一致，
    /// 用户会以为设备算错了。
    /// </summary>
    private void FeedBaselineProgress(MeasurementEvent ev)
    {
        BaselineAccumulator? acc = _baselineAccumulator;
        if (acc is null || !ev.Ohms.HasValue)
            return;

        // fresh=0 或 quality 位 0（无有效样本）都表示这一帧不可信
        bool valid = ev.Fresh && (ev.Quality & 1u) == 0;
        if (!valid)
            return;

        uint rate = _lastStatus?.Rate ?? 4000;
        acc.Feed(ev.Ohms.Value, BaselineAccumulator.SampleDtUs(rate));

        Config.Baseline.ProgressValue = acc.Progress;
        Config.Baseline.ProgressText =
            $"{acc.DurationUs / 1_000_000.0:F1} / {acc.MinDurationUs / 1_000_000.0:F0} s · " +
            $"{acc.Count} 样本";
        Config.Baseline.MeanText = $"{acc.Mean / 1000.0:F4} kOhm";
        Config.Baseline.CvText = double.IsNaN(acc.Cv) ? "—" : $"{acc.Cv * 100:F4}%";
        Config.Baseline.StabilityText = acc.IsStable
            ? (acc.HasEnoughSamples ? "已达稳定限" : "稳定")
            : $"未达稳定限（限 {acc.MaxCv * 100:F3}%）";
    }

    private static string DescribeClassification(Classification c) => c switch
    {
        Classification.Invalid => "无效",
        Classification.Warmup => "建立中",
        Classification.Unconfigured => "未配置（缺区间表）",
        Classification.Unmapped => "未映射",
        Classification.Pending => "确认中",
        Classification.Confirmed => "已确认",
        _ => c.ToString(),
    };

    // ---- 配置下发 ----

    /// <summary>
    /// 把界面上的配置整份下发。
    ///
    /// 这是"出厂空配置"下必须先做的一步：GET_CONFIG 返回 UNSUPPORTED 时
    /// 设备既没有区间表也没有基线策略，BUILD_R0 会被直接拒绝。
    /// </summary>
    public async Task<bool> ApplyConfigAsync()
    {
        DeviceSession? session = _session;
        if (session is null)
        {
            Config.ApplyResult = "未连接";
            return false;
        }

        List<MonitorInterval> intervals = Config.BuildIntervals();
        if (!Config.ConfigValid)
        {
            Config.ApplyResult = $"配置有误，未下发：{Config.ValidationText}";
            return false;
        }

        try
        {
            DeviceConfig config = Config.BuildConfig();
            byte[] settings = config.EncodeSettings();

            // 需要当前运行版本作为并发保护；读不到就当作 0（出厂状态）
            ulong expected = 0;
            try
            {
                ConfigReply current = await Task.Run(session.GetConfig);
                expected = current.RunningVersion;
            }
            catch (DeviceException ex) when (ex.Result == Result.Unsupported)
            {
                // 出厂空配置：这是正常路径，不是错误
                expected = 0;
            }

            ulong operation = await Task.Run(() => session.ApplyConfig(expected, settings));
            Config.ApplyResult = "已受理，等待设备完成…";

            OperationReply final = await OperationWaiter.WaitAsync(
                session, operation, TimeSpan.FromSeconds(15));

            if (final.Result == Result.Ok)
            {
                _baselinePolicyCount = config.BaselineMinCount;
                Config.ApplyResult = "配置已生效";
                StatusMessage = "配置下发成功";
                await RefreshStatusAsync();
                await TryLoadConfigFromDeviceAsync();
                return true;
            }

            Config.ApplyResult = $"下发失败：{final.Result}" +
                                 (final.Reason.HasValue ? $" / {final.Reason}" : "");
            return false;
        }
        catch (Exception ex)
        {
            Config.ApplyResult = $"下发异常：{ex.Message}";
            return false;
        }
    }

    /// <summary>把设备当前配置读回来填进界面（用于确认下发结果）。</summary>
    private async Task TryLoadConfigFromDeviceAsync()
    {
        DeviceSession? session = _session;
        if (session is null)
            return;
        try
        {
            ConfigReply cfg = await Task.Run(session.GetConfig);
            Dictionary<ushort, TlvField> fields = cfg.Fields;
            if (fields.TryGetValue(Tag.BaselineMinCount, out TlvField? count))
                _baselinePolicyCount = count.AsU32();
            if (fields.TryGetValue(Tag.Intervals, out TlvField? iv) && iv.Value.Length > 0)
                Config.LoadFromDevice(Messages.ParseIntervals(iv.Value));
        }
        catch (DeviceException)
        {
            // 空配置或读失败都不影响主流程
        }
    }

    // ---- 建立 R₀ ----

    /// <summary>
    /// 建立基线 R₀。
    ///
    /// 流程：本地前置检查 → 下发 BUILD_R0 → 轮询到终态。
    /// 采集窗口由用户在界面上选（10/30/60/180 s），对应配置里的 baseline_min_us。
    ///
    /// 重要：设备在成功后会**停止再重启采集**（drms_application.c:1310/1320），
    /// 联机曲线会断一次，generation 会变化。界面上要提示，否则用户会以为掉线。
    /// </summary>
    public async Task BuildBaselineAsync()
    {
        DeviceSession? session = _session;
        StatusReply? status = _lastStatus;
        if (session is null || status is null)
        {
            Config.Baseline.Result = "未连接或无状态";
            return;
        }

        List<string> problems = BaselineRunner.CheckPreconditions(status, _baselinePolicyCount);
        if (problems.Count > 0)
        {
            Config.Baseline.Result = "前置条件不满足：" + string.Join("；", problems);
            return;
        }

        ulong durationUs = Config.DurationUs;
        Config.Baseline.Running = true;
        Config.Baseline.Result = "";
        Config.Baseline.ProgressValue = 0;
        Config.Baseline.ProgressText = "已开始，等待设备采样…";
        StatusMessage = $"正在建立基线（窗口 {Config.SelectedDuration}）…";

        // 界面自己算实时统计：固件过程中不公开均值与离散度
        _baselineAccumulator = new BaselineAccumulator(
            minCount: 1, minDurationUs: durationUs, maxCv: 0.001);
        _baselineCts = new CancellationTokenSource();

        try
        {
            var runner = new BaselineRunner(session);

            // 设备超时是"预期时长 + 30 s"（固件 baseline_timeout_ms），这里留同样余量
            TimeSpan timeout = TimeSpan.FromMicroseconds(durationUs) + TimeSpan.FromSeconds(40);

            OperationReply final = await runner.RunAsync(timeout, (reply, elapsed) =>
            {
                Config.Baseline.ProgressText =
                    $"设备处理中（{elapsed.TotalSeconds:F0} s，phase={reply.Phase}）";
            }, _baselineCts.Token);

            if (final.Result == Result.Ok)
            {
                Config.Baseline.Result =
                    "基线已建立。注意：设备已重启采集，联机曲线会断一次，generation 会变化。";
                Config.Baseline.ProgressValue = 1.0;
                StatusMessage = "基线建立成功";
                await RefreshStatusAsync();
            }
            else
            {
                Config.Baseline.Result =
                    $"基线建立失败：{final.Result}" +
                    (final.Reason.HasValue ? $" / {final.Reason}" : "") +
                    "。常见原因：采样窗口内读数不稳定（CV 超限）、有丢帧、或切到了参考支路。";
                StatusMessage = "基线建立失败";
            }
        }
        catch (OperationCanceledException)
        {
            Config.Baseline.Result = "已取消。设备可能仍在完成本次建立，请查询状态确认。";
            StatusMessage = "已取消基线建立";
        }
        catch (DeviceException ex)
        {
            Config.Baseline.Result = $"基线建立异常：{ex.Message}";
        }
        finally
        {
            Config.Baseline.Running = false;
            _baselineAccumulator = null;
            _baselineCts?.Dispose();
            _baselineCts = null;
        }
    }

    public void CancelBaseline() => _baselineCts?.Cancel();

    private bool Set<T>(ref T field, T value, [CallerMemberName] string? name = null)
    {
        if (EqualityComparer<T>.Default.Equals(field, value))
            return false;
        field = value;
        Notify(name);
        return true;
    }

    private void Notify(string? name) => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
}
