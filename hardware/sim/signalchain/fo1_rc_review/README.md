# fo1_rc_review — 一阶 RC 四方案复核工作目录（**T00–T12 全量完成** 2026-10-24）

**当前状态**（2026-10-24 终态）：**T00–T12 全部实跑完成**（L1 理想基准 + L2 四测试族
AC/瞬态/稳定性/容差 + L3 离线后处理 + T12 BOM 核查）。最终结论见 **`REPORT.md`**
（七节齐备）；L3 专项细节见 `REPORT_L3.md`；声明假设与口径清单见 `assumptions.md`。
产物规模（2026-10-24 实测 `find`）：`netlists/` 内 **530 个 .net**（目录共 2,545 文件，
另含 LTspice 就地运行产物 .log 526 / .raw 1,040 / .db 448）、`raw/` 525 个 .raw、
`logs/` 526 个 .log、`csv/` 20 个 CSV（13,139 行）、`plots/` 51 张 PNG
（gitignore 不入库，靠脚本再生）。

**复现总入口（依序实跑，全部 `python3` 直跑）**：

```bash
cd hardware/sim/signalchain/fo1_rc_review
python3 run_all.py t00        # T00 环境回归（FO1_BASE 四项 + 锚定对拍）
python3 ac_family.py          # T01 差模 AC / T02 共模 AC / T03 通道匹配 / T10 群延迟
python3 tran_tests.py         # T04 建立 / T08 kickback(Ron×vcm 扫) / T09 注入残差+折叠
python3 run_stab.py           # T05 噪声(.noise) / T07 稳定性(PM/UGF/C9/过冲)
python3 t06_t11.py            # T06 容差(L1 MC n=1000×3档 + LTspice 31角点) / T11 温度供电角
python3 l3_hratio_alias.py    # L3 离线：sinc³ 锚点自证 + Hratio/混叠/CM 系数（非 LTspice 数字内核）
# T12 BOM/占地：见 bom_footprint_check.md §7（EasyEDA 桥接 + LCSC/DigiKey 检索，独立于电路）
```

单网表复跑：`~/.local/bin/ltspice-sim run netlists/<case>.net`（ASCII raw；同文件
flock 排他、不同文件可并行）；`.meas` 从 `logs/<case>.log` 读；AC 复数 raw 用
`hardware/sim/aaf/parse_r5.py` 的 `Raw` 类解析；断言示例
`~/.local/bin/ltspice-sim assert raw/<case>.raw 'V(pa1,na1)=0.7099 abs=1e-3'`。

**环境已知缺陷（如实，不影响产物有效性）**：`ltspice-sim run` 对 AC 复数 ASCII raw
行后处理崩溃 rc=1——LTspice 仿真本体均完成（.log 含 elapsed + 完整 .meas），台架以
LTspice 产物判定成功。LTspice 26.1.1 `.meas AC mag()/ph()` 输出 dB 元组，各脚本解析器
已换算并经 raw 交叉验证。

目录骨架：`README.md`（本文件）、`assumptions.md`（声明假设与风险）、
`run_all.py`（台架主脚本：gen / t00 / lint / all）、`fo_subs.inc`（整链子电路库，
run_all.py 生成）、`netlists/ logs/ raw/ csv/ plots/ models/`
（netlists/logs/raw 产物 gitignore 不入库，靠 run_all.py 再生）。

## T00 回归实跑记录（2026-10-24，LTspice 26.1.1 实测）

`python3 run_all.py t00`：FO1_BASE（47 Ω/47 nF/820 pF）四项仿真实跑，
T00 网表与 `aaf_first_order/gen_fo.py` 生成物**逐行一致**（脚本内自动对拍验证，
仅首行注释不同）。结果（`csv/t00_regression.csv`，锚定值 = 2026-10-23 报告）：

