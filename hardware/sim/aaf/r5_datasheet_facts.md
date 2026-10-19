# M1–M7 手册核实结果（Round 5 抗混叠采集子系统）

- **日期**：2026-10-18
- **用途**：为 `docs/design/spec/2026-10-18-aa-driver-design.md` §5.3 待核项填实，供 `opt_round5.py` / V8 kickback 模型 / 评分阈值使用
- **纪律**：本文所有数值均来自手册原文或手册图线的矢量读数，**不含凭记忆填值**；手册未给的项明确写"未给"，不猜测

---

## 0. 手册来源与版本（重要：规格文档的文献号写错了）

| 器件 | 规格文档/计划里写的 | **实际正确文献号** | 版本 | 来源 |
|---|---|---|---|---|
| ADS131A02 | ~~SBAS890~~ ❌ | **SBAS590E** | 2016-03 首版，2020-06 修订 E | ti.com `https://www.ti.com/lit/ds/symlink/ads131a02.pdf` |
| OPA388 | SBOS777 ✔️ | **SBOS777D** | 2016-11 首版，2020-07 修订 D | ti.com `https://www.ti.com/lit/ds/symlink/opa388.pdf` |

**SBAS890 是 ADS131M04 的手册**（已实测下载核对：`pdfinfo` 标题 = "ADS131M04 4-Channel ... datasheet (Rev. D)"，共 10 页）。
ADS131A02 的正确手册是 **SBAS590E**（95 页）。规格 §5.3 M1 与计划 Task 1 Step 1 的文献号需订正。

**本机 Obsidian 库未找到**：按本机全局约定应在 `20-硬件工程/datasheets/`，实际全盘检索无此目录（`E:/Obsidian` 仅有空库，`E:/wiki/datasheets` 只有 STM32H7 手册）。
故按任务指令回退到 ti.com 下载核实；**下载件未入库**（`.gitignore` + 入库守卫要求外部资料不入库）。

---

## 1. 机读数据块（供 opt_round5.py / 后续脚本 import）

```python
FACTS = {
    # ---- 时钟（M5）----
    "MCLK_HZ":            16.384e6,   # XTAL1/CLKIN，SBAS590E p9 / p11
    "FMOD_HZ":            4.096e6,    # = fCLKIN/2/2（CLK_DIV=001, ICLK_DIV=001），SBAS590E p11/p67/p68
    "FDATA_HZ":           128e3,      # = fMOD/32（OSR=1111），SBAS590E p68
    "OSR":                32,
    "CLK_DIV_SETTING":    0b001,      # fICLK = fCLKIN/2  （复位值 100 = /8，必须改）
    "ICLK_DIV_SETTING":   0b001,      # fMOD  = fICLK/2   （复位值 100 = /8，必须改）

    # ---- 数字滤波器（M1）----
    "SINC3_F3DB_HZ":      33790.0,    # 手册 Figure 46 矢量读数 0.264 x fDATA（不确定度 ±1%）
    "SINC3_F3DB_HZ_FORMULA": 33488.0, # 手册 Eq.7 解析式 0.26162 x fDATA（K=1.0，OSR=32）
    "SINC3_ATT_16K_DB":   -0.67,      # sinc3 在 16 kHz 处的固有跌落（与本设计强相关，见 §8）
    "SINC3_ATT_8K_DB":    -0.17,

    # ---- ADC 输入网络（M2/M3/M6）----
    "ADC_CS_PF":          3.5,        # 差分采样电容 Cs（EC 表 p10；Fig.38 以 Cs/2 画在每侧）
    "ADC_ZIN_OHM":        130e3,      # EC 表 typ @fMOD=4.096 MHz，p10
    "ADC_ZIN_FORMULA_OHM":139.5e3,    # Eq.5: 2/(fMOD*Cs)，p29
    "ADC_RSW_OHM":        None,       # ⚠️ 手册未给 —— 不得当作手册值使用
    "ADC_RSW_ASSUMPTION_OHM": 1.0,    # 规格 §7 规定的缺省建模值（LTspice 默认开关）
    "ADC_SW_DUTY":        0.5,        # Fig.37：S1/S2 各占 tMOD 的一半、180° 反相（p29）
    "ADC_SW_FREQ_HZ":     4.096e6,    # = fMOD（每 tMOD 一个采样周期）

    # ---- 跟随器（M4/M7）----
    "OPA388_AOL_4M_DB":   7.0,        # Figure 6-8 矢量读数（±0.3 dB），p12
    "OPA388_AOL_4M_VV":   2.24,       # 10**(7.0/20)
    "OPA388_GBW_HZ":      10e6,       # EC 表 p9
    "OPA388_ZOUT_CURVE_REF": "SBOS777D Figure 6-25（开环；手册无闭环曲线），p15",
}
```

