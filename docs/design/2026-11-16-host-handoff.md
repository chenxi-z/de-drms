# 上位机开发交接（2026-11-16）

**给在新电脑上接手本项目的会话**。本文假设你什么都不记得，按顺序读即可。
读完本文后，还应读 `host/README.md`（工程细节）与 `docs/design/2026-11-14-host-curve-display.md`（界面规格）。

---

## 一、当前状态一句话

**上位机第一版已可运行并在真板上验证**：连设备 → 下发配置 → 建立 R₀ → 主图画出 R/R₀ 曲线 → 判级。
缺少：记录按钮、历史回放、区间色带、平滑、视口缩放、MSC 交接。

---

## 二、新电脑上先做什么（按顺序，别跳）

### 1. 装 .NET 10 SDK

**必须是 .NET 10**，不能用 8/9。原因（实测，不是猜）：

```
ScottPlot.Avalonia 5.1.x  →  要求 Avalonia ≥ 12.0
Avalonia 12                →  要求 Roslyn ≥ 4.14（源码生成器用）
Roslyn 4.14                →  只在 .NET 10 SDK 中提供（.NET 8 只带 4.11）
```

两条路，任选：

```bash
# A. 用户目录安装（无需管理员，推荐）
curl -sSL https://dot.net/v1/dotnet-install.sh -o dotnet-install.sh
bash dotnet-install.sh --channel 10.0

# B. Windows 官方安装器
# https://dotnet.microsoft.com/download/dotnet/10.0 → dotnet-sdk-10.0.404-win-x64.exe
```

装完验证：

```bash
dotnet --version     # 必须 10.x
```

**如果装在用户目录**（`~/.dotnet`），每次新开终端都要先设环境：

```bash
export DOTNET_ROOT="$HOME/.dotnet"
export PATH="$DOTNET_ROOT:$PATH"
```

Windows Git Bash 下是 `export DOTNET_ROOT="C:/Users/<你>/.dotnet"`。

### 2. 装 Avalonia 模板

```bash
dotnet new install Avalonia.Templates
```

### 3. 装固件工具链（如果要改/构建固件）

```bash
# ST 官方命令行工具集，自带 arm-none-eabi-gcc 14.3.1 + make
# 从 https://www.st.com/en/development-tools/stm32cubeclt.html 下载安装
export PATH="/c/ST/STM32CubeCLT_1.22.0/GNU-tools-for-STM32/bin:/c/ST/STM32CubeCLT_1.22.0/Make/bin:$PATH"
make -C firmware/DE-DRMS-Code -j8
```

> **注意**：仓库文档记录的历史基线是 GCC 13.2.1，CubeCLT 给的是 14.3.1。
> 两者都能构建，但 `text` 段大小不可直接比较（`-O3 -flto` 代码生成不同）。
> **门禁看 `data+bss` 与关键符号尺寸，不看 text 绝对值。**
> 当前 `data+bss = 736.0 KiB`，距 736 KiB 门禁**只剩 16 字节**，加任何主 RAM 静态分配前必须核算。

### 4. 跑一遍测试确认环境正常

```bash
# 主机测试（456 项）
python -m unittest discover -s test -p 'test_*.py'

# 上位机测试（43 项）
cd host/Drms.Core.Tests && dotnet test
```

> **Windows 上必须用 `python` 而不是 `python3`**（后者常是应用商店占位符，静默退出码 9009）。
> 测试的跨平台适配（编译器名 `cc`/`gcc`、产物扩展名 `.so`/`.dll`、DLL 卸载）
> 全部集中在 `test/_platform.py`，**不要在任何测试里重新硬编码平台判断**。

### 5. 启动上位机

```bash
cd host
dotnet run --project Drms.Gui -- --auto COM5    # 启动即连接
dotnet run --project Drms.Gui                    # 手动选串口
```

要给别人用的独立 exe，发布自包含版本：

```bash
dotnet publish Drms.Gui/Drms.Gui.csproj -c Release -r win-x64 \
  --self-contained true -p:PublishSingleFile=true \
  -p:IncludeNativeLibrariesForSelfExtract=true -o dist
# 产物 host/dist/Drms.Gui.exe，约 101 MB，双击可运行，已被 .gitignore 忽略
```

---

## 三、踩过的坑（每条都实测过，别再踩）

### 坑 1：ScottPlot 的 AvaPlot 不守布局约束

**Avalonia 12 + ScottPlot.Avalonia 5.1.59 下，`AvaPlot` 会无视任何尺寸约束，
铺满整行并遮住同级控件。**

以下五种写法**全部实测失败**（用最小工程逐个复现，也查过 GitHub issues 与官方示例）：

