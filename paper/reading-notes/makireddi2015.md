# 精读笔记 · Makireddi 2015《Electro-elastic and piezoresistive behavior of flexible MWCNT/PMMA nanocomposite films prepared by solvent casting method for structural health monitoring applications》（Composites Science and Technology 118:101–107）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。

## 出处
- S. Makireddi, S. Shivaprasad, G. Kosuri, F.V. Varghese, K. Balasubramaniam, "Electro-elastic and piezoresistive behavior of flexible MWCNT/PMMA nanocomposite films prepared by solvent casting method for structural health monitoring applications," *Composites Science and Technology*, vol. 118, pp. 101–107, 2015. DOI: 10.1016/j.compscitech.2015.08.014. HAL / IIT Madras。
- PDF 7 页 = 印刷页 101–107（Elsevier 排版，文字层完整；"e"为连字符、µ 偶有丢失，涉处标待核）。
- 定位：**H6 应用域（MWCNT/PMMA 薄膜压阻传感）实验文**。测量链 = **手持式 Fluke 17B 万用表两线测量 + 银导电胶引线**——"测量环节商品化"的极端样本（手持 DMM 级）；无任何前端误差讨论。

## 核心命题（原文）
1. **总命题：MWCNT/PMMA 溶液浇铸薄膜的电气-力学-压阻行为，最高 GF 出现在渗流阈值处（p.101, Abstract）**：
   > "The percolation threshold for electrical conductivity is found to be 3 weight percentage of MWCNT. … Experimental results showed that addition of 10 weight percentage of MWCNT leads to a significant improvement in the tensile strength of PMMA by 291% and tensile strain by 122%. The piezoresistive behavior at different weight percentage of MWCNT is evaluated and highest gage factor of 4.37 is achieved at the percolation threshold."
2. **★测量链：手持 Fluke 17B 万用表、两线法（p.102, §2.1）**：
   > "The electrical resistance of the nanocomposite was measured by a Fluke 17B digital multi-meter using two-probe method."
   （一台手持 DMM 即全部测量硬件；**两线制明示，无四线选项**、无引线/接触电阻校正。）
3. **★梁上传感测量：两点探针 + 银导电胶 + 静载读数（p.103–104）**：
   > "A two-point probe was attached to the MWCNT/PMMA film using a silver conductive wire glue paste."（p.103）
   > "The change in resistance of the film with tensile load was measured and recorded at a crosshead displacement rate of 2 mm/min, held constant at definite loads for several seconds until a stable reading was obtained in the multi-meter."（p.104）
   （准静态人工读数：**"加载—保载数秒—等读数稳定"**——无连续采样、无动态测量，接触电阻全部进入读数。）
4. **应变基准：商品应变计四分之一桥（p.104）**：
   > "A conventional quarter bridge strain gage WK-13-125TM-350, with a gage factor of 2.08 ± 1% was attached to another specimen and given the same loading pattern to obtain the strain values."
   （应变侧是标准商品桥路；电阻侧是手持 DMM——域内"机械量精密、电测量随意"的典型不对称。）
5. **压阻机理：导电网络重构 + 隧穿距离变化（p.106）**：
   > "Change in resistance due to strain in the CNT/polymer nanocomposites occurs due to variation in the conductive network of CNTs, change in the tunneling resistance due to distance change in the neighboring CNTs and piezoresistive property of the CNTs."
   > "At the percolation threshold, this path is just formed and electrical conductivity increases significantly. If the film is strained at this point, breakage of conductive path occurs and a drastic change in resistance can be observed."（p.106）
   （渗流阈值处"通路刚成—应变即断—电阻剧变"——最大灵敏度在阈值处，与 DE-DRMS 网络损伤分级机制同源。）
6. **渗流区缓变非理论陡变（p.104, §3.2）**：
   > "Experimental results show that the raise in electrical conductivity near the percolation region is not as sharp as the theory envisages. This can be attributed to the uneven distribution of the MWCNTs in the polymer matrix."

## 关键数值（原文）
- 渗流阈值 **3 wt% MWCNT**（p.101/p.104）；文献范围 "an electrical percolation threshold from 0.005 to 11 weight percentage"（p.102）；单根 MWCNT 电导率 10⁷–10⁸ S/m（p.102）。
- 传感器电阻（p.105, Table 1）：**1/2/3/5/10/20 wt% → 23,966 / 10,670 / 3770 / 538 / 144.6 / 49.9 Ω**；CNT 涂料 131.2 Ω；商品应变计 351.2 Ω。
- 应变计系数 GF（p.105, Table 1）：**0.95 / 1.03 / 4.37 / 2.44 / 1.81 / 1.77**（1/2/3/5/10/20 wt%）；CARBOBYK-9810 CNT 涂料 **3.38**；商品应变计 **2.08±1%**（p.104）。最大 GF 比涂料/应变计高约 1.3/2.1 倍（p.106）。
- 电导率（Table 1, p.105）：0.7→150.4 S/m（1→20 wt%）。
- 力学（p.105）：10 wt% 时拉伸强度 +291%、模量 +103%、失效应变 +122%；杨氏模量 467 MPa（纯 PMMA）→951 MPa（10 wt%）。
- 加载：薄膜强度试验 1 mm/min @ 10 Hz 采样；压阻试验 2 mm/min（p.101, p.104）；膜厚 ~100 µm[原文 "100 mm"，µ 丢字待核]（p.102）。
- **无 CMRR / 接触电阻 / 噪声 / 不确定度指标——两线读数无任何误差预算。**

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：**无**。无电路、无激励源（DMM 欧姆档自带测量）、无直流/交流通道分析。
- **P2（Kelvin 结构地板）**：**低（取证价值高）**。明示 **two-probe method / two-point probe**（p.102, p.103）+ 银胶接触——域内测量链可缩到"手持 DMM 两线"的地板级样本；四线概念全篇未出现。这是 H6"测量环节全部商品化且两线通行"的最直接引文。
- **P3（衰减可达上界）**：**无**。
- **方法学（门槛化）**：**低**。GF 随掺量的单峰规律（阈值处最大）是材料设计结论；对照样（商品应变计 + CNT 涂料）同条件比较的做法可取，但无判据化。
- **killRisk 判断：无**。零电路内容，不可能触 P1/P2/P3；价值是 H6 现状证据（两线 + 手持 DMM + 准静态保载读数 + 传感器电阻 50 Ω–24 kΩ 量程域）。

## 没读到的
- Figures 4–7 曲线本体（图不进 OCR；数值以 Table 1 与正文为准）。
- 两线接触电阻（银胶/探针）对 GF 的系统影响——本文未讨论；若要量化须另行实验。
- 文中比较基线 CNT 涂料（CARBOBYK-9810, BYK）的规格书未读。
- 薄膜厚度原值（"100 mm" 疑为 100 µm，待核）。
