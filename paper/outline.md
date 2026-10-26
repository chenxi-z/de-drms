# P1 论文方向与大纲 v4（2026-10-26 · 正文精读+实验数据融合后的定稿方向）

> 取代 v3（v3 的 IMRaD 槽位结构保留，框架层升级为"四条边界"）。
> 依据：29 篇正文精读（15 份笔记）+ 本机全部实验数据（fo1/aaf_pkg 两轮，T00 锚定 LTspice + MC + sinc³ + EDA 实画）。
> 纪律：四条边界各配"正文谱系证据 + 本机实验验证"双柱，缺一不立。

---

## 〇·前、方法论定位（诚实声明）

"画性能包络/可行域"**不是本文发明**——数学工具是 Bode-Fano 匹配界（Bode 1945 → Fano 1950 → Nie 2016 多端口），
方法论是模拟 EDA 的设计空间探索/可行域映射（DATE 2010 等活跃领域）。
**本文的新贡献是把这套古典工具应用于一个从未被映射的类**（差分抗混叠 RC 网络 @ SC-ΣΔ 输入端），
并给出四条边界中边界Ⅰ/Ⅱ/Ⅳ 的无先例结果；边界Ⅲ 是 Bode-Fano 精神在约束对（D4∧D1）下的专项化。

## 〇、核心构思：性能包络的四条边界

**论文的对象不是"我们的滤波器"，也不是"选型方法"，而是——**

> **开关电容 ΣΔ 输入端无源差分 RC 网络的完整性能包络**

包络由四条边界围成，每条边界回答一个工程必问：

| 边界 | 工程问题 | 回答 | 正文谱系证据 | 本机实验验证 |
|---|---|---|---|---|
| **Ⅰ 匹配边界** | "元件选好能到多好？" | 双通道退化上限：失配通道有**系数匹配消去条件**（AC 版 Thomas 定理），Zcm 载荷通道**匹配不救** | Thomas 1948 eq(11) DC 祖先（a/b=A/B ⇒ 误差项恒零，与 L 无关，印刷 p.17）；Whitlock 2004 p.4 Zcm 载荷机理 | 配对矩阵：未配对 33.7 / 逐级 τ 51 / **整线同偏 90.5 dB**（t06 CSV） |
| **Ⅱ 拓扑边界** | "换元件/换配法也过不去的墙在哪？" | Kelvin 无源负端 ⇒ H_N/H_P 函数类不同 ⇒ **共模地板 ≈56 dB，与配对无关** | 4TP/自动平衡电桥用结构定义或主动置零"绕开"而非"匹配掉"（Cutkosky1970 p.65-66；Keysight §2.3.2 "converges to exactly zero"） | 六案地板恒定 56.08–56.31 dB（t02/t06 CSV），含配对极值角验证 |
| **Ⅲ 物理边界** | "加级数总能过吧？" | **不能**：平坦度 D4≤0.5dB 钉死 fc → N≤2 无源衰减上界 ~76 dB < 80 | **Bode-Fano 匹配界谱系**（fano1950matching 积分上界的数学同型；kerr1993limits 的'极限+实用'双柱结构同型；nie2016matching 多端口推广）；an699 配方表无约束对论证 | 实测 62–64 dB 贴界（t01 CSV），负荷损耗 ~12 dB 可解析 |
| **Ⅳ 实践边界** | "到底怎么选？" | 门槛化多目标裁决 + **真实 PCB 占地实画**（非本体面积） | sboa114 噪声预算路线（正文证实无 CMRR/失配内容） | 六案 Pareto（layout_area_report）：二阶全 0402 反比一阶含 0805 **小 16.5%** |

**四条边界合在一起 = 该类网络的完整可行域。** 任何设计决策都在这个包络内移动；论文的贡献是
第一次画出包络的每条边、证明出来、并用实验标定出来。六方案不是"我们的候选"，是"沿包络走一圈"的路标。

---

## 一、必要性链（"为什么不逃走"——全部有页码的正文引文）

