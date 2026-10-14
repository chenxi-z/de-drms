# DE-DRM CubeMX 工程配置清单

> STM32U545RET6Q LQFP-64 · 配套 `DE-DRM.ioc` · **2026-10-14 重排定稿**
>
> 这份清单是把 `firmware/DE-DRM/DE-DRM.ioc` 配齐到**可生成代码、引脚零警告**
> 所需的全部 CubeMX GUI 操作。设计依据见
> [主文档 E.6–E.11](../../docs/design/2026-10-10-universal-signal-chain.md)、
> [引脚分配总表](../../docs/design/pin-assignment.md)。
>
> **使用方式**：在 CubeMX 里打开 `DE-DRM.ioc`，逐项打勾 `[x]`。
> 全部勾完 → `File → Save Project`（让 CubeMX 重写 IOC，固化格式）
> → `Project Manager → Generate Code`。
>
> ⚠️ **不要手改 IOC 加 IP**：CubeMX 6.18 的 IOC 有内部"指纹"格式，
> 手写 IP 块会被**静默丢弃**（本仓已实测踩坑并回滚，见 AGENTS.md「已被否决」末条）。
> 必须走 GUI 操作。

---

## 0. 工程基础（Project Manager）

- [x] MCU：STM32U545RET6Q（已配）
- [x] Project Name：DE-DRM（已配）
- [x] Toolchain：Makefile（已配）
- [x] Heap 0x800 / Stack 0x800（IOC 已设）
- [ ] 标准库：STM32Cube FW_U5 V1.9.0+
- [ ] `File → Save Project` 后**核对 git diff**，确认 CubeMX 没把你刚配的东西又丢掉

---

## 1. 时钟方案（RCC + Clock Configuration）— 🔴 本节有一处必改错误

设计依据：E.7。**MCU 免晶振**（HSE 焊盘不贴），USB 用 HSI48+CRS 校准。

### 1.1 RCC 模块（System Core → RCC）

- [ ] 🟥 **HSE 必须改为 `BYPASS Clock Source` 或干脆 `Disable`** ——
  **当前 IOC 是 `Crystal/Ceramic Resonator` 且 `RCC_PLLSOURCE_HSE`，但 E.7 定稿 HSE 晶振不贴！**
  照现状生成代码 → HSE 不起振 → PLL 锁不住 → **SYSCLK 无输出，MCU 跑不起来**（主文档 E.10 #16）
- [ ] 🟥 **PLL 源改 `MSIS`（MSI）**：`PLL Source Mux = MSI`，`PLLN` 相应重算使 SYSCLK = 160 MHz
  （MSI 出厂 4 MHz；`4 × N / R = 160`）。改完再确认 `HSE_VALUE` 不再被 PLL 链路引用
- [ ] HSI：**ON**
- [ ] MSI：**ON**（现作 SYSCLK 主路径）
- [ ] HSI48：**ON**（USB / CRS 用）
- [x] LSE：**Crystal/Ceramic Resonator**（PC14/PC15 已配，给 RTC）
- [x] LSI：**ON**
- [ ] 若坚持"贴 16 MHz 晶振走 HSE"，则必须**回改主文档 E.7 的免晶振结论**并在 E.10 记录理由——
  二选一，不可维持"文档说不贴、IOC 用 HSE"的矛盾状态

### 1.2 Clock Configuration 标签页

- [ ] SYSCLK = **160 MHz**（源改为 MSI→PLL1 后重新校验）
- [ ] APB1/2/3 = 160 MHz（默认）
- [ ] **USB = 48 MHz 走 HSI48**，`CK48 MUX = HSI48`（不走 PLLQ）
- [ ] **ADC1 = 16 MHz**
- [ ] 🟥 **SDMMC1 = 48 MHz**，源选 **PLL2Q** 或 **CLK48**——
  **现 IOC 的 PLL2Q = 258 MHz，直接喂 SDMMC 会超频**；需把 PLL2Q 重配到 48 MHz
  （或 SDMMC 改吃 CLK48）。**SDMMC 不得用 SYSCLK/PLL1R**（E.10 #14）
- [ ] RTC = LSE 32.768 kHz

### 1.3 CRS（System Core → CRS）— 当前 IOC 缺这个 IP

- [ ] 启用 **CRS**（System Core 分类下，**独立 IP，光勾 USB 不算**）
- [ ] Clock Source = **USB SOF**
- [ ] 这是免晶振 USB 精度达标的关键（HSI48 出厂 ±1 %，USB FS 要求 ±0.25 %）

