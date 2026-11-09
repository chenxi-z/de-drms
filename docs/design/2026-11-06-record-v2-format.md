# DE-DRMS 记录文件格式 v2 规格（2026-11-08，T2b）

状态：规格冻结稿。C4 门禁交付——编码器实现必须与本文件逐字段一致；
实现前经本节自审（字段偏移/长度/端序、CRC 参数与覆盖范围、最大长度、错误处理、黄金文件全部固定）。
v1（`shared/protocol/de-drms-v1.json`）只读兼容；v2 写入不改动 v1 任何解释。

## 总则

- 全部多字节整数为**小端**；浮点为 IEEE754 binary64。
- 所有 CRC 为 **CRC-32/ISO-HDLC（zlib）**：多项式 0x04C11DB7（反射 0xEDB88320）、初值 0xFFFFFFFF、
  反射输入/输出、最终异或 0xFFFFFFFF（即 `zlib.crc32`）。未注明时 CRC 覆盖**所在块的全部前导字节**。
- 文件由**定长块头（4 B）+ 载荷**的 chunk 序列组成；解析按 chunk 流进行，不依赖文件级偏移。
- 线格式与内存结构无关：禁止把 C struct 直接落盘。

## 文件识别与 Chunk 帧

- **文件识别**：v1 以 `DRMS` 魔数开始；v2 文件是纯 chunk 流，首字节即首块
  块头（type=1 HEADER，小端 `01 00`）。主机工具按此分派解码器。
- v2 无文件级魔数与文件级 CRC：完整性由每块 CRC 与 END 存在性保证。

```
偏移  长度  字段
0     2     type    uint16：1=HEADER，2=DATA，3=END；其他=解析错误
2     2     length  uint16：载荷字节数（不含本 4 B 块头）；>0
4     len   payload
```

- 每块载荷末 4 B 为该块 CRC-32，覆盖载荷前 `length-4` 字节。
- 块总长 = 4+length ≤ 65539；解析器必须检查剩余字节是否足够，不足即**不完整文件**。

## HEADER（type=1，必为首个 chunk）

```
载荷偏移  长度  字段
0         2     uint16 format_version = 2
2         2     uint16 record_size = 16（冻结；不扩大 16B 帧）
4         4     uint32 flags        bit0 = NOMINAL 时间质量（文件时间为名义时间轴）
8         4     uint32 rate_hz      采样率（Hz，>0）
12        4     uint32 uid_w0       96-bit 出厂 UID（HAL_GetUIDw0/1/2 顺序）
16        4     uint32 uid_w1
20        4     uint32 uid_w2
24        8     uint64 record_id    会话标识（与 DRMS_End.record_id 一致）
32        4     uint32 anchor_generation   时间锚点：采集代次
36        4     uint32 anchor_rate_hz      锚点采样率（= rate_hz，冗余校验用）
40        8     uint64 anchor_sample_seq0  该代第一个观察到的 DRDY 序号
48        8     uint64 anchor_mono_us0     该 DRDY 时刻单调时钟（µs）
56        2     uint16 config_len          配置快照字节数（schema1 编码，0 = 未配置）
58        ...   config 快照原样字节（schema1，见 drms_user_config.h）
最后 4 B        uint32 crc32（覆盖本块载荷除 CRC 外全部字节）
```

- `config_len` 上限 4096；无配置快照时为 0（空记录/纯数据文件合法）。
- 锚点为该记录会话所属采集代次的名义时间轴；`flags bit0=1` 表示时间为 NOMINAL——
  正常 ADC/MCU 频差不构成错误，仅作诊断；缺锚点（generation=0）时主机不得把
  样本序号映射为时间（拒绝伪正常时间解码）。

## DATA（type=2，0..n 个，HEADER 之后 END 之前）

```
载荷 = N × 16B 原始帧记录 + 4B CRC，N ≥ 1；length = 16N + 4（去掉 CRC 后非 16 倍数 = 解析错误）
帧记录 = 12B 原始 ADC 字节 + uint32 sequence（帧内低 32 位序号，与 v1 相同）
```

- 64 位样本位置由 HEADER 锚点 + 顺序扩展重建（低 32 位回绕安全，可证明跨度 <2^31）。
- 坏帧（CRC/格式错误）原样保留在 DATA 中——原始记录不因质量剔除。

## END（type=3，恰好 1 个，必为最后一块；文件必须以 END 结束）

```
载荷偏移  长度  字段
0         4     uint32 acquisition_generation（结束时代次；与 HEADER 锚点代次不同 → 代次跨变）
4         8     uint64 record_id
12        8     uint64 ring_end            记录环 log_ticket 边界（非 raw 位置）
20        8     uint64 lost_count          兼容诊断计数（不得跨阶段相加）
28        8     uint64 first_index         首样本位置 B.sample_next（未知时 0）
36        8     uint64 end_exclusive_index 排他末样本位置；end_known=0 时必须为 0
44        8     uint64 last_confirmed_index 最后确认样本位置（无则 0）
52        1     uint8  end_known           1 = E 边界已一致捕获
53        8     uint64 capture_lost        本次 [B,E) 未发布采样
61        8     uint64 log_dropped         记录环丢弃（本会话独立累计）
69        8     uint64 quality_bad         CRC 坏帧数（已发布，独立计数）
77        1     uint8  unknown_loss        1 = LOSS_UNKNOWN
78        1     uint8  storage_error       1 = 写卡/收尾失败
79        4     uint32 reason              DRMS_Result 值（0=OK,9=INCOMPLETE,12=EMPTY…）
最后 4 B        uint32 crc32
```

- `end_known=0` 时 `end_exclusive_index` 必须为 0——**未知末边界不写伪精确值**。
- `unknown_loss=1` 或 `end_known=0` 或 `reason∈{INCOMPLETE,TIMEOUT,CANCELLED}` → 文件**不完整**。

## 错误处理（解码器必须全部实现）

| 情形 | 结论 |
| --- | --- |
| 首块缺失/非 HEADER / version≠2 | 非法文件 |
| 任意块剩余字节不足（截断） | 不完整文件（不得报告成功） |
| 块 CRC 不符 | 非法文件（该块起不可信） |
| 未知 chunk type | 非法文件 |
| DATA 扣除 CRC 后长度非 16 倍数 | 非法文件 |
| END 缺失（EOF） | 不完整文件 |
| 重复 END | 非法文件 |
| END 之后仍有字节 | 非法文件 |
| HEADER 与 END 的 record_id / generation 不一致 | 非法文件 |
| end_known=0 且 end_exclusive≠0 | 非法文件 |
| 空记录（无 DATA 且 first==end_exclusive 且无损失且 reason=EMPTY） | 合法空记录 |

## 黄金文件

`test/test_log_v2_codec.py` 构造并固化的最小黄金文件（手工可核算）：
单 DATA 块 3 帧（样本 100/101/102，其中一帧 CRC 坏）+ END（capture_lost=1、quality_bad=1、
INCOMPLETE、end_known=1、[100,103)），逐字节断言。

## 与 v1 的关系

- v1 解码路径不变；`tools/de_drms_log.py` 按首块 magic/version 自动分派 v1/v2。
- v2 写入侧（drms_logging 的写路径切换与 END 提供者）在 T7 系统集成接线；
  本任务交付规格 + 双端编解码 + 全部截断/翻转测试。
