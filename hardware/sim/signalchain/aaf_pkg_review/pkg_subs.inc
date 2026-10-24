* =====================================================================
* pkg_subs.inc — aaf_pkg_review 六方案整链子电路库（2026-10-24）
* 基座 = fo1_rc_review/fo_subs.inc 分段只读移植（dut/fsrc/fsadc 原样；
*        fsfo 一阶 → fsfo1 一阶 + fsfo2 二阶，参数由顶层 .param 传入）
* 依赖（绝对路径，规避全角逗号目录下 LTspice 相对 include 解析失败）：
*   ccsource/models.inc                  ：opa333t/nmosb/swNO/swsh
*   _candidate_models/opa388/OPAx388.LIB  ：TI 官方宏 Final 1.4（md5 97c4045ef608097ec1f1a67dca97ceae）
* =====================================================================
.include /media/anning/data/Project/DE-DRMS/hardware/sim/ccsource/models.inc
.include /media/anning/data/Project/DE-DRMS/hardware/sim/_candidate_models/opa388/OPAx388.LIB

* ---- nmosw：M2 关断管手册拟合宏（fo_subs.inc 同式）----
.model nmosw nmos(level=1 vto=1.25 kp=0.15 lambda=0.05 cgso=10.8p cgdo=1.43p cbd=0 cbs=0)

* ---- 被测电阻 + 线缆寄生（fo_subs.inc 原样；CTOT/CTT 顶层可扫）----
.subckt dut t s
Rsamp t s {RSAMP}
Ct   t  0 {CTOT}
Cs   s  0 {CTOT}
Cts  t s {CTT}
.ends dut

* ---- 恒流源芯（B′+P4 合流，fo_subs.inc 原样）----
.subckt fsrc ta b x currd
R1   vset ta  360k
R2   vset 0   200k
Cf   vset 0   100p
M2   vset xd 0 0 nmosw
Rg   xd   0   1meg
Bdis xd   0   V={3.3*V(currd)}
Cg   g    0   1n
M1   x    g b b nmosb
Xop  vset b ta 0 g opa333t
.ends fsrc

* ---- 一阶 AAF 单线（= fo_subs.inc fsfo 原样，仅更名）----
.subckt fsfo1 in vcc vee out
Xfo in fcc vcc vee fcc OPAx388
Rf  fcc out {RFO}
Cg  out 0   {CFO}
.ends fsfo1

* ---- 二阶 AAF 单线（任务书 §2：R1→节点1(CG1)→R2→节点2/ADC(CG2)）----
.subckt fsfo2 in vcc vee out
Xfo in fcc vcc vee fcc OPAx388
Rf1 fcc n1  {RF1}
Cg1 n1  0   {CF1}
Rf2 n1  out {RF2}
Cg2 out 0   {CF2}
.ends fsfo2

* ---- ADC 采样开关模型（fo_subs.inc fsadc 原样，M2/M6 口径）----
.subckt fsadc pa na vcm vswp vswn
Rin  pa  na  130k
Cpa  pa  0   5p
Cna  na  0   5p
S1a  pa  csa vswp 0  swsh
Csa  csa vcm 1.75p
S2a  csa vcm vswn 0  swsh
S1b  na  csb vswn 0  swsh
Csb  csb vcm 1.75p
S2b  csb vcm vswp 0  swsh
.ends fsadc
