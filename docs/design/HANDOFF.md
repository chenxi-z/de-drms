# 当前交接（2026-10-28）

先读设计README、主文档附录F、当前引脚表和CubeMX清单。
用户确定直流首板+扫频预留，图纸由用户修改。

**2026-10-28 变更（覆盖下方全部旧引脚/温度/TF电源描述）**：
- **MCU 改 STM32U575RGT6**（U545RET6Q 缺货）。同 LQFP-64；**PC4=CURR_DIS、PC5=PWR_BTN、
  PB0=SEL_K2、PB1=SEL_SENSE**（24–27 脚改名，走线未变）；**VCAP(30) 接 2.2 µF（C4）**；无 SMPS。
- **不做 I²C / 无 TMP117**（PB6/PB7 NC）。
- **TF 卡常电**，取消 SD_PWR_EN（PA8 NC）。
- **PA4 = ADS_CS，不作 DAC**。
- 权威引脚表 = `docs/design/pin-assignment.md`（按 PCB 焊盘实测重写）。

历史性能不得当作已验收；不需在云端重跑LTspice。原始仿真报告保持原判定。
以下旧交接全文仅为历史，不能复制其中旧引脚/电源/AAF作为新实现指令。

---

# 交接提示词

本文件存放用于**开启新会话**的交接提示词。分别对应两条线：
设计线（继续硬件/固件设计）与 Obsidian 归档线（器件手册整理）。

---

## 一、设计线：继续 DE-DRMS 硬件设计

> 复制以下整段作为新会话的首个提示词。
> **最后同步：2026-10-14**（引脚全表重排 + TF 记录子系统 E.11 + **二轮复核：DS14216 全表逐行核，4 处换脚 / BC1.2 反转 / 低功耗数值更正，E.10 #12 全清**）

