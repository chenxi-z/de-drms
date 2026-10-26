# 精读笔记 · Dunfee 1963《Method for Calibrating a Standard Volt Box》（J. Res. NBS 67C(1), 1–13）

> 格式标准（全组沿用）：出处 → 核心命题（原文引用）→ 关键数值（原文）→ 对 P1/P2/P3 的对照 → 没读到的。
> 读法：pdftotext 全文逐节读，引用一律原文加页码；不转述成模糊话。
> 页码 = 期刊页（1–13）＝ PDF 页 1–13。扫描 OCR 本；引用仅合并断词空格，
> 公式区 OCR 噪声重处（式 (1)–(5)、(9)–(31) 多数）照实标注。

## 核心命题（原文）

1. **差分测量法（difference technique）**："The ratios of a volt box are measured against those of a standard using a 'difference' technique."（摘要 p.1）；实施是把电位差计以反压插进两箱对应端子间测小差值："The potential differences V1 and V4 are small since they are essentially the potential drops in leads l1 and l2; similarly, if the volt box under test is of high quality, potential differences V2 and V3 will be small. Thus only moderate accuracy is required in the measurement of the potential differences in order to realize an extremely high accuracy for the values of ratio."（p.2）
2. **引线压降的结构性消去（消去）**：fig.2 加滑线 R1/R2——"The potential drops in the two sections of branch l1, as well as those in branch l2, are in opposition so that it is only necessary to adjust the respective sliders to achieve cancellation, which is indicated by a null on the detector connected at the V1 and V4 positions … For this condition, the second term on the right of eq (5) becomes zero."（p.3）——差模引线项被**电路结构归零**，不是被匹配掉。
3. **泄漏 = 守卫等电位（绕开）+ 绝缘阻值硬指标**："if the total resistance of the high side is 250,000 ohms the resistance of a leakage path bridging this section must be 2.5×10^9 ohms for an uncertainty no greater than 0.01 percent, and 2.5×10^11 ohms if an error no greater than 1 ppm is required. This protection may not be adequate … Additional protection must be provided by a guard network which, in effect, maintains the shields surrounding the resistance sections at the same potential as that of the resistance section within."（p.3）；"Metal guard rings surrounding each binding post … prevent leakage across and through the top panel."（p.3）；引线自带屏蔽接守卫电位（p.3）。
4. **不对称处置 = 逐项误差预算（绕开/修正）**：
   - 湿度："seasonal variations as large as 30 ppm" → 干燥空气；1960 年新箱线圈密封后 "no measurable seasonal variations"（p.3）；
   - 自热："with double rated voltage applied, the correction differs from that at reduced voltage by less than 5 ppm"（p.4）；
   - DRRS 读数误差被差分法稀释（见数值栏 p.8）；基准式近似的误差 "is of second order"（p.8–9）；"Dummy" 电阻不准配误差 "is second order since it is the product of two small terms"（p.9）。
5. **杆电阻（rod resistance）是"最阴险"残差，四端接法才能根除（③核心）**："This source of error could be the most critical of any because of its insidious nature. Two errors must be examined … If the rod resistances are equal they can introduce an error if, when the standard volt box is used, the connections differ from those made during the process of calibration. The second error occurs if the rod resistances differ in magnitude."（p.9）；"the ratio in use differs from the measured ratio by an amount equal to the rod resistance divided by the total resistance of the range used and occurs even though the rod resistances are equal. **If the standard volt box were used as a 4-terminal voltage divider the above correction to the ratio would not be necessary** since l1 becomes part of the high voltage side."（p.10，着重为引者）；脚注 5："The influence of these rod resistances can be completely avoided by modifying the circuit so that the 50-ohm sections are measured as 4-terminal resistors. This technique is described in reference [2]."（p.5）
6. **自校准（bootstrap）链**："One of the most powerful measuring techniques available and one capable of the highest accuracy is that in which small differences are measured between like and nearly equal quantities."（p.4）；结构 "The first five sections of any group have nominally equal resistances while the sixth section has a value nominally equal to the sum of the first five."（p.4）——每组 5 等份 + 1 份=前 5 之和，逐组向上溯源到首段 50 Ω。

## 关键数值（原文）