---

## 2. M1 — sinc³ 滤波器 −3 dB 频率 @OSR=32

| 项 | 内容 |
|---|---|
| **手册出处** | SBAS590E **p33** §9.3.6 Digital Decimation Filter（Eq.6/Eq.7 + Table 6）；**p34** Figure 45/46/47 |
| **手册给的形式** | 无 −3 dB 表，只有曲线。Figure 46 = "Sinc3 Filter Roll-Off"，横轴 fIN/fDATA 归一化 0–0.5，纵轴 0 ~ −20 dB（0.1/级的细网格） |
| **Figure 46 矢量读数** | **f₋₃dB = 0.264 × fDATA** → **33.79 kHz**（@fDATA=128 kHz，±1%） |
| **Eq.7 解析值** | 解 `\|sin(πNx)/(N·sin(πx))\|³ = 10^(−3/20)`，N=32 → x = 0.26162 → **33.49 kHz** |
| **Table 6 校正因子** | OSR=32 的 K = 1.0（仅 800/400/200 与 768/384/…/48 才需 K），故解析式可直接用于 OSR=32 |
| **两侧一致性** | 图 46 读数比解析式高 **+0.9%**（读图不确定度内） |
| **与规格推算偏差** | 规格未给数值推算。若按"0.262×fDATA"口径，偏差 **<1%**，远小于 20% 判据 ✅ |

**D4 判定基准的直接后果（务必读）**：sinc³ 的固有跌落是**数字域**的，模拟阶梯无法补偿，也不应补偿：

| 频率 | sinc³ 固有衰减 |
|---|---|
| 8 kHz | **−0.17 dB** |
| 16 kHz | **−0.67 dB** |
| −0.05 dB 点 | 4.37 kHz |
| −0.1 dB 点 | 6.18 kHz |

D4 在 §5.1 中定义为「AC 仿真」= V1 的**模拟段**（跟随器→阶梯→ADC 引脚）**相对 DC** 的偏差，
**本身已排除 sinc³**，故 0.05 dB 阈值在模拟段是可达的 ✅。
**唯一风险是执行时误扩口径**：若有人把 D4 当"整链/含数字滤波"来测，16 kHz 处 −0.67 dB 会超阈值 13 倍、三案全灭。
→ 已在 §5.3 写明边界：实测端到端频响与 D4 比对时，须先反算掉 sinc³ 的固有响应。

---

## 3. M2 — ADS131A02 输入采样电容

| 项 | 值 | 出处 |
|---|---|---|
| **差分采样电容 C_S** | **3.5 pF**（typ） | SBAS590E **p10** §7.5 Electrical Characteristics → ANALOG INPUTS → `Cs Input capacitance 3.5 pF` |
| 结构 | 每侧 **C_S/2**，经 S1 接入、S2 复位（180° 反相） | **p29** §9.3.2 + Figure 38 "Equivalent Analog Input Circuitry"（图内明确标 `Cs/2`） |

**换算**：差分采样电荷 Q = C_S × V_IN。

