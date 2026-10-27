# 精读笔记 · Khalifeh 2022《Microcontroller Unit-Based Wireless Sensor Network Nodes: A Review》（Sensors）
> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> 本篇为 H6 应用域（C 级）证据：按主代理要求只查「测量硬件用什么、是否讨论前端误差/校准、四线/两线制」。

## 出处
- Khalifeh, A.; Mazunga, F.; Nechibvute, A.; Nyambo, B.M.，"Microcontroller Unit-Based Wireless Sensor Network Nodes: A Review", *Sensors* 2022, 22, 8937（MDPI，DOI 10.3390/s22228937；22 页）。**题录警示**：`literature.bib` 第 4 作者作 "Nyathi, T."，原文实为 "Benny Munyaradzi Nyambo"——bib 作者名与原文不符，待修。
- 文件（正文 txt 抽取，直接读）：`/home/anning/Documents/Obsidian Vault/20-硬件工程/10-项目设计/p1-文献谱系/fulltext/H6-CNT-SHM/khalifeh2022mcu.txt`。**目录警示**：本篇归在 H6-CNT-SHM/ 下，但内容是 WSN 节点平台综述，非 CNT-SHM 应用文献。

## 测量环节现状证据（本篇核心，H6 专查项）
- **测量链被压缩为"传感器接口电路"一句话**（p.3 of 22，Sensing Sub-System 全节）：> "Sensors convert physical phenomena into electrical signals [5]. Therefore, the sensing sub-system links the node to the environment. Digital or analogue signals are obtainable from the sensors. The sensors' interfacing circuit enables the microcontroller to process the detected signals."（接口电路如何处理信号——调理/ADC/校准——全篇无一字。）
- **测量硬件 = 商品化即插板卡**（p.12 of 22，MICAz 商用 mote）：> "The mote can accommodate a number of different sensor and data acquisition boards through a standard 51-pin expansion connector. In addition, custom sensor boards are also offered."（"sensor and data acquisition boards" 是全文对测量硬件的全部称呼——DAQ 板卡即测量环节。）
- **前端误差/校准：grep `calibrat` 全文零命中**；`amplifier / ADC / Wheatstone / bridge / analog front` 亦零命中（仅 "data acquisition" 命中 3 处板卡描述）。四线/两线制无涉。
- 综述比较维度全在数字侧：> "The sensor nodes from the recent research articles are compared with the most widely used commercially available motes based on processing and memory specifications, communication capabilities, power supply and consumption, sensor support, potential applications, node programming and hardware security."（p.20 of 22，结论——七个维度里没有测量精度/前端误差。）

## 核心命题（原文）
1. **节点四大子系统的架构观**（p.3 of 22）：> "A basic wireless sensor node consists of the sensing (sensors interfacing and sensors), computation (a microcontroller), communication and power supply sub-systems as depicted in Figure 1."（感知子系统在架构层面与计算/通信/电源并列，但后续全部篇幅在计算/通信/电源。）
2. **商用 mote 的选型准则同样是平台指标**（p.4 of 22）：> "The commercially available motes (MICAZ, IRIS, LOTUS, WiSense and Waspmote Plug & Sense!) were selected for comparison in this study based on a number of criteria including popularity, published results and interesting characteristics and features."
3. **可靠性只以"测得可靠"一句带过，无精度理论**（p.19 of 22）：> "Reliable motes that give reliable measurements and do not often fail should be developed. These motes have to be robust against environmental changes by operating under different temperature, pressure, moisture and weather conditions without their accuracy being affected."（"accuracy"出现的环境是环境鲁棒性，不是前端误差预算。）
4. **未来趋势清单不含测量前端**（p.19 of 22，Challenges and Future Trends）：> "Some of the critical features and characteristics that should be considered by designers of wireless sensor nodes are ultralow power consumption, affordability, small physical size and software and hardware configurability."（挑战 = 功耗/成本/尺寸/可配置性/安全。）

## 关键数值（原文）
- 全部为节点平台指标，与测量链无关，择录：Jennic 压电节点 16 MHz JN5139、96 kB RAM、192 kB ROM，> "The piezo-based sensor node consumes a maximum current of 37 mA at 3.6 V supply. The sleep current of the node is 2.6 μA when the sleep timer is ON."（p.14 of 22）。
- 地震监测节点（p.14 of 22）：> "the node accommodates a three-component seismic sensor (Mark-l-4C3D) having a natural frequency of 1 Hz"（传感器只报型号与本征频率，信号链不提）；> "the node draws 70 mA and 80 mA of current in the standby and sampling modes, respectively."
- MCU 选型趋势（p.14 of 22）：> "from 2019 to 2022 the ARM Cortex series of MCUs have been dominating in most of the recent wireless sensor nodes reviewed in this paper."

## 对 P1/P2/P3 的对照
- **P1**：C 级空白侧证（WSN 平台域）——节点综述对模拟测量前端零讨论，传感链默认由商用板卡/内置 ADC 解决；支撑"应用文献视测量环节为已商品化"的判断。
- **P2**：无关。
- **P3**：无关。
- **方法学**：其平台比较框架（功耗/通信/内存/安全）与门槛化方法学无交集。
- **killRisk：无威胁**。理由：纯 WSN 平台综述，与 P1 三条主张及前端电路理论零交集；对 P1 仅作空白侧证使用。

## 没读到的
- Figure 1/2 与 Table 1/2 的图形内容未核（txt 抽取只有图片占位符）；Table 1 中各 mote 的具体传感器支撑列可能含个别测量器件型号——如需引用再核原文 PDF。
- 2016–2022 各节点分节（3.1–3.5）按 H6 快读原则只抽了传感/DAQ 相关句，其余为功耗/通信细节，未逐条录。
