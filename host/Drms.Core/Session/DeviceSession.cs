using Drms.Core.Protocol;
using Drms.Core.Transport;

namespace Drms.Core.Session;

/// <summary>设备会话错误。区别于协议字节错误。</summary>
public sealed class DeviceException(string message, Result? result = null, Reason? reason = null)
    : Exception(message)
{
    public Result? Result { get; } = result;
    public Reason? Reason { get; } = reason;
}

/// <summary>
/// 一条到设备的会话：握手、请求/应答配对、事件分发。
///
/// 设计要点（都来自协议正文，不是自选）：
///   · HELLO 必须 session=0、request_id=1；之后普通请求从 2 开始严格递增，不回绕。
///   · 同一会话内可以用原编号重发**内容相同**的请求；固件据此去重。
///   · ACCEPTED 只表示受理。要结论必须查 GET_OPERATION。
///   · 事件（MEAS_EVENT）的 request_id 为 0，不能和回复混在一起等。
///
/// 这里只在单线程里跑：一个后台读线程 + 调用方线程发请求。
/// </summary>
public sealed class DeviceSession : IDisposable
{
    private readonly IByteLink _link;
    private readonly FrameSplitter _splitter = new();
    private readonly object _sync = new();
    private readonly Dictionary<ulong, Message> _pending = new();
    private readonly List<byte[]> _outboxAccumulator = new();

    private Thread? _reader;
    private volatile bool _running;
    private ulong _nextRequestId = 2;
    private uint _session;

    /// <summary>收到 MEAS_EVENT 时触发（在读线程上，注意不要在这里做重活）。</summary>
    public event Action<MeasurementEvent>? MeasurementReceived;

    /// <summary>收到 RAW_EVENT 时触发（在读线程上）。每批含若干 16 B 原始帧。</summary>
    public event Action<RawEvent>? RawReceived;

    /// <summary>收到无法归类的事件或坏帧时触发，用于诊断。</summary>
    public event Action<string>? Diagnostic;

    public DeviceSession(IByteLink link) => _link = link;

    public bool IsHandshaken => _session != 0;
    public uint SessionId => _session;
    public HelloReply? Hello { get; private set; }

    /// <summary>握手超时。设备开机自检期间会慢一点，给足时间。</summary>
    public TimeSpan RequestTimeout { get; set; } = TimeSpan.FromSeconds(3);

    public void Start()
    {
        _running = true;
        _reader = new Thread(ReadLoop) { IsBackground = true, Name = "drms-cdc-reader" };
        _reader.Start();
    }

    private void ReadLoop()
    {
        while (_running)
        {
            byte[] chunk;
            try
            {
                chunk = _link.Read(TimeSpan.FromMilliseconds(50));
            }
            catch (Exception ex)
            {
                if (_running) Diagnostic?.Invoke($"读取失败：{ex.Message}");
                break;
            }

            if (chunk.Length == 0)
            {
                _splitter.CheckStale();
                continue;
            }

            foreach (byte[] raw in _splitter.Feed(chunk))
            {
                Message message;
                try
                {
                    message = FrameCodec.Decode(raw);
                }
                catch (ProtocolException ex)
                {
                    Diagnostic?.Invoke($"丢弃畸形帧：{ex.Message}");
                    continue;
                }

                Dispatch(message);
            }
        }
    }

    private void Dispatch(Message message)
    {
        if (message.Kind == Kind.Event)
        {
            if (message.Opcode == Opcodes.MeasEvent)
            {
                try
                {
                    MeasurementReceived?.Invoke(Messages.ParseMeasurementEvent(message));
                }
                catch (ProtocolException ex)
                {
                    Diagnostic?.Invoke($"MEAS_EVENT 解析失败：{ex.Message}");
                }
            }
            else if (message.Opcode == Opcodes.RawEvent)
            {
                try
                {
                    RawReceived?.Invoke(Messages.ParseRawEvent(message));
                }
                catch (ProtocolException ex)
                {
                    Diagnostic?.Invoke($"RAW_EVENT 解析失败：{ex.Message}");
                }
            }
            else
            {
                Diagnostic?.Invoke($"未处理的事件 opcode={message.Opcode}");
            }
            return;
        }

        if (message.Kind == Kind.Reply)
        {
            lock (_sync)
            {
                _pending[message.RequestId] = message;
                Monitor.PulseAll(_sync);
            }
        }
    }

