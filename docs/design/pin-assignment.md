# DE-DRMS 引脚分配总表

> STM32U545RET6Q LQFP-64 · ADS131A02 · SDMMC TF · 连接器 · **2026-10-14 重排定稿**
>
> 来源：主文档 **E.6**（MCU 引脚）、**E.11**（TF 记录）、**E.4**（ADC）、**E.9**（连接器）
>
> **本版变更摘要（2026-10-14）**
> ① 新增 **SDMMC1 4-bit**（TF 卡记录）；② **VBUS 检测由 PA9/OTG 硬件改为 PC1 + ADC 分压**
> （STM32U5 的 CubeMX 无 VBUS sensing 选项，且"PA9 5 V 容忍"未经 DS14216 核实）；
> ③ 辅助 GPIO 按**同端口聚堆**重排（ADC 簇归 PA、TMUX 簇归 PB、LED 簇归 PC）；
> ④ 取消 TMP117 ALERT（探头四线）、撤销 NTC 备选占位（PC1 让给 VBUS）；
> ⑤ **二轮复核（同日晚，全表按 DS14216 Table 27/28 逐行核）**：LQFP64_SMPS **无 PC4/PC5/PB9/PB12** →
> DRDY→**PA9**、SD_CD→**PA15**、ANA_EN→**PB15**、LED 橙→**PB14**；通道号更正 PC0=**IN1**、PC1=**IN2**；
> 调试串口更正为 **LPUART1**（U545 无 USART2）；电源脚更正（无 VCAP、无 PDR_ON；VDD=19/33/64、VSS=18/32/47/63）。
>
> **本版变更摘要（2026-10-20 重分配，v3）**
> ⑥ 开关矩阵整合落地（2026-10-18，单颗 **TMUX1134** 替换原 5 开关，原理图网表终验）：SEL1/2/3 = **PB2** 同沿、SEL4 = **PB8**，原 SEL_K1(PB5) 取消；
> ⑦ **PB5 = BQ_TS**（Q1 栅极门控：高 = 旁路 TS NTC，无 NTC 电池可充电；R13 100 kΩ 下拉默认 = NTC 使能）、
> **PA10 = ADC_DONE**（U7-18 DONE 输出，可选监视）→ **预留仅剩 PA1/PB0**；
> ⑧ **HSE/LSE 定位 = 扩展焊盘**（用户 2026-10-20 定）：晶振 + 负载电容 + 反馈电阻**必须画进原理图**（否则无法布局布线），SMT 按需不贴——HSE 默认不贴（免晶振）、LSE 默认贴（RTC）；
> ⑨ TF 卡供电定版 **U8 TPS22917DBVR** 高边开关（图上已实现，SLVSDW8B 逐项核过）；EDA 网名待标准化：`SD_CLX`→`SD_CK`、卡轨自动名→`3V3_SD`、`CURR`→`CURR_DIS`；
> ⑩ 2026-10-20 全工程网表终审（五页 142 器件/83 网）：本表脚位再次全部成立；**VNCP 反勘误 = 270 nF**（SBAS590E 精确值，本表旧写"1 µF"系笔误，图上 C30 正确）。
> ⑪ **同日二次重排（就近原则，PCB 布局驱动）**：PA8/PA9/PA10 位于封装顶边、与 PA4–PA7（左下 20–23 脚一带）对角相望 →
> ADC 控制簇收拢左下：**PA1 = ADC_DONE、PA2 = nRESET、PA3 = DRDY(EXTI3)**，与 SPI1 构成 **PA1–PA7 物理连续簇（封装 15–23 脚）**；
> **调试口 LPUART1(PA2/PA3) 改为 USART1(PA9/PA10, AF7)**，与 SWD 同侧、J3 扩 8P；**PA8 转预留（现预留 PA8/PB0）**。
>
> **本版变更摘要（2026-10-21 通用 GPIO 三排，封装就近原则）**
> ⑫ 用户提出"通用 GPIO 离得十万八千里"——按 LQFP-64 物理引脚序（CubeMX MCU XML 逐脚核）重排，
> **通信/模拟/SDMMC/SWD/USB 簇全部不动**，只动通用 GPIO：
> **LED 5 灯收拢 34–38 五连脚（PB13/PB14/PB15/PC6/PC7，2.5 mm）**；
> **TMUX 控制收拢 24–27**（SEL4 由 PB8(61) → PB0(24)）；**SD_PWR_EN 由 PB13 → PA8(41)**（紧贴 SD_D0/D1）；
> **ANA_EN 由 PB15 → PC3(11)**（左侧模拟角）；**ISET_HI 由 PB4 → PC2(10)**（消除 PB4 复位期红色待办）。
> 预留由 PA8/PB0 改为 **PB4/PB8**。
>
> ✅ **全表引脚存在性 / AF / 通道号已按 DS14216 核实（2026-10-14 二轮复核 + 2026-10-16 三次复核逐脚再验，结论不变；2026-10-20 网表终审再次成立；2026-10-21 三排后逐脚再核）**；
> 遗留待核仅 RM0456 四项（主文档 E.10 #17）+ PB4 复位态对默认充电档的影响（§ 1.1、E.8.4）。

---

## 1. MCU 引脚分配（STM32U545RET6Q LQFP-64）

### 1.1 按功能簇（推荐视图）

