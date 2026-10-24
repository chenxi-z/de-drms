# AAF 候选电容封装寄生核查 —— 47nF C0G 0805 vs 1210 等效性 + T1–T4 前提 SRF 覆盖

- **日期**：2026-10-24
- **任务依据**：`hardware/sim/AAF_基于已确认封装的候选参数与Zcode复核_2026-10-24.md` §5(6)（:69）
  「将 S0 的 CG 改成 0805 只用于*模拟相同理想参数的封装方案*；要核实实际供方所选 47nF/0805 的
  SRF、ESL、温度及容差，不得默认 1210 与 0805 在MHz频率下完全等效」；
  顺带核查 10nF/0402、820pF/0402、22nF/0805 C0G 的 SRF 是否覆盖本用途（T1–T4 全 0402 的前提）。
- **来源优先级**（任务书规定）：
  ① `hardware/sim/aaf/r5_bom_check.md` 与 `r5_datasheet_facts.md` 既有事实
  ② 厂商官网/检索（给链接）③ 标 NOT VERIFIED。
  另复用同线既有核查 `hardware/sim/signalchain/fo1_rc_review/bom_footprint_check.md`（LCSC/DigiKey 事实，2026-10-24 快照）。
- **频率口径**：fMOD = **4.096 MHz**（D1 主战场、采样开关频率）、MCLK = **16.384 MHz**（D3 时钟串扰）
  ——`r5_datasheet_facts.md:29-30`（SBAS590E 核实值）。
- **纪律**：本文只做介质/寄生/档位核实；**具体选料、价格、库存、交期归设计者**（任务书 §0 与 AGENTS.md E.10 #6）。
  本轮无 LTspice 仿真项（纯数据核查），区分三层：**厂商官方数据 / 理论估算 / NOT VERIFIED**。

---

## 0. 结论摘要

| 检查项 | 结论 |
|---|---|
| **47nF/0805/C0G 存在性（村田）** | ❌ **无此料号**。村田 GRM21（0805）47nF 只有 U2J / SL / UJ / X7R / B / R；**C0G 47nF 最小 1206**（SimSurfing 官方列表全库扫描，§2） |
| **47nF/0805/C0G 存在性（TDK）** | ❌ 检索无目录料号（C2012C0G1H473J 无任何分销商/官网记录，§2.3） |
| **47nF/0805/C0G 存在性（KEMET）** | ⚠️ C0805C473F3GEC7210（±1%）/ C0805C473G3GEC7210（±2%），**25V** C0G 0805——仅见于 broker 渠道（omo-ic / abc-semi），**无授权分销商现货证据**；LCSC 目录在册的 C0805X473F3GEC 0 库存（既有事实，`bom_footprint_check.md:103-104`） |
| **47nF/1210/C0G 存在性** | 村田 ❌（GRM32 47nF 仅 U2J 250V / X7R 630V）；**TDK C3225C0G1H473J200AA = NRND**（官网详情页明示），LCSC 0 库存（`bom_footprint_check.md:27`）；汽车级对应 **CGA6M2C0G1H473J200AA** 在产 |
| **4.096 MHz 段等效性** | ✅ **等效**。三档（0805/1206/1210）SRF 均 ≥ 4.7×fMOD，ESL 阻抗修正 **<3%**（0.827 Ω → 0.804–0.810 Ω，§4.1） |
| **16.384 MHz 段等效性** | ⚠️ **不得默认等效**。0805 档预期 SRF ≈ 28–29 MHz（同封装同容值实测参照）余量 1.7–1.8×；**1210 档无官方 SRF 数值**（理论 19–21 MHz，余量仅 1.2–1.3×，若实际 ESL >1.47 nH 则 SRF 跌破 MCLK 转感性）——NOT VERIFIED 项 §6 |
| **T1–T4 前提（SRF 覆盖）** | ✅ **全部成立**：10nF/0402 = **84.5 MHz**、820pF/0402 = **310 MHz**、22nF/0805 = **43.1 MHz**（村田官方值，全 C0G 量产，§5） |
| **温度特性** | C0G = 0±30 ppm/℃ **与封装无关**（三档一致）；⚠️ **U2J = 0±750 ppm/℃ 不得冒充 C0G**——ΔT=30℃ 时容值漂 ±2.25%，直接破坏 D8 配对口径与 fc/C9 精度（§3.4） |
| **容差档** | 47nF C0G：±5%（J）各档均有；**±2%（G）仅 1206**（GRM31M5C2A473GA01 / GRM3195C1H473GA05）；±1% 无 C0G 现货（KEMET X 系 0 库存）。r5_bom_check §4.4 要求首级 C "±5% 实测筛选、±2% 优先" → 1206 档满足度最高 |

