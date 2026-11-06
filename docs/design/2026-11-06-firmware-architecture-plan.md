# 固件架构收敛实施计划

> **For agentic workers:** 执行时使用 executing-plans 技能逐任务推进。仅用户明确选择委派时使用 subagent-driven-development；本文件不授权自动并行写入。每个任务通过门禁后才能进入依赖任务。

**Goal:** 修复架构复核 R1–R8 的八类缺口，形成可测试的控制、记录、配置和测量边界。

**Architecture:** 控制模块串行预占资源；采集/处理/存储通过有界数据和完成槽协作。算法纯函数与硬件后端分离；取消以资源静止证据结束，配置/R0以完整快照提交。

**Tech Stack:** C、STM32U575、ThreadX、FileX、USBX；Python unittest 编译真实 C 模块并注入硬件替身。

**Spec:** [固件架构规格](2026-11-05-firmware-architecture.md)，特别是实施约束 R1–R8；MSC 参考 [独立规格](2026-11-05-msc-design.md)。

## 全局约束与执行状态

- 本计划待用户审阅并选择执行方式；当前仅完成设计文档，不能勾选代码任务。
- 工作根目录 `/media/anning/data/Project/DE-DRMS`；下文文件路径相对于该根目录。
- 不修改 EDA、硬件、IOC IP、历史仿真或测试门槛；不自动推送，不清理用户未提交文件。
- 开机监测，记录仅显式请求；无卡可监测、建立 R0 和保存用户配置；不自动恢复试验。
- 保留既有 BIN v1 的解释与回归。新元数据采用独立版本，不在旧结构内偷换字段。
- 正式 COBS 协议、Bootloader、客户阈值标定是独立交付，不混入本次重构。
- R1–R8 是本计划验收要求；硬件实测缺席时结论必须为“软件通过、板测未验收”。
- 运行环境/文件与本计划不一致时先读实际源码，记录差异；不要覆盖其他会话的新实现。
- 文件列表中的“新增”是计划产物，不表示当前已存在；不修改 AGENTS.md 的目录登记。

## Review Focus

1. 文件已创建但 STARTING 被取消后，迟到 READY 不得启动记录（T2）。
2. END 到达时原始环仍有旧数据，最终文件不得缺尾或混入下一次试验（T2）。
3. 校准提交成功、用户区更新前掉电，旧 R0 必须因依赖不匹配而失效（T5）。
4. 存储隔离后的迟到 DMA 回调不得写入已归还给其他模块的缓冲（T3）。
5. 有效样本仅差一个就满足确认时间时出现无效输入，恢复后必须重新计时（T6）。

## 任务依赖与允许停止的位置

T0 → T1（公共契约冻结）→ T2a（内存边界）→ T3 → T4 → T5 → T2b（文件格式）→ T6 → T7 → T8。
每个任务独立提交并报告；T4 完成后可交付存储边界阶段，T6 完成后可交付业务纯逻辑阶段。
T7 才整合线程与启动行为；禁止前面边写边启动半套新状态机。
现有 MSC 计划先核对并复用；T4 负责补齐本次新所有权模型，不另建第二套存储所有者。

## 统一类型与接口约定

在 `Core/Inc/drms_architecture_contract.h` 定义（前缀路径均为 `firmware/DE-DRMS-Code/`）：

- `DRMS_Result`：OK、ACCEPTED、BUSY、INVALID、STALE、NO_CHANGE、IO_ERROR、TIMEOUT、CANCELLED、INCOMPLETE、QUARANTINED、UNSUPPORTED。
- `DRMS_Token`：`uint64_t operation_id; uint32_t generation;`。编号运行期不复用；复位后由 boot_id 区分。
- `DRMS_Position`：`uint32_t generation; uint64_t index;`。index 是唯一采集生产端发布的流位置，不依赖记录帧布局。
- `DRMS_End`：token、`uint64_t record_id, ring_end, lost_count;`、first/end_exclusive（DRMS_Position）、reason（DRMS_Result）。
- `DRMS_Resource` 位集合：ACQUISITION_CONFIG、RECORD_SESSION、TF_ACCESS、FLASH_MAINTENANCE、UPDATE_EXCLUSIVE。
- `DRMS_Health`：ABSENT、READY、FAULT；`DRMS_Owner`：LOCAL、EXPORTING、EXPORTED、RELEASING、QUARANTINED。
- 异步命令先返回接受/拒绝；最终结果由 token 匹配的完成槽/事件获得。裸指针载荷不跨线程，除非有显式固定池所有权。