- 精度目标："an accuracy of 10 parts per million or better using a Direct Reading Ratio Set and a group of resistance standards"（摘要 p.1）；结论 "good to an accuracy of 10 ppm or better"（p.10）
- 电压/阻值链：最大约 1,500 V；21 抽头，首段 0–0.15 V = 50 Ω，末段 250,000 Ω；333⅓ Ω/V（p.4）；每段 ≤25,000 Ω 独立绝缘板（p.3）；守卫电阻每段 = 工作电阻 0.8 倍、串 80 Ω（p.5 脚注 4/正文）
- 标准电阻组：50、200、500、2,000、5,000 Ω 各一 + 50,000 Ω 两只（p.5）；全标定 "in an hour by experienced personnel"（p.5）；最大耗散 0.45 W，可测至 200% 额定电压（p.5）
- DRRS：两臂约 100 Ω，A 臂 ±0.5%、最小步进 1 ppm，比较近等电阻精度 "about 1 ppm"（p.10）；一档 = 1 ppm = 10^-6 proportional parts（p.11）
- 误差稀释：每读数 +1 ppm 同向最坏情形，五段组内比误差 "For k = 5 the error would be 8/5 = 1.6 ppm"（通式 (k−1)²E/… OCR 噪声未读清）、两段组 "2E/2 = 1 ppm"、最高档合计 "only 9.4 ppm"；DRRS 自身修正 <0.3 ppm 随机分布 → "almost certain to be less than 1 ppm with no corrections applied"（p.8）
- 二阶项：β=0.1% × 500 ppm 只致 0.5 ppm（p.8–9）；Dummy 失配 500 ppm×500 ppm 只致 0.05 ppm（p.9）
- 漂移最坏：S 臂 50 Ω 每次 +0.0001 Ω 递增 → 该组比差 4 ppm（p.9）
- 杆电阻：NBS 新箱 0–6 V 段约 5×10^-4 Ω，随机符号，"maximum error they produce in a ratio measurement is less than 0.3 ppm"（p.10）
- 自热：双倍额定电压修正差 <5 ppm（p.4）；湿度历史波动 30 ppm（p.3）

## 三问专项

① **杂散/泄漏/不对称——消去还是绕开？** 泄漏：守卫等电位（shield 同电位 ⇒ 泄漏电压为零，p.3）+ 绝缘阻值上翻两个数量级（2.5×10^11 Ω @1 ppm）——本质是**绕开**（把泄漏路径的驱动电压做没）；引线压降：滑线反向抵消做**结构性消去**（p.3）；杆电阻/湿度/自热/DRRS 误差：**逐项定界 + 二阶小量论证**（p.8–10），不推导匹配条件。整体与 Cutkosky 两文同一路数：定义/守卫/对称相消，无"匹配消去"推导。
② **P1 反例搜索（无源 RC 差分网络失配→共模转差模的消去条件推导）**：**没有**。本文是纯直流电阻比网络，误差分析全为二阶微扰（"the product of two small terms", p.9）与差模引线项；最接近"差分对称消去"的是 fig.2 双滑线消 (V1+V4) 项（p.3），但那是**引线压降的差模对消**，不是共模经失配转差模的条件。结论：三篇 NBS 通读下来 P1 的"消去条件"在计量经典里**确属空白**（反例检索阴性）。
③ **四端对 ↔ Kelvin（P2 计量级原型论证）**：本文提供**电阻侧的原型判据**——(i) 电位箱校准时的杆电阻残差公式 "rod resistance divided by the total resistance of the range used"（p.10）＝Kelvin 意义下"电流端残阻进比值"的定量；(ii) "If the standard volt box were used as a 4-terminal voltage divider the above correction … would not be necessary"（p.10）＝四端定义根除该残差的正面陈述；(iii) 脚注 5（p.5）把 50 Ω 段改四端测即可 "completely avoided"，指到 Brooks NBS Mono.39 [2]；(iv) 校准与使用接法不一致本身成误差（p.9–10 fig.6）＝P2"定义端面与使用端面必须一致"的反面判例。与 1970 文 "The Kelvin bridge … currents exist in the potential leads … but cause no errors"（1970 文 p.65）互为直流/交流两翼。

## 对 P1/P2/P3 的对照

- **P1**：阴性对照第三件。三篇一致证明 NBS 传统处理不对称靠定义/守卫/对称相消/测量修正；本文的"二阶小量"论证法（p.8–9）可引为"失配效应若被设计成二阶乘积即无需消去条件"的工程替代路线——P1 可据此写"消去条件缺失时的第三种出路：把失配做成二阶"。
- **P2**：p.5 脚注 5 + p.10 的 4-terminal voltage divider 两句是**电阻比网络侧的计量级原型引文**（配合 1970 文 p.64–65 的原理段）；杆电阻"insidious nature"（p.9）适合做 P2 论证的动机句。
- **P3（AAF 衰减上界）**：无直接内容（本文纯直流比、无滤波器/频响分析）。唯一间接参照是自热/湿度等"带内慢变误差需测两点定界"的方法论，与 P3 无关。

## 没读到的

- 附录 A/B 的式 (13)–(31) 具体闭式：OCR 噪声未读清（推导链语义可辨：平衡方程 → 差值 → 组和 → 通式 (31) → N_m,k = N^s_m,k[1+μ_m,k]，末式尚可辨认于 p.13）；正文式 (1)–(5)、(9) 系数未读清。
- [1] Silsbee & Gross 1941 RP1419（原版电位箱与自校准法）、[2] Brooks NBS Mono.39 1962（**四端电阻测法原文**，脚注 5 指向）均无本地。
- 三接法（rod 位置三种方案）的误差比较推导只给结论 "figure 4a is preferred"（p.10），逐式 "Comparable sets of equations can be formed for the other two cases"（p.10）未展开。