| 指标 | 锚定 | 本轮实测 | 偏差 | 容差 | 判定 |
| --- | ---: | ---: | ---: | ---: | --- |
| D1 残留 dB @4.096 MHz | −40.7 | −40.689 | +0.011 | 2 dB | 复现 |
| D2 残留 dB @4.096 MHz | −46.4 | −46.410 | −0.010 | 2 dB | 复现 |
| D3 残留 dB @16.384 MHz | −62.7 | −62.673 | +0.027 | 2 dB | 复现 |
| D4 @16 kHz | 0.230 | 0.2234 | −0.007 | 0.1 dB | 复现 |
| 0.01% 建立 | ≈21 µs | 20.846 | −0.15 | 2.1 µs | 复现（口径见下） |
| 环路 PM | 98.6° | 98.568 | −0.03° | 9.9° | 复现 |

meas 与 raw 插值交叉校验一致（差 <0.001 dB）；建立时间镜像校验
（tran −0.71→0 与 tran2 0→+0.71 双极性出带法）同为 20.846 µs。

**口径排查发现（三项，均已如实记入 CSV note）**：
1. `.meas AC mag()` 输出为 `(-40.689dB,0°)` dB 元组——gen_fo.py:103 正则
   两种输出格式均不匹配，即旧 fo_results.json ac_dm/ac_cm/tran 空字段的根因（实测确认）；
2. gen_fo.py 原 `ts01 WHEN V(pa1,na1)=0.709929 RISE=1` **物理不可达**：DC 分压
   0.999278（94 Ω/130 k）使真终值 0.709487 V 低于阈值 0.709929 V，crossing 永不
   触发（且其 PWL 极性差分为 −0.71→0，正阈值 RISE 更不存在）→ 旧报告 ≈21 µs
   **不可能出自该 .meas**，产生口径不可考证；本轮改用 raw 带外最后出带法
   （终值 ±71 µV）双极性镜像口径对照，结果 20.85 µs 与锚定 ≈21 µs、
   理论 9.21τ=21.06 µs 三者相容；
3. ltspice-sim `run` 对 AC 复数 ASCII raw 行（`1.0e-01,0.0`）内部后处理崩溃
   （rc=1）——仿真本体已完成（.log 有 elapsed time + 完整 .meas），台架以
   LTspice 产物判定成功，该 rc 记为环境 note（不冒充失败也不掩盖）。

> **git 注意**：`.gitignore:188` `*.log`、`:219` `*.raw`、`:221`
> `hardware/sim/**/*.net` —— netlists/ logs/ raw/ 下的运行产物**不入库**，
> 可复现性必须靠入库的生成脚本（`gen_*.py`）+ 本 README 的口径记录。

---

## 环境与模型来源（逐项实测勘察，2026-10-24）

### 1. LTspice 批量执行入口：`~/.local/bin/ltspice-sim`

- **本体**：symlink → `/home/anning/ltspice-wine-setup/bin/ltspice-sim`
  （本机 Python 脚本，956 行，mtime 2026-10-12；无 `--version` 参数，以文件为准）。
- **环境实测**（命令 `~/.local/bin/ltspice-sim status`，本次实际执行，输出节选）：
  `ltspice_version: 26.1.1`、`wine: wine-11.0`、
  `ltspice_exe: /home/anning/.ltspice/drive_c/Program Files/ADI/LTspice/LTspice.exe`、
  `prefix: /home/anning/.ltspice`、`display: :77`（alive）、`ready: true`。
- **子命令**（`--help` 实测）：`status / doctor / display / mcp-prep /
  netlist / run / probe / assert / sim`。
  - `netlist file.asc` → 生成同名 `.net`（内部 `LTspice -netlist`，cwd=文件目录）；
  - `run file.net|file.asc` → `.asc` 自动先转网表再跑；内部执行
    `LTspice.exe -b [-ascii] <basename>`，**cwd = 网表所在目录**（规避 Wine 路径问题，
    脚本 `KNOWN_ISSUES` 第 3 条记录的陷阱）；**默认输出 ASCII `.raw`**（`--binary`
    才是二进制——`probe` 只解析 ASCII）；
  - `probe file.raw [V(out) ...]` → 每变量 first/last/min/max/mean；全局 `--at 1ms`
    可按时间取样；
  - `assert file.raw 'V(out)=5 abs=1e-3'`（支持 `V(out)@1ms=...` 形式）；
  - `sim` = netlist → run → probe（`--expect` 带断言）一条龙。
