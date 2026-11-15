using Drms.Core.Protocol;
using Drms.Core.Session;
using Drms.Core.Transport;
using Xunit;

namespace Drms.Core.Tests;

/// <summary>
/// 用假链路驱动完整会话逻辑——不需要真设备。
///
/// 这一层的价值是把"请求/应答配对、超时、ACCEPTED 不等于完成"这些
/// 容易搞错的地方固定下来；真设备联调另有一遍（Drms.Probe）。
/// </summary>
public class SessionTests
{
    /// <summary>
    /// 假链路：Write 时把字节交给一个"设备"回调，回调返回要回的帧。
    /// 这样能精确控制设备的回应顺序与时机。
    /// </summary>
    private sealed class FakeLink : IByteLink
    {
        private readonly Queue<byte[]> _toHost = new();
        private readonly Func<Message, byte[]?> _device;

        public FakeLink(Func<Message, byte[]?> device) => _device = device;

        public bool IsOpen => true;
        public bool Disposed { get; private set; }

        /// <summary>模拟设备主动推送（事件），不经过请求。</summary>
        public void Enqueue(byte[] frame)
        {
            lock (_toHost)
                _toHost.Enqueue(frame);
        }

        public void Write(ReadOnlySpan<byte> data)
        {
            byte[] copy = data.ToArray();
            Message request = FrameCodec.Decode(copy.AsSpan(0, copy.Length - 1));
            byte[]? reply = _device(request);
            if (reply is not null)
                lock (_toHost)
                    _toHost.Enqueue(reply);
        }

        public byte[] Read(TimeSpan timeout)
        {
            lock (_toHost)
            {
                if (_toHost.Count > 0)
                    return _toHost.Dequeue();
            }
            Thread.Sleep(5);
            return [];
        }

        public void Dispose() => Disposed = true;
    }

    private static byte[] Reply(Message request, Result result,
                               Action<TlvWriter>? build = null)
    {
        var tlv = new TlvWriter().AddU16(Tag.Result, (ushort)result);
        build?.Invoke(tlv);
        return FrameCodec.Encode(Kind.Reply, request.Opcode, 7u, request.RequestId, tlv.ToArray());
    }

    [Fact]
    public void Handshake_UsesRequestIdOneAndSessionZero()
    {
        ulong seenRequestId = 0;
        uint seenSession = 0;
        var link = new FakeLink(req =>
        {
            if (req.Opcode != Opcodes.Hello)
                return null;
            seenRequestId = req.RequestId;
            seenSession = req.Session;
            return Reply(req, Result.Ok, tlv => tlv
                .AddRaw(Tag.Uid, new byte[12])
                .AddU64(Tag.Boot, 0xDEADBEEF)
                .AddRaw(Tag.Capabilities, [1, 0, 2, 0])
                .AddU16(Tag.MaxPayload, 1024)
                .AddRaw(Tag.RateMonitor, [0xA0, 0x0F, 0, 0])
                .AddRaw(Tag.RateRecord, [0xA0, 0x0F, 0, 0]));
        });

        using var session = new DeviceSession(link);
        session.Start();
        HelloReply hello = session.Handshake();

        Assert.Equal(1ul, seenRequestId);
        Assert.Equal(0u, seenSession);      // 握手必须 session=0
        Assert.Equal(7u, session.SessionId); // 回复里的 session 成为会话编号
        Assert.Equal(0xDEADBEEFul, hello.Boot);
        Assert.True(hello.Supports(Opcodes.GetStatus));
        Assert.False(hello.Supports(Opcodes.Subscribe - 1));
    }

