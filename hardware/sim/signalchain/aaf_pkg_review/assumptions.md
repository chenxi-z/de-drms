# assumptions.md — aaf_pkg_review 声明假设与口径清单（全轮次汇总版，2026-10-24）

> 原则沿用 fo1_rc_review/assumptions.md：手册没给的值一律「显式假设 + 明示」，
> 不得伪装成手册实测。层级标记：**[LTspice]** 本轮实跑 ｜ **[解析]** 纯 Python ｜
> **[假设]** 声明参数 ｜ **[手册]** 页码级可查。
> 上一轮已定论的限制（OPAx388 宏 .temp 仅 25–27 ℃、Ron/vcm 无手册值等）见
> `fo1_rc_review/REPORT.md` §7 与 `fo1_rc_review/assumptions.md`，本轮直接沿用，不再推导。

## A. 复用与只读边界

| # | 项 | 内容 | 层级 |
| --- | --- | --- | --- |
| R1 | 复用源 | `fo1_rc_review/`（run_all.py T00 网表口径 + fo_subs.inc 基座 + ltspice-sim 运行判定逻辑）——**只读**，本轮未改动其任何文件；新台架脚本不 import 该目录任何模块（避免 `__pycache__` 写入受保护目录），所需函数带出处注释复制 | [LTspice] |
| R2 | 模型同源 | OPAx388.LIB md5 `97c4045ef608097ec1f1a67dca97ceae`（本轮 md5sum 复测一致）= TI 官方宏 Final 1.4；恒流源 fsrc（OPA333t+BSS138，B′+P4）、fsadc（M2/M6 断态）参数与 fo_subs.inc 逐行相同 | [LTspice] |
| R3 | 环境缺陷沿用 | ltspice-sim 对 AC 复数 ASCII raw 后处理崩溃 rc=1（仿真本体完成，以 LTspice 产物判定成功）——fo1_rc_review/README「环境已知缺陷」同款，本轮记 note 不判失败 | [LTspice] |

## B. 冒烟口径（本轮新增声明）

| # | 项 | 采用口径 | 依据 |
| --- | --- | --- | --- |
| C1 | S0/S1 差模激励 | Vp AC +0.5 / Vn AC −0.5（差分合计 1 V），共模 DC 2 V；D1 = −20log10\|V(pa1,na1)\|@4.096 MHz | t00_ac_dm / t01 dm 口径逐行复刻；DM 总激励 1 V → 绝对 dB 即每 1 V 归一 |
| C2 | S0/S1 共模激励 | **0.5 V**（t00 accm 口径，非 t02 的 1 V）。S0-D2 锚 46.41 = 该口径绝对 dB 残留取负；S1-D2 锚 38.11 = t02 的 **1 V 归一**口径 → 本轮以「绝对 dB − 6.0206」换算对锚，双口径副行并记（线性网络，换算精确无近似） | 锚值出处：ask 原文 + fo1_rc_review/csv/{t00_regression,t02_cm_ac}.csv |
| C3 | 冒烟容差 | 0.5 dB（ask：偏差 >0.5 dB 先查口径）；T2 16 kHz 对 §3 理想表趋势判 0.1 dB（一阶先例 S0：L1 0.2233 vs 实测 0.2234） | ask 原文 |
| C4 | 电气等同证明 | lint 阶段自动对拍：S0 dm/cm 网表与 t00_fo1_base_{acdm,accm}.net **除首行注释外逐行字节一致**；S1 dm 与 t01_dm_opa388_fo1_a.net 非 .meas 电路行完全一致；S1 cm 与 t02_cm_opa388_fo1_a.net 仅 2 行激励口径差（AC 1→0.5）+ .save 节点表差 | [LTspice]（本轮实测 diff） |
| C5 | 二阶拓扑解读 | R1→节点1（CG1 对地）→R2→节点2/ADC（CG2 对地），Cd 跨节点2 P/N，每线各一份 R/CG；网表 = t00 口径 + 该梯形扩展。**解读一致性证据**：本脚本 L1 引擎（复数 MNA，理想源 + Rin 130 k 差分 + C_pin 5 p/端）复现任务书 §3 理想表全六方案全列 ≤0.001 dB 级 | [解析]（对拍 §3 表） |
| C6 | L1 引擎负载口径 | §3 表头称「ADC 130 kΩ 典型差分电阻」；数值对拍确认其引擎含 Rin（且与本台架 C_pin 5 p/端差异 <0.001 dB @16 kHz，不可分辨） | [解析]（本轮对拍实测） |

