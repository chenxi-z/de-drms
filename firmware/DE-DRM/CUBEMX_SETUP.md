# DE-DRM CubeMX 工程配置清单

> STM32U545RET6Q LQFP-64 · 配套 `DE-DRM.ioc` · 2026-10-14
>
> 这份清单是把 `firmware/DE-DRM/DE-DRM.ioc` 配齐到**可生成代码、引脚零警告**
> 所需的全部 CubeMX GUI 操作。设计依据见
> [主文档 E.6–E.9](../../docs/design/2026-10-10-universal-signal-chain.md)、
> [引脚分配总表](../../docs/design/pin-assignment.md)。
>
> **使用方式**：在 CubeMX 里打开 `DE-DRM.ioc`，逐项打勾 `[x]`。
> 全部勾完 → `File → Save Project`（让 CubeMX 重写 IOC，固化格式）
> → `Project Manager → Generate Code`。
>
> ⚠️ **不要手改 IOC**：CubeMX 6.18 的 IOC 有内部"指纹"格式，
> 手写 IP 块它认不全（实测：SPI1/ADC1/USB/USART 写进去会被静默丢弃）。
> 必须走 GUI 操作。

---

## 0. 工程基础（Project Manager）

- [x] MCU：STM32U545RET6Q（已配）
- [x] Project Name：DE-DRM（已配）
- [x] Toolchain：Makefile（已配）
- [x] IDE：No IDE 或 STM32CubeIDE
- [ ] 标准库版本：STM32Cube FW_U5 V1.9.0+
- [ ] Heap/Stack：Heap 0x800 / Stack 0x800（IOC 已设）

---

## 1. 时钟方案（RCC + Clock Configuration）

设计依据：E.7。MCU 免晶振，USB 用 HSI48+CRS 校准。

### 1.1 RCC 模块（System Core → RCC）

- [ ] HSE：**Crystal/Ceramic Resonator**（焊盘预留，不贴；保留可贴晶振的备用路径）
- [ ] HSI：**ON**（系统默认）
- [ ] MSI：**ON**（默认 4 MHz；可作 SYSCLK 备用源）
- [x] LSE：**Crystal/Ceramic Resonator**（PC14/PC15 已配，给 RTC 用）
- [x] LSI：**ON**（给 RTC 备用 / IWDG）
- [ ] HSI48：**ON**（给 USB 用）

### 1.2 Clock Configuration 标签页

- [ ] SYSCLK = **160 MHz**：路径 HSE 16 MHz → PLL1 (M=1, N=10, R=1) → 160 MHz ✓ 已生效
- [ ] APB1/2/3 = 160 MHz（默认）
- [ ] **USB 时钟 48 MHz = HSI48**：选 HSI48 直连（不走 PLLQ），由 **CRS 模块从 USB SOF 实时校准**
- [ ] **ADC 时钟 = 16 MHz**：源 = RCC_ADC1CLK / SYSCLK 分频
- [ ] RTC 时钟 = LSE 32.768 kHz
- [ ] 48 MHz MUX（CK48）= HSI48

### 1.3 CRS（System Core → CRS）

- [ ] 启用 CRS
- [ ] Clock Source = **USB SOF**
- [ ] 这一步保证 HSI48 在 USB 通信时自动校准到 ±0.05%（USB FS 规范要求 ±0.25%）

---

## 2. 外设（Connectivity 栏）

### 2.1 SPI1 — ADS131A02 通信

- [ ] Mode：**Full-Duplex Master**
- [ ] 引脚自动占用：PA5(SCK) / PA6(MISO) / PA7(MOSI)
- [ ] Configuration → **Parameter Settings**：
  - Type：Full-Duplex Master
  - Direction：**2-Wire (only TX and RX)**
  - Data Size：**8 Bits**
  - First Bit：**MSB First**
  - Prescaler：**8**（160 MHz / 8 = 20 MHz；如嫌高选 16 → 10 MHz，ADS131A02 支持 20 MHz）
  - **CLKPolarity (CPOL)：Low (0)**
  - **CLKPhase (CPHA)：2 Edge** ← ADS131A02 用 SPI Mode 1，关键
  - NSS：**Disabled (Software)** ← 片选走 PA4 GPIO
  - NSSP Mode：Disabled
- [ ] 引脚 PA4 = **GPIO_Output**（ADC_nCS）

### 2.2 USART2 — 调试日志

