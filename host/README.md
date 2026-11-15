# DE-DRMS 上位机（第一版）

状态：**联机监测最小闭环已可运行**（2026-11-16）。
历史回放、MSC 交接、配置编辑界面尚未实现。

技术栈：**C# + .NET 10 + Avalonia 12 + ScottPlot 5**（见 [技术栈决定](../docs/design/2026-11-15-host-tech-stack.md)）。

## 目录

| 项目 | 作用 |
| --- | --- |
| `Drms.Core/` | 零 GUI 依赖：CDC v2 协议编解码、设备会话、区间表。可单测、可跨平台 |
| `Drms.Core.Tests/` | xUnit 测试（24 项）：四条权威向量逐字节对齐 + 会话层行为 |
| `Drms.Gui/` | Avalonia 界面：连接、双图曲线、实时读数 |
| `Drms.Probe/` | 控制台联调工具：对真设备跑握手/状态/配置/订阅 |

## 怎么启动

**前置**：需要 .NET 10 SDK（本机在 `C:\Users\chenx\.dotnet`，非系统安装）。

```bash
export DOTNET_ROOT="C:/Users/chenx/.dotnet"
export PATH="/c/Users/chenx/.dotnet:$PATH"
```

### 界面

```bash
cd host
dotnet run --project Drms.Gui                       # 启动后手动选串口并点“连接”
dotnet run --project Drms.Gui -- --auto COM5        # 启动即连接（现场/自动化用）
```

也可直接跑编译产物：`host\Drms.Gui\bin\Debug\net10.0\Drms.Gui.exe --auto COM5`

### 联调工具（验证协议，不需要界面）

```bash
cd host
dotnet run --project Drms.Probe -- COM5             # 握手 + 状态 + 配置
dotnet run --project Drms.Probe -- COM5 200         # 再加 200 ms 曲线订阅
```

输出包含 UID、能力列表、采集/记录/介质状态、ohms/ratio、配置字段与区间表。

### 测试

```bash
cd host/Drms.Core.Tests && dotnet test
```

## 已实现

- **COBS + 20 字节头 + TLV + CRC-32/ISO-HDLC**，用 `shared/protocol/de-drms-cdc-v2.json`
  的四条向量（含 1054 字节最大帧、254 字节段边界）逐字节验证。
- **会话层**：HELLO（session=0 / request_id=1）、请求编号严格递增、请求/应答配对、
  超时、`ACCEPTED` 与完成态区分、MEAS_EVENT 事件分发。
- **消息**：GET_STATUS / GET_OPERATION / GET_RECORD / GET_CONFIG /
  BEGIN_RECORD / END_RECORD / BUILD_R0 / CALIBRATE / APPLY_CONFIG / SAVE_CONFIG /
  SUBSCRIBE(CURVE) / UNSUBSCRIBE。
- **界面**：串口选择、1 Hz 状态轮询 + 200 ms 曲线订阅、上下双图（主 R/R0、副 R）、
  实时读数面板、中文显示。

## 重要行为约定（来自协议，不是实现选择）

1. **`ACCEPTED` 只表示受理**，不是完成。要看结果必须查 `GET_OPERATION`。
   界面当前仍直接显示 ACCEPTED 的即时反馈，操作轮询尚未接到 UI 上（见下节）。
2. **`HELLO.rate_monitor`/`rate_record` 恒为 4000**，是硬编码常量。
   真实采样率必须读 `GET_STATUS.rate`。
3. **`lost = 0` 不代表没有缺口**：固件只统计发送队列满，不覆盖发送侧丢弃。
   界面必须用 `sequence` 连续性交叉校验（已实现：序号跳变插入断点）。
4. **`ratio` 需要区间表才发布**。只建基线不配区间表时主图必然空白，
   界面已用文字说明原因，不要当成故障。
5. **R 与 R/R0 不能互相推导**（一个未滤波、一个滤波后，且量化不同），
   图上不得做"用 R 反算 R/R0"之类的功能。

## 已知限制 / 下一步

| 项 | 说明 |
| --- | --- |
| 建立 R0、开始/结束记录按钮 | 核心库已实现，界面按钮尚未接上 |
| 区间表编辑 | 解析/编码已实现（`Messages.ParseIntervals`/`EncodeIntervals`），无编辑界面 |
| **出厂空配置问题** | `GET_CONFIG` 返回 `UNSUPPORTED`，此时 `baseline_min_count` 不可读，`BUILD_R0` 前置条件不满足。**首次必须先完整下发一次 `APPLY_CONFIG`** |
| 操作轮询 | 受理后应轮询 `GET_OPERATION` 至终态；当前未接 |
| 历史回放 | 未实现。BIN v2 解析规格见 [记录格式](../docs/design/2026-11-06-record-v2-format.md) |
| MSC 交接 | 未实现（固件侧仍有 SAFE_STOP 与导出所有权冲突待定） |
| 界面平滑 / min-max 包络 | 未实现（规格 §7.4、§9 要求，当前是逐点折线） |
| 视口缩放 | 未实现，当前固定自动缩放 |

## 跨平台说明

同一份代码在 Ubuntu 与 Windows 都能构建。两处平台差异：
- 中文字体：Windows 注册 `msyh.ttc`，Linux 找 Noto CJK（`MainWindow.RegisterCjkFont`）。
  ScottPlot 走 SkiaSharp，**必须显式 `Fonts.AddFontFile`**，光写字体名会显示豆腐块。
- 串口：`System.IO.Ports` 托管实现，两侧一致；DTR 必须拉起，否则固件不接受 HELLO。
