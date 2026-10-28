# 2026-10-28 换型 STM32U575RGT6（原 U545RET6Q 缺货）

**型号变更**：MCU = **STM32U575RGT6**（C5270980）。同 LQFP-64，24–27 脚信号名变但**走线不改**。
- 575 **无 SMPS**：删除所有 REGSEL / 升频前降 <110 MHz / `PWR_SMPS_SUPPLY` 相关项（原 E.10 #16/#17 作废）。
- **VCAP(30) 必须接 2.2 µF 到地**（板上 C4 已布）；575 手册 DS13737。
- 24–27 脚按 575 命名：**PC4=CURR_DIS、PC5=PWR_BTN、PB0=SEL_K2、PB1=SEL_SENSE**。
- **不做 I²C/TMP117**（PB6/PB7 NC）；**TF 卡常电无 SD_PWR_EN**（PA8 NC）；**PA4 保持 ADS_CS 不作 DAC**。

# 2026-10-25 按已布线图纸更新

用户确认保留硬件（**2026-10-28 按 U575 改名**）：PA4=ADS_CS（输出High）、PC4=CURR_DIS（输出High）、
**PC4=CURR_DIS（输出High）、PC5=PWR_BTN（输入上拉）、PB0=SEL_K2（输出Low）、PB1=SEL_SENSE（输出Low）**；PA8=NC。
这四根普通GPIO可承担对应功能，SPI1保持软件NSS；PA4不能同时作为DAC输出。
当前IOC仅调整上述已有引脚配置，未手工增删IP；源码宏及PA8模拟态同步修正。

下方2026-10-24表中的PA4/PA8及PB0/PB2/PB10映射由本节取代。
旧IOC的其他修正仍需完成：PA1方向、PC1/ADC冲突、PC13输入、各初始电平等。
重新生成须先在临时副本核对，不能覆盖已有SMPS切换、FileX无卡容错和启动修复。
本轮临时副本使用CubeMX 6.18.1的`config load`与`project generate`测试：
`-q`与`-s`均未生成C/H源码；加载时还报告旧ADC CommonPathInternal/SelectedChannel等无效参数。
因此未将临时副本产物回填，**完整重新生成尚未完成**，仍需在CubeMX GUI纠正旧配置后生成。
当前源码已通过GPIO启动电平主机测试、ARM构建和3项SD启动回归，不代表新IOC已完整生成验证。

# CubeMX 当前修正清单（2026-10-24）

当前源代码已按直流首板目标修正，**DE-DRM.ioc仍为旧GUI基线**，不要直接Generate覆盖源码。
在CubeMX完成以下修改、Save并核对差异后再生成；本轮未手工增删IOC的IP块。

| GUI项 | 目标 |
| --- | --- |
| PA1 | ADS_DONE，GPIO_Input、NoPull |
| PA2 / PA3 | ADS_RESET输出Low；ADS_DRDY下降沿EXTI3、PullUp |
| PA4 / PA8 | **PA4 = ADS_CS 输出 High（2026-10-28 确认不作 DAC）**；**PA8 = NC 悬空**（TF 常电，取消 SD_PWR_EN） |
| PC1 | 从ADC1_IN2释放为BQ_EN输出Low |
| PC2 / PB5 | 从ISET_HI/BQ_TS改BQ_CHG/BQ_PG输入、PullUp |
| PC13 | USB_VBUS_N输入、PullUp（外部NPN检测） |
| PC3 / PB10 | ANA_EN输出Low；CURR_DIS输出High |
| PB0 / PB2 | SEL_K2 / SEL_SENSE输出Low；实际接SEL2与SEL1/3/4 |
| LED | PB13/14/15、PC6/7初始High（低亮） |
| 按键 | PA0/PB1下降沿、PullUp |
| SD_CD | PA15双沿、PullUp |
| ADC1 | 2个rank：IN1采样68周期、VREFINT采样391.5周期；删除IN2，不动PC1 |
| SPI1 | Mode1；SCK/MISO/MOSI引脚High速度，保留33 Ω，上板验证边沿 |
| I²C1 | 无TMP117，不在主程序初始化；以后需要时GUI重新启用 |
| PWR | **575 无 SMPS**：不需要 `PWR_SMPS_SUPPLY` / 升降压切换（原 RET6Q 相关项全部作废）；`HAL_PWREx_ConfigSupply` 用默认 LDO |
| SYSCLK | MSI→PLL 160 MHz，不启用未装的外部晶振 |
| SDMMC1 | 禁止在main外设初始化阶段调用；由FileX打开介质时初始化 |