| 簇 | 引脚 | 信号 | 说明 |
| --- | --- | --- | --- |
| **ADS131A02（PA 侧扇出）** | PA5 / PA6 / PA7 | SCLK / MISO / MOSI | SPI1（AF5），**模式 1**（CPOL=0 / CPHA=1） |
| | PA4 | nCS | GPIO，默认**高** |
| | **PA2** | nRESET | GPIO，默认**高**；低有效，脉宽 ≥800 ns（**2026-10-20 二次重排**：原 PA8 与 SPI1 簇在封装对角，违背就近原则） |
| | **PA3** | DRDY | **EXTI3**，内部上拉，**下降沿**（原 PA9/EXTI9，PA9 让予 USART1 调试口；EXTI0/1/15 已被按键与 SD_CD 占用，EXTI3 空闲已核） |
| | **PA1** | ADC_DONE | U7-18 DONE（通信帧完成指示，低有效输出），可选监视、可不用（原 PA10；WKUP3 让出——唤醒仍有 PA0/WKUP1、PB1/WKUP4）（EDA 网名 `ADS_DONE` 已有） |
| | | | → **PA1–PA7 物理连续模拟簇**（封装 15–23 脚，中间仅隔 18/19 VSS/VDD 对；PC0/PC1 监测在 8/9 脚、VDDA/VSSA 在 12/13，同处左下模拟角）；PA8/PA9/PA10 位于对侧顶边，不再跨片扇出（EDA 网名前缀 `ADS_*` 与本文档 ADC_* 同义） |
| **内部 ADC1 监测（PC 侧）** | PC0 | VBAT_MON | **ADC1_IN1**，电池分压 2×1 MΩ + 100 nF（常通 ~2 µA） |
| | **PC1** | **VBUS_MON** | **ADC1_IN2**，VBUS 分压 **1 MΩ / 1 MΩ + 100 nF**（比 0.5）；判"USB 在线"阈值 3.70 V |
| | 内部 | VREFINT | 反推 VDDA（外部分压测轨是恒等式，测不出）。采样时间依据 **DS14216 Table 37 `tS_vrefint = 12.65 µs typ`** → @16 MHz 取 **≥320 周期**；旧文档"最小 ≥4 µs"系误引 `tstart_vrefint`（缓冲启动时间），2026-10-16 已勘误。离散档枚举 DS14216 未载 → E.10 #17④ |
| | | | → 通道号已核（DS14216 Table 27）；高阻源合法性见主文档 E.6 注（100 nF 节点电容 + ≥100 ms 级轮询） |
| **SDMMC1 4-bit TF（PC 侧扇出）** | PC8 / PC9 / PC10 / PC11 | D0 / D1 / D2 / D3 | AF12 |
| | PC12 / PD2 | CK / CMD | AF12；CMD 10 kΩ 上拉到 **3V3_SD** |
| | **PA15** | SD_CD | **EXTI15**，内部上拉，下降沿（卡座机械开关）；**二轮复核改**：原 PB9 在 LQFP64_SMPS 未引出；PA15 复位默认 JTDI，SWD 模式不用 JTAG 故作 GPIO 合法 |
| | **PA8** | SD_PWR_EN | GPIO，默认**低 = 卡断电**；控制高边开关（**2026-10-21 三排**：原 PB13，移至 PA8 紧贴 SD_D0/D1 扇出） |
| | — | SD_CKIN | **不接**（SDR12/25 以下不需反馈时钟，本设计 24 MHz 起步） |
| | — | SD_WP | **不接**（写保护由固件 FatFS 标志承担） |
| **TMUX1134 自校准（PB 侧扇出，24–27 连续）** | PB2 | SEL_SENSE | 同时驱动 U10 **SEL1/SEL2/SEL3**（测量线对 K3/K4、K5、K1 同沿切换），默认**低**；**2026-10-18 起**单颗 TMUX1134 替换原 5 开关 |
| | **PB0** | SEL_K2 | U10 **SEL4**（K2 R_ref 回线）；互锁靠固件：**PB2=1 时 PB0 不得为 0**（否则样品与 R_ref 经 X 并联）。**2026-10-21 三排**：原 PB8（顶边 61 脚）→ PB0（24 脚），与 SEL_SENSE/CURR_DIS 聚为 24–27 连续簇 |
| **恒流源** | PB10 | CURR_DIS | **高 = 关断**、低 = 开启；复位/高阻默认 = 开启；零点模式置高 |
| **电源管理** | **PC3** | ANA_EN | TPS7A2033 EN，默认**低**；EN 内置 smart pulldown。**2026-10-21 三排**：原 PB15 → PC3（11 脚，左侧模拟角，紧邻 PC0/PC1 监测与 PA1–PA7 模拟簇） |
| | **PB5** | BQ_TS | Q1(BSS138) 栅极门控：**高 = 旁路 TS 的 NTC**（无 NTC 电池可充电），默认低（R13 100 kΩ 下拉）= NTC 使能；**2026-10-20 新增（SEL_K1 腾出转予）** |
| | **PC2** | ISET_HI | BQ24040 充电电流切换（500 mA ↔ 1 A），默认**低**；判据见 E.8.4。**2026-10-21 三排：由 PB4 迁至 PC2——消除 PB4 复位期 NJTRST+内部上拉的红色待办**（原须外部强下拉压内部上拉；PC2 复位为浮空输入，普通 100 kΩ 下拉即可定义 Low = 500 mA）；PC2 同时紧邻 USB/BQ24040 所在板左侧 |
| **USB FS（Device，外设 USB_DRD_FS）** | PA11 / PA12 | DM / DP | AF10 固定复用，FT_u 由 VDDUSB 供电；设备模式片内支持 BC1.2 BCD（DS14216 §3.47，见主文档 E.8.4） |
| | ~~PA9~~ | ~~VBUS~~ | ❌ **撤销**：本芯片 USB 无 VBUS sensing（CubeMX 无此项）；PA9 现为 USART1_TX（见下） |
| **I²C1（TMP117 四线探头）** | PB6 / PB7 | SCL / SDA | AF4，4.7 kΩ 上拉在主板侧 |
| | ~~PB8~~ | ~~ALERT~~ | ❌ 取消（探头仅 VDD/GND/SDA/SCL）；PB8 现为**预留**（原 SEL_K2 已迁 PB0） |
| **调试日志（USART1）** | **PA9 / PA10** | USART1 TX / RX | AF7；**2026-10-20 由 LPUART1(PA2/PA3) 改**——与 SWD(PA13/14)、SWO(PB3) 同侧组成右侧调试区，J3 扩为 8P；115200。**U545 无 USART2** 不受影响（USART1 独立存在，DS14216 §3.32） |
| **SWD 调试口** | PA13 / PA14 / PB3 / 引脚 7 | SWDIO / SWCLK / SWO / NRST | `Trace_Asynchronous_SW`：SWO 占 PB3、**NJTRST(PB4) 释放**（ISET_HI 已迁 PC2，PB4 现为预留） |
| **档位 LED ×4（34–38 连续簇）** | **PB13 / PB14 / PB15** / PC6 | 绿 / 黄 / 橙 / 红 | 灌电流，**默认高 = 灭**；同一时刻只亮一档。**2026-10-21 三排**：绿 PC2→PB13（34 脚）、黄 PC3→PB14（35 脚），与橙 PB15(36)/红 PC6(37) 及状态灯 PC7(38) 聚为 **34–38 五连脚（2.5 mm）**，原跨封装两侧 13.5 mm |
| **状态 LED** | PC7 | PWR/USB | 灌电流，默认高（38 脚，5 灯簇末位） |
| **按键 ×2** | PA0 | MEAS_BTN | **WKUP1**，内部上拉，低有效，100 nF 去抖 |
| | PB1 | PWR_BTN | **WKUP4**，内部上拉，低有效，100 nF 去抖 |
| **HSE 扩展焊盘** | PH0 / PH1 | OSC_IN / OSC_OUT | **原理图必须画全**（X1 16 MHz + 负载电容 + 1 MΩ 反馈——不画无法布局布线），SMT 可选不贴；本设计免晶振（PLL=MSIS）→ **默认不贴**；负载电容初值按 CL=9 pF → 单只 ≈12 pF（图上现 6.8 pF 为占位需改）（**2026-10-20 用户定**） |
| **LSE** | PC14 / PC15 | OSC32_IN / OUT | 32.768 kHz（X2，**默认贴**，供 RTC）；扩展焊盘性质同上；负载电容初值按 CL=12.5 pF → 单只 ≈18–20 pF（现 6.8 pF 占位需改——**负载错 RTC 走快**） |
| **BOOT0** | PH3（引脚 60） | — | PCB 10 kΩ 下拉，不在 CubeMX 配置 |