---

## 2. 外设（Connectivity 栏）

### 2.1 SPI1 — ADS131A02（🟥 当前 IOC 有 PA6/PA7 信号但 **SPI1 IP 未启用** = 孤儿信号，打开会报冲突）

- [ ] Mode：**Full-Duplex Master**（勾上后 PA5 自动进来）
- [ ] 引脚：**PA5 = SCK**、PA6 = MISO、PA7 = MOSI
- [ ] Parameter Settings：
  - Type：Full-Duplex Master
  - Direction：**2-Wire (only TX and RX)**
  - Data Size：**8 Bits**
  - First Bit：**MSB First**
  - Prescaler：**8**（160 MHz / 8 = 20 MHz；求稳可选 16 → 10 MHz，ADS131A02 支持 20 MHz）
  - 🟥 **CLKPolarity (CPOL) = Low (0)**
  - 🟥 **CLKPhase (CPHA) = 2 Edge** ← ADS131A02 用 **SPI Mode 1**，写错读不出数据
  - NSS：**Disabled (Software)** ← 片选走 PA4 GPIO
  - NSSP Mode：Disabled

### 2.2 USART2 — 调试日志（🟥 当前 IOC 完全没有）

- [ ] Mode：**Asynchronous**（自动占 PA2/PA3）
- [ ] Baud Rate **115200** / Word Length 8 / Stop 1 / Parity None / Flow Control None / Mode TX/RX

### 2.3 USB_OTG_FS — Type-C 数据上行（🟥 当前 IOC 完全没有）

- [ ] Mode：**Device only**
- [ ] 引脚自动占用：**PA11(DM) / PA12(DP)**
- [ ] 🟥 **确认 SOF 不映射到引脚**（SOF 常为 PA8，而 **PA8 现分配给 ADC_nRESET**，冲突！）
  —— 本设计不需对外 SOF，CRS 用内部 SOF 同步（E.10 #15）
- [ ] **VBUS sensing：无此选项**（STM32U5 的 OTG_FS 不提供；勿再找）
  → USB 在线检测改走 **PC1 的 ADC**（见 § 2.6）
- [ ] Middleware：Application → **USB_DEVICE**，Class 按上位机协议定（建议 **Custom_HID**，
  免 CDC 在 Win/Linux 装驱动；协议变更须 `shared/protocol/` 与 `docs/protocol/` 成对更新）

### 2.4 I2C1 — TMP117（已配，核对即可）

- [x] Mode I2C，PB6(SCL) / PB7(SDA)
- [ ] Speed Mode：**Fast**（400 kHz）
- [ ] **ALERT 不接**（探头四线）；4.7 kΩ 上拉在主板侧

### 2.5 SDMMC1 — TF 卡 4-bit（🟥 全新，当前 IOC 没有）

- [ ] Mode：**SDMMC 4-bit**（自动占 PC8=D0 / PC9=D1 / PC10=D2 / PC11=D3 / PC12=CK，
  CMD 选 **PD2**）
- [ ] Parameter Settings：
  - Clock division：**按 kernel 48 MHz 分频得 ≤24 MHz**（初始化用低速、握手后 SD 自主升速）
  - Clock division bypass：Disabled
  - Data timeout：0xFF（初值宽裕）
  - **Bus width：4 bits**
  - **Use DMA：ON**（SDMMC 自带 DMA；768 KB/s 靠 CPU 搬运会拖累采样链）
- [ ] 🟥 **不要选 CKIN**（SDR12/SDR25 以下不需反馈时钟；本设计 24 MHz 起步）

### 2.6 ADC1 — 电池 + VBUS 监测（🟥 当前 IOC 没有）

- [ ] Mode → Resolution **12 Bits**、Clock **16 MHz**、Data Alignment **Right**
- [ ] Continuous Conversion：**Disabled**；Scan Mode：**Disabled**（软件轮询两通道）
- [ ] **Channel configurations → Regular Conversion**：
  - **PC0 → 通道 5**（VBAT_MON，2×1 MΩ 分压），Rank **1**，Sampling time **47.5 Cycles**
  - 🟥 **PC1 → VBUS_MON（1 MΩ/1 MΩ 分压）**，Rank **2**，Sampling time **47.5 Cycles**
    —— **PC1 的通道号必须在 DS14216 的 ADC channel map 里核实**，不要照抄"IN6"这类猜测值
    （E.10 #12①；若 PC1 无 ADC 功能 → 改用 PC7 并重排 LED 簇）
  - **Internal channels → Vrefint**，Rank **3**，Sampling time **247.5 Cycles**
    （Vrefint 必须长采样，手册规定最小 ≥4 µs；用于反推 VDDA）
