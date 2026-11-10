# 正式 CDC v2 固件接口（设计候选版）

[机器定义](../../shared/protocol/de-drms-cdc-v2.json)列出字段号、类型、请求/成功回复字段、枚举和四条线上向量。本文规定编码与生命周期。版本 2 区别于现有 ASCII v1；当前固件的 CDC 入口支持 v2 HELLO、GET_STATUS、GET_OPERATION、SAFE_STOP、RESUME_MONITOR、SAVE_CONFIG、BUILD_R0、MSC_EXPORT 和 MSC_RELEASE；其他 v2 命令尚未实现并返回 UNSUPPORTED，ASCII v1 调试入口暂时保留。以下其余内容是目标规格，不能视作已实现能力；真实 USB 和硬件随机源仍须板测。

当前 CDC 收发由独立线程处理，发送端使用 4 个普通槽和 1 个安全停止专用槽；对应槽已满时，请求在业务受理前被丢弃，不产生动作，主机可超时重试。旧会话排队回复不会在新连接发送。故障优先队列和遥测流尚未实现，不能将本段视为下文完整 TX 调度能力已交付。

## 编码

- 全部多字节数为小端，无填充。固定头按顺序为 major:u8=2、kind:u8、opcode:u16、session:u32、request_id:u64、payload_length:u16、flags:u16=0。头长 20 字节。尾部 u32 CRC-32/ISO-HDLC 覆盖头和有效载荷，反射多项式 0xEDB88320，初值和最终异或均为 0xFFFFFFFF，“123456789”校验值 0xCBF43926。
- 整体标准 COBS 编码再追加 0x00。载荷至多 1024 字节，解码总长至多 1048 字节，含定界符的线上缓冲上限 1054 字节。任意拆包/粘包；连续零忽略。堆积超界或半帧从首字节起满 1000 ms 仍无分隔符，丢至下一个零。畸形、校验错误、未知主版本或 kind 的帧计数丢弃；可解析的请求若命令未实现，返回 UNSUPPORTED。
- 载荷依次排列 TLV，头为 tag:u16、value_length:u16，长度仅指 value。低 15 位为字段号，高位表示接收者必须理解；机器表中带问号表示可省略，其余字段必须出现。发送方对必填字段置高位。可选字段可清高位；未知且高位置位返回 INVALID/UNKNOWN_REQUIRED，未知可选字段按长度跳过。重复已知字段、缺少必填、长度错误、已知字段出现在错误消息、非零 flags 均拒绝。最多 64 个顶层字段。
- bool 只接受单字节 0 或 1，f64 是有限 IEEE754 binary64，utf8 为合法 UTF-8，无 NUL，最多 32 字节；定宽数列表为无填充元素串。可选数值无效时省略，不能用零替代。所有回复含 result；非成功或非受理回复可附 reason，错误回复无需成功字段。事件载荷按机器表 success 栏，事件 request_id=0，回复使用原请求编号和 opcode。
- config 为一层嵌套 TLV，完整配置包含机器表 tag 72 至 83 全部字段，禁止再嵌套。interval_list 为连续 30 字节条目：lo、hi、h 三个 f64，id:u16、level:u8、last_upper_closed:bool、direction:u8（0 无/1 下降/2 上升）、reserved:u8=0，最多 16 项。level 取 0..3，区间编号唯一。可选 config tag 84 为区间名称表，重复条目 id:u16、UTF-8 字节数:u8、名称字节；每项至多 16 字节，引用现有 id，每 id 至多一次。配置整体须装入单帧；不截断。算法边界校验按 C6。时间均按字段名单位；CV 为标准差与正均值之比，合法范围由校验配置决定。未标定允许用空区间表；baseline_min_count=0 表示基线参数未配置，此时后两项为零，建立 R₀ 返回 INVALID/WRONG_STATE。
- quality 位 0..5 分别表示无有效样本、帧完整性失败、激励无效、采样缺口、基线不适用、区间表缺失；fault 位 0..5 分别为采集、存储、持久化、时间基准、USB、隔离故障。各字段均是独立位集合，新位只增不复用。端点报告未知位时，读者保留原值。fresh 单列，不能用历史等级代替当前有效等级。