- [ ] Mode：**Asynchronous**
- [ ] 引脚自动占用：PA2(TX) / PA3(RX)
- [ ] Parameter Settings：
  - Baud Rate：**115200**
  - Word Length：**8 Bits (without parity)** 或 9 Bits（看需要）
  - Stop Bits：**1**
  - Parity：**None**
  - Hardware Flow Control：**None**
  - Mode：**TX/RX**

### 2.3 USB_OTG_FS — Type-C 数据上行

- [ ] Mode：**Device only**
- [ ] 引脚自动占用：PA11(DM) / PA12(DP)
- [ ] **VBUS**：**ON**，自动占用 PA9
- [ ] Parameter Settings → **Device** 标签：
  - **Software bus turnround = ON**
  - **PHY Interface = Internal PHY**（U545 内置 USB PHY，不需外部）
  - **Enable VBUS senses = ON**（让固件检测 VBUS 是否在线，决定充电/USB 模式）
  - **Battery charging = ON**（让 BC1.2 检测生效，配合 BQ24040 充电电流切换）
- [ ] **Middleware** 标签（左侧 Application Program → USB_DEVICE）：
  - 勾选 USB_DEVICE
  - Class for FS device：**Custom_HID**（先用 HID，避免 CDC 在 Win/Linux 都要装驱动的麻烦）
    或 **CDC**（如果上位机走纯虚拟串口）

### 2.4 I2C1 — TMP117 温度探头

- [x] Mode：**I2C**（已配）
- [x] 引脚：PB6(SCL) / PB7(SDA)
- [ ] Parameter Settings：
  - **I²C Speed Mode：Fast**（400 kHz）
  - I²C Maximum Speed：**400 kHz**
  - 4.7 kΩ 上拉在主板侧（不在 MCU 内部使能）

### 2.5 ADC1 — 电池电压监测

- [ ] **ADC1 mode**：
  - Resolution：**12 Bits**（U545 ADC1 默认）
  - Clock：**16 MHz**（从 Clock Config 来）
  - Data Alignment：**Right**
  - Continuous Conversion：**Disabled**
  - Scan Mode：**Disabled**（只有两个通道，软件轮询）
- [ ] **Channel configurations → Regular Conversion**：
  - **Channel 5 = PC0**（VBAT_MON，2×1MΩ 分压后），Rank **1**，Sampling time **47.5 Cycles**
  - **Internal Channel Vrefint**（反推 VDDA），Rank **2**，Sampling time **247.5 Cycles**
    （Vrefint 需要长采样，手册规定最小 ≥ 4 µs）
- [ ] **Settings**：
  - **Overrun = OVR_Data holds**
  - **Convert mode = Offset calibration** 或 None（视精度需求）
  - Low-power auto-wait：可选启用

---

## 3. 系统模块（System & Core）

### 3.1 SYS

- [x] Debug：**SWD**（已配，PA13/PA14/PB3/NRST）
- [ ] Timebase Source：**SysTick**（不要用 TIM1/TIM2 占用定时器）

### 3.2 PWR — 唤醒引脚（关键，决定能否关机再开机）

- [ ] Power & Power Management → **Wake-up pins**：
  - 勾选 **WKUP1**（默认绑定 PA0）
  - 勾选 **WKUP4**（默认绑定 PB1）
  - WKUP1/4 输入配置：**Pull-up**（让按键在 Stop/Standby 不耗电、按下拉低）

### 3.3 RCC

见 § 1.1

### 3.4 RTC

- [x] 已启用，配置见 IOC 中 RTC 块（24 小时格式 / Binary / 127+255 分频 = 1 Hz）
- [ ] 校验：Configuration → Parameter Settings：
  - **Hour Format：24-hour**
  - **Calendar Format：Binary**（输出整数计数，固件自己解析）
  - **Asynchronous Prescaler：127**
  - **Synchronous Prescaler：255**
  - 实际时基 = 32768 / (127+1) / (255+1) = **1 Hz** ✓

### 3.5 NVIC — 中断优先级

| 中断 | Enable | Preempt | Sub |
|---|---|---|---|
| EXTI4 (ADC_DRDY) | ✓ | **5** | 0 |
| SPI1 global | ✓ | **6** | 0 |
| I2C1 event / error | ✓ | **7** | 0 |
| USART2 global | ✓ | **8** | 0 |
| USB OTG FS global | ✓ | **9** | 0 |
| ADC1 global | ✓ | **10** | 0 |
| SysTick | ✓ | **15** | 0（最低，HAL 时基） |

