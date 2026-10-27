# 精读笔记 · Szczęsny 2016《Current-Mode FPAA with CMRR Elimination and Low Sensitivity to Mismatch》（Circuits, Systems, and Signal Processing 36:2672–2696）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。

## 出处
- Szczęsny, Szymon, "Current-Mode FPAA with CMRR Elimination and Low Sensitivity to Mismatch," *Circuits, Systems, and Signal Processing*, vol. 36, pp. 2672–2696, 2017（2016-11-04 在线；任务清单称 szczesny2016，bib 年份 2016）。DOI: 10.1007/s00034-016-0449-6。
- PDF：`fulltext/H2-差分CMRR/szczesny2016.pdf`（25 页）。bibkey：`szczesny2016`。
- 主题：开关电流（SI）电流模 FPAA 架构；**"CMRR elimination" = 在平衡电流模单元里加一个求和-相减模块，把共模（concurrent）分量 e 主动消掉**，配合"冗余解网格"编程法压失配。

## 核心命题（原文）
1. **平衡电流模结构中共模分量（e）是精度的首要限制，且靠优化 MOS 参数无法补偿**（p.2675, §2.1）：
   > "as it was discussed in [38] and [33] a common mode rejection ratio (CMRR) [10] may appear in a balanced current-mode structure. Compensation of the concurrent component by optimising the current structure is impossible because its value depends only to a certain extent on choosing MOS transistors parameters. Both of the mentioned phenomena are sources of a nonlinear error e in current signals. Therefore, a CMRR elimination module [41] was added to the circuit in Fig. 1."
   （"调元件参数不能消除共模分量 → 只能加消去模块"——与 P1 的"匹配何时充分/不充分"问题同源，但结论是**加主动结构**而非给出匹配条件。）
2. **消去机制 = 平衡假设下求和节点把信号分量精确归零、提取 2e 再相减**（p.2676, 式 1/3/5/6/7）：
   > "IN1 = −IN2                              (1)"（p.2675）
   > "CM21 [in] = −(IN1 · A + e),  CM22 [in] = −(IN2 · A + e)                (3)"（p.2676）
   > "CM3 [in] = A(IN1 + IN2 ) + 2e = 2e                                       (5)"（p.2676）
   > "Output from CMRR module is obtained by subtracting e from C M2 output signals (Eq. 6)."（p.2676）
   （代数上：因为 IN1+IN2≡0，求和节点把**差模（信号）分量精确消成零**、只留共模误差——与 P1 的 G_DC=H_N−H_P≡0 是对偶操作：P1 要差分网络自己把共模响应消成零，这里是用第三个镜像把共模误差提取后扣除。）
3. **全对称结构给出两路径公共延时（相位一致）**（p.2676）：
   > "Structure of the circuit is fully symmetrical, which minimises the current offset and guarantees a common delay on both paths."
   （"对称 ⇒ 等延时"即 P1 关心的 H_P 与 H_N 相位匹配的电路级实现。）
4. **SI 技术低精度的根源就是 CMRR 与两级失配**（p.2681, §2.2）：
   > "the SI technique is characterised by low data processing precision, which has its source especially in CMRR, unmatching between modules and unmatching between transistors used to build modules which work in the balanced mode."
   > "reconfigurable tracking of modules was designed to ensure the symmetry of the final array."（p.2681）
   （布线层也要保对称——共模性能是**架构全层（单元+布线+版图）**的函数，不是单元件参数。）
5. **失配敏感度靠"冗余解网格"（post-layout 实测参数表）吸收而非精确设计**（p.2682–2683, §3）：
   > "The possibility to generate grid of solutions at any design stage, the schematic stage or the layout stage (with parasitics) and even on the stage of the physical chip. It is a way to achieve higher data processing precision with thanks to taking into account the actual properties of circuits."（p.2682）
   （数字字选择映射实测标定——回避解析失配而不是消去失配；对增量四方法学是"标定/查表"路线的近亲。）
