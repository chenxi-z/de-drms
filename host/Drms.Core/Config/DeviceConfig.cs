using Drms.Core.Protocol;

namespace Drms.Core.Config;

/// <summary>
/// 一份可下发的完整配置。协议要求 APPLY_CONFIG 的 settings 包含
/// tag 72–83 全部字段（tag 84 interval_names 可选），缺一项设备就整体拒绝。
///
/// 为什么不暴露"只改一个字段"的接口：设备端校验是"整份接受或整份拒绝"，
/// 上位机这边也必须按整份构造，否则很容易发出被拒的半份配置。
/// </summary>
public sealed class DeviceConfig
{
    public required uint RateHz { get; init; }
    public required uint RecordDurationMs { get; init; }
    public required ulong TauUs { get; init; }
    public required ulong WarmupUs { get; init; }
    public required ulong ConfirmUs { get; init; }
    public required ulong StaleTimeoutUs { get; init; }
    public required IReadOnlyList<MonitorInterval> Intervals { get; init; }

    /// <summary>设备别名。utf8，无 NUL，最多 32 字节；空串合法。</summary>
    public string Alias { get; init; } = "";

    /// <summary>试件标识。同上限制。</summary>
    public string Specimen { get; init; } = "";

    public required uint BaselineMinCount { get; init; }
    public required ulong BaselineMinUs { get; init; }
    public required double BaselineMaxCv { get; init; }

    /// <summary>区间名称表。键是区间 id。</summary>
    public IReadOnlyDictionary<ushort, string>? IntervalNames { get; init; }

    /// <summary>
    /// 保守默认值。**这些是占位值，不是标定结论**——真实阈值必须由
    /// 该批试件的 R/R₀–位移曲线确定（AGENTS.md「需外部输入」）。
    /// 基线 4096 样本 / 30 s / CV 0.1%：@4 kSPS 约 1.02 s 就能采满 4096 样本，
    /// 所以实际由 30 s 时长主导，换来的是足够稳的统计。
    /// </summary>
    public static DeviceConfig ConservativeDefault(
        IReadOnlyList<MonitorInterval> intervals,
        ulong baselineMinUs = 30_000_000,
        uint baselineMinCount = 4096,
        double baselineMaxCv = 0.001)
        => new()
        {
            // 监测参数与出厂默认一致：4 kSPS、不滤波（tau=0）、无建立窗口。
            // stale_timeout 必须 ≥ max(10000, ceil(128000000/rate))，
            // 4 kSPS 下下限是 32000 µs，取 100000 µs（100 ms）留余量。
            RateHz = 4000,
            RecordDurationMs = 0,
            TauUs = 0,
            WarmupUs = 0,
            ConfirmUs = 0,
            StaleTimeoutUs = 100_000,
            Intervals = intervals,
            Alias = "",
            Specimen = "",
            BaselineMinCount = baselineMinCount,
            BaselineMinUs = baselineMinUs,
            BaselineMaxCv = baselineMaxCv,
        };

    /// <summary>
    /// 把配置编码成 settings 的嵌套 TLV 字节。
    /// 字段顺序无关，但保证 72–83 齐全——设备端缺项会整体拒绝。
    /// </summary>
    public byte[] EncodeSettings()
    {
        if (Intervals.Count > 16)
            throw new InvalidOperationException($"区间最多 16 条，当前 {Intervals.Count}");

        // stale_timeout 的设备端下限：max(10000, ceil(128000000/rate))，见 drms_config_wire.c
        ulong rate = RateHz;
        ulong minStale = (128_000_000UL + rate - 1) / rate;
        if (minStale < 10_000UL)
            minStale = 10_000UL;
        if (StaleTimeoutUs < minStale)
            throw new InvalidOperationException(
                $"stale_timeout_us={StaleTimeoutUs} 低于设备下限 {minStale}");

        var tlv = new TlvWriter()
            .AddU32(Tag.RateHz, RateHz)
            .AddU32(Tag.RecordDurationMs, RecordDurationMs)
            .AddU64(Tag.TauUs, TauUs)
            .AddU64(Tag.WarmupUs, WarmupUs)
            .AddU64(Tag.ConfirmUs, ConfirmUs)
            .AddU64(Tag.StaleTimeoutUs, StaleTimeoutUs);

        if (Intervals.Count > 0)
            tlv.AddRaw(Tag.Intervals, Messages.EncodeIntervals(Intervals));

        // alias / specimen 始终写（空串也是合法值），避免"有时有有时没有"的歧义
        tlv.AddRaw(Tag.Alias, System.Text.Encoding.UTF8.GetBytes(Alias));
        tlv.AddRaw(Tag.Specimen, System.Text.Encoding.UTF8.GetBytes(Specimen));
        tlv.AddU32(Tag.BaselineMinCount, BaselineMinCount);
        tlv.AddU64(Tag.BaselineMinUs, BaselineMinUs);
        tlv.AddF64(Tag.BaselineMaxCv, BaselineMaxCv);

        if (IntervalNames is { Count: > 0 })
            tlv.AddRaw(Tag.IntervalNames, EncodeIntervalNames(IntervalNames));

        return tlv.ToArray();
    }