- [ ] 🟥 **高阻源采样精度待核**：VBAT_MON 2×1 MΩ、VBUS_MON 1 MΩ 都属高阻源，
  100 nF 电容作电荷池缓解；**DS14216 允许的源阻抗/采样时间待查**（E.10 #12②）——
  **这条同时影响既有 VBAT_MON 的 3.65/3.50 V 判据余量**，不只新增项
- [ ] Overrun = OVR_Data holds

---

## 3. 系统模块（System & Core）

### 3.1 SYS

- [x] Debug：**SWD**（PA13/PA14/PB3 + NRST）
- [ ] Timebase Source：**SysTick**（不要占用 TIM，本设计要留定时器）

### 3.2 PWR — 唤醒引脚（🟥 决定能否"关机后用按键开机"）

- [ ] Power & Power Management → **Wake-up pins**：
  - 勾 **WKUP1（PA0）** + **WKUP4（PB1）**
  - 两者的 **Pull-up 在低功耗模式下保持使能**（否则 Stop/Standby 下按键无法拉低、也唤不醒）

### 3.3 RTC（已启用，核对）

- [x] 已配：24 小时 / Binary / AsynchPrediv 127 / SynchPrediv 255 → 32768/128/256 = **1 Hz**
- [ ] Clock Configuration 里确认 **RTC 源 = LSE**（当前 IOC 的 RCC 块未显式声明，可能起不来）

### 3.4 NVIC — 中断优先级

| 中断 | Enable | Preempt | 说明 |
|---|---|---|---|
| **EXTI9_8** | ✓ | **4** | PB9 SD_CD |
| **SDMMC1** | ✓ | **4** | 持续写吞吐敏感，优先级最高 |
| EXTI4 | ✓ | 5 | PC4 ADC_DRDY |
| SPI1 | ✓ | 6 | ADS131A02 |
| I2C1 event / error | ✓ | 7 | TMP117 |
| USART2 | ✓ | 8 | 调试日志 |
| USB OTG FS | ✓ | 9 | USB |
| ADC1 | ✓ | 10 | 电池/VBUS 监测 |
| SysTick | ✓ | **15** | HAL 时基，最低 |

- [x] Priority Group = 4 bits preempt / 0 bits sub（IOC 已设）

---

## 4. GPIO 配置（按 E.6 重排定稿；Label 必须设，固件 `main.h` 会生成宏）

### 4.1 输出（GPIO_Output，Push-Pull，Speed Low）

| 引脚 | Label | Pin state | 备注 |
|---|---|---|---|
| PA4 | ADC_nCS | **High** | 片选空闲高 |
| 🆕 **PA8** | **ADC_nRESET** | **High** | **原 PB0**；低有效，脉宽 ≥800 ns |
| PB2 | SEL_SENSE | **Low** | TMUX 测量线对 |
| PB4 | ISET_HI | **Low** | 500 mA 默认充电电流 |
| 🆕 **PB5** | **SEL_K1** | **Low** | **原 PC5**；K1（NO），高 = 通 |
| PB10 | CURR_DIS | **Low** | 高 = 关断；复位默认开启 |
| PB12 | ANA_EN | **Low** | TPS7A2033 EN；smart pulldown，复位即断模拟域 |
| 🆕 **PB13** | **SD_PWR_EN** | **Low** | **TF 卡默认断电**（省 50–100 µA）；仅 `f_mount`/sync 后才允许拉低 |
| 🆕 **PB8** | **SEL_K2** | **High** | **原 PC3**；K2（NC），高 = 断，与 SEL_K1 互锁 |
| 🆕 **PC2** | **LED_GREEN** | **High** | **原 PC6**；灌电流，低 = 亮 |
| 🆕 **PC3** | **LED_YELLOW** | **High** | **原 PC7** |
| 🆕 **PC5** | **LED_ORANGE** | **High** | **原 PC8** |
| 🆕 **PC6** | **LED_RED** | **High** | **原 PC9** |
| 🆕 **PC7** | **PWR_LED** | **High** | **原 PA8**（PA8 让给 ADC_nRESET） |

