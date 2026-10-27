# 精读笔记 · Parsan 2008《A comparator-based switched-capacitor integrator using a new charge control circuit》（IEEE SOC Conf. 2008, pp.139-142）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> H5 轴视角：**比较器基 SC（CBSC）积分器的电荷转移控制与输出建立**——① 用比较器+电流源"检测虚短"取代运放"强制虚短"，只适合驱动开关电容负荷；② 免预置（preset）方案靠减少每周期搬运电荷加快输出建立；③ 比较器延迟过冲在斜率恒定时退化为**常数直流失调**（系统性误差→可校准项）。踢回数值此篇没有，价值在"建立加速"与"误差→失调"两个方法学点。

## 出处
- Farhad Alibeygi Parsan, Ahmad Ayatollahi（Iran University of Science & Technology），"A comparator-based switched-capacitor integrator using a new charge control circuit", *2008 IEEE International SOC Conference*, pp. 139–142. DOI 10.1109/socc.2008.4641497。
- bibkey: `parsan2008`；全文 PDF：`fulltext/H5-kickback/parsan2008.pdf`（4 页，会议页 139–142，下引页码=会议页）。
- 主题：CBSC 积分器的新电荷控制电路（免 preset、双斜坡），0.18 µm CMOS、HSpice 仿真验证。

## 核心命题（原文）
1. **CBSC 用"检测虚短"取代运放"反馈强制虚短"，代价是只能驱动开关电容负荷**（p.139）：
   > "The idea is based on the detection of a virtual ground condition rather than forcing it via feedback. The advantages to this approach are inherently higher power efficiency, a removal of feedback and stability concerns, and its compatibility to most known opamp based architectures. On the other side, only switched-capacitor loads can be driven [3]."（H5"开关电容负荷"轴的边界条件文献：无运放反馈路径的电流源驱动只适用容性负荷，纯阻性/连续负载不可驱动。）
2. **传统 CBSC 时序：预置→粗斜坡(E1)→细斜坡(E2)；比较器延迟造成的过冲在斜率与延迟恒定时是常数失调**（p.139）：
   > "The final overshoot from the comparator delay is a constant offset in the output if the ramp rate and the comparator delay are constant [2]."（误差口径方法学：系统性瞬态误差在恒定斜率下退化为直流失调——可校准/可扣除，不必当随机误差处理。）
3. **免预置方案加快输出建立（少搬电荷=少花时间）**（p.140）：
   > "Eliminating the need to preset the output node at the beginning of the charge transfer phase will result in faster output settling. That is because the output node is not forced to start being charged from VSS in each clock cycle so less charge and consequently less time is needed to make output."（建立时间口径的一个变体：建立时间 ∝ 每周期需搬运的电荷量；从 VSS 全程充电是最慢的初始化选择。）
4. **所有电流源/沉关断后输出节点浮空，CL 上电荷保持**（p.140）：
   > "When all the current sources and the current sinks are inactive, the output node will be floating; therefore, the charge on CL will not change."（采样保持的"保持"物理：浮空即无电荷路径——与 H5"断开后节点扰动"讨论互补的另一半。）
5. **双斜坡使比较器延迟过冲可忽略**（p.140）：
   > "For practical applications a dual ramp charge control circuit is more desirable because the final overshoot due to the comparator delay will be negligible."（粗快细慢两段斜坡：终段斜率小 → 同样比较器延迟对应的过冲电压小。）
6. **开关与电流源串联消除每周期对 M1–M4 栅电容的充放电，提高电流驱动级开关速度**（p.141）：
   > "here the switches are in series with the current sources and the current sinks. This will eliminate charging the gate capacitances of M1–M4 with a constant reference current IREF in each clock cycle, hence it will increase the current drive circuit switching speed."（版图/拓扑级"减少每周期开关电荷搬运"技巧——与踢回抑制同思路：减少源头电荷而非事后对消。）

## 关键数值（原文）
- 仿真条件（p.142）：输入正弦 100 kHz、幅度 100 mV；时钟 1 MHz；C1 = 1 pF、C2 = 2 pF；0.18 µm CMOS；电源 1.5 V；两管阈值 |Vth| = 0.5 V；比较器输入失调 1 mV；VCM 取电源中点；HSpice。
- 误差结果（p.142）：比较器有限延迟造成的终态失调误差——单斜坡约 16 mV，双斜坡约 2 mV（8 倍改善）。
- 无硅实测（全部为仿真）；功耗/面积/建立时间绝对数值未给出。

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：无直接讨论（不涉两测量通道差分对消）。仅"过冲→常数失调"一点与"系统性误差可扣除"的口径沾边。相关度：低。
- **P2（Kelvin 结构地板）**：无。相关度：无。
- **P3（衰减可达上界）**：无。相关度：无。
- **方法学（D9/D5/C9）**：**中**。① D5 建立：建立时间与"每周期搬运电荷量"挂钩的定性依据（免 preset → 少电荷 → 快建立，p.140），可作为"建立时间口径必须写明初始化条件/起点"的引用；但**无建立时间绝对数值**（未给 µs/ns）；② C9 容性负荷驱动：CBSC 是"绕开运放驱动容性负荷"的替代路线（p.139"only switched-capacitor loads can be driven"），可作为 C9 讨论（运放峰值 ≤6 dB）的对照路线提及；③ 误差→失调的口径（p.139）支持门槛化方法学中的"系统性项与随机项分开列"。
- **killRisk**：无。不与 P1/P2/P3 冲突。

## 没读到的
- **踢回电流/电荷数值**：无 kickback/charge injection 的 pC 量化（H5 轴数值缺席）。
- **建立时间的绝对数值**：只有定性"faster settling"与仿真波形（Fig.9/10），无 ns/µs 级回稳时间、无回稳精度（0.01% 类口径没有）。
- 无硅实测数据；无功耗对比数字（"higher power efficiency"未给倍数）。
- 输入采样开关（Q2 相 C2 充电）上的电荷注入未讨论——踢回在输入侧的表现全文未触及。