- **退出码**（脚本头注释 :12）：0 成功 / 2 用法 / 3 环境 / 4 仿真失败 / 5 断言失败。
- **锁与并发**（脚本源码 `ltspice-sim:179-204` `file_lock()`，netlist/run 均套用
  :355/:393）：
  - 同一电路文件（按**绝对路径 sha1** 命名）在 `/tmp/ltspice-sim-locks/<hash>.lock`
    上 `flock(LOCK_EX|LOCK_NB)` 排他，拿不到锁每 0.5 s 重试，默认
    `--lock-timeout 180 s` 超时后报「等待 … 释放锁超时」；
  - **不同文件互不干扰，可多进程并行**（脚本头 :10「并发安全：同一个电路文件加
    flock，不同文件 / 不同工作区互不干扰」）→ 四方案各自独立 `.net` 可并行批跑；
  - Xvfb 单例由 `/tmp/ltspice-sim-xvfb.lock` 保护（:115-123）。
- **默认超时**：`--timeout 300 s`（单次 LTspice，:858）。fs 母本经验：整链 ms 级
  `.tran` 可达分钟级（fs_fullchain/README:63 记录 13.5 ms 短窗版 233 s），长跑要
  显式调大。
- **AC 复数结果解析**：`probe` 不认复数 raw（`aaf_first_order/gen_fo.py:120`
  明确记录）；既有先例 = 复用 `hardware/sim/aaf/parse_r5.py` 的 `Raw` 类解析
  复数 `.raw`（PM/UGF 即由此提取）。

### 2. 真实 TI OPA388 宏模型

- **路径**：`hardware/sim/_candidate_models/opa388/OPAx388.LIB`（17624 B，
  mtime 2022-06-07）。
- **md5（实测 `md5sum`）**：`97c4045ef608097ec1f1a67dca97ceae`
  ——与 `fs_fullchain/fs_subs.inc:5` 注记引用的 md5 **一致**（同源验证）。
- **文件头实测**（`head`）：(C) 2022 TI，Part OPAx388，Date 06JUN2022，
  **Model Version Final 1.4**，Model Type **"Generic (suitable for all analysis
  types)"**（→ `.noise` 合法），Datasheet **SBOS777D**；
  实例引脚 `.SUBCKT OPAx388 IN+ IN- VCC VEE OUT`（LIB:83）。
- **反面清单**：`ccsource/models.inc` 的 `opa388t` 是**行为宏**（E 源增益 5e5、
  无压摆率，models.inc:64-77）——fs 母本（ccsource/fs*.net）用的就是它。
  四方案复核的主口径必须是 TI 宏（任务书 §3.1），`opa388t` 只可用于交叉对照，
  不得冒充。

### 3. 整链基座判定（fs_fullchain vs aaf_first_order）