生成后必须保留/复核这些源码修复：
- `main.h`、`gpio.c`、`adc.c`中的新引脚与rank，部分在非USER CODE区，会被旧IOC覆盖。
- `sdmmc.c`无卡/初始化失败记录`sd_init_status`并返回，不能Error_Handler；头文件导出该状态。
- FileX glue根据`sd_init_status`返回失败，不能无条件成功；挂载失败线程退出，不能忙等或全局关中断。
- main不初始化I²C/SD，供电切换在升频前；SPI输出速度不得回退Low。
- 编译和无卡/坏卡/正常卡上电测试；无卡仍应能调度与诊断。热插拔重试尚未实现。

USB描述符/取电策略尚未定稿：不要沿用“自供电+0mA”作验收，也不能仅改数字500mA就算合规。
PC13状态与USBX附着/脱离、BQ输入电流授权需要应用层联动，当前只有GPIO配置。
ADC采集/DMA/校准/TF连续记录尚缺，编译成功不等于整机已可测量。

以下旧清单保留作历史，和上表冲突时以上表为准。

---

# DE-DRM CubeMX 工程配置清单

> **STM32U575RGT6** LQFP-64 · 配套 `DE-DRM.ioc` · 引脚以 `docs/design/pin-assignment.md`（PCB 实测）为准
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

- [x] MCU：**STM32U575RGT6**（2026-10-28 换型；原 U545RET6Q 缺货。IOC 需改 Mcu.CPN 并复核 RCC/PWR）
- [x] Project Name：DE-DRM（已配）
- [x] Toolchain：Makefile（已配）
- [x] Heap 0x800 / Stack 0x800（IOC 已设）
- [ ] 标准库：STM32Cube FW_U5 V1.9.0+
- [ ] `File → Save Project` 后**核对 git diff**，确认 CubeMX 没把你刚配的东西又丢掉

---

## 1. 时钟方案（RCC + Clock Configuration）— 🔴 本节有一处必改错误

设计依据：E.7（2026-10-28 修订）。**首板贴 HSE 16 MHz**（X4 已贴），PLL 源可用 HSE 或 MSIS 任一；
**USB 必须用 HSI48+CRS 校准**（USB 时钟不走 PLL）。

### 1.1 RCC 模块（System Core → RCC）

- [ ] 🟥 **HSE 必须改为 `BYPASS Clock Source` 或干脆 `Disable`** ——
  ✅ **2026-10-28：HSE 已实贴，此矛盾解除**（E.10 #16 关闭）。IOC 可保持 `RCC_PLLSOURCE_HSE`，
  也可改 MSIS——两者都能跑。**原红色警告（HSE 不贴→PLL 锁不住）已作废**。
  照现状生成代码 → HSE 不起振 → PLL 锁不住 → **SYSCLK 无输出，MCU 跑不起来**（主文档 E.10 #16）
- [ ] 🟥 **PLL 源改 `MSIS`（MSI）**：`PLL Source Mux = MSI`，`PLLN` 相应重算使 SYSCLK = 160 MHz
  （MSI 出厂 4 MHz；`4 × N / R = 160`）。改完再确认 `HSE_VALUE` 不再被 PLL 链路引用
- [ ] HSI：**ON**
- [ ] MSI：**ON**（现作 SYSCLK 主路径）
- [ ] HSI48：**ON**（USB / CRS 用）
- [x] LSE：**Crystal/Ceramic Resonator**（PC14/PC15 已配，给 RTC）
- [x] LSI：**ON**
- [x] ✅ **2026-10-28 已按"贴晶振走 HSE"落定**：E.7 已改写，E.10 #16 关闭。
  ⚠️ 负载电容待优化：X4 负载 12 pF，板上 C1/C2 = 20 pF（实载 ≈13–15 pF，频偏 +10~30 ppm），
  对 SYSCLK 无影响；若日后要切 USB 时钟到 PLL 需降到 10 pF

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

### 2.4 I2C1 — **本版不启用**（2026-10-28）

