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
- `DRMS_End`：token、`uint64_t record_id, ring_end, lost_count;`、first/end_exclusive/last_confirmed_position（DRMS_Position）、end_known（bool）、capture_lost/log_dropped/quality_bad（uint64）、unknown_loss/storage_error（bool）、reason（DRMS_Result）。lost_count仅保留兼容诊断，不作为跨阶段相加的精确总数。
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

### T0 执行记录（2026-11-08）

- **git 状态**：HEAD=37be37e；`git status --short` 共 828 行，快照存于本计划 SDD 工作区（`.superpowers/sdd/2026-11-06-firmware-architecture-plan/t0_git_status.txt`）。
  关键事实：`firmware/DE-DRMS-Code/` 整目录**未跟踪**（U575 重建工程与全部应用源码在工作区、未入库）；
  旧 `firmware/DE-DRM/`（545 工程）标记删除；用户另有 sim/文档/测试改动未提交。按用户规则不批量暂存、不清理、不重置。
- **实际 drms 模块**（全部未跟踪）：Inc 16 个（acquisition/application/calibration(+backend)/cdc/command/console/fifo/log_codec/logging/measurement/power/runtime/storage/time/usb）；Src 19 个（另含 calibration_codec/calibration_flash/calibration_journal/power_stm32/aux/time_codec）。
- **测试基线**：`python3 -m unittest discover -s test -p 'test_*.py'` → **104 项全过（3.0 s）**，与计划"不把历史104项当固定现状"一致——当前即为 104。
- **生成恢复检查**：`python3 tools/firmware_postgenerate.py`（不带 --apply）→ `OK: known CubeMX template fixes are present`，无差异，无需解释。
- **ARM 构建**：`make -C firmware/DE-DRMS-Code -j6 BUILD_DIR=/tmp/de-drms-architecture-baseline` 成功。
  工具链 arm-none-eabi-gcc 13.2.1（15:13.2.rel1-2）、Python 3.12.3、GNU Make 4.3。
  ELF：text 120144、data 408、bss 709184、dec 829736。
- **map RAM/Flash**：链接区 RAM 768 KiB @0x20000000、ROM 1008 KiB @0x08000000、CALDATA 16 KiB @0x080FC000（两 8 KiB 校准槽）、SRAM4 16 KiB @0x28000000（当前未用）。
  `.data` 408 B + `.bss` 0xac240=705,088 B（688.5 KiB）+ `_user_heap_stack` 4 KiB ≈ **693 KiB / 768 KiB**，静态余量约 75 KiB。
  608 KiB 三大缓冲实测在位：原始环 `.bss.frames` 0x10000=64 KiB（drms_acquisition.c:8，4096×16 B）、
  记录环 `.bss.records` 0x80000=512 KiB（drms_logging.c:15，32768×16 B）、staging 0x8000=32 KiB（drms_logging.c:17）。DRMS_RawFrame=16 B 确认。
- **线程/栈/池/优先级/阻塞点**（当前源码实测）：
  | 线程 | 栈 | 优先级 | 主循环与阻塞点 |
  | --- | --- | --- | --- |
  | Main Thread（app_threadx.c:78） | 4 KiB，从 Tx App 池分配 | 5 | `drms_runtime_run`→poll：命令队列(16×DRMS_Command)接收、`drain_frames`（测量/校准统计/记录入环）、LED 100 ms、辅助 1 s、UART 控制台（rx 128 B 环、tx 1 KiB DMA）；`tx_thread_sleep(1)` |
  | FileX App Thread（app_filex.c:104） | 4 KiB，从 Fx App 池 | 10 | `drms_storage_poll`（SD 挂载/CD）+`drms_log_poll`（记录环→staging→FileX 写卡，FileX 内部阻塞） |
  | USBX Device App Main Thread（app_usbx_device.c:92） | 1024 B，从 Ux App 池 | 10 | USBX 设备栈入口 |
  | CDC diagnostics（drms_cdc.c:96） | 3 KiB（768×4 B，静态） | 11 | `drms_cdc_poll`+sleep(1) |
  | ThreadX 定时器线程 | 默认 1024 B | 5（tx_user.h:116） | 系统定时 |
  | 池 | Tx 8 KiB / Fx 8 KiB / Ux 40 KiB（app_azure_rtos_config.h:53-59） | — | 线程栈从池分配，池在 .bss 内 |
  ISR 路径：ADS_DRDY(EXTI3)→`drms_acq_drdy`（**32-bit `drms_acq_edges` 序号**，C1 需扩展为 64-bit 流位置）→SPI DMA；DMA 完成 ISR→fifo push，失败置 error=6 并停采集。UART RX 单字节中断环。按键 EXTI 置位后由主线程轮询。与计划差异：无边界屏障、无 cancel/隔离、单主线程既做处理又做控制——由 T1/T2a/T7 重构。