    [Fact]
    public void RequestIds_IncreaseStrictlyAfterHandshake()
    {
        var seen = new List<ulong>();
        var link = new FakeLink(req =>
        {
            seen.Add(req.RequestId);
            if (req.Opcode == Opcodes.Hello)
                return Reply(req, Result.Ok, tlv => tlv
                    .AddRaw(Tag.Uid, new byte[12]).AddU64(Tag.Boot, 1)
                    .AddRaw(Tag.Capabilities, []).AddU16(Tag.MaxPayload, 1024)
                    .AddRaw(Tag.RateMonitor, []).AddRaw(Tag.RateRecord, []));
            return Reply(req, Result.Ok, tlv => tlv.AddU64(Tag.StatusRevision, 1)
                .AddU64(Tag.MonoUs, 1).AddU8(Tag.Acquisition, 3).AddU8(Tag.Recording, 0)
                .AddU8(Tag.Medium, 1).AddU8(Tag.Owner, 0).AddU8(Tag.Maintenance, 0)
                .AddU32(Tag.SampleGeneration, 1).AddU32(Tag.Rate, 4000).AddBool(Tag.Fresh, true)
                .AddU8(Tag.Classification, 0).AddU32(Tag.Quality, 0)
                .AddU64(Tag.RunningVersion, 0).AddU64(Tag.SavedVersion, 0)
                .AddU64(Tag.BaselineVersion, 0).AddU64(Tag.CalibrationVersion, 0)
                .AddU32(Tag.Fault, 0).AddBool(Tag.RtcValid, true).AddU32(Tag.MediaGeneration, 1));
        });

        using var session = new DeviceSession(link);
        session.Start();
        session.Handshake();
        session.GetStatus();
        session.GetStatus();

        // HELLO=1，随后 2、3
        Assert.Equal([1ul, 2ul, 3ul], seen);
    }

    [Fact]
    public void GetConfig_ThrowsOnUnsupportedSoCallerCanFallBack()
    {
        var link = new FakeLink(req =>
        {
            if (req.Opcode == Opcodes.Hello)
                return Reply(req, Result.Ok, tlv => tlv
                    .AddRaw(Tag.Uid, new byte[12]).AddU64(Tag.Boot, 1)
                    .AddRaw(Tag.Capabilities, []).AddU16(Tag.MaxPayload, 1024)
                    .AddRaw(Tag.RateMonitor, []).AddRaw(Tag.RateRecord, []));
            // 出厂空配置：设备明确回 UNSUPPORTED，且不带 settings
            return Reply(req, Result.Unsupported, tlv => tlv.AddU16(Tag.Reason, (ushort)Reason.BadField));
        });

        using var session = new DeviceSession(link);
        session.Start();
        session.Handshake();

        DeviceException ex = Assert.Throws<DeviceException>(() => session.GetConfig());
        Assert.Equal(Result.Unsupported, ex.Result);
        Assert.Equal(Reason.BadField, ex.Reason);
    }

    [Fact]
    public void BeginRecord_ReturnsAcceptedOperationAndRecord()
    {
        var link = new FakeLink(req =>
        {
            if (req.Opcode == Opcodes.Hello)
                return Reply(req, Result.Ok, tlv => tlv
                    .AddRaw(Tag.Uid, new byte[12]).AddU64(Tag.Boot, 1)
                    .AddRaw(Tag.Capabilities, []).AddU16(Tag.MaxPayload, 1024)
                    .AddRaw(Tag.RateMonitor, []).AddRaw(Tag.RateRecord, []));
            return Reply(req, Result.Accepted, tlv => tlv
                .AddU64(Tag.Operation, 42).AddU64(Tag.Record, 9));
        });

        using var session = new DeviceSession(link);
        session.Start();
        session.Handshake();

        var (operation, record) = session.BeginRecord();
        Assert.Equal(42ul, operation);
        Assert.Equal(9ul, record);
    }

    [Fact]
    public void BeginRecord_RejectsBusyInsteadOfPretendingAccepted()
    {
        var link = new FakeLink(req =>
        {
            if (req.Opcode == Opcodes.Hello)
                return Reply(req, Result.Ok, tlv => tlv
                    .AddRaw(Tag.Uid, new byte[12]).AddU64(Tag.Boot, 1)
                    .AddRaw(Tag.Capabilities, []).AddU16(Tag.MaxPayload, 1024)
                    .AddRaw(Tag.RateMonitor, []).AddRaw(Tag.RateRecord, []));
            return Reply(req, Result.Busy, tlv => tlv.AddU16(Tag.Reason, (ushort)Reason.Conflict));
        });

        using var session = new DeviceSession(link);
        session.Start();
        session.Handshake();

        DeviceException ex = Assert.Throws<DeviceException>(() => session.BeginRecord());
        Assert.Equal(Result.Busy, ex.Result);
    }