| 写法 | 结果 |
| --- | --- |
| `Grid ColumnDefinitions="*,300"` | 图表铺满 1200 px，右侧面板完全不显示 |
| `DockPanel` + `Dock="Right"` | 同上 |
| 覆盖层 `HorizontalAlignment="Right"` | 被图表盖住 |
| 固定左列 `Width="1040"` | 图表仍铺满 |
| 官方示例的 `Grid.Row/Column` + `Stretch` | 同样失败 |

**唯一可靠的约束是给固定 `Height`。** 当前布局：

```
ScrollViewer > StackPanel
  ├─ 连接栏
  ├─ 读数面板（单行 WrapPanel）
  ├─ 主图 R/R0      Height=340
  ├─ 副图 R         Height=240
  └─ Expander「配置与基线」IsExpanded=False
```

**不要试图改回左右分栏**，除非先验证新版本 ScottPlot 修了这个问题。

### 坑 2：中文显示成豆腐块

ScottPlot 走 SkiaSharp，**只认已注册的字体**。写 `FontName = "Microsoft YaHei"`
**没用**，系统字体不会被自动发现。必须显式加载字体文件：

```csharp
ScottPlot.Fonts.AddFontFile("Microsoft YaHei", @"C:\Windows\Fonts\msyh.ttc");
// 然后 Plot.Font.Set("Microsoft YaHei")
```

已在 `MainWindow.RegisterCjkFont()` 实现，会依次尝试 msyh.ttc / msyhl.ttc /
simhei.ttf / simsun.ttc，启动日志会打印实际注册的那个。

### 坑 3：`bin\Debug\...\Drms.Gui.exe` 双击起不来

那是**依赖框架**的构建产物，会去 `C:\Program Files\dotnet` 找 .NET 10 运行时。
如果 .NET 10 装在用户目录，双击会报 `You must install or update .NET`。

用 `dotnet run`，或用自包含发布产物 `dist\Drms.Gui.exe`。

### 坑 4：`GET_OPERATION` 的 result 字段是双关的

固件 `drms_cdc_v2.c:331` 写的是 `result = operation.result`——**同一个字段既承载
"查询是否成功"又承载"操作结果"**。

所以 `INCOMPLETE(9)` 的回复意思是"查询成功，操作以 INCOMPLETE 结束"，是**合法终态**。
如果像普通请求那样把非 OK 都当异常抛，基线失败时会直接崩溃（本项目真实踩过）。

正确判据：只有 `INVALID`/`STALE`/`BUSY` 才是查询失败。

### 坑 5：出厂空配置下 `BUILD_R0` 必然失败

`GET_CONFIG` 在出厂状态返回 `UNSUPPORTED`，此时 `baseline_min_count` 读不到，
`BUILD_R0` 的前置检查过不了。

**新设备第一次使用必须先点"下发配置"**（下发一份完整 APPLY_CONFIG，含区间表与基线策略）。
界面已把这条原因写在基线面板上，不要误报成"按钮坏了"。

### 坑 6：设备不接受外部给的 R₀

`drms_user_config.c:812` 明确："要真正建立新基线，只有 commit_baseline 这一条路径"，
而它只被 `BUILD_R0` 调用。协议里**也没有任何 r0 字段**。

所以"手工输入 R₀"或"点一下用当前值"这两种设计**在硬件上不存在**。
唯一合法方式就是 `BUILD_R0`：设备自己采一段连续有效读数算均值。

### 坑 7：小阻值测不准（不是 bug）

设备设计量程 **10–120 kΩ**。实测数据（2026-11-16，同一台设备）：

| 试件 | 信号占 ADC 满量程 | CV |
| --- | --- | --- |
| 短接 | 0.015% | 4.46% |
| 126 Ω | 0.041% | 5.33% |
| 443 Ω | 0.145% | 0.546% |
| 100 kΩ（板载参考） | ~34% | ~0.007% |

在 443 Ω 上 CV≈0.5% 是**模拟前端的噪声地板**，不是电阻在变。
建基线要求 CV ≤ 0.1%，所以小阻值必然失败——这是正确行为。

**临时验证软件流程**时可以放宽 CV 限值（`Drms.Probe COM5 10 0.6` 的第 3 个参数 =
CV 上限百分比），但**这样建出的 R₀ 没有物理意义**。

### 坑 8：Windows 上 `BUILD_DIR` 不能传 Windows 风格路径

```bash
# 错：生成 D:C:/... 这种非法依赖文件名
make -C firmware/DE-DRMS-Code BUILD_DIR=D:/tmp/build

# 对：省略即用仓库内 build/（已 gitignore）
make -C firmware/DE-DRMS-Code -j8
```

---

## 四、代码结构（host/）