## C. 沿用上一轮的声明假设（不在本轮重测，引用 fo1_rc_review/assumptions.md）

- **A1/A8** ADC 采样开关 Ron（扫 1/100/1 k Ω）与复位电位 vcm（扫 0/0.6/2.0 V）均无手册值
  （SBAS590E grep 0 命中）——AC/噪声/容差族口径为 fsadc 断态等效（Rin 130 k + C_pin 5 p/端）；
  D9/T08 族已按此扫值全扫（C10），数值仍为声明假设非手册值（fo1 A1/A8）；
- **A2** C_pin 5 pF/端：lad4b 工程口径非手册值（fo1 A2）；
- **A3** Z_IN 130 kΩ typ（手册 p10；Eq.5 复算 139.5 k 差 +7.3%，敏感性档未加，fo1 A3）；
- **OPAx388 宏 .temp 窗口 25–27 ℃**（fo1 assumptions §E）：温度趋势类指标本轮不做，
  勿在电路侧排查；
- **整链 .tran 未运行**是上一轮遗留口径（fo1 REPORT §7.1），本轮 full_\*_static.net 同样
  只生成过 lint 不运行，属同一遗留而非新结论。

## D. 冒烟轮 NOT VERIFIED 清单的销号状态（全轮次后复核）

| # | 冒烟轮未测项 | 全轮次状态 |
| --- | --- | --- |
| 1 | T1/T3/T4 全部仿真 | ✅ 已跑（AC 72 + 瞬态 168 + 噪声/稳定 64 + 容差 800，0 真失败） |
| 2 | T2 共模 AC、瞬态/稳定性/kickback、Kelvin 与整链场景 | ✅ 已跑（AC 族 + 瞬态族 + stab 族；整链 AC 口径 t02_cm_full/l3 已跑，**整链 .tran 仍遗留**，见 G-2） |
| 3 | 六方案真实模型 D1–D3 是否达 ≥80/60/100 dB | ✅ 已判定：**D1/D3 全六案 FAIL、D2 仅 T2/T3/T4 PASS**（门槛未降，REPORT §③a） |
| 4 | 47nF/0805 真实器件 SRF/ESL/温漂 | ⚠️ 部分核实（`parasitic_0805_0402.md`：目录层面 47nF/0805 **无 C0G 料号**、0805 档 SRF≈28–29 MHz 为同封装参照值非实测；具体料号实测归设计者/供方，见 G-8） |
| 5 | fp_pads.json / fp_sources.json 并行文件 | ✅ 归属已明：EasyEDA 占地评测线产物（任务书 §5.7 范畴），与 `draw_aaf_layouts.py`/`aaf_layout_*.json` 同族，产物见 `layout_area_report.md` |

## E. 与任务书的冲突/口径差异记录（不擅自改任务书）

1. **S0-D2 与 S1-D2 锚值口径不一致**：46.41（0.5 V 激励绝对 dB）与 38.11（1 V 归一）
   相差恒 6.0206 dB——非数据错误，系两锚出自 t00/t02 两套历史口径；本轮双口径并记
   （CSV 副行），未用口径差换取任何指标通过；
2. 任务书 §3 表头写「ADC 130 kΩ 典型差分电阻、不含采样开关」，数值对拍显示其引擎
   实际含 Rin 且与本台架负载等效（C5/C6）——无实质冲突，仅注记。

