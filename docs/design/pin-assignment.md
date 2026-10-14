# DE-DRMS 引脚分配总表

> STM32U545RET6Q LQFP-64 · ADS131A02 · SDMMC TF · 连接器 · **2026-10-14 重排定稿**
>
> 来源：主文档 **E.6**（MCU 引脚）、**E.11**（TF 记录）、**E.4**（ADC）、**E.9**（连接器）
>
> **本版变更摘要（2026-10-14）**
> ① 新增 **SDMMC1 4-bit**（TF 卡记录）；② **VBUS 检测由 PA9/OTG 硬件改为 PC1 + ADC 分压**
> （STM32U5 的 CubeMX 无 VBUS sensing 选项，且"PA9 5 V 容忍"未经 DS14216 核实）；
> ③ 辅助 GPIO 按**同端口聚堆**重排（ADC 簇归 PA、TMUX 簇归 PB、LED 簇归 PC）；
> ④ 取消 TMP117 ALERT（探头四线）、撤销 NTC 备选占位（PC1 让给 VBUS）。
>
> ⚠️ **凡未标"手册核实"的通道号/耐压/表号，均待对 DS14216 复核 → 见主文档 E.10 #12。**

---

## 1. MCU 引脚分配（STM32U545RET6Q LQFP-64）

### 1.1 按功能簇（推荐视图）

| 簇 | 引脚 | 信号 | 说明 |
| --- | --- | --- | --- |
| **ADS131A02（PA 侧扇出）** | PA5 / PA6 / PA7 | SCLK / MISO / MOSI | SPI1（AF5），**模式 1**（CPOL=0 / CPHA=1） |
| | PA4 | nCS | GPIO，默认**高** |
| | **PA8** | nRESET | GPIO，默认**高**；低有效，脉宽 ≥800 ns（**原 PB0**） |
| | PC4 | DRDY | **EXTI4**，内部上拉，**下降沿** |
| | | | → PA4–PA8 成连续 5 脚；DRDY 留 PC4（PA10 引出情况未核，不占） |
| **内部 ADC1 监测（PC 侧）** | PC0 | VBAT_MON | ADC1_IN5，电池分压 2×1 MΩ + 100 nF（常通 ~2 µA） |
| | **PC1** | **VBUS_MON** | ADC，VBUS 分压 **1 MΩ / 1 MΩ + 100 nF**（比 0.5）；判"USB 在线"阈值 3.70 V |
| | 内部 | VREFINT | 反推 VDDA（外部分压测轨是恒等式，测不出） |
| | | | → **通道号待核**（E.10 #12①） |
| **SDMMC1 4-bit TF（PC 侧扇出）** | PC8 / PC9 / PC10 / PC11 | D0 / D1 / D2 / D3 | AF12 |
| | PC12 / PD2 | CK / CMD | AF12；CMD 10 kΩ 上拉到 **3V3_SD** |
| | PB9 | SD_CD | **EXTI9**，内部上拉，下降沿（卡座机械开关） |
| | PB13 | SD_PWR_EN | GPIO，默认**低 = 卡断电**；控制高边开关 |
| | — | SD_CKIN | **不接**（SDR12/25 以下不需反馈时钟，本设计 24 MHz 起步） |
| | — | SD_WP | **不接**（写保护由固件 FatFS 标志承担） |
| **TMUX 自校准（PB 侧扇出）** | PB2 | SEL_SENSE | 测量线对（K3/K4），默认**低** |
| | **PB5** | SEL_K1 | K1 样品回线（NO），**高 = 通**，默认**低**（**原 PC5**） |
| | **PB8** | SEL_K2 | K2 R_ref 回线（NC），**低 = 通**，默认**高**；与 SEL_K1 互锁（**原 PC3**） |
| **恒流源** | PB10 | CURR_DIS | **高 = 关断**、低 = 开启；复位/高阻默认 = 开启；零点模式置高 |
| **电源管理** | PB12 | ANA_EN | TPS7A2033 EN，默认**低**；EN 内置 smart pulldown |
| | PB4 | ISET_HI | BQ24040 充电电流切换（500 mA ↔ 1 A），默认**低**；判据见 E.8.4 勘误 |
| **USB OTG FS（Device）** | PA11 / PA12 | DM / DP | AF10 固定复用，FT_u 由 VDDUSB 供电 |
| | ~~PA9~~ | ~~VBUS~~ | ❌ **撤销**：本芯片 OTG_FS 无 VBUS sensing（CubeMX 无此项），PA9 释放为预留 |
| **I²C1（TMP117 四线探头）** | PB6 / PB7 | SCL / SDA | AF4，4.7 kΩ 上拉在主板侧 |
| | ~~PB8~~ | ~~ALERT~~ | ❌ 取消（探头仅 VDD/GND/SDA/SCL），PB8 转予 SEL_K2 |
| **调试日志** | PA2 / PA3 | USART2 TX / RX | 预留焊盘，115200 |
| **SWD 调试口** | PA13 / PA14 / PB3 / 引脚 7 | SWDIO / SWCLK / SWO / NRST | `Trace_Asynchronous_SW`：SWO 占 PB3、**NJTRST(PB4) 释放**作 ISET_HI |
| **档位 LED ×4** | PC2 / PC3 / PC5 / PC6 | 绿 / 黄 / 橙 / 红 | 灌电流，**默认高 = 灭**；同一时刻只亮一档 |
| **状态 LED** | PC7 | PWR/USB | 灌电流，默认高（**原 PA8**） |
| **按键 ×2** | PA0 | MEAS_BTN | **WKUP1**，内部上拉，低有效，100 nF 去抖 |
| | PB1 | PWR_BTN | **WKUP4**，内部上拉，低有效，100 nF 去抖 |
| **HSE 焊盘预留** | PH0 / PH1 | OSC_IN / OSC_OUT | 16 MHz 焊盘不贴，引脚不他用 |
| **LSE** | PC14 / PC15 | OSC32_IN / OUT | 32.768 kHz，供 RTC |
| **BOOT0** | PH3（引脚 60） | — | PCB 10 kΩ 下拉，不在 CubeMX 配置 |