- **结论**：基线可复现，无失败项，不停止。T0 通过（软件层面；无硬件项）。

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

### T1 执行记录（2026-11-08）

**交付物**：`Core/Inc/drms_architecture_contract.h`（公共契约唯一位置，仅标准 C 类型）、
`Core/Inc/drms_control.h`、`Core/Src/drms_control.c`、`Core/Inc/drms_capture_time.h`、
`Core/Src/drms_capture_time.c`、`test/test_control_contract.py`（13 项）、`test/test_capture_time.py`（9 项）。
测试先失败（缺实现）后实现；全量 `test_*.py` 126/126 通过（104 旧 + 22 新）。
`drms_control.c`/`drms_capture_time.c` 暂不入 Makefile（T7 统一接线），ARM 构建不受影响。

**冻结接口清单**（签名 / 调用上下文 / 同步性 / 所有权）：

| 签名 | 上下文 | 同步性 | 所有权与说明 |
| --- | --- | --- | --- |
| `void drms_control_init(DRMS_ControlDispatch)` | 启动 | 同步 | 注入投递钩子；清零全部控制状态 |
| `DRMS_Result drms_control_submit(const DRMS_ControlRequest*)` | 任意线程 | 同步返回 ACCEPTED/BUSY/INVALID/CANCELLED | 复制请求入 8 深有界队列；不返回 token |
| `void drms_control_poll(uint32_t max_requests)` | 仅控制任务 | 同步 | reserve→dispatch；reserve 失败/投递失败即写完成记录回滚 |
| `DRMS_Result drms_control_reserve(uint32_t resources, DRMS_Token*out)` | 仅控制任务 | 同步 | 一次性全量检查，无部分占用；UPDATE_EXCLUSIVE 展开为全部；lease 表 4 深 |
| `DRMS_Result drms_control_complete(DRMS_Token, DRMS_Result, uint32_t quiescent_mask)` | 仅控制任务 | 同步 | quiescent 掩码内归还，其余转隔离（保持占用）；代次不符返回 STALE 仅清理 |
| `void drms_control_stop(void)` / `DRMS_Result drms_control_resume(void)` | 仅控制任务 | 同步 | stop 幂等（代次只增一次）；resume 要求无活动租约 |
| `uint32_t drms_control_collect(DRMS_ControlCompletion*, uint32_t)` | 仅控制任务 | 同步 | 排空完成环（8 深，溢出丢最旧并计数） |
| `void drms_control_get_snapshot(DRMS_ControlSnapshot*)` | 任意（只读） | 同步（短临界区复制） | 不消费完成结果 |
| `uint32_t drms_control_resources_for(DRMS_Operation)` | 纯查询 | 同步 | C2 资源集合唯一定义 |
| `void drms_capture_time_reset(void)` | 采集所有者（代次切换） | 同步 | 停产+消费者确认后调用 |
| `DRMS_Result drms_capture_time_publish(raw_ticket, consumed_raw_next, gen, drdy_mono_us)` | 仅生产者（块首帧入环前） | 同步 | 覆盖资格用消费水位判定；不足返回 IO_ERROR 不覆盖 |
| `DRMS_Result drms_capture_time_lookup(raw_ticket, gen, *lower_bound_us)` | 仅消费者（释放环槽前） | 同步 | 无效/覆盖/换代返回 STALE |
| `uint64_t drms_capture_time_nominal_us(const DRMS_TimeAnchor*, sample_seq)` | 纯函数 | 同步 | 商余分解防溢出；只供算法不供新鲜度 |
| `drms_monitor_init/configure/step/tick`（contract.h 声明） | 仅处理线程 | 同步 | T6 实现公共体已冻结 |

