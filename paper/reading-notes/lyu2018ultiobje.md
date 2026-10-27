# 精读笔记 · Lyu 2018《Multi-objective Bayesian Optimization for Analog/RF Circuit Synthesis》（DAC 2018）

> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。

## 出处
- Lyu, Wenlong; Yang, Fan; Yan, Changhao; Zhou, Dian; Zeng, Xuan. "Multi-objective Bayesian Optimization for Analog/RF Circuit Synthesis." *Proceedings of DAC '18: The 55th Annual Design Automation Conference*, 2018, San Francisco, pp. 1–6. DOI: 10.1145/3195970.3196078（ACM 版）；bib 中另有 IEEE 版 DOI 10.1109/dac.2018.8465872（同文双录）。
- PDF：`/home/anning/Documents/Obsidian Vault/20-硬件工程/10-项目设计/p1-文献谱系/fulltext/H8-灵敏度与统计电路设计/lyu2018ultiobje.pdf`（6 页；下文页码 = PDF 物理页 1–6）。

## 核心命题（原文）
1. **多目标优化的立场：不再找单点最优，而是均匀逼近 Pareto 前沿**（p.1）：> "Instead of optimizing a single objective and seeking for the single best design, multi-objective optimization methods try to find a set of uniformly distributed Pareto-optimal design to approximate the Pareto Front(PF) [15], which represents the most ambitious trade-off of the conflicting performances."（多目标框架的总纲：PF = 相互冲突性能间的"最进取权衡"集合，交给设计者二次决策。）
2. **加权标量化路线的固有缺陷**（p.1）：> "The problem with this approach is that it is difficult to assign appropriate weights for the performances. Wrong weights might lead to inappropriate designs."（点出单目标加权合成的要害——与 P3 若用加权法处理"平坦度 vs 衰减"时的方法学警示直接相关。）
3. **支配关系的标准定义**（p.2）：> "a design x 1 is said to dominate x 2 , if ∀i ∈ {1 . . . m}, f i (x 1 ) ≤ f i (x 2 ) and ∃j ∈ {1 . . . m}, such that f j (x 1 ) < f j (x 2 ). A design is said to be Pareto-optimal if no design in the whole design space dominates it."（教科书级 Pareto 支配/最优定义，可作 P1 方法学章节的定义引用源之一。）
4. **每目标一个 LCB 采集函数，再对采集函数族做多目标优化**（p.2–3）：> "In this work, the single-objective Bayesian optimization is extended to handle multiobjective optimization, the lower confidence bound (LCB) function is chosen as the acquisition function for each objective."（p.2）> "LCB i (x) = µ i (x) − κ i σ i (x),"（p.3，式前文；κ=3。关键机制：GP 代理模型给每个目标的均值与不确定度，LCB 把"利用/探索"合成进逐目标的采集函数。）
5. **LCB 前沿与真实前沿的关系（收敛论证）**（p.3）：> "If the GP models are accurate, the Pareto front of the LCB functions would be same with the Pareto front of the problem (1), if the GP models are still inaccurate, the Pareto-optimal points of the LCB functions will reside in areas where the uncertainties are high."（代理模型准确时 LCB 前沿=真前沿；不准时自动偏往高不确定区——这是该框架的收敛直觉，无严格证明，p.2 引 [4] 给单目标 LCB 的指数遗憾界：> "it is proved that under some regularity assumptions, the LCB-based Bayesian optimization has exponentially vanishing instantaneous regret."）
6. **corner 最坏情形作为优化目标（非统计方法）**（p.5）：> "We consider five process corners (TT/FF/SS/SF/FS) and three temperatures (25°C/-40°C/125°C). A total of 15 simulations are required for one design. The worst performances across all corners are to be optimized."（与 graeb2007areto 的"线性化 worst-case"不同，本文用离散 corner 枚举取最坏值——H8 轴内两条 worst-case 路线的对照样本。）