- [x] 主程序**不初始化 I2C1**；PB6/PB7 保持 GPIO 模拟态/悬空。
- 本版无 TMP117（不做温度补偿，见主文档 E.5.2）。将来恢复时：GUI 勾 I2C1 Fast 400 kHz + 4.7 kΩ 上拉 + TMP117 探头。

- [x] Mode I2C，PB6(SCL) / PB7(SDA)
- [ ] Speed Mode：**Fast**（400 kHz）
- [ ] **ALERT 不接**（探头四线）；4.7 kΩ 上拉在主板侧

### 2.5 SDMMC1 — TF 卡 4-bit（2026-10-21 已配置，核对）

- [x] **Mode：`SD 4 bits Wide bus`**（PC8–PC12 + PD2；**不是** `SDIO 4 bits Wide bus`——
  SDIO 与 SD 卡语义不同，FileX uSD 驱动走的是 `HAL_SD_*` 不是 `HAL_SDIO_*`，选错无法识别 TF 卡）
- [x] Parameter Settings：
  - Clock Edge：**Rising**（与官方 `Fx_uSD_File_Edit` 一致）
  - Clock Power Save：**Disable**
  - Bus Wide：**4 bits**
  - Hardware Flow Control：**Disable**
  - Clock Div：**0**（48 MHz 直通；ClockDiv=2 → 12 MHz 浪费 4× 带宽余量）
- [x] **DMA 模式：无需在 GUI 里勾"DMA Settings"——SDMMC 用片上 IDMA，不经 GPDMA**
  （2026-10-21 查证 `stm32u5xx_hal_sd.c:1284-1285`：`HAL_SD_ReadBlocks_DMA` 直接写
  `IDMABASER + IDMACTRL = SDMMC_ENABLE_IDMA_SINGLE_BUFF`，完全片上，不消耗 GPDMA 通道。
  FileX `fx_stm32_sd_driver_glue.c:118` 就是调这个 API。）
- [ ] 🟥 **不要选 CKIN**（SDR12/SDR25 以下不需反馈时钟；本设计 48 MHz 起步）
- [ ] **NVIC：`SDMMC1_IRQn` 抢占优先级 = 4**（中断里完成 IDMA 中断状态机的关键，低于 ThreadX 系统调用门限）

### 2.6 ADC1 — 电池 + VBUS 监测（2026-10-21 已配置，核对）

- [x] Resolution **12 Bits**、Clock **16 MHz**、Data Alignment **Right**（异步 DIV1）
- [x] Scan Mode：**Enabled（2 conversions）**；Continuous Conversion：**Disabled**
- [x] **Regular Conversion 已配 2 通道**：
  - **Rank 1 = IN1（PC0，VBAT_MON）**，采样时间 **68 Cycles**
  - **Rank 2 = IN2（PC1，VBUS_MON）**，采样时间 **68 Cycles**
- [x] **Vrefint 通道（2026-10-21 修正写法）**：
  - ✅ **不走 Rank**——勾 **ADC1 → Mode → "Vrefint Channel"**（虚拟引脚 `VP_ADC1_Vref_Input`）
  - ✅ **必须同步**在 ADC1 参数面板勾 `Common Path Internal → ChannelVREF`
    （IOC 键 `ADC1.CommonPathInternal=ADC_CHANNEL_VREFINT|null|null|null` + `ADC1.SelectedChannel=ADC_CHANNEL_VREFINT`；
    参照官方 U575 `LPBAM_ADC_IntExtChannelSwitch.ioc:368/378`）
  - ⚠️ **曾踩坑**：把 VREFINT 塞进 Rank 3 会让 CubeMX 报"非法通道"（U545 ADC1 的 VREFINT 不是规则通道），
    必须走 Common Path；本项 2026-10-21 已修正
  - 采样时间：Common Path 采样时间**单独**一项（`SamplingTime Common 1`），取 **391 Cycles**（≥320 周期判据）