**状态写入上下文自审**：submit（任意线程，PRIMASK 短临界区）；poll/complete/stop/resume/collect（仅控制任务）；init（启动）。租约表写者全部为控制任务上下文；快照读经临界区。

**决议（ledger）**：
- Ruling: `drms_control_submit` 不返回 token——C5 明文"submit只复制命令并返回ACCEPTED/BUSY/INVALID"，请求方以 (source,session,request_id) 关联完成记录，内部 operation_id 由 reserve 分配并随 dispatch/complete 交付。若作他解会违反 C5 冻结文本。
- Ruling: 投递失败回滚 = `complete(token, result, 全租约资源)`——工作从未到达后端，租约整体静止，无隔离项；完成记录 quiescent_mask=全租约。
- Ruling: 8×8 矩阵中不相交对的第二个操作无完成记录（在途），以 dispatch 次数=2、双租约并存、reserved_mask=两集合并集断言。
- Ruling: 单调微秒时钟后端选 **TIM2 @1 MHz、32 位计数 + 单写者 64 位扩展**（ISR 双读稳定取值），精度=±1 µs 计数粒度；回绕由唯一所有者上下文扩展。已在 contract.h 注释冻结；实板精度/回绕验收留 T7/T8。
- Ruling: 新增 `drms_control_resume()`——R2 要求"只有全部必要清理完成才解除 STOPPING"，stop 单向无法表达该解除路径。
- 侧表 2080 B 静态断言（`sizeof(DRMS_CaptureTimeEntry)==32`）+ `drms_capture_time_bytes()` 供预算测试。

**结论**：软件验收通过（主机测试）；无硬件项。C5 门禁（先头文件后实现、自包含编译、类型/单位/上下文清单）已满足。

## T2a 记录首末边界与完成槽

**新增：** `Core/Inc/drms_record_session.h`、`Core/Src/drms_record_session.c`、`test/test_record_boundary.py`。
**修改：** `Core/{Inc,Src}/drms_logging.*`、`drms_acquisition.*`、`drms_application.*`；保持 `drms_fifo` acquire/release语义。

**接口：**
`DRMS_Result drms_record_prepare(DRMS_Token token, uint64_t record_id);`
`DRMS_Result drms_record_ready(DRMS_Token token, DRMS_CaptureBoundary begin);`
`DRMS_Result drms_record_stop_at(DRMS_Token token, DRMS_CaptureBoundary end_exclusive);`
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

### T2a 执行记录（2026-11-08）

**交付物**：`Core/Inc/drms_record_session.h`、`Core/Src/drms_record_session.c`（纯逻辑会话状态机，无 HAL/RTOS）；
`drms_acquisition.{h,c}` 增加 64 位流记账（sample_seq/raw_ticket/capture_lost_total/unknown_loss_epoch）、
采集代次与一致边界 request/service/get（service 仅在无在途 DMA 的静止时刻快照，DMA 完成路径自动调用）；
`drms_logging.{h,c}` 增加 64 位 log_ticket（END.ring_end 域）与 enqueue 返回值；`test/test_record_boundary.py` 20 项。
全量 `test_*.py` 146/146（104 旧含回归 + 42 新）。ARM 构建通过零警告（text 120592，bss 709312）。
`drms_record_session.c` 暂不入 Makefile（T7 接线）。

**测试覆盖**（对计划条目）：100..109 缺 102 三位置断言（sample 跨 10/raw 跨 9/log 9，INCOMPLETE 且缺口=1）；
积压 SKIP/窗口 RECORD/边界后 MONITOR；未处理数据 STOP 不漏帧；重复 STOP 保持首次 E（NO_CHANGE）；
STARTING 取消+迟到 READY STALE；连续两会话（槽未 ack 前 BUSY）；32 位序号回绕扩展与 ≥2^31 不可证明跨度→LOSS_UNKNOWN；
重复序号→LOSS_UNKNOWN；跨 generation E 拒绝（STALE）后超时收尾（end_known=false+TIMEOUT）；
START 屏障超时；屏障期原始环满→INCOMPLETE；监测期损失不归属（B=7,E=7→0；B=0,E=2→2）；E 后损失不改冻结 END；
B==E 无损失→EMPTY、有样全丢→INCOMPLETE；首帧缺失不移动 B；在途 DMA 归结后才发布边界；环满仍发布 END（log_dropped→INCOMPLETE）；
延迟 E 回复期间消费者不越过 E、E 后帧不进旧记录；END 槽 ack 语义（错 token STALE）。

