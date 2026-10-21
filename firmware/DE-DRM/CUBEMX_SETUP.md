# DE-DRM CubeMX 工程配置清单

> STM32U545RET6Q LQFP-64 · 配套 `DE-DRM.ioc` · **2026-10-14 重排定稿 + 二轮复核**
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
  **现 IOC 的 PLL2Q = 258 MHz、`RCC.SDMMCFreq_Value = 80 MHz`（2026-10-16 读 IOC 文件实测，远超 24 MHz）**；
  需把 PLL2Q 重配到 48 MHz（或 SDMMC 改吃 CLK48）。**SDMMC 不得用 SYSCLK/PLL1R**（E.10 #14）
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

### 2.2 USART1 — 调试日志（🟥 当前 IOC 完全没有）

- [ ] Mode：**Asynchronous**（自动占 **PA9/PA10**）
- [ ] Baud Rate **115200** / Word Length 8 / Stop 1 / Parity None / Flow Control None / Mode TX/RX
- [ ] ⚠️ **2026-10-20 二次重排：由 LPUART1(PA2/PA3) 改为 USART1(PA9/PA10, AF7)**——与 SWD(PA13/14)、
  SWO(PB3) 同侧组成右侧调试区，J3 由 6P 扩为 8P（§ 4 J3 表）；PA2/PA3 让给 ADC_nRESET/ADC_DRDY。
  原 LPUART1 配置作废，GUI 里**删除 LPUART1、新增 USART1**。

### 2.3 USB（USB_DRD_FS）— Type-C 数据上行（🟥 当前 IOC 完全没有）

- [ ] Mode：**Device only**（外设为 USB_DRD_FS，device/host 双角色；本设计用 device）
- [ ] 引脚自动占用：**PA11(DM) / PA12(DP)**
- [ ] **SOF 不占引脚**：CRS 用**内部 SOF 信号**同步（E.10 #15 已销号）；PA8 已转预留、ADC_nRESET=PA2，无冲突
- [ ] **VBUS sensing：无此选项**（STM32U5 的 USB 不提供；勿再找）
  → USB 在线检测改走 **PC1 的 ADC**（见 § 2.6）
- [ ] **BC1.2 BCD**：U545 设备模式**片内支持**（DS14216 §3.47 末条）——E.8.4 的 DCP 判 1 A 依赖它；
  使能路径（寄存器/HAL）DS14216 不载，**待 RM0456**（E.10 #17），生成代码后需补此项
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
  - **PC0 → 通道 1（IN1）**（VBAT_MON，2×1 MΩ 分压），Rank **1**，Sampling time 取 **≥64 Cycles**（见下方档位说明）
  - **PC1 → 通道 2（IN2）**（VBUS_MON，1 MΩ/1 MΩ 分压），Rank **2**，Sampling time 取 **≥64 Cycles**
    —— 通道号已按 DS14216 Table 27 核实（2026-10-14 二轮复核，E.10 #12① 销号）
  - **Internal channels → Vrefint**，Rank **3**，Sampling time 取 **≥320 Cycles**
    —— **依据（2026-10-16 勘误）**：DS14216 **Table 37** `tS_vrefint = 12.65 µs typ` 才是"读 VREFINT 时的采样时间"，
    16 MHz 下 ≈**202 周期** → 取 320 周期（20 µs）留余量；**此前写的"最小 ≥4 µs"是误引**，
    4/6 µs 是同一张表的 `tstart_vrefint`＝**基准缓冲启动时间**，与采样时间两回事。
    Table 37 注 2 另说"最短采样时间需按应用多次迭代确定" → 上板实测校。
  - 🟨 **档位名待核（E.10 #17④）**：本清单旧版写的 "47.5 / 247.5 Cycles" 在 **DS14216 查无出处**
    （手册只给 `ts = 5…814` 周期，Table 105）。以 **CubeMX 下拉里实际存在的档位为准**，
    按上面两条判据就近**取大**即可，不必纠结原数值。
