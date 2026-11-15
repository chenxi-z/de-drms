# 上位机技术栈决定（2026-11-15）

状态：**已选定并验证**。用户 2026-11-15 确认。
接续 [需求交接](2026-11-13-host-requirements-handoff.md)与[曲线显示规格](2026-11-14-host-curve-display.md)。

本文只记录技术选型与其依据。**功能范围与界面行为以曲线规格为准**，本文不重复。

## 1. 决定

| 项 | 选择 | 版本（2026-11-15 实测） |
| --- | --- | --- |
| 语言 | **C#** | — |
| 运行时 | **.NET 10** | SDK 10.0.404 |
| GUI 框架 | **Avalonia** | 12.1.6 |
| 图表 | **ScottPlot.Avalonia** | 5.1.59 |
| 目标平台 | Windows 主交付，Ubuntu 主力开发 | — |

**开发方式（用户确认）**：Windows 机器可用，但**日常开发在 Ubuntu**，
Windows 用于最终验收与打包。

## 2. 为什么不是 WPF

用户最初倾向 WPF。**WPF 无法在 Linux 上构建或运行**——它依赖 DirectX 与 Windows
图形子系统，`net10.0-windows` 目标框架只能在 Windows 上编译。
这与"日常在 Ubuntu 开发"直接冲突。

Avalonia 是 WPF 的跨平台继任者：XAML 语法、MVVM、数据绑定、控件模型高度相似，
迁移成本低，且同一份代码在 Ubuntu 与 Windows 都能编译运行。

## 3. 版本组合是一条连环依赖（实测，不能自由搭配）

```
ScottPlot.Avalonia 5.1.x  →  要求 Avalonia ≥ 12.0
Avalonia 12              →  要求 Roslyn ≥ 4.14（源码生成器用）
Roslyn 4.14              →  只在 .NET 10 SDK 中提供（.NET 8 只带 4.11）
```

**实测反例**（2026-11-15 在本机验证）：

| 组合 | 结果 |
| --- | --- |
| .NET 8 + Avalonia 11.2.3 | 编译通过（去掉 v12 专属 `WithDeveloperTools()` 后） |
| .NET 8 + Avalonia 11 + ScottPlot.Avalonia 5.1.59 | **还原失败**：ScottPlot 要求 Avalonia ≥ 12 |
| .NET 8 + Avalonia 12 | **编译失败**：`InitializeComponent` 缺失，因 Roslyn 4.11 < 4.14 |
| **.NET 10 + Avalonia 12.1.6 + ScottPlot 5.1.59** | **编译通过，0 错误 0 警告** |

**因此必须整体使用 .NET 10 + Avalonia 12 + ScottPlot 5**，不要尝试降版本。
Avalonia 12 的项目模板默认目标即为 `net10.0`，说明这是官方主路径。

## 4. 为什么选 ScottPlot

曲线规格要求的核心能力：视口导航（§7.1）、min/max 包络抽稀（§7.4）、
千万点级数据、MATLAB 风格（§10）。ScottPlot 是 .NET 生态中对大数据最友好的
绘图库，内置降采样，`SignalPlot` 面向大数组设计。

**未选用**：

| 库 | 不选的理由 |
| --- | --- |
| OxyPlot | 大数据性能一般；Avalonia 支持存在但更新滞后 |
| LiveCharts2 | 动画开销大，实时场景吃 CPU |

## 5. 本机环境状态（2026-11-15 已装并验证）

| 项 | 状态 |
| --- | --- |
| .NET 8 SDK | 8.0.428（保留，兼容旧项目） |
| .NET 10 SDK | 10.0.404（默认） |
| Avalonia 模板 | 已安装 |
| 安装方式 | `dotnet-install.sh` 装到 `~/.dotnet`（用户目录，无需 root） |
| PATH | 已在 shell 配置中，新开终端 `dotnet` 可用 |

验证方式：`dotnet new avalonia.app` + `dotnet add package ScottPlot.Avalonia` + `dotnet build`。

## 6. 架构分层（与语言无关）

按需求交接 §6 的建议，core 与 GUI 分离：

```
host/
  Drms.Core/          # 零 GUI 依赖，可单测
    Protocol/         # CDC v2 编解码（COBS + TLV + CRC-32）
    BinFile/          # BIN v2 读取（含分段）
    Session/          # 会话、重连、request_id 去重
    Store/            # 本地试验归档
  Drms.Gui/           # Avalonia + ScottPlot
  Drms.Core.Tests/    # 无界面测试
```

好处：core 可在 Ubuntu 上用 `dotnet test` 全速验证（含模拟设备回放），
GUI 只是薄层；Windows 打包风险集中在 GUI 层。

### 6.1 已有资产需移植

`tools/de_drms_log.py` 的 `LogReaderV2` / `LogReaderV2Segments` 是**已验证的参考实现**：
chunk 流、逐块 CRC、锚点时间重建、v1/v2 分派、分段拼接、缺口与帧格式校验。
C# 侧需等价重写，**并用 `test/test_log_v2_codec.py` 的黄金文件逐字节对齐**——
该测试含手工可核算的期望值，是解析正确性的锚点。

移植时保留 Python 版作为交叉校验工具（双方对同一文件应得相同结论）。

## 7. 未决

1. **Windows 打包方式**：`dotnet publish` 自包含单文件 vs 依赖框架；需在 Windows 实测体积与启动时间。
2. **USB CDC 在 Windows 的枚举稳定性**：需实机验证设备拔插、驱动匹配（可能需自定义 INF 或指定 VID/PID）。
3. **图表样式细节**：MATLAB 风格的具体参数（字号、网格密度）待首版界面成型后调。
4. ScottPlot 与视口模型的对接方式：用 `SignalPlot` 内置降采样还是自行提供 min/max 包络数组（倾向后者，因为规格 §7.4 明确要求保尖峰且比内置算法可控）。

## 8. 参考

- [需求交接](2026-11-13-host-requirements-handoff.md)
- [曲线显示规格](2026-11-14-host-curve-display.md)
- [CDC v2 协议](../protocol/de-drms-cdc-v2.md)
- [BIN v2 格式](2026-11-06-record-v2-format.md)