**决议（ledger）**：
- Ruling: `end_known` ⟺ 捕获到一致 E。失败路径（超时/取消/环满）一律 end_known=false、end_exclusive 置零、
  LOSS_UNKNOWN=true（有 B 无 E 时尾部连续性不可证明，对齐 C1"E 无法取得"条）；文件内已记录范围由 ring_end + last_confirmed_position 界定。
- Ruling: 新增 `drms_record_session_request_stop()` 与 `note_log_ticket/note_recorded/note_consumed/poll/barrier/classify` ——
  处理循环的屏障与回报协议需要显式入口；`drms_record_session_configure(wait_ms)` 供测试与 T7 配置边界等待期限。
- Ruling: 会话不直接读采集模块——B/E 以值传入（纯逻辑可测）；`prepare` 后处理循环须先 `note_consumed` 同步消费水位。
- Ruling: T2a 不改 `drms_application.c`（避免半套新状态机上线，符合 T7"禁止边写边启动"）；应用层接线归 T7。
- Ruling: `drms_log_enqueue` 返回入环结果并保留全局诊断 `drms_log_dropped` 自增（既有 STATUS 语义不变）；
  会话级 log_dropped 由 note_recorded 按返回值另计。
- ctypes 教训（已固化在测试中）：C 按值结构体参数（DRMS_CaptureBoundary）必须声明为结构体类型而非 POINTER，否则寄存器错位产生随机垃圾。

**结论**：软件验收通过（主机联合仿真）；无硬件项。文件/缺尾解码语义留待 T2b。

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

### T3 执行记录（2026-11-08）

**交付物**：`Core/Inc/drms_resource_lifecycle.h`、`Core/Src/drms_resource_lifecycle.c`（无 HAL：后端钩子表注入）；
`drms_acquisition.{h,c}` 增加采集生命周期后端 `drms_acq_resource_backend()`（abort=先抑制 CURR_DIS 再有界
`HAL_SPI_Abort`、静止证据=无在途 DMA 且采集已停止、recover=清错误闩锁由 acq_start 重建新代次）；
`test/test_resource_lifecycle.py` 13 项（9 项注入后端 + 3 项真实采集后端）。全量 159/159；
回归 test_power*.py / test_sd_driver_recovery.py / test_usb_dcd_abort.py 全过（模块未改动）。ARM 构建零警告。

**生命周期语义**（R4）：cancel 进入 CANCELLING 并立即一次有界中止尝试（abort=ACCEPTED 即 QUIESCENT）；
tick 周期 probe 静止证据，期限到达再尝试一次 abort/恢复，仍无法确认 → QUARANTINED（保持占用、拒绝 activate、
不假释放）；quiescent() 为所有者确认（ACTIVE/CANCELLING→QUIESCENT，已静止时幂等）；release 仅在 QUIESCENT
后归还；recover 仅显式调用、失败保持隔离不循环。取消总期限默认为未验证占位值（1000 ms），
`drms_resource_configure` 供测试注入小超时；**实测定值归 T7/T8 依据后端驱动阻塞上限**——
已核实边界：`HAL_SPI_Abort` 同步返回（HAL 内部标志等待，有界）；SD/FileX 操作由驱动超时约束（T4 接管存储后端时核对）。

**决议（ledger）**：
- Ruling: 存储与电源后端适配器**不在 T3 落地**——TF 生命周期语义在 T4（所有权/MSC 在途读取取消）才成形，
  电源安全停止序在 T7 接线；T3 以注入后端验证生命周期本体 + 采集真实后端示范，避免半套钩子造成假接口。
- Ruling: `drms_resource_recover` 成功返回 DRMS_OK（同步完成语义）；cancel 返回 ACCEPTED（异步取消开始）。
- Ruling: 无后端资源的 cancel 返回 UNSUPPORTED 且保持 ACTIVE（如 UPDATE_EXCLUSIVE 整机租约的取消由 T7 系统级路径处理）。
- Ruling: 安全停止验证点——采集后端 cancel() 内即时抑制完成（QUIESC）而存储仍 ACTIVE/CANCELLING；
  总期限到达未确认静止 → QUARANTINED → 快照可证明"不得虚报已保存"。