- [ ] ✅ **高阻源合法性已核（E.10 #12② 销号）**：DS14216 Table 106 的 RAIN 上限（12 bit 仅 470 Ω @ 180 ns）**注 3 明示
  "Values without external capacitor"**——两路节点各带 100 nF ≫ 2^12×CADC(5 pF)≈20.5 nF，
  单次采样电荷扰动 ≪1 LSB（注 5 的 470 Ω 还是"扫描模式 + 上通道接 VREF+、本通道接 VREF−"的最坏情形，本设计仅 3 Rank 慢轮询，余量更大）。
  **固件约束：两路只做 ≥100 ms 级轮询、不得高速连扫**
  （分压 Thevenin 500 kΩ × 100 nF → τ=50 ms）；电压是慢变量，秒级轮询足够
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
| **EXTI15_10** | ✓ | **4** | PA15 SD_CD |
| **SDMMC1** | ✓ | **4** | 持续写吞吐敏感，优先级最高 |
| **EXTI3** | ✓ | 5 | PA3 ADC_DRDY |
| SPI1 | ✓ | 6 | ADS131A02 |
| I2C1 event / error | ✓ | 7 | TMP117 |
| **USART1** | ✓ | 8 | 调试日志（PA9/PA10, AF7） |
| USB | ✓ | 9 | USB（USB_DRD_FS） |
| ADC1 | ✓ | 10 | 电池/VBUS 监测 |
| SysTick | ✓ | **15** | HAL 时基，最低 |

- [x] Priority Group = 4 bits preempt / 0 bits sub（IOC 已设）
- [x] **2026-10-21 已按本表写入 IOC**（8 个中断：EXTI15_10/EXTI3/SPI1/I2C1_EV/I2C1_ER/USART1/ADC1/SDMMC1）
  —— 格式与项目历史一致（9 字段），静态核验通过

> ⚠️ **本次 IOC 改动未经 CubeMX GUI 复存**（无头模式无法保存：`xvfb-run` 下 CLI 只能加载不能写盘）。
> **首次在 GUI 打开时请确认**：① ADC1 采样时间显示 **68 Cycles**（不是 5）；② NVIC 表 8 个中断已勾选且优先级如上；
> ③ SYS → Debug = **Trace Asynchronous SW**。若 GUI 里任一项回落，说明该键被 CubeMX 归一化覆盖，需在 GUI 重设。

---

## 3.5 ADC1 采样时间（2026-10-21 修正）

| 通道 | 引脚 | 采样时间 | 依据 |
|---|---|---|---|
| VBAT_MON | PC0 / ADC1_IN1 | **68 Cycles** | AGENTS 硬约束 ≥64 周期；离散档只有 5/6/12/20/36/68/391/814 → 就近取大 |
| VBUS_MON | PC1 / ADC1_IN2 | **68 Cycles（待补）** | 同上。**当前 IOC 只配了 1 个通道（IN1）**，IN2 需在 GUI 里加进 Rank 1/2 |

> ⚠️ **IOC 现状：ADC1 只排了 1 个规则转换（IN1）**。设计需要 PC0(VBAT) + PC1(VBUS) 两个通道 + VREFINT 内部通道。
> 需在 ADC1 参数设置里把 **Number of Conversion 改为 3**，Rank1=IN1、Rank2=IN2、Rank3=Vrefint，
> 采样时间分别 68/68/391（VREFINT 要求 ≥320 → 取 391）。

---

## 4. GPIO 配置（按 E.6 重排定稿；Label 必须设，固件 `main.h` 会生成宏）

> ⚠️ **IOC 里已有的标签是重排前的旧映射**：PA8=PWR_LED、PB0=ADC_nRESET、PC3=SEL_K2、PC6–PC9=四色 LED。
> 按下表配置时**先清/移旧标签再设新标签**——尤其 PC8/PC9 现为 SD_D0/SD_D1（SDMMC 占用），
> 旧 LED 标签不删会导致信号名与 `main.h` 宏错乱。

### 4.1 输出（GPIO_Output，Push-Pull，Speed Low）