    /// <summary>区间名称表：重复 [id:u16][len:u8][utf8]。</summary>
    private static byte[] EncodeIntervalNames(IReadOnlyDictionary<ushort, string> names)
    {
        var buffer = new List<byte>();
        foreach ((ushort id, string name) in names.OrderBy(p => p.Key))
        {
            byte[] bytes = System.Text.Encoding.UTF8.GetBytes(name);
            if (bytes.Length > 16)
                throw new InvalidOperationException($"区间 {id} 名称超过 16 字节");
            buffer.Add((byte)(id & 0xFF));
            buffer.Add((byte)(id >> 8));
            buffer.Add((byte)bytes.Length);
            buffer.AddRange(bytes);
        }
        return buffer.ToArray();
    }
}

/// <summary>
/// 按百分比阈值生成区间表。
///
/// 为什么要这个：用户关心的是"涨了多少个百分点算黄/橙/红"，
/// 而协议要的是升序不重叠的 lo/hi 区间。手工把百分比翻成 lo/hi 容易错位，
/// 这里一次性做好并复用同一套校验。
///
/// 固件校验规则（drms_config_wire.c）：
///   · lo &lt; hi
///   · h ≥ 0 且 2h &lt; hi-lo（回差不能盖住整个区间）
///   · 区间必须按 lo 升序，且相邻不能重叠
///     有间隙时要求 prev_h + h &lt; lo - prev_hi（两边回差之和不能越过间隙）
///   · id 唯一，level ≤ 3
/// </summary>
public static class IntervalBuilder
{
    /// <summary>
    /// 绿色下界的容差（百分比）。试件电阻小幅下降是正常现象，
    /// 给下行留 10% 空间，避免正常波动被判成"掉出区间表"。
    /// </summary>
    public const double LowerTolerancePercent = 10.0;

    /// <summary>一个等级的上界百分比。绿色下界固定为 0%。</summary>
    public sealed record Band(string Name, byte Level, double UpperPercent, double HysteresisPercent);

    /// <summary>
    /// 由"上界百分比"列表生成连续区间。
    ///
    /// 例：绿 ≤1%、黄 ≤3%、橙 ≤6%、红 ≤20%
    ///   → [0,1.01) [1.01,1.03) [1.03,1.06) [1.06,1.20)
    /// 注意这里转换为 R/R₀ 是 1 + pct/100，所以 1% 上界 = ratio 1.01。
    /// </summary>
    public static List<MonitorInterval> FromPercentBands(IReadOnlyList<Band> bands,
                                                        out List<string> problems)
    {
        problems = new List<string>();
        var result = new List<MonitorInterval>();
        if (bands.Count == 0)
        {
            problems.Add("至少要有一条区间");
            return result;
        }
        if (bands.Count > 16)
        {
            problems.Add($"区间最多 16 条，当前 {bands.Count}");
            return result;
        }

        // 绿色下界：默认从 -10% 起，而不是 0%。
        //
        // 为什么不是 0%：实测中 443 Ω 试件的 ratio 在 0.99–1.01 之间正常波动，
        // 若区间从 1.000 起，任何低于基线的点都会掉出整张表、被报成"未映射"。
        // 试件电阻小幅下降是常见且无害的（温度、接触改善），不该当作异常。
        // 曲线规格 §3.6 的默认区间也是 0.9 起。真正的损伤判据是"上升"，
        // 所以下行留出 -10% 的容差，超出才算异常。
        double lower = -LowerTolerancePercent;
        for (int i = 0; i < bands.Count; i++)
        {
            Band band = bands[i];
            double upper = band.UpperPercent;

            if (upper <= lower)
            {
                problems.Add($"“{band.Name}”上界 {upper}% 必须大于下界 {lower}%");
                continue;
            }
            double hyst = band.HysteresisPercent;
            if (hyst < 0)
            {
                problems.Add($"“{band.Name}”回差不能为负");
                continue;
            }
            // 2h < hi-lo 是设备端硬约束，换算成百分比就是 2h < upper-lower
            if (2 * hyst >= upper - lower)
            {
                problems.Add(
                    $"“{band.Name}”回差 {hyst}% 太大：2×回差必须小于区间宽度 {upper - lower:F2}%");
                continue;
            }

            result.Add(new MonitorInterval
            {
                Low = 1.0 + lower / 100.0,
                High = 1.0 + upper / 100.0,
                Hysteresis = hyst / 100.0,
                Id = (ushort)(i + 1),
                Level = band.Level,
                // 最后一条上界闭合，这样恰好等于上界时仍落在本区间
                LastUpperClosed = i == bands.Count - 1,
            });
            lower = upper;
        }
        return result;
    }

