#ifndef DRMS_ARCHITECTURE_CONTRACT_H
#define DRMS_ARCHITECTURE_CONTRACT_H
/* 公共契约唯一位置（C5）。仅标准 C 类型；禁止包含 HAL/RTOS 头。
 * 其他模块只引用本文件，不得复制类型。字段单位与调用上下文在每处定义旁注明。
 * 数值冻结后不得改动；线格式/文件/Flash 编码在各自模块显式编解码，不直接序列化本结构。
 * 64-bit 字段在 M33 上不假设天然原子：跨上下文一致读取必须走各模块 get_snapshot
 * 的短临界区或序列协议。 */
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* ------------------------------------------------------------------ */
/* 结果码（C5/T1）。文件与协议编码使用这些数值，冻结后不复用。 */
/* ------------------------------------------------------------------ */
typedef enum {
  DRMS_OK = 0,            /* 同步成功 */
  DRMS_ACCEPTED = 1,      /* 已受理（租约取得/命令入队/工作已投递）；最终结果另行报告 */
  DRMS_BUSY = 2,          /* 资源被占/队列满/转换中 */
  DRMS_INVALID = 3,       /* 参数非法/无此操作/匹配不到目标 */
  DRMS_STALE = 4,         /* 代次/会话已过期；仅允许清理语义 */
  DRMS_NO_CHANGE = 5,     /* 同值提交，未执行擦写 */
  DRMS_IO_ERROR = 6,      /* 后端 I/O / 数据通路故障 */
  DRMS_TIMEOUT = 7,       /* 有界等待超时（不代表资源已释放） */
  DRMS_CANCELLED = 8,     /* 被停止/取消路径终止 */
  DRMS_INCOMPLETE = 9,    /* 明确的不完整结果（如记录缺尾、丢样） */
  DRMS_QUARANTINED = 10,  /* 无法证明静止，资源被隔离 */
  DRMS_UNSUPPORTED = 11,  /* 后端/能力不支持 */
  DRMS_EMPTY = 12         /* 合法但为空（如零样本记录） */
} DRMS_Result;

/* ------------------------------------------------------------------ */
/* 资源位（C2）。全部为独占租约；UPDATE_EXCLUSIVE 申请时自动展开为全部资源。 */
/* ------------------------------------------------------------------ */
#define DRMS_RES_ACQUISITION_CONFIG (1u << 0) /* 采集/算法配置与解释快照 */
#define DRMS_RES_RECORD_SESSION     (1u << 1) /* 记录会话（STARTING..收尾） */
#define DRMS_RES_TF_ACCESS          (1u << 2) /* TF/SD 介质（含导出交接；不要求卡在位） */
#define DRMS_RES_FLASH_MAINTENANCE  (1u << 3) /* 内部 Flash 擦写维护 */
#define DRMS_RES_UPDATE_EXCLUSIVE   (1u << 4) /* 升级独占（展开为全部资源） */
#define DRMS_RES_ALL                (DRMS_RES_ACQUISITION_CONFIG | DRMS_RES_RECORD_SESSION | \
                                     DRMS_RES_TF_ACCESS | DRMS_RES_FLASH_MAINTENANCE | \
                                     DRMS_RES_UPDATE_EXCLUSIVE)

