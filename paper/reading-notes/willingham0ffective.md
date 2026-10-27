# 精读笔记 · Willingham 1990《Effective Clock-Feedthrough Reduction in Switched Capacitor Circuits》（ISCAS 1990, pp.2821-2824）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> H5 轴视角：**本文是"馈通对消条件"与"抑制建立时间"的正源文献**——① 差分/准差分对消成立的五要素对称条件（结构/版图/时钟波形/开关端电压/小信号阻抗）；② 开关端阻抗决定沟道电荷分配比例、低阻驱动使电荷注入对时钟斜率不敏感；③ 反馈式抑制的"抑制倍数 vs 环路带宽"定量绑定与恢复时间；④ **毛刺（glitch）与采样值（被离散时间电路忽略的瞬态）的区分**——对 P1 D9 踢回口径的成立性判断直接可用。

## 出处
- Scott D. Willingham, Kenneth W. Martin（UCLA Integrated Circuits & Systems Laboratory），"Effective Clock-Feedthrough Reduction in Switched Capacitor Circuits", *Proc. IEEE ISCAS 1990*, pp. 2821–2824. DOI 10.1109/iscas.1990.112597。
- bibkey: `willingham0ffective`；全文 PDF：`fulltext/H5-kickback/willingham0ffective.pdf`（4 页，会议页 2821–2824，下引页码=会议页；扫描件 OCR，µ 常被误读为 p、时钟相符号损，均已标注）。
- 主题：SC 电路时钟馈通抑制三路线（全差分对消、准差分对消、负反馈抑制）的实现条件与多通道 D/A 示例（3 µm MOSIS 工艺，HSpice 全晶体管级仿真验证）。

## 核心命题（原文）
1. **差分/准差分馈通对消的成立条件 = 五要素严格对称（对消条件的正源表述）**（p.2821）：
   > "Differential and quasi-differential cancellation techniques rely on common-mode symmetry for proper feedthrough cancellation. Critical circuit nodes must have exactly symmetrical circuit structure, layout, clock waveforms, switch terminal voltages, and small-signal impedances."（对消不是接成差分就自动成立，须结构/版图/时钟波形/开关端电压/小信号阻抗五者全对称——"对消条件"领域最常被引的条件句。）
2. **开关端阻抗决定沟道电荷的分配比例；对消要求对称开关对的端阻抗尽量匹配**（p.2822）：
   > "the impedance seen at each switch terminal influences the proportion of conduction channel charge that flows into each terminal [10, 11]. Therefore, for maximum feedthrough cancellation, the terminal impedances of each symmetrical switch pair must be as well matched as possible. For this reason, it is advantageous to have a low impedance at node A."（电荷注入去向由两端阻抗比分——这决定"踢回有多少进入源侧"的机理框架。）
3. **低阻抗源使电荷注入对时钟斜率不敏感**（p.2822）：
   > "Additionally, low impedance sources tend to make charge injection less sensitive to variations in the slope of the clocking signals [10, 11]."（P1 若主张"低阻驱动/缓冲下踢回可控"，此句为直接文献支撑。）
4. **关键开关对（S10/S11）补偿的匹配要求**（p.2822）：
   > "The crucial clock-feedthrough in this circuit is due to switch S10 and it must be compensated by the feedthrough of switch S11. These switches are identical in size, have identical clocking and terminal voltages, and their feedthrough appears across identically sized capacitors."（对消元件级实现：同尺寸、同时钟、同端电压、同尺寸电容。）
5. **负反馈抑制：反馈在保持期间纠正注入电荷；抑制倍数与带宽缩减是同一因子，恢复时间可由电容比优化**（p.2822）：
   > "When S8 turns off, it injects a small charge into node B. However, negative feedback is still maintained through SH and Cx. This feedback acts to correct the output voltage, thus suppressing the clock-feedthrough." —— 以及 "The clock-feedthrough of this circuit is also multiplied by the factor Cx·(1/CA + 1/CB), which is chosen to be much less than unity. Hence, the amount of feedthrough suppression required and the bandwidth reduction that must be tolerated are identical. By choosing CB >> CA, the amplitude of the initial feedthrough (upon opening S8) can be minimized so that the circuit's recovery time is small despite its reduced bandwidth."（H5"建立"轴核心权衡：抑制 N 倍 ⇔ 带宽降 N 倍；初值小则恢复时间短——"半周期内回稳"类指标的机理依据。）
6. **抑制比 10 所需的建立预算 = 主时钟半周期**（p.2823）：
   > "For a feedthrough suppression ratio of 10, a period between φ8 and φ'[OCR损：原文字符为相符号] equal to one half-period of the main clocks is sufficient for full suppression."（把"抑制倍数"与"时间预算"挂钩的显式门槛：10× 抑制 ↔ 半周期。可与 P1 D9"122 ns（半周期）内回稳 0.01%"同型对照——注意本文口径是 10×（20 dB），远松于 0.01%（80 dB）。）