**一句话**：寄生层面 0805（预期 SRF≈29 MHz）与 1210（理论 19–21 MHz，无官方值）在 4.096 MHz 完全等效、在 16.384 MHz 0805 反而余量更大更安全；**但「S0 的 CG=47nF 换 0805」在 C0G 限定下的真正阻断项不是寄生，而是村田/TDK 均无 47nF/0805/C0G 目录料号**（0805/47nF 只有 U2J/SL/X7R，全部违反介质限定）——电气等效性判定成立的同时，采购可行性不成立（除非接受 KEMET 25V broker 件或放宽容值/介质，均归设计者裁决）。

---

## 1. 数据源与取证方法（全部真实执行）

| # | 数据源 | 取证方式 | 版本/规模 |
|---|---|---|---|
| S1 | **村田 SimSurfing 官方 MLCC 产品列表**（含逐料号 `SRF(MHz)` 列） | `curl -s -A "Mozilla/5.0" -H "Referer: https://ds.murata.co.jp/simsurfing/mlcc.html" https://ds.murata.co.jp/simsurfing_data/data/mlcc.zip` → 解压 `mlcc.csv`，Python csv 解析 | 数据版本 **202508025_01**（def.json version_info），**25,626 行**，覆盖 GRM/GCM/GCH 全系 |
| S2 | TDK 产品详情页（webReader 渲染） | `https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C3225C0G1H473J200AA` | 规格表 + Product Status；curl/WebFetch 直连被 Akamai 拒（403 Access Denied，本轮实测） |
| S3 | 分销商/目录检索 | WebSearch：DigiKey / Mouser / LCSC / broker 命中 | 2026-10-24 |
| S4 | 仓库既有事实 | `r5_bom_check.md`（§3.2 ESL 档位 :120–126、§3.4、§4.4、§7）；`r5_datasheet_facts.md`（fMOD/MCLK）；`fo1_rc_review/bom_footprint_check.md`（§1.4/§1.6/§4.3，LCSC+DigiKey 快照） | — |

> 村田 SRF 列的口径：SimSurfing 官方发布的料号级典型自谐振频率（器件本体、不含 PCB 走线）。
> ESL 由 `L = 1/((2π·SRF)²·C_nom)` 反推——因 SRF 处有效容量 ≤ 标称值，该式给出的 ESL 偏保守（上界），方向安全。

---

## 2. 47nF 档存在性矩阵（村田全库扫描，C0G 限定）

### 2.1 村田：47nF 在各封装×介质的全部量产（production status A/B）件

| 封装 | 料号 | 介质 | 容差 | Vr | **SRF (MHz)** | 状态 |
|---|---|---|---|---|---|---|
| **0805 (GRM21)** | GRM21B7U1H473JA01 | **U2J** | ±5% | 50 | **29.1** | B 量产 |
| 0805 | GRM21B1X1H473JA01 | SL | ±5% | 50 | 29.1 | B 量产 |
| 0805 | GRM21B3U1H473JA01 | UJ | ±5% | 50 | 29.1 | B 量产 |
| 0805 | GRM21BB/BR11H473KA01 等 | X7R/B/R | ±10/20% | 50 | 31.8 | C 停产中 |
| 0805 | **（C0G 47nF：无任何料号）** | — | — | — | — | — |
| **1206 (GRM31/GCM31)** | **GRM31M5C1H473JA01** | **C0G** | ±5% | 50 | **24.5** | B 量产 |
| 1206 | GRM31M5C2A473GA01 | C0G | **±2%** | 100 | **25.5** | B 量产 |
| 1206 | GCM31M5C1H473JA16（车规） | C0G | ±5% | 50 | 24.5 | B 量产 |
| 1206 | GRM3195C1H473JA05 / GA05 | C0G | ±5% / **±2%** | 50 | 26.7 | B 量产 |
| **1210 (GRM32)** | GRM32D7U2E473JW31 | U2J | ±5% | 250 | 26.1 | B 量产 |
| 1210 | GRM32DR72J473KW01 | X7R | ±10% | 630 | 27.5 | B 量产 |
| 1210 | **（C0G 47nF：无任何料号）** | — | — | — | — | — |