/* ------------------------------------------------------------------ */
/* 业务操作（C2：六类资源集合展开为 8 种）。 */
/* ------------------------------------------------------------------ */
typedef enum {
  DRMS_OP_NONE = 0,
  DRMS_OP_RECORD = 1,        /* ACQ + RECORD_SESSION + TF_ACCESS */
  DRMS_OP_MSC_EXPORT = 2,    /* TF_ACCESS */
  DRMS_OP_FILE_DOWNLOAD = 3, /* TF_ACCESS */
  DRMS_OP_CONFIG_APPLY = 4,  /* ACQ + FLASH_MAINTENANCE */
  DRMS_OP_BASELINE_R0 = 5,   /* ACQ + TF_ACCESS + FLASH_MAINTENANCE */
  DRMS_OP_CALIBRATE = 6,     /* ACQ + TF_ACCESS + FLASH_MAINTENANCE */
  DRMS_OP_CONFIG_SAVE = 7,   /* ACQ + TF_ACCESS + FLASH_MAINTENANCE */
  DRMS_OP_UPDATE = 8,        /* 全部资源（UPDATE_EXCLUSIVE 展开） */
  DRMS_OP_MSC_RELEASE = 9,   /* 归还已持有的 TF 租约；本操作不预占 TF */
  DRMS_OP_RESUME_MONITOR = 10, /* 仅恢复监测；停止屏障期间允许受理 */
  DRMS_OP_FILE_LIST = 11, /* temporary TF lease for a bounded directory scan */
  DRMS_OP_SET_UTC = 12 /* RTC only; monotonic recording deadlines are unaffected */
} DRMS_Operation;

/* 请求来源（命令信封）。 */
typedef enum {
  DRMS_SOURCE_NONE = 0,
  DRMS_SOURCE_BUTTON = 1,
  DRMS_SOURCE_CONSOLE = 2,
  DRMS_SOURCE_CDC = 3
} DRMS_RequestSource;

/* 命令公共信封：任意任务上下文经控制 submit 投递；大载荷只用固定池描述符，
 * 裸指针生命周期由所有者保证到 dispatch 复制完成。 */
typedef struct {
  uint32_t source;       /* DRMS_RequestSource */
  uint32_t session;      /* 通信会话标识；0 = 本机 */
  uint64_t request_id;   /* 会话内请求编号（去重/关联）；内部编号与它分离 */
  DRMS_Operation operation;
  uint32_t value;        /* 整型参数（如采样率 Hz、时长），按 operation 解释 */
  double number;         /* 浮点参数（如参考电阻 Ω），按 operation 解释 */
  const void *payload;   /* 固定池描述符指针；可为 NULL */
  uint32_t payload_length;
  uint64_t expected_version; /* 配置写入版本；CDC RECORD 时为时长覆盖存在标志（0/1） */
  uint64_t record_id; /* 由控制裁决器在 RECORD 入队时分配，调用者不得指定 */
} DRMS_ControlRequest;

/* ------------------------------------------------------------------ */
/* 代次与位置（C1/C5）。控制、采集、记录代次为不同命名字段，禁止共用。 */
/* ------------------------------------------------------------------ */
typedef struct {
  uint64_t operation_id; /* 运行期不复用；复位后由 boot_id 区分 */
  uint32_t generation;   /* 控制代次 */
} DRMS_Token;

/* 流位置：index 是唯一采集生产端发布的 64-bit 流位置，不依赖记录帧布局；
 * generation 是该位置所属的采集代次（与控制代次、记录会话标识分立命名）。 */
typedef struct {
  uint32_t generation;
  uint64_t index;
} DRMS_Position;

/* 一致捕获边界（C1）：由采集模块在短临界区一次发布；等待发生在临界区外。 */
typedef struct {
  uint32_t acquisition_generation;
  uint64_t sample_next;         /* 下一个观察到的 DRDY 的 sample_seq */
  uint64_t raw_next;            /* 下一个原始环发布位置 raw_ticket */
  uint64_t capture_lost_total;  /* 累计未发布到原始环的采样（每样最多计一次） */
  uint64_t unknown_loss_epoch;  /* 无法证明连续性时递增的纪元号 */
} DRMS_CaptureBoundary;

/* 记录结束描述符（C1）：每次记录独占完成槽；存储确认前不得被下一次覆盖。
 * lost_count 仅兼容诊断；跨阶段损失不得相加成"精确总数"。 */