> **LED 簇为何不连号（2026-10-14 二轮复核重写）**：原注"PA10 引出未核、DRDY 留 PC4"已过时——
> 真实原因是 **LQFP64_SMPS 没有 PC4/PC5**（DS14216 Table 27，此前误按 LQFP64 非 SMPS 版核脚）。
> 复核后 DRDY 改 PA9、橙灯改 PB14；绿/黄/红 + 状态灯仍在 PC 口一侧，仅橙灯跨到 PB14。

### 1.2 按端口顺序（装配/查表视图）

| 端口 | 引脚分配 |
| --- | --- |
| **PA** | 0=MEAS_BTN · 1=ADC_DONE(ADS_DONE) · 2=ADC_nRESET(ADS_RESET) · 3=ADC_DRDY(ADS_DRDY) · 4=ADC_nCS(ADS_CS) · 5=SPI1_SCK(ADS_CLK) · 6=SPI1_MISO(ADS_MISO) · 7=SPI1_MOSI(ADS_MOSI) · **8=SD_PWR_EN(2026-10-21)** · 9=USART1_TX · 10=USART1_RX · 11=USB_DM · 12=USB_DP · 13=SWDIO · 14=SWCLK · 15=SD_CD |
| **PB** | **0=SEL_K2(SEL4)** · 1=PWR_BTN · 2=SEL_SENSE · 3=SWO · **4=预留** · 5=BQ_TS · 6=I2C1_SCL · 7=I2C1_SDA · ~~8~~**预留** · ~~9~~**未引出** · 10=CURR_DIS · ~~11/12~~**未引出** · **13=LED_GREEN** · 14=LED_YELLOW · **15=LED_ORANGE** |
| **PC** | 0=VBAT_MON · 1=VBUS_MON · **2=ISET_HI** · **3=ANA_EN** · ~~4/5~~**未引出** · 6=LED_RED · 7=PWR_LED · 8=SD_D0 · 9=SD_D1 · 10=SD_D2 · 11=SD_D3 · 12=SD_CK · 13=**不用**(VSW) · 14=LSE_IN · 15=LSE_OUT |
| **PD** | 2=SD_CMD |
| **PH** | 0=HSE_IN · 1=HSE_OUT · 3=BOOT0 |

> **LQFP64_SMPS 未引出脚（DS14216 Table 27，2026-10-14 二轮复核）**：**PC4、PC5、PB9、PB12**（PB11 两版 LQFP-64 均不引出）。
> 另：该封装 28=VLXSMPS、29=VDDSMPS、30=VSSSMPS、**31 与 62 均为 VDD11**（无 VCAP）。

