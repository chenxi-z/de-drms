# DE-DRMS 直流首板固件（2026-11-04）

目标器件：STM32U575RGT6，TrustZone 关闭。以当前 IOC、主文档附录 F 和引脚表为准。
本版已接上测量应用，不再是空线程模板；本机测试通过不代表实板已验收。

## 已实现

- ADS131A02 上电、READY/命令/寄存器回读、内部 2.442 V 基准、24-bit 固定四字帧、双向 CRC16。
  `VNCPEN=0`，匹配 VNCP 接 AGND；`M0/M1/M2` 继续使用板上既定绑接。
- DRDY 触发 SPI1 全双工 DMA。默认 4 kSPS，提供 1/4/8/16/32/64/128 kSPS 档；
  高档是否无损必须实测，不能由配置成功推断。
  **2026-11-12 实板结论：64 kSPS 是无损上限。**
  实测（每次数秒、`spi_overrun`/`frame_drop`/`crc_bad` 全为 0）：16 kSPS 15,988 Hz、
  32 kSPS 31,899 Hz、64 kSPS 63,955 Hz，4 kSPS 读数正常（≈100 kΩ）。
  128 kSPS **不达标**，见下条。
- **128 kSPS 为何不可达（ADC 自己给出的证据）**：把 128 kSPS 的一批帧从卡上读出后，
  状态字节 `STAT_1 = 0x12`，即 `F_DRDY | F_ADCIN`。`F_ADCIN` 按设计忽略（AIN2N 接 AVSS），
  触发 `DRMS_SAMPLE_ADC_FAULT` 的是 **`F_DRDY`**。SBAS590E 对该位的定义是
  “data are not completely shifted out when new data are ready … the DOUT output shift
  register is not updated with the new conversion result”，即**上一帧没读完，ADC 已丢弃新结果**。
  也就是说 128 kSPS 的失败源于读取速度不足，而不是通信出错——同一批帧 `crc_bad = 0`，
  字节完整，ADC 只是没等我们读完。据此 `r_valid = 0` 是正确判定，不得放宽。
  时间预算：128 kSPS 每帧 7.81 µs，SPI 传 12 字节 @24 MHz 占 4.00 µs，只剩 3.81 µs 给
  DRDY 中断进入、DMA 重装与完成处理，闭环实测平均略超预算，约 10% 的帧被 ADC 判定丢弃。
  要突破需更高的 SCLK：24 MHz 已是 MSIK/2 上限（48 MHz MSIK / 2），而 ADS131A02 允许的最快
  SCLK 是 31.25 MHz（tc(SC) ≥ 32 ns），SYSCLK 分频只能给出 20 MHz 或超规格的 40 MHz。
  提高主频没有空间（U575 上限 160 MHz）。**因此 128 kSPS 受硬件时序限制，当前不可用。**
- 采集期末帧传输改为直接操作 SPI1 与两路 GPDMA，不再走每帧一次的
  `HAL_SPI_TransmitReceive_DMA`（该路径每帧重算传输量、重挂四个 DMA 回调、调用两次
  `HAL_DMA_Start_IT`，在高速档放不进帧预算）。实测传输结束后 SPI 保持使能且 TSIZE 不变，
  故每帧只需换接收缓冲、重装两路通道、清 DMA/SPI 错误标志、置 SPE 与 CSTART；
  完成由 `GPDMA1_Channel1_IRQHandler` 接管，帧的 CRC、序号与安全停采语义与原先一致。
  四个配套修正：完成时两路通道都要关（只关发送侧会让下一帧的占用检查必然失败）；
  DRDY(EXTI3) 优先级须低于 GPDMA（否则新转换会抢占上一帧的重装，实测重装被拉长到 16 µs）；
  CS 用 BSRR 直写并去掉每帧两次的 volatile NOP 延时；高速档时间戳每 8 帧取一次
  （时间轴本就由样本序号重建）。
- **超过 64 kSPS 的速率在入口被拒绝**：`drms_acq_start` 对 `rate > 64000` 直接返回失败
  （`cmd_result = 2`），并把 `rate` 归到 64000，不触碰 ADC。原因不只是 128 kSPS 读不快：
  被推到那一档后 ADC 会停发 DRDY，之后即便重新编程成功也不再出帧，实测只有 MCU 复位能
  恢复（断电 50 ms 不够）。拒绝比"进去再救"更可靠，设备不会因此卡死。
- 队列溢出（`adc_error=6`）仍走原先的降级：停采并关激励，此时 `START` 回 `OK queued` 但
  不会真正起采，需复位后恢复。该行为是既有的安全设计（资源状态无法证明静止时即隔离），
  本次未改变。