typedef struct {
  DRMS_Token token;
  uint64_t record_id;
  uint64_t ring_end;   /* 记录环独立 log_ticket 边界，不是 E.raw_next */
  uint64_t lost_count; /* 兼容诊断 */
  DRMS_Position first;
  DRMS_Position end_exclusive;          /* end_known=false 时不写伪精确值 */
  DRMS_Position last_confirmed_position;
  bool end_known;
  uint64_t capture_lost;  /* 本次 [B,E) 内未发布采样 */
  uint64_t log_dropped;   /* 记录环按 record_id 独立累计 */
  uint64_t quality_bad;   /* CRC 坏帧（已发布，独立计数） */
  bool unknown_loss;      /* B/E unknown_loss_epoch 不同 → LOSS_UNKNOWN */
  bool storage_error;     /* 写卡/收尾失败 */
  DRMS_Result reason;
} DRMS_End;

/* 介质双轴（R5）：所有权与健康分离；外部旧 ERROR 为投影值，不作内部所有权。 */
typedef enum {
  DRMS_HEALTH_ABSENT = 0,
  DRMS_HEALTH_READY = 1,
  DRMS_HEALTH_FAULT = 2
} DRMS_Health;

typedef enum {
  DRMS_OWNER_LOCAL = 0,
  DRMS_OWNER_EXPORTING = 1,
  DRMS_OWNER_EXPORTED = 2,
  DRMS_OWNER_RELEASING = 3,
  DRMS_OWNER_QUARANTINED = 4
} DRMS_Owner;

/* ------------------------------------------------------------------ */
/* 时间锚点与名义时间（C3）。 */
/* ------------------------------------------------------------------ */
typedef struct {
  uint32_t acquisition_generation;
  uint32_t rate_hz;      /* Hz */
  uint64_t sample_seq0;  /* 该代第一个观察到的 DRDY 的 sample_seq */
  uint64_t mono_us0;     /* 该 DRDY 时刻的单调时钟读数（µs） */
} DRMS_TimeAnchor;

/* 单调微秒时钟后端（T0/T1 决议）：TIM2 @1 MHz、32 位计数 + 单写者 64 位扩展；
 * 回绕规则：唯一所有者上下文在计数回绕时扩展高位，ISR 双读稳定取值。
 * 后端故障不得通过改写旧时间修正；实板精度/回绕验收在 T7/T8。 */
/* 名义算法时间 = mono_us0 + floor((sample_seq-sample_seq0)*1e6/rate_hz)，
 * 用商余分解防溢出；仅在同代 sample_seq >= sample_seq0 时有效。 */

/* ------------------------------------------------------------------ */
/* 监测算法公共契约（C6）。单位：ohms/r0 为 Ω；区间 lo/hi/h 为 R/R0 比值
 * （无量纲）；时间字段为 µs。capture_us 是名义算法时间，只供算法；
 * capture_lower_bound_us 是 MCU 实测时间下界，只供实时新鲜度，两者不得相减。 */
/* ------------------------------------------------------------------ */
typedef enum {
  DRMS_MONITOR_INVALID = 0,
  DRMS_MONITOR_WARMUP = 1,
  DRMS_MONITOR_UNCONFIGURED = 2,
  DRMS_MONITOR_UNMAPPED = 3,
  DRMS_MONITOR_PENDING = 4,
  DRMS_MONITOR_CONFIRMED = 5
} DRMS_MonitorState;

/* Output.reason 位集合（无效/过渡原因）。 */
#define DRMS_REASON_QUALITY_BAD    (1u << 0) /* CRC/格式/ADC 故障帧 */
#define DRMS_REASON_SAMPLE_GAP     (1u << 1) /* 采样缺口/代次变化/依赖不适用 */
#define DRMS_REASON_NOT_FINITE     (1u << 2) /* NaN/Inf/非法分母 */
#define DRMS_REASON_NO_BASELINE    (1u << 3) /* 无有效 R0 */
#define DRMS_REASON_STALE          (1u << 4) /* 实时展示过期覆盖 */
#define DRMS_REASON_WARMUP         (1u << 5) /* 滤波未建立 */
#define DRMS_REASON_UNCONFIGURED   (1u << 6) /* 未配置区间表 */