    /// <summary>
    /// 发一条请求并等对应回复。超时抛 <see cref="DeviceException"/>。
    /// </summary>
    public Message Transact(byte[] wireFrame, ulong requestId)
    {
        lock (_sync)
            _pending.Remove(requestId);

        _link.Write(wireFrame);

        var deadline = DateTime.UtcNow + RequestTimeout;
        lock (_sync)
        {
            while (true)
            {
                if (_pending.TryGetValue(requestId, out Message? reply))
                {
                    _pending.Remove(requestId);
                    return reply;
                }
                var remaining = deadline - DateTime.UtcNow;
                if (remaining <= TimeSpan.Zero)
                    throw new DeviceException($"请求 {requestId} 超时（{RequestTimeout.TotalSeconds:0.#}s）");
                Monitor.Wait(_sync, remaining);
            }
        }
    }

    /// <summary>握手。失败时抛出带 result/reason 的异常。</summary>
    public HelloReply Handshake()
    {
        ulong requestId = 1;
        byte[] request = Messages.HelloRequest(requestId);
        Message reply = Transact(request, requestId);

        Result result = Messages.ReadResult(reply);
        if (result != Result.Ok)
            throw new DeviceException($"HELLO 被拒绝", result, Messages.ReadReason(reply));

        Hello = Messages.ParseHello(reply);
        _session = reply.Session;
        _nextRequestId = 2;
        return Hello;
    }

    /// <summary>取下一个请求编号（会话内严格递增）。</summary>
    public ulong NextRequestId()
    {
        lock (_sync)
            return _nextRequestId++;
    }

    public StatusReply GetStatus()
        => Result_<StatusReply>(Messages.GetStatusRequest(_session, NextRequestId()), Messages.ParseStatus);

    /// <summary>
    /// 查操作结果。
    ///
    /// 注意这里**不接受** result 非 OK 的回复：固件的 GET_OPERATION 把
    /// "查询是否成功"和"操作结果"合并在同一个 result 字段里
    /// （drms_cdc_v2.c 的 opcode==3 分支：`result = operation.result`）。
    /// 所以一个 INCOMPLETE(9) 的回复表示"查询成功，操作以 INCOMPLETE 结束"，
    /// 是合法终态，不是协议错误。把它当异常抛出去会让调用方拿不到结果。
    ///
    /// 真正的查询错误只有 BUSY/STALE/INVALID 这几种（drms_control_get_operation 的返回）。
    /// </summary>
    public OperationReply GetOperation(ulong operation)
    {
        Message reply = Send(Messages.GetOperationRequest(_session, NextRequestId(), operation));
        Result result = Messages.ReadResult(reply);

        // 这三种才表示"查不到这个操作"，其余都是操作的终态结果
        if (result is Result.Invalid or Result.Stale or Result.Busy)
            throw new DeviceException($"查询操作 {operation} 失败", result, Messages.ReadReason(reply));

        return Messages.ParseOperation(reply);
    }

    /// <summary>查记录结果。与 GetOperation 同理：result 是记录的业务结果。</summary>
    public RecordReply GetRecord(ulong record)
    {
        Message reply = Send(Messages.GetRecordRequest(_session, NextRequestId(), record));
        Result result = Messages.ReadResult(reply);
        if (result is Result.Invalid or Result.Stale)
            throw new DeviceException($"查询记录 {record} 失败", result, Messages.ReadReason(reply));
        return Messages.ParseRecord(reply);
    }

    public ConfigReply GetConfig()
        => Result_<ConfigReply>(Messages.GetConfigRequest(_session, NextRequestId()), Messages.ParseConfig);

    /// <summary>BEGIN_RECORD：返回受理得到的 (operation, record)。</summary>
    public (ulong Operation, ulong Record) BeginRecord(uint? durationMs = null)
    {
        Message reply = Send(Messages.BeginRecordRequest(_session, NextRequestId(), durationMs));
        EnsureAccepted(reply);
        return Messages.ParseOperationAndRecord(reply);
    }

