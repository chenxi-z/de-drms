# 精读笔记 · Song 1993《A Clock Feedthrough Reduction Circuit for Switched-Current Systems》（IEEE JSSC 28(2):133-137）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> H5 轴视角：**时钟馈通（clock feedthrough）= 输入踢回同族机理的直接文献**——重叠电容耦合 + 沟道电荷再分配两个效应、沟道电荷定量式 Qc = Cox·AQ·(VgQ−VTn)、误差电压表、"抑制手段 vs 最高工作频率"权衡、以及**信号依赖分量靠镜像电流对消**的方案。作用场域是开关电流（电流拷贝器）而非 ADC 输入级，但机理与对消方法学可直接迁移引用。

## 出处
- Minkyu Song, Yongman Lee, Wonchan Kim（首尔国立大学），"A Clock Feedthrough Reduction Circuit for Switched-Current Systems", *IEEE Journal of Solid-State Circuits*, vol. 28, no. 2, pp. 133–137, Feb. 1993. DOI 10.1109/4.192044。
- bibkey: `minkyusong1993`；全文 PDF：`fulltext/H5-kickback/minkyusong1993.pdf`（5 页，期刊页 133–137，下引页码=期刊页）。
- 主题：开关电流系统的时钟馈通机理分析与对消电路；1.2 µm CMOS 测试芯片。

## 核心命题（原文）
1. **时钟馈通的两大机理：重叠电容 + 沟道电荷再分配**（p.133）：
   > "Although there are many secondary effects that produce the clock feedthrough problem, the two most important effects are overlap capacitances and channel charge redistribution."（H5 轴最根本的机理分类句：开关动作向敏感节点注入误差的两大通道。）
2. **沟道电荷是主导误差源，可比重叠电容效应严重得多**（p.134）：
   > "From Table II it is shown that the error voltage due to the channel charge redistribution is much more serious than the error voltage due to overlap capacitances. If the size of the switch transistor is much larger than that of the mirror transistor, the clock feedthrough error is so large that the error voltage is approximately up to the power supply."（量化结论：开关远大于受扰管时误差电压可接近电源轨。）
3. **尺寸调整抑制法牺牲速度（踢回抑制 vs 工作频率的权衡）**（p.133/135）：
   > "In Fig. l(a) clock feedthrough errors can be reduced by increasing the size of MN2 and minimizing the size of MNQ. However, this reduces the maximum operating frequency [7]."（p.133）——以及（p.135）"if the error voltage is allowed to be less than 0.1 V by the clock feedthrough offset, from (5) and Table II the size of the mirror transistor should be about 40 times larger than that of the switching transistor, when Vgg is 5 V and N is 2. In this case, however, the advantage of the switched-current systems-that they can be operated at high frequencies due to small MOS transistors-almost disappears."（纯"被动吸收"路线把受扰侧电容做大 40 倍才压到 0.1 V，代价是高速优势尽失——这是"踢回靠吸收 vs 靠对消 vs 靠时间预算"三角权衡的经典表述。）
4. **虚管（dummy）法与复制（replica）法的缺陷**（p.133）：
   > "Although the dummy transistor MN5 collects the error charge of MNQ, the accuracy of this technique is dependent on the phases of two clocks, which is very difficult to control."（dummy 法依赖双时钟相位配合）——与——"This technique cancels only the signal-independent clock feedthrough current. If the signal-dependent clock feedthrough current is large, the output current is significantly distorted by the signal-dependent clock feedthrough current."（replica 法只消与信号无关分量，信号依赖分量残留会显著失真。）
5. **本文方案：信号依赖分量经镜像反极性叠加对消，误差几乎抵尽**（p.135）：
   > "The circuit adopts the current cancellation technique. In Fig. 4(a), if all the transistors are small, io1 and io2 are very distorted by the clock feedthrough error voltages. However, the polarity of io1 is reversed by the current mirror, and then it is added into io2. Therefore, the clock feedthrough error at the output node almost cancels out."（把含信号依赖馈通的支路电流成对反相相加——对消条件=两路径匹配（镜像对称），与 P1"差分对消要求两通道一致"同构。）