6. **经典镜像失配可达百分之几十，阵列法可全程补偿**（p.2679）：
   > "In the dedicated circuit, the discrepancy between the expected and the actual current mirror multiplier coefficient, assuming a fixed sampling time of circuits with switched currents, may range up to dozens of %. Applying the approach described in Sect. 3 of this article makes it possible to compensate these phenomena in the full range of changes in input signals and maintaining a full symmetry of operation of the RCM module."

## 关键数值（原文）
- 工艺/电源：180 nm CMOS、1.8 V；IPcore 版图 748×1492 µm（p.2681–2682）。
- 标定网格（Table 1, p.2685）：S_MIN=0.02、S_MAX=4.2、平均失配 e_avg=0.0657%、最大 e_MAX=2.24%；B1/B2 各 6 bit。
- 失配规律：N_{S+e} ∼ 1/(B1·B2)（式 21, p.2684）、e ∼ B1·B2（式 22）、e ∼ S（式 23）。
- 10-bit DAC（Table 2, p.2686）：DNL ±0.65 LSB、INL ±0.56 LSB、5 MS/s、2.29 mW、输入电流 0–10 µA、FoM 223.6 fJ/step。
- 椭圆滤波器（p.2687–2689）：三阶梯形原型、阻带 20 dB、通带波纹 0.6 dB；参数离散度 Hooke–Jeeves AVG 0.921 / MAX 1.181，Powell AVG 1.142 / MAX 1.437（Table 3, p.2688）；实现后 SNR=40.42 dB、功耗 22.97 mW、积分器最高钟频 3.6 MHz（p.2689）。
- 图像处理器：2D-DCT 4×4 PSNR=53.05 dB / 1.7 µs（Table 4, p.2693）；RGB→YCrCb PSNR=46.95 dB（同工艺专用电路 49.16 dB；90 nm 43.54 dB）（p.2693）。
- 配置存储：全 IPcore 3056 bit（p.2684）。

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：相关度 **中低**。给出的是**有源电流模单元级**的共模消去：靠拓扑（第三镜像求和+相减）而非元件匹配条件，且只在"平衡输入 IN1=−IN2"的理想假设下精确（式 5 中 2e 的提取以 IN1+IN2≡0 为前提）。**无 s 域分析、无多级无源网络消去条件、无频率响应**——不触及 P1 空缺主张。价值：作为"消去的另一类手段（主动相减 vs 无源匹配）"的对照类；其"参数优化不可能补偿共模分量"（p.2675）可作为 P1 动机引文。
- **P2（Kelvin 结构地板）**：相关度 **无**。无开尔文结构/四线内容。
- **P3（平坦度约束下衰减可达上界）**：相关度 **无**。椭圆滤波器只是实现案例（20 dB 阻带），无平坦度-衰减的解析约束。
- **方法学（增量四 D1–D10）**：相关度 **低**。post-layout 网格标定是"实测参数吸收失配"的查表路线，与增量实验方法论有亲缘但对象不同。
- **killRisk 判断**：**无威胁**。全文无 G_DC(s)=H_N−H_P 形式的消去条件推导；其"elimination"是电路技巧（加法器+减法器），非元件何值使传递恒零的判定定理。与 Hornero 2021（无源差分滤波器失配解析）不构成叠加风险。

## 没读到的
- CMRR 的频率响应完全未分析——"CMRR"在文中只以直流量 e 出现，无 |H_N(jω)−H_P(jω)| 随频率变化的数据或公式。
- 消去模块自身的误差（第三镜像失配、相减精度）未量化——2e 提取的残余误差地板未给数值。
- 引用 [10] 即 giustolisi2000cmrr（CMOS OTA 的 CMRR 频响），本库已有该文，可串联阅读。
- 文中术语"concurrent component"疑为"common-mode component"的非母语用法，引用时建议保留原文并加注。
