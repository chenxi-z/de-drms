# 精读笔记 · Cseresnyés 2013《Role of phase angle measurement in electrical impedance spectroscopy》（International Agrophysics）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。

## 出处
- Cseresnyés I., Rajkai K., Vozáry E., Int. Agrophys., 2013, 27, 377-383，DOI 10.2478/intag-2013-0007。
- PDF 共 7 物理页 = 印刷页 377–383（页码下文按物理页 1–7 对应印刷 377–383）。
- 内容：玉米盆栽根系阻抗谱（EIS）应用研究——论证相位角测量对选择"特征频率"的必要性。**应用领域论文（农学），非计量仪器论文**。注意：pdftotext 将 Ω 丢失为 W / kW（实为 Ω / kΩ）。

## 核心命题（原文）
1. **中心主张：固定频率工作而不测相位角谱应被禁止；特征频率须由相位角谱选出**（p.1 Abstract）：
   > "Consequently, the regularly repeated phase angle measurement is advisable in time-course studies for effective application of the electrical impedance method, and the systematic operation at the same frequency without determination of phase angle spectra should be avoided."
2. **机理：耗散与根系尺寸无关 → 相位角（容性强度）决定阻抗–根尺寸回归质量**（p.1 Abstract）：
   > "Since the rate of energy dissipation is independent of root extent, the higher phase angle and lower energy dissipation were associated with the higher coefficient of determination achieved for the root electrical impedance – root system size (root dry mass and root surface area) regressions."
3. **仪器与接线：两电极 LCR 电桥（非四端、非比率结构）**（p.2）：
   > "The EI, phase angle (F) and dissipation factor (D) were measured with a HP 4284A LCR-bridge (Agilent Techn., Santa Clara, USA) in a parallel equivalent circuit at 55 logarithmically distributed, pre-programmed frequencies ranging from 100 to 10 000 Hz with 1 V terminal voltage."
   > "One terminal of the instrument was connected to the ground electrode ie a stainless steel rod (6.3 mm in diameter and 15 cm long) inserted to a depth of 10 cm into the potting soil and positioned 6 cm away from the stem base. The second terminal was attached to the plant stem with a spring tension clamp"
4. **耗散因子定义**（p.2）：
   > "The phase angle is inversely proportional to the dissipation factor (D = 1/tan F) and is used for measuring the tendency of dielectric materials to absorb and dissipate some energy without inducing charge alignment on the membrane surfaces."
5. **频带两端的两类系统误差（电极极化 / 杂散电容）**（p.5）：
   > "Additionally, this phenomenon can be intensified by occurrence of two sources of systematic error such as electrode polarization impedance and parasitic (stray) capacitances apparent at low and high frequencies, respectively (Cao et al., 2010; Ozier-Lafontaine and Bajazet, 2005)."
6. **生物学解释框架：α/β 色散区间**（p.5）：
   > "The a-dispersion (100 mHz – 1 kHz) is due to surface admittance and depends principally on the external membrane surface and apoplastic structures (cell walls), while b-dispersion (1 kHz – 1 MHz) is mainly associated with the internal membrane and intracellular structures."
7. **特征频率随植株老化持续上移（频谱漂移 → 必须重复测相位谱）**（p.6）：
   > "Owing to the insulating effect of suberin, principally inhibition of the apoplastic pathway occurs; therefore, the maximal value of F shifts continuously to the higher frequency."

## 关键数值（原文）
- 实验 1（p.3，n=18）：EI–根干重回归 "R2 = 0.561 was obtained at the lower end of the frequency range (100 Hz); then, it greatly increased along with the increasing frequency, reaching the maximum value of 0.946 at 1090 Hz. From this point, the coefficient decreased continuously with the increasing current frequency (R2 = 0.823 at 10 000 Hz)."；EI–根表面积回归 "R2 = 0.491 was obtained at 100 Hz; it culminated at 1 300 Hz (R2 = 0.916) and finally reduced to the value of 0.772 at 10 000 Hz."（回归型均取 y = −a×ln(x) ± b）。
- 相位角谱（p.4）："The phase angle had an upward trend from 100 Hz (F = -24.8°) to 1190 Hz (F = -37.4°) and then it decreased towards the higher current frequencies (F = -33.2° at 10 000 Hz). Thus, the apex of F practically coincided with the culmination of R2 values considering the current frequency."
- 实验 2（除草剂 acetochlor，p.4，n=16）："The highest level of significance (p < 0.001) was obtained when current frequencies between 250 Hz and 1 830 Hz were applied"；"became statistically insignificant (p > 0.05) below 120 Hz or above 2 820 Hz"；"The maximum F value (-30.3°) occurred at the frequency of 920 Hz"；"The highest significance level obtained … coexisted with the F value more than approximately -27° … undetectable at the frequency range corresponding to F lower than about -24.5°."
- 实验 3（时间进程，p.4–5，n=12，day 11–74）：day 11 "a -30.7° maximal phase angle and 1.68 minimal D values"；day 39 "the highest phase angle (F = -39.5°) and inherently the lowest energy dissipation (D = 1.26)"；day 74 "the maximal F and minimal D were -26.3° and 2.06"；特征频率 "shifted continuously to 3 650 Hz obtained on experiment day 60, thereafter it remained constant"（最初两次测量为 920 Hz）。
- 土壤 vs 根系系统阻抗（p.3，Ω 被 pdftotext 丢成 W）："EI in soil was only 120~160 W [Ω] with a -0.4~ -0.6° phase angle. These values were insignificant in relation to the magnitude of EI (8~48 kW [kΩ]) and F (-22~ -38°) measured in the root-soil system."（土壤支路可忽略，未做修正）
- 环境：24/18°C 昼夜、光强 300 µmol m⁻² s⁻¹（原文印 mmol，应为 µmol，[OCR/排版疑误，待核]）；Arenosol 土壤 1.8 kg/盆；盆栽 1.25 dm³。

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：相关度**无**。无 SC ΣΔ、无滤波网络、无比率/失配议题。
- **P2（Kelvin 结构地板）**：相关度**无**（间接反向例：两电极夹持测量、无任何四端/比率结构，其精度上限由被测系统生物学决定，属另一世界）。
- **P3（衰减可达上界）**：相关度**无**。
- **方法学（增量四）**：相关度**低**。可取的一点是"有效测量窗口"论证范式：频带两端因系统误差（电极极化@低频、杂散电容@高频）+ 被测对象色散特性导致指标退化，中间存在最优工作频段且随时间漂移——与"门槛化方法学"（定义有效域并动态校核）形似，但对象是生物学频谱而非电路失配。
- **killRisk 判断：无威胁**。应用领域论文，与 P1/P2/P3 无主张交集。

## 没读到的
- Fig.1–3 的完整曲线数值（图不可读，正文只给极值点）。
- HP 4284A 的测量模式细节（Cs-Rp 并联等效之外的开尔文/两端夹具配置、电缆补偿是否启用——正文未述）。
- "D = 1/tan F" 中 F 取负角时 D 的符号约定（正文数值 D 恒正，疑取模，未明说，待核）。
