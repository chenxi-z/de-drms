using Drms.Core.Config;
using Drms.Core.Protocol;
using Drms.Core.Session;
using Xunit;

namespace Drms.Core.Tests;

/// <summary>
/// 配置组装与区间表测试。
///
/// 重点验证"上位机生成的区间能通过固件校验"——固件那套规则（升序、
/// 不重叠、2h &lt; hi-lo、间隙要够宽）如果这里生成时没守住，
/// 用户点下发只会得到一个笼统的 INVALID。
/// </summary>
public class ConfigTests
{
    private static readonly IntervalBuilder.Band[] DefaultBands =
    [
        new("绿", 0, 1.0, 0.2),
        new("黄", 1, 3.0, 0.2),
        new("橙", 2, 6.0, 0.2),
        new("红", 3, 20.0, 0.2),
    ];

    [Fact]
    public void PercentBands_ProduceAscendingNonOverlappingIntervals()
    {
        List<MonitorInterval> intervals =
            IntervalBuilder.FromPercentBands(DefaultBands, out List<string> problems);

        Assert.Empty(problems);
        Assert.Equal(4, intervals.Count);

        // 绿色从 -10% 起（ratio 0.90），上界 1% → 1.01
        Assert.Equal(0.90, intervals[0].Low, 12);
        Assert.Equal(1.01, intervals[0].High, 12);
        Assert.Equal(0, intervals[0].Level);
        Assert.Equal(1, intervals[0].Id);

        // 红色上界 20% → 1.20，且末区间闭合
        Assert.Equal(1.20, intervals[3].High, 12);
        Assert.True(intervals[3].LastUpperClosed);
        Assert.False(intervals[0].LastUpperClosed);

        // 相邻首尾相接，没有重叠也没有间隙
        for (int i = 1; i < intervals.Count; i++)
            Assert.Equal(intervals[i - 1].High, intervals[i].Low, 12);
    }

    [Fact]
    public void PercentBands_PassTheFirmwareValidationRules()
    {
        List<MonitorInterval> intervals =
            IntervalBuilder.FromPercentBands(DefaultBands, out _);

        // Validate 复刻了 drms_config_wire.c 的规则
        Assert.Empty(IntervalBuilder.Validate(intervals));
    }

    [Fact]
    public void PercentBands_RejectNonIncreasingUpperBounds()
    {
        IntervalBuilder.Band[] bad =
        [
            new("绿", 0, 3.0, 0.1),
            new("黄", 1, 2.0, 0.1), // 上界反而更小
        ];
        IntervalBuilder.FromPercentBands(bad, out List<string> problems);
        Assert.NotEmpty(problems);
        Assert.Contains(problems, p => p.Contains("必须大于下界"));
    }

    [Fact]
    public void PercentBands_RejectHysteresisTooLargeForBand()
    {
        // 绿色下界是 -10%，所以单条绿色区间宽度为 11%（-10%→1%）。
        // 要触发 2h ≥ 宽度，得把回差设得超过 5.5%。
        IntervalBuilder.Band[] bad = [new("绿", 0, 1.0, 6.0)];
        IntervalBuilder.FromPercentBands(bad, out List<string> problems);
        Assert.Contains(problems, p => p.Contains("2×回差"));
    }

    [Fact]
    public void PercentBands_RejectNegativeHysteresis()
    {
        IntervalBuilder.Band[] bad = [new("绿", 0, 1.0, -0.1)];
        IntervalBuilder.FromPercentBands(bad, out List<string> problems);
        Assert.Contains(problems, p => p.Contains("不能为负"));
    }

    [Fact]
    public void PercentBands_RequireAtLeastOneBand()
    {
        IntervalBuilder.FromPercentBands([], out List<string> problems);
        Assert.Contains(problems, p => p.Contains("至少要有一条"));
    }

    [Fact]
    public void Validate_DetectsOverlap()
    {
        var intervals = new[]
        {
            new MonitorInterval { Low = 1.0, High = 1.05, Hysteresis = 0.001, Id = 1, Level = 0 },
            new MonitorInterval { Low = 1.04, High = 1.10, Hysteresis = 0.001, Id = 2, Level = 1 },
        };
        List<string> problems = IntervalBuilder.Validate(intervals);
        Assert.Contains(problems, p => p.Contains("重叠"));
    }