- [ ] **NVIC Priority Group = 4 bits preempt / 0 bits sub**（IOC 已设）

---

## 4. GPIO 配置（按 E.6 全部列出，逐项手配）

> 标签名（Label）必须在 CubeMX 里设，固件 `main.h` 会自动生成
> `#define ADC_nCS_Pin GPIO_PIN_4` / `#define ADC_nCS_GPIO_Port GPIOA`。

### 4.1 输出（GPIO_Output，Push-Pull，Speed = Low 默认即可）

| 引脚 | Label | Pin state | 备注 |
|---|---|---|---|
| PA4 | ADC_nCS | **High** | 片选空闲高 |
| PA8 | PWR_LED | **High** | 灌电流，低=亮 |
| PB0 | ADC_nRESET | **High** | 低有效复位 |
| PB2 | SEL_SENSE | **Low** | TMUX 线对 |
| PB4 | ISET_HI | **Low** | 500 mA 默认充电电流 |
| PB10 | CURR_DIS | **Low** | 恒流源默认开启 |
| PB12 | ANA_EN | **Low** | 模拟域默认关（smart pulldown） |
| PC3 | SEL_K2 | **High** | K2 NC，高=断开（默认测量态） |
| PC5 | SEL_K1 | **Low** | K1 NO，低=断开（默认测量态） |
| PC6 | LED_GREEN | **High** | 灌电流，低=亮 |
| PC7 | LED_YELLOW | **High** | 同上 |
| PC8 | LED_ORANGE | **High** | 同上 |
| PC9 | LED_RED | **High** | 同上 |

### 4.2 输入（含上拉，按键对地，低有效）

| 引脚 | Label | 模式 | Pull | EXTI |
|---|---|---|---|---|
| PA0 | MEAS_BTN | **GPXTI0** | Pull-up | 下降沿 |
| PB1 | PWR_BTN | **GPXTI1** | Pull-up | 下降沿 |
| PC4 | ADC_DRDY | **GPXTI4** | Pull-up | **下降沿**（DRDY 拉低 = 数据就绪） |

> **关键**：PA0/PB1 在 CubeMX 引脚视图右键 → 选 `GPXTI0` / `GPXTI1`
> 而不是 `PWR_WKUP1` / `PWR_WKUP4`——选 GPXTI 既保留运行时 EXTI 中断能力，
> 又能让 PWR 模块（§ 3.2）通过 WKUP 唤醒。两者**信号不冲突，CubeMX 自动合并**。

### 4.3 复用（自动占用，无需手动配，只确认 CubeMX 引脚视图无黄/红）

| 引脚 | 信号 | 来自 IP |
|---|---|---|
| PA2 / PA3 | USART2_TX / RX | § 2.2 |
| PA5 / PA6 / PA7 | SPI1_SCK / MISO / MOSI | § 2.1 |
| PA9 | OTG_FS_VBUS | § 2.3 |
| PA11 / PA12 | USB_OTG_FS_DM / DP | § 2.3 |
| PA13 / PA14 / PB3 | SWDIO / SWCLK / SWO | § 3.1 |
| PB6 / PB7 | I2C1_SCL / SDA | § 2.4 |
| PC0 | ADC1_IN5 | § 2.5 |
| PC14 / PC15 | OSC32_IN / OUT | § 1.1 |
| PH0 / PH1 | OSC_IN / OUT | § 1.1 |

### 4.4 未用引脚（保持 Reset State 即可）

PA1 / PA10 / PA15 / PB5 / PB8 / PB9 / PB13 / PB14 / PB15 / PC1 / PC2 / PC10 / PC11 / PC12 / PC13 / PD2 / PE? — 全部不配置。

> 其中 **PB9 / PB13 / PB14 / PB15 = SPI2 完整引脚组**，留给 PT100+MAX31865 扩展（E.6）。
> PC1 = NTC 备选 2P 焊盘（J5），不贴。

---

## 5. 电源脚（不通过 CubeMX 配置，由原理图保证）

> 这些不是 CubeMX 软件设置，是 PCB 硬件连接。列在此处便于核对：