**结论**：软件验收通过（主机注入时钟）；无硬件项。

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

### T4 执行记录（2026-11-08）

**交付物**：`Core/Inc/drms_msc.h`、`Core/Src/drms_msc.c`（所有权状态机 + 单在途读邮箱 + FileX 交接，
已入 Makefile 与 postgenerate 恢复清单）；`drms_storage.{h,c}` 增加 `drms_storage_snapshot(owner, health)`
双轴一致快照（健康由卡在位/挂载/容量事实单源推导，旧 mounted/status 仅为投影）、容量缓存、原始扇区读、
驱动释放钩子；`USBX/App/ux_device_msc.c` 回调接线（Read→drms_msc_read、Write 恒 DATA PROTECT、
Status/Flush 未导出返回 NOT READY、最后 LBA=块数−1、块长恒 512、非法 LUN 拒绝）；
`test/test_storage_ownership.py` 10 项。全量 169/169；ARM 构建零警告（text 121136）。

**测试覆盖**：LOCAL+ABSENT 不阻断监测且无卡导出回落 LOCAL（不开放磁盘）；flush/close 失败交接回落且
不残留双重管理；导出→释放往返、真实扇区内容、导出期阻断记录入口；LBA 越界/溢出/零块/空缓冲拒绝；
导出期零写请求（审计 uninit 次数）；读超时槽不释放、缓冲由存储线程占用至归结、归结后数据有效；
cancel（IRQ 入口）撤就绪→RELEASING→LOCAL 收敛且代次递增；换卡重导出容量刷新；释放仅在在途读归结后
重挂载 FileX；监督者显式隔离（mark_quarantined）拒绝新请求且清理仍收敛回 LOCAL。

**决议（ledger）**：
- Ruling: 隔离（QUARANTINED）只能由监督者显式进入（`drms_msc_mark_quarantined`，T7 看门狗接入）——
  存储线程卡死在驱动内时本模块不可自观察；service 在隔离下继续收敛既有清理后回 LOCAL。
- Ruling: 读等待钩子（`drms_msc_set_wait_hook`）由集成方注入：生产=调度让出，测试=驱动 service 步进；
  USBX 线程永不直接触碰 SD。
- Ruling: 导出代次在"发布就绪"与"撤销就绪"两个方向都递增（MSC 设计 §退出导出）。
- Ruling: 导出容量取自挂载成功时的 FileX 媒体信息（`fx_media_total_sectors`），换卡/重挂载刷新；
  LUN 几何更新与 CDC/控制台命令（MSC EXPORT/RELEASE）接线归 T7。
- Ruling: USBX FIFO 双类配置与类注册失败不附着属板测/集成范围（T7/T8），本任务只接线回调语义。
- Ruling: `fx_media_driver_logical_sector` 为 FileX 真实字段名（fx_api.h），修正初版误用的 sector_start。

**结论**：软件验收通过（主机联合仿真）。MSC 实板枚举/复制/写拒绝等项未执行——板测单独标记（T8）。

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

### T5 执行记录（2026-11-08）

**交付物**：`Core/Inc/drms_user_config.h`（schema1 布局文档化于头注释：小端固定整数、IEEE754 binary64
显式编码、TLV 长度化字段、CRC-32/ISO-HDLC=zlib 参数、总长 ≤4096B、页尾提交四字）；`Core/Src/drms_user_config.c`
（编码/整体校验/A-B 页事务：apply 暂存、save 持久化、commit_baseline 配置+R0 原子提交、load 依赖检查）；
`Core/Src/drms_user_journal.c` 未建——页提交逻辑内聚于 user_config.c，Flash 后端独立为
`Core/Src/drms_user_backend.c`（对齐 drms_calibration_flash 模式，已入 Makefile+postgenerate 清单）；
`STM32U575xx_FLASH.ld` ROM 1008K→992K + USERDATA 16K 保留区；postgenerate 同步（ROM 恢复值 992、
USERDATA 分区检查、新增源文件）；`test/test_user_config.py` 9 项 + `test/test_user_journal.py` 4 项。
全量 191/191；ARM 构建零警告；map 核对最高 Flash 符号 0x0801D92C ≪ 0x080F8000（应用不越入用户区）。

