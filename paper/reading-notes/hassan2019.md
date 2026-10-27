# 精读笔记 · Hassan 2019《Failure prediction in self-sensing nanocomposites via genetic algorithm-enabled piezoresistive inversion》（Structural Health Monitoring）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> H6 轴定位：CNT-SHM 应用域 C 级证据。要点 = 测量硬件（Keithley 6221 源表 + NI PXIe-6368 DAQ，全商品化）；接触阻抗只作为 EIT 正问题模型项（complete electrode model），非硬件误差项。页码 = 印刷页码（SAGE 排版 1–16，PDF 页与文页一致；PDF 共 17 页含末页广告）。

## 出处
- Hassan, Tallman. "Failure prediction in self-sensing nanocomposites via genetic algorithm-enabled piezoresistive inversion." Structural Health Monitoring 2019 (OnlineFirst 00(0)). doi:10.1177/1475921719863062。
- bib key：`hassan2019`。

## 核心命题（原文）
1. **核心主张：从"检测损伤"升级为"预测失效"——GA 反演压阻变化得位移/应变/应力，再加失效准则**（p.1 摘要）：
   > "Our approach makes use of a genetic algorithm (GA) to determine the mechanical state of the structure using conductivity changes observed via EIT. ... Lastly, a failure criterion is used to predict failure. By validating our results with finite element analysis and digital image correlation, we demonstrate that the proposed approach can accurately predict the onset of failure..."
2. **测量链 = 商品源表 + 商品 DAQ（无自制前端）**（p.9）：
   > "Electrode connections were made to a current source (Keithley 6221) and a DAQ system (National Instruments PXIe-6368) to measure the electrode voltages. The current used had a magnitude of 10 mA."
3. **激励/测量制式：对面电极对注流、其余对面电极对测压（EIT across 注入方案）**（p.3）：
   > "The domain to be imaged is lined with electrodes. Current is injected between the first opposing electrode pair and the voltages between the remaining opposing pairs are measured. The current injection is then shifted to the next opposing pair..."
   （激励与测量电极在时序上分离（互异电极对），但物理引线仍是同一套铜电极——非 Kelvin 四线电阻测量范式。）
4. **接触阻抗进入的是正问题模型（CEM 边界条件），而非仪器误差预算**（p.3）：
   > "Next, we enforce the complete electrode model boundary conditions on equation (1). The first boundary condition assumes a voltage drop across the electrodes due to contact impedance between the electrodes and the domain, as shown in equation (2)."
   （这是数学建模层的处理；全文无万用表/前置放大器级误差、失调、增益、CMRR 讨论——已 grep 确认。）
5. **电极制作：银胶斑块 + 铜胶带引出 + 美纹胶带保压**（p.6）：
   > "Electrodes were applied by first painting colloidal silver patches measuring 3.175 mm along the gauge length of the specimen on either side of the hole. Next, copper tape with extended tabs was applied to the silver patches to act as electrodes."
6. **结论：该方法的增量在于给出力学状态而非仅损伤定位**（p.13）：
   > "The novelty of this approach is that while prevailing SHM seeks only to localize damage using conductivity changes, GA-enabled piezoresistive inversion can determine the underlying mechanical state and allow for accurate damage prediction capabilities."

## 关键数值（原文）
- 注流幅值 10 mA（Keithley 6221，p.9）；基线电导率 σ0 = 4.857×10⁻⁴ S/m，反演得 nanofiller 质量分数 w = 1.26%（p.9）。
- 失效位移 uF ≈ 0.8 mm；加载取 31%、62%、93% uF 三档（p.9）。
- 试样：中央带孔矩形 CNF/epoxy 试件，模压厚 4 mm；加强片 57×46.5×1.72 mm（p.6）。
- 银电极斑块 3.175 mm（p.6）；DIC 相机 5 MP（Correlated Solutions），拉伸速率 1.5 mm/s（p.9）。
- CNF 形貌图取 2.0 wt% 断口（图 3，p.6）；弹性模量 E = 2.534 GPa（p.5）。

## 对 P1/P2/P3 的对照
- **P1（G_DC≡0 元件条件）**：无前端级误差分析。Keithley 6221+PXIe-6368 被当理想源/理想表使用；唯一"误差项"（电极接触阻抗）被吸收进 EIT 正问题物理模型（CEM，式 2），属建模而非仪器校正——P1 空白侧证成立。
- **P2（Kelvin 结构地板 ≈56 dB）**：无。无两线/四线制讨论；EIT 多电极注流-测压在功能上分离了电流与电压通路，但论文从未从"引线/接触电阻引入误差"角度讨论该分离的测量学收益。
- **P3（衰减可达上界）**：无。准静态加载（1.5 mm/s），无带宽/漂移/衰减议题。
- **方法学（门槛化）**：与"分级监测"正相关：以失效准则（应力状态 vs 强度）给出失效预测，等效于"阈值化 = 反演出的力学状态 + 失效判据"，比 R/R0 直接阈值更高级一层。但阈值本体（强度值）来自材料表征而非测量链分析。
- **killRisk**：无（不触碰 P1/P2/P3；反证应用域文献把前端当黑箱）。

## 没读到的
- Keithley 6221 / PXIe-6368 的量程、精度、采样率、扫描时间：原文未给。
- 前置放大/滤波/防混叠：无（已 grep）。
- CEM 接触阻抗 zl 的取值或辨识方法：式 (2) 引入但未给数值（待核是否在后文/补充材料——正文未见）。
- 四线制（four-wire/4-wire）字样：全文无。
