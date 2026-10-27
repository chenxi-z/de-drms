# 精读笔记 · Nedelcu 2022《A customizable, low-power, wireless, embedded sensing platform for resistive nanoscale sensors》（Microsystems & Nanoengineering）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> H6 轴定位：本批 H6 中唯一的"测量平台/前端工程"论文（ETH Hierold 组，气敏 CNT，非结构 SHM 应变）。它**确实量化了前端噪声/失调**——但方式是"实测残差+报告"，而非元件级条件消除；无差分/Kelvin/AC 调制。页码 = PDF 页（排版"Page N of 11"，PDF 页与文页一致）。

## 出处
- Nedelcu, Thodkar, Hierold. "A customizable, low-power, wireless, embedded sensing platform for resistive nanoscale sensors." Microsystems & Nanoengineering (2022) 8:10. doi:10.1038/s41378-021-00343-1。PDF 11+1 页。
- bib key：`nedelcu2022platform`。

## 核心命题（原文）
1. **平台指标：nA–µA 电流数字化 + 可编程双极偏压**（p.1 摘要）：
   > "Here we report a platform capable of acquiring currents ranging from 1.5 nA to 7.2 µA full-scale with 20-bit resolution and variable sampling rates of up to 3.125 kSPS. In addition, it features a bipolar voltage programmable in the range of −10 V to +5 V with a 3.65 mV resolution."
2. **测电阻 = 恒压偏置 + 测流（两端器件、纯 DC，无比例测量）**（p.3）：
   > "For instance, the CNT has a typical resistance of ~100 kΩ to 20 MΩ, resulting in a current from 1 µA to 5 nA (bias = 100 mV)."
3. **前端实现 = 商用电流-数字转换器 DDC114 时间交织积分器 + 12 bit DAC MCP4922 + MAX660 倍压电荷泵**（p.3）：
   > "Figure 1c shows the detailed schematic of DDC114 time-interleaved integrators in 'Convert Configuration' and 'Integrate Configuration' with the timing diagram. The front-end integrators are followed by dedicated ADCs (16 or 20-bit configurable resolution)..."
   > "...the potential bias of the sensor is software-defined and converted by a 12-bit DAC MCP4922, offering 1.25 mV resolution on each channel."
4. **前端误差有实测表征：开路输入的输入端等效 RMS 噪声与失调（含 PCB 寄生与漏电）**（p.4，H6 批中最接近"前端误差"的段落）：
   > "...the noise, parasitic capacitances, and leakage currents originating from the PCB tracks, socket, and ceramic package, have been evaluated. With the four channels in an 'open' state, Fig. 3e shows the input-referred current RMSnoise together with the current offset."
   （Fig. 3e，p.5：IN1 失调 0.98 nA / RMS 1.17 nA；IN2 −0.01/1.15；IN3 0.02/1.13；IN4 −0.09/1.11 nA。）
5. **门槛化方法学：3σ LOD + 斜率检测模式**（p.1 摘要；p.7 展开）：
   > "Although sensor signals are measured for NO2 concentrations of 1 ppb, the 3σ limit of detection (LOD) of 23 ppb is determined (1σ: 7 ppb) in slope detection mode, including the sensor signal variations in repeated measurements."
6. **无任何 AC/斩波/锁频抑失调手段**：全文无 lock-in/chopper/modulation（已 grep）；带宽由积分器配置决定（Fig. 3c–d，p.5），失调靠"输入端等效、实测报数"处理。

## 关键数值（原文）
- 电流量程 1.5 nA–7.2 µA FS，20 bit；采样 0.001–3.125 kSPS；Tconv 0.64–2000 ms；Crange 积分电容 {3, 12.5, 25, 50} pF（p.1、p.3–4）。
- 偏压 −10…+5 V，3.65 mV 分辨率；DAC MCP4922 12 bit、1.25 mV/通道（p.3）。
- 开路输入失调/RMS 噪声：见命题 4（Fig. 3e，p.5）。
- 功耗 64.5 mW @ 3 样/s（含 0 dBm BLE 广播）（p.1）。
- NO2 实验：200 ppb → 1 ppb 阶梯；3σ LOD = 23 ppb（1σ 7 ppb），斜率检测模式（p.1、p.6–7）；QSS 模式 LOD 另算（p.7 图中 LOD_SD 23.4、LOD_QSS≈52 ppb 量级——逐值待核 Fig. 5）。
- CNT 器件电阻典型 100 kΩ–20 MΩ；偏置例 100 mV（p.3）。

## 对 P1/P2/P3 的对照
- **P1（G_DC≡0 元件条件）**：**中相关、无冲突**。该文证明应用/平台侧"会测残差"（开路失调 ≈1 nA 级、RMS 噪声 ≈1.1 nA），但没有给出任何使 DC 误差恒为零或被结构抑制的电路条件——误差被表征、被报告，随后进入 LOD 预算（3σ），并未被设计消除。P1 的"元件条件"层面仍是空白；本文是"H6 空白"命题的**边界样本**（气敏平台文，非 SHM 应变文；写笔记时勿把它归入"完全不谈前端"的一类）。
- **P2（Kelvin 结构地板 ≈56 dB）**：无。两端器件插座/焊接接触，100 kΩ–20 MΩ 下接触电阻不可见，全文无 four-wire/Kelvin/接触电阻讨论（已 grep）。
- **P3（衰减可达上界）**：无。DC 偏置占空比工作，传感器自身的 settling（~20 min）主导时间行为；无通道直流衰减/漂移模型。
- **方法学（门槛化）**：**中偏高**——LOD=3σ·噪声/斜率 是把"测量链噪声→检测门槛"公式化的标准做法（p.7），与增量四的"门槛化"同构；但其噪声项是整机实测 RMS，非链路解析上界。
- **killRisk**：无（其前端为电流积分型恒压偏置，与 P1 的恒流+比例/条件消除路线不同构，无正面交锋）。

## 没读到的
- 补充材料（Supplementary Section 1 的 FS/传函推导、Fig. S2–S7）：未随正文 PDF 提供，公式细节待核。
- Fig. 5a 的 LOD_SD/LOD_QSS 拟合逐值（正文图给 23.4 与 52 ppb 量级，精确值待核）。
- 表 1（p.9，与其他平台对比表）逐列数值：未逐项摘录（含"±30 ±3%ss"等字样，需原表核对）。
- 任何差分/共模/Kelvin 讨论：无（已确认）。
