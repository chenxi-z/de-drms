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
* BSS138 macro: VTO=1.25V typ, square-law sized to ~1mA@Vgs~1.9V
.model nmosb nmos(level=1 vto=1.25 kp=180u lambda=0.05 cgso=1p cgdo=1p cbd=0 cbs=0)
* linear-only variant for transient (no clamp; loop stays in linear range)
.subckt opa333t inp inn vsp vsn out
E1 a 0 VALUE={2e6*(V(inp)-V(inn))}
Rp a b 1meg
Cp b 0 0.909u
Rout b out 100
.ends
