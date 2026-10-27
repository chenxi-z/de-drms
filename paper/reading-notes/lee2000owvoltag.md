# 精读笔记 · Lee 2000《Low-Voltage Opamp Design and Differential Difference Amplifier Design Using Linear Transconductor with Resistor Input》（IEEE TCAS-II 47(8)）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
## 出处
- Lee, Edward K. F.（Iowa State University）
- IEEE Transactions on Circuits and Systems—II: Analog and Digital Signal Processing, Vol. 47, No. 8, August 2000, pp. 776–778, doi:10.1109/82.861410
- PDF 共 3 物理页（=期刊页 776–778）。全文已读（OCR 将「±」读成 0/6，数值已按上下文校正标注）。

## 核心命题（原文）
1. **1 V 电源下基于多晶电阻线性跨导器实现运放与 DDA**（p.1，摘要）：> "This paper describes a 1-V wide-input range and high linearity transconductance input stage that uses poly resistor and input-impedance boosting technique."（主题是低压线性跨导器电路，不是无源差分滤波。）
2. **交叉耦合双跨导器构成伪差分、抑制共模**（p.2）：> "A fully differential input transconductor can be realized using two transconductors shown in Fig. 1. By cross coupling the outputs of the transconductors as shown in Fig. 2, the output currents will remain unchanged when both input voltages of the transconductors are equal. Therefore, the common-mode input signal is rejected and a good common-mode rejection ratio (CMRR) can be achieved using this psuedo-differential scheme."（「psuedo」为原文拼写笔误。其 CM 抑制来自两个有源跨导器输出相减的电路对称，不是无源网络的全频段消去条件；且为「两输入相等→输出电流不变」的静态对称论证，无失配→CM 误差解析式、无频域条件。）
3. **增益精度由电阻匹配主导**（p.2）：> "Since the value of gm is inversely proportional to the resistor R (shown in Fig. 1), the accuracy of the amplifier gain is mainly determined by resistor matching."（承认电阻匹配决定精度，与 P1 动机同向，但只针对增益精度，未建 CM 通道。）
4. **跨导器失配的后果 = 失调电流，只能靠版图缓解**（p.2）：> "Another effect that will be caused by transistor mismatch is the input offset current, which can only be minimized with good layout techniques such that good matching for the current mirrors (M2; M4; M9 and M13) and the current sources (M5; M6; M12 and M14) can be achieved."（失配的出路是版图匹配，无解析补偿/消去机制。）

## 关键数值（原文）
- 工艺/电源：1.2 µm CMOS，VTN≈0.6 V、VTP≈0.8 V，供电 1 V（±0.5 V 测试）（p.3）。
- 跨导器 THD：> "The transconductor has a total harmonic distortion (THD) of less than 60 dB for an input swing of 400 mV at 10 kHz."（p.1，OCR 作 060 dB）
- **实测 CMRR**（p.3）：> "The CMRR was measured to be greater than 43 dB."（线性差分放大器配置，R1=30 kΩ，THD<−70 dB @ 600 mV p-p、10 kHz 同段给出）
- 输入阻抗 156 kΩ（地电位）@ 加阻抗提升；无提升时提高 >6 倍（p.3）：> "The input impedance is increased by more than six times compared to the case without input-impedance boosting."
- 运放开环直流增益 ≈58 dB、单位增益频率 2.2 MHz、相位裕度 65°（20 pF 负载）；功耗：运放 0.5 mW、DDA 0.67 mW（p.3）。
- 差分放大器增益误差 <1.5%（三个可选增益 2/4/8）（p.3）。

## 对 P1/P2/P3 的对照
- **P1（无源差分网络失配→CM 误差解析条件）**：低。给出的是有源伪差分电路的 CM 抑制机制（对称输出相减），无元件失配→CM 误差的解析条件，无全频段消去条件；对 P1 的「无源网络」定位不构成竞争，反而是有源路线的对照点。
- **P2（Kelvin 结构地板 ≈56dB）**：低。其 43 dB 实测 CMRR 可作 P1/P2 论文里的对照数值（有源伪差分 < 56 dB 无源结构地板），但该文自身无地板概念。
- **P3（平坦度约束衰减上界）**：无。连续时间滤波器只是结论里的应用展望（"continuous time filters with cutoff frequencies up to the low megahertz range"），无平坦度-衰减约束。
- **方法学（D1–D10）**：无。
- **killRisk 判断**：无威胁。CMRR 43 dB 的量级反而支持 P2「被动结构才可能高 CMRR」的叙事；引用时注意其 CMRR 是电路级实测（伪差分）而非网络级解析。
- 谱系定位：四层谱系之外（低压有源模拟电路线）。

## 没读到的
- Fig.2/Fig.4 电路图细节未逐管核对；43 dB CMRR 的测试条件（CM 输入幅度、频率）文字未给全，「待核」。
