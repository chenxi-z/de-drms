# 精读笔记 · Keller 2022《Noise Coupling》（Design for EMC — In a Nutshell, Springer, Ch.12 pp.189–209）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> 页码用书页（189–209）；PDF 页 1–21 与之差 188。EMC 教材章节：耦合路径分类 + DM/CM 分解 + 不平衡因子 h 与 IDM（不平衡差分建模）。

## 出处
- Keller, R.B., "Noise Coupling", Chapter 12 in *Design for Electromagnetic Compatibility – In a Nutshell*, Springer, 2022（版权行 "© The Author(s) 2023"），pp. 189–209. doi:10.1007/978-3-031-14186-7_12. Open Access（CC BY 4.0）.
- 本地：`H2-差分CMRR/keller2022noisecoupling.pdf`（21 页）。bib key：`keller2022noisecoupling`（literature.bib L1757，备注"不平衡因子 h=Z1/(Z1+Z2)"）。

## 核心命题（原文）

1. **EMI 三要素与四种耦合路径分类（章框架）**（p.189–190）：
   > "1. Source. … 2. Coupling path. The noise needs a path from the source to the victim. … 3. Victim. … Figure 12.2 shows the four different types of coupling: 1. Conductive coupling (common impedance coupling) 2. Capacitive coupling (electric field coupling) 3. Inductive coupling (magnetic field coupling) 4. Radiated coupling (electromagnetic field coupling)"（p.189–190）
   中文：教科书式分类法；共阻抗/容性/感性/辐射四路，P1/P2 的共模入侵路径清单可引此为总纲。
2. **不平衡因子 h=Z1/(Z1+Z2)：把"差分对不平衡"参数化的标准 EMC 度量**（p.199）：
   > "In the case of a balanced transmission line (both conductors have equal impedances to ground), the common-mode voltage V_CM [V] is 0.5 of the sum of the voltages … However, in the case of an unbalanced transmission line, things are getting a little more complicated, and therefore, we have to define the imbalance factor h. … h = Z1/(Z1 + Z2)  (12.11)"（p.199）
   > "V_CM = h · V1 + (1 − h) · V2  (12.13) … I_DM = (1 − h) · I1 − h · I2  (12.14)"（p.200）
   中文：h 是**阻抗比**形式的频率相关不平衡度量；Z1=Z2（平衡）时 h=0.5、V_CM=(V1+V2)/2。与 P1 的 G_DC=H_N−H_P 同一物理（两支路不对称→模式转换）但不同形式（单参数 h vs 全传递函数差）。
3. **共模→差模转换发生在不平衡处；高增益仪表放大器入口是敏感点**（p.202–203）：
   > "A common-mode noise current I_nCM [A] can be converted to a differential-mode noise voltage V_nDM [V] in the case of unbalanced lines. Unbalanced lines mean that the lines are not 100 % balanced; — in other words, the forward and return current lines of a differential signal have [3]: 1. Different impedances along their length 2. Different impedances to ground."（p.202–203）
   > "Electronics designers should especially ensure that signal lines at the input of high-gain instrument amplifiers are well balanced. Otherwise, even a tiny common-mode noise current I_nCM [A] could cause a significant noise voltage V_nDM [V] at the output of the high-gain amplifier."（p.203）
   中文：P2（Kelvin 地板）动机的直接引文——入口不平衡是共模电流变差模电压的闸门；但本文只给"保持平衡"的定性处方，**没有可达的平衡极限**（无容差→残余转换的闭式）。
4. **IDM 不平衡差分建模：转换电压=差模电压×不平衡度变化 Δh**（p.206）：
   > "Any change in electrical balance to ground of a transmission line converts some power of the differential-mode signal into a common-mode signal [4]. This differential-to-common-mode conversion happens if—and only if—there is a change in balance of the transmission line [2]."（p.205）
   > "V_AM = V_DM · Δh  (12.16) … Δh = hL − hR = change of imbalance factor h at the imbalance interface"（p.206）
   中文：模式转换被压缩成**一个标量乘法**——这与 P1 把转换压缩成 H_N−H_P 同样是"降维"，但 IDM 面向辐射发射最坏情形，P1 面向测量精度的精确频域消去；审稿人可能要求比较两者，P1 应说明 h 形式无法表达多级 RC 的零极点结构（交叉项）。