| V_IN | Q |
|---|---|
| 2.442 V（满量程） | 8.55 pC |
| 1.0 V | 3.50 pC |
| 0.86 V | 3.0 pC ← 与既有 README 的 `Q=3 pC @ fMOD` 假设吻合 |

**对规格的影响**：§4 决策 3 的"C_diff ≥ 采样电容 20~50 倍"→ 仅需 **70~175 pF**，几乎免费；
C_diff 实际取 nF 级是被 kickback 回稳与噪声带宽驱动，不是被这条比值驱动。原文口径不算错，但**不是约束**。

---

## 4. M3 — 输入电流 / 阻抗

| 项 | 值 | 出处 |
|---|---|---|
| **差分输入阻抗 Z_IN** | **130 kΩ typ @ fMOD = 4.096 MHz** | SBAS590E **p10** EC 表 `Zin Differential input impedance` |
| 阻抗公式 | `Z_IN = 2 / (fMOD × C_S)` | **p29** Eq.5 |
| 公式复算 | 2/(4.096 MHz × 3.5 pF) = **139.5 kΩ** | 与手册 130 kΩ 差 **+7.3%**（手册取整/含寄生） |
| **输入偏置电流（模拟）** | **手册未给数值** ⚠️ | 全文无 analog input bias current 规格行；仅有定性要求 **p85** "Leakage currents between the PCB traces can exceed the input bias current of the ADS131A0x…" |
| （易误引）`IIN = 10 µA` | **不是模拟输入**，是 DIGITAL INPUT/OUTPUT 的数字脚漏电 | **p11** EC 表 |

**结论**：M3 的"阻抗"已核实（130 kΩ，规格 E.4 现用值正确）；
"输入电流"**没有手册数值**，靠 Eq.5 的开关电容等效电流（V_IN/Z_IN，2.442 V 时 ≈18.8 µA 平均）建模，
不得把数字脚的 10 µA 当模拟输入偏置电流引用。

---

## 5. M5 — fMOD 确切值：**是 fCLKIN/4，但 /4 是寄存器配置出来的，不是固定关系**

时钟链（SBAS590E **p27** Figure 35；**p28** §9.3.1.2/§9.3.1.3）：

```
XTAL1/CLKIN ──[CLK_DIV]──> fICLK ──[ICLK_DIV]──> fMOD ──[OSR]──> fDATA
```

| 寄存器 | 字段 | 复位值 | 本设计所需 | 依据 |
|---|---|---|---|---|
| CLK1 (0Dh) | `CLK_DIV[2:0]` | 100 = **/8** | **001 = /2** | **p67** Table 28 |
| CLK2 (0Eh) | `ICLK_DIV[2:0]` | 100 = **/8** | **001 = /2** | **p68** Table 29 |
| CLK2 (0Eh) | `OSR[3:0]` | 0110 = /400 | **1111 = /32** | **p68** Table 29 / **p69** Table 30 |

**本设计定值**：fCLKIN = 16.384 MHz → fICLK = 8.192 MHz（/2）→ **fMOD = 4.096 MHz（/2）→ 总 /4** → fDATA = 128 kSPS（OSR=32）。✅

**条文佐证**：
- EC 表 **p11**：`fICLK` typ **8.192 MHz**（CLKSRC=0）；`fMOD` high-res/VNCPEN=0：min 0.1 / **typ 4.096** / max **4.25 MHz**
- EC 表 **p9**：`fCLKIN` min 0.4 / **typ 16.384** / max 25 MHz
- Table 30（**p69**）：OSR=32 在 fMOD=4.096 MHz 下 fDATA = **128.000 kHz**；OSR=4096 → 1.000 kHz

