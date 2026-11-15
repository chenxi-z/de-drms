using Drms.Core.Protocol;

namespace Drms.Core.Session;

/// <summary>
/// 把"受理"跟进到"终态"。
///
/// 为什么必须有这一层：协议里 ACCEPTED 只表示请求被收下了，
/// 真正的结论要查 GET_OPERATION 的 phase 到 FINISHED。直接把 ACCEPTED
/// 当成功显示，会让用户以为记录已经开始了——而实际上可能稍后失败。
/// </summary>
public static class OperationWaiter
{
    /// <summary>
    /// 轮询直到 phase == FINISHED 或超时。返回最终结果（可能仍是失败）。
    ///
    /// <paramref name="onProgress"/> 会在每次轮询后回调，界面上可以显示已耗时。
    /// </summary>
    public static async Task<OperationReply> WaitAsync(
        DeviceSession session,
        ulong operation,
        TimeSpan timeout,
        TimeSpan? pollInterval = null,
        Action<OperationReply, TimeSpan>? onProgress = null,
        CancellationToken cancellation = default)
    {
        TimeSpan interval = pollInterval ?? TimeSpan.FromMilliseconds(300);
        var started = DateTime.UtcNow;
        OperationReply last = null!;

        while (true)
        {
            cancellation.ThrowIfCancellationRequested();
            last = await Task.Run(() => session.GetOperation(operation), cancellation);
            TimeSpan elapsed = DateTime.UtcNow - started;

            if (last.IsFinished)
                return last;

            onProgress?.Invoke(last, elapsed);

            if (elapsed > timeout)
                throw new DeviceException(
                    $"操作 {operation} 在 {timeout.TotalSeconds:0.#}s 内未结束（phase={last.Phase}）",
                    last.Result);

            await Task.Delay(interval, cancellation);
        }
    }
}
