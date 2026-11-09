#ifndef DRMS_USER_CONFIG_H
#define DRMS_USER_CONFIG_H
/* 用户配置/R0 事务（T5/R3）。用户区 = Flash 末端 A/B 两页（0x080F8000 起，
 * 各 8 KiB），整页快照提交：擦目标→写内容→读回校验→最后写提交标志→校验。
 * 任意中间掉电恢复得到完整旧快照或完整新快照。编码 schema1 见本文件注释，
 * 不依赖 C struct 布局；禁止 memcpy 结构体落盘。
 * 业务调用是后端处理接口（控制/维护上下文）；CDC 线程不得直接擦写。 */
#include "drms_architecture_contract.h"

#define DRMS_USER_BODY_MAX 4096u /* 快照总长上限（含头与 CRC，字节） */
#define DRMS_USER_INTERVALS_MAX 16u
#define DRMS_USER_NAME_MAX 48u /* 每项显示名称 UTF-8 字节上限 */
#define DRMS_USER_PAGE_SIZE 8192u

/* schema1 布局（小端；CRC-32/ISO-HDLC=zlib 参数，见 drms_crc32）：
 *   0  "DRMSUC01"            8B  魔数+schema 版本
 *   8  uint32 body_len       含本头与尾部 CRC 的总长
 *   12 uint64 config_version 提交序号（单调）
 *   20 uint64 calibration_version  R0 依赖的校准代次
 *   28 uint8 flags           bit0 = R0 有效
 *   29 uint8 reserved[3]
 *   32 double r0             IEEE754 binary64，Ω
 *   40 TLV: uint16 type, uint16 len, value[len]
 *        type1 区间表: uint16 count; count×{u16 id; u8 level; u8 flags(bit0=末项闭合上端);
 *                     f64 lo; f64 hi; f64 h; u8 name_len; name[name_len]}
 *        type2 监测参数: u32 rate_hz; u64 tau_us; u64 warmup_us; u64 confirm_us; u64 stale_timeout_us
 *        type3 别名: UTF-8 ≤64B
 *        type 0xD701 基线质量条件: u32 min_count; u64 min_duration_us; f64 max_cv
 *        未知 type：整段保留（保存时原样回写），不解释
 *   body_len-4: uint32 crc32（覆盖 [0, body_len-4)）
 * 页尾提交四字（页末 16B）: "UCMT" u32, config_version 低 32 位 u32, body_crc u32, 保留 u32 */

void drms_user_config_init(void);

/* 注入当前仪器校准代次（load 的 R0 依赖检查用；T7 接线）。 */
void drms_user_config_set_calibration_generation(uint64_t generation);

/* 开机恢复：读取 A/B 两页有效提交，取 config_version 最新者；未知 schema
 * 保留原始页并进入恢复状态（普通保存拒绝覆盖）；两页均无效 → 出厂默认。 */
void drms_user_config_load(void);

/* 校验并暂存运行配置（整体校验；任何非法输入整包拒绝，不部分生效）。
 * expected_version 必须等于当前运行版本，否则 STALE。成功后运行版本 +1、
 * 置未保存标志；持久化由 save/commit_baseline 完成。 */
DRMS_Result drms_user_config_apply(const uint8_t *encoded, size_t length,
                                   uint64_t expected_version);

/* 暂存运行配置持久化（expected_version 须等于当前运行版本）。
 * 同值已持久化 → NO_CHANGE 不擦写；写失败保留旧页内容与未保存标志。 */
DRMS_Result drms_user_config_save(uint64_t expected_version);

/* 建立 R0：冻结当前运行配置并与新 R0 一起原子提交；成功才整体发布
 * （运行版本 +1 且持久化版本同步）；失败保留旧 R0 与未保存状态。
 * r0 须有限且 >0；calibration_version 写入 R0 依赖标识。 */
DRMS_Result drms_user_config_commit_baseline(double r0, uint64_t expected_version,
                                             uint64_t calibration_version);

/* 状态查询（任意上下文只读）。 */
uint64_t drms_user_config_run_version(void);
uint64_t drms_user_config_persisted_version(void);
uint32_t drms_user_config_dirty(void);
uint32_t drms_user_config_r0_valid(void);
double drms_user_config_r0(void);
uint64_t drms_user_config_r0_calibration_version(void);
uint32_t drms_user_config_unsupported_schema(void); /* 未知 schema 恢复状态 */
typedef struct {
  uint32_t min_count;
  uint64_t min_duration_us;
  double max_cv;
} DRMS_BaselinePolicy;
/* Returns 0 when no policy is configured. A staged policy follows run_version. */
uint32_t drms_user_config_get_baseline_policy(DRMS_BaselinePolicy *out);
/* Sampling rate of the snapshot that baseline commit would persist. */
uint32_t drms_user_config_baseline_rate(void);
/* Copy supported persisted monitoring settings. Returns 0 if no complete,
 * locally supported set is available; caller may retain safe defaults. */
uint32_t drms_user_config_get_monitor(DRMS_MonitorConfig *out);
/* Configuration owner copies the committed running snapshot into caller storage.
 * Returns encoded length or zero if no compatible configuration or insufficient space. */
uint32_t drms_user_config_export(uint8_t *out, uint32_t capacity);

/* 运行配置快照（已校验）；返回 1 = 有已应用配置。 */
uint32_t drms_user_config_get_intervals(uint16_t *count,
                                        double *lo, double *hi, double *h,
                                        uint16_t *ids, uint8_t *levels);

#endif /* DRMS_USER_CONFIG_H */
