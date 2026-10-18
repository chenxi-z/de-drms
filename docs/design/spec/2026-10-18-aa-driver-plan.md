# 抗混叠与采集驱动子系统实现计划（Round 5）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 按规格文档 v3 完成抗混叠采集子系统的三案参数求解、LTspice 十维评分复测、图纸产出，为用户定档决策提供完整数据包。

**Architecture:** 理论引擎（模态分解 + MNA，已有 `opt_engine.py`）在新约束下求解三案参数 → LTspice 批处理复测（V1–V9）→ 十维评分表 + 图纸。理论预测与 LTspice 实测双向交叉验证，偏差点亮即停。

**Tech Stack:** Python 3 + numpy/scipy（优化与解析）、LTspice 24.1 命令行批处理（`-b -ascii`）、cairosvg（图纸渲染）、`tools/svg_schematic_check.py`（图纸门禁）。

**Spec:** `docs/design/spec/2026-10-18-aa-driver-design.md`（v3，随本计划同行；执行者两者都要读）

## Global Constraints

- 抗混叠锚点 **fMOD = 4.096 MHz**（M5 核实后以此为准），MCLK = 16.384 MHz
- 扫频上限 16 kHz（每周期 8 点 @128 kSPS）；精密区 ≤8 kHz；**测相位**（D10 正式维度）
- 模拟 fc 目标区间 50~80 kHz；四线统一全配（含 AIN1N）
- 跟随器只当缓冲不进反馈环路（OPA388 GBW=10 MHz 判死有源拓扑）
- 电容必须 C0G/NP0 或薄膜；单电容 ≤100 nF（>47 nF 须核 SRF>fMOD）
- 每线串联电阻总和 ≤5 kΩ；LSB = 291 nV（2×2.442/2²⁴）
- 标准测试条件表（共模 1V AC + 2.0V DC 偏置等，§5.1a 后）执行者不得改动
- **手册值纪律**：M1–M7 不查手册不得开跑；凭记忆填值 = 返工
- 文本 LF；仿真产物（.raw/.op.raw/.net）不入库；图纸 SVG 必须过门禁
- **锁屏风险**：LTspice `-b` 对 `.net` 可直接跑；`.asc` 需要 GUI 会话解锁（历史教训：锁屏时 .asc 批处理挂死）。所有批处理一律走 `.net`

---

### Task 1: 手册核实 M1–M7 + 更新规格锚点

**Files:**
- Modify: `docs/design/spec/2026-10-18-aa-driver-design.md`（§5.3 表填入实测值）
- Create: `hardware/sim/aaf/r5_datasheet_facts.md`

**Interfaces:**
- Produces: `FACTS` 字典（后续所有任务的脚本 import 此文件的数据）——
  `FMOD_HZ, MCLK_HZ, SINC3_F3DB_HZ, ADC_CS_PF, ADC_RSW_OHM, ADC_SW_DUTY, OPA388_AOL_4M_DB, OPA388_ZOUT_CURVE_REF`

- [ ] **Step 1: 查 ADS131A02 手册（SBAS890）填 M1/M2/M3/M5/M6**

  需查：sinc³ −3 dB 频率 @OSR=32（滤波器响应图）；输入采样电容（输入结构节）；输入电流/阻抗；fMOD = fCLKIN/4 还是 /8；开关等效电阻与时序。手册在 Obsidian `20-硬件工程/datasheets/`（若缺，从 TI 官网下载放 Obsidian，**不入库**）。

- [ ] **Step 2: 查 OPA388 手册（SBOS777）填 M4/M7**

  AOL @4 MHz（验证 GBW=10 MHz 近似）；闭环输出阻抗随频率曲线（记下参考图号）。

- [ ] **Step 3: 写 `r5_datasheet_facts.md`**

  格式：每项一行 = 值 + 手册页码/图号 + 与规格推算值的偏差（如有）。同时把值填回规格文档 §5.3 表（标注"已核实"）。

