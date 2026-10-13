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