来源：S1（村田 mlcc.csv 逐行提取，容值码 473、按尺寸前缀与介质码 5C=C0G / 7U=U2J 筛选）。
**0805 C0G 的容值上界旁证**（同库）：GRM2195C2A683JE01 = **68nF / C0G / 0805 / 100V / ±5%，SRF 27.3 MHz，B 量产**；
GRM2195C2A393JE01 = 39nF C0G 0805（35.4 MHz）。→ 0805 封装 C0G 工艺可达 68nF，**47nF 缺档是产品开档问题，不是物理极限**。

### 2.2 TDK：1210 与 0805

| 封装 | 料号 | 介质 | 容差 | Vr | SRF | 状态 | 来源 |
|---|---|---|---|---|---|---|---|
| 1210 | **C3225C0G1H473J200AA** | C0G(0±30ppm/℃) | ±5% | 50 | **官网仅给典型特性曲线，无单点数值**（§6 NV-1） | **NRND**（官网 Product Status） | S2；DigiKey 970469 / Mouser（`bom_footprint_check.md:27,85`） |
| 1210 | CGA6M2C0G1H473J200AA（车规，官网指定替代） | C0G | ±5% | 50 | 同上 | 在产 | S2（详情页明示 "Please refer to Part No. CGA6M2C0G1H473J200AA for Automotive use"） |
| 0805 | **（C2012C0G1H473J：无目录/分销记录）** | — | — | — | — | — | S3：DigiKey/Mouser/全网检索 0 命中；TDK 0805 C0G 目录 47nF 档不存在 |

### 2.3 KEMET（0805 C0G 47nF 的唯一候选）

| 料号 | 规格 | 渠道证据 | 状态 |
|---|---|---|---|
| C0805C473F3GEC7210 | 0805 / 47nF / **25V C0G ±1%** | 仅 broker（omo-ic.com） | 未验证授权渠道库存 |
| C0805C473G3GEC7210 | 0805 / 47nF / **25V C0G ±2%** | 仅 broker（abc-semi.com） | 同上 |
| C0805X473F3GEC | 0805 / 47nF / NP0 ±1% 25V | LCSC C19554891 **目录在册、0 库存** | `bom_footprint_check.md:103-104` 既有事实 |

来源：S3 + `bom_footprint_check.md` §1.6。本应用节点电压 ≤2.442 V（ADC 基准），25V 档耐压不是问题；
问题是**渠道**与**无官方 SRF/ESL 数据**（§6 NV-2）。

> **村田型号编码澄清**：任务书 §5(6) 写「村田 GRM31/21 系」——村田尺寸码 **GRM21 = 0805（2012 公制）、GRM31 = 1206（3216）、GRM32 = 1210（3225）**。即 GRM31 系是 1206 而非 1210；1210 对应 GRM32（47nF C0G 无档，§2.1）。

---

## 3. SRF / ESL / 温度 / 容差：0805 vs 1206 vs 1210 对比

### 3.1 器件本体 ESL（由村田官方 SRF 反推，S1）

| 器件 | 官方 SRF | 反推 ESL（nH） | 备注 |
|---|---|---|---|
| 47nF/0805（U2J 件，几何同 C0G） | 29.1 MHz | **0.64** | ESL 由端子几何决定，与介质无关——C0G 件若存在，ESL 同量级 |
| 47nF/1206 C0G（±5%） | 24.5 MHz | **0.90** | |
| 47nF/1206 C0G（±2%，100V） | 25.5 MHz | **0.83** | |
| 68nF/0805 C0G（旁证） | 27.3 MHz | 0.50 | 0805 C0G 工艺上限件 |
| 22nF/0805 C0G | 43.1 MHz | 0.62 | 与 47nF/0805 的 0.64 交叉印证 0805 ≈0.6 nH |
| 1210 C0G（TDK，无官方 SRF） | — | **无数据**（理论档 1.2–1.5 nH，`r5_bom_check.md:120-126` + `bom_footprint_check.md:194`） | NV-1 |

**与既有档位的关系**：村田器件本体 ESL（0402 0.32–0.36 / 0805 0.50–0.64 / 1206 0.83–0.90 nH）全部**低于**
`r5_bom_check.md` §3.2 的保守档（0402 0.4 / 0805 0.9–1.2 / 1206 1.2 nH）——r5 档位含焊盘/走线安装寄生余量，
两者口径不同、不矛盾；实际器件余量比 r5 估算更好。

### 3.2 4.096 MHz 与 16.384 MHz 的实际阻抗（含 ESL）