### 1.3 按封装物理序（LQFP-64 1→64 脚，PCB 布局/装配首选视图）

> 2026-10-21 三排后新增。**★ = 本次重排的通用 GPIO**（其余为通信/模拟/SDMMC/SWD 簇，全部未动）。

| 脚 | 引脚 | 类型 | 信号 / 连接 |
| --- | --- | --- | --- |
| 1 | VBAT | Power | 接 3.3V_D（无后备电池） |
| 2 | PC13 | I/O | **不用**（经 VSW 供电，仅 3 mA/30 pF） |
| 3 | PC14 | I/O | LSE_IN — 32.768 kHz 晶振（默认贴，供 RTC） |
| 4 | PC15 | I/O | LSE_OUT — 同上 |
| 5 | PH0 | I/O | HSE_IN — 16 MHz 扩展焊盘（默认不贴，免晶振） |
| 6 | PH1 | I/O | HSE_OUT — 同上 |
| 7 | NRST | Reset | 复位（J3-5） |
| 8 | PC0 | I/O | **VBAT_MON** — ADC1_IN1，2×1 MΩ 分压 |
| 9 | PC1 | I/O | **VBUS_MON** — ADC1_IN2，1M/1M 分压，阈值 3.70 V |
| 10 | PC2 | I/O | **ISET_HI** — BQ24040 充电档（100 kΩ 下拉，默认 500 mA）★ |
| 11 | PC3 | I/O | **ANA_EN** — TPS7A2033 EN（smart pulldown，默认断）★ |
| 12 | VSSA | Power | 模拟地 |
| 13 | VDDA | Power | 3.3V_D + 100 nF + 1 µF |
| 14 | PA0 | I/O | **MEAS_BTN** — WKUP1，内部上拉，100 nF 去抖 ★ |
| 15 | PA1 | I/O | **ADC_DONE** — U7-18 DONE 帧完成指示（可选） |
| 16 | PA2 | I/O | **ADC_nRESET** — 低有效，脉宽 ≥800 ns，默认高 |
| 17 | PA3 | I/O | **ADC_DRDY** — EXTI3 下降沿，内部上拉 |
| 18 | VSS | Power | — |
| 19 | VDD | Power | 3.3V_D |
| 20 | PA4 | I/O | **ADC_nCS** — GPIO，默认高 |
| 21 | PA5 | I/O | **SPI1_SCK** — AF5，模式 1 |
| 22 | PA6 | I/O | **SPI1_MISO** — AF5 |
| 23 | PA7 | I/O | **SPI1_MOSI** — AF5 |
| 24 | PB0 | I/O | **SEL_K2（SEL4）** — TMUX1134 K2 R_ref 回线 ★ |
| 25 | PB1 | I/O | **PWR_BTN** — WKUP4，内部上拉 ★ |
| 26 | PB2 | I/O | **SEL_SENSE** — TMUX1134 SEL1/2/3 同沿 ★ |
| 27 | PB10 | I/O | **CURR_DIS** — 高 = 关断恒流源 ★ |
| 28 | VLXSMPS | Power | **不启用内部 SMPS** — 处置待 RM0456（E.10 #17②） |
| 29 | VDDSMPS | Power | 同上 |
| 30 | VSSSMPS | Power | 同上 |
| 31 | VDD11 | Power | 2.2 µF → VSS（内核 LDO 输出） |
| 32 | VSS | Power | — |
| 33 | VDD | Power | 3.3V_D |
| 34 | PB13 | I/O | **LED_GREEN** — 绿，灌电流低亮 ★ |
| 35 | PB14 | I/O | **LED_YELLOW** — 黄 ★ |
| 36 | PB15 | I/O | **LED_ORANGE** — 橙 ★ |
| 37 | PC6 | I/O | **LED_RED** — 红 ★ |
| 38 | PC7 | I/O | **PWR_LED** — 状态灯 ★ |
| 39 | PC8 | I/O | **SD_D0** — AF12，33 Ω 串阻 |
| 40 | PC9 | I/O | **SD_D1** — AF12，33 Ω |
| 41 | PA8 | I/O | **SD_PWR_EN** — TPS22917 高边开关，默认低 = 断电 ★ |
| 42 | PA9 | I/O | **USART1_TX** — AF7，调试日志 115200 → J3-7 |
| 43 | PA10 | I/O | **USART1_RX** — AF7 → J3-8 |
| 44 | PA11 | I/O | **USB_DM** — AF10 |
| 45 | PA12 | I/O | **USB_DP** — AF10 |
| 46 | PA13 | I/O | **SWDIO** — J3-3 |
| 47 | VSS | Power | — |
| 48 | VDDUSB | Power | 3.3V_D + 100 nF |
| 49 | PA14 | I/O | **SWCLK** — J3-4 |
| 50 | PA15 | I/O | **SD_CD** — EXTI15 下降沿，内部上拉 |
| 51 | PC10 | I/O | **SD_D2** — AF12，33 Ω |
| 52 | PC11 | I/O | **SD_D3** — AF12，33 Ω |
| 53 | PC12 | I/O | **SD_CK** — AF12，33 Ω |
| 54 | PD2 | I/O | **SD_CMD** — AF12，33 Ω + 10 kΩ 上拉 3V3_SD |
| 55 | PB3 | I/O | **SWO** — TRACESWO，J3-6 |
| 56 | PB4 | I/O | **预留**（原 ISET_HI 已迁 PC2；复位期 NJTRST+上拉，现无害） |
| 57 | PB5 | I/O | **BQ_TS** — Q1 栅极门控（高 = 旁路 NTC；R13 100 kΩ 下拉 = NTC 使能）★ |
| 58 | PB6 | I/O | **I2C1_SCL** — AF4，4.7 kΩ 上拉 → J4-3 |
| 59 | PB7 | I/O | **I2C1_SDA** — AF4，4.7 kΩ 上拉 → J4-4 |
| 60 | PH3 | I/O | **BOOT0** — PCB 10 kΩ 下拉 |
| 61 | PB8 | I/O | **预留**（原 SEL_K2 已迁 PB0） |
| 62 | VDD11 | Power | 2.2 µF → VSS |
| 63 | VSS | Power | — |
| 64 | VDD | Power | 3.3V_D |

