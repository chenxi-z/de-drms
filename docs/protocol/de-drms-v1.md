# DE-DRMS v1 控制与记录协议

机器权威定义：[de-drms-v1.json](../../shared/protocol/de-drms-v1.json)。本说明与其同次维护。
设备为 STM32U575RGT6 + ADS131A02 直流首板；没有温度传感和预设损伤分档阈值。

控制口是 USB CDC ACM（DTR=1）或 USART1 115200 8N1。ASCII 大写命令，每行最多 63 字节，
LF 结束，兼容 CRLF；破损、溢出行丢弃至下一分隔符。串口发送忙时不覆盖旧回复，
`uart_tx_drop` 可观察回复丢弃，因此应一问一答，不连续灌命令。

| 命令 | 含义 |
| --- | --- |
| PING / STATUS / HELP | 立即回复，STATUS 是 `OK key=value ...` |
| START [rate] | 样品模式，默认 4000；可选 1000/4000/8000/16000/32000/64000/128000 SPS |
| STOP | 取消排队控制，抑制激励，停 DMA，排空采集队列，结束并 flush 记录 |
| REF / MEASURE | 按当前采样率进入参考/样品模式；记录中拒绝换路 |
| CAL [Rref_mohm] | 参考模式下取 4096 个有效样本，默认 100000000 mΩ=100 kΩ |
| SAVE | 已校准且采集/记录都停止时交替保存至两个 Flash 页 |
| RECORD / END | 新建文件记录/排空关闭记录；END 不停止测量 |
| TIME YYYY-MM-DDTHH:MM:SS | 设置 UTC，合法范围 2000–2099 年 |

控制回复 `OK queued` 仅表示接受；随后查询 STATUS 的 `last_cmd/cmd_result`。STOP 是取消屏障，
会清掉排队的 START 等命令。`cmd_result=0` 成功，1 状态不允许，2 采集故障，3 忙，
4 校准失败/取消，5 记录不可用，6 Flash 保存失败，7 RTC 设置失败，100 校准进行中。
`last_cmd` 编号依次是 START=1、STOP=2、REF=3、MEASURE=4、CAL=5、SAVE=6、RECORD=7、END=8、TIME=9。

关键状态：`running/mode/rate`（mode 0 样品、1 参考）；`r_valid/r_mohm`（mΩ）；
`cal/cal_dirty/cal_generation/cal_active/cal_count/cal_result`；
`adc_error/edges/spi_overrun/frame_drop/crc_bad/adc_fault/excitation_ok`；
`sd/sd_status/log/log_state/log_status/records/log_drop`；
`bat_mv/bat_valid/rtc_valid/utc_date/utc_time`；`vbus/bq_pg/bq_chg/usb_io/usb_status`。
`utc_date/utc_time` 为 YYYYMMDD/HHMMSS 数字，未设 RTC 时 `rtc_valid=0`；前导零可省略。
`config_state=0` 无已保存监测配置、1 可用、2 已保存配置与本固件不兼容。
`log_state=0` 空闲、1 正在开/换文件、2 正在记录、3 排空关闭。
`adc_error=1` READY 失败、2 配置/应答失败、3 SPI DMA 错误、4 数据超时、5 连续帧完整性失败、
6 采集队列满而主动停采。
`sd_status/log_status` 是底层 FileX 状态码，0 为成功；`flash_status=1` 布局不支持/忙，2 写入或校验失败。

`shutdown=1` 请求软关机并等待 FileX；`power_status=0` 正常，1 正在等关闭，2 待机入口返回（可能被调试器阻止）；
`low_battery=1` 是电池供电下 ≤3.65 V 提示。连续 5 次有效秒级读数 ≤3.50 V 才请求停采待机，
USB/外部电源有效或电压无效时不执行低电关机。USB 在线取消关机。
测量键启动测量并尝试记录，再按停止；电源键短按停止、长按约 2 s 后关闭介质并待机。
PWR/MEAS 按键或 USB 插入唤醒会复位重启，RAM 新校准须先 SAVE。

`r_valid=1` 表示该读数通过本版数据链路与激励粗筛，不等于达到某个精度等级。
初次上电 `cal=0` 使用 150 kΩ 名义比例因子；参考校准只修正比例，不替代零点验证和温度补偿。
激励粗筛按 VSET=1.178571 V ±10%、`Vsample+Vsense≤2.47 V`，具体码值在机器定义中。

文件名 `DRMS0000.BIN` 起递增，已有文件不覆盖。每个文件是 **64 字节头 + N×16 字节记录 + 64 字节尾**。
头/尾多字节整数为小端，浮点是 IEEE754 binary64 小端。记录的前 12 字节原样保留 ADC SPI 帧（大端字）：
STAT_1 响应 24-bit、CH1 24-bit、CH2 24-bit、CRC16 及零填充 24-bit；末 4 字节是小端 DRDY 序号。
所有字段偏移见 JSON。CRC16 为 CCITT-FALSE，初值 FFFF、多项式 1021，覆盖 ADC 帧前 9 字节。
头和尾的 CRC32 覆盖各自前 60 字节。

STAT_1 单独的 `F_ADCIN` 保留为诊断：图上 AIN2N 接 AVSS 会触发低阈值比较器；
其他 STAT_1 错误、CRC/格式错误、饱和、激励粗筛失败都不得解释成有效电阻。
原始坏帧仍保留，便于定位问题。R=`scale_ohms×CH1/CH2`，不能对无效码或零分母计算有效读数。

每个采集起点重置序号；同一文件内跳号表示丢失的已观测 DRDY 事件，32-bit 回绕合法。
物理边沿也可能在中断屏蔽期间合并，所以“软件不跳号”不足以证明无丢样。
相对时间由序号差/rate 推算，需先验收 DRDY 时序；头内 RTC 是 RECORD 请求时间，
不是精确第一采样点 UTC。不要据此声称绝对时间同步。

约 1 GiB 自动结束当前文件并继续下一个文件，文件间采集队列不断开。
各分段头保留同一 RECORD 请求的元数据；尾内 records 是**本文件记录数**，
log_dropped 是本次 RECORD 会话累计值，SPI/采集队列丢帧是该次 START 累计值。
记录结构本身约 2.048 MB/s@128 kSPS；该采样档和写卡吞吐量仍须实测。

正常 END 的最后步骤是写有效尾、关闭文件和 flush。安全 STOP 中断正在进行的记录时关闭并 flush 已写数据，文件保持缺尾以标记不完整。尾校验和计数匹配才叫正常结束；
缺尾/截断只能恢复前缀，突然断电仍可能损坏 FAT 或卡内部缓存。
解析示例：`python3 tools/de_drms_log.py input.BIN --csv output.csv`，
stderr 输出完整性、有效样本和丢帧统计；正常关闭与计数匹配才有 `clean_end=true`，
这不等于无丢样。`no_reported_loss=true` 也仅表示软件统计未发现丢失，仍要做物理 DRDY 对照。
工具对已报告的 CRC/丢帧或不完整文件默认返回 1；格式/头尾损坏返回 2。
需要诊断恢复时加 `--allow-incomplete`，不会把无效样本变为有效测量。