- [ ] ✅ **高阻源合法性已核（E.10 #12② 销号）**：DS14216 Table 106 的 RAIN 上限（12 bit 仅 470 Ω @ 180 ns）**注 3 明示
  "Values without external capacitor"**——两路节点各带 100 nF ≫ 2^12×CADC(5 pF)≈20.5 nF，
  单次采样电荷扰动 ≪1 LSB。
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
| ~~I2C1 event / error~~ | — | — | **本版不用 I²C**（2026-10-28） |
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
| PH0 / PH1 | **HSE 16 MHz 已贴（X4 + C1/C2 20 pF + R1 1 MΩ）** | § 1.1 |

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
| ~~**E.10 #12** DS14216/SLUS941 五项待核~~ | ✅ **2026-10-14 二轮复核全清**：① PC0=ADC1_IN1 / PC1=ADC1_IN2；② 高阻源合法（Table 106 注 3，见 § 2.6）；③ 低功耗表号 Table 62/65/68/70；④ ~~BQ24040 PG（pin 5）~~ → 换 BQ24074 后 **PG = pin 7**；⑤ SDMMC 全手册仅 PC8–PC12/PD2。另清出 4 处换脚（PC4/PC5/PB9/PB12 未引出）+ 电源脚更正 |
| ~~**E.10 #16** IOC 时钟源与免晶振矛盾~~ | ✅ **2026-10-28 关闭**：HSE 实贴，矛盾消失 |
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

---

## 9. 2026-10-21 IOC 集中审查与回填（按官方例程对齐）

> **背景**：前一轮 GUI 改完后，仍有一批"GUI 默认值"与"官方 U545/U575 例程默认值"不一致。
> 本轮**对照官方 NUCLEO-U545RE-Q（ThreadX / FileX / USBX CDC_ACM）与 U575I-EV（Fx_uSD_File_Edit）例程**，
> 把 IOC 里缺失/错误的键一次性补齐。本节记录全部改动 + 未决项 + 复存 checklist。

### 9.1 本轮 IOC 自动修改项（已写入 `firmware/DE-DRM/DE-DRM.ioc`，需 GUI 复存确认）

#### SDMMC1
| 键 | 旧值 | 新值 | 依据 |
|---|---|---|---|
| `PC8.Mode` … `PD2.Mode` | `sdio_4_bits_Wide_bus` | **`SD_4_bits_Wide_bus`** | 官方 `Fx_uSD_File_Edit.ioc:87-98`；SDIO ≠ SD，FileX uSD 驱动走 `HAL_SD_*` |
| `SDMMC1.ClockDiv` | `2` | **`0`** | 官方 `hsd1.Init.ClockDiv = 0`（48 MHz 直通）；=2 会把 SD 时钟压到 12 MHz |
| `SDMMC1.BusWide` | （缺） | **`SDMMC_BUS_WIDE_4B`** | 官方 `hsd1.Init.BusWide = SDMMC_BUS_WIDE_4B` |
| `SDMMC1.ClockEdge` | （缺） | **`SDMMC_CLOCK_EDGE_RISING`** | 官方显式写出 |

#### FileX（全部补齐）
| 键 | 值 | 依据 |
|---|---|---|
| `FILEX.FX_SD_INTERFACE` | `1` | 官方 `Fx_uSD_File_Edit.ioc:9`；**缺它则 `fx_stm32_sd_driver_glue.c` 不生成** |
| `FILEX.FX_APP_MEM_POOL_SIZE` | `1024*4` | 官方 4 KB |
| `FILEX.FILEX_APPLICATION_THREAD_STACK_SIZE` | `1024*2` | 官方 2 KB |
| `FILEX.GLUE_FUNCTIONS` | `DMA_API` | 走 `HAL_SD_ReadBlocks_DMA`（内部 IDMA） |
| `FILEX.TRANSFER_NOTIFICATION` | `ThreadX_Semaphore` | DMA 完成用信号量唤醒 FileX 线程 |
| `FILEX.FX_DRIVER_SDMMC_INIT` | `1` | 由 FileX 驱动做 SD 卡初始化 |
| `FILEX.IPParameters` | 追加以上 6 项 | — |

#### ThreadX（全部补齐）
| 键 | 旧值 | 新值 | 依据 |
|---|---|---|---|
| `THREADX.TX_APP_MEM_POOL_SIZE` | `1024*3` | **`(3 * 1024)`** | 官方 `Tx_Thread_Creation.ioc:177` **带括号**；裸 `1024*3` 在代码生成时不被求值 |
| `THREADX.TX_APP_CREATION` | （缺） | `1` | 官方行 175 |
| `THREADX.TX_APP_GENERATE_INIT_CODE` | （缺） | `true` | 官方行 176 |
| `THREADX.TX_APP_THREAD_ENTRY` | （缺） | `MainThread_Entry` | 官方行 178 |
| `THREADX.TX_APP_THREAD_NAME` | （缺） | `Main Thread` | 官方行 179 |
| `THREADX.TX_APP_THREAD_PRIO` | （缺） | `5` | 官方行 180 |
| `THREADX.TX_DISABLE_PREEMPTION_THRESHOLD` | （缺） | `0` | 官方行 181 |

