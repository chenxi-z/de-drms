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

## 高速记录吞吐排查与修复（2026-11-12）

旧版在 16/64 kSPS 录制时填满 32768 帧记录环并以 `DRMS_INCOMPLETE` 结束。
环满停止是正确保护；实际瓶颈是存储路径与 CPU/调度的叠加，不能靠扩大环来掩盖。

已修正：

- **FileX 部分扇区后的 DMA 地址错位**：v2 HEADER 长度为 `66 + config_len`，
  FileX 先补齐当前扇区后会推进源指针。原来仅对齐 staging 基址，反而让后续
  整扇区数据落入逐扇区 scratch 写入。现在源指针的模 4 偏移与文件偏移一致，
  文件字节和 v1/v2 格式不变；每次换文件重新建立偏移。
- **CRC 与打包预算**：CRC16 按字节查表，CRC32 用 slicing-by-4；保留逐帧 ADC 校验、
  文件 CRC 和相同校验参数。32 KiB staging 的末尾可容纳短 DATA 块，不再固定浪费约 4 KiB。
- **调度与批量提交**：普通 FileX 服务优先级仍为 10，仅活动记录的 log poll 临时升为 4，
  退出后恢复原优先级（处理线程为 5）；启动建文件不提级。约 2000 帧攒一批，
  50 ms 上限处理小尾批；有整批积压时不额外睡一个 10 ms tick。
  卡短暂 busy 可在最多 1 ms 内轮询，长期 busy 仍睡眠并保留超时。
- **启动边界**：文件创建期间尚未请求 BEGIN 边界，继续消费监测帧；文件就绪并开始请求
  边界后才维持原来的屏障。避免文件名查找或建文件超过原始环约 64 ms 容量时停采。
- **SD 高速协商**：先用 24 MHz 初始化；只有 CMD6 High Speed 协商成功后才切换
  48 MHz / 4-bit。协商或切换失败时完整重初始化并回到 24 MHz，保留慢卡兼容性。
- **构建与内存**：默认 `-O3 -flto`，仍保留调试符号；再生成后由 postgenerate 恢复。
  `OPT=-Og` 可单独用于低速调试，需使用不同构建目录，不能沿用高速性能结论。
  DRDY 时序统计由 `DRMS_ACQ_TIMING_PROBE` 显式开启，默认移除统计开销，错误计数仍保留。
  16 KiB FileX 缓存实验没有解决瓶颈且超出 RAM 门禁，恢复单扇区缓存；互斥格式元数据与
  CPU 帧暂存共用原有 SRAM4 预算，512 KiB 记录环和 32 KiB DMA staging 不变。
- **MSC 读出等待**：保留逐扇区内部邮箱、撤销代次和超时隔离，将 USBX/存储线程之间的固定 tick 等待改为请求/完成事件，避免每 512 B 固定等待约 10 ms。交还时保持 RELEASING/QUARANTINED 至 FileX 重挂载返回，随后才发布 LOCAL，防止主线程提前报告失败或释放租约。
- **可观察的业务失败**：ASCII STATUS 新增 `record_result/record_phase/record_clean_end/record_unknown_loss`。
  `sd_status/log_status=0` 只表示底层 I/O 成功；`record_result=9` 才是业务上的不完整。
  `record_clean_end=1` 表示 END 已写出，仍须检查结果和未知损失；CDC v2 继续用 GET_RECORD。

台架对照：停止采集时，同一张卡写 512 KiB 用时 174 ms（约 3 MB/s）。
24 MHz 下逐步修复后 64 kSPS 能录制约 45 s，仍有溢出，因此这一组合不按持续记录放行。
48 MHz 已在同一卡上协商成功，实读 SDMMC1 `POWER=0x3`、`CLKCR=0x4000`（4-bit、CLKDIV=0）。
最终默认优化固件的台架结果：

| 采样率 | 文件 | 记录数 | 等效记录时长 | 最终结果 |
| --- | --- | ---: | ---: | --- |
| 64 kSPS | DRMS0049.BIN（最终固件复测；前一轮为 DRMS0046.BIN） | 4,393,647 | 约 68.65 s | result=0、clean_end=1、unknown_loss=0 |
| 16 kSPS | DRMS0047.BIN | 426,565 | 约 26.66 s | 同上 |
| 32 kSPS | DRMS0048.BIN | 852,810 | 约 26.65 s | 同上 |

三档 `log_drop/spi_overrun/frame_drop/crc_bad/adc_fault` 均为 0。
64 kSPS 中间状态的落盘增长约 63,954 帧/s（约 1.023 MB/s 原始记录负载，不含块头/CRC）。
当前证据限于这张卡、USB 供电、未接电池和被测物的记录链路，不替代模拟精度验收；
回退 24 MHz 的卡不沿用 64 kSPS 持续记录结论。

三份最终选取文件（0047/0048/0049）已完整复制并由现有 `tools/de_drms_log.py` 的
`LogReaderV2` 全量解析：文件/帧 CRC、帧格式、ADC 故障位、序号缺口/乱序、
HEADER/END 身份与首末边界均通过；记录数与上表一致。
64 kSPS 的 `no_reported_loss=true`，END 的 `capture_lost/log_dropped/quality_bad` 全为 0，
`unknown_loss/storage_error=false`。16/32 kSPS 文件的 `quality_bad` 分别为
426,565/852,810，故 `no_reported_loss=false`；当前台架未接被测物，低速测量质量
未通过，不可把结构完整、传输无损当作有效电阻测量。
MSC 只读拷贝实测约 447–477 KiB/s（改动前约 20 KiB/s）；完成后已释放导出并重新挂载本地介质，采集停止。