**测试覆盖**：黄金向量（魔数/版本/长度/CRC/提交四字位置）；区间校验 12 类拒绝（零宽/倒序/重叠/乱序/
NaN/Inf/回差≥半宽/负回差/超16项/名称>48B/非法UTF8/截断UTF8）+ 16 项合法 + 空表合法（UNCONFIGURED）；
apply 版本门（STALE/整包拒绝不生效）；save 脏标志与同值 NO_CHANGE 不擦写；**掉电逐步注入**（begin/erase/
每个 program/提交前后共 ~40 个注入点，重启必得完整旧或完整新快照）；commit_baseline 原子性（失败旧 R0 保留、
版本不升）；NaN/零 R0 拒绝；校准代次变化 → 载入后 R0 失效（旧值保留可诊断）；未来 schema 页保留且
apply/save/commit 全部 UNSUPPORTED 不覆盖；撕裂提交标志回落另一页；A/B 轮换保持旧副本；四字粒度+尾部补白；
双页取最新。

**决议（ledger）**：
- Ruling: 页提交逻辑内聚于 `drms_user_config.c`（计划中的 `drms_user_journal.c` 并入），Flash 后端独立为
  `drms_user_backend.c`——与校准"journal 纯逻辑 + flash 后端"两文件结构等价，未建第二套后端。
- Ruling: schema1 内未知 TLV 类型按长度跳过但不做保留回写（真正的向前兼容边界是 schema 版本字节，
  载入即进 UNSUPPORTED 恢复态并拒绝普通写路径）；该边界已在头注释冻结。
- Ruling: 监测参数（rate/tau/warmup/confirm/stale）为可选段：未配置（rate=0）不编码，编码后载入校验
  一致——参数未配置即算法层 UNCONFIGURED（C6）。
- Ruling: R0 依赖检查在 load 内执行（当前校准代次由 `drms_user_config_set_calibration_generation`
  注入，T7 接线）；失效仅清 valid 标志，不删除旧值。
- Ruling: 事务接口为同步后端处理接口；CDC 线程不得直接调用（T7 由控制路径投递）。
- Ruling: 版本语义冻结——apply 成功 run_version+1；commit_baseline 成功再 +1（配置与 R0 一起发布）；
  失败一律不升版本；持久化版本只在页提交成功后跟随。

**结论**：软件验收通过（主机注入后端）。实板 Flash 擦写/掉电与 NMT ECC 行为未执行——随 T8 板测。

## T6 纯算法拆分与无效恢复

**新增：** `Core/Inc/drms_filter.h`、`Core/Src/drms_filter.c`、`Core/Inc/drms_classifier.h`、`Core/Src/drms_classifier.c`、`Core/Inc/drms_baseline.h`、`Core/Src/drms_baseline.c`、`test/test_monitor_pipeline.py`。
**保留/接入：** drms_measurement.h/c中的解码换算；drms_application.c仅协调。

**接口规则：** 严格实现设计C6的DRMS_MonitorInput/Config/Output与init/configure/step/tick接口；内部filter/classifier/baseline模块保持显式context。公共头文件在T1冻结，T6不得重新解释单位、端点或状态。调用无I/O、无RTOS、不分配堆。

- [ ] 首版filter明确采用流式一阶IIR：y += alpha*(x-y)，alpha由采样间隔和配置时间常数换算；首样本初始化y=x，时间常数0为旁路。配置另含连续有效建立时间，不以IIR理论完全收敛为有效条件。
- [ ] 区间采用有序不重叠表及显式端点；未覆盖值输出UNMAPPED。候选跨级直接选择目标区间；回差仅用于退出当前区间，阈值以R/R0单位表示。
- [ ] 回差严格执行C6的2h<区间宽度及空隙约束；跨越多个区间不逐级等待。确认时间0允许首次合格结果立即生效。
- [ ] 测试边界本身/两侧、上下方向、缺口、回差、跨级；使用合成阈值，不当客户正式参数。
- [ ] 测试持续确认只差一个样本时出现NaN/CRC故障/缺样/代次变化：计时归零，滤波失效；恢复需完整建立窗口后再确认。
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
- [ ] 将C2八种业务操作编码为唯一资源集合表，UPDATE自动展开全资源；测试8×8有序操作对及升级单独位被拒绝/展开。
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

### T2b 执行记录（2026-11-08）

