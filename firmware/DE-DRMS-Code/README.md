# DE-DRMS 直流首板固件（2026-11-04）

目标器件：STM32U575RGT6，TrustZone 关闭。以当前 IOC、主文档附录 F 和引脚表为准。
本版已接上测量应用，不再是空线程模板；本机测试通过不代表实板已验收。

## 已实现

- ADS131A02 上电、READY/命令/寄存器回读、内部 2.442 V 基准、24-bit 固定四字帧、双向 CRC16。
  `VNCPEN=0`，匹配 VNCP 接 AGND；`M0/M1/M2` 继续使用板上既定绑接。
- DRDY 触发 SPI1 全双工 DMA；ISR 只搬帧，主线程校验、计算和统计。默认 4 kSPS，提供
  1/4/8/16/32/64/128 kSPS 档；高档是否无损必须实测，不能由配置成功推断。
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

Flash 共 1024 KiB：程序区 1008 KiB，最后 16 KiB 是校准区 `0x080FC000–0x080FFFFF`。
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
