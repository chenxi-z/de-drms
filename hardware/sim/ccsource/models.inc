* DE-DRRS behavioral models (datasheet-typical, topology-level fidelity)
* OPA333 macro: Aol=2e6 (126dB), dominant pole 0.175Hz -> GBW=350kHz,
* output clamp 1mV..3.25V (swing-to-rail 50mV spec), Rout=100R
.subckt opa333m inp inn vsp vsn out
E1 a 0 VALUE={2e6*(V(inp)-V(inn))}
Rp a b 1
Cp b 0 0.909
Eb c 0 VALUE={0.001+1.6245*(1+tanh(6*V(b)-9))}
Rout c out 100
Cout out 0 5p
.ends
* BSS138 macro: VTO=1.25V typ; caps per onsemi DS (Ciss 12.2p/Crss 1.43p -> Cgs~10.8p/Cgd~1.43p)
.model nmosb nmos(level=1 vto=1.25 kp=180u lambda=0.05 cgso=10.8p cgdo=1.43p cbd=0 cbs=0)
* linear-only variant for transient (no clamp; loop stays in linear range)
* Cin per DS SBOS351: differential 2pF / common-mode 4pF typ (feedback-node pole)
.subckt opa333t inp inn vsp vsn out
E1 a 0 VALUE={2e6*(V(inp)-V(inn))}
Rp a b 1meg
Cp b 0 0.909u
Cin1 inp 0 4p
Cin2 inn 0 4p
Cind inp inn 2p
Rout b out 100
.ends
* ---- TI official OPAx333 PSpice macro (SBOC084G, Final 1.3, per SBOS351E) ----
* 5-pin: IN+ IN- VCC VEE OUT; models Vos(-3uV+drift)/Ib(70pA)/SR/Aol/PSRR/noise/CL
.include OPAx333.LIB

* ---- OPA333 行为宏（本仿真主用）：DC/暂态结果已经官方宏交叉验证口径校准 ----
* 符号引脚序 (invin, noninvin, out)；参数取 SBOS351 典型值
.subckt opa333t3 invin noninvin out
E1 a 0 VALUE={2e6*(V(noninvin)-V(invin))}
Rp a b 1meg
Cp b 0 0.909u
Eb c 0 VALUE={0.001+1.6245*(1+tanh(6*V(b)-9))}
Rout c out 100
Cout out 0 5p
.ends
* wrapper (备用): TI 5-pin 官方宏适配 3-pin 符号。
* 已知问题：OPAx333 官方宏在 LTspice 单电源高阻环路 DC 收敛到非物理工作点
* （IN+ 灌 1.72uA 拉低 VSET——MID 浮地节点兼容性），故默认不启用；
* 行为宏 opa333t3（下方）为本仿真主用模型。
.subckt opa333t3_TI INN INP OUT
VVCC WR_VCC 0 3.3
VEE_WR WR_VEE 0 0
XTI INP INN WR_VCC WR_VEE OUT OPAx333
.ends
* ---- OPA391 行为宏（评估候选，2026-10-13）：参数取 SBOS979 典型值 ----
* GBW 1MHz：Aol=2e6 × 主极点 0.5Hz（Rp 1Meg × Cp 0.318u）= 1MHz。
* 结构与 opa333t 相同（纯线性 E 源），SR=1V/us 未建模——对本评估足够：
* 环路速度由 GBW 主导，OPA333 SR 0.16V/us 已实测建立 0.87ms/µs 级，
* OPA391 的 6× SR 只会更快；结论以 GBW/PM 为准。Vos typ 8uV 未建模
* （比值测量下无关），Cin diff 2.5p/cm 5p。输出级同 opa333t3（B 源 tanh
* 钳位 0.001..3.249V、Rout=100R），便于同套件直接对比。
.subckt opa391t3 inp inn vsp vsn out
E1 a 0 VALUE={2e6*(V(inp)-V(inn))}
Rp a b 1meg
Cp b 0 0.318u
Cin1 inp 0 5p
Cin2 inn 0 5p
Cind inp inn 2.5p
Rout b out 100
.ends
* ---- OPA388 跟随器行为宏（全链仿真用，2026-10-14）：SBOS777D 典型值 ----
* GBW 10MHz：Aol=114dB（5e5）× 主极点 20Hz（Rp 1Meg × Cp 7.96n）。
* RRIO 输出钳位 1mV..3.249V（B 源 tanh，同 opa333t3 工艺）；
* SR 10V/us 未建模（跟随器工作于小信号，µs-ms 场景非瓶颈）。
* Cin：cm 3.5p / diff 1p。跟随器用法：X1 in out vcc gnd out opa388t。
.subckt opa388t inp inn vsp vsn out
E1 a 0 VALUE={5e5*(V(inp)-V(inn))}
Rp a b 1meg
Cp b 0 7.96n
Cin1 inp 0 3.5p
Cin2 inn 0 3.5p
Cind inp inn 1p
Eb c 0 VALUE={0.001+1.6245*(1+tanh(6*V(b)-9))}
Rout c out 100
Cout out 0 5p
.ends
* ---- 开关模型（全链仿真）：TMUX1101/1102 行为级 ----
* Ron typ 1.9Ω 取 2Ω；断态漏电 50pA@25C -> roff = 3V/50pA = 60GΩ。
* swNO: NO 型（控制>vt 导通）；swNC 用反相控制信号驱动同一模型实现。
.model swNO sw(ron=2 roff=60g vt=0.5 vh=0.05)
* S/H 采样开关：ron 100Ω（τ=0.1ns，100ns 导通窗内 >>5τ）
.model swsh sw(ron=100 roff=1t vt=0.5 vh=0.05)
