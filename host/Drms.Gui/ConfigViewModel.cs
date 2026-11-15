using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using Drms.Core.Config;
using Drms.Core.Protocol;
using Drms.Core.Session;

namespace Drms.Gui;

/// <summary>界面上的一行区间。数字都用"百分比"表达，转换交给 IntervalBuilder。</summary>
public sealed class BandRow : INotifyPropertyChanged
{
    public event PropertyChangedEventHandler? PropertyChanged;

    private string _name = "";
    private string _upper = "";
    private string _hysteresis = "";
    private byte _level;

    public string Name { get => _name; set { _name = value; Notify(); } }

    /// <summary>上界百分比，例如 "1.0" 表示 1%。</summary>
    public string UpperPercent { get => _upper; set { _upper = value; Notify(); } }

    public string HysteresisPercent { get => _hysteresis; set { _hysteresis = value; Notify(); } }

    public byte Level { get => _level; set { _level = value; Notify(); } }

    private void Notify([CallerMemberName] string? n = null)
        => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(n));
}

/// <summary>
/// 建立 R₀ 的过程状态。界面绑这一组属性。
/// </summary>
public sealed class BaselinePanelState : INotifyPropertyChanged
{
    public event PropertyChangedEventHandler? PropertyChanged;

    private bool _running;
    public bool Running { get => _running; set { _running = value; Notify(); Notify(nameof(CanStart)); } }

    private string _result = "";
    public string Result { get => _result; set { _result = value; Notify(); } }

    private string _progress = "未开始";
    public string ProgressText { get => _progress; set { _progress = value; Notify(); } }

    private double _progressValue;
    public double ProgressValue { get => _progressValue; set { _progressValue = value; Notify(); } }

    private string _meanText = "—";
    public string MeanText { get => _meanText; set { _meanText = value; Notify(); } }

    private string _cvText = "—";
    public string CvText { get => _cvText; set { _cvText = value; Notify(); } }

    private string _stabilityText = "—";
    public string StabilityText { get => _stabilityText; set { _stabilityText = value; Notify(); } }

    private string _precondition = "";
    public string PreconditionText { get => _precondition; set { _precondition = value; Notify(); Notify(nameof(CanStart)); } }

    public bool CanStart => !Running && string.IsNullOrEmpty(PreconditionText);

    private void Notify([CallerMemberName] string? n = null)
        => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(n));
}

/// <summary>
/// 配置与基线界面的数据模型。
///
/// 界面用"上界百分比"编辑区间（用户关心百分比），真正下发前转换成
/// lo/hi 区间并跑一遍与固件同样的校验——把错误挡在本地。
/// </summary>
public sealed class ConfigViewModel : INotifyPropertyChanged
{
    public event PropertyChangedEventHandler? PropertyChanged;

    public ObservableCollection<BandRow> Bands { get; } = new();

    public BaselinePanelState Baseline { get; } = new();

    public ObservableCollection<string> BaselineDurations { get; } = new()
    {
        "10 秒", "30 秒", "60 秒", "180 秒",
    };

    private string _selectedDuration = "30 秒";
    public string SelectedDuration
    {
        get => _selectedDuration;
        set { if (_selectedDuration != value) { _selectedDuration = value; Notify(); } }
    }

    /// <summary>所选窗口对应的字节数（µs）。</summary>
    public ulong DurationUs => SelectedDuration switch
    {
        "10 秒" => 10_000_000ul,
        "60 秒" => 60_000_000ul,
        "180 秒" => 180_000_000ul,
        _ => 30_000_000ul,
    };

    private string _validationText = "";
    public string ValidationText { get => _validationText; set { _validationText = value; Notify(); } }

    private bool _configValid;
    public bool ConfigValid { get => _configValid; set { _configValid = value; Notify(); } }

    private string _applyResult = "";
    public string ApplyResult { get => _applyResult; set { _applyResult = value; Notify(); } }

    public ConfigViewModel()
    {
        // 保守默认：绿 ≤1%、黄 ≤3%、橙 ≤6%、红 ≤20%，回差各 0.2%。
        // 这些是占位值，真实阈值须由试件标定曲线确定。
        Bands.Add(new BandRow { Name = "绿", Level = 0, UpperPercent = "1.0", HysteresisPercent = "0.2" });
        Bands.Add(new BandRow { Name = "黄", Level = 1, UpperPercent = "3.0", HysteresisPercent = "0.2" });
        Bands.Add(new BandRow { Name = "橙", Level = 2, UpperPercent = "6.0", HysteresisPercent = "0.2" });
        Bands.Add(new BandRow { Name = "红", Level = 3, UpperPercent = "20.0", HysteresisPercent = "0.2" });

        foreach (BandRow row in Bands)
            row.PropertyChanged += (_, _) => Validate();

        Validate();
    }

    /// <summary>把界面上的百分比解析成区间表。解析失败时返回空表并写进校验信息。</summary>
    public List<MonitorInterval> BuildIntervals()
    {
        var bands = new List<IntervalBuilder.Band>();
        var parseErrors = new List<string>();

        for (int i = 0; i < Bands.Count; i++)
        {
            BandRow row = Bands[i];
            if (!double.TryParse(row.UpperPercent, out double upper))
            {
                parseErrors.Add($"第 {i + 1} 行上界“{row.UpperPercent}”不是数字");
                continue;
            }
            if (!double.TryParse(row.HysteresisPercent, out double hyst))
            {
                parseErrors.Add($"第 {i + 1} 行回差“{row.HysteresisPercent}”不是数字");
                continue;
            }
            bands.Add(new IntervalBuilder.Band(row.Name, row.Level, upper, hyst));
        }

        if (parseErrors.Count > 0)
        {
            ValidationText = string.Join("；", parseErrors);
            return [];
        }

        List<MonitorInterval> intervals =
            IntervalBuilder.FromPercentBands(bands, out List<string> problems);

        // 再用固件的规则复核一次，双重保险
        problems.AddRange(IntervalBuilder.Validate(intervals));

        if (problems.Count > 0)
        {
            ValidationText = string.Join("；", problems.Distinct());
            ConfigValid = false;
        }
        else
        {
            ValidationText = "区间表合法";
            ConfigValid = intervals.Count > 0;
        }
        return intervals;
    }

    public void Validate()
    {
        BuildIntervals();
    }

    /// <summary>按界面当前设置组装完整配置。</summary>
    public DeviceConfig BuildConfig()
    {
        List<MonitorInterval> intervals = BuildIntervals();
        return DeviceConfig.ConservativeDefault(intervals, DurationUs);
    }

    /// <summary>把设备读回来的区间填回界面。</summary>
    public void LoadFromDevice(IReadOnlyList<MonitorInterval> intervals)
    {
        if (intervals.Count == 0)
            return;
        Bands.Clear();
        List<IntervalBuilder.Band> bands = IntervalBuilder.ToPercentBands(intervals);
        for (int i = 0; i < bands.Count; i++)
        {
            IntervalBuilder.Band b = bands[i];
            var row = new BandRow
            {
                Name = b.Name,
                Level = b.Level,
                UpperPercent = b.UpperPercent.ToString("0.###"),
                HysteresisPercent = b.HysteresisPercent.ToString("0.###"),
            };
            row.PropertyChanged += (_, _) => Validate();
            Bands.Add(row);
        }
        Validate();
    }

    private void Notify([CallerMemberName] string? n = null)
        => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(n));
}