### 1.4 MCU 电源脚（DS14216 Table 27，2026-10-14 二轮复核）

| 引脚 | 连接 | 去耦 |
| --- | --- | --- |
| VDD **19/33/64** + VSS **18/32/47/63** | 3.3V_D | 每对 100 nF + 共 10 µF |
| VDDA(13) / VSSA(12) | 3.3V_D | 100 nF + 1 µF（内部 ADC 不用作测量） |
| VDDUSB(48) | 3.3V_D | 100 nF |
| VBAT(1) | 接 VDD | 无后备电池（锂电 4.2 V 超 VBAT 上限 3.6 V） |
| **VDD11 (31 与 62)** | 各 2.2 µF → VSS | 内核 LDO 输出（**RET6Q 无 VCAP**，原"VCAP(30)→4.7 µF"系按非 SMPS 版误写） |
| VLXSMPS(28) / VDDSMPS(29) / VSSSMPS(30) | 内部 SMPS 不启用的处置 **待 RM0456**（同族 U575 写"接 GND"）→ 主文档 E.10 #17 | — |

> ⚠️ **RET6Q 是 SMPS 版**：本设计用外部双 LDO、**内部 SMPS 不启用**。
> 生成代码中 `HAL_PWREx_ConfigSupply()` 应选 **`PWR_LDO_SUPPLY`**；
> 复位后默认稳压器模式 DS14216 未载明（"选错则不上电"系推断，已降级）→ 待 RM0456（E.10 #17）。
> ~~PDR_ON~~：**DS14216 无此脚**（F4/F7 遗绪），已删除。

### 1.5 预留脚

**PB4（56 脚）、PB8（61 脚）**；**PC13 不使用**（经 VSW 供电，仅 3 mA/30 pF）。
（2026-10-21 三排：PA8 → SD_PWR_EN、PB0 → SEL4，预留由 PA8/PB0 变为 PB4/PB8。PB4 虽预留，其复位期 NJTRST+内部上拉特性无害。）

> **预留消耗史**：2026-10-14 原 SPI2 预留组四脚用尽（PB13→SD_PWR_EN、PB14→LED 橙、PB15→ANA_EN、PB9→SD_CD 后改 PA15）；
> 2026-10-20 再耗：**PB5**（SEL_K1 取消后腾出）→ BQ_TS、**PA1/PA2/PA3**（LPUART1 撤销让位）→ ADC_DONE/nRESET/DRDY；
> **PA8/PA9/PA10** 因与 SPI1 簇对角、违背就近原则让出——PA9/PA10 转调试 USART1，PA8 入预留。
> 该预留本为 PT100+MAX31865 而留，**PT100 已于 E.5.2 否决**，预留失效合理。

---

## 2. ADS131A02 引脚连接

### 信号引脚

| 引脚 | 连接 | 说明 |
| --- | --- | --- |
| AIN0P | OPA388(T) 输出 → **AAF B 案**（见下注） | 通道 0 正：T 点电压 |
| AIN0N | OPA388(S) 输出 → **AAF B 案** | 通道 0 负：S 点电压（经 K3） |
| AIN1P | OPA388(B) 输出 → **AAF B 案** | 通道 1 正：B 点电压 |
| AIN1N | E 点（Rsense 底端）→ **AAF B 案** | 通道 1 负：Kelvin 引线，不经跟随器 |
| SCLK | PA5（SPI1 SCLK） | — |
| DIN | PA7（SPI1 MOSI） | — |
| DOUT | PA6（SPI1 MISO） | — |
| nCS | PA4（GPIO） | — |
| DRDY | **PA3**（**EXTI3**） | 下降沿中断，内部上拉（**2026-10-20 二次重排**：原 PA9；EXTI0/1/15 已占，EXTI3 空闲） |
| DONE | **PA1**（GPIO 输入，可选） | 通信帧完成指示，低有效输出；异步中断模式下可不接用（**2026-10-20 二次重排**：原 PA10） |
| nRESET | **PA2**（GPIO） | 低有效，脉宽 ≥800 ns（**2026-10-20 二次重排**：原 PA8） |

> **每线抗混叠 = AAF B 案三级无源阶梯（E.4.4 定版，2026-10-19）**：
> `6.19 Ω + 68 nF → 6.04 Ω + 68 nF → 13.7 Ω + 27 nF（对地，C0G）+ 末级 12 nF 差分`；
> R 全 E96 1%（ΣR=25.93 Ω），fc ≈ 80 kHz，建立 ≤30.1 µs（73 Ω–600 kΩ 十六点）。
> **两线须按 R·C 乘积异向配对**（R×(1+m) 配 C×(1−m)）：1% 单体不配对 CMRR 仅 48.5 dB、配对后 95.5 dB——
> **BOM 必须加配对工序**。定版图 `docs/design/diagram/抗混叠滤波电路.svg`。
> ~~原 1 kΩ + 10 nF（fc 15.9 kHz）~~ 已作废：与 16 kHz 扫频上限重叠，通带边缘衰减 ~3 dB。
| XTAL1 / XTAL2 | 16.384 MHz 晶振 | 负载电容按手册 Figure 36b |