    [Fact]
    public void Validate_DetectsGapSmallerThanHysteresisSum()
    {
        // 间隙 1.05→1.06 只有 0.01，但两边回差各 0.004，和 0.008 < 0.01 通过；
        // 加大到各 0.006（和 0.012 > 0.01）就应被拒。
        var intervals = new[]
        {
            new MonitorInterval { Low = 1.0, High = 1.05, Hysteresis = 0.006, Id = 1, Level = 0 },
            new MonitorInterval { Low = 1.06, High = 1.10, Hysteresis = 0.006, Id = 2, Level = 1 },
        };
        List<string> problems = IntervalBuilder.Validate(intervals);
        Assert.Contains(problems, p => p.Contains("间隙"));
    }

    [Fact]
    public void Validate_DetectsDuplicateIdAndBadLevel()
    {
        var intervals = new[]
        {
            new MonitorInterval { Low = 1.0, High = 1.05, Hysteresis = 0.001, Id = 7, Level = 5 },
            new MonitorInterval { Low = 1.05, High = 1.10, Hysteresis = 0.001, Id = 7, Level = 0 },
        };
        List<string> problems = IntervalBuilder.Validate(intervals);
        Assert.Contains(problems, p => p.Contains("id 重复"));
        Assert.Contains(problems, p => p.Contains("level=5"));
    }

    [Fact]
    public void ToPercentBands_RoundTripsFromIntervals()
    {
        List<MonitorInterval> original =
            IntervalBuilder.FromPercentBands(DefaultBands, out _);
        List<IntervalBuilder.Band> bands = IntervalBuilder.ToPercentBands(original);

        Assert.Equal(4, bands.Count);
        Assert.Equal(1.0, bands[0].UpperPercent, 9);
        Assert.Equal(3.0, bands[1].UpperPercent, 9);
        Assert.Equal(20.0, bands[3].UpperPercent, 9);
        Assert.Equal(0.2, bands[0].HysteresisPercent, 9);
    }

    [Fact]
    public void DeviceConfig_EncodesAllMandatoryFields()
    {
        List<MonitorInterval> intervals =
            IntervalBuilder.FromPercentBands(DefaultBands, out _);
        DeviceConfig config = DeviceConfig.ConservativeDefault(intervals);

        byte[] settings = config.EncodeSettings();
        Dictionary<ushort, TlvField> fields =
            TlvReader.Index(TlvReader.Parse(settings));

        // 协议要求 72–83 全部出现
        foreach (ushort tag in new ushort[]
                 {
                     Tag.RateHz, Tag.RecordDurationMs, Tag.TauUs, Tag.WarmupUs,
                     Tag.ConfirmUs, Tag.StaleTimeoutUs, Tag.Intervals, Tag.Alias,
                     Tag.Specimen, Tag.BaselineMinCount, Tag.BaselineMinUs,
                     Tag.BaselineMaxCv,
                 })
        {
            Assert.True(fields.ContainsKey(tag), $"缺少字段 tag {tag}");
        }

        Assert.Equal(4000u, fields[Tag.RateHz].AsU32());
        Assert.Equal(4096u, fields[Tag.BaselineMinCount].AsU32());
        Assert.Equal(30_000_000ul, fields[Tag.BaselineMinUs].AsU64());
        Assert.Equal(0.001, fields[Tag.BaselineMaxCv].AsDouble(), 12);

        // 区间表应能原样解回来
        List<MonitorInterval> parsed = Messages.ParseIntervals(fields[Tag.Intervals].Value);
        Assert.Equal(4, parsed.Count);
        Assert.Equal(1.01, parsed[0].High, 12);
    }

    [Fact]
    public void DeviceConfig_RejectsStaleTimeoutBelowDeviceFloor()
    {
        // 4 kSPS 下限 = ceil(128000000/4000) = 32000 µs
        var config = new DeviceConfig
        {
            RateHz = 4000,
            RecordDurationMs = 0,
            TauUs = 0,
            WarmupUs = 0,
            ConfirmUs = 0,
            StaleTimeoutUs = 1000, // 远低于 32000
            Intervals = [],
            BaselineMinCount = 4096,
            BaselineMinUs = 30_000_000,
            BaselineMaxCv = 0.001,
        };
        InvalidOperationException ex =
            Assert.Throws<InvalidOperationException>(() => config.EncodeSettings());
        Assert.Contains("32000", ex.Message);
    }

    [Fact]
    public void MonitorIntervalHysteresis_IsStrictlyLessThanHalfWidth()
    {
        // 固件规则：2h < hi-lo。用默认参数生成的区间必须满足。
        foreach (MonitorInterval iv in IntervalBuilder.FromPercentBands(DefaultBands, out _))
            Assert.True(2 * iv.Hysteresis < iv.High - iv.Low);
    }

