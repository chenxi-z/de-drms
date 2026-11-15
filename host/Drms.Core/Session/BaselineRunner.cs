using Drms.Core.Protocol;

namespace Drms.Core.Session;

/// <summary>
/// 建立 R₀ 过程中的实时统计。
///
/// 为什么上位机自己算：固件只在 BUILD_R0 结束时给出最终结果，
/// 过程中不公开均值与离散度。用户要决定"这段够不够稳、要不要重来"，
/// 就得看到实时进度——否则只能盲等，等完才知道失败。
///
/// 这里用 Welford 在线算法（与固件 drms_baseline.c 同一套），
/// 保证长窗口下数值稳定，不会因为累加平方出现大数相减的精度损失。
/// </summary>
public sealed class BaselineAccumulator
{
    private ulong _count;
    private double _mean;
    private double _m2;
    private ulong _durationUs;

    /// <summary>目标样本数。0 表示只受时长约束。</summary>
    public uint MinCount { get; }

    /// <summary>目标时长（µs）。</summary>
    public ulong MinDurationUs { get; }

    /// <summary>稳定限值：标准差/均值 的上界。0 表示不检查。</summary>
    public double MaxCv { get; }

    public BaselineAccumulator(uint minCount, ulong minDurationUs, double maxCv)
    {
        MinCount = minCount;
        MinDurationUs = minDurationUs;
        MaxCv = maxCv;
    }

    public ulong Count => _count;
    public ulong DurationUs => _durationUs;

    /// <summary>当前均值。样本为 0 时为 0。</summary>
    public double Mean => _count == 0 ? 0 : _mean;

    /// <summary>样本标准差。样本不足 2 个时为 0。</summary>
    public double StandardDeviation => _count > 1 ? Math.Sqrt(_m2 / (_count - 1)) : 0;

    /// <summary>变异系数 = 标准差 / 均值。均值为 0 或样本不足时返回 NaN。</summary>
    public double Cv => _count > 1 && _mean > 0 ? StandardDeviation / _mean : double.NaN;

    /// <summary>时长进度 0..1。</summary>
    public double DurationProgress =>
        MinDurationUs == 0 ? 1.0 : Math.Min(1.0, (double)_durationUs / MinDurationUs);

    /// <summary>样本数进度 0..1。</summary>
    public double CountProgress =>
        MinCount == 0 ? 1.0 : Math.Min(1.0, (double)_count / MinCount);

    /// <summary>总体进度：取两者较小值，因为两个条件都要满足。</summary>
    public double Progress => Math.Min(DurationProgress, CountProgress);

    /// <summary>是否已达时长与样本数要求（还没判稳定度）。</summary>
    public bool HasEnoughSamples =>
        _count >= MinCount && _durationUs >= MinDurationUs;

    /// <summary>是否满足稳定度。MaxCv 为 0 时视为不检查。</summary>
    public bool IsStable
    {
        get
        {
            if (MaxCv <= 0)
                return true;
            double cv = Cv;
            return !double.IsNaN(cv) && cv <= MaxCv;
        }
    }

    /// <summary>可以结束了吗：样本够 且 稳定。</summary>
    public bool IsReady => HasEnoughSamples && IsStable;

    /// <summary>
    /// 喂一个有效读数。<paramref name="sampleDtUs"/> 是该样本代表的采样间隔。
    ///
    /// 只应喂"有效"样本：设备侧建立基线时也只统计无故障帧，
    /// 这里若把无效帧算进去，均值就会与设备最终写入的 R₀ 不一致。
    /// </summary>
    public void Feed(double ohms, ulong sampleDtUs)
    {
        if (double.IsNaN(ohms) || double.IsInfinity(ohms))
            return;

        _count += 1;
        _durationUs += sampleDtUs;

        double delta = ohms - _mean;
        _mean += delta / _count;
        _m2 += delta * (ohms - _mean);
    }

    /// <summary>从采样率算单个采样间隔（µs）。</summary>
    public static ulong SampleDtUs(uint rateHz) =>
        rateHz == 0 ? 0 : 1_000_000UL / rateHz;
}

/// <summary>
/// 建立 R₀ 的完整流程封装：检查前置条件 → 下发 → 等结果。
///
/// 前置条件逐条对应固件 drms_application.c 的 DRMS_OP_BASELINE_R0 分支，
/// 在本地先查一遍能给出具体原因，而不是让用户对着一个 INVALID 猜。
/// </summary>
public sealed class BaselineRunner
{
    private readonly DeviceSession _session;

    public BaselineRunner(DeviceSession session) => _session = session;

    /// <summary>检查是否允许建立基线。返回空列表表示通过。</summary>
    public static List<string> CheckPreconditions(StatusReply status, uint? baselinePolicyCount)
    {
        var problems = new List<string>();

        if (status.Acquisition == Acquisition.Reference)
            problems.Add("设备处于参考支路（REF 模式），请先切回样品测量");
        else if (status.Acquisition != Acquisition.Monitor)
            problems.Add($"采集未在正常运行（当前 {status.Acquisition}）");

        if (status.Maintenance != Maintenance.Idle)
            problems.Add($"有维护任务在进行（当前 {status.Maintenance}）");

        if (status.Recording is Recording.Active or Recording.Starting)
            problems.Add("正在记录，建立基线前需先结束记录");

        if (baselinePolicyCount is null or 0)
            problems.Add("设备尚无基线策略配置，需先下发一次完整配置（含基线参数）");

        if (!status.Fresh)
            problems.Add("当前读数不新鲜，等采集稳定后重试");

        return problems;
    }

    /// <summary>
    /// 发起 BUILD_R0 并等待终态。<paramref name="timeout"/> 应覆盖设备预期的采样时长。
    /// </summary>
    public async Task<OperationReply> RunAsync(TimeSpan timeout,
                                               Action<OperationReply, TimeSpan>? onProgress = null,
                                               CancellationToken cancellation = default)
    {
        ulong operation = _session.BuildR0();
        return await OperationWaiter.WaitAsync(_session, operation, timeout,
                                               TimeSpan.FromMilliseconds(400), onProgress, cancellation);
    }
}
