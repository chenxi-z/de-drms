* =====================================================================
* fo_subs.inc — fo1_rc_review 整链子电路库（2026-10-24）
* 基座 = fs_fullchain/fs_subs.inc 分段移植（dut/fsrc/fsadc 原样；fslad 四级 → fsfo 一阶）
* AIN1N Kelvin 接法（无第四运放）在顶层场景网表实现，不在本库。
* 依赖（绝对路径，规避全角逗号目录名下 LTspice 相对 include 解析失败）：
*   ccsource/models.inc                     ：opa333t/nmosb/swNO/swsh
*   _candidate_models/opa388/OPAx388.LIB    ：TI 官方宏 Final 1.4（md5 97c4045ef608097ec1f1a67dca97ceae）
* 一阶参数 RFO/CFO 由顶层 .param 传入（四方案共用同一子电路，仅参数不同）。
* =====================================================================
.include /media/anning/data/Project/DE-DRMS/hardware/sim/ccsource/models.inc
.include /media/anning/data/Project/DE-DRMS/hardware/sim/_candidate_models/opa388/OPAx388.LIB

* ---- nmosw：M2 关断管手册拟合宏（fs_subs.inc 同式）----
.model nmosw nmos(level=1 vto=1.25 kp=0.15 lambda=0.05 cgso=10.8p cgdo=1.43p cbd=0 cbs=0)

* ---- 被测电阻 + 线缆寄生（fs_subs.inc 原样；CTOT/CTT 顶层可扫）----
.subckt dut t s
Rsamp t s {RSAMP}
Ct   t  0 {CTOT}
Cs   s  0 {CTOT}
Cts  t s {CTT}
.ends dut

* ---- 恒流源芯（B′+P4 合流，fs_subs.inc 原样）：ta(3.3VA) b(Rsense顶) x(BSS138漏极/回线) currd ----
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

* ---- 一阶 AAF 单线（替换 fslad 四级）：跟随器(TI 宏) + R(fcc→out) + C_G(out→0) ----
* 任务书 §2 拓扑：每条输入线各串一颗 R、各一颗对地 C_G；C_D 在顶层跨 pa/na（串联 R 之后）
.subckt fsfo in vcc vee out
Xfo in fcc vcc vee fcc OPAx388
Rf  fcc out {RFO}
Cg  out 0   {CFO}
.ends fsfo

* ---- ADC 采样开关模型（fs_subs.inc fsadc 原样，M2/M6 口径）----
* C_S=3.5pF 差分（每侧 1.75pF）；S1/S2 180° 反相 @fMOD=4.096MHz、各占 50%
* Ron=100Ω（swsh，lad4b D9 主口径；手册无规格 → 声明假设，T08 扫 1/100/1k）
* ms 场景：vswp=vswn=0（断态，只留 Z_IN/C_pin/C_S 负载）；µs 场景：顶层 PULSE 实时钟
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