| 器件 | \|Z\|@4.096 MHz（理想 → 含 ESL） | ESL 修正 | \|Z\|@16.384 MHz（理想 → 含 ESL） | MCLK/SRF |
|---|---|---|---|---|
| 47nF/0805（ESL 0.64 nH） | 0.827 → **0.810 Ω** | **−2.0%** | 0.207 → **0.141 Ω** | 0.56（容性区） |
| 47nF/1206（ESL 0.90 nH） | 0.827 → **0.804 Ω** | **−2.8%** | 0.207 → **0.114 Ω** | 0.67（容性区） |
| 47nF/1210（ESL 1.2–1.5 nH，理论） | 0.827 → ~0.798 Ω | ~−3.5% | 0.207 → **0.083–0.053 Ω** | 0.78–0.86（贴近 SRF） |

（Python 计算，脚本与输出见 §7；理想 = 1/ωC，含 ESL = \|ωL − 1/ωC\|，未含 ESR——C0G 件 ESR 数十 mΩ 量级，对此处欧姆级/百毫欧级阻抗为二阶项。）

### 3.3 等效性判定

- **4.096 MHz（fMOD）**：三档 SRF 均 ≥ 4.7×fMOD，工作点深度容性，ESL 修正 <3% →
  **0805 / 1206 / 1210 电气等效**（判定成立，数据层：0805/1206 为厂商官方值，1210 为理论估算层）。
- **16.384 MHz（MCLK，D3）**：
  - **0805 档**（以同封装 47nF U2J 件 29.1 MHz + 68nF C0G 件 27.3 MHz 双重参照，预期 SRF≈28–29 MHz）：
    MCLK 仍在容性区（0.56×SRF），对地阻抗 0.141 Ω，比理想电容低 32%（旁路更强，对 D3 有利方向）；
    **余量 1.7–1.8×** → 等效性成立且优于 1210。
  - **1210 档**：无官方 SRF。理论 ESL 1.2–1.5 nH → SRF 19–21 MHz，**MCLK 余量仅 1.2–1.3×**；
    若实际 ESL >1.47 nH（SRF <16.384 MHz）即转入感性区、对地阻抗回升，D3 恶化；且 ESL≈1.5 nH 附近
    存在 r5_bom_check §4.3-2 实测过的 **D3 窄带峰**（不可作设计依据）。
    → **1210 档在 16.384 MHz 的行为不得默认与 0805 等效**（结论：NOT VERIFIED，需 TDK 曲线取数或样机实测回填）。
  - 方向性提示（非判定依据）：越接近 SRF，容性支路对地阻抗越低、对时钟串扰的旁路反而越强；
    1210 的风险不是"等效性差"，而是**余量窄 + 无官方数据**。

### 3.4 温度特性与容差

| 项 | 0805 | 1206 | 1210（TDK） |
|---|---|---|---|
| C0G 温度系数 | 0±30 ppm/℃（同介质，与封装无关；工作温度 −55~125℃） | 同左 | 同左（官网页明示 C0G(0±30ppm/°C)，S2） |
| 47nF C0G 容差 | N/A（无料号；同封装 22nF 有 ±5/±2/±1% 档） | **±5% 与 ±2% 均有** | ±5%（J） |
| ⚠️ 介质陷阱 | 0805/47nF 现货件全是 U2J/SL/X7R：**U2J = 0±750 ppm/℃**（EIA Class I 温度码；村田 tcc 字段=U2J）、SL = +350~−1000 ppm/℃ | — | — |

**U2J 冒充 C0G 的定量否决**：ΔT=30℃ 时 U2J 容值漂移 ±2.25%——大于 C0G ±5% 容差带的三分之一、
远超 r5_bom_check §5.7 温度跟踪判据（同批同封装漂移 <0.01%）、直接破坏 D8 的 R·C 乘积配对与
C9/D4 的 fc 精度。**0805/47nF 的 U2J 件不构成 C0G 替代**，S0 的 CG 不得用其落地。

---

## 4. ② T1–T4 前提容值的 SRF 覆盖（全 0402 的前提核查）

