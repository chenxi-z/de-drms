using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Runtime.CompilerServices;
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