**交付物**：`docs/design/2026-11-06-record-v2-format.md`（规格冻结稿：chunk 帧/HEADER/DATA/END 字节布局、
CRC-32/ISO-HDLC 参数、识别规则、错误处理表、黄金文件说明、与 v1 关系）；`drms_log_codec.{h,c}` v2 pack
函数（header/data/end，显式小端编码 + 每块载荷 CRC，未知末边界拒绝伪精确 end）；
`tools/de_drms_log.py` LogReaderV2（按 DRMS 魔数/chunk 流分派 v1/v2，完整错误处理表实现）；
`test/test_log_v2_codec.py` 8 项（含逐字节截断 ~209 例、逐字节位翻转 ×2 位 ~418 例）。
全量 199/199；ARM 构建零警告。

**黄金文件**：独立手工 Python 编码（hand_header/hand_data/hand_end）与 C 编码器输出**逐字节一致**，
双端可解码；含配置快照（T5 schema1 真实编码）往返、空记录合法、INCOMPLETE 汇总语义。

**错误处理覆盖**：每字节截断（不完整/非法，绝不报告成功）；位翻转全部被 CRC/结构检查捕获；
重复 END / END 前缺 HEADER / 未知块类型 / DATA 非 16 倍数 / 超长块 / END 后尾随字节 / 未知末边界
携带伪精确 end（C 拒绝编码 + 解码拒绝）→ 全部非法；v1 夹具仍按旧规则解码。

**决议（ledger）**：
- Ruling: v2 文件为纯 chunk 流、无文件级魔数/CRC（识别 = 首块 type=1）；v1 以 `DRMS` 魔数识别。
  规格文档已同步该识别规则。
- Ruling: v2 **写入侧切换**（drms_logging 写路径 + 会话 END 提供者）归 T7——C4 要求的格式/黄金文件/
  双端编解码门禁本任务已齐，写路径切换需要 T2a 的会话 END 描述符与存储流整合，避免在 T2b 造半套
  无 END 来源的写入器。
- Ruling: DATA 块批量上限 256 帧（u16 长度约束下的实现边界），不扩大 16B 帧。

**结论**：软件验收通过（主机双端交叉验证）。真实存储写入（v2 落盘+MSC 导出取回）随 T7/T8。

### T6补充：独立tick与分类转换表

- [ ] 按C3建立无样本tick测试：119999/120000us边界、无首帧、旧积压帧、时基倒退、RTC变化。
- [ ] 按C6转换表逐行测试，包括离开confirmed后PENDING不继续输出旧正常等级、空隙UNMAPPED、候选返回旧区间重新确认。
- [ ] 相同采样时间序列按1帧/批、多帧/批输入输出一致；tick只更新实时展示新鲜度，不修改历史算法状态，也不能完成等级确认。
- [ ] IIR alpha在配置变化时计算或缓存，不在每帧无必要重复exp；原始记录不受滤波影响。

### T7/T8补充：可观测上界与最终交付

- [ ] 处理任务有独立10ms新鲜度检查唤醒，不依赖ADC中断继续存在；记录最大调度延迟及过期可见上界。
- [ ] C1–C6、R1–R8全部有测试对应；接口清单、v2格式、资源矩阵、线程预算必须与代码一致。
- [ ] 最终报告分列：设计契约完成、软件门禁通过、实板门禁通过、客户参数定标。没有证据的一列不得标完成。

闭环映射：C1→T2a；C2→T1；C3→T6/T7；C4→T2b；C5→T1；C6→T6。
预算门禁是项目工程策略，真实容量和水位证据来自T0/T7/T8，不混称芯片要求。


## 第三次复检修订的必测项（2026-11-06）

本节直接落实C1/C3修订，不新增代码实施范围。

- [ ] T0/T1：选择并记录单调微秒时钟后端及其精度/回绕规则，固定DRMS_TimeAnchor类型；用合成时间验证商余换算、长时间运行及低32位序号回绕。
- [ ] T2a：START和STOP请求前消费者均进入屏障；延迟边界回复期间生产者继续，断言消费者不越过最终E，E后帧不进入旧记录。边界失败/超时/原始环满返回INCOMPLETE且迟到回复无效。
- [ ] T2b：文件头包含代次时间锚点、采样率和NOMINAL时间质量；缺锚点或代次不匹配拒绝伪正常解码。正常时钟频差只作诊断；未知丢样导致失败结束，不篡改旧时间轴。
- [ ] T6：相同样本流插入不同tick时序，断言历史算法输出一致；STALE覆盖不清滤波/候选。真实质量故障与采样缺口仍重置算法。
- [ ] T6/T7：step后tick再原子发布；积压旧帧不能短暂发布正常灯状态。仅当前新鲜有效结果才解除覆盖。
- [ ] T7/T8：测量并报告名义时间精度，正常频差不得触发记录终止。新鲜度严格采用C3实测时间侧表，不使用名义时间减now；无实板证据时明确时间精度未验收。