⚠️ **固件配置陷阱**：若按复位值不动（CLK_DIV=/8、ICLK_DIV=/8），得 fICLK=2.048 MHz、fMOD=0.256 MHz、
OSR=32 时 fDATA 只有 8 kSPS。**必须在 CLK1/CLK2 里显式写 001/001/1111**。
（规格文档"fMOD=4.096 MHz"的结论正确，但从未记录这三位配置，属遗漏。）

**MCLK = 16.384 MHz**（晶振，p28 Table 5 推荐 Abracon ABLS-16.384MHZ-L4Q-T 等）。

---

## 6. M6 — 输入开关等效电阻与时序：**电阻手册未给，时序只给了波形**

| 项 | 手册情况 | 出处 |
|---|---|---|
| **R_on（开关导通电阻）** | **全文无规格** ⚠️（`grep -i "on-resistance\|on resistance\|\bRon\b"` 在 SBAS590E 全文命中 0 次） | — |
| **孔径时间 / 采样保持时间** | **无规格**（只有 sinc³ 的 t_SETTLE = 3 个转换周期，属数字滤波，不是采样开关） | p35 §9.3.6 |
| **开关时序** | S1、S2 **180° 反相**，周期 **t_MOD = 1/f_MOD**，各导通约 **50%**（Figure 37 方波，占空比目测 50%，上升沿无交叠） | **p29** Figure 37 |
| 开关拓扑 | 每侧：AIN → S1 → C_S/2 → S2 → (复位/共模)；差分两半反相工作 | **p29** Figure 38 |
| 相关设计约束 | "Do keep the input series resistance low to maximize THD performance"（无具体限值） | **p79** §12 Layout Guidelines |

**V8 建模规范（据此执行）**：
- R_sw **必须**按规格 §7 的缺省 `Ron = 1 Ω` 建模，并在报告中**明示这是假设而非手册值**；
  建议同时跑 `Ron = 1 / 100 / 1 kΩ` 三档灵敏度。
- 量级判据（本次实算）：C_S = 3.5 pF 时，`τ = R_on·C_S`；R_on 即使到 1 kΩ 也只有 **3.5 ns**，
  远小于 fMOD 半周期 **122 ns** → **R_on 不是 kickback 回稳的瓶颈**，瓶颈在外部 R_iso 与 C_diff。
  该结论与 R_on 具体值无关，可放心用于 D9 定性判断。
- 占空比按 **0.5**；开关频率按 **fMOD = 4.096 MHz**（每 t_MOD 完成一次采样）。

---

## 7. M4 / M7 — OPA388

### M4：AOL @ 4 MHz

| 项 | 值 | 出处 |
|---|---|---|
| **AOL @ 4.096 MHz** | **≈ 7.0 dB（2.24 V/V）**，读数带 ±0.3 dB | SBOS777D **p12** Figure 6-8 "Open-Loop Gain and Phase vs Frequency"（矢量路径读数） |
| 读图细节 | 4 MHz → 7.0 dB；2 MHz → 12.25 dB；1 MHz → 17.5 dB；8 MHz → 2.5 dB | 同上 |
| 0 dB 交点（f_T） | **≈ 11.7 MHz**（曲线），EC 表 GBW typ **10 MHz** | p12 / **p9** EC 表 |
| DC AOL | 126 dB min / **148 dB typ**（R_LOAD=10 kΩ，距轨 0.15 V） | **p9** EC 表 `AOL` |
| **GBW 近似校核** | 单极点近似：AOL(4.096 MHz) = 20log(10 M/4.096 M) = **7.75 dB**；实测曲线 **7.0 dB** → 偏差 **−0.75 dB（V/V 口径 −11%）** ✅ <20% |
| 与规格 §4 的对比 | 规格写"fMOD 主战场环路增益 ~8 dB"；实测 **7.0 dB**（约 0.88×，即低 1 dB）→ 方向一致、略偏悲观，**不需改结论** | — |

**含义（供 V9）**：跟随器在 4.096 MHz 处环路增益只有 2.24 V/V（≈7 dB）。
规格 §4 判"不进反馈环路"的依据成立，但裕量比想象薄：若做 Sallen-Key，Q 与 fc 在该频点会被明显拉动。