```
host/
  Drms.Core/                 零 GUI 依赖，可单测，Ubuntu 与 Windows 都能构建
    Protocol/
      Crc32.cs               CRC-32/ISO-HDLC（"123456789" → 0xCBF43926）
      Cobs.cs                标准 COBS
      FrameCodec.cs          20 字节头 + 载荷 + CRC + 0x00 分隔符；FrameSplitter 处理拆包/粘包
      Tlv.cs                 TLV 读写；73 个字段号与 JSON 一一对应
      Enums.cs               全部枚举（数值取自 JSON，不按 C 源码推断）
      Messages.cs            业务消息编解码 + 区间表 30 字节条目
    Config/
      DeviceConfig.cs        完整配置组装（tag 72–83）+ IntervalBuilder（百分比 ↔ lo/hi）+ Validate
    Session/
      DeviceSession.cs       握手、请求配对、超时、事件分发
      OperationWaiter.cs     ACCEPTED → 轮询到 FINISHED
      BaselineRunner.cs      前置检查 + BUILD_R0 封装
    Transport/
      IByteLink.cs           链路抽象（便于用假设备做单测）
      SerialByteLink.cs      System.IO.Ports 实现（DTR 必须拉起）
  Drms.Core.Tests/           43 项：4 条权威向量逐字节 + 会话/配置/基线
  Drms.Gui/                  Avalonia 12 + ScottPlot 5
    MainViewModel.cs         界面状态 + 动作（连接/下发配置/建基线）
    ConfigViewModel.cs       区间表编辑（四行百分比）+ 基线面板状态
    MainWindow.axaml(.cs)    布局与绘图
  Drms.Probe/                控制台联调工具（不算界面就能验证协议）
```

### 分层原则

- **`Drms.Core` 不许引用任何 GUI 类型**——这是它能在 Ubuntu 上全速测试的前提。
- 协议字节问题抛 `ProtocolException`；设备返回错误抛 `DeviceException`（带 Result/Reason）。
  两者不要混。
- 界面只做"调 Core + 转成人能读的文字"，不自己解释协议。

---

## 五、已验证内容（2026-11-16，真板 COM5）

台架条件：USB 供电、未接电池、样品端 443 Ω 电阻（**临时替代，不是标定试件**）。

| 项 | 结果 |
| --- | --- |
| 四条协议向量逐字节对齐 | ✅ |
| 握手 / UID 与 Windows 枚举一致 | ✅ |
| GET_STATUS 全字段解析 | ✅ |
| CURVE 订阅 200 ms、`lost=0`、间隔精确 200000 µs | ✅ |
| 配置下发 → 回读逐值精确（4 条区间） | ✅ |
| BUILD_R0 → `Ok`，`baselineVer` 递增 | ✅ |
| ratio 发布（0.994–1.006 波动） | ✅ |
| 判级 6/6 次 `Confirmed` / `level=0` | ✅ |
| 界面主副图绘制、中文显示 | ✅ |
| 基线失败路径（开路 → `Incomplete`） | ✅ 如实报告，不崩溃不误报 |
| 自包含 exe（`dist/`）双击运行 | ✅ |

**未验证**：真实标定试件、10–120 kΩ 满量程精度、长期稳定性、掉电恢复、
多卡兼容、Windows 打包分发、USB 拔插重连。

---

## 六、下一步建议（按价值排序）

1. **开始/结束记录按钮**（核心库方法已有：`BeginRecord`/`EndRecord`，只差接界面）。
   接上后"联机监测 + 记录"的最小闭环才完整。
2. **区间色带**（规格 §3.5 要求主图叠加）。数据已在 `Config.Bands`，只需画到图上。
3. **历史回放**（BIN v2 解析）。规格见 `docs/design/2026-11-06-record-v2-format.md`，
   已验证的参考实现是 `tools/de_drms_log.py` 的 `LogReaderV2`/`LogReaderV2Segments`，
   C# 侧应等价重写并用 `test/test_log_v2_codec.py` 的黄金文件逐字节对齐。
4. **界面平滑与 min-max 包络**（规格 §7.4、§9）。注意包络必须先于平滑计算。
5. **视口缩放**（规格 §7.1 的视口 + 尺度滑块模型）。

---

## 七、必须遵守的约束

- **改协议要成对更新** `shared/protocol/`（机器可读）与 `docs/protocol/`（人读），同一提交。
- **不要改 EDA / IOC / 原理图**（用户自己管）。
- **外部资料不入库**（器件手册、论文）→ Obsidian 库。
- **提交后同时推 GitHub 与 Gitee** 并核对两端 SHA。用户 2026-11-15 说明本机以 Gitee 为准，
  但换电脑后若两个 remote 都在，按仓库 `AGENTS.md` 的双远端规则执行。
- 引脚、器件型号等定稿结论若变更，要同步主文档附录 F + `pin-assignment.md` +
  `README.md` + `AGENTS.md` + `HANDOFF.md`。
