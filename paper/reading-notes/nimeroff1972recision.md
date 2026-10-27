# 精读笔记 · Nimeroff 1972《Precision Measurement and Calibration: Selected NBS Papers on Colorimetry》（NBS SP 300 Vol. 9）

> 2026-10-27 补件更新：SP300 电学 v3（1968）和 v4（1970）已从 NIST 官方补齐（nbs1968sp300v3 / nbs_sp300v4）。以下为此前色度卷异常记录；目标篇尚待在新电学卷内定位并精读，不再标整个电学卷缺件。
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> 页码口径：**卷印刷页（PDF 物理页）**；PDF 页 ≈ 印刷页 + 18（§4.5 段经页脚双页码核实）。
> **结论先行：本卷是色度学卷，未在卷内定位到任何与变压器比例臂电桥 / 量子-数字桥 / Kelvin 四端计量相关的目标论文**——bib 题录（DOI 10.6028/nbs.sp.300v9）即整卷，卷内 37 篇重印全部属 Colorimetry and Spectrophotometry。真正的电学卷为 SP300 Vol 3 / Vol 4（见下方目录证据），不在本库。

## 出处
- NBS Special Publication 300, Vol. 9, "Selected NBS Papers on **Colorimetry**", Isadore Nimeroff, Editor, Institute for Applied Technology, issued 1972。DOI: 10.6028/nbs.sp.300v9。
- 扉页（PDF p.5）："Precision Measurement and Calibration / Selected NBS Papers on / **Colorimetry** / Isadore Nimeroff, Editor … NBS Special Publication 300"。
- Abstract（PDF p.6，逐字）："**Volume 9 treats the field of Colorimetry. It contains 37 re- prints on Colorimetry and Spectrophotometry assembled in 8 sections: (1) Spectrophotometry, (2) Color Vision, (3) Color Specification, (4) Sources and Instrumentation, (5) Color Spac- ing and Metamerism, (6) Variabilities and Uncertainties, (7) Appearance and Gloss, (8) List of Publications…**"——八节均为色度学，无电测章节。
- PDF 共 469 页。OCR 质量中下（扫描倾斜、公式/希腊字母多损），以下引用逐字照录并标 [OCR损]。

## 目录证据（卷首系列页逐字摘录，PDF p.2 "Volumes available or to be published in the NBS Special Publication 300 series"）
> "SP300, Vol. 2, Temperature, J. F. Swindells, Editor, Aug. 1968, 520 pages"
> "**SP300, Vol. 3, Electricity — Low Frequency, F. L. Hermach and R. F. Dziuba, Editors, Dec. 1968, 498 pages**"
> "**SP300, Vol. 4, Electricity — Radio Frequency, A. J. Estin, Editor, June 1970, 450 pages**"
> "SP300, Vol. 5, Frequency and Time, B. E. Blair and A. H. Morgan, Ed [OCR损，跨行]"
（变压器比例臂、比率计量、阻抗电桥的系统 treatment 应在 Vol 3 / Vol 4——**本库未收**。）

## 核心命题（原文，仅卷内与「滤波器逼近目标函数」相关的两篇）
1. **滤色片是设计者唯一能充分控制的逼近手段（P3「滤波器形状匹配」的光学同构物）**（p.313 / PDF p.331，§4.5 Emara & Teele《Development of Filters for a Thermoelectric Colorimeter》）：
   > "The only parts of a colorimeter over which the designer can exercise much control are the filters used to modify the detector response to obtain the x, y, and z functions of the CIE standard observer. The x function is bimodal and therefore two filters are used [OCR损，跨栏断句]"
2. **逼近精度的前提 = 探测器非选择性（响应一致性才值得做最佳逼近）**（p.312 / PDF p.330，同篇摘要）：
   > "Filters have been designed for use with photocells and phototubes in tristimulus colorimeters, but because of the variation in spectral response of these detectors from one to the other, it has not been worthwhile to attempt to achieve the best possible duplication of the CIE tristimulus functions. In the case of a thermoelectric detector, however, the response is so nonselective that the same filter designs can be used with any thermopile."
   （ detectors 一致性差 → 逼近无意义；热电堆非选择性 → 同一滤片组可复用。与 P3「约束下逼近目标响应」同构，但**与衰减上界无关**。）
3. **玻璃滤片厚度设计方程（Beer–Lambert + 反射修正）**（p.307 / PDF p.325，§4.4《A Colorimeter for Pyrotechnic Smokes》）：
   > "The filter design is accomplished by determining the proper combination of colored glasses. Where the transmittance, T0 of a glass of stock thickness d0 is to be changed to a transmittance, Tu [OCR损，=T1], the fol- [OCR损，跨栏]"

## 关键数值（原文）
- 本卷无任何电阻/比率/电桥不确定度数值。§4.5（p.313 / PDF p.331）："Three identical cells with 1-mm thick windows and 50-mm spacing were selected… the windows were nonselective in transmittance from 380 to 780 mµ [OCR损，=nm] except for variations less than **1.5 percent**."

## 对 P1/P2/P3 的对照（全文关键词审计结果）
- **全文命中审计（pdftotext 全文，逐词核对上下文）**：`common mode / common-mode / CMRR / Wheatstone / ratio arm / transformer / attenuat*` 均 **0 命中**；`bridge` 27 处全部为地名 **Cambridge**；`Kelvin` 6 页命中全部是**色温单位**（"temperature in degrees Kelvin"，PDF p.125/190/209/254）；`mismatch` 6 页命中全部是**视觉色失配/metamerism**（PDF p.122/166/176/344："…indexes to represent the degree of metamerism (spectral mismatch)…"）；`guard` 唯一命中为 "Coast Guard"（PDF p.295）；`shield` 唯一命中为 "light with a black shield"（PDF p.294）。
- **P1 消去条件**：无。本卷不构成 P1 的出处或反例（无任何电气网络内容）。
- **P2 结构地板**：无。无电桥、无比率器件、无屏蔽接地电气实践（仅光学/视觉文献）。
- **P3 可达边界**：命题 1–3 是「用物理滤波器逼近规定响应函数」的光学设计记录，可在 Discussion 中作同构先例一句带过，**不承载任何衰减-上界论证**。
- **killRisk 判断**：无威胁。与 P1/P2/P3 均无交集；卷册身份与任务预期不符（疑似选题时把 SP300 系列卷号与电学卷混淆），引用时应改投 Vol 3（Hermach & Dziuba, *Electricity—Low Frequency*）。

## 没读到的
- **目标论文本身未定位到**——本卷目录（PDF p.2 系列页 + PDF p.6 Abstract 八节清单）与全文关键词审计一致表明卷内无电计量内容；如需比率臂/量子化比率谱系，须取 SP300 Vol 3 / Vol 4 或本库已有的 Cutkosky 1961/1970、Dunfee 1963 单行本。
- 卷内其余 34 篇（色视觉、色空间、光泽、CIE 术语文献）仅做关键词扫描，未逐字精读。
- §4.4/§4.5 的滤片透过率曲线与三刺激值逼近误差图（desired/expected/actual 三曲线）为扫描图版，OCR 无文字层，未读出数值。
