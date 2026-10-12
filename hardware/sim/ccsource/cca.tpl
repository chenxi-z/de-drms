* DE-DRMS constant current source — Variant A (sense at FET source, Rsense source-to-GND)
.inc models.inc
V1 ta 0 3.3
Rsample ta sn {RL}
Rk1 sn b 2
Vsm b dd 0
M1 dd g e e nmosb
Rs e 0 150k
R1 vset ta 360k
R2 vset 0 200k
Cf vset 0 1n
M2 vset xd 0 0 nmosb
Rg xd 0 1meg
Vdis xd 0 0
Xop vset e ta 0 g opa333m
.op
.end