结构只用于进程内；线格式/文件/Flash均显式编解码。64-bit字段在M33上不假设天然原子，快照必须通过短临界区或序列协议一致读取。

## T0 基线与迁移清单

**文件：** 只读现有 Core/Inc、Core/Src、USBX、FILEX、Makefile、链接脚本、tools/firmware_postgenerate.py；更新本计划执行记录。

- [ ] 记录 `git status --short`、当前提交、实际所有 drms 模块及用户改动；创建隔离工作区前确保未提交新固件不会被遗漏。不能仅用 HEAD 的旧 U545 工程开始实现。
- [ ] 运行 `python3 -m unittest discover -s test -p 'test_*.py'`，记录实际数量和结果，不把历史104项当固定现状。
- [ ] 运行 `python3 tools/firmware_postgenerate.py`；有差异先解释，不盲目 --apply 覆盖用户新模板。
- [ ] 运行 `make -C firmware/DE-DRMS-Code -j6 BUILD_DIR=/tmp/de-drms-architecture-baseline`，保存工具版本、ELF/map摘要。
- [ ] 从当前线程创建代码列出线程、栈、池、优先级、阻塞点；从 map 列出总 RAM/Flash。

**通过：** 基线可复现，已有失败有明确归因；若生成工程缺失或基线失败原因不明，停止后续，不把失败带入重构。

## T1 原子资源裁决与代次

**新增：** `Core/Inc/drms_architecture_contract.h`、`Core/Inc/drms_control.h`、`Core/Src/drms_control.c`、`test/test_control_contract.py`。
**后续接入：** `Core/Src/drms_application.c`，此任务先保留旧入口适配，不并行运行新旧裁决器。

**接口：**
`DRMS_Result drms_control_reserve(uint32_t resources, DRMS_Token *out);`
`DRMS_Result drms_control_complete(DRMS_Token token, DRMS_Result result, uint32_t quiescent_mask);`
`void drms_control_stop(void);`
控制上下文私有；以上函数只在控制任务调用。其他任务发送消息，不能直接调用改变状态。

- [ ] 写测试：先 reserve(RECORD|TF) 成功，再 reserve(TF) 返回 BUSY；资源无部分占用。
- [ ] 写测试：投递失败回滚尚未启动预占；已投递超时不能释放；旧 generation 完成不启动新业务。
- [ ] 写测试：stop 后已排队 start 失效；重复 stop 幂等；完成结果通道拥塞仍可查询结果。
- [ ] `python3 -m unittest discover -s test -p 'test_control_contract.py'`，先确认失败源于缺少实现，再实现到通过。
- [ ] 审查所有状态写入仅在一个上下文；提交本任务文件。

**通过：** 每个资源任意时刻最多一个有效所有者；停止没有迟到重启路径。

## T2a 记录首末边界与完成槽

**新增：** `Core/Inc/drms_record_session.h`、`Core/Src/drms_record_session.c`、`test/test_record_boundary.py`。
**修改：** `Core/{Inc,Src}/drms_logging.*`、`drms_acquisition.*`、`drms_application.*`；保持 `drms_fifo` acquire/release语义。

**接口：**
`DRMS_Result drms_record_prepare(DRMS_Token token, uint64_t record_id);`
`DRMS_Result drms_record_ready(DRMS_Token token, DRMS_Position next_published);`
`DRMS_Result drms_record_stop_at(DRMS_Token token, DRMS_Position end_exclusive);`
`DRMS_Result drms_record_end_get(DRMS_End *out);`
`DRMS_Result drms_record_end_ack(DRMS_Token token, DRMS_Result result);`
ready/stop由处理上下文调用；end_get/ack通过单槽同步在存储上下文执行，不能引入多生产者数据环。

