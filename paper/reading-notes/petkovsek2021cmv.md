# 精读笔记 · Petkovšek & Zajec 2021《Evaluating Common-Mode Voltage Based Trade-Offs in Differential-Ended and Single-Supplied Signal Conditioning Amplifiers》（Electronics 10(16):1982, 1–18）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。

## 出处
- Petkovšek, M.; Zajec, P., "Evaluating Common-Mode Voltage Based Trade-Offs in Differential-Ended and Single-Supplied Signal Conditioning Amplifiers," *Electronics*, vol. 10, no. 16, art. 1982, pp. 1–18, 2021. DOI: 10.3390/electronics10161982（MDPI 开放获取）。
- 全文：`fulltext/H2-差分CMRR/petkovsek2021cmv.txt`（注意：**本篇是 .txt/markdown 抽取版，非 PDF**；页码按 MDPI 页脚 "X of 18" 标注，下文 p.X = 第 X 页/共 18 页）。bibkey：`petkovsek2021cmv`。
- 主题：低压汽车电力电子（低边安全开关拓扑）中**负极性共模电压**下的差分信号调理：单级/两级单电源 RRIO 运放差分电路的 CMV 输入合规设计流程、满量程最大化、基准电压敏感性、端子反接简化。

## 核心命题（原文）
1. **单级差放共模精确消去的教科书条件 = 电阻比值配对（DC、纯阻性）**（p.2–3, 式 3→4）：
   > "To reject its impact on the output voltage (u_out)  u_out = R2/(R1+R2)·(1+R4/R3)·u_in+ − (R4/R3)·u_in−,   (3)  the resistances R3 = R1 and R4 = R2 must be paired, resulting in  u_out = (R2/R1)(u_in+ − u_in−) = (R2/R1)u_meas,   (4)"
   （经典差放：比值相等 ⇒ 输出只含差模——单级、直流、无频率变量的消去条件；与 P1"单级 τ 匹配充要"同构的电阻版。）
2. **理想匹配给"无穷大"抑制、实际靠运放 CMRR**（p.3）：
   > "In (5), an infinitive rejection of CMV, provided by perfect resistance matching and an ideal OP, is assumed. In contrast, the real OPs exhibit a finite capacity given by CMRR to reject CMV (u_CM,OP) being present directly at the inputs of the operational amplifier."
   （CMRR 的两层来源：电阻网络匹配 + 运放自身有限抑制。）
3. **两级（仪表放大型）电路的消去条件不止比值相等——还须阻抗对称（多级条件的直接证据）**（p.5, 式 13–15）：
   > "To attain high CMRR (i.e., rejecting u_gG), the resistance quotients in front of u_in+ and u_in− in (13) must be equal. Subsequently, all four resistors should comply with  R2/R1 = RG1/RG2.   (14)"
   > "The relations R1 = RG2 and R2 = RG1 should also be met, to assure the impedance symmetry at the front-side of the amplifier."（p.5）
   （**仅式 14 比值相等不够，还要 R1=RG2、R2=RG1 阻抗对称**——两级拓扑的精确消去需要比单级更多的条件；这是 P1"多级梯形匹配不再充分"命题在**纯阻性直流域**的近亲表述，但完全无频率维度。）
4. **两级拓扑把运放输入 CMV 钉死为常数基准（结构性 CMV 解耦）**（p.5–6, 式 16–17）：
   > "u_+,1 = u_CM,OP1 = u_REF1,   (16)  u_+,2 = u_CM,OP2 = u_REF2.   (17)  Thus, the reference voltages must be positive and their magnitude inside the supply rail-to-rail levels to meet input OP restrictions."（p.6）
   > "the CMV applied (i.e. u_gG) affect neither of the u_CM,OP (16) nor (17), but it does affect the u_in+ = u_meas + u_gG"（p.6）
   （前端结构把外部 CMV 从运放输入端解耦——与"用结构而非精度对付共模"的思路，P1 的对照路线。）
