# 精读笔记 · Swindells 1968《Precision Measurement and Calibration: Selected NBS Papers on Temperature》（NBS SP 300 Vol. 2）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> 页码口径：**卷印刷页（PDF 物理页）**；PDF 页 = 印刷页 + 12（卷扉页 PDF p.5）。
> 注：本卷是**温度**论文合订本（非电学卷）；任务所warning「目标论文只是其中一篇」不适用——bib 题录即整卷（DOI 10.6028/nbs.sp.300v2）。真正的电学卷 Vol 3《Electricity—Low Frequency》（Hermach & Dziuba）不在本库（卷首 Preface 12 卷目录为证，PDF p.8）。

## 出处
- NBS Special Publication 300, Vol. 2, "Selected NBS Papers on **Temperature**", J. F. Swindells, Editor, Issued August 1968。DOI: 10.6028/nbs.sp.300v2。
- 扉页（PDF p.5）："Precision Measurement and Calibration / Selected NBS Papers on / Temperature / J. F. Swindells, Editor … NBS Special Publication 300 — Volume 2 / Issued August 196S"（末词 "196S" 为 OCR 损，实为 1968）。
- PDF 共 537 页（含空白封面）；正文为 NBS 论文原样重印，双页码（卷页-原刊页，如页脚 "121-141"）。
- Preface（PDF p.8）列 SP300 十二卷规划，其中 "**Electricity— Low Frequency, F. L. Hermach and R. F. Dziuba**"（=Vol 3）、"Electricity Radio Frequency, A. J. Estin"（=Vol 4）——本卷不含电桥/比率计量专章，相关内容散见于电阻测温各篇。
- OCR 质量中等：Ω→"fl/Mfi"、µ→"^/pt/fi"、断词常见（"hridge"=bridge、"acciiracy"=accuracy、"ehminates"=eliminates）；以下引用逐字照录并标 [OCR损]。

## 核心命题（原文）
1. **比率是电阻测温的精度载体**（p.121 / PDF p.133，Stimson《Precision Resistance Thermometry and Fixed Points》）：
   > "Precision resistance thermometry with a standard resistance thermometer, therefore, depends upon the precision and accuracy with which **these ratios** can be determined.."
   （温度由 R_t/R_0 之比定出，精度=比率测定精度。前句原文："…provide the means for determining an unknown temperature relative to the ice point temperature from a determination of the ratio of two resistances of the thermometer"。）
2. **换向消引线电阻的成立条件（最接近 P1 的"消去条件"句式）**（p.152 / PDF p.164，《Notes to Supplement Resistance Thermometer Reports》）：
   > "The function of the commutator is to interchange the thermometer leads in such a way that the average of the resistances measured with the commutator in the N (normal) position and in the R (reverse) position is the resistance of the resistor of the thermometer. **The resistance of the leads is completely eliminated by this technique only if the difference in the resistance of the two leads appearing in the arms of the bridge is the same when measurements are made in the N as when measurements are made in the R position.** By making a series of four measurements, at equal time intervals, in the order N R R N, any change of the difference of the lead resistance is computable and the average value of the four measurements is independent of any linear drift in this difference."
   （显式等值条件：**两引线电阻之差在 N/R 两态下不变 → 完全消去**；外加 N-R-R-N 等间隔四读数消线性漂移。"computable" 系 OCR 原样，疑为 compensated/compensable，待核纸本。）
3. **比率臂失配经同步反向被压制 10³ 倍**（p.131–132 / PDF p.143–144，Stimson "Bridge Developments"，Mueller 退休后设计之桥，Hoge 建议）：
   > "One new feature in the commutator switch is the addition of an extra pair of mercury-contact links which serve to reverse the ratio coils simultaneously with the thermometer leads. This feature was suggested by Hoge, who was then at the National Bureau of Standards. This feature automatically makes the combined error of the normal and reverse readings only one in a million, for example, when the ratio arms are unequal by as much as a part in a thousand, and thus prac- [OCR损，跨页] tically eliminates an error from lack of balance in the ratio-arms. It does not eliminate any systematic error in the contact resistance at the end of the ratio arms on the decades, however, because the mercury reversing switch has to be in the arms."
   （不是"匹配到零"而是**对称反向求和消差**：失配 10⁻³ → 正反合计残差 10⁻⁶；且明确**残余项**——十进盘端接触电阻——不在消去范围。）