| 用途 | 容值/封装 | 村田料号（全 C0G 量产） | 官方 SRF | vs fMOD 4.096 MHz | vs MCLK 16.384 MHz |
|---|---|---|---|---|---|
| T1–T4 CG1/CG2 | **10nF / 0402** | GRM1555C1H103JE01（50V ±5%；25V/35V 同 SRF） | **84.5 MHz** | 20.6× | **5.2×** ✅ |
| S0/S1/T1–T4 Cd | **820pF / 0402** | GRM1555C1H821JA01（50V ±5%）；±2% 档 GRM1555C2A821GE01 | **310 MHz** | 75.7× | 18.9× ✅ |
| S1 CG | **22nF / 0805** | GRM21B5C1H223JA01（50V ±5%）；±2% GRM2165C1H223GA01（49.1 MHz）；LCSC 现货 ±1% GCM21B5C1H223FA16L（`bom_footprint_check.md:23`） | **43.1 MHz** | 10.5× | **2.6×** ✅ |
| （对照）0402/22nF C0G | 村田无档 | — | — | 与任务书 §1「22nF 自 0805 起」一致 ✅ | — |

**判定：T1–T4 的全 0402 前提（10nF、820pF）与 S1 的 0805 前提（22nF）在 SRF 覆盖上全部成立**——
所有电容在 fMOD 与 MCLK 均深度容性（ESL 修正：10nF@MCLK −3.7%、820pF@MCLK −0.3%、22nF@MCLK −14.5%，
后者的 −14.5% 是对地阻抗下降、旁路增强方向）。
最小余量 = 22nF/0805 vs MCLK 2.6×，安全；10nF/0402 反而是最宽松位（84.5 MHz）。

---

## 5. 冲突记录（任务书/仓库 vs 厂商目录事实）