    // ---- 基线统计 ----

    [Fact]
    public void BaselineAccumulator_MatchesWelfordReference()
    {
        var acc = new BaselineAccumulator(minCount: 0, minDurationUs: 0, maxCv: 0.001);
        double[] values = [100.0, 101.0, 99.0, 100.5];
        foreach (double v in values)
            acc.Feed(v, 250);

        double mean = values.Average();
        double sd = Math.Sqrt(values.Sum(v => (v - mean) * (v - mean)) / (values.Length - 1));

        Assert.Equal((ulong)values.Length, acc.Count);
        Assert.Equal(mean, acc.Mean, 12);
        Assert.Equal(sd, acc.StandardDeviation, 12);
    }

    [Fact]
    public void BaselineAccumulator_TracksProgressAgainstBothLimits()
    {
        // 需要 8 个样本 且 2000 µs
        var acc = new BaselineAccumulator(minCount: 8, minDurationUs: 2000, maxCv: 0);
        for (int i = 0; i < 4; i++)
            acc.Feed(100.0, 250);

        Assert.False(acc.HasEnoughSamples);          // 样本数不够
        Assert.Equal(0.5, acc.CountProgress, 6);
        Assert.Equal(0.5, acc.DurationProgress, 6);
        Assert.Equal(0.5, acc.Progress, 6);

        for (int i = 0; i < 4; i++)
            acc.Feed(100.0, 250);

        Assert.True(acc.HasEnoughSamples);
        Assert.True(acc.IsReady);
        Assert.Equal(1.0, acc.Progress, 6);
    }

    [Fact]
    public void BaselineAccumulator_FlagsInstabilityBeyondCvLimit()
    {
        var acc = new BaselineAccumulator(minCount: 4, minDurationUs: 0, maxCv: 0.001);
        // 均值 100，标准差约 5 → CV ≈ 5% ≫ 0.1%
        foreach (double v in new[] { 90.0, 110.0, 90.0, 110.0 })
            acc.Feed(v, 250);

        Assert.True(acc.HasEnoughSamples);
        Assert.False(acc.IsStable);
        Assert.False(acc.IsReady);
        Assert.True(acc.Cv > 0.001);
    }

    [Fact]
    public void BaselineAccumulator_IgnoresNonFiniteValues()
    {
        var acc = new BaselineAccumulator(minCount: 2, minDurationUs: 0, maxCv: 0);
        acc.Feed(double.NaN, 250);
        acc.Feed(double.PositiveInfinity, 250);
        Assert.Equal(0ul, acc.Count);
    }

    [Fact]
    public void BaselineRunner_PreconditionsExplainWhyBaselineIsBlocked()
    {
        var status = new StatusReply
        {
            StatusRevision = 1, MonoUs = 0,
            Acquisition = Acquisition.Reference,   // REF 模式
            Recording = Recording.Idle,
            Medium = Medium.Ready,
            Owner = StorageOwner.Local,
            Maintenance = Maintenance.Idle,
            SampleGeneration = 1, Rate = 4000, Fresh = true,
            Classification = Classification.Invalid, Quality = 0,
            RunningVersion = 0, SavedVersion = 0, BaselineVersion = 0, CalibrationVersion = 0,
            Fault = 0, RtcValid = false, MediaGeneration = 1,
        };

        List<string> problems = BaselineRunner.CheckPreconditions(status, baselinePolicyCount: 0);

        Assert.Contains(problems, p => p.Contains("参考支路"));
        Assert.Contains(problems, p => p.Contains("基线策略"));
    }

    [Fact]
    public void BaselineRunner_PassesWhenEverythingIsReady()
    {
        var status = new StatusReply
        {
            StatusRevision = 1, MonoUs = 0,
            Acquisition = Acquisition.Monitor,
            Recording = Recording.Idle,
            Medium = Medium.Ready,
            Owner = StorageOwner.Local,
            Maintenance = Maintenance.Idle,
            SampleGeneration = 1, Rate = 4000, Fresh = true,
            Classification = Classification.Unconfigured, Quality = 0,
            RunningVersion = 0, SavedVersion = 0, BaselineVersion = 0, CalibrationVersion = 0,
            Fault = 0, RtcValid = false, MediaGeneration = 1,
        };

        Assert.Empty(BaselineRunner.CheckPreconditions(status, baselinePolicyCount: 4096));
    }
}