5. **容性耦合两极限：低阻 victim 按 jωRC12 恶化，高阻 victim 变成与频率无关的分压器**（p.194）：
   > "Vn = jωRC12 V1, in case of relatively low R  (12.5) … Vn = [C12/(C12 + C2G)] V1, in case of relatively large R  (12.8)"（p.194）
   > "This means for a very large R [Ω], the conductive noise coupling is independent of the frequency ω … and the noise voltage is of larger amplitude than when R [Ω] is small."（p.194）
   中文：高阻节点（如 P1 传感层 150 kΩ 源阻抗）的容性串扰是**频率无关的分压型**——低通滤波压不掉，只能在几何/屏蔽上解决；这是 P1 论证"AAF 之外还须共模入口设计"的旁证。

## 关键数值（原文）

- h = Z1/(Z1+Z2)；平衡线 h=0.5（p.199）。
- IDM 最坏情形转换比（p.207）："As a worst-case, it can be assumed an imbalance factor change of Δh = 0.5 (perfectly balanced to completely unbalanced and vice versa)"，故 |V_AM| = |V_DM|·0.5 (12.18)——**模式转换最坏 −6 dB**。
- 辐射最坏估算链（p.207–208）：I_AM,max = V_AM/(36.5·k_board·k_cable)；R_min = 36.5 Ω（λ/4 单极子辐射电阻）；E_AM,max ≈ 60·I_AM,max/d × sin 因子（12.19）；板等效长 l_board 公式 (12.23)。
- 容性耦合：i_n(t)=C12·dv1/dt (12.2)；感性：v_n(t)=M12·di1/dt (12.9)、V_n = jωM12|I1| = jωΦ12 (12.10)；共阻抗：V_n = I_n·Z_com 且 |Z_com(f)| 随频率升（p.192）。
- 辐射抗扰测试口径（p.198）：IEC 61000-4-3，80 MHz–6 GHz，典型 d=3 m；CISPR 32 辐射发射 30 MHz–6 GHz，d=3/10 m。

## 对 P1/P2/P3 的对照

- **P1（失配消去条件）**：相关性**中（相邻形式体系，非对手）**。h/IDM 把不平衡→模式转换参数化为标量乘法（V_AM=V_DM·Δh），与 P1 的 G_DC=H_N−H_P 是同一物理的两种压缩；但 Keller 无 RC 网络、无零极点、无"何值使转换≡0"的消去定理，也无多级交叉项——不构成 kill，反而是 P1"传递函数级 vs 标量级"方法优势的对照物。P1 写作时应在 related work 引 IDM 并划界（IDM=EMC 最坏情形标量法；P1=测量域精确频域消去法）。
- **P2（Kelvin 地板）**：相关性**中低**。"signal lines at the input of high-gain instrument amplifiers are well balanced"（p.203）支持"入口平衡决定共模抑制"的动机；无 Kelvin、无地板数值（最坏转换只给 Δh=0.5 的 −6 dB）。
- **P3（平坦度约束衰减上界）**：相关性**低**。滤波只作为对付耦合的措施出现（"These filters are typically low-pass filters with capacitors or ferrites"，p.192；"For differential signal interfaces, common-mode chokes are also a good filter option"，p.198），无衰减/平坦度定量约束。
- **方法学（D1–D10）**：无。但第 1 条（源/路径/受害者三分）与"耦合常级联叠加"（"coupling mechanisms often happen in cascades and interfere with each other"，p.198）可用于 D 项的威胁模型清单框架。
- **killRisk 判断**：非 killRisk（EMC/辐射发射域，与 P1/P2/P3 无主张重叠）。

## 没读到的
- RC 差分滤波器/抗混叠/τ 匹配（全文无）；
- Kelvin 四线结构；任何"容差→残余转换"的统计或闭式；
- 滤波器衰减上界/平坦度约束；
- 本章为教材章，参考文献 9 条为概览级（Ott、Paul、LearnEMC 等），未含仪器测量文献；
- bib 备注"综述见 Illing & Wu（题录待核）"——本文引文中无此条，仍待核。