> LED 簇落在 PC2/PC3/PC5/PC6/PC7、**断在 PC4**（ADC_DRDY）。
> 本想占满 PC2–PC6 连号，需把 DRDY 挪 PA10，但 **PA10 是否引出 LQFP-64 未经 DS14216 核实**，
> 不凭猜测占脚。同端口、仅隔一脚，扇出方向一致，可接受。

### 4.2 输入（含上拉，按键/开关对地，低有效）

| 引脚 | Label | 模式 | Pull | Edge |
|---|---|---|---|---|
| PA0 | MEAS_BTN | **GPXTI0** | **Pull-up** | Falling |
| PB1 | PWR_BTN | **GPXTI1** | **Pull-up** | Falling |
| PC4 | ADC_DRDY | **GPXTI4** | **Pull-up** | **Falling**（DRDY 拉低 = 数据就绪） |
| 🆕 PB9 | SD_CD | **GPXTI9** | **Pull-up** | Falling（插卡拉低） |

> 🟥 **PA0 / PB1 当前 IOC 没设 Pull-up → CubeMX 黄灯**。
> 硬件上按键对地，**必须**内部上拉，否则浮空乱触发。
> 在引脚视图双击 → Signal 选 `GPXTI0`/`GPXTI1`（保留运行时 EXTI 能力），
> 右侧 GPIO 面板 Pull 选 **Pull-up**，再在 § 3.2 的 PWR 里勾 WKUP。
> **不要**把 Signal 直接选成 `PWR_WKUP1/4`——那样会丢运行时中断能力。

### 4.3 复用（勾 IP 后自动占用，只确认无黄/红）

| 引脚 | 信号 | 来自 |
|---|---|---|
| PA2 / PA3 | USART2_TX/RX | § 2.2 |
| PA5 / PA6 / PA7 | SPI1_SCK/MISO/MOSI | § 2.1 |
| PA11 / PA12 | USB_OTG_FS_DM/DP | § 2.3 |
| PA13 / PA14 / PB3 | SWDIO / SWCLK / SWO | § 3.1 |
| PB6 / PB7 | I2C1_SCL/SDA | § 2.4 |
| PC0 / PC1 | ADC1 通道（VBAT / VBUS） | § 2.6 |
| PC8–PC12 / PD2 | SDMMC1 D0–D3 / CK / CMD | § 2.5 |
| PC14 / PC15 | LSE | § 1.1 |
| PH0 / PH1 | HSE（焊盘预留不贴，见 § 1.1 红色项） | § 1.1 |

### 4.4 不配置（保持 Reset State 即正确）

PA1（WKUP3 预留）、PA9、PA10、PA15、PB0、PB14、PB15、**PC13**、PD 其余。

> ⚠️ **PC13 绝对不用**：经 VSW 供电，驱动能力仅 3 mA / 30 pF。
> ⚠️ **PB4 (NJTRST) 作 GPIO 输出**：DEBUG 须停在 `Trace_Asynchronous_SW`（SWD+SWO），
> 该模式才释放 NJTRST；若误选别的调试模式，PB4 = ISET_HI 会被驱动逻辑抢走。
> ⚠️ **BOOT0 (PH3)** 是 PCB 上 10 kΩ 下拉，**不在 CubeMX 里配**。

---

## 5. 电源脚（不在 CubeMX 配置，由原理图保证）

| 引脚 | 连接 |
|---|---|
| VDD 19/32/64 + VSS 18/31/47/63 | 3.3V_D（每对 100 nF + 共 10 µF） |
| VDDA(13) / VSSA(12) | 3.3V_D + 100 nF + 1 µF（内部 ADC 不用于测量） |
| VDDUSB(48) | 3.3V_D + 100 nF |
| VBAT(1) | 接 VDD（锂电 4.2 V 超 VBAT 上限 3.6 V，**不可直连电芯**） |
| VCAP(30) | 4.7 µF 到地（±20 %，ESR<20 mΩ @3 MHz，耐压 ≥10 V） |
| PDR_ON | 🟥 **按 DS14216 处理，待核**（RET6Q 有 SMPS，此脚接法需确认，E.10 #12） |