- [ ] 测试：READY时发布水位为100，旧0..99不进入记录；STOP捕获110，则文件含100..109，110后只监测。
- [ ] 测试：原始数据尚未处理时STOP，不漏边界前数据；重复STOP保持首次末边界。
- [ ] 测试：STARTING取消、迟到READY、连续两试验、32-bit序号回绕、跨generation拒绝、数据环满仍能发END。
- [ ] 测试：写/尾/close/flush分别失败均不报告成功；无尾文件解码标记不完整。
- [ ] 运行 `python3 -m unittest discover -s test -p 'test_record_boundary.py'`，失败→实现→通过；同时跑现有test_logging.py/test_fifo.py/test_log_decoder.py。
- [ ] 本任务只验收内存边界；文件/缺尾相关测试移交强制前置任务T2b，未完成T2b不得报告记录交付。

**通过：** 每个成功记录有确定的闭开样本区间；数据/END顺序可证明；存储确认前不能复用槽。安全停止可截短但必须报告原因。

## T3 取消、隔离和资源恢复

**新增：** `Core/Inc/drms_resource_lifecycle.h`、`Core/Src/drms_resource_lifecycle.c`、`test/test_resource_lifecycle.py`。
**修改：** drms_acquisition.c、drms_storage.c、drms_power.c及对应后端；仅在需要处修改SD驱动恢复工具。

**接口：**
`DRMS_Result drms_resource_cancel(uint32_t resource, DRMS_Token token, uint64_t now_ms);`
`DRMS_Result drms_resource_quiescent(uint32_t resource, DRMS_Token token);`
`DRMS_Result drms_resource_recover(uint32_t resource, uint64_t now_ms);`
后端独立提供 abort/recover 结果；生命周期模块不直接包含 HAL。

- [ ] 对每个后端写清“静止证据”和取消总期限来源；核实当前HAL/驱动实际阻塞上限，不能仅在外层增加无效超时。
- [ ] 注入时钟测试 ACTIVE→CANCELLING→QUIESCENT；超时一次恢复失败→QUARANTINED；拒绝新请求且缓冲仍占用。
- [ ] 测试迟到DMA回调、旧token、重复取消、恢复成功、恢复失败不循环重启；主机超时不能释放底层缓冲。
- [ ] 测试安全停止先执行抑制，不等文件；关机总期限到达不能虚报已保存。
- [ ] `python3 -m unittest discover -s test -p 'test_resource_lifecycle.py'` 失败→实现→通过，并回归test_power*.py/test_sd_driver_recovery.py/test_usb_dcd_abort.py。

**通过：** 无超时后内存重用、无无界等待、无无限恢复循环；无法证明静止时资源隔离而非假释放。

## T4 TF 双轴状态与 MSC 接入

**修改：** drms_storage.h/c、drms_logging.c、USBX/App/ux_device_msc.c（以实际生成文件名为准，先 rg 确认）、既有MSC适配、test/test_storage_lifecycle.py。
**新增测试：** `test/test_storage_ownership.py`。

**接口：** `void drms_storage_snapshot(DRMS_Owner *owner, DRMS_Health *health);` 返回一致快照；现有状态字段只作为兼容投影，禁止双写新旧状态源。

- [ ] 测试LOCAL+ABSENT/FAULT不阻止纯监测及Flash维护；记录要求LOCAL+READY且挂载成功。
- [ ] 测试导出与开始记录同时到达只允许一个预占成功；导出切换失败不同时开放FileX和原始读取。
- [ ] 测试隔离SD拒绝维护；确认静止后仅卡故障不阻止Flash保存。
- [ ] 按既有MSC计划完成在途读取、拔卡/reset/unconfigure、容量变化、只读拒写；复用T3取消，不另设不受控制的清理路径。
- [ ] `python3 -m unittest discover -s test -p 'test_storage_ownership.py'` 失败→实现→通过，再执行现有MSC计划的全部软件门禁。

**通过：** 无卡不依赖FileX初始化成功；整个SD生命周期只有一个所有者；MSC板测单独标记。