    [Fact]
    public void MeasurementEvent_IsRaisedWithRequestIdZero()
    {
        var link = new FakeLink(req =>
        {
            if (req.Opcode == Opcodes.Hello)
                return Reply(req, Result.Ok, tlv => tlv
                    .AddRaw(Tag.Uid, new byte[12]).AddU64(Tag.Boot, 1)
                    .AddRaw(Tag.Capabilities, []).AddU16(Tag.MaxPayload, 1024)
                    .AddRaw(Tag.RateMonitor, []).AddRaw(Tag.RateRecord, []));
            return null;
        });

        using var session = new DeviceSession(link);
        var gate = new ManualResetEventSlim(false);
        MeasurementEvent? captured = null;
        session.MeasurementReceived += ev => { captured = ev; gate.Set(); };

        session.Start();
        session.Handshake();

        // 事件帧：kind=Event、request_id=0
        byte[] payload = new TlvWriter()
            .AddU64(Tag.Sequence, 77).AddU64(Tag.Lost, 0).AddU64(Tag.MonoUs, 123456)
            .AddBool(Tag.Fresh, true).AddU8(Tag.Classification, 5).AddU32(Tag.Quality, 0)
            .AddF64(Tag.Ohms, 100000.5).AddF64(Tag.Ratio, 1.000005).ToArray();
        byte[] eventFrame = FrameCodec.Encode(Kind.Event, Opcodes.MeasEvent, 7u, 0, payload);
        link.Enqueue(eventFrame);

        Assert.True(gate.Wait(TimeSpan.FromSeconds(3)));
        Assert.NotNull(captured);
        Assert.Equal(77ul, captured!.Sequence);
        Assert.Equal(123456ul, captured.MonoUs);
        Assert.Equal(Classification.Confirmed, captured.Classification);
        Assert.Equal(100000.5, captured.Ohms!.Value, 6);
        Assert.Equal(1.000005, captured.Ratio!.Value, 9);
    }

    [Fact]
    public void Timeout_RaisesDeviceException()
    {
        // 永不回应的设备
        var link = new FakeLink(_ => null);
        using var session = new DeviceSession(link) { RequestTimeout = TimeSpan.FromMilliseconds(200) };
        session.Start();

        DeviceException ex = Assert.Throws<DeviceException>(() => session.Handshake());
        Assert.Contains("超时", ex.Message);
    }

    [Fact]
    public void Intervals_RoundTripThroughEncodeAndParse()
    {
        var original = new[]
        {
            new MonitorInterval { Low = 0.95, High = 1.05, Hysteresis = 0.01, Id = 1, Level = 0 },
            new MonitorInterval { Low = 1.05, High = 1.20, Hysteresis = 0.02, Id = 2, Level = 1,
                                  LastUpperClosed = true, Direction = 2 },
        };

        byte[] encoded = Messages.EncodeIntervals(original);
        Assert.Equal(60, encoded.Length); // 2 × 30

        List<MonitorInterval> parsed = Messages.ParseIntervals(encoded);
        Assert.Equal(2, parsed.Count);
        Assert.Equal(0.95, parsed[0].Low, 12);
        Assert.Equal(1.05, parsed[0].High, 12);
        Assert.Equal(1, parsed[0].Id);
        Assert.Equal(0, parsed[0].Level);
        Assert.False(parsed[0].LastUpperClosed);

        Assert.Equal(1.20, parsed[1].High, 12);
        Assert.Equal(2, parsed[1].Id);
        Assert.Equal(1, parsed[1].Level);
        Assert.True(parsed[1].LastUpperClosed);
        Assert.Equal(2, parsed[1].Direction);
    }

    [Fact]
    public void ParseIntervals_RejectsNonMultipleOfThirty()
    {
        Assert.Throws<ProtocolException>(() => Messages.ParseIntervals(new byte[31]));
    }
}