4. **比率测量使单位误差共模约去**（p.153 / PDF p.165）：
   > "Since only ratios of resistances are required to determine temperature, the units may be absolute ohms, international ohms, or any arbitrary unit; but the calibrated bridge (or potentiometer) must be self-consistent."
   （同链测分子分母 → 单位/绝对误差在比值中约掉，只需桥**自洽**。同页前段 [OCR损]："The acciiracy of temperatures determine from values of R, /R obviously IS not limited by the uncertainty of the resistance units if the values of R^ and R are determined in the same units."）
5. **比率臂阻值放大以稀释接触电阻**（p.131 / PDF p.143）：
   > "He has made the resistances of the ratio arms 3000 ohms so that the uncertainty of contact resistance, 0.0001 ohm, produces an uncertainty of only one part in 30,000,000. With 30 ohms, for example, in each of the other arms of the bridge, these two ratio-arm contacts should produce an uncertainty of resistance measurement of 1.41 microhms."
6. **桥校准前先把比率臂调平**（p.156 / PDF p.168）：
   > "Before beginning the bridge calibration the ratio arm should be adjusted to equality. This adjustment of the ratio arms is necessary because the 0.1 ohm decade is not in the same arm of the bridge as the other decades."
7. **Johnson 噪声地板与"未解之谜"**（p.132 / PDF p.144）：
   > "…the magnitude of the Johnson noise in a circuit including an instrument having a one-second period would be of the same order of magnitude as an unbalance of 1 microhm in the measuring arm of a bridge when one milliampere was flowing in a 25-ohm thermometer. In practice there seems to be a discrepancy between this limit and what we realize. We have found that for a net time of over a minute of observing, for observations at 1.5 and 2.5 ma to extrapolate to zero current, the determinations of the resistance of thermometers in triple point cells have a standard deviation of a single determination of about 8 microhms. … it remains one of the unsolved problems of precision resistance thermometry."
8. **双电流外推零电流（自热消去）须控电流比**（p.127 / PDF p.139）：
   > "In striving for a precision of a few microhms in the determination of the resistance e.xtrapolated [OCR损=extrapolated] to zero current it is necessary to control carefully the ratio of the currents used for the measurements and to consider the variance of the measurements at each of these currents."
9. **等温结对消热电势**（p.163 / PDF p.175，Evans & Burns）：
   > "The copper to platinum junctions are located side by side in a small piece of four-hole porcelain tubing which is surrounded by a close-fitting copper sleeve. In this manner the junctions are kept at nearly the same temperature, thereby reducing thermal emf in th [OCR损，栏末=the thermometer]."
10. **双层接地铜屏笼消 RF 焦耳热（P2 谱系原句）**（p.189 / PDF p.201，锗电阻低温标定篇）：
    > "A lead from one of the sheets is connected to a surrounding screen cage which is at earth potential. The double-wall, copper-screen cage completely encloses the d-c measuring apparatus and ehminates [OCR损=eliminates] a-c joule heating that is caused by signals which emanate from nearby commercial transmitters [14]."
    （守卫/屏蔽的目的：外来 RF 在电阻上整流/发热 → 直流漂移；**屏蔽先于匹配**。）
11. **Hartshorn 互感电桥（变压器/互感比例臂一类，全卷唯一一处）**（p.101 / PDF p.113，CMN 磁温度计篇）：
    > "The CMN specimen formed the core of a mutual inductance which could be measured by means of a Hartshorn bridge [l4] normally operated at 267 H [OCR损，=Hz]. … The minimum detectable bridge unbalance was 0.002 turn at 25 mA primary current (equi- valent primary field =0.75 x 10"* [OCR损] tesla) which corresponds to ± 0.01° at 4°K, ± 0.003° at 2°K, and 0.0008° at 1. 1°K."
    （比率载体是**互感匝**——"bridge turns"，最小可分辨 0.002 匝；这是本卷里最接近"结构性比率"的器件，但仅此一处、无电路细节。）