| 引脚 | Label | Pin state | 备注 |
|---|---|---|---|
| PA4 | ADC_nCS | **High** | 片选空闲高 |
| 🆕 **PA2** | **ADC_nRESET** | **High** | **原 PB0→PA8→PA2**（2026-10-20 二次重排，就近 ADC 簇）；低有效，脉宽 ≥800 ns |
| PB2 | SEL_SENSE | **Low** | TMUX 测量线对（SEL1/2/3 同沿） |
| 🆕 **PC2** | **ISET_HI** | **Low** | **2026-10-21 三排：由 PB4 迁来**（PB4 复位期 NJTRST+内部上拉，移走后普通 100 kΩ 下拉即可定义 Low = 500 mA） |
| 🆕 **PC3** | **ANA_EN** | **Low** | **2026-10-21 三排：PB15→PC3**（左侧模拟角）；TPS7A2033 EN，smart pulldown |
| 🆕 **PA8** | **SD_PWR_EN** | **Low** | **2026-10-21 三排：PB13→PA8**；TF 卡默认断电（省 50–100 µA） |
| **PB13** | **LED_GREEN** | **High** | **2026-10-21 三排**：灌电流，低 = 亮 |
| **PB14** | **LED_YELLOW** | **High** | 同上 |
| **PB15** | **LED_ORANGE** | **High** | 同上 |
| 🆕 **PB5** | **BQ_TS** | **Low** | **原 SEL_K1 已取消**（TMUX1134 整合）；Q1 栅极门控：高 = 旁路 TS NTC，默认低（R13 100 kΩ 下拉）= NTC 使能 |
| 🆕 **PB0** | **SEL_K2** | **High** | **2026-10-21 三排：PB8→PB0**（与 SEL_SENSE 聚为 24–27）；U10 SEL4，高 = 断，互锁：PB2=1 时不得为 0 |
| PB10 | CURR_DIS | **Low** | 高 = 关断；复位默认开启 |
| **PC6** | **LED_RED** | **High** | 灌电流，低 = 亮 |
| **PC7** | **PWR_LED** | **High** | 灌电流，低 = 亮 |

> **LED 簇 = PB13 / PB14 / PB15 / PC6 / PC7**（绿黄橙红 + 状态灯），**封装 34–38 五连脚（2.5 mm）**
> —— 2026-10-21 三排成果（原跨封装左右两侧 13.5 mm）。
> **TMUX/恒流控制簇 = PB0 / PB1 / PB2 / PB10**（封装 24–27 连续）。
> **模拟电源 ANA_EN = PC3**（左侧模拟角，与 PC0/PC1 监测、PA1–PA7 模拟簇同侧）。

### 4.2 输入（含上拉，按键/开关对地，低有效）

| 引脚 | Label | 模式 | Pull | Edge |
|---|---|---|---|---|
| PA0 | MEAS_BTN | **GPXTI0** | **Pull-up** | Falling |
| PB1 | PWR_BTN | **GPXTI1** | **Pull-up** | Falling |
| 🆕 **PA3** | **ADC_DRDY** | **GPXTI3** | **Pull-up** | **Falling**（DRDY 拉低 = 数据就绪；**2026-10-20 二次重排**，原 PC4→PA9→PA3；EXTI0/1/15 已占，EXTI3 空闲已核） |
| 🆕 **PA1** | **ADC_DONE** | **GPIO_Input** | **No Pull** | —（U7-18 DONE 帧完成指示，低有效，可选监视；**2026-10-20 新增，二次重排后落 PA1**） |
| 🆕 **PA15** | **SD_CD** | **GPXTI15** | **Pull-up** | Falling（插卡拉低；**原 PB9 未引出**；PA15 复位默认 JTDI，SWD 模式可作 GPIO；Table 27 注 4 说它复位期**内部上拉已使能**，与本设计所需方向一致，无冲突） |

> 🟥 **PA0 / PB1 当前 IOC 没设 Pull-up → CubeMX 黄灯**。
> 硬件上按键对地，**必须**内部上拉，否则浮空乱触发。
> 在引脚视图双击 → Signal 选 `GPXTI0`/`GPXTI1`（保留运行时 EXTI 能力），
> 右侧 GPIO 面板 Pull 选 **Pull-up**，再在 § 3.2 的 PWR 里勾 WKUP。
> **不要**把 Signal 直接选成 `PWR_WKUP1/4`——那样会丢运行时中断能力。

### 4.3 复用（勾 IP 后自动占用，只确认无黄/红）

| 引脚 | 信号 | 来自 |
|---|---|---|
| **PA9 / PA10** | **USART1_TX/RX（AF7）** | § 2.2（2026-10-20 由 LPUART1 改，J3 扩 8P） |
| PA5 / PA6 / PA7 | SPI1_SCK/MISO/MOSI | § 2.1 |
| PA11 / PA12 | USB_DM/DP（USB_DRD_FS） | § 2.3 |
| PA13 / PA14 / PB3 | SWDIO / SWCLK / SWO | § 3.1 |
| PB6 / PB7 | I2C1_SCL/SDA | § 2.4 |
| PC0 / PC1 | ADC1 通道（VBAT / VBUS） | § 2.6 |
| PC8–PC12 / PD2 | SDMMC1 D0–D3 / CK / CMD | § 2.5 |
| PC14 / PC15 | LSE | § 1.1 |
| PH0 / PH1 | HSE（焊盘预留不贴，见 § 1.1 红色项） | § 1.1 |