### 必接脚（原理图阶段勿漏）

| 引脚 | 连接 | 说明 |
| --- | --- | --- |
| RESV(16) | IOVDD | 手册明写 "connect to IOVDD"，不得悬空 |
| CAP(28) | 1 µF → GND | 内部数字 LDO 输出 |
| NC(24) | 10 kΩ → GND | 数字输出，须下拉或悬空 |
| NC(5–8) | AVSS 或悬空 | — |
| AVDD | 3.3V_A，≥1 µF 解耦 | 模拟电源（**受 ANA_EN 门控**） |
| IOVDD | 3.3V_D，≥1 µF 解耦 | 数字电源（**常开**；工况合法性见 E.8.6） |
| REFP(12) | 内部 2.442 V 基准输出 | 1 µF → REFN/AVSS（图上 C31 1 µF ✓） |
| REFN(13) | 接 AVSS | 图上 ✓ |
| REFEXT(14) | MIN 2.0 V / MAX AVDD−0.5 V | 用内部基准时 **1 µF → AVSS**（手册明文；图上 C32 ✓） |
| VNCP(11) | **270 nF → AVSS**（电荷泵使能时；SBAS590E 精确值） | ⚠️ **本表旧写"1 µF"系笔误，2026-10-20 勘误**——图上 C30 = 270 nF 正确 |
| M0/M1/M2 (30/31/32) | 绑定电平选模式，绑接电阻须 **<1 kΩ**（手册明文） | 图上各 1 kΩ：M0→IOVDD = **异步中断模式**、M1→GND = **24-bit 字**、M2→GND = **Hamming 关**；建议改 0 Ω/470 Ω 严格合规 |
| DOUT(21) | **100 kΩ 上拉到 IOVDD**（手册明文） | 图上 R21 100 kΩ → VCC ✓ |

---

## 3. SDMMC TF 卡接口

| 卡座脚 | 网络 | MCU | 外部元件 |
| --- | --- | --- | --- |
| DAT0 | SD_D0 | **PC8** | 33 Ω 串阻（靠 MCU） |
| DAT1 | SD_D1 | **PC9** | 33 Ω |
| DAT2 | SD_D2 | **PC10** | 33 Ω |
| DAT3 | SD_D3 | **PC11** | 33 Ω（兼作卡内 CS 上电默认高） |
| CLK | SD_CK | **PC12** | 33 Ω；走线 ±10 mm（时序参考） |
| CMD | SD_CMD | **PD2** | 33 Ω + **10 kΩ 上拉到 3V3_SD** |
| VDD | 3V3_SD | — | 高边开关输出；**1 µF + 100 nF** 就地去耦 |
| GND | GND | — | — |
| CD | SD_CD | **PA15** | 卡座机械开关，插卡拉低；内部上拉，EXTI15 下降沿（**二轮复核改**：原 PB9 未引出） |
| WP | — | — | **不接**（E.11） |

**供电与控制（2026-10-20 定版，图上已实现并经手册 SLVSDW8B 核实）**：`3.3V_D → **U8 TPS22917DBVR** 高边开关 → 3V3_SD`，EN = **PB13 (SD_PWR_EN)**（高有效，EN 内置 750 kΩ 智能下拉，PB13 复位浮空 = 断电，无需外部电阻）；**QOD 接 VOUT**（断电 150 Ω 放电）、**CT 悬空**（软启动 ≈100 µs，1.1 µF 负载涌流 ≈36 mA）。
RON ≈90 mΩ typ / 110 mΩ max @3.6 V·25 ℃ → 100 mA 写瞬态压降 ≤11 mV，**以压降判据替代原"Rds(on) < 100 mΩ"字面要求**。
**若省掉该开关，TF 卡待机 50–100 µA 会直接压垮 E.8.6 的 ≈10.8 µA 预算。**
卡轨去耦 = **C38 100 nF + C55 1 µF**；**R42 10 kΩ CMD 上拉必须挂 3V3_SD**（防卡断电时经 IO 保护二极管倒灌）；**7×0402ESDA-05N**（D9–D15）覆盖 D0–D3/CK/CMD/CD 全部卡座信号（热插拔 ESD）。

**EDA 落地注记（2026-10-20 网表终审）**：① 网名标准化：`SD_CLX`→`SD_CK`、卡电源轨自动名→`3V3_SD`（固件宏按网名生成，文档↔图名必须一致）；② **33 Ω×6 串阻与 MCU 侧全部扇出尚未画**（MCU 信号脚当前零连接，本节引脚已定，补图时一并）；③ 卡座 EDA 位号 = CARD1，本文档编 **J9**。

**走线规则**：D0–D3 + CMD 等长 **±5 mm**；CK **±10 mm**（允许略短，不允许长）；
串阻靠 MCU 端；6 根线从 PC 端口一侧扇出，**不穿越模拟区**。

**时钟源**：SDMMC1 kernel clock **不得用 SYSCLK/PLL1R**；取 PLL2Q=48 MHz 或 CLK48。
现 IOC 中 PLL2Q = 258 MHz、**`RCC.SDMMCFreq_Value` 实测 80 MHz**（2026-10-16 读文件核实），**生成代码前必须重配**（E.10 #14）。

---

## 4. 连接器引脚分配

### USB Type-C（J1）

