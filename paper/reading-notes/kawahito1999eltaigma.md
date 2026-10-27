# 精读笔记 · Kawahito 1999《Delta-Sigma Modulation Sensor Interface Circuits with Improved Conversion Gain for Capacitive Readout Chemical Sensors》（IEEJ Trans. Sensors and Micromachines 119-E(3):138-142）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> H5 轴视角：本文核心正是 **SC 输入采样结构的电荷转移完整性**——运放输入共模跳变导致电荷转移损失，交叉耦合分裂电容方案把转移效率拉回 ≈100%。这是"输入级开关切换扰动"机理的经典文献（作用点在运放输入节点而非传感器节点）。
> 文件为 e.Typist OCR 版，公式区与个别字符已损，引用中损处以 [OCR损] 标注。

## 出处
- Kawahito (Toyohashi Univ. of Technology), Koll, Hagleitner, Baltes (ETH Zurich), Tadokoro, "Delta-Sigma Modulation Sensor Interface Circuits with Improved Conversion Gain for Capacitive Readout Chemical Sensors", 電学論E, Vol.119-E, No.3, pp.138–142, 1999. DOI 10.1541/ieejsmas.119.138。
- bibkey: `kawahito1999eltaigma`；全文 PDF：`fulltext/H5-kickback/kawahito1999eltaigma.pdf`（5 页，期刊页 138–142，OCR 层，下引页码=期刊页）。
- 主题：CMOS 集成化学传感器（聚合物叉指电容）+ 二阶 ΔΣ 调制器读出，改进电容读出方案。

## 核心命题（原文）
1. **传统差分 SC 采样保持级因运放输入共模电压跳变损失传感电荷**（p.138）：
   > "This causes the loss of sensor signal charge because of the common-mode volt[age] change of the input of the differential amplifier."（引言中点名传统方案的损失机理：差分放大器输入端共模电压变化 → 传感电容电荷未完整转移——即输入采样开关节点扰动造成增益损失的机理。）
2. **传统方案的电荷转移过程（φ1 放电、φ2 充电+转移）**（p.139）：
   > "in φr1 phase, both a sensor capacitance Cs and a reference capacitance CR are discharged to zero. In φ2 phase, both Cs and CR are charged by VR, and at the same time, the charge is transferred into the feed[back] capacitance CF. ... In this scheme, however, the charges on Cs and CR are not completely transferred into CF, because of the large common-mode volt[age] change at the input of the fully differential ampli[fier]."（两相不交叠时钟下的输入采样结构完整描述；损失根源=共模大摆。）
3. **改进方案：传感/参考电容各分裂两半交叉耦合，运放输入电压在电荷转移期间不变，转移效率≈100%**（p.139）：
   > "Both the sensor capacitor and the refer[ence] capacitor are split into two parts. There are two types of charge transfer modes in SC amplifier; inverting and non-inverting. A pair of the split capacitors (CS/2 and CR/2) is used in inverting mode and the other pair is used in non-inverting mode. ... Hence the input voltage of the operational amplifier is unchanged during the charge transfer, and we can expect the charge transfer efficiency of approxi[mately] 100%."（核心命题：交叉耦合使每次转移中反相/同相支路对称，运放输入共模不动——把"开关切换扰动"从机理上消除而非靠建立时间等待。）
4. **转换增益 CR/CF 的上界由运放开环增益与 kT/C 噪声夹逼**（p.139）：
   > "the capacitive sensor sensitivity (ΔC/CR) can be enhanced by taking a large ratio of CR to CF. The maximum ratio of CR to CF is restricted by the open loop gain of the operational amplifier and usually the ratio is chosen as the value much smaller than the open loop gain to ensure the stable operation and the good linearity. ... On the other hand, the small CF leads to the large sampled thermal noise, or the kT/C noise."（SC 增益比的可行域=精度（开环增益）与噪声（kT/C）双向约束——与 H5"外部元件取值依据"同型的方法论。）
5. **二阶级联结构兼作相关双采样抑制 1/f 与失调**（p.140）：
   > "The two-stage second-order modulator acts as a correlated double sampling scheme to reduce the 1/f noise and the offset of the front-end stage (5)."（输入级开关切换误差的经典抑制手段 CDS 被结构性地吸收进调制器。）

## 关键数值（原文）
- SNR：DC–5 kHz 内 80.1 dB（65536 点 FFT，fs=1 MHz，正弦 1007.08 Hz）（p.140）；二次谐波约 2 kHz 处 −72 dB（p.141）。
- 电容与参考：VREF = VCS = VCR = 1 V [OCR损：原文作 "Vas"]，CR = 2.3 pF，C[OCR损：疑为 CF] = 2 pF，采样频率 250 kHz（p.141）。
- 灵敏度：乙醇 ≈2.5 Hz/ppm @28 ℃ → 对应 40 aF/ppm；最小可检测水平估计 1 ppm（DC–50 Hz）；湿度响应 3.2 kHz/10%RH（非线性）（p.141）。
- 漂移：72 小时约 5 Hz（fs=500 kHz），即满量程频移 250 kHz 的 20 ppm；化学源切断时频移保持零（p.141）。
- 工艺/面积：0.8 µm CMOS（AMS），接口电路约 2.0 × 0.7 mm²，叉指电容 400 × 400 µm²（p.140，"2•~0.7mm2"、"400 •~ 400ƒÊm2" 为 OCR 损形）。

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：**中**。本文差分输入（传感电容 vs 参考电容成对出现在同一 SC 积分器）+ 交叉耦合保证两支路电荷转移对称、共模不动——是"差分两路在开关切换下保持对称才能不损失信号"的电路级实例。它不直接讨论 P1 的消去条件（如两通道增益/相位匹配条件），但给"切换期间共模/对称性保持"这一必要条件的实际做法。相关度：中。
- **P2（Kelvin 结构地板）**：未涉及四线/Kelvin 或引线电阻地板。相关度：无。
- **P3（衰减可达上界）**：无衰减上界讨论；仅有 CR/CF 增益比可行域（开环增益上限、kT/C 下限），属结构增益而非滤波衰减。相关度：无。
- **方法学（D9/D5/C9）**：**中**。① 输入采样结构（两相不交叠时钟 φ1 放电/φ2 充电转移）是 H5 轴基准结构描述；② "共模跳变→电荷转移损失"机理 = 输入级开关扰动不加数值的定性机理（作用点在片内运放输入，不是片外传感器端 kickback）；③ CR/CF 取值依据（开环增益 + kT/C 双约束）是外部/内部无源件取值方法学的旁证。未给踢回电流/电荷 pC 数值，也未给建立时间口径。
- **killRisk**：无。本文不与 P1/P2/P3 主张冲突；其"转移期间输入共模不变"反而支持"切换扰动必须被结构或时间预算消化"的增量四立场。

## 没读到的
- **踢回电流/电荷数值**：全文无 kickback/charge injection 的 pC/µA 量化（H5 轴要的数值此篇没有）；"损失"只以转移效率（50% 减半、改进后 ≈100%）表述。
- 式 (1)–(5) 在 OCR 层全部丢失（版面公式区），ΔV0 与输出码的精确表达式无法逐字引用——如需公式须对照原刊。
- 运放建立时间/压摆率口径、开关时钟非交叠宽度等时序数值未给（Fig.4 时序图有波形但无 ps/ns 数）。
- "C = 2pF"（p.141）疑为 CF，OCR 无法确认，**待核**。