| 逃生门 | 正文代价引文 | 出处 |
|---|---|---|
| 反相两次测量 | "Data accusation of 1 Hz signal takes up to 7 seconds to complete, **14 seconds**."（×2 时间 + 两测间须平稳） | Ji 2016 p.76-77 |
| 电桥/自动平衡 | 零值检波+反馈+量程电阻整套有源架构；"the unbalance current **converges to exactly zero**" | Keysight §2.3.2 |
| IC 自举/激光修调 | "0.005% matching → ~90 dB CMRR"——"Discrete implementations **practically impossible**" | Whitlock 2004 p.5 |
| CT-ΣΔ 换芯片 | AIN 无强制滤波（**勘误确认**），但残余=Rs/6.25kΩ 分压温漂；高阻源仍需缓冲 | AD4134 p.6/p.37；CTSD tut. p.19/22 |

→ **测量窗口内不可切换 + 成本敏感 + 高阻源**的交集场景（本设备即全中）无门可逃。

---

## 二、理论核心（写作第一步：sympy 推导，`paper/derivations/`）

- **定理 1（匹配消去，P1-a）**：N 阶无源差分 RC 梯形 G_DC(s)=H_N(s)−H_P(s)。
  N=1：G_DC≡0 ⟺ τ 匹配（退化为 Thomas 1948 的 AC 版）；N≥2：系数向量含 R1·C2 交叉项 ⟹
  逐级 τ 不充分（51 dB 实证）；**整线同偏**⟹系数全等⟹G_DC≡0（90.5 dB 实证）。
- **定理 2（Zcm 载荷，P1-b）**：对地 C_G 即使完美匹配仍降 Zcm(f)、放大源失配敏感度（Whitlock p.4）；
  本机量化：T2 的 C_G=10nF 在 16 kHz 的 Zcm 值 vs 无穷 Zcm 基准的 CMRR 差（t02 CSV 可提取）。
- **定理 3（结构地板，P2）**：P 端缓冲 + N 端无源直连 ⇒ H_P 与 H_N 结构不同类（阶数/极点数不同）
  ⇒ 任何元件取值不能 G_DC≡0；地板量级 ≈|H_N/H_P| 最坏频点比值。六案 56.08–56.31 dB 恒定。
- **定理 4（可达上界，P3）**：|H(j2πf_b)|≥1−δ ⇒ f_c 上界 ⟹ N 阶在 f_MOD 衰减 ≤ 20N·log₁₀(f_MOD/f_c) −
  负荷损耗。N=2, δ=0.5dB, f_b=16kHz, f_MOD=4.096MHz → ≈76 dB < 80（实测 62–64，负荷损耗 ~12 dB）。

---

## 三、IMRaD 结构（v3 槽位不变，框架替换为包络叙事）

- **Introduction**：八谱系"四名字九十年" → 各族解到够用 → 宽带精确消去需求的交集新生 → 四条边界贡献预告。
- **Theoretical framework**：定理 1–4（sympy 推导；附录代数细节）。
- **Validation methodology**：V1–V5（v3 不变）。
- **Case study & results**：六网络 = "沿包络走一圈"——R3 配对矩阵走边界Ⅰ（核心图 Fig.5）；
  R4 Kelvin 恒定走边界Ⅱ；R6 贴界曲线走边界Ⅲ（Fig.4 叠 Bode 界线）；R5 占地反转走边界Ⅳ。
- **Discussion**：D1 对 Hornero 建设性接续；D2 负端无源直连族=P2 普适律；D3 四扇门的正文代价表；
  D4 局限如实四条。

---

## 四、题名

1. *Limits of Passive Differential Anti-Aliasing Networks at SC-ΣΔ Inputs: Cancellation Conditions, Structural Floors, and a Reachability Bound*（推荐——题名即三定理）
2. *Four Boundaries of Passive Differential Anti-Aliasing at Switched-Capacitor ΣΔ Converter Inputs*（备选——最短）
3. *When Matching Cannot Save You: The Performance Envelope of Passive Differential RC Front Ends for Ratiometric ΣΔ Measurement*（口语备选）

---

## 五、论文之外的方向判断

1. **设备已锁定 T2**（V1.4 入库）：接受代价=整线同 m 配对 + D6a 正交口径超线 + D1/D3 靠 PCB+首板关闭；
2. **写作第一步不是英文 Methods——是 sympy 推导定理 1–4**（`paper/derivations/`）：论文新颖性全在定理层；
3. P2 仪器论文等首板实测；文献底盘已够（230 条+Zotero 九轴+Obsidian 谱系库）。