### 4.4 不配置（保持 Reset State 即正确）

**PB4**（预留）、**PB8**（预留）、**PC13**、PD 其余。
（PA1 已改 ADC_DONE、PA9/PA10 已改 USART1、PA8 已改 SD_PWR_EN、PB0 已改 SEL_K2 —— 均不再"不配置"；
2026-10-21 三排后预留由 PA8/PB0 变为 **PB4/PB8**。）

> ⚠️ **PC13 绝对不用**：经 VSW 供电，驱动能力仅 3 mA / 30 pF。
> ✅ **PB4 已释放（2026-10-21）**：ISET_HI 迁至 PC2 后，PB4 仅作预留，其 NJTRST 复用特性不再影响功能；
> 但仍建议 DEBUG 停在 `Trace_Asynchronous_SW`（SWD+SWO）。
> ⚠️ **BOOT0 (PH3)** 是 PCB 上 10 kΩ 下拉，**不在 CubeMX 里配**。

---

## 5. 电源脚（不在 CubeMX 配置，由原理图保证）

| 引脚 | 连接 |
|---|---|
| VDD **19/33/64** + VSS **18/32/47/63** | 3.3V_D（每对 100 nF + 共 10 µF；原 19/32/64 + 18/31/47/63 系按非 SMPS 版误写） |
| VDDA(13) / VSSA(12) | 3.3V_D + 100 nF + 1 µF（内部 ADC 不用于测量） |
| VDDUSB(48) | 3.3V_D + 100 nF |
| VBAT(1) | 接 VDD（锂电 4.2 V 超 VBAT 上限 3.6 V，**不可直连电芯**） |
| **VDD11 (31 与 62)** | **各 2.2 µF → VSS**（内核 LDO 输出；**RET6Q 无 VCAP**，原"VCAP(30)→4.7 µF"系按非 SMPS 版误写） |
| VLXSMPS(28) / VDDSMPS(29) / VSSSMPS(30) | 内部 SMPS 不启用的处置 **待 RM0456**（同族 U575 DS13737 写"接 GND"）→ 主文档 E.10 #17 |

> 🟥🟥 **RET6Q 是 SMPS 版 —— 本设计不启用内部 SMPS**（用外部双 LDO）。
> 生成代码后**必须人工核对** `Core/Src/main.c`：
> `HAL_PWREx_ConfigSupply(PWR_LDO_SUPPLY)` ← 应选这个；
> 复位后默认稳压器模式 DS14216 未载明（此前"选错 PWR_LDO_SUPPLY 则 MCU 完全不上电"系**推断**，已降级）
> → 待 RM0456 核实（E.10 #17）。
> ~~PDR_ON~~：**DS14216 无此脚**（F4/F7 遗绪，全文零命中），已删除。

---

## 6. 生成代码后必查（逐项人工确认）

- [ ] 🟥 `HAL_PWREx_ConfigSupply()` 实参 = **`PWR_LDO_SUPPLY`**（不是 SMPS；复位默认稳压器待 RM0456，E.10 #17）
- [ ] 🟥 `SystemClock_Config()` 里 PLL 源 = **MSI/MSIS**，**没有** `__HAL_RCC_HSE_ENABLE()`
- [ ] `MX_SDMMC1_SD_Init()` + `MX_FATFS_Init()` 已生成，SDMMC 时钟 ≤24 MHz
- [ ] `MX_GPIO_Init()` 覆盖 § 4.1/4.2 全部引脚；输出脚 `GPIO_NOPULL`、输入脚 `GPIO_PULLUP`
- [ ] `HAL_GPIO_WritePin()` 默认电平与 § 4.1 表一致（**尤其 PB13 = Low、PC2/PC3/PC6/PC7/PB14 = High**）
- [ ] ⚠️ **PB4 的复位态软件改不了**（Table 27 注 4：复位后 NJTRST + 内部上拉）→ 只核对生成代码把它配成推挽输出 Low，
      "上电瞬间即 500 mA"须由**原理图的外部下拉**保证，代码层无法兜住