本轮默认 ARM 构建、postgenerate 只读检查和 454 项软件测试通过；使用本次新生成
map/ELF 检查主 RAM ≤736 KiB、SRAM4 ≤16 KiB 及 DMA 区域，未放宽门禁。
本次不改变 128 kSPS 既有不可用结论，不宣称已完成 1 GiB 实物轮转或掉电测试。

## 2026-11-13 台架压力测试补充（模拟前端开路、无电池）

台架条件：被测端开路（`excitation_ok=0`、样品通道顶在 24 bit 正满量程 8388607）、
未接电池、USB 供电、单张 14.6 GiB TF 卡。以下结论只在该条件下成立。

**通过的项目**

- **互斥**：记录中请求 `MSC_EXPORT` 返回 `BUSY` 且记录不中断；导出中请求
  `BEGIN_RECORD` 返回 `BUSY`；两者均不被静默放行。注意首次回复是 `ACCEPTED`
  （受理），必须用返回的操作号查 `GET_OPERATION` 才能拿到最终 `BUSY`——
  把 `ACCEPTED` 当结论会误判。
- **CURVE 订阅**：`period_ms` = 100/200/500/1000 实测速率与设定偏差 ≤2%，
  序号单调、无缺口、`lost=0`；断线重连后订阅不继承，需重新订阅。
- **多档连续记录（干净复位后）**：16 kSPS 498,725 帧 / 32 kSPS 992,362 帧，
  `spi_overrun/frame_drop/crc_bad/log_drop/adc_error` 全 0，`result=0 clean_end=1`。
- **文件读回**：`FILE_OPEN`→`FILE_READ` 取 HEADER，`version=2`、`record_size=16`、
  `rate` 与设定一致，UID 三字与 `HAL_GetUIDw0/1/2` 完全一致，HEADER chunk 的
  CRC32 与自算值相符（0xEB4A35F1）。
- **64 kSPS 长时记录**：4,393,647 帧量级的短时记录仍为零丢失（与 2026-11-12 一致）。

**未通过 / 新发现的问题**

1. **64 kSPS 长时记录在约 10 分钟后出现丢样**。实测跑到 19,062,497 帧
   （约 298 s 后触发）时 `log_drop=1`，记录结果如实报 `INCOMPLETE`、
   `unknown_loss=true`、`clean_end=true`——设备没有伪报成功，这是正确行为。
   根因是记录环（32768×16 B）在存储线程排空不及时被填满，
   `drms_log_enqueue` 按设计丢帧并计数（`adc_error=0`、`spi_overrun=0`，
   说明瓶颈在"记录环→存储"段而非采集）。**结论：64 kSPS 的持续记录能力
   目前只能保证到约 5 分钟量级，不能按"无限时长无损"宣称。**
2. **MSC 导出的容量基准错误**。设备用 `fx_media_total_sectors`（FAT 卷内
   扇区数，不含 `hidden_sectors`）作为 SCSI 逻辑块总数对外报告，而该值被
   主机当作**从 LBA 0 起的绝对块数**。结果：主机看到 30,717,952 扇区，
   却把 VBR 当 MBR 解析出 31,148,032 扇区的分区表，内核报
   `p1 size ... extends beyond EOD, truncated` 并多出 210 MiB，
   `mount`/`dd` 读越界区域时长时间无响应，vfat 挂载卡死。
   **主机侧无法完成挂载与复制**；这解释了 2026-11-12 记录里"MSC 只读拷贝
   447–477 KiB/s"与本次挂载失败的差别（当时是主机已成功挂载的情形）。
   修复方向：对外报告的块总数应为**卡的实际物理扇区数**（或按分区表
   `hidden_sectors + 卷长`），而不是卷内扇区数。
3. **`lost` 计数不覆盖发送侧丢弃**。`drms_cdc_v2_publish` 先用
   `can_send` 判断，再调 `send`；而 `send_v2` 里 `tx_enqueue` 的返回值被丢弃。
   实测：订阅 `period_ms=1` 后 30 s 完全不读，恢复时收到的序号已跳段，
   但 `lost` 仍为 0。协议规定"`lost` 为本次订阅累计未交付条目数"，
   当前实现不满足——主机无法据此判断丢了多少。
4. **`SAFE_STOP` 会撤销 MSC 导出**（`drms_application.c` 的
   `drms_msc_cancel()`），实测导出中 `SAFE_STOP` 后 `owner` 由 `EXPORTED`
   变 `LOCAL`。而 [MSC 设计](../../docs/design/2026-11-05-msc-design.md)第 131 行
   写的是"STOP 可继续停止采集，但不会默默将 TF 从电脑收回"。
   **文档与实现冲突，需确认以哪一方为准后再改其一。**
5. **脏状态会污染后续采样档位**。在一次异常（记录环满 + 高速档重配失败）
   之后直接切到 16/32 kSPS，会立刻出现 `spi_overrun=3216/6433`、`adc_error=4`
   （200 ms 无完成帧），`RECORD` 无法进行；**只有 MCU 复位能恢复**。
   复位后同样两档立即恢复全零。这与既有文档"高速档异常后需复位"一致，
   但说明**一次记录失败后不能靠 STOP/START 重试**，验收脚本必须先复位。

实板仍未验收：1 GiB 实物轮转（本次失败于约 5 分钟处）、掉电恢复、
模拟测量精度、其他卡与 24 MHz 回退路径、Windows 下 MSC 挂载。

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