/* Output.freshness_reason 位集合（展示新鲜度）。 */
#define DRMS_FRESH_NO_SAMPLE       (1u << 0)
#define DRMS_FRESH_TIMEBASE_FAULT  (1u << 1)
#define DRMS_FRESH_STALE           (1u << 2)

typedef struct {
  double lo;               /* 含左端点 */
  double hi;               /* 开右端点；最后一项允许闭合上端 */
  double h;                /* 退出回差，R/R0 单位；约束 2h < hi-lo 且两侧 h 之和 < 空隙 */
  uint16_t id;
  uint8_t level;
  bool last_upper_closed;
} DRMS_MonitorInterval;

#define DRMS_MONITOR_INTERVALS_MAX 16

typedef struct {
  uint32_t rate_hz;        /* Hz */
  uint64_t tau_us;         /* 一阶 IIR 时间常数；0 = 旁路 */
  uint64_t warmup_us;      /* 连续有效建立时间 */
  uint64_t confirm_us;     /* 区间确认时间 */
  uint64_t stale_timeout_us; /* 展示新鲜度超时；下限见 C3 配置校验 */
  double r0;               /* Ω */
  bool baseline_valid;
  uint8_t interval_count;
  DRMS_MonitorInterval intervals[DRMS_MONITOR_INTERVALS_MAX];
} DRMS_MonitorConfig;

typedef struct {
  double ohms;             /* Ω */
  uint64_t capture_us;             /* 名义算法时间（锚点重建） */
  uint64_t capture_lower_bound_us; /* MCU 实测捕获时间下界 */
  uint64_t sample_seq;
  uint32_t acquisition_generation;
  uint32_t quality_flags;  /* 解码级质量位集合（模块内定义） */
  uint64_t config_version;
  uint64_t baseline_version;
} DRMS_MonitorInput;

typedef struct {
  DRMS_MonitorState state;
  uint32_t reason;               /* DRMS_REASON_* 位集合 */
  uint64_t capture_lower_bound_us; /* 当前展示所用时间下界 */
  bool fresh;                    /* 实时展示新鲜标志（独立于算法状态） */
  uint32_t freshness_reason;     /* DRMS_FRESH_* 位集合 */
  int16_t observed;              /* 查表结果；-1 = 无 */
  int16_t candidate;             /* -1 = 无 */
  int16_t confirmed;             /* -1 = 无 */
  double ratio;                  /* R/R0 */
  bool hysteresis_hold;
  uint64_t sample_seq;
  uint32_t acquisition_generation;
  uint64_t config_version;
  uint64_t baseline_version;
} DRMS_MonitorOutput;

/* 算法上下文：仅由算法持有，init 后不共享可写；内部字段在 drms_monitor.c
 * 定义，调用方不得直接读取。step/tick 由处理线程唯一调用，发布前 step 后
 * tick 并一致复制输出。分配：调用方提供 DRMS_MONITOR_CONTEXT_BYTES 的
 * 对齐字节区并以 (DRMS_MonitorContext *)cast 传入。 */
#define DRMS_MONITOR_CONTEXT_BYTES 4096u
typedef struct DRMS_MonitorContext DRMS_MonitorContext;

/* 公共算法接口（T6 实现；公共头在 T1 冻结，T6 不得改变字段语义）。
 * 无 I/O、无 RTOS 调用、不分配堆。 */
void drms_monitor_init(DRMS_MonitorContext *ctx);
DRMS_Result drms_monitor_configure(DRMS_MonitorContext *ctx, const DRMS_MonitorConfig *cfg);
void drms_monitor_step(DRMS_MonitorContext *ctx, const DRMS_MonitorInput *in, DRMS_MonitorOutput *out);
void drms_monitor_tick(DRMS_MonitorContext *ctx, uint64_t now_us, DRMS_MonitorOutput *out);

#endif /* DRMS_ARCHITECTURE_CONTRACT_H */
