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

### 界面（最简单：直接双击）

**`host\dist\Drms.Gui.exe`** —— 自包含单文件，**不需要装 .NET**。
第一次使用前先生成它：

```bash
export DOTNET_ROOT="C:/Users/chenx/.dotnet"
export PATH="/c/Users/chenx/.dotnet:$PATH"
cd host
dotnet publish Drms.Gui/Drms.Gui.csproj -c Release -r win-x64 \
  --self-contained true -p:PublishSingleFile=true \
  -p:IncludeNativeLibrariesForSelfExtract=true -o dist
```

产物约 101 MB（内含 .NET 运行时）。双击即可运行，`dist/` 已被 `.gitignore`
忽略，不入库，换机器需重新发布。

命令行带自动连接：

```bat
host\dist\Drms.Gui.exe --auto COM5
```

### 界面（开发时从源码跑）

**前置**：.NET 10 SDK（本机在 `C:\Users\chenx\.dotnet`，非系统安装）。

```bash
export DOTNET_ROOT="C:/Users/chenx/.dotnet"
export PATH="/c/Users/chenx/.dotnet:$PATH"
cd host
dotnet run --project Drms.Gui                       # 启动后手动选串口并点“连接”
dotnet run --project Drms.Gui -- --auto COM5        # 启动即连接（现场/自动化用）
```

> ⚠️ **不要直接双击 `bin\Debug\net10.0\Drms.Gui.exe`**。那是依赖框架的构建产物，
> 它会去 `C:\Program Files\dotnet` 找 .NET 10 运行时（那里只有 6/8），
> 报 `You must install or update .NET`。要么用 `dotnet run`，要么用上面的
> 自包含 `dist\Drms.Gui.exe`。

### 联调工具（验证协议，不需要界面）

```bash
cd host
dotnet run --project Drms.Probe -- COM5             # 握手 + 状态 + 配置 + 建基线
dotnet run --project Drms.Probe -- COM5 10 0.6      # 窗口 10 s，CV 限值放宽到 0.6%
dotnet run --project Drms.Probe -- measure COM5 300 # 只测阻值与稳定性（300 点统计）
```

第三个参数（CV 上限百分比）**只用于临时验证流程**。默认 0.1% 是设计要求；
放宽后建出的 R₀ 没有物理意义，不要当作测量结果。

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
- **配置**：等级区间按「上界百分比」编辑（四行表格），本地按固件同一套规则校验
  （升序、不重叠、`2h < hi-lo`、间隙不小于两边回差之和），通过后整份下发。
  绿色下界自动取 **−10%**（见下方"区间下界"）。
- **建立 R₀**：可选 10/30/60/180 s 采样窗口；过程中界面自己算均值与 CV
  （固件不公开中间值），显示进度条；`BUILD_R0` 受理后轮询 `GET_OPERATION` 到终态。

## 区间下界为什么是 −10% 而不是 0%

实测 443 Ω 试件时 `ratio` 在 0.99–1.01 之间正常波动。若绿色区间从 `ratio = 1.000` 起，
任何低于基线的点都会掉出整张表，被判成 `Unmapped`——实测 6 次采样里有一半落在表外。

试件电阻小幅下降是常见且无害的（温度、接触改善），损伤判据关注的是**上升**。
因此绿色下界取 −10% 作为容差，与曲线规格 §3.6 的默认区间（`lo` 从 0.9 起）一致。
超出 ±10% 才算真正异常。

## ⚠️ AvaPlot 布局限制（实测，别改回去）

**ScottPlot.Avalonia 5.1.59 + Avalonia 12 下，`AvaPlot` 不遵守布局约束。**
它会无视 `Grid` 的列宽/行高、铺满整行，并把同级的其它控件完全遮住。

以下写法**全部实测失败**（用最小工程逐个复现，不是猜测）：

| 尝试 | 结果 |
| --- | --- |
| `Grid ColumnDefinitions="*,300"` | 图表铺满 1200 px，右侧面板不显示 |
| `DockPanel` + `Dock="Right"` | 同上 |
| 覆盖层 `HorizontalAlignment="Right"` | 被图表盖住 |
| 固定左列宽度 `1040` | 图表仍铺满 |
| 官方示例的 `Grid.Row/Column` + Stretch 写法 | 同样失败 |

**唯一可靠的约束是给固定 `Height`。** 当前布局：
`ScrollViewer > StackPanel`，主图 `Height="340"`、副图 `Height="240"`、
配置区放在 `Expander`（默认折叠）。折叠状态下曲线占满可视区；
展开时图表让出高度，配置面板完整可见。