| # | 表述 | 事实 | 处理 |
|---|---|---|---|
| K-1 | 任务书 §1「47 nF：**0805 及以上**，无 0603」（设计者已确认可找到）与「所有候选电容继续限定 **C0G/NP0**」（§1 末） | 两者在村田/TDK 目录内**不可兼得**：0805/47nF 只有 U2J/SL/X7R（§2.1/§2.2）；C0G 47nF 最小 1206。唯一 0805 C0G = KEMET 25V broker 件（§2.3） | 按优先级处理：C0G 限定源自 r5 规格 C4（`r5_bom_check.md:82`，X7R 类会击穿 D7/D8）不放宽；**S0 的 0805 化当前不可采购落地**，是否改用 1206（村田 GRM31M5C1H473JA01L，LCSC 现货 51,375 只，`bom_footprint_check.md:28`）或 0805 C0G 68nF 换容值，归设计者裁决 |
| K-2 | 旧基线「47nF/**1210**」（S0 原封装） | 该档全市场唯一 C0G 目录件 TDK C3225C0G1H473J200AA 已 **NRND** 且 LCSC 0 库存（§2.2） | 1210 档自身供货劣化中；新设计若保留 47nF，1206（村田量产+现货）优于 1210（NRND+预订）——与本轮寄生结论（1206 SRF 24.5 MHz > 1210 理论 19–21 MHz）方向一致 |
| K-3 | r5_bom_check §3.2 封装 ESL 档位（0805 ≈0.9–1.2 nH） | 村田器件本体 ESL 实测反推 0805 ≈0.50–0.64 nH（§3.1） | 非冲突：r5 档位含安装寄生为保守口径；本轮在等效性计算中用村田器件值，工程上两者结论同向 |

---

## 6. NOT VERIFIED 清单（不编造，缺什么写什么）

| # | 项 | 缺什么 |
|---|---|---|
| NV-1 | **TDK 1210（C3225C0G1H473J200AA / CGA6M2C0G1H473J200AA）官方 SRF/ESL 数值** | product.tdk.com 直连被 Akamai 拒（curl/WebFetch 403，本轮实测）；webReader 仅取到规格表，典型特性曲线的数据点/CSV 接口未能取得。1210 SRF 现只有**理论估算层 19–21 MHz**（r5 ESL 档 1.2–1.5 nH）。样机阶段按 r5_bom_check §3.4 用网络分析仪实测回填 |
| NV-2 | **KEMET 0805/47nF/C0G（C0805C473F3GEC7210 等）的 SRF/ESL 与授权渠道可购性** | K-SIM 未访问；broker（omo-ic/abc-semi）信息非授权渠道证据。本文 0805/47nF 的 SRF≈28–29 MHz 是**同封装同容值 U2J 件 + 同封装 C0G 68nF 件的几何参照值**，非该料号实测 |
| NV-3 | **1210 档在 16.384 MHz 的实际对地阻抗** | 依赖 NV-1；ESL 若 >1.47 nH 则 SRF<MCLK、转感性 |
| NV-4 | 村田列表 SRF 的逐料号测试条件（夹具、参考面） | 列表未随行给出；口径为 SimSurfing 官方典型值（含器件本体、不含 PCB 走线——走线 ≈1 nH/mm 仍需按 r5_bom_check §3.4 控制接地回路 <3 mm + 多过孔） |
| NV-5 | LTspice 层面的 0805/1210 分档 D1/D3 复跑 | 本任务为数据核查（§5(6) 范围）；分档仿眔回 `r5_bom_esl_esr` 口径另跑（r5_bom_check §4 已有 ESL 0–2 nH 扫描框架可复用） |

---

## 7. 证据与复现路径

**本机既有事实（优先级①）**
- `hardware/sim/aaf/r5_bom_check.md`：§3.2（:120–126 封装 ESL 档）、§3.3/§3.4（SRF 判据与走线要求）、§4.2–4.3（ESL/ESR 对 D1/D3 实测敏感性、1.5 nH 窄峰）、§4.4（C 容差 ±5%/±2% 要求）、§7（料号级 ESL/SRF 未核——本轮即补此洞）
- `hardware/sim/aaf/r5_datasheet_facts.md`：:29–30（fMOD=4.096 MHz、MCLK=16.384 MHz，SBAS590E）
- `hardware/sim/signalchain/fo1_rc_review/bom_footprint_check.md`：§0/:27（TDK 1210 LCSC 0 库存+DigiKey/Mouser 有）、:28（村田 1206 现货 51,375）、:82–85（1210 尺寸/焊盘/理论 SRF 19–21 MHz）、:103–104（KEMET C0805X473F3GEC 0 库存）、:191–206（§4.3 SRF 理论估算口径）
- `hardware/sim/AAF_基于已确认封装的候选参数与Zcode复核_2026-10-24.md`：§1（封装×介质限定）、§2（S0/S1/T1–T4 参数）、§5(6)（:69 本任务）

**本轮真实执行的取证（优先级②）**
1. 村田列表下载：`curl -A "Mozilla/5.0" -H "Referer: https://ds.murata.co.jp/simsurfing/mlcc.html" https://ds.murata.co.jp/simsurfing_data/data/mlcc.zip`
   （端点路径由 SimSurfing 前端 JS `muratalib/js/product/simsurfing_mlcc_func.min.js` 逆向确认：`DataPath("../simsurfing_data")+"/data/"+FileName("mlcc")+ZipFormat(".zip")`）；
   解压 `mlcc.csv` 6,862,117 字节、25,626 行，数据版本 202508025_01（`https://ds.murata.co.jp/simsurfing/data/json/def.json`）。
   逐行筛选容值码 473/223/103/821 × 尺寸前缀 × 介质码，提取 `SRF(MHz)`、`tolerance`、`tempchar`、`tcc`、`rvol`、`production_status` 列——§2/§3/§4 全表即该原始数据。
2. ESL 反推与频点阻抗：Python（`math`），公式与全部输出见 §3.1/§3.2（无手算环节）。
3. TDK 详情页：webReader 渲染 `https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C3225C0G1H473J200AA`
   （取到：C0G(0±30ppm/°C)、±5%、50V、Q≥1000、Product Status=Production (NRND)、汽车替代 CGA6M2C0G1H473J200AA）；
   直连尝试 `curl`/WebFetch 均被 Akamai `Access Denied`（Reference #18.26a93417，留痕）。
4. 存在性检索（WebSearch，2026-10-24）：
   - 村田 GRM21B5C1H473JA01（0805/47nF/C0G/50V 猜测料号）→ simserve 料号库与 mlcc.csv 均**无此档**（同容值 0805 量产件全介质见 §2.1）；
   - TDK C2012C0G1H473J → DigiKey/Mouser 无记录（0805 C0G 47nF 目录不存在）；
   - KEMET C0805C473* → 仅 broker 命中（omo-ic.com / abc-semi.com，25V C0G ±1%/±2%）；
   - TDK C3225C0G1H473J200AA → DigiKey https://www.digikey.com/en/products/detail/tdk/C3225C0G1H473J200AA/970469（1210 C0G ±5% 50V）。
   - 村田产品线入口：https://www.murata.com/en-us/products/capacitor/ceramiccapacitor/overview/lineup/smd/grm ；
     SimSurfing：https://ds.murata.co.jp/simsurfing/mlcc.html

**本轮未做**：任何 LTspice 仿真（NV-5）；LCSC 实时库存复核（沿用 bom_footprint_check.md 2026-10-24 01:20 CST 快照，下单前须复核——E.10 #6 归用户）。