- [ ] **Step 4: 冲突仲裁检查**

  若 fMOD ≠ 4.096 MHz 或 sinc³ −3 dB 与推算偏差 >20%，**停下报告用户**（阈值可能要改）；否则继续。

- [ ] **Step 5: Commit**

```bash
git add docs/design/spec/2026-10-18-aa-driver-design.md hardware/sim/aaf/r5_datasheet_facts.md
git commit -m "docs(sim): M1-M7手册核实值回填规格锚点"
```

---

### Task 2: 优化引擎升级（opt_round5.py）

**Files:**
- Create: `hardware/sim/aaf/opt_round5.py`
- Modify: `hardware/sim/aaf/opt_engine.py`（仅在交叉验证发现 bug 时）
- Test: `hardware/sim/aaf/test_opt_round5.py`

**Interfaces:**
- Consumes: Task 1 的 `FACTS`；`opt_engine.ladder_matrices(stages, mode, tol_r, tol_c)`、`H()`、`settle_time()`（现有签名不变）
- Produces: `solve_candidate(n_stages: int, seed: int) -> dict`，返回 `{"stages": [(R_ohm, C_gnd_F, C_diff_F), ...], "pred": {"A_dm": dB, "A_cm": dB, "A_mclk": dB, "dG_16k": dB, "t_settle_wc_s": s, "group_delay_flat_s": s}}`

- [ ] **Step 1: 写失败测试（理论引擎自洽性）**

```python
# test_opt_round5.py
from opt_engine import ladder_matrices, H, settle_time
from opt_round5 import solve_candidate

def test_two_stage_solvable():
    r = solve_candidate(2, seed=0)
    assert len(r["stages"]) == 2
    # 通带平坦度必须达标（这是新约束下最容易崩的维度）
    assert r["pred"]["dG_16k"] <= 0.5

def test_engine_regression():
    # 旧参数回放：FIN1 二级在新引擎下预测值应与旧战役一致（±0.5 dB）
    from opt_engine import H
    h = H([(330, 47e-9, 47e-9), (2700, 6.8e-9, 5.6e-9)], mode="dm")
    import math
    assert abs(20*math.log10(abs(h(4.096e6))) - (-123.5)) < 0.5
```

- [ ] **Step 2: 跑测试确认失败**（`solve_candidate` 不存在）

- [ ] **Step 3: 实现 opt_round5.py**

  Nelder-Mead 多起点（沿用 opt_round4 框架），目标函数 = min(D1..D10) 的**理论预测版**（D6 噪声/D9 kickback 理论不可测，用代理：D6_proxy = 末级 R 约翰逊噪声积分；D9_proxy = 末级 τ 与 122 ns 之比）。硬约束：fc∈[50k,80k]（由 dG_16k≤0.5 dB 反推）、rsum≤5k、C≤100nF。
  **单位纪律**：`settle_time()` 返回秒，与 µs 预算比较前必须 `*1e6`（前战役踩过的坑）。

- [ ] **Step 4: 测试通过 + 三案求解**

  `solve_candidate(2)`, `(3)`, `(4)` 各跑多起点，打印帕累托前沿。

- [ ] **Step 5: Commit**

```bash
git add hardware/sim/aaf/opt_round5.py hardware/sim/aaf/test_opt_round5.py
git commit -m "feat(sim): round5优化引擎——新fc约束+十维理论预测"
```

---

### Task 3: E 系列取整 + 三案参数冻结

**Files:**
- Create: `hardware/sim/aaf/snap_round5.py`
- Create: `hardware/sim/aaf/r5_candidates.json`

**Interfaces:**
- Consumes: Task 2 `solve_candidate()`
- Produces: `r5_candidates.json` —— `{"A": {"stages": [...], "pred": {...}}, "B": {...}, "C": {...}}`（E24 电阻/E12 电容取整后，邻域枚举重评分后的冻结值）

- [ ] **Step 1: 写 snap_round5.py**（沿用 snap_round4 逻辑：E24/E12 取整 + 邻域 ±1 档枚举 + 理论重评分）