| 引脚 | 连接 |
|---|---|
| VDD 19/32/64 + VSS 18/31/47/63 | 3.3V_D（每对 100 nF + 共 10 µF） |
| VDDA(13) / VSSA(12) | 3.3V_D + 100 nF + 1 µF（内部 ADC 不用作测量） |
| VDDUSB(48) | 3.3V_D + 100 nF |
| VBAT(1) | 接 VDD（锂电 4.2 V 超 VBAT 上限 3.6 V，不直连） |
| VCAP(30) | 4.7 µF 到地（±20%，ESR<20 mΩ @3 MHz，耐压 ≥10 V） |

> ⚠️ **RET6Q 是 SMPS 版**：内部 LDO 与 SMPS 二选一供电。本设计用外部双 LDO，
> SMPS 不启用——CubeMX 生成的 `HAL_PWREx_ConfigSupply()` 应选
> `PWR_LDO_SUPPLY`，**不要选 `PWR_SMPS_1V8_SUPPLIES_LDO`**。
> 这一步生成代码后**必须**人工核对 `Core/Src/main.c`，确保走 LDO 分支。

---

## 6. 生成代码后必查

- [ ] `Core/Src/main.c` 的 `MX_GPIO_Init()` 中：
  - `GPIO_InitStruct.Pin = ...` 包含上面 § 4.1/4.2 全部引脚
  - `HAL_GPIO_WritePin(...)` 的默认电平正确（与 § 4.1 表一致）
  - `GPIO_InitStruct.Pull = GPIO_NOPULL` 输出脚；`GPIO_PULLUP` 输入脚
- [ ] `MX_SYSCLK_Init` / `HAL_RCC_DeInit` 路径正常，SYSCLK = 160 MHz
- [ ] `MX_USB_DEVICE_Init()` 已被生成（如果勾了 USB_DEVICE middleware）
- [ ] `HAL_PWREx_ConfigSupply(PWR_LDO_SUPPLY)` ← SMPS 版必须显式选 LDO
- [ ] `PWR_WKUP1` / `PWR_WKUP4` 使能：`HAL_PWR_EnableWakeUpPin(PWR_WAKEUP_PIN1 | PWR_WAKEUP_PIN4)`

---

## 7. 当前 IOC 已包含 / 未包含

**已包含**（来自 `cb91980` 版本）：
- 时钟：HSE 16 MHz / LSE 32.768 kHz / PLL1 → 160 MHz / USB 48 MHz
- IP：DEBUG / I2C1 / LPBAM / MEMORYMAP / NVIC / PWR / RCC / RTC / SYS
- 引脚已设：PA0 / PA4 / PA6 / PA7 / PA8 / PB0 / PB1 / PB2 / PB4 / PB6 / PB7 / PB10 / PC3 / PC6 / PC7 / PC8 / PC9 + LSE/HSE + SWD + 虚拟脚
- 标签：见 IOC 中 `*_GPIO_Label=...`，与 § 4 一致

**需要你在 CubeMX 里补**（清单 § 1–§ 5 中带 `[ ]` 的项）：
- 启用 SPI1 IP，参数 + PA5 自动连（§ 2.1）
- 启用 USART2 IP + PA2/PA3（§ 2.2）
- 启用 USB_OTG_FS IP + PA11/PA12/PA9（§ 2.3）
- 启用 ADC1 IP + PC0（§ 2.5）
- 启用 EXTI4 PC4（§ 4.2）
- 启用 PB12 ANA_EN + PC5 SEL_K1（§ 4.1）
- PWR WKUP1/4 启用（§ 3.2）
- PA0/PB1 加内部上拉修复黄灯（§ 4.2）
- NVIC 各中断使能（§ 3.5）

完成上述后保存，让 CubeMX 重写 IOC，全部配置才"落地"。

---

## 8. 排障提示

| 症状 | 排查 |
|---|---|
| PA0/PB1 黄灯 | GPIO_Pull-Up 没生效，双击引脚在右侧 GPIO 面板勾 Pull-up |
| 时钟树红线 | PLLN/PLLP/PLLQ 配错，或 HSE_VALUE ≠ 16000000 |
| USB 红线 | HSI48 没开，或 CK48 MUX 没选 HSI48 |
| ADC1 红线 | ADC 时钟没配 / ADC 内核时钟 = 0 |
| 生成代码后编译失败 | `make` 看报错第一行；IOC 格式问题不会让代码编译失败，多半是 HAL 库版本不匹配 |
| 烧录进去 MCU 不上电 | 检查 SMPS vs LDO 选择（§ 5 末尾的 ⚠️） |
