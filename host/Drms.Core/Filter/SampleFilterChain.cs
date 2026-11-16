using System.Globalization;

namespace Drms.Core.Filter;

/// <summary>滤波模式。三者互斥（不串联）。</summary>
public enum FilterMode
{
    /// <summary>原始：旁路，不改变数据。</summary>
    Bypass = 0,
    /// <summary>工频谐波陷波器组（本方案）。</summary>
    MainsNotch = 1,
    /// <summary>单周期滑动平均：与陷波互斥，仅用于对比。</summary>
    PeriodAverage = 2,
}

/// <summary>
/// 滤波配置。默认值取自规格：50 Hz、谐波 [1,2,3,5]、B=2 Hz、建立 2 s。
/// 注意"不默认启用全部谐波"——只列选定倍数。
/// </summary>
public sealed record FilterSettings(
    FilterMode Mode = FilterMode.Bypass,
    double LineHz = 50.0,
    int[]? Harmonics = null,
    double BandwidthHz = 2.0,
    double EstablishSeconds = 2.0)
{
    public static readonly int[] DefaultHarmonics = [1, 2, 3, 5];

    public int[] EffectiveHarmonics => Harmonics ?? DefaultHarmonics;

    /// <summary>配置与采样率是否等价（用于判断是否需要重建系数）。</summary>
    public bool EquivalentTo(FilterSettings other, double sampleRateHz, double otherRateHz)
        => Mode == other.Mode && LineHz.Equals(other.LineHz) && BandwidthHz.Equals(other.BandwidthHz)
           && sampleRateHz.Equals(otherRateHz)
           && EffectiveHarmonics.SequenceEqual(other.EffectiveHarmonics);
}

/// <summary>
/// 逐样本滤波链路：负责"模式选择 + 状态重置 + 建立期标记"，
/// 数学部分在 <see cref="MainsNotchBank"/> / <see cref="PeriodAverageFilter"/>。
///
/// 重置条件（规格 §5，全部实现）：
///   · 采样序号不连续（缺口或乱序）；
///   · 帧无效 / 电阻不可计算；
///   · 采样率变化、滤波配置或模式变化；
///   · 显式 <see cref="Reset"/>（重连、重启由调用方触发）。
/// 不补零、不重复旧样本、不跨缺口拼接。
///
/// 建立期：重置后 <c>EstablishSeconds × fs</c> 个样本内 <see cref="Filtered"/> 标记为
/// "建立中"，期间不得用于自动基线与判级。2 s 是保守候选值，不是收敛上限。
///
/// 线程模型：单线程（RAW 读线程），非线程安全。
/// </summary>
public sealed class SampleFilterChain
{
    private FilterSettings _settings = new();
    private double _sampleRate;
    private MainsNotchBank? _notch;
    private PeriodAverageFilter? _average;
    private bool _primed;
    private ulong _lastSequence;
    private bool _hasSequence;
    private long _sinceReset;

    /// <summary>当前配置。</summary>
    public FilterSettings Settings => _settings;
    public double SampleRateHz => _sampleRate;
    public FilterMode Mode => _settings.Mode;
    /// <summary>算法版本串（写进导出元数据）。</summary>
    public string Version => _settings.Mode switch
    {
        FilterMode.MainsNotch => _notch?.Version ?? "mains-notch/1",
        FilterMode.PeriodAverage => _average?.Version ?? "period-avg/1",
        _ => "bypass",
    };

    /// <summary>重置过多少次（诊断用）。</summary>
    public int ResetCount { get; private set; }

    /// <summary>重置原因（最近一次，诊断与界面提示用）。</summary>
    public string? LastResetReason { get; private set; }