6. **同等误差指标下面积代价从 40× 降到 5×**（p.135）：
   > "if the allowed output error current is the same as that of the size adjustment technique above whose allowed error voltage Vc2 is 0.1 V, then the area of the mirror transistor in the proposed circuit is only about 5 times larger than that of the switching transistor."（对消法相对吸收法的量化收益。）

## 关键数值（原文）
- 沟道电荷定量式（式 3，p.134）：Qc = Cox·AQ·(VgQ − VTn)；栅节点总电荷式（式 1）Q = (Vg2−VgQ)C1 + (Vg2−VO)C2 + Vg2·Cg2；开关关断后栅压（式 2）与总误差电压（式 5）＝重叠项 + 沟道项之和。
- Table II（p.134，**OCR 损**，行读作 "72/20 → 0.027 / 4.340 / 4.367"）：同工艺下沟道电荷再分配误差电压（V 量级）远大于重叠电容误差（≈0.027 V）；具体行列结构损，**待核**。
- 面积比结论：误差允许 0.1 V@Vgg=5 V、N=2 时，尺寸调整法镜像管须为开关管 40 倍；对消法仅需 5 倍（p.135）。dummy 侧开关误差减半关系 Vcs = Qc/Cg1 = Qc/2Cg2 ≈ Vc2/2（p.135）。
- 测试条件（p.136）：1.2 µm CMOS、5 V 电源、输入正弦 190 mVpp @1 kHz、时钟 0–5 V 脉冲 20 kHz；最小管尺寸 6/6 µm²（避免 dog-bone 版图与短沟道效应，p.134）。
- Table III 芯片特性（p.137）：die 尺寸 190×130 µm²（本文）vs 230×130 µm²（常规，面积省 ≈20%）；3 dB 频率 250 kHz vs 200 kHz；功耗 3 mW vs 2 mW（本文功耗更大）。

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：**中**。本文的对消电路给出"两条镜像路径反相叠加→馈通误差几乎对消"的电路实例，其成立条件是路径匹配（尺寸/电容成比例）；这与 P1"两通道差分对消需满足匹配条件"在方法学上同构，可作跨域旁证。但本文对消的是**开关馈通误差**而非测量通道公共项，非 P1 的直接场景。相关度：中。
- **P2（Kelvin 结构地板）**：未涉及引线电阻/四线结构。相关度：无。
- **P3（衰减可达上界）**：无衰减/滤波讨论。相关度：无。
- **方法学（D9/D5/C9）**：**高**。① 机理与定量：踢回两通道（重叠电容 + 沟道电荷）+ 沟道电荷式 Qc = Cox·AQ·(VgQ−VTn)，可直接搬进 D9 kickback 的机理叙述；② 量化口径：误差以"误差电压"（V）计、抑制指标以"允许误差 <0.1 V"设门槛——与 P1 增量四"门槛化方法学"（给数值门槛而非定性说法）同型；③ 权衡证据："抑制馈通的三条路（吸收/对消/时间）各有代价"：吸收→面积与最大频率（40×、高速优势消失），对消→匹配条件+功耗（3 vs 2 mW）；④ C9 运放驱动容性负荷：本文非直接，但"最大工作频率随管子变大而降"同一物理。**注意**：本文数值全部是 1.2 µm CMOS、5 V 工艺的电流拷贝器场景，迁移到 P1（fMOD=4.096 MHz、122 ns 半周期、0.01% 回稳）时只能引方法学，不能引数值。
- **killRisk**：无。不与 P1/P2/P3 冲突；其"信号依赖分量必须对消而非只靠 dummy/replica"的结论反而支持增量四把踢回门槛写成显式判据的做法。

## 没读到的
- **建立时间口径**：全文无 settling time 数值（无 ns/µs 级回稳时间），H5 轴"建立时间口径"此篇缺席（只有"最大工作频率 250/200 kHz"间接相关）。
- Table II 完整数值矩阵 OCR 损坏（仅可辨一行 0.027/4.340/4.367），各行对应的管尺寸无法核对，**待核**。
- 式 (5) 中各项系数的完整排版（OCR 中下标/分数线损），精确形式**待核**（需对原刊或重扫件）。
- 未讨论 ADC 输入级（采样开关对源阻抗+采样电容的踢回）场景——开关电流与开关电容的负载结构不同，kickback 传递函数不能直接套用。