## 关键数值（原文）
- LCB 参数（p.2）：> "We set κ = 3 in this work."
- ZDT1/ZDT2 基准（p.4）：MOBO 上限 300 次评估 vs GPMOOG 1800 / MOEA/D 3600；> "it can achieve very good approximations to the true Pareto fronts of ZDT1 and ZDT2 functions within only 300 evaluations. Although the GPMOOG and MOEA/D also achieved good results with 1800 and 3600 evaluations, they failed to generate acceptable Pareto fronts within 600 evaluations."
- 三级运放（SMIC 55nm，24 个设计变量，p.5）：MOBO 每轮 400 次仿真（含 80 个初始随机采样）vs 对照组 800 次；最优值 Max Gain 98.93 dB / Max UGF 4.03 MHz / Max PM 131.15°（GPMOOG 86.76 dB/2.04 MHz/130.57°；MOEA/D 83.38 dB/1.93 MHz/132.62°）；hypervolume 差 p 值 0.0016（vs GPMOOG）/0.0001（vs MOEA/D）。
- 60 GHz 变压器（TSMC 65nm，4 变量，ADS Momentum EM 仿真，p.5）：MOBO 300 次仿真（含 40 初始采样）vs 对照组 350 次；Max PTE 84.34%（GPMOOG 82.33%、MOEA/D 82.29%）、Min Area 64.27 µm²；p 值 2.43e-12 / 5.70e-12。
- 2.5 GHz 功放（TSMC 65nm，211 个相同 cell 阵列，5 变量，p.6）：MOBO 300 次仿真（含 40 初始采样）vs 对照组 500 次；Max Eff 65.12% / Min THD 5.90 dB / Max Pout 26.55 dBm；p 值 8.01e-11 / 3.78e-9。
- 改进 NSGA-II 三处改动（p.3–4）：遗传操作换差分进化（DE）；crowding distance 求和改求积（> "It can be viewed as the crowding volume rather than crowding distance."，尺度无关免归一化）；已仿真数据以"零不确定度 GP 预测"身份充当 > "\"elitist anchor\"" 参与进化。
- 评价指标：hypervolume 差 I−H = HV(P*) − HV(P)（p.4，式(9)），参考前沿由全部算法采样合并提取；显著性判据 > "Generally, p < 0.05 or p < 0.005 are recognized as a significance level."（p.4）。

## 对 P1/P2/P3 的对照
- **P1（消去条件 G_DC=H_N−H_P≡0）**：无。全文是晶体管级尺寸综合（运放/变压器/功放），不涉无源网络传递函数恒等式、失配消去或差分结构元件条件；GP 黑箱代理路线与 P1 的解析元件级推导完全不同层。
- **P2（Kelvin 结构地板 ≈56dB）**：无。不涉共模抑制、接地结构或 CMRR。
- **P3（平坦度约束衰减可达上界 = Bode-Fano 亲缘）**：中。它正面回答了本批重点问题①：**触及"多目标 Pareto 框架"本身（支配关系、PF、hypervolume、均匀分布），但应用域是晶体管尺寸综合，不是滤波器/无源网络频响设计**——全文无一例滤波器算例，不做频域响应平坦度-衰减权衡，不触 Bode-Fano/匹配界。对 P3 只能作"多目标权衡框架的现代综述级引用"（p.1 明确列出 GP+MOEA/D、标量化 [21=Stehr/Graeb NBI]、层次化 PF 复用 [6=Eeckelaert] 等谱系），不能作为"滤波器多目标优化已有先例"的内容性支撑。
- **方法学（D1–D10 门槛化）**：中。若 P1 方法学需要"昂贵仿真下的多目标探索"工具箱，本文是 2018 年代表性引用（MOBO/GP/LCB）；但注意其权衡是启发式逼近（代理模型+进化），P1 的 D1–D10 若主打"解析门槛+逐条判据"，引用时应划清"黑箱搜索 vs 解析判据"的方法层级。
- **killRisk**：无威胁。四条主张均不与其重叠；唯一须划界处：若 P1 方法学章节出现"将多目标 Pareto 引入无源抗混叠网络设计"的首创性表述，须引用本文（及 graeb2007areto）作为 Pareto 框架既有文献，把首创性收窄到"无源差分网络 + 消去条件门槛"的组合上。

## 没读到的
- bib 中 lyu2018ultiobje2 与本文同题同作者同页码（DOI 10.1145/3195970.3196078 vs 10.1109/dac.2018.8465872），疑为同一论文的 ACM/IEEE 双录条目——待读 lyu2018ultiobje2.pdf 后在另一笔记中核实。
- 图 3/6 中 Pareto 前沿散点的逐点数值未从图上提取（正文只给表 1–3 的统计量与最优值）。
- 参考文献 [4]（De Freitas et al. 2012，LCB 遗憾界证明）与 [21]（Stehr/Graeb 2007 NBI+Fourier–Motzkin，被本文列为标量化代表）未读原文；后者与 graeb 系工作有谱系关联，如需深挖 Pareto 射线法可补读。
- 收敛性只有单目标遗憾界引用，多目标 MOBO 本身无理论收敛证明（正文未声称）。