#### USBX CDC_ACM
| 键 | 旧值 | 新值 | 依据 |
|---|---|---|---|
| `USBD_CDCACM_EPIN_ADDR` | `2` | **`1`** | 官方 `Ux_Device_CDC_ACM.ioc:233`；2 与 EPINCMD 冲突 |
| `USBD_CDCACM_EPOUT_ADDR` | `3` | **`1`** | 官方默认 1；3 超出 FS IN EP 数 |
| `USBD_CDCACM_EPINCMD_ADDR` | （缺） | **`2`** | 官方行 232；CDC ACM 必须单独的通知端点 |
| `UX_DEVICE_CLASS_CDC_ACM_WRITE_AUTO_ZLP` | （缺） | `1` | 官方行 241；自动补 ZLP 否则主机在恰好 64B 包边界会挂 |
| `USBD_COMPOSITE_USE_IAD` | （缺） | `1` | 官方行 234 |
| `UX_APP_MEM_POOL_SIZE` | （缺） | `11*1024` | 官方行 239 |
| `USBX_SYS_SIZE` | （缺） | `4*1024` | 官方行 238 |
| `USBD_PID` / `USBD_PRODUCT_STRING` / `USBD_SERIAL_NUMBER` | （缺） | `22336` / `STM32 Virtual ComPort` / `CDC_ACM001` | 官方行 235-237（占位，量产前换自己的 VID/PID） |
| `USBD_VID` | （缺） | （默认 1155 = 0x0483 ST） | 官方默认 |
| `UX_SLAVE_REQUEST_DATA_MAX_LENGTH` | （缺） | `512` | 官方行 244 |
| `MAX_POWER_IN_MILLI_AMPER` | （缺） | `0` | 官方行 230 |
| `BSP.number` | （缺） | `1` | 官方行 227 |
| `UX_Device_Controller` | （缺） | `1` | 官方行 242；**缺它则 HAL PCD 不链接进 USBX** |
| `REG_USBX_DEVICE_CON_CK` | （缺） | `0` | 官方行 231 |

#### ADC1 — 启用 VREFINT（修前坑）
| 键 | 值 | 依据 |
|---|---|---|
| `ADC1.CommonPathInternal` | `ADC_CHANNEL_VREFINT\|null\|null\|null` | 官方 U575 `LPBAM_ADC_IntExtChannelSwitch.ioc:368` |
| `ADC1.SelectedChannel` | `ADC_CHANNEL_VREFINT` | 官方行 378 |
| `ADC1.IPParameters` | 追加上两项 | — |
| **曾错配** | ~~`ADC1.Channel-2=ADC_CHANNEL_VREFINT`~~ | U545 ADC1 的 VREFINT **不是规则通道**，塞 Rank 会被 CubeMX 拒 |

#### NVIC（12 处调整）
- `SavedPendsvIrqHandlerGenerated / SavedSvcallIrqHandlerGenerated / SavedSystickIrqHandlerGenerated` 三项 **`true → false`**
  （**ThreadX 必须接管 PendSV/SVCall/SysTick** 做上下文切换；官方 ThreadX 例程全是 false）
- 11 个外设中断**抢占优先级**（ThreadX 门限为 5，**SysTick=14 / TIM6=15 是 HAL 时基，不动**）：

| IRQ | 新优先级 | 原因 |
|---|---|---|
| SDMMC1 | **4** | 持续写吞吐最敏感，**但 < 5 意味着 ISR 内不可调 `tx_*`/`fx_*`**，只能在 ISR 里 `tx_semaphore_put`（允许） |
| EXTI15（SD_CD） | 5 | 拔插卡唤醒 |
| EXTI3（ADS_DRDY） | 5 | 128 kSPS 数据就绪 |
| SPI1 | 6 | ADS131A02 通信 |
| USB | **7** | 官方 U545 CDC_ACM 例程就是 7 |
| ~~I2C1_EV / I2C1_ER~~ | ~~8~~ | **本版不用 I²C**（2026-10-28 取消） |
| USART1 | 9 | 调试日志 |
| ADC1 | 10 | 慢速电池/VBUS 监测 |
| EXTI0/EXTI1（MEAS_BTN/PWR_BTN） | 11 | 按键，最低 |

