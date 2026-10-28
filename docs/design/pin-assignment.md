# 引脚分配总表 — 按 STM32U575RGT6 已布线图纸（2026-10-28）

**型号：STM32U575RGT6（C5270980），LQFP-64。**
本表依据 **PCB 焊盘网络表逐脚实测**（115 网络 / U10 全部 64 焊盘，经 EDA API 读取），
不是按手册推导，可直接作为固件与改图依据。

> **换型说明（2026-10-28）**：原 STM32U545RET6Q 缺货（立创库存 0），换 575RGT6。
> 两片同为 LQFP-64，**24–27 脚信号名不同但物理脚位不变**，PCB 走线一根未改。
> 本表已按 575 实际信号名书写。545 对照见主文档 E.5.1。

## 主表（按封装脚序）

| 脚 | 引脚 | 网络 | 方向/模式 | 说明 |
| --- | --- | --- | --- | --- |
| 1 | VBAT | VCC | 电源 | 无后备电池 |
| 2 | PC13 | PC13 | 输入 上拉 | USB_VBUS 检测（外部 NPN 集电极，低 = VBUS 在） |
| 3/4 | PC14/PC15 | OSC32_IN/OUT | — | LSE 扩展焊盘（不贴） |
| 5/6 | PH0/PH1 | OSC_IN/OUT | — | HSE 扩展焊盘（不贴） |
| 7 | NRST | NRST | 复位 | — |
| 8 | PC0 | VBAT_MON | ADC1_IN1 | 电池分压；采样 68 周期 |
| 9 | PC1 | BQ_EN | 输出 Low | BQ24074 EN1 |
| 10 | PC2 | BQ_CHG | 输入 上拉 | 低 = 充电中 |
| 11 | PC3 | ANA_EN | 输出 Low | 模拟 LDO(U4) EN；R81 100 kΩ 下拉 |
| 12/13 | VSSA/VDDA | GND/VCC | 电源 | 100 nF + 1 µF |
| 14 | PA0 | MEAS_BTN | EXTI0 下降沿 上拉 | **WKUP1** |
| 15 | PA1 | ADS_DONE | 输入 | 无上下拉；经 33 Ω R61 |
| 16 | PA2 | ADS_RESET | 输出 Low | 经 33 Ω R62；R78 10 kΩ 下拉 |
| 17 | PA3 | ADS_DRDY | EXTI3 下降沿 上拉 | 经 33 Ω R60 |
| 18/19 | VSS/VDD | GND/VCC | 电源 | — |
| 20 | PA4 | ADS_CS | 输出 High | 经 33 Ω R56；软件 NSS。**不作 DAC** |
| 21/22/23 | PA5/PA6/PA7 | ADS_CLK/MISO/MOSI | SPI1 AF5 | Mode 1；各经 33 Ω（R57/58/59） |
| 24 | **PC4** | **CURR_DIS** | 输出 High | 恒流源抑制（BSS138 拉低 VSET）。**545 时代此脚为 PB0** |
| 25 | **PC5** | **PWR_BTN** | 输入 上拉 | 下降沿；**PWR_WKUP5**。**545 时代此脚为 PB1** |
| 26 | **PB0** | **SEL_K2** | 输出 Low | TMUX1134 SEL4。**545 时代此脚为 PB2** |
| 27 | **PB1** | **SEL_SENSE** | 输出 Low | TMUX1134 SEL1/2/3。**545 时代此脚为 PB10** |
| 28 | PB2 | — | **NC** | 545 时代为 VLXSMPS |
| 29 | PB10 | — | **NC** | 545 时代为 VDDSMPS |
| 30 | **VCAP** | — | **2.2 µF → GND** | **C4（CL21B225KAFNNNE）**。内核 LDO 输出，**不可接地短路** |
| 31/32 | VSS/VDD | GND/VCC | 电源 | 545 时代为 VDD11/VSS |
| 33 | **PB12** | VCC | — | 545 时代为 VDD |
| 34/35/36 | PB13/PB14/PB15 | LED_GREEN/YELLOW/ORANGE | 输出 High（低亮） | 灌电流驱动 |
| 37/38 | PC6/PC7 | LED_RED / PWR_LED | 输出 High（低亮） | 五灯簇 34–38 连续 |
| 39/40 | PC8/PC9 | SD_D0 / SD_D1 | SDMMC1 AF12 | 经 R44/R45 串阻；R53/R63 上拉 |
| 41 | **PA8** | — | **NC** | **本版不用**（原 SD_PWR_EN，已取消） |
| 42/43 | PA9/PA10 | USART1_TX/RX | AF7 | 调试串口 115200 |
| 44/45 | PA11/PA12 | PA11 / PA12 | USB_DRD_FS | Type-C。网络名即引脚别名 |
| 46 | PA13 | SWDIO | 调试 | — |
| 47 | VSS | GND | 电源 | — |
| 48 | VDDUSB | VCC | 电源 | — |
| 49 | PA14 | SWCLK | 调试 | — |
| 50 | PA15 | SD_CD | EXTI15 双沿 上拉 | 经 R46 至卡座 CD；R64 上拉 VCC。插卡低 |
| 51/52 | PC10/PC11 | SD_D2 / SD_D3 | SDMMC1 AF12 | 经 R13/R39；R16/R49 上拉 |
| 53 | PC12 | **SD_CLX**（=SD_CK） | SDMMC1 AF12 | 经 R43；R52 上拉。**网络上 `SD_CLX` 是图上笔误** |
| 54 | PD2 | SD_CMD | SDMMC1 AF12 | 经 R41；R50 上拉 |
| 55 | PB3 | SWO | 调试 | Trace_Asynchronous_SW |
| 56 | PB4 | — | **NC** | 预留 |
| 57 | PB5 | BQ_PG | 输入 上拉 | 低 = 输入电源有效 |
| 58/59 | PB6/PB7 | — | **NC** | **不接 I²C**（本版无 TMP117，见主文档 E.5.2） |
| 60 | PH3 | BOOT0 | — | 10 kΩ 下拉 |
| 61 | PB8 | — | **NC** | 预留 |
| 62 | PB9 | — | **NC** | 545 时代为第二 VDD11 |
| 63/64 | VSS/VDD | GND/VCC | 电源 | — |

## 关键约束

1. **PA4 = ADS_CS，不作 DAC**（575 上该脚有 DAC1_OUT1，本版不用）。
2. **TF 卡常电**：无 SD_PWR_EN，PA8 悬空。掉电安全只靠正常 `fx_media_close`/flush 一道防线。
3. **无 I²C / 无 TMP117**：PB6/PB7 保留为空，为将来温度补偿升级预留（加装不需改 MCU 侧布线）。
4. **VCAP（30 脚）必须接 2.2 µF 到地**——这是 575 与 545 最关键的电源差异，接错会损坏芯片。
5. **575 无 SMPS**：不需要任何 REGSEL / 升频前降频流程（原 E.10 #16/#17 作废）。
6. **U10 内部 TMUX1134/OPA 编号**见主文档附录 F；禁止沿用旧"PB2=SEL_SENSE、PB10=SEL_K2"的 545 描述。

## 待清理（不影响功能）

- `SD_CLX` 网络名建议改为 `SD_CK`（纯命名，不改走线）。
- `VLX`、`V11` 两个孤立网络（无任何焊盘使用）是 545 SMPS 时代残留，建议删除。
- `USB_DN`、`USB_DP` 两个空网络名同理（实际连接走 `PA11`/`PA12`）。