## 连接、请求和查询

USB 配置完成且 DTR 有效后接受 HELLO（session=0）。同一次连接重复 HELLO 返回同一会话，握手无业务副作用。回复头携带非零 session。uid 为 w0、w1、w2 顺序的三个小端 u32，人读时逐字按八位大写十六进制显示。boot 是每次启动生成的非零 64 位随机标识；启用会话前检查随机源健康，失败时维持脱机服务并报告诊断。session 在同次启动递增分配，耗尽时拒绝新会话。DTR 撤销、USB 复位或断开使会话失效，USB suspend 单独发生时保留会话和卡所有权。旧会话请求拒绝；未握手不得改变状态。

capabilities 是实际开放的请求 opcode 列表；订阅 RAW 前还须验证当前速率与带宽组合，拒绝未验证组合。rate_monitor/rate_record 仅列可用采样档。初始 HELLO 使用 request_id=1；该会话普通请求从 2 开始严格递增，不回绕。客户端可在同会话内用原编号重发相同请求。固件按收到顺序裁决；状态修改保留最近 4 个请求的完整请求字节（头和载荷）及回复或操作引用，执行中项固定至结束。满且均在执行时拒绝新修改，不驱逐在途项；编号过期返回 STALE/EXPIRED，同编号不同内容返回 INVALID/REQUEST_ID_REUSED。忙后重新发起新尝试用新编号。只读查询可用新号重复，旧号未缓存则返回过期。缓存与业务结果保留分别计入 RAM。

GET_STATUS 为一次逻辑一致快照，status_revision 按发布快照递增，mono_us 为启动后单调时间。record 和 operation 为当前记录与最近活动操作提示；多个并发操作分别以受理时的编号查询。GET_OPERATION 在本次启动内保留全部在途及最近 8 个已结束操作。GET_RECORD 至少保留当前及最近 4 个结束记录的摘要，脱机按键记录同样可查。环满淘汰最老终态，过期返回 STALE/EXPIRED，未分配编号 INVALID/NOT_FOUND；重启后重新握手，客户端用 (uid,boot,id) 识别结果。更早的持久记录以文件为准。事件是提示，丢失事件后查询仍有效。

## 操作行为

