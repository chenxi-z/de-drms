# AGENTS.md — DE-DRMS 工作区说明

双电极直流电阻测量仪（用于两端 MWCNTs 导电网络传感层的结构损伤分级监测）。
**当前是纯设计文档阶段**：`firmware/`、`host/`、`hardware/` 等目录仅有 `.gitkeep` 占位，
尚无代码、原理图与 PCB，**没有构建/测试命令可跑**。

## 必读文档（动手前按序读）

1. `docs/design/README.md` — 设计文档索引（入口，含已定稿决策总表与未决事项）
2. `docs/design/2026-10-10-universal-signal-chain.md` — 主设计文档：
   **附录 D** = 应用需求与指标（需求来源）；**附录 E** = 硬件实现定稿。
   **两者冲突时以附录 E 为准**；更早版本文档（V1.0~V2.2）仅是决策历史，不得据此实现。
3. `docs/design/HANDOFF.md` — 新会话交接提示词（设计线 + Obsidian 归档线）

## 仓库结构

目录职责全表见根 `README.md`。要点：

- `docs/design/` — 权威设计文档与选型记录（adc-selection/、mcu-selection/、diagram/）
- `adc_ds/` — 选型期间候选 ADC 数据手册（PDF + txt 提取，已入库）；
  完整器件手册库在 Obsidian `20-硬件工程/datasheets/`（另一会话管理，勿在本仓库重复存放）
- `shared/protocol/`（机器可读）与 `docs/protocol/`（人读）是协议的单一事实来源，
  **改协议必须成对更新、同一提交**
- 其余目录（host/firmware/hardware/…）目前为空

## 已定稿硬件决策（无新依据不要推翻）

| 环节 | 定稿 |
| --- | --- |
| 拓扑 | 恒流激励 + 双通道同步实测（恒流测电阻，不做电桥） |
| 激励 | 8 µA 恒流；Rsense = 150 kΩ 0.1%；运放 OPA333/OPA388 + BSS138 |
| ADC | ADS131A02（2 通道同步、24 bit、128 kSPS、内部 1.2 V 基准、3.3 V 直连） |
| 前端 | 每通道一颗跟随器（OPA388/OPA320）；保护 BAV199（默认）/ 低漏电 ESD 阵列（备选焊盘） |
| 自校准 | 0.1% Rsense 打底 + 板上 R_ref 自检（切换电路待细化，方案见 E.3） |
| MCU | STM32U575RGT6（M33 160 MHz、1 MB Flash、786 KB SRAM、USB OTG FS、LQFP-64） |
| 温度/电源/通信 | TMP117（I²C）；1S 锂电（可充电）+ 双 LDO 3.3 V；USB OTG FS 设备模式 |

## 硬约束（改任何参数都要复核）

- 电流与 Rsense 配套：V_Rsense = I×Rsense ≤ 1.2 V 且 V_sample = I×R_max ≤ 1.2 V
  （8 µA × 150 kΩ = 1.2 V，正好用满 ADS131A02 内部基准）
- 测量窗口内不切换增益 / 电流 / 极性
- 高阻节点保护漏电 < 1 nA（源阻抗最高 150 kΩ）
- 温度补偿是能否达到 1% 精度的决定性环节（材料温度系数 −4 ~ −10 %/℃）

## 已被否决（不要重走）

- 电桥（被测对象是两端电阻条，物理上无法成桥）
- 比例式（Rsense 接 REF）+ ADS127L11（基准输入电流 ±2 µA，对 150 kΩ 源阻抗致命）
- 分压激励替代恒流源（电流随 R 变 50%、自热不一致、断裂时输出不定）
- ADS1262（需 4.75 V 供电）、AD779x（无基准缓冲）、ADS1235（500 nA + 5 V）
- STM32 U5↔G4 pin2pin（不存在；pin21 VCAP vs VDDA 硬冲突）

## 需外部输入才能推进（不要自行假设）

- 分档阈值（绿/黄/橙/红）：需该批试件的 R/R₀–位移标定曲线
- 温度系数：需实测（论文值仅作参考）
- "R₀ 的 1%" 的适用区间与量程下限

## 工作约定

- 远端 `git@gitee.com:chenxi666/de-drms.git`（SSH 已配好）；提交后推送并核对远端 SHA
- 提交用 Conventional Commits；文档中文、代码标识符英文；文本 LF（`.gitattributes` 固定）
- 只提交源文件与文档；固件产物、EDA 输出、编译目录不入库；空目录用 `.gitkeep` 占位
- **规格必须查数据手册核实，不要凭记忆**——此前曾把 STM32U545 RAM 误报为 160 KB
  （实际 274 KB），也曾误判 ADS127L11 可做比例式（被基准输入电流否决）
- 建议的下一步顺序：R_ref 自校准切换电路细化 → 引脚分配/时钟/电源域（E.5.5）→
  原理图/PCB/BOM → 固件与上位机