### M7：输出阻抗——**手册只有开环曲线，没有闭环曲线**

⚠️ **必须澄清**：SBOS777D 全文只有 **Figure 6-25 "Open-Loop Output Impedance vs Frequency"**（**p15**），
没有 closed-loop output impedance 曲线（`grep -i "closed-loop output"` 在 OPA388 全文 0 命中；
Figure 6-9 是 closed-loop **Gain**，不是阻抗）。

**手册值**：

| 来源 | 值 |
|---|---|
| EC 表 `Z_O`（**p9**） | **100 Ω typ**，条件 **f = 1 MHz, I_O = 0 A**（开环！） |
| Figure 6-25（**p15**）矢量/像素读数（开环，V_S=±2.5 V, C_L=100 pF） | 1 kHz ≈ **0.2 Ω**；10 kHz ≈ **5 Ω**；16 kHz ≈ **11 Ω**；100 kHz ≈ **95 Ω**；400 kHz ≈ **190 Ω**（峰值）；1 MHz ≈ **155 Ω**；2 MHz ≈ **123 Ω**；**4.096 MHz ≈ 110 Ω**；10 MHz ≈ **117 Ω** |

> 注：EC 表的 100 Ω @1 MHz 与 Figure 6-25 在 1 MHz 处读到的 ~155 Ω **对不上（差 ~55%）**。
> 手册自身不一致；本设计工作在 4 MHz，取曲线值 **110 Ω** 并记录该矛盾，供后续核对（不阻塞）。

**闭环值（本次推导，非手册曲线——使用须标注）**：
单位增益跟随器 `Z_o,cl = Z_o,ol / (1 + A_OL·β)`，β = 1：

| f | Z_o,ol（图 6-25） | A_OL（图 6-8） | **Z_o,cl（推导）** |
|---|---|---|---|
| 16 kHz | 11 Ω | 637 V/V | **17 mΩ** |
| 100 kHz | 95 Ω | 100 V/V | **0.94 Ω** |
| 1 MHz | 155 Ω | 7.5 V/V | **18.2 Ω** |
| **4.096 MHz** | **110 Ω** | **2.24 V/V** | **≈ 34 Ω** |
| 10 MHz | 117 Ω | 1.11 V/V | ≈ 55 Ω |

**对规格 §4"阶梯首级驱动假设（源阻抗 ≈0 Ω）"的影响**：
- 通带（≤16 kHz）：17 mΩ，完全可忽略 ✅
- **fMOD 处：≈34 Ω**。若阶梯首级 R 取 300–500 Ω，源阻抗占 **7–11%** → D1/D3 的 120/150 dB 预算里要计入；
  V7/V9 必须用非理想源阻抗重跑（规格 §7 V9 已要求，此处给出具体量级）。

---

## 8. 冲突仲裁（规格 §5.3 纪律 / 计划 Task 1 Step 4）

| 判据 | 结果 |
|---|---|
| fMOD ≠ 4.096 MHz？ | **否**，fMOD 确为 **4.096 MHz**（fCLKIN/2/2），Table 30 给出对应 fDATA=128 kSPS ✅ |
| sinc³ −3 dB 与推算偏差 >20%？ | **否**，偏差 **<1%**（33.79 kHz 图值 vs 33.49 kHz 解析值） ✅ |
| **结论** | **无冲突，可继续 Task 2** |

**但有三项"非冲突、须注意"的发现（不影响继续执行）**：

1. **D4 口径边界**：sinc³ 在 16 kHz 有 **−0.67 dB** 固有跌落。D4 按 §5.1 定义为模拟段 AC 仿真（已排除 sinc³），
   阈值可达；但**执行时不得把 D4 扩成整链/含数字滤波口径**，否则三案全灭（见 §2）。