    /// <summary>
    /// 配置（采样率 + 模式 + 参数）。任何变化都会重建系数并清状态。
    /// 返回是否需要重置（调用方据此标记建立期，本方法内部已重置）。
    /// </summary>
    public void Configure(double sampleRateHz, FilterSettings settings)
    {
        if (!(sampleRateHz > 0) || !double.IsFinite(sampleRateHz))
            throw new ArgumentOutOfRangeException(nameof(sampleRateHz));
        _settings = settings;
        _sampleRate = sampleRateHz;
        _notch = settings.Mode == FilterMode.MainsNotch
            ? new MainsNotchBank(sampleRateHz, settings.LineHz, settings.EffectiveHarmonics, settings.BandwidthHz)
            : null;
        _average = settings.Mode == FilterMode.PeriodAverage
            ? new PeriodAverageFilter(sampleRateHz, settings.LineHz)
            : null;
        Reset("配置变化");
    }

    /// <summary>清空全部状态；下一次有效样本重新初始化（不补零）。</summary>
    public void Reset(string reason)
    {
        _notch?.Reset();
        _average?.Reset();
        _primed = false;
        _hasSequence = false;
        _sinceReset = 0;
        ResetCount++;
        LastResetReason = reason;
    }

    /// <summary>建立期样本数阈值。</summary>
    private long EstablishSamples =>
        (long)Math.Round(_settings.EstablishSeconds * _sampleRate);

    /// <summary>是否仍在建立期（重置后不足 establish 秒）。</summary>
    public bool IsEstablishing => _sinceReset < EstablishSamples;

    /// <summary>一次逐样本处理的结果。</summary>
    public readonly record struct Result(
        double Value,          // 滤波后值（Bypass / 建立期初值时等于输入）
        bool Establishing,     // 建立中（不得用于自动基线与判级）
        bool Reset,            // 本次调用触发了重置
        string? ResetReason);

    /// <summary>
    /// 处理一个样本。
    /// </summary>
    /// <param name="sequence">样本序号：不连续即重置（缺口/乱序都不跨接）。</param>
    /// <param name="ohms">已计算的电阻值。</param>
    /// <param name="valid">该样本是否有效（帧 CRC/格式/激励/量程）。</param>
    public Result Process(ulong sequence, double ohms, bool valid)
    {
        string? resetReason = null;

        // 1) 连续性：序号必须严格 +1（首样本建立基准）
        if (_hasSequence && sequence != _lastSequence + 1)
        {
            resetReason = sequence <= _lastSequence ? "序号乱序" : "序号缺口";
        }
        _hasSequence = true;
        _lastSequence = sequence;

        // 2) 无效样本：不参与滤波，且清状态（不补零、不沿用旧值）
        if (!valid || !double.IsFinite(ohms))
            resetReason ??= "样本无效";

        if (resetReason is not null)
        {
            Reset(resetReason);
            return new Result(double.NaN, Establishing: true, Reset: true, resetReason);
        }

        // 3) 首次有效样本：用 x0 初始化（避免从零启动的跳变）
        if (!_primed)
        {
            _notch?.Initialize(ohms);
            _average?.Initialize(ohms);
            _primed = true;
            _sinceReset = Math.Max(_sinceReset, 1);
            return new Result(ohms, IsEstablishing, Reset: false, null);
        }

        double value = _settings.Mode switch
        {
            FilterMode.MainsNotch => _notch!.Step(ohms),
            FilterMode.PeriodAverage => _average!.Step(ohms),
            _ => ohms,
        };

        if (!double.IsFinite(value))
        {
            Reset("滤波输出非有限（数值异常）");
            return new Result(double.NaN, Establishing: true, Reset: true, "数值异常");
        }

        _sinceReset++;
        return new Result(value, IsEstablishing, Reset: false, null);
    }

    /// <summary>人类可读的配置摘要（界面与导出元数据用）。</summary>
    public string Describe() => _settings.Mode switch
    {
        FilterMode.MainsNotch => string.Create(CultureInfo.InvariantCulture,
            $"谐波陷波 {string.Join('/', _settings.EffectiveHarmonics)}×{_settings.LineHz:F1}Hz B={_settings.BandwidthHz:F2}Hz"),
        FilterMode.PeriodAverage => string.Create(CultureInfo.InvariantCulture,
            $"周期平均 {_settings.LineHz:F1}Hz（{_average?.Window ?? 0} 样本）"),
        _ => "原始（旁路）",
    };
}