| 候选 | 内容物 | 对四方案复核的可用性 |
| --- | --- | --- |
| `signalchain/fs_fullchain/` | README.md + `fs_subs.inc`（段子电路库）+ `fsp.py`（ASCII raw 解析）**共 3 件** | 分段最全：`dut`（DUT+线缆寄生 200p/端+30p 线间）/`fsrc`（恒流源 B′+P4：OPA333+BSS138）/`fslad`（**TI 宏 OPAx388**+lad4b 四级 AAF，每线）/`fsadc`（M2/M6 采样开关：Z_IN 130k 常挂+C_pin 5p/端+C_S 1.75p/侧双相 swsh Ron=100Ω）。**但 AAF 段是 lad4b 四级阶梯，不是一阶**；且 README §三（fs_fullchain/README:33-43）声称的场景网表 `fs1_static/fs2_shock/fs3_seq/fs_kb/fs_probe_*/fs_loop_cal2/fs_disc_a..d` **全部不在目录里**（须按 README 骨架重建） |
| `signalchain/aaf_first_order/` | `gen_fo.py` + `fo_results.json` + `gen_compare_svg.py` | 一阶结构实现与任务书 §2 拓扑**逐件一致**（`ladder()`：每线 `Ra1 fpa→pa1` + `Ca1 pa1→0`，`Cd pa1–na1` 跨接，gen_fo.py:29-32,44），真实 TI 宏直挂 + ADC 引脚负载（Rin 130k + 5p/端）。**但为孤立台架**：理想源 Vp/Vn 直驱两颗对称跟随器——无恒流源、无 K1–K4、无 Rsense、**AINxN 是对称第二运放**（任务书 §1 明令禁止单独以此为整链结论）、无采样开关（无 C_S/kickback 模型） |

**判定：整链基座 = `fs_fullchain/fs_subs.inc`，一阶 AAF 段从 `gen_fo.py` 移植。**

落地方式（写给施工阶段）：

1. **AAF 段替换**：在新的子电路库里做 `fsfo`（每线：`Xfo in fcc vcc vee fcc OPAx388`
   跟随器 + `R fcc→out` + `C_G out→0`），替代 `fslad` 内 lad4b 四级（fs_subs.inc:46-56）。
   T/M/B 三线（AIN0P/AIN0N/AIN1P 对应测量点）各一份；
2. **AIN1N Kelvin 保真**：**不放第四颗运放**。参照 fs 母本 `ccsource/fs1_static.net:41-42`
   的既有真实接法（`Rf3 0 a1n 1k` + `Cf3 a1n 0 10n`——E=Rsense 底端，在低边拓扑里
   即地节点 `Rs b 0 150k` 的 node 0）：改为 `R_N E→na1` + `C_GN na1→AGND`，
   **保留真实源阻抗与接地回路**（任务书 §1「特别核对」项）；
3. **C_D 位置**：每差分通道 1 颗，跨接 `pa/na` 两 ADC 引脚（串联 R 之后），顶层挂；
4. **ADC 负载与采样**：`fsadc` 原样保留；沿用 fs_subs.inc:80-88 的**时间尺度分层
   口径**——ms 场景（fs1/fs2/fs3 类）S1/S2 置断态只留 Z_IN/C_pin/C_S 负载，
   µs 场景（fs_kb 类）真实 PULSE 两相时钟 4.096 MHz 跑 kickback；
5. **include 用绝对路径**（fs_subs.inc:3-5 记录的实测陷阱：全角逗号目录名下
   LTspice 相对 include 解析失败）；
6. **场景网表须重建**：fs_fullchain 的 fs1_static/fs2/fs3/fs_kb/fs_probe/fs_disc
   均缺失（见风险 3），拓扑骨架以 fs_fullchain/README §三 + fs 母本
   `ccsource/fs1_static.net`（K1–K4 时序、δ0/k 校准、Brout 比值重构）为参照。
   注意 fs 母本用 `opa388t` 行为宏 + 1k/10n RC + 2µs 孔径 S/H——**只借接线与时序
   骨架，器件模型一律换成 TI 宏 + 一阶 RC + M2/M6 采样开关**。

### 4. ADC 口径出处（全部页码级可查：`hardware/sim/aaf/r5_datasheet_facts.md`）