- [ ] **Step 2: 运行并生成 r5_candidates.json**，打印三案取整前后的理论评分对比（取整损失 >5% 的维度标红）

- [ ] **Step 3: 人工检查**：任一维度取整后跌破及格线 → 该档方案标记"取整后不及格"，报告用户（可能需要降档诉求或放宽约束）

- [ ] **Step 4: Commit**

```bash
git add hardware/sim/aaf/snap_round5.py hardware/sim/aaf/r5_candidates.json
git commit -m "feat(sim): 三案E系列取整与参数冻结"
```

---

### Task 4: LTspice 网表生成器（.net 直出）

**Files:**
- Create: `hardware/sim/aaf/gen_netlists_r5.py`
- Create: `hardware/sim/aaf/r5_{A,B,C}_{v1..v9}.net`（生成物，不入库——`.net` 已 gitignore；保留生成脚本即可复现）

**Interfaces:**
- Consumes: `r5_candidates.json`
- Produces: 九个仿真类型的网表模板函数 `gen_v1(cand)`, `gen_v2(cand)`, ... `gen_v9(cand)`，每个返回网表字符串

- [ ] **Step 1: 实现网表模板**

  关键拓扑（单通道差分对，两线对称）：
  ```
  * V1: AC 差分 —— VP/VN 源经阶梯到 AINP/AINN 探针
  V1 VP 0 AC 1 DC 2.0
  V2 VN 0 AC -1 DC 2.0
  R1a VP n1 {R1}  / C1a n1 0 {C1} / C1d n1 n2 {Cd1}（若有）
  ...逐级...
  ```
  V3（失配角）= 两线 R 值分别 ±1%。V5/V6 = `.step param` 或 Python 循环生成 30 个网表。V8 kickback = 开关模型：`S1 AINP 0 swp 0 SW` + `.model SW SW(Ron={RSW} ...)`，开关频率 fMOD、占空比按 M6。V9 = OPA388 子电路 `.include OPA388.lib`（TI 模型，执行者自行下载放入 `hardware/sim/aaf/lib/`，该目录 gitignore）。

- [ ] **Step 2: 冒烟测试**——生成方案 A 的 V1 网表，`LTspice.exe -b -ascii r5_A_v1.net`，确认 `.raw` 产出且 `.log` 无报错

- [ ] **Step 3: Commit**

```bash
git add hardware/sim/aaf/gen_netlists_r5.py
git commit -m "feat(sim): r5九类仿真网表生成器"
```

---

### Task 5: LTspice 批量复测 + 结果解析

**Files:**
- Create: `hardware/sim/aaf/run_r5.py`、`hardware/sim/aaf/parse_r5.py`
- Create: `hardware/sim/aaf/r5_results.json`

**Interfaces:**
- Consumes: Task 4 网表生成器
- Produces: `r5_results.json` —— 三案 × 九仿真 × 十维实测值

- [ ] **Step 1: run_r5.py**——遍历三案 × V1-V9，调 `LTspice.exe -b -ascii`（Windows 路径），超时 300 s/个；锁屏检测：先试跑一个 .net，若 60 s 无产出则中止并提示用户解锁

- [ ] **Step 2: parse_r5.py**——ASCII .raw 解析（复用 parse_and_plot.py 的头部/点索引处理）；提取十维值：AC 取 4.096M/16.384M/16k 频点、群延迟 = −d(phase)/dω、瞬态建立时间（0.01% 带）、噪声积分（trapz 电压噪声谱²）、kickback 判稳（122 ns 窗内 0.01% 带）

- [ ] **Step 3: 理论 vs LTspice 交叉验证**（规格 §8）——AC ≤0.5 dB、建立 ≤5%；超标 → 停，查引擎或模型，修后重跑

- [ ] **Step 4: 产出 r5_results.json + Commit**

```bash
git add hardware/sim/aaf/run_r5.py hardware/sim/aaf/parse_r5.py hardware/sim/aaf/r5_results.json
git commit -m "feat(sim): r5批量复测与十维实测数据"
```