### 9.2 未决 / 需 GUI 复存确认项

| 项 | 状态 | 说明 |
|---|---|---|
| **IOC 已被 CubeMX GUI 复存** | 🟥 **必须做** | 手改 IOC 后**首次**用 GUI 打开，GUI 会按键值重绘界面；**Save** 后本表所有改动才真正"入指纹"。若 GUI 打开后某项回落到默认，说明该键被归一化覆盖，需 GUI 重设。 |
| **代码生成** | 🟥 **本机 headless 不可用** | 实测 `xvfb-run STM32CubeMX -s script.txt` / `-q` 在本环境均无法生成代码（脚本加载但不写盘）。请在 GUI 里 File → Generate Code。 |
| `ProjectManager.StackSize=0x800 / HeapSize=0x800` | 🟨 未改 | 主栈+堆各 2 KB 对 ThreadX 偏小；建议 GUI → Project Manager → Project → Linker Settings 把 HeapSize 调到 0x1000 |
| **GPDMA1** | ✅ **不需要配置** | 2026-10-21 查证：SDMMC 用片上 IDMA（`IDMABASER`），不经 GPDMA1/LPDMA1；SPI1 当前是 polling（20 MHz × 8 bit 远低于 GPDMA 必要阈值）；USB_DRD_FS 内嵌专用 DMA 也不经 GPDMA |
| **FreeRTOS/RT-Thread 残留** | ✅ 已清 | `Mcu.ThirdPartyNb=0` |
| **USB Class 已定为 CDC_ACM** | ✅ 与官方例程对齐 | 与 § 2.3 旧文"建议 Custom_HID"冲突——**以本表（CDC_ACM）为准**，理由：U545 官方有完整 CDC_ACM 例程可直接抄，Custom_HID 需自写报告描述符 |
| **E.10 #16 IOC 时钟源** | ✅ **已关闭** | HSE 实贴后 `RCC_PLLSOURCE_HSE` 合法；MSIS 可作备选 |
| **E.10 #14 SDMMC 时钟源** | ✅ **已默认 = CLK48**（`RCC.SDMMCClockSelection=RCC_SDMMCCLKSOURCE_CLK48`，`SDMMCFreq_Value=48000000`） | 与本设计一致，无需改 |

### 9.3 时钟树复核（2026-10-21）

| 信号 | 值 | 反推路径 |
|---|---|---|
| SYSCLK / HCLK / PCLK1/2/3 | **160 MHz** | MSIS 16 MHz → PLLM=3 → VCOIn=5.333 MHz → PLLN=10 → VCO=160 MHz → PLLR=1 |
| USB / SDMMC / RNG | **48 MHz** | CK48（HSI48 + CRS 内部 SOF 同步，无外部晶振） |
| ADC | **16 MHz** | 异步 MSIS 16 MHz / DIV1 |
| I2C1 / USART1 / SPI1 / LPUART1 | **160 MHz** | APB 总线 |
| SPI1 实际 | **20 MHz** | 160 MHz / 8 |
| RTC | LSE 32.768 kHz | PC14/PC15 已占用 |

✅ 与官方 `Tx_Thread_Creation.ioc` 同架构（仅 PLLM/N 取值不同，两者都合法）。  
🟨 `PLL2/PLL3` 输出显示 3.096 GHz 是**未启用残留**——不用即不关事，但建议 GUI 里把 PLL2/PLL3 全关以省电。

### 9.4 已知 Bug 记录（本次修复过程中发现并已改正）

| 时间 | 现象 | 根因 | 处置 |
|---|---|---|---|
| 2026-10-21 19:43 | 修改后 IOC 的 NVIC 行字段从 9 降到 7 | 我的 sed 正则把 `\:` 后接数字时误吞 | 第二轮脚本重建字段，全部恢复 9 字段格式 |
| 2026-10-21 19:51 | CubeMX headless 报 `MCU is unknown` | `load` 命令的路径被 CubeMX 拼到 `db/mcu/` 前缀下 | 不再尝试 headless，改由用户在 GUI 里 Generate Code |