- 按 `SEL_SENSE/SEL_K2` 的 `00` 样品、`11` 参考切换；先抑制激励，通过 `10` 中间态，
  不经过禁止的 `01`。切换复位 ADC，等待模拟和数字滤波建立后才接收数据。
- 4096 个有效参考样本计算 `k=Rref*sum(CH2)/sum(CH1)`，测量 `R=k*CH1/CH2`。
  未校准时 `k=150000 Ω` 并明确报告 `cal=0`。参考电阻默认名义 100 kΩ，当前 BOM 公差约 ±0.02%；
  可输入实测值。没有温度补偿，也没有将隔离支路擅自视作已验证零点。
- 校准显式保存至 Flash 两页交替记录，包含版本、CRC32、代次和最后提交的独立 quadword。
  保留旧页，损坏/中断记录退回旧值或未校准值。仅在停采、结束记录后允许 SAVE。
- FileX / SDMMC 4-bit 挂载、无卡/坏卡退让重试、热拔出降级、32 KiB 批量写入、每秒 flush、
  正常结束文件尾和关闭。约 1 GiB 自动换新文件，不覆盖已有文件；换文件期间继续收样。
  CLK48下软件将SD总线启动分频限为1（24 MHz），不在未明确协商High Speed时直接用CLKDIV=0的48 MHz。
- USBX 栈、OTG FIFO、PCD 启停，依据 PC13 附着/脱离；独立 CDC 线程处理控制命令。
- **CDC v2 实时推送（SUBSCRIBE opcode 64）**：周期快照（电阻、等级、质量位）由
  **CDC 发送线程** 按订阅周期推出，编码用独立缓冲、订阅用 epoch 做跨线程失效判定。
  `lost` 累计"该发而未发"的周期数，主机据此区分"设备安静"与"链路卡住"。
  RAW 流（period_ms=0）显式回 INVALID，不做静默降级。
- **HAL 毫秒时基必须高于采集中断（2026-11-12 实机定位）**：TIM7 原用默认优先级 15
  （最低），而 4 kSPS 采集的 DRDY(EXTI3)=7 与 GPDMA=6 每秒各来 4000 次，TIM7 被持续
  抢先，更新中断在 pending 里合并，`uwTick` 每秒只前进约 91 次而非 1000 次——
  `HAL_GetTick()` 慢了整整一个数量级。症状：100 ms 的订阅只发出 2 条/秒，
  设备单调时间只走真实时间的 1/10，所有超时与记录时长同步失真。
  把 TIM7 提到优先级 0 后 tick 精确回到 1 kHz（实测事件间隔与 `mono_us`
  逐拍对齐）。TIM7 的 ISR 只有一次 `HAL_IncTick()`，不挤占采集预算。
  排查中被否掉的两个假设：不是 PLL/分频错（`RCC->CFGR2` 全 0，AHB/APB 不分频，
  CPU 实测 159.1 MHz），也不是 TIM7 时钟源错（`PSC=159/ARR=999` 本就是 160 MHz 下的 1 kHz）。
  USART1 使用中断接收和 TX DMA，接收溢出丢弃破损命令，发送缓冲在 DMA 完成前不复用。
- 内部 ADC 电池电压与 VREFINT 校正、RTC 设置和有效标志、状态灯与按键。
  USB 未配置/挂起/复位撤销 500 mA 档；配置完成才允许该档。

## 构建与回归

在仓库根目录运行：

```bash
python3 tools/firmware_postgenerate.py
python3 -m unittest discover -s test -p 'test_*.py'
make -C firmware/DE-DRMS-Code -j6 BUILD_DIR=/tmp/de-drms-build
```

构建产物在 `/tmp/de-drms-build`，不入库。固件源码修改没有改 IOC 或 EDA。

以后在 CubeMX Generate Code 后运行：

```bash
python3 tools/firmware_postgenerate.py --apply
python3 -m unittest discover -s test -p 'test_*.py'
make -C firmware/DE-DRMS-Code -j6 BUILD_DIR=/tmp/de-drms-build
```

脚本默认只检查；`--apply` 仅恢复已知非 USER 区的 SD 容错、DCD 返回值/取消保护、链接分区和
Makefile 源文件列表。遇到未知模板、丢失 USER 内容或错误 MCU 会停止，不修改 IOC。
CubeMX 的 **Keep User Code** 必须保持启用；SD 初始化调用仍由 FileX 发起，不回到 main。

链接脚本将配置事务与记录编码的 12 KiB CPU 临时工作区放在 SRAM4；这些缓冲每次使用前写入，
不依赖复位清零。采样环、记录环和 SD 写入缓冲仍在主 SRAM。更改后应重新构建并检查链接映射；
SRAM4 在实际板上的访问和长时间记录表现仍需验证。