```
# 任务：继续 DE-DRMS 双电极电阻测量仪的硬件设计

## 先读这些（按顺序）
1. /media/anning/data/Project/DE-DRMS/docs/design/README.md   ← 文档索引，先读它
2. 同目录 2026-10-10-universal-signal-chain.md               ← 主设计文档
   - 附录 D = 应用需求与指标（需求来源）
   - 附录 E = 硬件实现定稿（E.1–E.11；**硬件以 E 为准**；与 D 冲突时以 E 为准）
   - **E.11 = TF 卡数据记录子系统（2026-10-14 新增）**
3. 同目录 pin-assignment.md                                  ← 引脚分配总表（2026-10-14 重排定稿）
4. /media/anning/data/Project/DE-DRMS/firmware/DE-DRM/CUBEMX_SETUP.md ← CubeMX GUI 配置清单
5. 仓库根 AGENTS.md                                          ← 工作规约、硬约束、被否方案清单

## 项目背景
- 仪器：双电极直流电阻测量仪，用于**两端 MWCNTs 导电网络传感层**的结构损伤分级监测
- 被测对象：两端电阻条（导电银胶 + 铜电极引出）
- 基线 R₀ 10–20 kΩ（每次实测、编程可设）；损伤时升至 ~120 kΩ（R/R₀ ≈ 6×）
- 精度：**R₀ 的 1%**；输出绿/黄/橙/红四级判定（**阈值留空，待标定**）
- 温度补偿**必须做**：材料温度系数 −4 ~ −10 %/℃，远超 1% 指标

## 已定稿（无新依据不要推翻）
- 拓扑：**恒流激励 + 双通道同步实测**（恒流测电阻，**不做电桥**）
- 激励：**8 µA** 恒流，Rsense = **150 kΩ 0.1%**；恒流源 OPA333 + BSS138（低边拓扑）。
  **2026-10-14 终审封存**（OPA391/Howland/LM334/REFEXT 全数评审，见 hardware/sim/ccsource README + E.2.1）
- ADC：**ADS131A02**（2 通道同步、24 bit、128 kSPS、**内部 2.442 V 基准**、3.3 V 直连）；
  采样策略：**冲击全程 128 kSPS 采满、按需数字降采样**（E.4.3）
- 前端：**3 颗跟随器 OPA388**（T、M、B 三线；AIN1N 直接经 RC 接 Rsense 底端）；
  T 点顶端偏置 R_top 10 kΩ / R_b 150 kΩ（E.2）；保护 BAV199（默认）/ 低漏电 ESD 阵列（备选焊盘）；
  抗混叠 = 每线 **B 案三级阶梯** 6.19 Ω+68 nF → 6.04 Ω+68 nF → 13.7 Ω+27 nF（对地）+ 末级 12 nF 差分，
  fc≈80 kHz（E.4.4，2026-10-19 定版；旧 1 kΩ+10 nF 已于同日作废：与 16 kHz 扫频带重叠）
- 自校准：0.1% Rsense 打底 + 板上 R_ref（100 kΩ 0.01%）自检，**单颗 TMUX1134 切换**（SEL1/2/3=PB1、SEL4=PB0）：
  **零点模式**消 ADC 失调（**SEL_SENSE=PB1、SEL_K2=PB0**，2026-10-28 按 575 命名；2026-10-18 TMUX1134 整合）；
  δ0 只存 RAM，k 只由上位机写 Flash（电路见 E.3 + diagram/模拟前端与自校准）
- **MCU：STM32U575RGT6**（2026-10-28 换型；M33 160 MHz、**1 MB Flash**、**786 KB SRAM**、
  USB FS 双角色（USB_DRD_FS）、LQFP-64、**无 SMPS**；数据手册 **DS13737**）
  ⚠️ 原定 U545RET6Q **已缺货**（立创库存 0），改 575RGT6。两者同 LQFP-64，
  **24–27 脚信号名不同但走线不改**；**575 VCAP(30) 须接 2.2 µF 到地（板上 C4）**
- **引脚（2026-10-28 按 PCB 焊盘实测，权威表 = `docs/design/pin-assignment.md`）**：
  **已取消 I²C/TMP117（PB6/PB7 NC）**、**TF 卡常电无 SD_PWR_EN（PA8 NC）**、**PA4=ADS_CS 不作 DAC**
- **引脚 2026-10-14 全表重排 + 二轮复核 + 2026-10-20 v3 重分配 + 同日二次重排（就近原则）**
  （原则：**通信 AF 不动 + 辅助 GPIO 同端口聚堆 + 封装就近**；权威表 = `docs/design/pin-assignment.md`；
  **LQFP64_SMPS 无 PC4/PC5/PB9/PB12**）：
  - **ADC 簇 PA1–PA7 物理连续（封装 15–23 脚）**：**PA1(ADC_DONE)/PA2(nRESET)/PA3(DRDY, EXTI3)**
    + PA4(nCS)/PA5(SCK)/PA6(MISO)/PA7(MOSI)（原 PA8/PA9/PA10 与 SPI1 簇封装对角，违背就近原则已让出）
  - **调试口 = USART1(PA9/PA10, AF7)**（2026-10-20 由 LPUART1(PA2/PA3) 改，与 SWD 同侧、J3 扩 8P）
  - 内部 ADC 监测：**PC0 = VBAT_MON（ADC1_IN1）**、**PC1 = VBUS_MON（ADC1_IN2）**（+ VREFINT 反推 VDDA）；
    高阻源合法（100 nF 节点电容 ≫ 2^12×CADC），固件须 ≥100 ms 级轮询
  - **SDMMC1 4-bit：PC8/PC9/PC10/PC11 = D0–D3、PC12 = CK、PD2 = CMD**（全手册仅此一组映射）；
    **PA15 = SD_CD**（EXTI15；原 PB9 未引出，PA15 复位默认 JTDI、SWD 模式可作 GPIO）、
    **PA8 = SD_PWR_EN**（默认低 = 卡断电；2026-10-21 三排由 PB13 迁来）
  - TMUX 簇 **PB2(SEL1/2/3 同沿)/PB0(SEL4)/PB10(CURR_DIS)**（封装 24–27 连续，单颗 TMUX1134）；**PB5 = BQ_TS**
  - **LED 簇 PB13/PB14/PB15/PC6/PC7 = 封装 34–38 五连脚**；**ANA_EN=PC3、ISET_HI=PC2**（左侧模拟角）
  - 恒流/电源 PB10(CURR_DIS)、**PB15(ANA_EN**——原 PB12 未引出**)**、PB4(ISET_HI，⚠️ 复位期是 NJTRST+内部上拉，非 Low →
    默认 500 mA 需外部下拉保证，Table 27 注 4，见 E.8.4)
  - LED 簇 **PC2/PC3/PB14/PC6 = 绿/黄/橙/红、PC7 = PWR_LED**（原 PC5 未引出，橙灯改 PB14）
  - 按键 **PA0 = MEAS_BTN(WKUP1)**、**PB1 = PWR_BTN(WKUP4)**
  - USB PA11(DM)/PA12(DP)；调试日志 **LPUART1 PA2/PA3**（**U545 无 USART2**）
  - 预留：PA1(WKUP3)、PA10、PB0；**PC13 不用**（VSW 供电仅 3 mA/30 pF）
  - **原 SPI2 预留组已耗尽**（PB13→SD_PWR_EN、PB14→LED 橙、PB15→ANA_EN；PB9 本未引出）；PT100 已否，该预留本就失效
- 温度：**本版不做**（2026-10-28 取消 I²C/TMP117）
- 通信：USB FS（Type-C，CC×2 各 5.1 kΩ 下拉；外设 USB_DRD_FS，**设备模式片内支持 BC1.2 BCD**）
- **记录（2026-10-14 新增，E.11）**：测量数据 → **外部 TF (micro SD) 卡，SDMMC1 4-bit**；
  校准系数仍存 MCU Flash（EEPROM 仿真）。理由：768 KB/s 冲击采满远超 512 KB Flash。
  走线：每根串 33 Ω 靠 MCU 端；D0–D3+CMD 等长 ±5 mm、CK ±10 mm；CMD 10 kΩ 上拉到 **3V3_SD**；
  卡供电经高边开关（Rds<100 mΩ）由 PB13 控制；**WP 不接**；文件系统 FAT32 簇 32 KB + SDMMC DMA
- 电源：1S 锂电 103450 + **BQ24074**（2026-10-28 换料；QFN-16 带 PowerPath，BAT/VOUT 分离）+ 双 LDO
  （**数字 TPS7A0233 25 nA 常开 / 模拟 TPS7A2033 6.5 µA、7 µVrms EN 受控**）
- 电池管理：**报警 3.65 V / 停测软关机 3.50 V**（仅电池供电态生效）；
  充电默认 500 mA、切 1 A 的判据 = **MCU USB 外设片内 BCD 判 DCP/CDP**（2026-10-14 二轮复核反转，见下）。
  ⚠️ **"默认 500 mA"须靠外部网络保证**：PB4 复位期是 NJTRST + 内部上拉、并非被驱动的低电平（2026-10-16 三次复核，Table 27 注 4）
- 待机预算（E.8.6，二轮复核按 DS14216 Table 62 更正）：已知项 **≈10.8 µA**（全 SRAM）/ **≈7.7 µA**（留 8 KB SRAM2）；
  **TF 卡靠 PB13 断电才成立**，不断电则 50–100 µA 成为最大项
- 引脚/时钟/电源域/交互/连接器已全部定稿（主文档 **E.6–E.9**）；E.5.5 三项待办已销号

## 硬约束（改任何参数都要复核）
- 电流与 Rsense **配套**：V_Rsense = I×Rsense ≤ **2.442 V** 且 V_sample = I×R_max ≤ **2.442 V**
  且合规栈（V_sample+V_Rsense+管压降）≤ 栈顶（T 点）电压 − 0.5 V；跟随器输入 / 输出距电源轨 ≥ 0.15 V
  （**不得缓冲电源轨或地**）
- **测量窗口内不切换**增益 / 电流 / 极性
- 高阻节点保护漏电 < 1 nA（源阻抗最高 150 kΩ）
- 温度补偿是能否达到 1% 的决定性环节
- **ADS131A02 必接脚**：`RESV(16)→IOVDD`、`CAP(28)→1 µF 到 GND`、`NC(24)` 是 **digital output**
  须悬空或 10 kΩ 下拉、`NC(5–8)` 悬空或接 AVSS、AVDD/IOVDD 各 ≥1 µF、REFP/REFN/REFEXT/VNCP 见 E.4.2
- **RET6Q 是 SMPS 版但不用 SMPS**：生成代码里 `HAL_PWREx_ConfigSupply()` 应选 **`PWR_LDO_SUPPLY`**；
  复位默认稳压器模式 DS14216 未载明（"选错则不上电"系推断，已降级）→ 待 RM0456（E.10 #17）
- ~~**MCU 免晶振 = PLL 源必须 MSIS/MSI**~~ → **2026-10-28 修订：首板贴 HSE 16 MHz**（X4 已贴），
  HSE-PLL / MSIS-PLL 均可用，E.10 #16 关闭；USB 仍须 CRS 校准 HSI48。原结论如下（仅历史）：
  ~~HSE 焊盘不贴；IOC 若留 `RCC_PLLSOURCE_HSE` → HSE 不起振
  → PLL 锁不住 → **SYSCLK 无输出**。**当前 IOC 正犯此错**（E.10 #16）
- **SDMMC kernel clock 不得取 SYSCLK/PLL1R**；现 IOC 的 PLL2Q = 258 MHz **非 48 MHz**，生成代码前必须重配（E.10 #14）
- **TF 卡断电只在 `f_mount`/sync 完成后执行**，否则毁 FAT 表
- **规格必须查数据手册核实，不要凭记忆**（历史踩坑：U545 RAM 误报 160 KB、ADS127L11 基准电流、
  ADS131A02 基准实为 2.442 V 非 1.2 V、BQ24040 无独立 BAT 脚、U575/U545 手册号混淆）

## 已被否决（不要重走）
- 电桥（被测对象是两端电阻条，物理上无法成桥）
- 比例式（Rsense 接 ADC REF）：ADS127L11 基准输入电流 ±2 µA 致命；换 ADS131A02 后死因更新为
  **REFEXT 合法输入 MIN 2.0 V / MAX AVDD−0.5 V**（TYP 2.5 V 不是上限），V_Rsense 1.18 V 低于下限，
  强抬则量程崩（R_max ≈20 kΩ）
- 分压激励替代恒流源；改进型 Howland 电流泵；LM334 / JFET 恒流二极管 / BJT 电流沉 / 运放直驱；
  OPA391 换装（详见 AGENTS.md 与 sim README）
- ADS1262（需 4.75 V）、AD779x（无基准缓冲）、ADS1235（500 nA + 5 V）
- **PT100 替 TMP117**（贴装温差 0.5–2 ℃ 主导误差，非传感器精度；E.5.2）
- pin2pin U5↔G4（不存在；pin21 VCAP vs VDDA 硬冲突）
- 电池尾段硬撑测量；PhotoMOS/干簧做 R_ref 切换（TMUX110x 全温漏电 max 唯一合格）
- **TF 卡走 SPI 模式（2026-10-14 否）**：250–500 KB/s < 768 KB/s 需求，必丢样
- **OTG 硬件 VBUS sensing（2026-10-14 否）**：**STM32U5 的 OTG_FS 在 CubeMX 里没有 VBUS 选项**（属 F4/F7 系）；
  且原写"PA9 5 V 容忍"未经 DS14216 核实。→ ~~改 VBUS 分压 → PC1 ADC~~ **2026-10-28 实际图纸改为
  PC13 检测（外部 NPN 集电极，低 = VBUS 在），PC1 改作 BQ_EN**；
  阈值 **3.70 V**（ADC 节点 1.85 V，12-bit 码 ≈2296），可配置。分压 2.6 µA **只在 VBUS 存在时流通，不计入电池待机口径**
- **"VBUS 有 + 3 s 内无 SOF/未枚举 → 判 DCP"启发式（2026-10-14 二轮复核否）**：挂起 / 枚举失败 / 断线
  皆无 SOF ≠ DCP，且 Type-C 只装 Rd 的设备本就无权取 1 A。**BC1.2 结论同日反转**：DS14216 §3.47 末条——
  **U545 USB 外设设备模式片内支持 BC1.2 BCD**（早间"STM32 无 BC1.2"系把 F4/F7 OTG_FS 结论误套 U5）。
  E.8.4 定稿判据：`VBUS>3.70 V` 确认插着电后，**片内 BCD 判 DCP/CDP → 切 1 A**；判 SDP → 按枚举电流、
  维持 500 mA；判不出维持 500 mA。~~BQ24040 仍无 BC1.2，分型全由 MCU 侧完成~~
  → **2026-10-22 该逻辑整体删除**（固定单档充电），**2026-10-28 换料 BQ24074**，本段仅历史。
  另：**BQ24074 的 PG 是 pin 7**（开漏低有效）；BQ24040 的 pin 5 结论作废
- **"只看 SOF/枚举判断 USB 在线"（2026-10-14 否）**：插充电头不接 PC 时无 SOF，会误判"未插 USB"，
  令"在线不报警"逻辑失效
- **手改 CubeMX IOC 增删 IP 块（2026-10-14 实测否）**：手写 SPI1/ADC1/USART2/USB_OTG_FS 的 IP 段会被
  CubeMX **静默丢弃**（IOC 有内部指纹格式）。只能在 GUI 里配、Save 落盘；agent 只提供点击清单

## 🔴 当前阻塞项（原理图/固件前必须清）
- ~~**E.10 #12**~~ ✅ **2026-10-14 二轮复核全清**（均按 DS14216/SLUS941 原文）：
  PC0=**IN1**、PC1=**IN2**；**高阻源合法**（Table 106 注 3 "Values without external capacitor"，
  100 nF ≫ 2^12×CADC(5 pF)，代价 = ≥100 ms 级轮询）；低功耗表号 Table 62/65/68/70
  （Stop3 LDO 4.6/7.7、Standby 0.52、Shutdown 0.40 µA）；BQ24074 **PG = pin 7**；
  SDMMC 信号**全手册仅 PC8–PC12/PD2**。**另清出 4 处换脚**（LQFP64_SMPS 无 PC4/PC5/PB9/PB12）
- ~~**E.10 #16 — IOC 时钟源与免晶振矛盾**~~ ✅ **2026-10-28 关闭**：首板 **HSE 16 MHz 已实贴**
  （X4 + C1/C2 20 pF + R1 1 MΩ），`RCC_PLLSOURCE_HSE` 不再矛盾；MSIS 可作备选。
  **USB 仍必须开 CRS**（HSI48 需从 SOF 校准到 ±0.25 %）
- **E.10 #14 — SDMMC 时钟源**：现 IOC `PLL2Q = 258 MHz`、**`SDMMCFreq_Value` 实测 80 MHz**（2026-10-16 读文件核实）
  → 需重配到 48 MHz（或改 CLK48），**不阻塞原理图**
- ~~**E.10 #15**~~ ✅ **销号**：CRS 用内部 SOF 同步、不占引脚；PA8=ADC_nRESET 无冲突
- **E.10 #17 — RM0456 待核（2026-10-14 新增，2026-10-16 加④）**：① USB_DRD_FS 片内 BCD 使能路径（固件项）；
  ② **SMPS 不启用的 VLXSMPS/VDDSMPS 引脚接法**（同族 U575 写"接 GND"——**原理图前确认，仅两脚**）；
  ③ 复位默认稳压器模式（固件项）；④ **ADC1 采样时间离散档**（DS14216 只给 ts=5…814 周期，未列可选值；
  47.5/247.5 系凭惯例，按 GUI 实际档就近取大：VBAT/VBUS ≥64、VREFINT ≥320 周期）
- **🟥 PB4 复位态（2026-10-16 三次复核新发现，原理图阶段核）**：DS14216 **Table 27 注 4**——
  PB4 复位后为 **NJTRST 复用 + 内部上拉使能**（不是被驱动的 Low），故"**复位默认 500 mA**"这条**取决于外部 ISET 网络**；
  需要复位即锁 500 mA 就得加外部下拉（明显强于内部上拉，RPU 值待 RM0456）或改反相驱动。见 E.8.4 / § 1.1
- **✅ 2026-10-16 三次复核（逐脚 + AF + 通道号再验一遍，脚位结论不变）**，另清出三处**引用层失实**（非脚位错）：
  ① VREFINT 采样依据应为 **Table 37 `tS_vrefint = 12.65 µs typ`**（旧写"≥4 µs"误引了 `tstart_vrefint`＝缓冲启动时间）；
  ② ADC 采样时间**离散档手册未载** → 转 #17④；③ 上条 PB4 复位态。
  同时证实：**USART2 在 DS14216 全文 0 命中**、PC0=IN1/PC1=IN2、PA0=WKUP1/PB1=WKUP4/PA1=WKUP3、
  AF 号 SPI1=5 / SDMMC=12 / USB=10 / I2C1=4 / LPUART1=8、PC13-15 经 VSW（3 mA、≤30 pF、≤2 MHz、不得驱动 LED）
- **示意图已返工（2026-10-17）；2026-10-20 二次重排后待再核**：`diagram/` 各图的引脚标注（2026-10-17 修的是 SEL_K1(PC5)/SEL_K2(PC3)/"PC6-9 · PA8 (PWR)"/DRDY(PC4)/SD_CD(PB9)）
  已按 E.6 与手册值对齐（ANA_EN=PB15、**DRDY=PA3·EXTI3（2026-10-20 二次重排）**、SEL1/2/3=PB2/SEL4=PB8（TMUX1134）、LED 簇 PC2/3/PB14/6+PC7、SD_CD=PA15；恒流源 VSET 1.179 V / 7.86 µA；电源树新增 3V3_SD 支路、整体框图新增 TF 卡支路）；交付必跑
  `python3 tools/svg_schematic_check.py <图>.svg` 且分区放大目视

## 下一步（建议顺序）
1. 清 **E.10 #16**（CubeMX 里 PLL 源改 MSIS/MSI）与 **#17②**（查 RM0456 定 VLXSMPS/VDDSMPS 接法）；
   顺带把 **PB4 复位态**（Table 27 注 4）在原理图上落实成"外部下拉或反相驱动"，否则默认充电档不确定
2. 原理图 → PCB → BOM（EasyEDA / eda-toolkit 可用；**TF 卡座料号与卡型号由用户核实**，E.10 #6）
3. CubeMX 按 `firmware/DE-DRM/CUBEMX_SETUP.md` 在 **GUI 里**补齐 IP（SPI1/**LPUART1**/USB(DRD_FS)/ADC1/SDMMC1/CRS/PWR WKUP），
   Save 后让 CubeMX 重写 IOC；生成代码后**人工核对 `PWR_LDO_SUPPLY` 与 PLL 源**
4. 固件（测量流程、数字滤波/平均、分档判定、USB、电池+VBUS 监测、**FatFS 记录 + 卡不在位降级策略**）与上位机

## 需要外部输入才能推进（不要自行假设）
- 分档阈值：需该批试件的 R/R₀–位移标定曲线
- 温度系数：需实测（论文值仅作参考）
- "R₀ 的 1%" 的适用区间
- **上位机新增**：TF 卡记录文件的格式定义与取数方式（走 USB 还是拔卡）；
  格式属协议，须 `shared/protocol/`（机器可读）与 `docs/protocol/`（人读）**成对更新、同一提交**

## 工作约定
- 仓库 /media/anning/data/Project/DE-DRMS，远端 gitee.com:chenxi666/de-drms.git（SSH 已配好）
- 文档中文；提交用 Conventional Commits；提交后推送并核对远端 SHA
- **外部资料不入库**（器件手册、论文、厂商参数表/导出件）→ 一律放 Obsidian 库
  `20-硬件工程/datasheets/`（另一会话管理）；本仓库只放自己的设计文档、源码与图
- **规格必须查数据手册核实，不要凭记忆**；凡未核实在文档里**如实标注"待核"**，不要写成既成事实
- **工作区出现新目录/新文件时先问用户**，不要自行猜测职责或写进 AGENTS.md 目录清单
- 引脚分配、器件型号等定稿结论若变更，必须**主文档 E + pin-assignment.md + README + AGENTS.md + HANDOFF.md
  五处同步**，历史遗留引用要 grep 清（本轮就靠 grep 揪出 E.3.2 模式表残留 PC5/PC3）
- 器件手册在 Obsidian 库 20-硬件工程/datasheets/（由另一会话管理，本仓库不重复存放）
```

