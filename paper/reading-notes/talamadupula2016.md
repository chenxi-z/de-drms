# 精读笔记 · Talamadupula 2016《2-Scale Hierarchical Multiscale Modeling of Piezoresistive and Damage Response in Polymer Nanocomposite Bonded Explosive》（ASME SMASIS2016-9234）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。

## 出处
- K. K. Talamadupula, A. K. Chaurasia, G. D. Seidel, "2-Scale Hierarchical Multiscale Modeling of Piezoresistive and Damage Response in Polymer Nanocomposite Bonded Explosive," *Proc. ASME 2016 SMASIS*, Stowe, VT, SMASIS2016-9234. DOI: 10.1115/smasis2016-9234. Virginia Tech（AFOSR FA9550-12-1-0205）。
- PDF 10 页 = 会议纸页 1–10（ASME 排版，文字层完整；公式有排版粘连段，不引用）。
- 定位：**H6 应用域（CNT-压阻自传感）——纯计算细观力学文**。全程有限元仿真 RVE，**无任何测量硬件、无前端、无实验电测**；对本轴的价值是"应用域工作重心在材料建模而非测量链"的极端样本（C 级，笔记从短）。

## 核心命题（原文）
1. **总命题：CNT 增强聚合物粘结炸药（NCBX）的有效压阻响应由纳米-微观两尺度模型预测，界面分离/损伤通过电流通路重构放大压阻响应（p.1, Abstract）**：
   > "This paper builds on previous work done [1, 2] to explore the effective piezoresistive response of polymer bonded explosive (PBX) materials where the polymer medium is reinforced with carbon nanotubes (CNTs). … The overall microscale piezoresistive effect is measured by using the volume averaged properties of the microscale RVE."
   （此处的 "measured" 是**仿真里对 RVE 做体积平均**，非电测——全文无一台仪器。）
2. **本构：局部电阻率线性依赖于局部平均应变（p.2, Eqn.1）**：
   > "The local resistivity of the nanocomposite is bolstered according to Eqn. 1, where GF represents the gage factor chosen and εavg is the local average strain."（Eqn.1: ρ = ρo(1 + GF·εavg)）
   另（p.4, Eqn.5 上下文）：
   > "The general relationship for a piezoresistive material relates the strain tensor to the relative change in resistivity, i.e. current strain resistivity minus unstrained resistivity (Δρ) normalized by the unstrained resistivity (ρ0)"
3. **★损伤→电流通路断裂→电阻跳变：结构损伤分级的传感物理（p.5）**：
   > "On application of larger strains, some of the current density pathways get completely severed because of cohesive zone damage resulting in smaller current densities across the interface. The evolution of the current density pathways in response to separating and damaging interfacial cohesive zones results in an effective piezoresistive response of the microscale RVE"
   （损伤前小斜率线性压阻、损伤后大幅跳变——与 DE-DRMS"网络损伤→电阻跳变分级"物理图像同构，且是仿真可控展示。）
4. **晶粒本身不压阻，宏观压阻全部来自 CNT 粘结相与界面（p.4）**：
   > "In the current study, it will be assumed that the explosive HMX crystals and sugar surrogate crystals are not inherently piezoresistive, i.e. all components of the piezoresistive strain tensor are zero. However, due to the piezoresistive nanocomposite binder and local interfacial separation/damage, the effective macroscale material demonstrates an effective piezoresistive response"
5. **仿真口径：均匀电场 + 平面应变 + 最大 0.1125% 拉应变（p.2）**：
   > "All simulations are performed till a maximum strain values of 0.1125% in tension in the x2 direction under a uniform electric field applied in the same direction."
   （"测量"边界条件 = 理想均匀电场，无引线/接触/仪表任何寄生——应用域建模文的典型理想化。）

## 关键数值（原文）
- 宏观应变计系数（损伤前斜率）：糖晶粒+0.5%CNT **GF≈5.13**（p.5）；HMX+0.5%CNT **GF≈5.72**（p.6）；(1000)(0.5)/(1000)(1.0)/(5000)(0.5)/(5000)(1.0) = **5.72 / 4.56 / 7.40 / 6.44**（p.7）；**损伤后"Extremely high macroscale gage factors are seen for all cases post damage initiation"**（p.7，无数值）。无 CNT 对照组 GF ≈ 0（p.5: "The gage factor obtained for this case is negligibly close to 0"）。
- 粘结相固有 GF 取 10（p.5: "A gage factor of 10 is taken to describe the inherent piezoresistivity of the nanocomposite binder"）。
- 材料参数（p.4, Table 1）：HMX E=15–31 GPa、ν=0.25–0.32、ρ=**100–5000 Ωm**；糖 E=27 GPa、ρ=10⁹ Ωm；环氧 ρ=10⁹ Ωm；环氧+0.5wt%CNT E=5.98 GPa、ρ=**0.0164 Ωm**；环氧+1.0wt%CNT E=7.25 GPa、ρ=**0.0107 Ωm**。
- HMX 晶粒损伤起始应变 ≈**0.03%–0.05%**（p.2）；RVE：31 晶粒、6055 单元、3967 节点、833 对界面节点对、晶粒体积分数 70%（粘结相 30%）（p.2, p.5）。
- **无任何测量硬件型号、无 CMRR/精度/噪声指标——无实验电测。**

## 对 P1/P2/P3 的对照
- **P1（消去条件）**：**无**。纯材料建模，无电路、无直流/交流通道、无消去结构。
- **P2（Kelvin 结构地板）**：**无**。无测量链（仿真边界条件为理想均匀电场，p.2）。对 H6 的取证价值：**应用域存在整篇无硬件的建模文——"测量环节商品化/不可见"的另一极端形态**。
- **P3（衰减可达上界）**：**无**。
- **方法学（门槛化）**：**低**。参数化研究（晶粒电导 × CNT wt%）+ 损伤前后两段响应的区分（损伤前线性小 GF / 损伤后大 GF）是一种朴素的"分级"叙事，但无判据化、无不确定性。
- **killRisk 判断：无**。与 P1/P2/P3 三主张零接触；仅作 H6 域材料侧背景（损伤→通路断裂→电阻跳变的仿真证据）。

## 没读到的
- Figures 4–9 的云图与曲线本体（图不进 OCR；数值以正文与 Table 1 为准）。
- 前作 [1] Chaurasia et al. 2014（实验表征 + 计算建模）、[2] Talamadupula et al. 2015（两尺度模型前篇）未读——内聚区电学定律的细节与实验对照在彼处；若需 H6"实验电测硬件"证据应改读 [1]。
- 损伤后 GF 的具体数值（正文只给"extremely high"，无数字）。