Flash 共 1024 KiB：程序区 992 KiB（`0x08000000–0x080F7FFF`），用户配置区 16 KiB
（`0x080F8000–0x080FBFFF`），校准区 16 KiB（`0x080FC000–0x080FFFFF`）。
持久化后端只接受本器件的默认双 Bank、未交换映射；其他布局返回错误，不修改 Option Bytes。
整片擦除仍会删除校准；普通复位不会。设置区 ECC 故障只在受限读取窗口内降级，其他 NMI 保持原处理。

工程内两处 ST 中间件补丁由后生成脚本保护：FileX SD 驱动的异常清理/等待退让；USBX DCD 的
“请求取消与端点启动”竞态。CDC 独立线程使用无限 I/O 等待，由 reset/unplug/参数变更正确中止，
避免该 DCD 软件超时后残留端点和完成信号；它的等待不阻塞采集、FileX 或 USB 附着线程。

## 第一次上板使用

串口为 115200、8N1；USB CDC 终端要拉起 DTR。命令大写，行尾 LF 或 CRLF。
一次发一条并检查结果，特别是串口 TX DMA 忙时不会覆盖旧回复。

```text
PING
STATUS
TIME 2026-11-04T05:00:00
START 4000
STATUS
RECORD
STATUS
STOP
STATUS
```

TIME 的时间按 UTC 输入。`OK queued` 是接收命令，不是执行完成；查看 `last_cmd/cmd_result`。
停采后等 `running=0 log_state=0 log_status=0` 再断电。无卡仍可测量和诊断；本版不自动格式化卡，
使用 FAT32，当前未启用 exFAT。记录文件为 `DRMS0000.BIN` 起自动递增。

参考校准流程：

```text
REF
CAL 100000000
STATUS
STOP
SAVE
STATUS
START 4000
```

`CAL` 参数单位 **mΩ**，上例是 100000 Ω。先确认 REF 成功，再等
`cal_count=4096 cal_result=0 cal=1`；SAVE 后 `cmd_result=0 cal_dirty=0` 才表示保存成功。
读完整状态后再发下一条，不要把以上整段不加等待地粘贴执行。

`MEAS_BTN` 启动默认 4 kSPS 测量并尝试记录，再按一次停采关闭记录；无卡则只测量并报告记录不可用。
`PWR_BTN` 短按先安全停采，长按约 2 s 请求软关机；等待文件/介质关闭和按键释放后进入 Standby。
电源键、测量键或插入 USB 可唤醒（复位重启）；启动时仍按住电源键不会立即再次关机。
USB 在线取消软关机；电池供电时 ≤3.65 V 提示，连续 5 次有效秒级读数 ≤3.50 V 才停采软关机。
外部电源有效或 ADC 电池读数无效时不按低电关机。TF 仍常供电，不是整板物理断电。
新校准须先 SAVE；未保存的 RAM 校准不会跨 Standby 保留。
绿=样品测量有效，黄=参考模式，橙=未记录/文件切换/记录丢样/低电提示，红=采集/记录故障；
电源灯心跳。**这些是运行状态，不是损伤等级**，损伤阈值仍需试件标定曲线。

## 取出数据

```bash
python3 tools/de_drms_log.py /path/to/DRMS0000.BIN --csv /path/to/result.csv
```

工具按机器协议解析文件头、原始 ADC 帧、CRC、序号、文件尾与丢帧统计。没有有效文件尾时标为
非正常结束；可加 `--allow-incomplete` 允许导出不完整/有损诊断前缀，不会把它改称完整记录。
工具默认对已报告的 CRC/丢帧或非正常结束返回非零；`clean_end` 只指正常关闭，
`no_reported_loss` 也只是软件未报告丢失，仍须物理时序对照。
协议见 [人读说明](../../docs/protocol/de-drms-v1.md) 和 [机器定义](../../shared/protocol/de-drms-v1.json)。

## 已知未解决：高速档记录写卡吞吐不足（2026-11-12 实测）

**症状**：`START <高速档>` + `RECORD` 后，记录只写一小段就自行终止。
`records` 停在一个固定值（36k–38k 量级），`log_state` 归 0，
`log_drop` 变成 1，会话 END 被标 `DRMS_INCOMPLETE`；而
`sd=1 sd_status=0 log_status=0` 全部报正常，看起来"没出错"。

**机制已经查清（不是猜测）**：
- 记录会话的 `drms_record_session_note_recorded()` 有一条硬规则——
  `enqueue_ok == 0`（记录环 32768 帧写满）就立即 `fail_session(DRMS_INCOMPLETE)`。
  这是有意的保守设计：环满意味着后面的数据必然缺失，宁可如实标残缺，
  也不能给一份看着完整的坏数据。