---

## 二、归档线：Obsidian 器件手册归档

> 复制以下整段发给负责 Obsidian 的会话。
> 状态（2026-10-13 核查）：首批 10 份手册已于 vault 提交 `0f3c71c` 归档完成；以下为**第二批**待办。

```
# 任务：DE-DRMS 器件手册第二批归档

## 库位置与既有约定
- Vault：/media/anning/data/obsidian/vault （git 仓库，master 分支）
- 先读 00-INDEX.md，遵循其中的目录结构与笔记规范
- `20-硬件工程/datasheets/`            = 源文件（PDF/DOCX），**笔记的 source 字段指向这里**
- `20-硬件工程/00-Datasheet/NN-分类/<product>/NN-name.md` = 器件手册笔记（11 个分类）
- `20-硬件工程/10-项目设计/`            = 本项目的设计判断（选型、取舍、误差预算）

## 1. 已在库但未提交（untracked）：请建笔记并提交
- `datasheets/OPA333.pdf`   ← **定版**恒流源运放
- `datasheets/BQ24074.pdf`  ← **定版**充电管理（2026-10-28 换料；BQ24040.pdf 仅历史）
- `datasheets/TPS7A02.pdf`  ← **定版**数字轨 LDO（TPS7A0233）
- `datasheets/TPS7A20.pdf`  ← **定版**模拟轨 LDO（TPS7A2033）
- `datasheets/TLV755P.pdf`  （LDO 落选备选，仅存档）
- `10-项目设计/DE-DRMS-ADC参数筛选-20261012.xlsx` ← **请优先提交**：它已从 DE-DRMS 仓库历史中清除，库里这份是唯一副本

## 2. 库里还没有的手册：需下载入库
- TMUX1101 / TMUX1102（TI SCDS410D）← **定版** R_ref 切换开关（主文档 E.3.2 引用其漏电规格）
- BAV199 ← **默认贴装**的输入保护双二极管（E.4.1）
- **STM32U575xx 数据手册 DS13737** ← ⚠️ **2026-10-28 换型后应以此为准**（原 DS14216 为 U545 手册，仅历史）：
  E.10 #12 五项已凭 DS14216 全清且结论对 575 同族适用
  （PC0=IN1/PC1=IN2、高阻源合法、低功耗表号、SDMMC 仅 PC8-12/PD2 一组映射）；
  **575 特有项需查 DS13737**：VCAP 2.2 µF、无 SMPS、Stop3 电流值
- **STM32U5 参考手册 RM0456** ← 新需求：E.10 #17 **四项**待核依赖它（USB_DRD_FS 片内 BCD 使能路径、
  SMPS 不启用的 VLXSMPS/VDDSMPS 处置、复位默认稳压器、**ADC1 采样时间离散档**）；
  另 PB4 复位期内部上拉的**阻值（RPU）**也只在 RM0456 里给（DS14216 无），决定 §1.1/E.8.4 那条外部下拉取不取得准
- 高边负载开关候选（如 TPS22919）← TF 卡供电开关（E.11.3），选型阶段可后补

## 3. 过时笔记：请按设计仓同步
- `10-项目设计/DE-DRMS选型决策.md`：仍写"内部 1.2 V 基准"（应为 2.442 V）、"运放 OPA333/OPA388"
  （恒流源已落定 OPA333，OPA388 用作 3 颗跟随器）、"跟随器 OPA388/OPA320"（OPA320 已去掉）
- `10-项目设计/恒流源选型决策.md`：疑为 V3.0 阶段（OPA192 / 36 V 恒流源）产物，核对后请标注
  "已被 DE-DRMS 主文档附录 E 取代"
- **MCU 选型笔记（若有）**：若写 U575RGT6 / 786 KB SRAM / 1 MB Flash / DS13737，
  需改为 **STM32U545RET6Q、512 KB / 274 KB、DS14216**；
  并补记三条勘误：**U5 的 USB 无 VBUS sensing（CubeMX 无此项）**、**调试串口是 LPUART1（U545 无 USART2）**、
  **BC1.2 结论反转——U545 设备模式片内支持 BC1.2 BCD（DS14216 §3.47），"STM32 无 BC1.2"系误套 F4/F7 结论；
  "3 s 无 SOF 判 DCP"启发式已否决**；另注意 **LQFP64_SMPS 无 PC4/PC5/PB9/PB12**（封装核对须用 Table 27 文本表，勿读位图）
- **若笔记提到"预留 SPI2 给 PT100+MAX31865"**：已失效（PT100 否决 + PB13/PB14/PB15 已分予 LED 绿/黄/橙，SD_PWR_EN 已迁 PA8、ANA_EN 迁 PC3）

## 注意事项
1. 归档完成后请**自行提交**。
2. 设计取舍的权威来源是 /media/anning/data/Project/DE-DRMS/docs/design/README.md；
   该仓库不重复存放手册。
```