    /// <summary>
    /// 反向：从已有区间表推出"上界百分比"表示。
    /// 用于把设备上读回来的配置填回界面。
    /// </summary>
    public static List<Band> ToPercentBands(IReadOnlyList<MonitorInterval> intervals,
                                            IReadOnlyList<string>? names = null)
    {
        var bands = new List<Band>();
        for (int i = 0; i < intervals.Count; i++)
        {
            MonitorInterval iv = intervals[i];
            string name = names is not null && i < names.Count ? names[i] : $"等级 {iv.Level}";
            bands.Add(new Band(name, iv.Level,
                               (iv.High - 1.0) * 100.0,
                               iv.Hysteresis * 100.0));
        }
        return bands;
    }

    /// <summary>
    /// 按固件同样的规则校验一份区间表。返回空列表表示通过。
    ///
    /// 这是"本地先拦一道"——设备端也会拒，但让用户在这里就看到具体哪条不对，
    /// 比发出去等一个笼统的 INVALID 有用得多。
    /// </summary>
    public static List<string> Validate(IReadOnlyList<MonitorInterval> intervals)
    {
        var problems = new List<string>();
        if (intervals.Count > 16)
            problems.Add($"区间最多 16 条，当前 {intervals.Count}");

        var seenIds = new HashSet<ushort>();
        for (int i = 0; i < intervals.Count; i++)
        {
            MonitorInterval iv = intervals[i];
            string tag = $"第 {i + 1} 条(id={iv.Id})";

            if (!seenIds.Add(iv.Id))
                problems.Add($"{tag}：id 重复");
            if (iv.Level > 3)
                problems.Add($"{tag}：level={iv.Level} 超出 0..3");
            if (iv.Direction > 2)
                problems.Add($"{tag}：direction={iv.Direction} 超出 0..2");
            if (!(iv.Low < iv.High))
                problems.Add($"{tag}：lo={iv.Low} 必须小于 hi={iv.High}");
            if (double.IsNaN(iv.Low) || double.IsInfinity(iv.Low) ||
                double.IsNaN(iv.High) || double.IsInfinity(iv.High))
            {
                problems.Add($"{tag}：lo/hi 必须是有限值");
                continue;
            }
            if (iv.Hysteresis < 0 || 2 * iv.Hysteresis >= iv.High - iv.Low)
                problems.Add($"{tag}：回差 {iv.Hysteresis} 不合法（需 ≥0 且 2h < hi-lo）");
            if (iv.LastUpperClosed && i + 1 != intervals.Count)
                problems.Add($"{tag}：只有最后一条可以闭合上界");

            if (i > 0)
            {
                MonitorInterval prev = intervals[i - 1];
                if (iv.Low < prev.High)
                    problems.Add($"{tag}：与上一条重叠（lo={iv.Low} < 上一条 hi={prev.High}）");
                else if (iv.Low > prev.High && !(prev.Hysteresis + iv.Hysteresis < iv.Low - prev.High))
                    problems.Add($"{tag}：与上一条的间隙小于两边回差之和");
            }
        }
        return problems;
    }
}