5. **自定义差放天生 CMRR 较低，仍被采用是成本权衡**（p.15）：
   > "That is why a custom-built difference amplifier has a vital role in cost-sensitive applications regardless of the inherently lower common-mode rejection ratio (CMRR)."
6. **失配的实验口径：0.5% 电阻下的最坏误差带**（p.13–14）：
   > "For comparison, Figure 17 also shows the calculated worst-case voltage error margin vs. imposed negative CMV for resistances variation of ±0.5% (labelled R 0.5% limit)."（p.13；实测输出随 −60 V→0 V CMV 扫描偏离 3.3 V 常值，落在 0.5% 失配带内，Fig. 17, p.14）

## 关键数值（原文）
- 应用场景：U_HP=60 V 系统，CMV 范围 0…−60 V；U_S+=3.3 V 单电源；测量量程 U_FS,ag=3.3 V、U_FS,HP=60 V、u_cps=18 V（pp.6–7, 14）。
- 设计点（Table 1, p.7）：单级 G*=0.0521（3.3 V 档）/0.0275（60 V 档）、u_REF*=3.128 V/1.65 V；两级 R2/R1 同上、R_F/R_G1=19.185/2.0 等。
- 满量程对比（Table 2, p.8）：单级 U_FS,out=0.172 V（3.3 V 档）/1.65 V（60 V 档）；两级恒 3.3 V 全摆幅。
- 基准敏感度（式 30–31, p.10–11）：Δu_out% = (u_REF/u_out)·Δu_REF%；两级经电阻比 a 缩放；基准换 1 V 标称件后误差显著增大（Fig. 11b, p.11）。
- 元件：R1=100 kΩ 先选（耐压/自热，0.125 W），全部电阻 0.5% 容差（p.13）；实验平台 3.7 kW DC/DC 样机（p.12–13）。
- RRIO 运放负 CMV 裕量仅约 0.5 V 超出轨（NCV5230/TLV9001，p.1）。

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：相关度 **中**。给出单级差放（R3=R1、R4=R2）与两级仪放型（式 14 比值 + 阻抗对称双条件）的**直流纯阻性精确消去条件**——特别是"两级需要附加条件"这一点与 P1"多级不再充分"方向一致。但：①只有 DC 电阻网络，无 s 域、无频率响应；②对象是有源运放电路非无源梯形滤波器；③无"全频段"概念。**必须划界**：引用其式(14)+阻抗对称条作为"多级拓扑消去条件比单级多"的既有例证（DC 域），P1 的增量在频域/无源梯形。
- **P2（Kelvin 结构地板）**：相关度 **无**。无开尔文/四线内容。
- **P3（平坦度约束下衰减可达上界）**：相关度 **无**。"Trade-off"全部是 CMV 合规 vs 满量程/成本/基准可得性的权衡，无滤波器衰减-平坦度约束。
- **方法学（增量四 D1–D10）**：相关度 **低**。敏感性分析只对基准电压做（电阻用匹配对"减弱影响"后跳过），是减法式简化而非增量归因。
- **killRisk 判断**：**无威胁，须划界**。最接近 P1 的表述是式(14)+阻抗对称（p.5），但那是两级**有源**差放的 DC 消去条件，未触及"多级无源网络全频段精确消去条件"（无传递函数、无频率、无滤波器）。在 P1 论文中可作为"多级需附加条件的先例"友好引用。

## 没读到的
- 频域/动态特性被明确排除："Dynamic and frequency features of the signal conditioning circuits were thus put in second plan."（p.6, §3 开头）——**无 CMRR(f) 数据、无滤波器频响**。
- 电容/滤波器元件完全未出现（无抗混叠、无频率补偿讨论）。
- CMRR 数值未给出（只有"custom-built 差放 inherently lower CMRR"的定性陈述）。
- 图片为外部链接（.txt 版未嵌入），图 7–17 的曲线细节以正文描述与表格为准；若需精确曲线须取 MDPI 原版 PDF。