7. **毛刺≠误差：电荷经非零阻抗开关转移期间的电压毛刺不消除，但可被下游离散时间电路忽略**（p.2824）：
   > "It should be kept in mind that the techniques described above do not eliminate voltage glitches during times of charge transfer through switches with non-zero impedance. However, the techniques are quite effective when the circuit output is further processed by discrete-time circuitry that ignores the glitches."（关键口径区分：**观察点若在离散时间域，瞬态毛刺可忽略；若在连续时间模拟域（如 P1 被测源/模拟链），毛刺即真实扰动**——这界定了 D9 踢回主张的适用边界，写 P1 时应主动引用此区分以免被反方以"毛刺无害论"攻击。）

## 关键数值（原文）
- 抑制效果（HSpice 全晶体管级，3 µm MOSIS 双层多晶 p-well，Vref = −2 V，p.2824）：主导转换误差为线性失调，均值 64 µV[OCR损：µ 误读为 p，下同]、总散布 22 µV；S/H 残余馈通 ≈62 µV；关反馈式抑制→失调约 445 µV（7 倍差）；关准差分抑制→失调 5.6 mV；开全部抑制→S/H 开关打开前失调 <10 µV。
- 建立时间口径（p.2823）：主时钟周期 5 µs[OCR损：原文"5 ps"系 µs 误读]；抑制比 10 需 φ8→φ' 间隔 = 主时钟半周期（即 2.5 µs）；仿真总环路带宽 ≈1.2 MHz。
- 元件取值（Table 1/2，p.2823）：C3、C3' = 220 单位、Cx = 100 单位（单位 0.1 pF，即 22 pF / 10 pF）；开关 S10、S11 为单沟道 n 管 50 µm/3 µm；S4、S7 = 50/50 µm；S1、S2、S3、S5、S6、S8 = n 5 µm / p 20 µm；S9、S12–S14 = 5/5 µm；全部沟长 3 µm。
- 阻抗匹配单元（p.2823）：三极管区阻抗胞与源跟随器 B1 的阻抗跟踪在参考电流变化 100% 范围内保持 1–2%。
- 时钟次序（p.2822）：φ1'/φ2' 须先于其他时钟切换（S1/S2、S3、S6、S8 闭合时 S10、S11 正在关断）——先进后出的时钟编排是对消生效前提。

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：**高**。本文给出差分对消成立的显式条件清单（五要素对称）与"端阻抗决定电荷分配"的机理——若 P1 消去条件主张中含"两通道/两开关对的对称性条件"，本文是 SC 域的直接文献支撑；反之，若 P1 未列端阻抗匹配，本文暴露该缺口（潜在补强点而非否定）。相关度：高。
- **P2（Kelvin 结构地板）**：未涉及引线电阻/四线制。相关度：无。
- **P3（衰减可达上界）**：无衰减理论；仅有 Cx·(1/CA+1/CB)≪1 的抑制因子（结构性衰减而非滤波衰减）。相关度：无。
- **方法学（D9/D5/C9）**：**高**。① D9 踢回：端阻抗分配机理 + 低阻驱动降低时钟斜率敏感（p.2822）可直接入 P1 文献综述；② D5 建立：抑制比 10 ↔ 半周期的门槛化表述（p.2823）是"把抑制倍数写进时间预算"的先例，但口径（10×、5 µs 时钟）远松于 P1（0.01%、4.096 MHz），引用时须并排声明差距，不可混同；③ 毛刺/采样值区分（p.2824）是 D9 适用边界的判据文献；④ C9 容性负荷运放：反馈式抑制即"运放经小电容 Cx 驱动容性负荷修正注入电荷"，其带宽缩减公式（式 3，OCR 损[待核]）是峰值≤6dB 类讨论的旁支。
- **killRisk**：无。本文不否定 P1/P2/P3；其条件清单反而强化"门槛化方法学"（把对消条件写成显式检查表）。唯一须防的误用：把本文"毛刺可被忽略"错引到连续时间观察点（P1 恰是连续域）。

## 没读到的
- **无硅实测**：全部结论为 HSpice 仿真（作者自注"actual circuits will exhibit less ideal performance"，p.2824），实测数据此篇没有。
- 式 (1)(2)(3) 的精确形式（z 域传函、增益误差 ∝ A⁻¹、带宽缩减式）在 OCR 中损毁（分数线/下标丢失），**待核**（可从文中引用的 [2][9] 与作者硕士论文 [12] 找回）。
- 馈通电荷绝对量（pC 级）未给——只有"残余误差电压"（µV 级），H5 轴"踢回电荷数值"此篇以电压口径间接呈现。
- 沟道电荷注入的解析模型未展开（直接引 [10] Shieh/Sheu 1987 与 [11] Wegmann/Vittoz 1987——**追踢回电荷定量模型应转读这两篇**，已在本文参考文献中定位）。