自检一致性：资源表6类集合、展开8种操作、测试8×8；记录ready/stop接口均用DRMS_CaptureBoundary；
算法state与展示fresh分离；16B帧容量不变，新增时间信息为有界锚点和65×32B原始环侧表，总计另计RAM，不改变帧大小。


## 第四次复检收敛：直接执行清单

以下接口/测试在对应任务中实施，禁止保留被替代的“名义时间偏差越限即停录”实现。

### 公共接口补齐（T1）

- [ ] DRMS_CaptureBoundary增加capture_lost_total/unknown_loss_epoch（uint64），与sample_next/raw_next一致发布。
- [ ] DRMS_End增加end_known和last_confirmed_position，以及分阶段损失字段；未知末边界不写伪精确end。
- [ ] DRMS_MonitorInput/Output增加capture_lower_bound_us；tick只用此字段计算实时新鲜度，capture_us只供算法。
- [ ] 新建 `Core/Inc/drms_capture_time.h`、`Core/Src/drms_capture_time.c`，侧表固定65×32B，静态断言大小；新增 `test/test_capture_time.py` 编译真实模块。
- [ ] 接口：`DRMS_Result drms_capture_time_publish(uint64_t raw_ticket, uint64_t consumed_raw_next, uint32_t acquisition_generation, uint64_t drdy_mono_us);`
  仅生产者在块首帧发布前调用，consumed_raw_next取原始环acquire读取的消费水位；以及`DRMS_Result drms_capture_time_lookup(uint64_t raw_ticket, uint32_t acquisition_generation, uint64_t *lower_bound_us);`
  仅消费者在释放原始环槽前调用。侧表覆盖资格必须使用原始环已消费水位，publish前检查，不得仅依赖valid标志。

### 启停屏障和损失隔离（T2a/T2b）

- [ ] 统一START_BOUNDARY_WAIT/STOP_BOUNDARY_WAIT，均不pop原始环；定时和取消事件仍处理。
- [ ] B/E回复都核对token与代次；超时后旧回复只能清理，不重新开放记录入口。
- [ ] 监测期capture_lost_total=7，B=7，E=7：本次capture_lost=0；E后增加到9仍不修改本次END。
- [ ] B=7，E=9：本次capture_lost=2；CRC坏帧增加quality_bad，不重复增加capture_lost。
- [ ] 第一帧缺失不得移动B伪装成功；B/E相等且无损失才EMPTY，有采样但全丢失为INCOMPLETE。
- [ ] E无法取得：end_known=false、LOSS_UNKNOWN、最后可确认位置；文件解码明确不完整。
- [ ] v2头/尾包含对应锚点、分阶段损失与未知边界字段，黄金文件覆盖上述各场景。

### 时间与实时显示（T6/T7/T8）

- [ ] 测试侧表槽0在第65块到达时仍按真实消费水位判断是否可覆盖；4096帧滑动窗口跨65块不串时间。
- [ ] 消费者复制时间后才释放帧槽；故意交错生产/消费验证读不到新块替换的旧时间。
- [ ] 录入DRDY实测时间，下界>=now的两种情况分别检查：相等允许age=0，严格领先报告时基故障。
- [ ] 注入长期正常频差，让名义时间领先/落后数秒：记录保持正常，新鲜度按实测下界判断。
- [ ] 陈旧数据配最新处理时刻仍为STALE；实际停止DRDY后仅tick也失效。
- [ ] 配置校验最小stale_timeout_us按C3两个块周期公式；侧表2080B及在途DRDY时间槽纳入map预算，不放进原始/记录帧。

通过标准：启停无消费者越界、损失只归属本次区间、无无符号时间下溢、正常频差不误终止试验；
测试记录必须列出上述反例的断言与执行结果，不以静态文档检查替代。