> **LED 簇为何断在 PC4**：想让 5 颗 LED 占 PC2–PC6 完美连号，需把 ADC_DRDY 挪到 PA10；
> 但 **PA10 是否引出 LQFP-64 未经 DS14216 核实**，不凭猜测占脚。
> 故 DRDY 留 PC4，LED 落 PC2/PC3/PC5/PC6/PC7——同端口、仅隔一脚，扇出方向仍一致。

### 1.2 按端口顺序（装配/查表视图）

| 端口 | 引脚分配 |
| --- | --- |
| **PA** | 0=MEAS_BTN · 1=预留(WKUP3) · 2=USART2_TX · 3=USART2_RX · 4=ADC_nCS · 5=SPI1_SCK · 6=SPI1_MISO · 7=SPI1_MOSI · 8=ADC_nRESET · 9=预留 · 10=预留 · 11=USB_DM · 12=USB_DP · 13=SWDIO · 14=SWCLK · 15=预留 |
| **PB** | 0=预留 · 1=PWR_BTN · 2=SEL_SENSE · 3=SWO · 4=ISET_HI · 5=SEL_K1 · 6=I2C1_SCL · 7=I2C1_SDA · 8=SEL_K2 · 9=SD_CD · 10=CURR_DIS · 12=ANA_EN · 13=SD_PWR_EN · 14=预留 · 15=预留 |
| **PC** | 0=VBAT_MON · 1=VBUS_MON · 2=LED_GREEN · 3=LED_YELLOW · 4=ADC_DRDY · 5=LED_ORANGE · 6=LED_RED · 7=PWR_LED · 8=SD_D0 · 9=SD_D1 · 10=SD_D2 · 11=SD_D3 · 12=SD_CK · 13=**不用**(VSW) · 14=LSE_IN · 15=LSE_OUT |
| **PD** | 2=SD_CMD |
| **PH** | 0=HSE_IN · 1=HSE_OUT · 3=BOOT0 |

> PB11 在 LQFP-64 未引出，故表中跳过。

### 1.3 MCU 电源脚（手册核实）

| 引脚 | 连接 | 去耦 |
| --- | --- | --- |
| VDD 19/32/64 + VSS 18/31/47/63 | 3.3V_D | 每对 100 nF + 共 10 µF |
| VDDA(13) / VSSA(12) | 3.3V_D | 100 nF + 1 µF（内部 ADC 不用作测量） |
| VDDUSB(48) | 3.3V_D | 100 nF |
| VBAT(1) | 接 VDD | 无后备电池（锂电 4.2 V 超 VBAT 上限 3.6 V） |
| VCAP(30) | 4.7 µF 到地 | ±20 %，ESR<20 mΩ @3 MHz，耐压 ≥10 V |
| PDR_ON | 按手册接 | ⚠️ 待核 DS14216（RET6Q 有 SMPS，PDR_ON 处理方式需确认，E.10 #12） |

> ⚠️ **RET6Q 是 SMPS 版**：本设计用外部双 LDO、**内部 SMPS 不启用**。
> 生成代码中 `HAL_PWREx_ConfigSupply()` 必须是 **`PWR_LDO_SUPPLY`**，
> 不得选 `PWR_SMPS_1V8_SUPPLIES_LDO`，否则 MCU 不上电。

### 1.4 预留脚

**PA1（WKUP3）、PA9、PA10、PA15、PB0、PB14、PB15**；**PC13 不使用**（经 VSW 供电，仅 3 mA/30 pF）。

> **原 SPI2 预留组已消耗**（2026-10-14）：PB9→SD_CD、PB13→SD_PWR_EN。
> 该预留本为 PT100+MAX31865 而留，**PT100 已于 E.5.2 否决**，预留失效，让位 TF 记录合理。
> PB14/PB15 仍空，可作其它 SPI 从机或备用。

---

## 2. ADS131A02 引脚连接

### 信号引脚