## 关键数值（原文）
- 换向消差倍率：比率臂失配 1/1000 → 正反读合计误差 1/10⁶（p.131–132 / PDF p.143–144）。
- 比率臂 3000 Ω + 接触电阻 0.0001 Ω → 1/30,000,000；另两臂 30 Ω 时该两触点 → 1.41 microhms；百分欧姆盘零位 → 0.4 microhm（p.131 / PDF p.143）。
- Mueller 型桥（新版）：量程 "0 to 422 ohms in 1 microhm steps"（p.164 / PDF p.176）；第七十进盘一步 ≡ 10 microhms，设计不确定度 "not exceeding two or three microhms"，汞触点 <1 microhm（p.131 / PDF p.143）。
- 噪声地板：dV = 1.12 × 10⁻⁹ √(Rτ)（OCR 作 "1.12 X 10-'"\/Wr"，[OCR损]）@300°K；实测单次标准差 ≈ **8 microhms**（1.5/2.5 mA 外推零电流，三相点瓶）vs 理论 ≈1 microhm @1 mA/25 Ω/1 s（p.132 / PDF p.144）。
- 水三相点复现：内熔法 "within about 0.00008°C"（p.135 / PDF p.147）；三相点 ±0.0002 °C vs 冰点 "five to ten times worse"（p.152 / PDF p.164）。
- 锗电阻标定：测量电流 1–2 µA，由两只 50,000 Ω 分压器并联供电（OCR "2 fiA…50,000 fl voUage dividers"，p.189 / PDF p.201）；绝缘电阻日常测到 "10 MΩ — the limit of a portable Wheatstone bridge"（OCR "10 Mfi"，p.184 / PDF p.196）。
- Hartshorn 桥：267 Hz、初级 25 mA、最小可辨失衡 0.002 匝 → ±0.01°@4 K / ±0.003°@2 K / 0.0008°@1.1 K；1 bridge turn = 3.06 µH（OCR "3. 06 pH"，[OCR损]，p.101 / PDF p.113）。

## 对 P1/P2/P3 的对照
- **P1 消去条件**：本卷无 a/b=A/B 式定理，也无 RC 网络共模转差模内容；但命题 2 给出计量学谱系里最工整的**消去条件句式**——"only if the difference … is the same when …"（结构失衡在两个对称态下不变 → 精确消去），与命题 3 的**对称反向把失配从 10⁻³ 压到 10⁻⁶**。P1 的"全频段精确消去"可以此为历史原型：NBS 传统用「对称态+平均」绕开元件匹配，而非匹配元件本身。
- **P2 结构地板**：命题 10（双层接地铜屏笼消 RF 焦耳热）+ 命题 5/6（比率臂 3000 Ω 稀释接触电阻、校准前调平）+ 命题 11（Hartshorn 互感桥、0.002 匝分辨）是可直接引用的 NBS 原句；Kelvin-type double bridge 仅提名一次（p.152 / PDF p.164："The resistance may also be measured with a potentiometer and a stable reference resistor or with a Kelvin-type double bridge."），无电路细节。变压器比例臂的系统论述在 Vol 3（本库无）。
- **P3 平坦度约束衰减上界**：无内容（attenuat* 命中均为热/光衰减）。
- **killRisk 判断**：无威胁。本卷是电阻测温/温度计量谱系，不涉及 P1 的 RC 差分失配命题；其价值在为 P2 提供「屏蔽+对称换向+比率约去」的 1960s 计量原语，引文需注明对象是直流测温电桥。

## 没读到的
- 真正的电学卷 SP300 Vol 3《Electricity—Low Frequency》（Hermach & Dziuba）与 Vol 4（Estin）不在本库——变压器比例臂、Wagner 接地、guard 电极的系统 treatment 应在 Vol 3。
- 本卷仅精读上列页段；未逐字精读：插值篇（印刷 169–177）、光学/光谱测温篇、两篇测温书目（印刷 447–510）。
- 《Notes to Supplement Resistance Thermometer Reports》为 NBS 1963 报告重印、无期刊出处；"computable" 一词 OCR 存疑，引用前宜核纸本。
- Hartshorn 桥句中 "0.75 x 10"* tesla"（=10⁻⁴?）与 "3.06 pH"（=µH?）OCR 受损，数值引用前需核原件。
- 旧合卷笔记（H7_nbs_sp300_v2v6v9.md）曾引锗电阻篇"thermal emfs … eliminated"一句，本次在印刷 p.184–185 附近未再定位到该逐字句，**放弃引用**（待核）。