## T5 用户配置/R0事务与链接保护

**新增：** `Core/Inc/drms_user_config.h`、`Core/Src/drms_user_config.c`、`Core/Src/drms_user_journal.c`、`test/test_user_config.py`、`test/test_user_journal.py`。
**修改：** STM32U575xx_FLASH.ld、tools/firmware_postgenerate.py、test/test_postgenerate.py；复用现有校准后端模式，不改校准槽地址。

**接口：**
`DRMS_Result drms_user_config_apply(const uint8_t *encoded, size_t length, uint64_t expected_version);`
`DRMS_Result drms_user_config_save(uint64_t expected_version);`
`DRMS_Result drms_user_config_commit_baseline(double r0, uint64_t expected_version, uint64_t calibration_version);`
业务调用为异步请求的后端处理接口，不允许CDC线程直接擦写；持久化完成后才返回成功给完成槽。

- [ ] 定义编码schema1：固定小端整数、浮点显式IEEE754 binary64编码（检查有限性）、长度化字段、完整CRC参数与提交单位；总长≤4096B。将布局写入本模块格式文档，测试黄金字节向量，禁止memcpy struct落盘。
- [ ] 测试区间≤16、名称≤48UTF8字节、非法UTF8/NaN/Inf/重叠/非法端点/超长拒绝；未配置表合法但分类为UNCONFIGURED。
- [ ] 测试未保存运行配置+新R0原子提交；保存失败旧R0保留；校准版本改变后掉电恢复旧R0无效。
- [ ] 在每个擦除/编程/提交步骤注入掉电；重启只得到完整旧或新快照；同值保存不擦写；未来schema不被普通保存覆盖。
- [ ] 链接改ROM=992KiB并保护080F8000..080FFFFF；现有校准保留080FC000..080FFFFF。同步postgenerate及地址越界测试后才允许写新区域。
- [ ] 运行 `python3 -m unittest discover -s test -p 'test_user_*.py'` 失败→实现→通过，回归校准journal、postgenerate；执行ARM构建并核对map。

**通过：** 无卡可提交；任意提交阶段掉电不形成配置/R0错配；固件和工具不会覆盖32KiB配置区。

## T6 纯算法拆分与无效恢复

**新增：** `Core/Inc/drms_filter.h`、`Core/Src/drms_filter.c`、`Core/Inc/drms_classifier.h`、`Core/Src/drms_classifier.c`、`Core/Inc/drms_baseline.h`、`Core/Src/drms_baseline.c`、`test/test_monitor_pipeline.py`。
**保留/接入：** drms_measurement.h/c中的解码换算；drms_application.c仅协调。

**接口规则：** 严格实现设计C6的DRMS_MonitorInput/Config/Output与init/configure/step/tick接口；内部filter/classifier/baseline模块保持显式context。公共头文件在T1冻结，T6不得重新解释单位、端点或状态。调用无I/O、无RTOS、不分配堆。

- [ ] 首版filter明确采用流式一阶IIR：y += alpha*(x-y)，alpha由采样间隔和配置时间常数换算；首样本初始化y=x，时间常数0为旁路。配置另含连续有效建立时间，不以IIR理论完全收敛为有效条件。
- [ ] 区间采用有序不重叠表及显式端点；未覆盖值输出UNMAPPED。候选跨级直接选择目标区间；回差仅用于退出当前区间，阈值以R/R0单位表示。
- [ ] 回差严格执行C6的2h<区间宽度及空隙约束；跨越多个区间不逐级等待。确认时间0允许首次合格结果立即生效。
- [ ] 测试边界本身/两侧、上下方向、缺口、回差、跨级；使用合成阈值，不当客户正式参数。
- [ ] 测试持续确认只差一个样本时出现NaN/CRC故障/缺样/过期/代次变化：计时归零，滤波失效；恢复需完整建立窗口后再确认。
- [ ] baseline采用有界流式统计；质量规则参数显式输入，测试稳定/超时/异常值；输出候选不直接保存。
- [ ] `python3 -m unittest discover -s test -p 'test_monitor_pipeline.py'` 失败→实现→通过；审查不包含HAL/USB/FileX/ThreadX头。