2. **文献号错误**：规格 §5.3 与计划 Task 1 写 **SBAS890**，实为 **ADS131M04** 手册；ADS131A02 正确是 **SBAS590E**。
3. **M3/M6/M7 三项手册无值**：模拟输入偏置电流、开关 R_on/孔径时间、闭环输出阻抗曲线 —— 均已在上文标注"未给"，
   后续脚本必须用**显式假设 + 明示**，不得伪装成手册值（V8 的 Ron=1 Ω、V9 的 Z_o,cl 推导公式）。

---

## 9. 页码索引（便于复核）

| 手册 | 印刷页码 | 内容 |
|---|---|---|
| SBAS590E | **p9** | fCLKIN 0.4/16.384/25 MHz |
| SBAS590E | **p10** | EC 表：C_S = 3.5 pF、Z_IN = 130 kΩ、Data rate 1–128 kSPS |
| SBAS590E | **p11** | EC 表：fICLK typ 8.192 MHz；fMOD typ 4.096 / max 4.25 MHz；数字脚 I_IN = 10 µA |
| SBAS590E | **p23** | §8.1 Table 1（噪声表，条件明写 "fMOD = 4.096 MHz"） |
| SBAS590E | **p27** | Figure 35 时钟分频链 |
| SBAS590E | **p28** | §9.3.1.2/1.3/1.4（ICLK/MODCLK/Data Rate）；Table 5 推荐晶振 |
| SBAS590E | **p29** | §9.3.2 Analog Input；Figure 37 S1/S2 时序；Figure 38 输入等效电路（Cs/2）；Eq.5 Z_IN |
| SBAS590E | **p33** | §9.3.6 数字抽取滤波；Eq.6/Eq.7；Table 6 K 因子 |
| SBAS590E | **p34** | Figure 45/46/47/48/49 sinc³ 响应（**46 = Roll-Off，M1 主证据**） |
| SBAS590E | **p35** | §9.3.6 sinc³ 建立（3 个转换周期） |
| SBAS590E | **p67** | Table 28 CLK1（CLK_DIV，复位 100=/8） |
| SBAS590E | **p68** | Table 29 CLK2（ICLK_DIV，复位 100=/8；OSR[3:0]） |
| SBAS590E | **p69** | Table 30 数据率表（OSR=32 → 128 kSPS @4.096 MHz） |
| SBAS590E | **p79** | Layout：input series resistance 要低（无具体限值） |
| SBAS590E | **p85** | 输入偏置电流仅定性（PCB 漏电可超过它） |
| SBOS777D | **p9** | EC 表：A_OL 126/148 dB；GBW 10 MHz；**Z_O = 100 Ω @1 MHz（开环）** |
| SBOS777D | **p10** | Table 6-1 图表索引（Figure 6-25 = Open-Loop Output Impedance） |
| SBOS777D | **p12** | **Figure 6-8 AOL/Phase vs Frequency（M4 主证据）**；Figure 6-9 Closed-Loop **Gain** |
| SBOS777D | **p15** | **Figure 6-25 Open-Loop Output Impedance vs Frequency（M7 唯一曲线）** |

---

## 10. 核实方法留痕（可复现）

- 手册取自 ti.com（`curl -sSL https://www.ti.com/lit/ds/symlink/{ads131a02,opa388}.pdf`），**未入库**
- 文字数据：`pdftotext -enc UTF-8 -layout -f <page> -l <page>` 逐页抽取
- 图线数据：`PyMuPDF (fitz) get_drawings()` 抽矢量路径 + 轴刻度标定（Figure 46 轴：x₀=346.20 pt，374.34 pt/单位；y 0 dB=77.75 pt，−20 dB=210.65 pt）
- sinc³ −3 dB：解析式二分求根 + Figure 46 矢量读数双向交叉验证，两者差 0.9%
- S1/S2 时序：Figure 37 矢量顶点抽取，方波高/低各占 t_MOD 一半
