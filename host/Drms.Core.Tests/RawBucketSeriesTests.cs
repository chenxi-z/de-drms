using System.Buffers.Binary;
using Drms.Core.Record;
using Xunit;

namespace Drms.Core.Tests;

/// <summary>
/// RAW 流式分桶：帧数→桶的边界、min/max 保尖峰、环形回绕、半个桶冲刷。
/// 契约：曲线规格 §7.4（抽稀必须保尖峰，包络不得用平均替代）。
/// </summary>
public class RawBucketSeriesTests
{
    /// <summary>造一帧：voltage/sense 决定比值，scale=1000 时 kΩ = V/I。</summary>
    private static byte[] Frames(params (int Voltage, int Sense)[] values)
    {
        var buffer = new byte[values.Length * 16];
        for (int i = 0; i < values.Length; i++)
        {
            var f = buffer.AsSpan(i * 16, 16);
            f[0] = 0x22; f[1] = 0x10;
            int v = values[i].Voltage, s = values[i].Sense;
            f[3] = (byte)(v >> 16); f[4] = (byte)(v >> 8); f[5] = (byte)v;
            f[6] = (byte)(s >> 16); f[7] = (byte)(s >> 8); f[8] = (byte)s;
            BinaryPrimitives.WriteUInt32LittleEndian(f[12..], (uint)i);
        }
        return buffer;
    }

    [Fact]
    public void BucketsCarryMinMaxAndMean()
    {
        var series = new RawBucketSeries(framesPerBucket: 4);
        // 4 帧一桶：比值 10, 12, 8, 10 kΩ（scale=1000 → kΩ = V/I 当 sense=1000）
        series.Append(Frames((10000, 100000), (12000, 100000), (8000, 100000), (10000, 100000)), 100000, 0.0);
        Assert.Equal(1, series.BucketCount);
        var (_, min, max, mean) = series.Snapshot();
        Assert.Equal(8.0, min[0], 6);
        Assert.Equal(12.0, max[0], 6);      // 尖峰必须保留（不能只留均值）
        Assert.Equal(10.0, mean[0], 6);
    }

    [Fact]
    public void PartialBucketIsNotEmittedUntilFlushed()
    {
        var series = new RawBucketSeries(framesPerBucket: 4);
        series.Append(Frames((10000, 100000), (11000, 100000)), 100000, 0.0);
        Assert.Equal(0, series.BucketCount);       // 只有半桶
        series.FlushPartial();
        Assert.Equal(1, series.BucketCount);
        var (_, _, _, mean) = series.Snapshot();
        Assert.Equal(10.5, mean[0], 6);
    }

    [Fact]
    public void RingBufferKeepsNewestBuckets()
    {
        var series = new RawBucketSeries(framesPerBucket: 1, capacity: 3);
        for (int i = 0; i < 5; i++)
            series.Append(Frames(((i + 1) * 1000, 100000)), 100000, i);
        Assert.Equal(3, series.BucketCount);
        var (seconds, _, _, mean) = series.Snapshot();
        Assert.Equal([2.0, 3.0, 4.0], seconds);     // 最老的两个被覆盖
        Assert.Equal([3.0, 4.0, 5.0], mean);
    }

    [Fact]
    public void InvalidFramesAreSkipped()
    {
        var series = new RawBucketSeries(framesPerBucket: 2);
        // sense 太小（激励无效）与整帧为 0 都应跳过，不污染统计
        series.Append(Frames((10000, 100), (0, 0), (10000, 100000), (10000, 100000)), 100000, 0.0);
        Assert.Equal(1, series.BucketCount);
        var (_, min, max, _) = series.Snapshot();
        Assert.Equal(10.0, min[0], 6);
        Assert.Equal(10.0, max[0], 6);
    }

    [Fact]
    public void ZeroScaleFallsBackToRawRatio()
    {
        var series = new RawBucketSeries(framesPerBucket: 1);
        series.Append(Frames((10000, 100000)), scaleOhms: 0, seconds: 0);
        var (_, _, _, mean) = series.Snapshot();
        Assert.Equal(0.1, mean[0], 6);    // V/I = 10000/100000，无校准系数时就是比值
    }

    [Fact]
    public void ResetClearsEverything()
    {
        var series = new RawBucketSeries(framesPerBucket: 1);
        series.Append(Frames((1000, 100000)), 100000, 1.0);
        series.Reset();
        Assert.Equal(0, series.BucketCount);
        series.Append(Frames((2000, 100000)), 100000, 2.0);
        var (seconds, _, _, mean) = series.Snapshot();
        Assert.Equal([2.0], seconds);
        Assert.Equal([2.0], mean);
    }
}