**通过：** 失效时无正常等级；算法可离线复现；内存不随任意时窗增长。实际默认时常/质量门限需客户或台架依据，未定标时不启用正常等级输出。

## T7 线程集成、启动与预算

**修改：** Core/Src/app_threadx.c、drms_runtime.c、drms_application.c、USBX/App、FILEX/App实际入口、Makefile、tools/firmware_postgenerate.py。
**新增测试：** `test/test_architecture_integration.py`。

- [ ] 依据T0清单给出最终线程表及静态栈/队列分配，写入本计划执行记录；所有数值须在代码中集中定义，不散落魔数。
- [ ] 先接通控制/采集/处理/存储，再本机交互与通信；每迁移一个所有者删除旧轮询写路径，不能同时保留两个控制源。
- [ ] 处理线程调用T6纯模块；记录分发调用T2；控制协调T1/T3/T5；只在本机交互上下文驱动灯。
- [ ] 把UART调试及CDC旧入口适配为同一业务请求；正式二进制协议未完成时不宣称COBS已实现。
- [ ] 测试开机/唤醒/重连/插卡自动监测但不记录；基线未配置为无效等级；停止记录不停止监测；无卡/坏卡运行完整流程。
- [ ] 从map统计主RAM总预算≤736KiB；每个队列溢出有测试与计数，每个启动资源创建失败有拒绝路径。
- [ ] 明确持续就绪处理任务与存储的调度策略；禁止仅用yield或固定10ms睡眠作为吞吐保证。
- [ ] `python3 -m unittest discover -s test -p 'test_architecture_integration.py'` 失败→实现→通过，然后全量回归与生成检查。

**通过：** 单一所有者可从调用图验证；启动/停止/配置/导出没有跨线程同步循环等待；RAM有余量。

## T8 系统验收与交接

- [ ] `python3 -m unittest discover -s test -p 'test_*.py'` 全通过，记录数量；新增测试必须调用真实C生产模块，不能只检查源字符串或复写算法。
- [ ] `python3 tools/firmware_postgenerate.py` 通过；生成恢复幂等测试通过。
- [ ] `make -C firmware/DE-DRMS-Code -j6 BUILD_DIR=/tmp/de-drms-architecture-final` 成功；新增警告必须消除。
- [ ] `git diff --check` 通过；逐文件审查只包含授权范围，按阶段提交源文件/文档，不提交产物。
- [ ] 硬件可用时测试各宣称支持采样档：单监测、记录、MSC复制、慢主机、USB反复插拔、卡写满/拔出、配置保存断电。
- [ ] 测量DRDY至SPI完成最坏延迟、处理最长失调度、卡最长停顿、队列峰值/溢出、栈水位；主RAM及栈门槛按R6，不降低门槛换通过。
- [ ] 无硬件则填写“板测未执行”，正式能力保留已验证范围；128kSPS不得默认升级为已支持。

## 结果模板与自查

每个执行agent必须给出：

```text
阶段 / 提交：
输入基线：
修改文件与边界：
接口变化及调用方：
测试命令、退出码、数量：
故障注入与结果：
资源所有者与释放证据：
RAM/Flash/栈证据（适用时）：
未完成项及阻塞条件：
结论：未完成 / 软件验收通过、板测未验收 / 软件及列明板测通过
```

自查映射：R1→T2；R2→T1；R3→T5；R4→T3；R5→T4；R6→T0/T7/T8；R7/R8→T6。
不得仅以“编译成功”“全部完成”结束交接；下一个agent必须能从结果重放验证。

## 本次文档自审记录

2026-11-06：已逐项映射八条评审问题、对应模块与故障测试；现有文件名通过仓库读取核对。
本计划新增模块尚未创建，未执行代码任务；性能和硬件恢复时间未冒充实测值。
本计划只覆盖架构收敛；正式协议字节规范、客户定标和Bootloader另行交付；最小新版记录格式纳入强制任务T2b。


## 二次复核后的强制补充任务与门禁

本节与设计C1–C6同时生效，覆盖此前概要接口的歧义。所有[ ]保持未执行，不能把文档检查算作代码测试通过。