    public (ulong Operation, ulong Record) EndRecord(ulong record)
    {
        Message reply = Send(Messages.EndRecordRequest(_session, NextRequestId(), record));
        EnsureAccepted(reply);
        return Messages.ParseOperationAndRecord(reply);
    }

    /// <summary>BUILD_R0：设备会先停采、写基线、再重启采集，曲线会断一次。</summary>
    public ulong BuildR0()
    {
        Message reply = Send(Messages.BuildR0Request(_session, NextRequestId()));
        EnsureAccepted(reply);
        return reply.Index.Require(Tag.Operation, "operation").AsU64();
    }

    public ulong Calibrate()
    {
        Message reply = Send(Messages.CalibrateRequest(_session, NextRequestId()));
        EnsureAccepted(reply);
        return reply.Index.Require(Tag.Operation, "operation").AsU64();
    }

    public ulong ApplyConfig(ulong expectedVersion, byte[] settings)
    {
        Message reply = Send(Messages.ApplyConfigRequest(_session, NextRequestId(), expectedVersion, settings));
        EnsureAccepted(reply);
        return reply.Index.Require(Tag.Operation, "operation").AsU64();
    }

    public ulong SaveConfig(ulong expectedVersion)
    {
        Message reply = Send(Messages.SaveConfigRequest(_session, NextRequestId(), expectedVersion));
        EnsureAccepted(reply);
        return reply.Index.Require(Tag.Operation, "operation").AsU64();
    }

    public uint SubscribeCurve(uint periodMs)
    {
        Message reply = Send(Messages.SubscribeCurveRequest(_session, NextRequestId(), periodMs));
        Result result = Messages.ReadResult(reply);
        if (result != Result.Ok)
            throw new DeviceException("SUBSCRIBE 被拒绝", result, Messages.ReadReason(reply));
        // 返回设备实际采用的周期
        return reply.Index.Optional(Tag.PeriodMs)?.AsU32() ?? periodMs;
    }

    /// <summary>SUBSCRIBE stream=RAW（全速率原始帧，period_ms=0）。
    /// 返回设备实际批周期（ms）：4 kSPS 下 60 帧/批约 15 ms。
    /// 超带宽档位设备返回 INVALID（不静默降级），调用方应回落 CURVE 轮询。</summary>
    public uint SubscribeRaw()
    {
        Message reply = Send(Messages.SubscribeRawRequest(_session, NextRequestId()));
        Result result = Messages.ReadResult(reply);
        if (result != Result.Ok)
            throw new DeviceException("SUBSCRIBE(RAW) 被拒绝", result, Messages.ReadReason(reply));
        return reply.Index.Optional(Tag.PeriodMs)?.AsU32() ?? 0;
    }

    public void Unsubscribe(StreamKind stream)
    {
        Message reply = Send(Messages.UnsubscribeRequest(_session, NextRequestId(), stream));
        Result result = Messages.ReadResult(reply);
        if (result != Result.Ok)
            throw new DeviceException("UNSUBSCRIBE 被拒绝", result, Messages.ReadReason(reply));
    }

    public Message Send(byte[] wireFrame)
    {
        // 从已编码的帧里解出 request_id，避免调用方还要单独传一次。
        Message probe = FrameCodec.Decode(wireFrame.AsSpan(0, wireFrame.Length - 1));
        return Transact(wireFrame, probe.RequestId);
    }

    private static void EnsureAccepted(Message reply)
    {
        Result result = Messages.ReadResult(reply);
        // 协议：ACCEPTED 表示受理，不等于完成。这里只拒绝"没被受理"的情况。
        if (result is not (Result.Ok or Result.Accepted))
            throw new DeviceException("请求未被受理", result, Messages.ReadReason(reply));
    }

    /// <summary>发一次请求、检查 result、再解析成功字段。</summary>
    private T Result_<T>(byte[] request, Func<Message, T> parse)
    {
        Message reply = Send(request);
        Result result = Messages.ReadResult(reply);
        if (result != Result.Ok)
            throw new DeviceException("设备返回错误", result, Messages.ReadReason(reply));
        return parse(reply);
    }

    public void Dispose()
    {
        _running = false;
        _reader?.Join(TimeSpan.FromSeconds(1));
        _link.Dispose();
    }
}