| 引脚 | 连接 | 说明 |
| --- | --- | --- |
| A1/B12 (GND) | GND | — |
| A4/B9 (VBUS) | BQ24040 IN + **分压到 PC1** | 5 V 输入；VBUS_MON 兼作"USB 在线"检测（E.8.3） |
| A5 (CC1) | 5.1 kΩ → GND | UFP 下拉 |
| B5 (CC2) | 5.1 kΩ → GND | UFP 下拉 |
| A6 (D+) | PA12 (USB_DP) | — |
| A7 (D−) | PA11 (USB_DM) | — |
| B1/B12 (GND) | GND | — |

### 被测件接口（J5–J8）— 4 × SMA 母座（2026-10-17 两线/四线兼容）

| 端子 | 网络 | 说明 |
| --- | --- | --- |
| **J5 · I+** | T（顶端偏置 ~3.0 V） | 经 R_top 10 kΩ 接 3.3V_A；**力线** |
| **J6 · V+** | OPA388(T) 输入（经 AAF B 案） | **感线**；与 J5 同夹 = Kelvin 夹 A |
| **J7 · I−** | K1/K2 公共端 → X | **力线**回线（样品 / R_ref） |
| **J8 · V−** | K3/K4 公共端 → M | **感线**；与 J7 同夹 = Kelvin 夹 B |
| **JP1** | J5 ↔ J6 | 0 Ω 0603 / 插针：**焊上 = 两线制**（只接 J5、J7） |
| **JP2** | J7 ↔ J8 | 同上 |

> **两种模式**：四线制（JP1/JP2 不焊）4 线 + 2 只 Kelvin 夹，引线/接触/K1–K4 导通电阻不进结果（≈0 误差）；两线制（JP1/JP2 焊上）只用 J5、J7，误差 = (引线+接触)/R_sample —— 0.5 Ω 在 73 Ω 处 0.68%、10 kΩ 处 0.005%、120 kΩ 处 0.0004%。
> **屏蔽**：4 只 SMA 外壳 → AGND（仪器侧单端）；电缆 4 芯屏蔽（I+/I− 与 V+/V− 各双绞）。接线示意见 `docs/design/diagram/两电极四线制接法.svg`。

### 调试口（J3）— 8P 排针（**2026-10-20 6P→8P**，加 USART1 串口）

| 引脚 | 信号 | 说明 |
| --- | --- | --- |
| 1 | 3V3_D | — |
| 2 | GND | — |
| 3 | SWDIO (PA13) | — |
| 4 | SWCLK (PA14) | — |
| 5 | NRST | MCU 复位 |
| 6 | SWO (PB3) | TRACESWO |
| 7 | USART1_TX (PA9) | 调试日志 115200 |
| 8 | USART1_RX (PA10) | — |

### TMP117 温度探头（J4）— 4P 焊盘（1.25 mm 间距，连接器用户自选）

| 引脚 | 信号 | 说明 |
| --- | --- | --- |
| 1 | 3V3_D (VDD) | — |
| 2 | GND | — |
| 3 | SCL (PB6) | I²C1，4.7 kΩ 上拉 |
| 4 | SDA (PB7) | I²C1，4.7 kΩ 上拉 |

> 仅四线，**无 ALERT**；采购须 ADD0 接地版（地址 0x48）。

### TF 卡座（J9，EDA 位号 CARD1）— micro SD 8P 卧贴（2026-10-14 新增；**2026-10-20 编号 J6→J9**，原 J6 与被测件 SMA J6 撞号）

见 § 3。位置靠板边便于换卡；料号由用户在 BOM 阶段核实（E.10 #6）。

> ~~J5 NTC 备选 2P 焊盘~~ → **撤销**（2026-10-14）：PC1 让给 VBUS_MON。

---

## 5. 信号网络汇总

| 网络名 | 起点 | 终点 | 说明 |
| --- | --- | --- | --- |
| 3.3V_D | TPS7A0233 OUT | MCU VDD/VDDA/VDDUSB、USB、LED、TMP117、ADS131A02 IOVDD、高边开关输入 | 数字域，常开 |
| **3V3_SD** | 高边开关 OUT | TF 卡 VDD、CMD 上拉 | **受 PB13 控制**，默认断电 |
| 3.3V_A | TPS7A2033 OUT | ADS131A02 AVDD、OPA388×3、OPA333、TMUX、VSET、R_top/R_b | 模拟域，EN 受控 |
| T | R_top/R_b 偏置节点 | 样品顶端、R_ref 顶端、OPA388(T) 输入 | ~2.97–3.07 V |
| S | 样品底端 | K3 → M → OPA388(S) 输入 | 2.03–2.99 V |
| M | K3/K4 汇合点 | OPA388(S) 输入 | 测量=S，校准=R_ref |
| B | BSS138 源极 / Rsense 顶端 | OPA388(B) 输入 | ~1.18 V |
| E | Rsense 底端 = GND | AIN1N（Kelvin 引线） | 0 V |
| VSET | 360 kΩ/200 kΩ 分压 | OPA333 + → BSS138 Gate | 1.179 V |
| CURR_DIS | PB10 | BSS138 关断控制 | 高 = 关断（EDA 网名 `CURR` 建议改 `CURR_DIS`） |
| **BQ_TS** | **PB5** | Q1(BSS138) 栅极 | 高 = 旁路 TS NTC（无 NTC 电池可充电）；默认低 = NTC 使能（R13 100 kΩ 下拉）；**2026-10-20 新增** |
| **ISET_HI** | **PC2** | BQ24040 ISET 分压切换 | 高 = 1 A / 低 = 500 mA；**2026-10-21 三排由 PB4 迁来**（PB4 复位期 NJTRST+内部上拉 → 移走后普通 100 kΩ 下拉即可定义默认 Low） |
| **ADS_DONE** | U7-18 → **PA1** | 帧完成指示（可选） | 低有效输出，可不接用；**2026-10-20 新增，二次重排后落 PA1** |
| ANA_EN | **PC3** | TPS7A2033 EN | 高 = 模拟域上电（**2026-10-21 三排**：原 PB12→PB15→PC3，左侧模拟角） |
| **SD_PWR_EN** | **PA8** | **TPS22917 EN** | 高 = TF 卡上电，默认低（EN 内置下拉，复位浮空 = 断电）；**2026-10-21 三排：原 PB13→PA8**，紧贴 SDMMC 扇出 |
| **VBUS_MON** | VBUS 分压中点 | **PC1**（ADC） | 比 0.5；阈值 3.70 V |
| **VBAT_MON** | 电池分压中点 | **PC0**（ADC） | 比 0.5；报警 3.65 V / 停测 3.50 V |
| **被测件端子** | **J5/J6/J7/J8** | 见「被测件接口」节 | J5=I+→T、J6=V+→OPA388(T)、J7=I−→K1/K2→X、J8=V−→K3/K4→M；JP1(J5↔J6)/JP2(J7↔J8) 焊上即退化为两线制 |

