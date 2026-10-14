# DE-DRMS 引脚分配总表

> STM32U545RET6Q LQFP-64 · ADS131A02 · 连接器 · 2026-10-14 定稿
>
> 来源：主文档 E.6（MCU）、E.4（ADC）、E.9（连接器）

---

## 1. MCU 引脚分配（STM32U545RET6Q LQFP-64）

| 功能块 | 信号 | MCU 引脚 | 说明 |
| --- | --- | --- | --- |
| **USB OTG FS** | DM / DP | PA11 / PA12 | 固定复用，FT_u 由 VDDUSB 供电 |
| | VBUS 检测 | PA9 | OTG_FS_VBUS（5 V 容忍）；BC1.2 充电口检测 |
| **SWD 调试口** | SWDIO / SWCLK / SWO / NRST | PA13 / PA14 / PB3 / 引脚 7 | SWO=PB3 默认 TRACESWO |
| **调试日志** | USART2 TX / RX | PA2 / PA3 | 预留焊盘 |
| **ADS131A02** | SCLK / MISO / MOSI | PA5 / PA6 / PA7 | SPI1（AF5），模式 1（CPOL=0/CPHA=1） |
| | nCS | PA4 | GPIO |
| | DRDY | PC4 | EXTI4，下降沿 |
| | nRESET | PB0 | 低有效，脉宽 ≥800 ns |
| **R_ref 切换** | SEL_K1 | PC5 | K1（样品回线，NO）：高 = 通 |
| | SEL_K2 | PC3 | K2（R_ref 回线，NC）：低 = 通；与 SEL_K1 互锁 |
| | SEL_SENSE | PB2 | 测量线对（K3/K4） |
| **恒流源** | CURR_DIS | PB10 | 高 = 关断、低 = 开启；复位/高阻默认 = 开启 |
| **电源管理** | ANA_EN | PB12 | TPS7A2033 EN；EN 内置 smart pulldown |
| | VBAT_MON | PC0 | 电池分压（2×1 MΩ + 100 nF，常通 ~2 µA） |
| | ISET_HI | PB4 | BQ24040 充电电流切换（500 mA↔1 A） |
| **TMP117** | SCL / SDA | PB6 / PB7 | I²C1（AF4），4.7 kΩ 上拉在主板侧 |
| | ALERT | PB8 | 可选（成品探头常不带此线） |
| **NTC 备选** | AIN | PC1 | 2P 焊盘预留，不贴 |
| **档位 LED ×4** | 绿 / 黄 / 橙 / 红 | PC6 / PC7 / PC8 / PC9 | 灌电流驱动，同一时刻只亮一档 |
| **状态 LED** | PWR/USB | PA8 | — |
| **按键 ×2** | PWR_BTN / MEAS_BTN | PB1 / PA0 | 内部上拉、低有效；PB1=WKUP4、PA0=WKUP1 |
| **HSE 焊盘预留** | OSC_IN / OSC_OUT | PH0 / PH1 | 16 MHz 晶振焊盘不贴，引脚不他用 |
| **BOOT0** | — | PH3（引脚 60） | 10 kΩ 下拉 |

### MCU 电源脚

| 引脚 | 连接 | 去耦 |
| --- | --- | --- |
| VDD 19/32/64 + VSS 18/31/47/63 | 3.3V_D | 每对 100 nF + 共 10 µF |
| VDDA(13) / VSSA(12) | 3.3V_D | 100 nF + 1 µF（内部 ADC 不用作测量） |
| VDDUSB(48) | 3.3V_D | 100 nF |
| VBAT(1) | 接 VDD | 无后备电池（锂电 4.2 V 超 VBAT 上限 3.6 V） |
| VCAP(30) | 4.7 µF 到地 | ±20 %，ESR<20 mΩ @3 MHz，耐压 ≥10 V |

### 预留脚

PA1（WKUP3）、PA15、PC2、PC10、PC11、PC12、PB5、PB9、PB13、PB14、PB15、PD2。

其中 **PB13/PB14/PB15 + PB9 恰为完整 SPI2**——留给未来 PT100+MAX31865 扩展。PC13 不用（经 VSW 供电，仅 3 mA/30 pF）。

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
| nRESET | PB0（GPIO） | 低有效，脉宽 ≥800 ns |
| XTAL1 / XTAL2 | 16.384 MHz 晶振 | 负载电容按手册 Figure 36b |

### 必接脚（原理图阶段勿漏）

| 引脚 | 连接 | 说明 |
| --- | --- | --- |
| RESV(16) | IOVDD | 手册明写 "connect to IOVDD"，不得悬空 |
| CAP(28) | 1 µF → GND | 内部数字 LDO 输出 |
| NC(24) | 10 kΩ → GND | 数字输出，须下拉或悬空 |
| NC(5–8) | AVSS 或悬空 | — |
| AVDD | 3.3V_A，≥1 µF 解耦 | 模拟电源 |
| IOVDD | 3.3V_D，≥1 µF 解耦 | 数字电源 |
| REFP / REFN | 内部 2.442 V 基准 | 外接 1 µF 电容 |
| REFEXT | MIN 2.0 V / MAX AVDD−0.5 V | 本设计用内部基准，此脚可不接 |
| VNCP | 1 µF → AVSS | 内部电荷泵 |

---

## 3. 连接器引脚分配

### USB Type-C（J1）

| 引脚 | 连接 | 说明 |
| --- | --- | --- |
| A1/B12 (GND) | GND | — |
| A4/B9 (VBUS) | BQ24040 IN | 5 V 输入 |
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

### TMP117 温度探头（J4）— 4P 焊盘（1.25 mm 间距，用户自选连接器）

| 引脚 | 信号 | 说明 |
| --- | --- | --- |
| 1 | 3V3_D (VDD) | — |
| 2 | GND | — |
| 3 | SCL (PB6) | I²C1，4.7 kΩ 上拉 |
| 4 | SDA (PB7) | I²C1，4.7 kΩ 上拉 |

> ALERT (PB8) 不在 4 线内则弃用；采购须 ADD0 接地版（地址 0x48）。

### NTC 备选（J5）— 2P 焊盘，不贴

| 引脚 | 信号 | 说明 |
| --- | --- | --- |
| 1 | PC1 (AIN) | Q16A |
| 2 | GND | — |

---

## 4. 信号网络汇总

| 网络名 | 起点 | 终点 | 说明 |
| --- | --- | --- | --- |
| 3.3V_D | TPS7A0233 OUT | MCU VDD、USB、LED、TMP117、ADS131A02 IOVDD | 数字域，常开 |
| 3.3V_A | TPS7A2033 OUT | ADS131A02 AVDD、OPA388×3、OPA333、TMUX、VSET、R_top/R_b | 模拟域，EN 受控 |
| T | R_top/R_b 偏置节点 | 样品顶端、R_ref 顶端、OPA388(T) 输入 | ~2.97–3.07 V |
| S | 样品底端 | K3 → M → OPA388(S) 输入 | 2.03–2.99 V |
| M | K3/K4 汇合点 | OPA388(S) 输入 | 测量=S，校准=R_ref |
| B | BSS138 源极 / Rsense 顶端 | OPA388(B) 输入 | ~1.18 V |
| E | Rsense 底端 = GND | AIN1N（Kelvin 引线） | 0 V |
| VSET | 360 kΩ/200 kΩ 分压 | OPA333 + → BSS138 Gate | 1.179 V |
| CURR_DIS | PB10 | BSS138 关断控制 | 高 = 关断 |
| ANA_EN | PB12 | TPS7A2033 EN | 高 = 模拟域上电 |
