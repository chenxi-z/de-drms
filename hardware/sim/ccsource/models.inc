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
* 3-pin variant for LTspice 'opamp' symbol (internal 3.3V rails, tanh clamp)
* NOTE: symbol pin order is (invin, noninvin, out) -> arg1 = inverting input!
.subckt opa333t3 invin noninvin out
E1 a 0 VALUE={2e6*(V(noninvin)-V(invin))}
Rp a b 1meg
Cp b 0 0.909u
Eb c 0 VALUE={0.001+1.6245*(1+tanh(6*V(b)-9))}
Rout c out 100
Cout out 0 5p
.ends