| 参数 | 值 | 出处（r5_datasheet_facts.md 行号 → SBAS590E 页码） |
| --- | --- | --- |
| 差分采样电容 C_S | **3.5 pF typ**（差分；每侧 C_S/2 经 S1 接入/S2 复位） | :93 → p10 §7.5 EC 表 `Cs Input capacitance`；:94 → p29 §9.3.2 + Fig.38（图标 `Cs/2`） |
| 输入阻抗 Z_IN | **130 kΩ typ @fMOD=4.096 MHz** | :113 → p10 EC 表 `Zin Differential input impedance`；:114-115 → p29 Eq.5 `Z_IN=2/(fMOD·C_S)`，复算 139.5 kΩ，与 130 k 差 +7.3%（手册取整/含寄生） |
| 采样开关时序 | S1/S2 **180° 反相、各 50% 占空、fMOD=4.096 MHz**（半周期 122.07 ns） | :48-49 → p29 Fig.37 |
| 开关 Ron | **手册全文无规格**（grep 0 命中）→ **只能作声明假设** | :158（无规格）、:165-166（建议缺省 1Ω + 1/100/1kΩ 扫值） |
| 无手册值三项 | 模拟输入偏置电流 / 开关 Ron·孔径时间 / 闭环输出阻抗曲线 | :237-238 |

spec 侧规定：`docs/design/spec/2026-10-18-aa-driver.md:140,184`（M6/V8）——
「若手册未给 R_sw/时序，用缺省 Ron=1 Ω 建模并在报告中**明示假设**」。

**口径冲突（既有件内部不一致，复核时按任务书 T08 扫值覆盖）**：
`fs_subs.inc` 的 `fsadc` 用 `swsh` **Ron=100 Ω**（ccsource/models.inc:85，
lad4b D9 主口径），而 spec V8 缺省是 **1 Ω**——两者都是声明假设，扫值
（1/100/1kΩ）后该差异不再影响结论。

`C_pin 5p/端`：**工程口径非手册值**——lad4b FIN 台架假设
（`signalchain/aaf_lad4b/README.md:116`），fsadc 沿用（fs_subs.inc:62）。
已登记 assumptions.md。

### 5. 任务书路径勘误 + D/C 定义权威

- 任务书 §1 写 `docs/design/2026-10-23-signal-chain-variants.md` ——
  **实际在 `docs/design/spec/2026-10-23-signal-chain-variants.md`**（实测 find）；
- 任务书 §1/§5.1 写 `docs/design/spec/2026-10-18-aa-driver-design.md` ——
  **实际文件名 `docs/design/spec/2026-10-18-aa-driver.md`（无 `-design` 后缀）**；
  同一后缀笔误也出现在 `fs_fullchain/fs_subs.inc:58` 注释（既有文件，本次不改，仅记录）。
- **D1–D10 / C1–C9 / M1–M7 / V1–V9 的定义权威 =
  `docs/design/spec/2026-10-18-aa-driver.md`**：D1–D10 评分维度表 :70-82（含总分
  min() 规则 :82、D5/D7/D8 容差角条件 :82）、C9 peaking ≤6 dB :126、M2/M6 手册
  核实 :136/:140、V8 构建规范 :179-184、维度-仿真覆盖矩阵 :182（D1→V1 … D10→V1）、
  版本沿革 v2 六维→十维 :231 / v4 修订（D6 拆分、D8 配对条件、C9 新增）:233。
- **FO1 基线回归锚点数值出处** = `docs/design/spec/2026-10-23-signal-chain-variants.md`
  :33-38（D1 −40.7 dB / D2 −46.4 dB / D3 −62.7 dB / D4 0.230 dB / PM 98.6°）与
  :57-61（建立 21 µs、C9 +1.4 dB、免配对、D1–D3 天花板 ≈−45 dB）；
  未测项声明 :109（一阶 D7 蒙特卡洛 / D9 kickback / D10 群延迟未专项实测、噪声仅
  解析估算）——与任务书 §6.2 的 T00 复核锚点一致。

---

## 已知风险与缺口（勘察期登记 → 2026-10-24 终态标注）

1. ~~**fo_results.json 逐点数值不可复原**~~ ✅ 已闭环（T00 重跑，六项锚定复现；
   根因 = `.meas` dB 元组格式 + ts01 物理不可达，实测确认，见顶部口径记录）；