- [ ] `HAL_PWR_EnableWakeUpPin(PWR_WAKEUP_PIN1 | PWR_WAKEUP_PIN4)` 存在（**已对手册核实**：PA0=WKUP1、PB1=WKUP4，Table 27 附加功能列）
- [ ] ADC 通道顺序 = VBAT(IN1) / VBUS(IN2) / Vrefint，采样时间按 § 2.6（**VBAT/VBUS ≥64 周期、VREFINT ≥320 周期 @16 MHz**）
- [ ] `make` 编译通过（arm-none-eabi-gcc；跨平台注意见根 README 与本节）

---

## 7. 待办依赖（不清会导致返工）

| 项 | 状态 |
|---|---|
| ~~**E.10 #12** DS14216/SLUS941 五项待核~~ | ✅ **2026-10-14 二轮复核全清**：① PC0=ADC1_IN1 / PC1=ADC1_IN2；② 高阻源合法（Table 106 注 3，见 § 2.6）；③ 低功耗表号 Table 62/65/68/70；④ BQ24040 PG 确有（pin 5）；⑤ SDMMC 全手册仅 PC8–PC12/PD2。另清出 4 处换脚（PC4/PC5/PB9/PB12 未引出）+ 电源脚更正 |
| **E.10 #16** IOC 时钟源与免晶振矛盾（现配 HSE-PLL，但 HSE 不贴） | 🔴 **阻塞固件**，§ 1.1 已列改法 |
| **E.10 #14** SDMMC 时钟源（现 IOC：PLL2Q 258 MHz、`SDMMCFreq_Value` 实测 **80 MHz** → 需重配到 48 MHz） | 🟥 阻塞生成代码 |
| ~~**E.10 #15** USB SOF 是否占 PA8~~ | ✅ **销号**：CRS 用**内部 SOF** 信号，不占引脚，PA8=ADC_nRESET 无冲突 |
| **E.10 #17**（新增）RM0456 四项：① USB_DRD_FS 片内 BCD 使能路径（固件项）；② SMPS 不启用时 VLXSMPS(28)/VDDSMPS(29) 引脚处置（**原理图前须确认**）；③ 复位后默认稳压器模式；④ **ADC1 采样时间离散档**（DS14216 未列，47.5/247.5 系凭惯例，按 GUI 实际档就近取大：VBAT/VBUS ≥64、VREFINT ≥320） | 🟥 ② 阻塞原理图；①③④ 固件/核对项，④ **不阻塞原理图** |
| **PB4 复位态（2026-10-16 新增，Table 27 注 4）**：PB4 复位后 = NJTRST + **内部上拉使能**，非 Low → "上电默认 500 mA"取决于外部 ISET 网络 | 🟥 **原理图阶段核**（需外部下拉或反相驱动，见 § 4.1） |
| **E.10 #13** TF 持续写实测（768 KB/s 是否丢帧） | 🔸 上板后 |
| 四张示意图按新 E.6 重画（SEL_K1/SEL_K2/LED 簇/ADC_nRESET 标注 + 加 TF 与 VBUS 支路；旧图中 DRDY(PC4)/SD_CD(PB9) 亦需改 PA9/PA15） | 🟥 交付门禁必跑 `tools/svg_schematic_check.py` |

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
| ADC 读数漂移/建立慢 | 高阻源合法性已核（100 nF 电荷池，§ 2.6）；若读数漂移先看**轮询间隔是否 <100 ms**（τ=50 ms 未充满）——不得高速连扫 |
| 上电/复位瞬间充电档不对（预期 500 mA 却跑到 1 A 附近） | **PB4 复位后是 NJTRST + 内部上拉，不是 Low**（Table 27 注 4，§ 4.1）→ 外部加下拉（阻值须明显强于内部上拉，RPU 值待 RM0456）或改反相驱动 |
| VREFINT 反推的 VDDA 偏差大 | 采样档给短了：读 VREFINT 需 **≥320 周期 @16 MHz（≈20 µs）**，依据 DS14216 Table 37 `tS_vrefint = 12.65 µs typ`（**不是** 4/6 µs，那是缓冲启动时间 `tstart_vrefint`） |
| CubeMX 里没有 47.5 / 247.5 Cycles 这一档 | 正常——DS14216 只给 `ts = 5…814` 周期，离散档属 RM0456/GUI 内容（E.10 #17④）。按 § 2.6 判据就近取大即可 |
| CubeMX 打开后我配的东西没了 | IOC 被 CubeMX 重写过。**每次改完 Save 后 `git diff` 核对** |