| 引脚 | 连接 | 说明 |
| --- | --- | --- |
| AIN0P | OPA388(T) 输出 → 1 kΩ + 10 nF | 通道 0 正：T 点电压 |
| AIN0N | OPA388(S) 输出 → 1 kΩ + 10 nF | 通道 0 负：S 点电压（经 K3） |
| AIN1P | OPA388(B) 输出 → 1 kΩ + 10 nF | 通道 1 正：B 点电压 |
| AIN1N | E 点（Rsense 底端）→ 1 kΩ + 10 nF | 通道 1 负：Kelvin 引线，不经跟随器 |
| SCLK | PA5（SPI1 SCLK） | — |
| DIN | PA7（SPI1 MOSI） | — |
| DOUT | PA6（SPI1 MISO） | — |
| nCS | PA4（GPIO） | — |
| DRDY | PC4（EXTI4） | 下降沿中断 |
| nRESET | **PA8**（GPIO） | 低有效，脉宽 ≥800 ns |
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
| REFP / REFN | 内部 2.442 V 基准 | 外接 1 µF 电容 |
| REFEXT | MIN 2.0 V / MAX AVDD−0.5 V | 本设计用内部基准，此脚可不接 |
| VNCP | 1 µF → AVSS | 内部电荷泵 |

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
| CD | SD_CD | **PB9** | 卡座机械开关，插卡拉低；内部上拉，EXTI9 下降沿 |
| WP | — | — | **不接**（E.11） |

**供电与控制**：`3.3V_D → 高边开关 → 3V3_SD`，开关使能 = **PB13 (SD_PWR_EN)**，默认低（断电）。
高边开关 Rds(on) **< 100 mΩ**（写瞬态 80–100 mA）。
**若省掉该开关，TF 卡待机 50–100 µA 会直接压垮 E.8.6 的 ≈7.4 µA 预算。**

**走线规则**：D0–D3 + CMD 等长 **±5 mm**；CK **±10 mm**（允许略短，不允许长）；
串阻靠 MCU 端；6 根线从 PC 端口一侧扇出，**不穿越模拟区**。

**时钟源**：SDMMC1 kernel clock **不得用 SYSCLK/PLL1R**；取 PLL2Q=48 MHz 或 CLK48。
现 IOC 中 PLL2Q = 258 MHz，**生成代码前必须重配**（E.10 #14）。

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

### 被测件接口（J2）— XH2.54-2P 卧式座

| 引脚 | 网络 | 说明 |
| --- | --- | --- |
| 1 | T（顶端偏置 ~3.0 V） | 经 R_top 10 kΩ 接 3.3V_A |
| 2 | S（样品底端） | 经 K3 到 M 点 → OPA388 → AIN0N |

### 调试口（J3）— 6P 排针

| 引脚 | 信号 | 说明 |
| --- | --- | --- |
| 1 | 3V3_D | — |
| 2 | GND | — |
| 3 | SWDIO (PA13) | — |
| 4 | SWCLK (PA14) | — |
| 5 | NRST | MCU 复位 |
| 6 | SWO (PB3) | TRACESWO |

### TMP117 温度探头（J4）— 4P 焊盘（1.25 mm 间距，连接器用户自选）

| 引脚 | 信号 | 说明 |
| --- | --- | --- |
| 1 | 3V3_D (VDD) | — |
| 2 | GND | — |
| 3 | SCL (PB6) | I²C1，4.7 kΩ 上拉 |
| 4 | SDA (PB7) | I²C1，4.7 kΩ 上拉 |

> 仅四线，**无 ALERT**；采购须 ADD0 接地版（地址 0x48）。

### TF 卡座（J6）— micro SD 8P 卧贴（2026-10-14 新增）

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
| CURR_DIS | PB10 | BSS138 关断控制 | 高 = 关断 |
| ANA_EN | PB12 | TPS7A2033 EN | 高 = 模拟域上电 |
| **SD_PWR_EN** | **PB13** | 高边开关使能 | 高 = TF 卡上电，默认低 |
| **VBUS_MON** | VBUS 分压中点 | **PC1**（ADC） | 比 0.5；阈值 3.70 V |
| **VBAT_MON** | 电池分压中点 | **PC0**（ADC） | 比 0.5；报警 3.65 V / 停测 3.50 V |

---

## 6. CubeMX 落地注意

- 手改 IOC 加 IP 块会被 CubeMX **静默丢弃**（已实测踩坑）——必须在 **GUI 里配**，配完 Save 让 CubeMX 重写 IOC。
- 操作清单见 [`firmware/DE-DRM/CUBEMX_SETUP.md`](../../firmware/DE-DRM/CUBEMX_SETUP.md)。
- 当前 `DE-DRM.ioc`（commit `cb91980` 版）仍缺：SPI1 IP、USART2、USB_OTG_FS、ADC1、SDMMC1、CRS、PC4 EXTI、PB12/PC5 等；
  且 PA6/PA7 已挂 SPI1 信号但 SPI1 IP 未启用 → **孤儿信号，CubeMX 打开会报冲突**。