---

### Task 6: 十维评分报告 + 图纸

**Files:**
- Create: `hardware/sim/aaf/score_r5.py`、`hardware/sim/aaf/r5_report.md`、`hardware/sim/aaf/r5_bom_check.md`
- Create: `hardware/sim/aaf/图纸_r5_{A,B,C}_抗混叠.svg` + `@2x.png`（复用 gen_schematics.py 框架）

**Interfaces:**
- Consumes: `r5_results.json`、`r5_candidates.json`
- Produces: 十维评分表（min 制总分 + 每维 LTspice 实测 vs 理论预测双列）、BOM 核查表、图纸

- [ ] **Step 1: score_r5.py**——按规格 §5.1 阈值逐项归一化，min 总分，排序

- [ ] **Step 2: r5_report.md**——评分表 + CH1/CH2 群延迟差专项 + 交叉验证偏差表 + 推荐结论（不预判，按分数说话）

- [ ] **Step 3: r5_bom_check.md**——每元件 E24/E96 档映射、介质、>47 nF 的 SRF 结论

- [ ] **Step 4: 图纸**——三案 SVG，`python tools/svg_schematic_check.py <svg>` 必须 PASS（exit=0），cairosvg 出 @2x.png，read_image 分区目视

- [ ] **Step 5: Commit**

```bash
git add hardware/sim/aaf/score_r5.py hardware/sim/aaf/r5_report.md hardware/sim/aaf/r5_bom_check.md hardware/sim/aaf/图纸_r5_*
git commit -m "feat(sim): r5十维评分报告+BOM核查+三案图纸"
```

---

### Task 7: 迭代回路（条件触发，最多 3 轮）

**触发条件**（Task 6 后检查）：
- 三案 min 总分全 <1.0 → 进入迭代：分析短板维度 → 调整约束（如 fc 区间、级数）→ 回 Task 2
- A 案及格 → 不迭代，直接推荐 A
- D4 与 D1 强冲突（fc 抬高后 D1 <80 dB）→ **触发规格 U3 决策点，停下问用户**：接受四级方案 or 回压频率上限

**每轮迭代**：只重跑受影响的任务（改约束 → Task 2 起；改参数 → Task 4 起），在 r5_report.md 追加迭代记录。

- [ ] **Step 1: 判定触发条件并向用户报告迭代必要性**
- [ ] **Step 2: 执行迭代（回相应 Task）**
- [ ] **Step 3: 追加迭代记录 + Commit**

---

### Task 8: 定稿同步（用户选定方案后）

**Files:**
- Modify: `docs/design/diagram/抗混叠滤波电路.svg`（更新为定稿参数）
- Modify: `docs/design/2026-10-10-universal-signal-chain.md` E.4 节
- EasyEDA 采集页原理图（替换旧 100Ω+2.7nF 网络；顺带修 C34→GND、C35→GND 两处已知错）

- [ ] **Step 1: 用户选定 A/B/C 后才启动本任务**
- [ ] **Step 2: 更新示意图 + 过门禁**
- [ ] **Step 3: E.4 文档同步**（新参数 + 十维评分结论摘要 + 定稿日期）
- [ ] **Step 4: EasyEDA 采集页更新**（经 bridge API；改前备份当前页网络清单，改后重跑并查集网表验证）
- [ ] **Step 5: Commit + push**

---

## 自审记录

- **规格覆盖**：M1-M7→Task 1；三案求解→Task 2/3；V1-V9→Task 4/5；十维评分→Task 6；交叉验证→Task 5 Step 3；BOM 核查→Task 6 Step 3；图纸→Task 6 Step 4；U3 决策点→Task 7；E.4/示意图/原理图同步→Task 8。全覆盖。
- **占位符扫描**：无 TBD/TODO；所有脚本步骤给出了关键实现要点或复用来源。
- **类型一致性**：`solve_candidate` 返回结构在 Task 2/3 一致；`FACTS` 键名在 Task 1 定义、Task 2 消费。