## F. 全轮次新增口径声明（AC/瞬态/噪声稳定/容差四族 + 占地 + 寄生线）

| # | 项 | 采用口径 | 层级/证据 |
| --- | --- | --- | --- |
| C7 | **D2 判罚口径** | 1 V 归一衰减量（`t02_cm_ac.csv` D2_atten_dB 列）；0.5 V 绝对 dB 恒差 +6.0206 dB 仅作锚定副行 | [LTspice]（C2 的判罚延伸） |
| C8 | **D6a 双口径** | 判罚 = r4 冻结线性口径 (n1−n3)/n3 ≤10%（六案 PASS）；正交口径 (n1−n3)/n1 并列落 CSV（T 系 30.0–45.2% 超 30% 淘汰线，如实保留不放宽）；绝对宽带噪声另列（T 系 2020–2896 nV 反而低于 S 系 2352–3301 nV） | [LTspice]（`t05_noise.csv` d6a_linear/quad_pct + note_3） |
| C9 | **D8 三口径** | ① 免配对（模式A A1/A5 MC+L2 角点）② 实际配对：各自配（B2）与整线同 m（B2L）——**二阶 B2 只到 51.1–54.5 dB（R1·C2 交叉项失配，L1 数值实证）**，B2L 恢复 90.5–91.6 dB ③ Kelvin 口径：结构地板 56.08–56.31 dB（拓扑决定，配对不可修复）。门槛 ≥80 dB 未降 | [LTspice]+[解析]（`t06_d7_d8_verdict.csv` 117 行） |
| C10 | **D9 判罚口径** | 物理主判据 chan：残余 ≤0.01%×通道差分稳态（六案×Ron{1,100,1000}Ω×vcm{0,0.6,2.0}V 全过，最坏 T4=5.02e-5）；ownss 判据在 Kelvin N 脚（na1）分母退化（稳态仅 1–5 mV，上轮 fo1 同款已知退化）→ 注记不判 FAIL。Ron/vcm 无手册值（SBAS590E grep 0 命中）沿用 fo1 A1/A8 声明假设 | [LTspice]（`t08_kickback.csv`） |
| C11 | **THD 双口径** | 任务书未给判决门 → 参考 24bit 满量程 LSB（291.11 nV）。".four Total"（0.002–0.0087%）由 4.096M 开关纹波泄漏（=基波 256/4096 次谐波）主导；真 2–10 次谐波 6e-8–2.3e-6%（0.0002–0.038 LSB ≪1 LSB）。两口径并报不互换 | [LTspice]（`thd_summary.csv`） |
| C12 | **D10 判罚口径** | 舱口径（t10 CH0_opa388_bench 行 dtau@16k）；整链串模群延迟绝对值不可用（OPA333 恒流环低频动力学污染，CH1 dtau=684823 µs、CH0 负群延迟——环路带宽附近相位急变致数值微分发散），仅串模 dphi 保留结构参考 | [LTspice]（`t10_group_delay.csv`） |
| C13 | **.meas 相位差分语法不可信** | LTspice 26.1.1 `ph(V(a,b))` proto 实测返回 (26.02dB,180°) 而 raw 真值 −20.0° → 相位一律取 raw 复数插值；幅度 .meas 与 raw 交叉校验：真信号 6862 项 max Δ=0.0001 dB | [LTspice]（tol 族 proto 留痕） |
| C14 | **面积口径** | 真实占地 = 铜包围框（焊盘+地过孔+走线外接矩形）；本体面积 = 任务书 §4 估算规则（0402=0.5、0805=2.5 mm²）——两者分列不互换；S0/S1 同 0805 等级占地等同（39.05 vs 39.06），不给 S1 面积分 | [实测]（`layout_area_report.md` + `aaf_layout_readback.json`，184 焊盘+40 过孔逐件命中容差 0.06 mil） |
| C15 | **寄生数据口径** | 村田 SimSurfing 官方典型值（数据版本 202508025_01，mlcc.csv 25,626 行，器件本体不含 PCB 走线 ≈1 nH/mm）；0805/47nF SRF≈28–29 MHz 为同封装 U2J 件 + 68nF C0G 件几何参照值（该 C0G 料号不存在）；TDK 详情经 webReader（curl/WebFetch 被 Akamai 403） | [手册/目录]（`parasitic_0805_0402.md`） |
| C16 | **sinc³ 合成口径** | L3 = 离线 Python 后处理（模拟 AC raw × sinc³ 传递函数）非 LTspice 数字核仿真；OSR=32 全局同设（A11）、alias gain 0 dB 最坏（理想冲激采样）、孔径衰减未建模（A12） | [解析]（`l3_sinc3_alias.csv` STATEMENT 行） |
| C17 | **供电角与温度角** | vlo/vhi=Vcc±5%（声明假设）：建立时间与标称全同（3 位小数）；T11 温度角为 RC 温漂全同向代入（R±100 ppm/℃ 声明假设、C0G ±30 ppm/℃ spec），不破坏 P/N 对称 | [LTspice]+[假设]（`t04/t11`） |

