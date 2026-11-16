using Drms.Core.Protocol;

namespace Drms.Core.Record;

/// <summary>
/// RAW 流的**流式分桶**：把 4 kSPS 的逐帧数据压成固定宽度的桶（默认 100 ms），
/// 每个桶保留 min / max / mean。界面只画桶，不画原始帧——1 小时 4 kSPS 是
/// 1440 万点，逐点画既没意义（一列像素覆盖几十点）也会把内存吃光。
///
/// 为什么是 min/max 而不是平均：曲线规格 §7.4 要求"抽稀必须保尖峰"，
/// 平均值会把瞬态抹平；包络 + 均值线两者都画，既看趋势也不丢尖峰。
///
/// 线程模型：<see cref="Append"/> 在 RAW 读线程调用，<see cref="Snapshot"/>
/// 在 UI 线程调用；内部用一把锁保护环形缓冲（写入很快，临界区很小）。
/// </summary>
public sealed class RawBucketSeries
{
    private readonly object _sync = new();
    private readonly double[] _startSeconds;
    private readonly double[] _min;
    private readonly double[] _max;
    private readonly double[] _mean;
    private readonly double[] _count;   // 桶内样本数，用于判断桶是否已满
    private readonly int _framesPerBucket;
    private readonly int _capacity;

    private int _next;          // 下一个写入位置
    private int _filled;        // 已写入桶数（≤ capacity）
    private double _bucketMin = double.MaxValue;
    private double _bucketMax = double.MinValue;
    private double _bucketSum;
    private int _bucketCount;
    private double _bucketStart;

    /// <param name="framesPerBucket">每桶帧数（4 kSPS 下 400 = 100 ms）。</param>
    /// <param name="capacity">环形缓冲桶数（默认 600 = 60 s 视窗）。</param>
    public RawBucketSeries(int framesPerBucket, int capacity = 600)
    {
        if (framesPerBucket <= 0) throw new ArgumentOutOfRangeException(nameof(framesPerBucket));
        if (capacity <= 0) throw new ArgumentOutOfRangeException(nameof(capacity));
        _framesPerBucket = framesPerBucket;
        _capacity = capacity;
        _startSeconds = new double[capacity];
        _min = new double[capacity];
        _max = new double[capacity];
        _mean = new double[capacity];
        _count = new double[capacity];
        Array.Fill(_min, double.NaN);
        Array.Fill(_max, double.NaN);
        Array.Fill(_mean, double.NaN);
    }

    /// <summary>桶内帧数（用于显示"100 ms/点"）。</summary>
    public int FramesPerBucket => _framesPerBucket;

    /// <summary>已完成的桶数（不含正在累积的那个）。</summary>
    public int BucketCount { get { lock (_sync) return _filled; } }

    /// <summary>丢弃全部数据（重新开始流时调用）。</summary>
    public void Reset()
    {
        lock (_sync)
        {
            _next = _filled = 0;
            _bucketCount = 0;
            _bucketMin = double.MaxValue;
            _bucketMax = double.MinValue;
            _bucketSum = 0;
            Array.Fill(_min, double.NaN);
            Array.Fill(_max, double.NaN);
            Array.Fill(_mean, double.NaN);
            Array.Fill(_count, 0);
        }
    }

    /// <summary>
    /// 喂入一批 16 B 原始帧。<paramref name="scaleOhms"/> 是校准系数：
    /// kΩ = scale × V / I / 1000；<=0 时退化为比值 V/I（无单位，仅看噪声）。
    /// <paramref name="seconds"/> 是这一批的到达时刻（主机单调时间）。
    /// </summary>
    public void Append(ReadOnlySpan<byte> frames, double scaleOhms, double seconds)
    {
        lock (_sync)
        {
            for (int offset = 0; offset + 16 <= frames.Length; offset += 16)
            {
                ReadOnlySpan<byte> f = frames.Slice(offset, 16);
                int voltage = ((sbyte)f[3] << 16) | (f[4] << 8) | f[5];
                int sense = ((sbyte)f[6] << 16) | (f[7] << 8) | f[8];
                if (sense <= 4096 || voltage >= 8388606 || voltage <= -8388607) continue;  // 与解码器同口径
                double value = scaleOhms > 0 ? scaleOhms * voltage / sense / 1000.0 : (double)voltage / sense;
                if (double.IsNaN(value) || double.IsInfinity(value)) continue;

                if (_bucketCount == 0) _bucketStart = seconds;
                if (value < _bucketMin) _bucketMin = value;
                if (value > _bucketMax) _bucketMax = value;
                _bucketSum += value;
                _bucketCount++;
                if (_bucketCount < _framesPerBucket) continue;

                FlushBucketLocked();
            }
        }
    }

    /// <summary>把正在累积的半个桶也写出去（停止流时调用，避免丢掉尾巴）。</summary>
    public void FlushPartial()
    {
        lock (_sync)
        {
            if (_bucketCount > 0) FlushBucketLocked();
        }
    }

    private void FlushBucketLocked()
    {
        _startSeconds[_next] = _bucketStart;
        _min[_next] = _bucketMin;
        _max[_next] = _bucketMax;
        _mean[_next] = _bucketSum / _bucketCount;
        _count[_next] = _bucketCount;
        _next = (_next + 1) % _capacity;
        if (_filled < _capacity) _filled++;
        _bucketCount = 0;
        _bucketMin = double.MaxValue;
        _bucketMax = double.MinValue;
        _bucketSum = 0;
    }

    /// <summary>
    /// 取一份按时间排序的快照（供绘图）。返回的数组是新分配的，
    /// 调用方可以安全持有到下一帧——不与写入线程共享。
    /// </summary>
    public (double[] Seconds, double[] Min, double[] Max, double[] Mean) Snapshot()
    {
        lock (_sync)
        {
            int n = _filled;
            var seconds = new double[n];
            var min = new double[n];
            var max = new double[n];
            var mean = new double[n];
            int start = _filled < _capacity ? 0 : _next;   // 环形回绕：最老的桶位置
            for (int i = 0; i < n; i++)
            {
                int idx = (start + i) % _capacity;
                seconds[i] = _startSeconds[idx];
                min[i] = _min[idx];
                max[i] = _max[idx];
                mean[i] = _mean[idx];
            }
            return (seconds, min, max, mean);
        }
    }
}