---

## 6. CubeMX 落地注意

- 手改 IOC 加 IP 块会被 CubeMX **静默丢弃**（已实测踩坑）——必须在 **GUI 里配**，配完 Save 让 CubeMX 重写 IOC。
- 操作清单见 [`firmware/DE-DRM/CUBEMX_SETUP.md`](../../firmware/DE-DRM/CUBEMX_SETUP.md)。
- 当前 `DE-DRM.ioc`（回滚至 commit `cb91980` 基线）仍缺：SPI1 IP、LPUART1、USB（USB_DRD_FS）、ADC1、SDMMC1、CRS、
  PA9/PA15 EXTI、PB14/PB15 等 GPIO 配置；
  且 PA6/PA7 已挂 SPI1 信号但 SPI1 IP 未启用 → **孤儿信号，CubeMX 打开会报冲突**。
- ⚠️ IOC 里已有的 GPIO 标签也是**重排前**的：PA8=PWR_LED、PB0=ADC_nRESET、PC3=SEL_K2、PC6–PC9=四色 LED。
  GUI 改脚位时**先清/移旧标签再设新标签**——尤其 PC8/PC9 现为 SD_D0/SD_D1，旧 LED 标签必须删除，
  否则 SDMMC 信号名与 LED 宏错乱（固件 `main.h` 按 Label 生成宏）。
- **2026-10-16 三次复核（全 45 脚 + 电源脚逐一对 Table 27/28/29 再核一遍）**：脚位分配**全部成立**，
  AF 号亦对（SPI1=AF5、SDMMC=AF12、USB=AF10、I2C1=AF4、LPUART1=AF8）；`USART2` 在 DS14216 全文 **0 命中**（再次确认无此外设）。
  另清出**三处引用层失实**（不影响脚位）：① VREFINT 采样依据应为 Table 37 `tS_vrefint = 12.65 µs typ`，
  旧写"≥4 µs"是 `tstart_vrefint`（缓冲启动时间）误引；② 采样时间**离散档 DS14216 未列**（只给 ts=5…814 周期），
  "47.5 / 247.5 Cycles"凭惯例填写 → 转 **E.10 #17④**，按 GUI 实际档就近取大；
  ③ **PB4/PA15 复位期内部上拉使能**（Table 27 **注 4**），PB4 复位期不是 Low → 默认充电档须外部下拉保证（见 § 1.1、E.8.4）。
- **2026-10-20 全工程网表终审**（五页 142 器件/83 网，Protel2 导出逐网核对）：本表全部脚位成立。已通过：TF 卡区（TPS22917/QOD/1 µF/CMD 上拉挂 3V3_SD/7×0402ESDA）、AAF B 案（6.19+68n→6.04+68n→13.7+27n+12n 差分逐值命中 E.4.4）、
  ADS131A02 全脚（含 VNCP 270 nF、M0/M1/M2 绑定、DOUT 100 kΩ 上拉）、TMUX1134、BAV199 ×4。
  **缺口 = MCU 信号扇出未画**：SD 全部信号 + 33 Ω×6、PB 簇控制（PB2/5/8/10/13/15）、SPI1 簇 + PA10、USB、VBAT_MON/VBUS_MON 分压、
  I2C1 + TMP117、SWD J3、LPUART1 焊盘、档位 LED ×4 + 状态 LED、MEAS/PWR 按键。
  GUI 配置新增两脚：**PA10**（GPIO 输入）、**PB5**（GPIO 输出），其余按本表；另改晶振负载电容初值（§ 1.1 HSE/LSE 行）。
- **2026-10-20 二次重排后的 GUI 变化**：**新增 USART1 IP**（PA9/PA10，AF7——GUI 手动加，老规矩 IOC 不可手改）；**删除 LPUART1**；
  **PA1**（GPIO 输入 = ADS_DONE）、**PA2**（GPIO 输出 = ADS_RESET）、**PA3**（EXTI3 下降沿 + 内部上拉 = ADS_DRDY）、**PA8** 释放。
  EDA 侧网名不变（`ADS_*` 照旧），只是标签落到新引脚；调试网名 `USART1_TX/RX`。