## G. 全轮次 NOT VERIFIED 清单（如实，不得引用为已测；与 REPORT §⑦ 同源）

1. **PM@温度**（−20/+85 ℃ 全六方案）：OPAx388 宏断环 AC 线性化仅 25–27 ℃ 窗口正确（窗外直流环路增益塌 ~1000×，fo1 REPORT §7.2 定论，本轮 t11_t2_t85 一跑复核同缺陷）；
2. **整链 .tran**（full_*_static.net 只 lint 未运行，沿 fo1 REPORT §7.1）；PSRR 交流传递函数（T11 为 DC 轨角；±1.5% 影响 <1e-6 dB 系宏模型轨不敏感的模型口径非物理结论）；
3. **ADC 内部噪声**数值对比（手册在 Obsidian 不在本仓库，沿 fo1 §7.3）；前端源阻抗噪声（六案共同项，解析 ≈16 µVrms 量级，不参与横向对比）；
4. **CMRR『RC 自身』标称舱**的 cmdm 为求解器数值底（−254~−334 dB，器件完全对称），真实未配对值以容差 MC/角点为准，不以数值底冒充（CSV caliber_note 声明）；
5. **运放单体间失配**（Zo/Aol 逐片）未建模——真实 CMRR 上界可能低于本轮值；MC 分布=容差带均匀独立假设（非实测/截尾）；
6. **L1 MC 的 Kelvin 口径**仅含失配分量（理想源无闭环输出阻抗，结构性 ~56 dB 项缺失）——Kelvin 真实值以 L2 标称角为准；
7. **600 kΩ DUT** 未扫（8 µA×600k=4.8 V 超合规栈，物理不可运行，沿 fo1 A7；扩展工况用 1 kΩ）；sinc³ 其他 OSR/滤波器档位未测；
8. **1210 档官方 SRF/ESL**（Akamai 403，理论估算层 19–21 MHz）与 **KEMET 0805/47nF/C0G**（broker 渠道，K-SIM 未访问）未验证；LCSC/DigiKey 库存时效沿 2026-10-24 01:20 CST 快照，下单前复核（E.10 #6 归用户）；
9. **占地 DRC 与真实落位**：DRC 未在副本跑（评测块在板框外）；「真实板内落位走线」属施工阶段（走廊被既有前端 RC 群占据，落位建议已给）；截图以坐标证据替代（EasyEDA API 无导出图接口）；工程级副本走手动步骤（API 无 copyProject，`layout_area_report.md` §2.2）；
10. **本轮未跑 LTspice 分档 D1/D3 复仿**（可复用 r5_bom_esl_esr 框架）。