### T1补充：公共契约冻结与冲突矩阵

- [ ] 在drms_architecture_contract.h固定C5/C6公共类型及单位，结果枚举补EMPTY；控制/采集/记录代次分别命名，边界类型采用DRMS_CaptureBoundary，不再将raw_ticket当sample_seq。
- [ ] 定义并编译验证各公共模块init/get_snapshot、控制submit/poll、资源tick以及完成消息结构；在本计划附接口清单（函数签名、调用上下文、同步/异步、所有权）。这是实现开始的可审查交付，不允许跳过到T2a。
- [ ] 将C2七类操作编码为唯一资源集合表，UPDATE自动展开全资源；测试7×7有序操作对及升级单独位被拒绝/展开。
- [ ] 查询只读，消费完成槽仅控制线程；测试查询不会吞掉完成结果。

### T2a补充：三种位置验证

- [ ] 用C1的100..109缺102场景分别断言sample/raw/log三个计数，不能只测试连续正常样本。
- [ ] 捕获边界时注入在途DMA、入环失败和DRDY；边界发布前所有旧DMA已归结；超时不返回可用边界。
- [ ] 新会话在第一帧前不得报告RECORDING；无第一帧取消不挂起；空记录返回EMPTY。
- [ ] 不扩大原始/记录帧使608KiB预算失效；低32位扩展超过可证明跨度时LOSS_UNKNOWN并结束记录。

### T2b 新版记录规格与编解码（T5之后，T7之前）

**新增：** `docs/design/2026-11-06-record-v2-format.md`、`test/test_log_v2_codec.py`。
**修改：** `Core/Inc/drms_log_codec.h`、`Core/Src/drms_log_codec.c`、`Core/Src/drms_logging.c`、`tools/de_drms_log.py`；若涉及控制协议字段，同时更新docs/protocol与shared/protocol对应定义。

- [ ] 先交付C4要求的字节布局表、CRC参数、最大长度、错误处理以及至少一个手工可核算黄金文件；规格自审后才写编码器。未定义字段是此子任务待完成项，不得带入实现猜测。
- [ ] 测试真实C编码器与Python解码器对配置快照、UID、首末边界、坏帧、已知/未知损失、结束原因解释一致。
- [ ] 测试每个字节截断和位翻转、超长chunk、重复END、END后额外数据；不完整/非法文件不能显示成功。
- [ ] 测试v1历史夹具仍按旧规则解码，新写入明确v2，不在旧文件追加未定义字段。
- [ ] 运行 `python3 -m unittest discover -s test -p 'test_log_v2_codec.py'`，失败→实现→通过；回归现有日志测试。

**通过：** 格式文档、黄金向量、两端编解码与真实存储写入测试齐备；不能以T2a通过代替。

### T6补充：独立tick与分类转换表

- [ ] 按C3建立无样本tick测试：119999/120000us边界、无首帧、旧积压帧、时基倒退、RTC变化。
- [ ] 按C6转换表逐行测试，包括离开confirmed后PENDING不继续输出旧正常等级、空隙UNMAPPED、候选返回旧区间重新确认。
- [ ] 相同采样时间序列按1帧/批、多帧/批输入输出一致；tick只能失效，不能在没有新样本时完成等级确认。
- [ ] IIR alpha在配置变化时计算或缓存，不在每帧无必要重复exp；原始记录不受滤波影响。

### T7/T8补充：可观测上界与最终交付

- [ ] 处理任务有独立10ms新鲜度检查唤醒，不依赖ADC中断继续存在；记录最大调度延迟及过期可见上界。
- [ ] C1–C6、R1–R8全部有测试对应；接口清单、v2格式、资源矩阵、线程预算必须与代码一致。
- [ ] 最终报告分列：设计契约完成、软件门禁通过、实板门禁通过、客户参数定标。没有证据的一列不得标完成。

闭环映射：C1→T2a；C2→T1；C3→T6/T7；C4→T2b；C5→T1；C6→T6。
预算门禁是项目工程策略，真实容量和水位证据来自T0/T7/T8，不混称芯片要求。