> 🟥🟥 **RET6Q 是 SMPS 版 —— 本设计不启用内部 SMPS**（用外部双 LDO）。
> 生成代码后**必须人工核对** `Core/Src/main.c`：
> `HAL_PWREx_ConfigSupply(PWR_LDO_SUPPLY)` ← 必须是这个；
> 若 CubeMX 生成 `PWR_SMPS_1V8_SUPPLIES_LDO`，**MCU 会完全不上电**（VSW/VSD 供电路径改变）。

---

## 6. 生成代码后必查（逐项人工确认）

- [ ] 🟥 `HAL_PWREx_ConfigSupply()` 实参 = **`PWR_LDO_SUPPLY`**（不是 SMPS）
- [ ] 🟥 `SystemClock_Config()` 里 PLL 源 = **MSI/MSIS**，**没有** `__HAL_RCC_HSE_ENABLE()`
- [ ] `MX_SDMMC1_SD_Init()` + `MX_FATFS_Init()` 已生成，SDMMC 时钟 ≤24 MHz
- [ ] `MX_GPIO_Init()` 覆盖 § 4.1/4.2 全部引脚；输出脚 `GPIO_NOPULL`、输入脚 `GPIO_PULLUP`
- [ ] `HAL_GPIO_WritePin()` 默认电平与 § 4.1 表一致（**尤其 PB13 = Low、PC3/PC5/PC6/PC7/PC2 = High**）
- [ ] `HAL_PWR_EnableWakeUpPin(PWR_WAKEUP_PIN1 | PWR_WAKEUP_PIN4)` 存在
- [ ] ADC 通道顺序 = VBAT / VBUS / Vrefint，采样时间按 § 2.6
- [ ] `make` 编译通过（arm-none-eabi-gcc；跨平台注意见根 README 与本节）

---

## 7. 待办依赖（不清会导致返工）

| 项 | 状态 |
|---|---|
| **E.10 #12** DS14216/SLUS941 五项待核（**PC1 ADC 通道号**、**ADC 高阻源允许源阻抗**、SMPS 低功耗表号、BQ24040 有无 PG、SDMMC 备选脚映射） | 🔴 **阻塞原理图** |
| **E.10 #16** IOC 时钟源与免晶振矛盾（现配 HSE-PLL，但 HSE 不贴） | 🔴 **阻塞固件**，§ 1.1 已列改法 |
| **E.10 #14** SDMMC 时钟源（PLL2Q 258 MHz → 48 MHz） | 🟥 阻塞生成代码 |
| **E.10 #15** USB SOF 是否占 PA8 | 🟥 与 ADC_nRESET 冲突风险 |
| **E.10 #13** TF 持续写实测（768 KB/s 是否丢帧） | 🔸 上板后 |
| 四张示意图按新 E.6 重画（SEL_K1/SEL_K2/LED 簇/ADC_nRESET 标注 + 加 TF 与 VBUS 支路） | 🟥 交付门禁必跑 `tools/svg_schematic_check.py` |

---

## 8. 排障提示

| 症状 | 根因 / 排查 |
|---|---|
| PA0/PB1 黄灯 | GPIO Pull-up 没设。双击引脚在右侧面板选 Pull-up |
| PA6/PA7 报冲突或变红 | **SPI1 IP 未启用**，孤儿信号。§ 2.1 勾 Full-Duplex Master |
| 生成代码后 MCU 完全不上电 | **先看 `HAL_PWREx_ConfigSupply` 是不是 SMPS**（§ 5）；再看 PLL 源是否还吃 HSE（§ 1.1） |
| 上电跑起来但 USB 不枚举 | CRS 未启用，或 CK48 MUX 没选 HSI48（§ 1.3） |
| ADS131A02 读全 0 / 乱码 | **CPHA 没设 2 Edge**（ADS131A02 要 SPI Mode 1）；或 nCS/nRESET 默认电平错 |
| 写卡掉帧 / 卡死采样 | SDMMC DMA 未开；或 FatFS 擦除阻塞未做双缓冲；或 SDMMC 时钟超 24 MHz |
| 拔插卡后文件系统坏 | 未在 `f_mount`/sync 后才拉低 PB13；CD 中断未做卸载流程 |
| 待机掉电快 | TF 卡未断电（PB13 应默认低）；或 WKUP 脚上拉没在 PWR 里保持 |
| ADC 读数偏高/偏低且有增益误差 | 高阻源超手册允许值 → 加长采样时间或降分压阻值（E.10 #12②） |
| CubeMX 打开后我配的东西没了 | IOC 被 CubeMX 重写过。**每次改完 Save 后 `git diff` 核对** |