| 请求 | 规则 |
| --- | --- |
| BEGIN_RECORD、END_RECORD | BEGIN 的 duration_ms 省略表示使用当前配置，零表示手动结束；非零以确认起点 B 的单调时刻起算。受理先分配记录号和操作号。开始操作在确认 B 后完成；记录本身持续。END 指定 record，受理后待末边界 E 及存储收尾完成才结束。GET_RECORD 的 phase 反映记录生命周期，进行中 clean_end=false。 |
| SAFE_STOP、RESUME_MONITOR | 安全停止失效化冲突启动、停止激励与采集、有界收尾。恢复仅启动监测。查询和安全路径保留容量；同目标重复停止可合并。 |
| GET_CONFIG、APPLY_CONFIG、SAVE_CONFIG、BUILD_R0、CALIBRATE、SET_UTC | APPLY 和 SAVE 校验 expected_version 等于当前运行版本；配置整体校验。R₀ 使用当前试件，校准使用板载参考。UTC 为 Unix epoch 秒，范围 2000–2099。返回 ACCEPTED 的操作均可按操作号查最终结果；校时不改定时试验截止时间。 |
| MSC_EXPORT、MSC_RELEASE | 显式申请/交还 TF；CDC 保持可查询。RELEASE 等所有原始读退出；实际重挂载失败报告故障。 |
| FILE_LIST、FILE_OPEN、FILE_READ、FILE_CLOSE | 只读历史文件。file_id 对应 DRMSnnnn.BIN 的 nnnn。列表按编号递增，cursor 为下一候选号（首次 0），每次至多一项，无 next_cursor 表示结束，查询不持有跨请求租约。每次列举都须获短时 TF 访问权。列表是即时视图；换卡使旧选择失效，介质代次见下文。OPEN 建立本会话唯一下载，成功回复 OK 时文件已打开，operation 是下载句柄；READ 使用绝对偏移，可重读，count=1..768，offset 等于文件大小返回空 data、eof=true，越界拒绝。CLOSE 或断线退出句柄，等在途 I/O 完成才释放。文件请求可异步等待存储线程，CDC 接收线程保持可用。 |
| SUBSCRIBE、UNSUBSCRIBE | 会话级，断线清除。stream=CURVE 为经降速的最新快照，period_ms 正值；RAW 以 period_ms=0 请求分块，受带宽限制。返回实际周期。每流 sequence 从 1 递增，lost 为本次订阅累计未交付条目数（曲线点或原始帧）。RAW data 为同一代次连续的 16 字节记录，按 [BIN 记录布局](../design/2026-11-06-record-v2-format.md)；缺口或换代另起帧。 |
| OP_EVENT、FAULT_EVENT、MEAS_EVENT、RAW_EVENT | 设备单向发送；故障及操作结果在帧边界优先。控制回复保留发送槽，慢主机先丢可替代遥测并统计。当前没有已实现的升级能力，升级命令在独立 Bootloader 规格冻结时分配。 |

介质代次 media_generation:u32 用 tag 85；GET_STATUS、FILE_LIST 成功回复必须携带，FILE_OPEN 必须提交列举时取得的代次。遍历多页时每页核对介质代次，变化后从头列举。每次插拔或介质重新识别均推进，旧代次请求返回 STALE；句柄同时绑定介质及 USB 会话。BEGIN/END 等控制请求不接受文件路径。跨会话重连后先查询；旧请求和订阅不自动重放。

## 队列满、重试与状态恢复

- 解码后按会话串行完成准入。先为首次修改预留去重位置和必要回复槽，再投递业务。收到四槽均忙时的 BUSY 后，该编号被消耗；同号重发至多得到 BUSY 或 STALE，不能稍后自行生效。安全停采另有一个固定锁存位和回复槽，不消耗普通四槽。普通控制洪泛不能饿死该路径。已受理的操作即使 TX 断开仍由设备控制归结。
- FILE_OPEN、FILE_CLOSE 和订阅变更同属需去重的修改。FILE_READ 为绝对偏移只读查询；同偏移新编号可重试。文件句柄的 phase 持续为 ACTIVE 至关闭。GET_RECORD 的 result 在终态前用 ACCEPTED；空记录、关闭完整性、采集缺失分别表达。结果缓存只存小回复或操作引用；不缓存下载数据块。
- GET_STATUS 中等级字段仅供 fresh 且 CONFIRMED 时显示；ratio 和 ohms 各自需要有效输入。未配置的 R₀ 或校准版本用 0。基线不可用不阻止单独输出有效电阻。序号、版本号、UTC 不能相互代替。枚举不依赖 C 源码值，按机器表转换。
- TX 有一个在途帧。为控制和故障保留容量，故障重复通知可合并，最终结果可查询。原始流出现采样序号跳跃时保留实际位置；USB 订阅丢弃计数与采集丢失分别解释。流调度根据实际完成及已验证的限速参数推进。

## 放行

编码器和解码器各自从机器向量跑通，另外覆盖空载荷、内部零、连续 254 个非零字节、最大载荷、CRC 端序、超长后重同步及未知字段。测试必须从实际 CDC 收包入口到控制结果以及单一发送者，不以直接调业务函数代替。当前无上位机，可以使用测试端回放；Windows/Linux 枚举、实际发送完成与断开恢复另做板测。