若将来 ScottPlot 修复此问题，可改回左右分栏；在那之前不要浪费时间重试。

## 重要行为约定（来自协议，不是实现选择）

1. **`ACCEPTED` 只表示受理**，不是完成。要看结果必须查 `GET_OPERATION`。
   已实现 `OperationWaiter` 轮询至 `phase = FINISHED`。
2. **`GET_OPERATION` 的 `result` 同时承载"查询状态"和"操作结果"**
   （固件 `drms_cdc_v2.c:331` `result = operation.result`）。
   只有 `INVALID`/`STALE`/`BUSY` 才是查询失败；`INCOMPLETE` 等是合法终态。
   **把它当异常抛会丢掉结果**——这是本项目踩过的真实缺陷。
3. **`HELLO.rate_monitor`/`rate_record` 恒为 4000**，是硬编码常量。
   真实采样率必须读 `GET_STATUS.rate`。
4. **`lost = 0` 不代表没有缺口**：固件只统计发送队列满，不覆盖发送侧丢弃。
   界面必须用 `sequence` 连续性交叉校验（已实现：序号跳变插入断点）。
5. **`ratio` 需要区间表才发布**。只建基线不配区间表时主图必然空白，
   界面已用文字说明原因，不要当成故障。
6. **R 与 R/R0 不能互相推导**（一个未滤波、一个滤波后，且量化不同），
   图上不得做"用 R 反算 R/R0"之类的功能。
7. **设备不接受外部给的 R₀**。`drms_user_config.c:812` 明确"只有 commit_baseline
   这一条路径"，而它只被 `BUILD_R0` 调用；协议里也没有任何 r0 字段。
   所以上位机只能"让设备自己采一段算"，无法手工输入或直接指定某个读数。

## 已知限制 / 下一步

| 项 | 说明 |
| --- | --- |
| 开始/结束记录按钮 | 核心库已实现（`BeginRecord`/`EndRecord`），界面按钮尚未接上 |
| **出厂空配置问题** | `GET_CONFIG` 返回 `UNSUPPORTED`，此时 `baseline_min_count` 不可读，`BUILD_R0` 前置条件不满足。**首次必须先完整下发一次 `APPLY_CONFIG`**（界面上的"下发配置"按钮） |
| 历史回放 | 未实现。BIN v2 解析规格见 [记录格式](../docs/design/2026-11-06-record-v2-format.md) |
| MSC 交接 | 未实现（固件侧仍有 SAFE_STOP 与导出所有权冲突待定） |
| 界面平滑 / min-max 包络 | 未实现（规格 §7.4、§9 要求，当前是逐点折线） |
| 视口缩放 | 未实现，当前固定自动缩放 |
| 区间色带 | 未绘制（规格 §3.5 要求主图叠加区间色带） |

## 验证状态（2026-11-16 真机）

台架条件：USB 供电、未接电池、样品端 443 Ω 电阻（临时替代，非标定试件）。

| 项 | 结果 |
| --- | --- |
| 四条协议向量逐字节对齐 | ✅ |
| 握手 / UID 与 Windows 枚举一致 | ✅ |
| GET_STATUS 全字段解析 | ✅ |
| CURVE 订阅 200 ms、`lost=0` | ✅ |
| 配置下发 → 回读逐值精确（4 条区间） | ✅ |
| BUILD_R0 → `Ok`，`baselineVer` 递增 | ✅ |
| ratio 发布（0.994–1.006 波动） | ✅ |
| 判级 `Confirmed` / `level=0` | ✅ |
| 界面主副图绘制 | ✅ |
| **基线失败路径**（开路 → `Incomplete`） | ✅ 如实报告，不崩溃不误报 |

**未验证**：真实标定试件、10–120 kΩ 满量程精度、长期稳定性、掉电恢复、
多卡兼容、Windows 打包分发。443 Ω 远低于设计量程下限（10 kΩ），
该点 CV≈0.5–4.4%，信号仅占 ADC 满量程 0.015–0.145%，**不能作为精度证据**。

## 跨平台说明

同一份代码在 Ubuntu 与 Windows 都能构建。两处平台差异：
- 中文字体：Windows 注册 `msyh.ttc`，Linux 找 Noto CJK（`MainWindow.RegisterCjkFont`）。
  ScottPlot 走 SkiaSharp，**必须显式 `Fonts.AddFontFile`**，光写字体名会显示豆腐块。
- 串口：`System.IO.Ports` 托管实现，两侧一致；DTR 必须拉起，否则固件不接受 HELLO。