2. **一阶与整链的历史 .net/.raw/.log 全部不在工作树**（.gitignore:188/219/221）：
   可复现性靠入库脚本 + 本 README 口径记录（本轮 netlists/raw/logs 已再生于本目录）；
3. ~~**fs_fullchain 场景网表缺失**~~ ⚠️ 部分闭环：`netlists/full_fo1_*_static.net`
   已生成过 lint，**整链场景 .tran 未运行**（L2 为通道台架口径）——REPORT.md §7.1 遗留；
4. `hardware/sim/signalchain/` 整目录**未被 git 跟踪**（`git status` 显示 `??`，
   含 REPORT.md 与各子目录）——本目录结论若要留档，需用户决定入库范围；
5. ~~**Ron 口径差**（100 Ω vs 1 Ω）~~ ✅ 已闭环（T08 扫 1/100/1k Ω × vcm 三档）；
   **Z_IN 130k vs 139.5k** 公式差 +7.3% 敏感性档未加（assumptions A3）；
6. **C_pin 5p/端、线缆寄生 200p/端+30p、Cff=100p 均为工程假设/新增建议**
   （fs_fullchain/README §二 判别 D 定档），非手册值；Cff 回填 BOM 前须经设计
   Owner 确认（fs_fullchain/README:77 已声明）；
7. ~~LTspice `.noise` 支持性与 200 MHz 收敛性未验证~~ ✅ 已闭环（T05 全跑，
   TI 宏 Final 1.4 实测可用，逐器件归属 attr_xcheck=0.0%）；
8. **OPAx388 宏 .temp 窗口限制**（本轮新发现）：断环 AC 线性化仅 25–27 ℃ 正确，
   PM 温度趋势 NOT VERIFIED（T11 归因记录，非电路问题）。

## 复现方法（终版：六脚本依序实跑，见顶部「复现总入口」；以下为骨架说明）

```bash
# 批跑单个网表（ASCII raw，默认）
~/.local/bin/ltspice-sim run hardware/sim/signalchain/fo1_rc_review/netlists/<case>.net
# .meas 从 logs/<case>.log 读；AC 复数从 raw/ 用 hardware/sim/aaf/parse_r5.py 解析
# 断言示例
~/.local/bin/ltspice-sim assert raw/<case>.raw 'V(pa1,na1)=0.7099 abs=1e-3'
```

**脚本 ↔ 测试项 ↔ CSV 对应表**（任务书 §4 全覆盖）：

| 脚本 | 测试项 | 输出 CSV |
| --- | --- | --- |
| run_all.py t00 | T00 | t00_regression.csv |
| ac_family.py | T01/T02/T03/T10 | t01_dm_ac / t02_cm_ac / t03_channel_match / t10_group_delay |
| tran_tests.py | T04/T08/T09 | t04_settling / t08_kickback / t09_ac_residual / t09_fold_check |
| run_stab.py | T05/T07 | t05_noise / t07_stability |
| t06_t11.py | T06/T11 | t06_mc_all / t06_mc_summary / t06_ltspice_corners / t06_ltspice_summary / t06_d7_d8_verdict / t11_corners（注：t06_l1_l2_xcheck.csv 为历史产物——现版脚本不含其写出代码，且该文件是 L1 引擎 6 dB 归一 bug 修复前版本，详见 REPORT.md §6.3） |
| l3_hratio_alias.py | L3 | l3_hratio_alias.csv（+ REPORT_L3.md） |
| （独立核查） | T12/L1 | bom_footprint_check.md / l1_ideal_rc.csv（L1 引擎在 t06/t11 脚本内共用） |

四方案参数（任务书 §2 表，原文照录）：FO1_BASE 47Ω/47nF/820pF、
FO1_A 100Ω/22nF/820pF、FO1_B 200Ω/10nF/820pF、FO1_C 100Ω/10nF/6.8nF。
理想 fc 自检基准表（任务书 §2 末）是接线自查工具，**不是 LTspice 验收真值**。
