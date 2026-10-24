# aaf_pkg_review — 六方案小封装 AAF 候选台架（全轮次汇总版，2026-10-24）

任务书：`hardware/sim/AAF_基于已确认封装的候选参数与Zcode复核_2026-10-24.md` §2（参数方案）/
§5(1)–(8)（复用 fo1_rc_review 真实台架、不得改坏基线；门槛一律不降）。

**判罚结论（详见 [REPORT.md](REPORT.md)）**：D1≥80/D3≥100 dB **全六案 FAIL**（门槛未降）；
D2≥60 仅 T2/T3/T4 PASS；D4–D10/C9 全案 PASS（D4 全案 PARTIAL：>0.05 满分线、≤0.5 淘汰线；
D8 免配对全 FAIL、配对后一阶 P / 二阶须「整线同 m」、Kelvin 口径结构地板 ~56 dB 拓扑性 FAIL）。
**推荐 T2**（最优电气折中 + 全 0402 真实占地 32.62 mm²/通道）；S0/S1 出局（D2 差 ~20 dB、
占地反大 16.5%、S0 另有 47nF/0805 C0G 无目录料号阻断）。

六方案（任务书 §2）：S0 47Ω/47nF/820pF（一阶，同旧 BASE）、S1 100Ω/22nF/820pF
（一阶，同旧 FO1_A）、T1 100+100、T2 100+120、T3 68+150、T4 82+160
（二阶各配 10nF×2 + 820pF，全 0402）。

## 测试矩阵与完成状态（LTspice 26.1.1 + TI OPAx388 宏实跑 0 真失败；D7/D8 MC 判罚值为 L1 纯 Python 线性 MC（理想源+Rin130k+Cpin5p/端，n=1000，L1↔L2 交叉核对 Δ≤0.0002 dB 同判），不得称 LTspice 结果——层级声明见 t06_t11.py 头注与 assumptions.md）

| 族 | 内容 | 仿真数 | CSV |
| --- | --- | ---: | --- |
| 冒烟锚定 | S0/S1 电气等同旧轮（4 锚全 PASS，max 偏差 0.015 dB）+ T2 二阶网表可跑 | 5 | `smoke_anchor.csv` |
| AC 族 | D1/D2/D3/D4、幅相、Kelvin 口径、整链 CM（线缆寄生耦合）、CH0↔CH1 匹配、群延迟、sinc³ 合成 | 72 | `t01/t02/t02_cm_full/t03/t10/l3_*` |
| 瞬态族 | D5 建立（8 角×6 案）、D9 kickback（Ron×vcm 全扫）、THD（1k/16k 双口径）、4.096M±{1,8,16}k 折回 | 168 | `t04/t08/t09_*/thd_summary/tran_metrics.json` |
| 噪声/稳定族 | D6a 双口径、C9 peaking、断环 PM/UGF、过冲、噪声分解 | 64 | `t05/t07_*` |
| 容差族 | D7 σ、D8 三口径（免配对/各自配/整线同 m）、温度/供电角、Hratio MC | 800 | `t06_*/t11` |
| 占地线（EasyEDA） | 六方案实画布局读回，真实占地 vs 本体面积 | — | `layout_area_report.md` + `aaf_layout_*.json` |
| 寄生线（目录核查） | 47nF 三档封装 SRF/ESL/介质/容差/供货；T 系前提容值核实 | — | `parasitic_0805_0402.md` |

环境已知缺陷沿用：ltspice-sim 对 AC 复数 ASCII raw 后处理崩溃 rc=1（仿真本体完成，
以 LTspice .log/.raw 判定成功；AC/stab/tol 族触发，.noise/.tran 不触发）——全程记 note 不判失败。

## 复现（python3 直跑；LTspice 产物 gitignore，网表靠脚本再生）

```bash
cd hardware/sim/signalchain/aaf_pkg_review
python3 run_all.py all          # 冒烟：gen（19 网表 + pkg_subs.inc）→ lint（含旧网表逐行同一性对拍）→ smoke（5 只）
python3 ac_family.py all        # AC 族（--workers 4 默认）：gen/lint/probe/run/analyze/l3
python3 tran_family.py all      # 瞬态族：gen/lint/run/extract（THD 1kHz 单只 1400–1500s、raw 1.7–2.0GB）
python3 run_t05_t07.py all      # 噪声/稳定族：gen/lint/run/parse
python3 t06_t11.py all          # 容差族（--workers 4 默认）：gen/run/mc/parse/plots
# 占地线：draw_aaf_layouts.py（EasyEDA 写入）+ verify_aaf_layouts.py（读回断言）——需 EasyEDA 会话
```

全量复跑时长以天计（容差族 800 只 AC + 瞬态族 168 只 .tran，raw/ 峰值 7.7 GB 已 gitignore）。

## 目录与文件

| 文件 | 内容 |
| --- | --- |
| **`REPORT.md`** | **全轮次汇总报告**（结论/锚定/六案总表/Pareto 三行/关键问题/证据索引/遗留未测）——入口 |
| `assumptions.md` | 口径与声明假设（A–G：复用边界、冒烟口径、沿用假设、销号状态、冲突记录、全轮次口径 C7–C17、NOT VERIFIED） |
| `run_all.py` / `ac_family.py` / `tran_family.py` / `run_t05_t07.py` / `t06_t11.py` / `build_metrics.py` | 台架脚本（均过 py_compile） |
| `pkg_subs.inc` | 整链子电路库（fo_subs.inc 只读移植 + fsfo1 一阶/fsfo2 二阶；fsadc/fsrc/dut 原样） |
| `netlists/` | 各族网表（5,421 只，gitignore 再生） |
| `csv/` | 22 份结果 CSV + `tran_metrics.json`（26,102 行，判罚数据源） |
| `logs/` `raw/` | LTspice 产物（1,116 份 log；raw gitignore） |
| `plots/` | 84 张波形/分布图（t01–t11/thd/l3/smoke 各族） |
| `layout_area_report.md` | EasyEDA 占地评测报告（副本 PCB1_1、坐标证据、面积口径） |
| `parasitic_0805_0402.md` | 0805/0402 器件寄生与目录核查（村田 SimSurfing 官方数据） |
| `fp_pads.json` `fp_sources.json` `aaf_layout_*.json` `draw_aaf_layouts.py` `verify_aaf_layouts.py` | 占地线数据/脚本（任务书 §5.7 范畴） |

## NOT VERIFIED（不得引用为已测；全表见 REPORT.md §⑦ / assumptions.md §G）

PM@温度（宏 25–27 ℃ 限制）、整链 .tran、ADC 内部噪声（手册在 Obsidian）、前端源阻抗噪声、
运放单体失配、MC 分布假设、sinc³ 其他 OSR 档、1210 档官方 SRF 与 KEMET 料号可购性、
库存时效（下单前复核，E.10 #6 归用户）、占地 DRC 与真实板内落位（施工阶段）。

## 沿用的上一轮定论（不重复推导）

OPAx388 宏 .temp 仅 25–27 ℃、Ron/vcm 无手册值须扫值、C_pin 5p/端与线缆寄生的工程口径、
ltspice-sim 复数 raw 后处理崩溃——见 `../fo1_rc_review/REPORT.md` §7 与 `assumptions.md`。
本轮对 `fo1_rc_review/` 全程只读（目录 mtime 与 __pycache__ 均为上一轮；OPAx388.LIB
md5 `97c4045ef608097ec1f1a67dca97ceae` 复测同源）。

> `hardware/sim/signalchain/` 整目录当前未被 git 跟踪（上一轮 README 风险 #4），入库范围归用户决定。
