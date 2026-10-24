# 引脚分配总表 — 直流首板目标（2026-10-24）

以主设计文档附录F为准。本表是用户待落实的改图目标，不声称远端V1.2已改。
STM32U545RET6Q，LQFP64。PA4/DAC与PA8封装位置经ST MCU XML核对；其他连接沿V1.2。

| 引脚 | 网络/模式 | 默认与连接 |
| --- | --- | --- |
| PA1 | ADS_DONE 输入 | 无内部上下拉，禁止推挽驱动ADC输出 |
| PA2 | ADS_RESET 输出 | 低，外部10 kΩ下拉；启动序列完成后释放 |
| PA3 | ADS_DRDY EXTI3 | 下降沿、内部上拉 |
| PA4（20脚） | 未来DAC1_OUT1 | 首板模拟态，不接VSET；禁止与Q3直接并联 |
| PA5/PA6/PA7 | SPI1 SCK/MISO/MOSI，AF5 | Mode1；PA5不能再当DAC输出 |
| PA8（41脚） | ADS_CS 输出 | 高；由原PA4迁来，保留33 Ω与ADC侧10 kΩ上拉 |
| PB2 | SEL_SENSE 输出 | 低；U10 SEL1/3/4，物理1/11/20脚 |
| PB0 | SEL_K2 输出 | 低；U10 SEL2，物理10脚 |
| PB10 | CURR_DIS 输出 | 高；Q3压低VSET，R29改100 kΩ上拉VCC |
| PC3 | ANA_EN 输出 | 低，外加100 kΩ下拉 |
| PC1 | BQ_EN 输出 | 低；连接BQ24074 EN1，保留R47下拉；不是CE充电开关，不再作为ADC1_IN2 |
| PC2 | BQ_CHG 输入 | 上拉VCC，低=正在充电；高不能独立证明充满 |
| PB5 | BQ_PG 输入 | 上拉VCC，低=输入电源状态有效；不能区分供电来源 |
| PC13 | USB_VBUS_N 输入 | 上拉VCC，NPN集电极，低=原始USB VBUS存在 |
| PC0 | VBAT_MON ADC1_IN1 | 电池分压输入；ADC扫描后接内部VREFINT |
| PC8/9/10/11、PC12、PD2 | SDMMC1 D0–3、CK、CMD | AF12；TF直接VCC供电，无SD_PWR_EN |
| PA15 | SD_CD EXTI15 | 双沿、内部上拉；外加10 kΩ上拉，插卡低 |
| PA9/PA10 | USART1 TX/RX AF7 | 调试串口 |
| PA11/PA12 | USB DM/DP | USB_DRD_FS |
| PA13/PA14/PB3 | SWDIO/SWCLK/SWO | 调试；CN2外5 V不是3.3 V并联供电 |
| PA0/PB1 | MEAS_BTN/PWR_BTN | 内部上拉，下降沿 |
| PB13/PB14/PB15 | 绿/黄/橙LED | 低亮，初始高 |
| PC6/PC7 | 红/状态LED | 低亮，初始高 |
| PB6/PB7 | 预留I²C | 本版无TMP117，主程序不初始化I²C |
| PB4/PB8 | 预留 | 不新增功能 |
| PC14/PC15、PH0/PH1 | 晶振扩展焊盘 | 不因预留而启用；当前系统MSI→PLL，USB/SD用HSI48 |

U10模式顺序见附录F，禁止使用旧“SEL1/2/3同沿、SEL4=PB0”描述。
ADC物理AIN1P/N对应样品电压，AIN2P/N对应Rsense；第二通道负端走Kelvin地RC，无跟随器。
MCU VDD11去耦和SMPS电感沿现工程；运行前检查实际安装，固件升频前切SMPS。
USB检测输入仅配置GPIO，USB连接管理仍待实现；BQ模式脚与电流限制尚未验收。