- 所以"写一小段就停"= 写卡吞吐跟不上采样率，环在几十毫秒到几百毫秒内填满。
- 实测吞吐（`records` 增量 ÷ 时长，多次测量）：
  | 采样率 | 需求 | 实测吞吐 | 结果 |
  | --- | --- | --- | --- |
  | 4 kSPS | 62 KB/s | ~81–83 KB/s | 勉强跟上 |
  | 16 kSPS | 250 KB/s | ~95–97 KB/s | 环满，终止 |
  | 64 kSPS | 1000 KB/s | ~15–160 KB/s | 环满，终止 |
  吞吐基本**与采样率无关**，是固定量级 → 瓶颈是固定节拍，不是数据量。

**已经排除的方向（都实机验证过，不要重走）**：
- **不是** FileX 媒体缓存太小：把 `fx_sd_media_memory` 从 512 B 加到 16 KiB，
  吞吐没有数量级改善（改动保留，但它不是解药）。
- **不是** 时基问题：本文件上面那条 TIM7 优先级修复已让 `HAL_GetTick()`
  与真实时间对齐，与本缺陷无关。
- **不是** 本次修复引入：用修复前的提交 `2785298` 单独构建烧录跑同样流程，
  表现完全一致（记录同样写一小段就停）。
- **不是** 采集侧丢帧：同期 `spi_overrun` / `frame_drop` / `crc_bad` 全为 0，
  原始环 `raw_used` 长期只有个位到几百（4096 容量），采集与消费都正常。
- **不是** 卡坏了：同一张卡曾成功写入 151,684 / 167,924 / 70,961 条，
  `tools/de_drms_log.py` 解出 `crc_errors=0`、`sequence_gaps=0`。

**已经定位到但还需要继续缩小的范围**：
`fx_file_write()` 单次实测约 **165 ms 写 26.6 KB**（≈161 KB/s），
用 DWT 周期计量的。26.6 KB 对应 52 个扇区，即约 **3.2 ms/扇区**。
SDMMC 配成 24 MHz 4-bit（`sd_startup_init` 里 `ClockDiv = 1`），
理论 12 MB/s，实测量级差两个数量级。下一步应在
`fx_stm32_sd_write_blocks()` 内部（`HAL_SD_WriteBlocks_DMA` 本体
与等信号量之间）做分解计时，判断是 DMA 真慢、还是等完成被调度延迟。

**影响面**：4 kSPS 及以下可连续记录；16 kSPS 以上记录不可用（测量本身正常）。
在查清前，不要承诺"高速档 + 记录"的组合。

## 上板验收边界

- 采样建立、模拟稳定性、输入共模、电阻精度与参考校准恢复必须实测；不沿用旧文的性能承诺。
  `excitation_ok` 仅按 VSET ±10% 与合规余量做初步筛查，不是电流精度规格。
- ADS131A02 的 `F_ADCIN` 单独出现时只保留诊断，因为 AIN2N 按图接 AVSS，低于故障比较器阈值；
  协议、CRC、重同步、丢帧和数字饱和仍会使读数无效。硬件输入故障仍需逐脚/示波器验证。
- 当前采集队列 4096 帧、记录队列 32768 帧。128 kSPS 时分别约 32 ms 和 256 ms 缓冲。
  原始记录每点 **16 字节**，写卡需求约 **2.048 MB/s**；CRC、ISR 与文件系统开销也必须纳入测试。
  采集队列满时会主动抑制激励并停采（`adc_error=6`），避免高采样率让 CPU 陷入 IRQ 饱和。
  需要逻辑分析仪对照物理 DRDY/CS 时序，不能只凭软件序号连续判无丢样：中断屏蔽时物理边沿可能合并。
- TF 拔出/掉电可能损坏未提交的数据或 FAT。每秒 flush 和有效文件尾帮助恢复，不构成突然掉电保护保证。
  持续采集、坏卡、满卡、换文件、热拔出、断电恢复必须在实际卡上验收。
- **BQ24074 EN2 接地时，EN1=0 是 USB100，EN1=1 是 USB500，低电平不等于关闭充电**。
  该硬件无法仅靠这根 GPIO 进入 EN1=EN2=1 的 USB Standby；USB 挂起取电合规仍需硬件解决并实测。
  来源：[TI BQ24074 手册 EN1/EN2 表](https://www.ti.com/lit/ds/symlink/bq24074.pdf)。
- HSE/LSE 启动裕量、USB 实际枚举/挂起恢复、电池分压误差、Flash 实物断电/ECC 恢复、
  Standby 进出及三路唤醒均尚未在板上验证。调试器阻止待机时会恢复调度并报告 `power_status=2`。
