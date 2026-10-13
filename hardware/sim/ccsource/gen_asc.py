#!/usr/bin/env python3
"""Generate ccsource.asc - LTspice schematic of the finalized DE-DRMS current source.
All coordinates explicit; orthogonal wires only; topology = E.2/E.2.1 (cc2_dc.net, RL=10k).
Pin offsets (LTspice SCHEMATIC-REFERENCE / OpAmps/opamp.asy):
  res A(16,16) B(16,96); voltage +(0,16) -(0,96); nmos D(48,0) G(0,80) S(48,96);
  opamp in-(-32,48) in+( -32,80) out(32,64). R90 transform: world = (x - py, y + px)."""
G = 16
W, F, S = [], [], []
def wire(x1, y1, x2, y2):
    assert x1 == x2 or y1 == y2, f"diagonal {x1},{y1}->{x2},{y2}"
    if (x1, y1) != (x2, y2): W.append(f"WIRE {x1} {y1} {x2} {y2}")
def hline(x1, x2, y): wire(x1, y, x2, y)
def vline(x, y1, y2): wire(x, y1, x, y2)
def flag(x, y, net): F.append(f"FLAG {x} {y} {net}")
def sym(name, x, y, rot, inst, val, w0=(40,8), w3=(40,40)):
    S.append((name, x, y, rot, inst, val, w0, w3))

TA, GND = 160, 1120          # top rail (3.3V_A node TA) and bottom GND bus

# --- V1 supply ---
sym('voltage', 64, 368, 'R0', 'V1', '3.3')          # +(64,384) -(64,480)
vline(64, 384, TA);  flag(64, TA, 'TA')
vline(64, 464, GND); flag(64, GND, '0')

# --- TA top rail: V1 flag .. R1.A .. R3.A (all at y=160) ---
hline(64, 288, TA); hline(288, 672, TA); flag(64, TA, 'TA'); flag(288, TA, 'TA'); flag(672, TA, 'TA')

# --- R1/R2 VSET divider ---
sym('res', 272, 144, 'R0', 'R1', '360k')            # A(288,160) B(288,240)
sym('res', 272, 480, 'R0', 'R2', '200k')            # A(288,496) B(288,576)
vline(288, 240, 368); vline(288, 368, 496)            # R1.B -> R2.A via VSET junction
flag(288, 368, 'VSET')
vline(288, 576, GND); flag(288, GND, '0')

# --- M2 CURR_DIS pull-down on VSET ---
sym('nmos', 432, 464, 'R0', 'M2', 'nmosb')           # D(480,464) G(432,544) S(480,560)
vline(480, 464, 368); hline(288, 480, 368)           # drain to VSET junction
sym('voltage', 432, 720, 'R0', 'Vdis', 'PULSE(0 3.3 5m 10u 10u 5m 15m)')  # +(432,736) -(432,832)
vline(432, 544, 736); flag(432, 736, 'VDIS')
# NOTE: Vdis+ pin sits ON this wire at (432,736) - pin connects only at endpoints, so split:
vline(432, 816, GND); flag(432, GND, '0')
vline(480, 560, GND); flag(480, GND, '0')
sym('res', 432, 912, 'R0', 'Rg', '1meg')             # A(448,928) B(448,1008)
vline(448, 1008, GND); flag(448, GND, '0')
hline(432, 448, 928)                                  # gate rail to Rg.A
vline(432, 736, 928)                                  # Vdis+ down to Rg row (splits gate wire)
# gate wire: (432,544) down to 928 — passes Vdis+ pin (432,736): that IS the gate drive junction
# (Vdis+ connects to same vertical wire) — junction at (432,736).

# --- R3/R4 T-node bias ---
sym('res', 656, 144, 'R0', 'R3', '10k')              # A(672,160) B(672,240)
sym('res', 656, 480, 'R0', 'R4', '150k')             # A(672,496) B(672,576)
vline(672, 240, 368); vline(672, 368, 496); flag(672, 368, 'T')  # tap split at T node
vline(672, 576, GND); flag(672, GND, '0')

# --- Rsamp load from T node; Rk1 in series ---
sym('res', 848, 304, 'R0', 'Rsamp', '10k')           # A(864,320) B(864,400)
vline(864, 320, 368); hline(672, 864, 368)           # up to T rail
flag(864, 368, 'T')
sym('res', 848, 480, 'R0', 'Rk1', '2')               # A(864,496) B(864,576)
vline(864, 400, 448); vline(864, 448, 496); flag(864, 448, 'SN')  # split at SN node

# --- X rail: Rk1.B -> Vsm (0V ammeter) -> M1 drain ---
sym('nmos', 1136, 656, 'R0', 'M1', 'nmosb')          # D(1184,656) G(1136,736) S(1184,752)
sym('voltage', 1024, 576, 'M90', 'Vsm', '0', w0=(-64,16), w3=(-64,48))
# M90 voltage: + = (x+16, y+0) = (1040,576); - = (x+96, y+0) = (1120,576)
# (+ on Rk1 side so I(Vsm) reads POSITIVE for load current flowing into M1 drain)
wire(864, 576, 1040, 576)                              # Rk1.B -> Vsm(+)
wire(1120, 576, 1184, 576)                             # Vsm(-) -> M1 drain column
vline(1184, 576, 656)
flag(1184, 576, 'X')

# --- Rsense source-to-GND ---
sym('res', 1136, 848, 'R0', 'Rsense', '150k')        # A(1152,864) B(1152,944)
vline(1184, 752, 800); vline(1184, 800, 864); hline(1152, 1184, 864)  # S stub split at B tap
flag(1152, 864, 'B')
vline(1152, 944, GND); flag(1152, GND, '0')

# --- Opamp U1: in+=VSET, in-=B, out=M1 gate ---
sym('opamp', 672, 688, 'R0', 'U1', 'opa333t3', w0=(-32,48), w3=(-32,80))
# pins: in-(640,736) in+(640,768) out(704,752)
# in+ feed: avoid crossing R2 body (x=288 col) - go left to x=208 first, then down, then right
hline(208, 288, 368); vline(208, 368, 768); hline(208, 640, 768)
flag(640, 768, 'VSET')
# NOTE: opamp input pins additionally carry their own net flags (LTspice wire-pin contact at
# (640,736)/(640,768) proved flaky in netlist extraction; flags on pins are authoritative)
# B feedback: tap M1.S stub at y=800 (x=1184), rail left to x=640, up to in- (640,736)
vline(1184, 752, 800); hline(624, 1184, 800); vline(624, 736, 800); hline(624, 640, 736)
flag(1184, 800, 'B'); flag(640, 736, 'B')
# out -> M1 gate
hline(704, 1136, 752); vline(1136, 736, 752); flag(1136, 736, 'VG')

# ---------------- emit ----------------
out = ["Version 4.1", "SHEET 1 2432 1320"]
seen = set()
def emit(l):
    p = l.split()
    key = tuple(sorted([tuple(p[1:3]), tuple(p[3:5])])) if l.startswith('WIRE') else \
          (('F', p[1], p[2]) if l.startswith('FLAG') else (l,))
    if key in seen: return
    seen.add(key); out.append(l)
for l in W: emit(l)
for l in F: emit(l)
for name, x, y, rot, inst, val, w0, w3 in S:
    out.append(f"SYMBOL {name} {x} {y} {rot}")
    out.append(f"WINDOW 0 {w0[0]} {w0[1]} VLeft 2")
    out.append(f"WINDOW 3 {w3[0]} {w3[1]} VLeft 2")
    out.append(f"SYMATTR InstName {inst}")
    out.append(f"SYMATTR Value {val}")
out += [
 "TEXT 96 1168 Left 2 ;DE-DRMS constant current source (E.2/E.2.1): I = VSET/Rsense = 7.857uA",
 "TEXT 96 1200 Left 2 ;VSET = 3.3V x 200k/560k (R1/R2) ; M1 BSS138 pass ; Rsense 150k source-to-GND",
 "TEXT 96 1232 Left 2 ;T-node bias R3 10k + R4 150k (E.10#8) ; CURR_DIS: Vdis high -> M2 pulls VSET low",
 "TEXT 96 1264 Left 2 ;U1 = behavioral macro opa333t (models.inc) ; Vsm = 0V ammeter (probe I(Vsm))",
 "TEXT 96 1328 Left 2 !.include models.inc",
 "TEXT 96 1360 Left 2 !.tran 0 15m 1m 1u",
 "TEXT 96 1392 Left 2 ;.ac dec 100 0.1 10meg",
]
open('ccsource.asc', 'w', encoding='ascii').write("\n".join(out) + "\n")
print(f"written: {len(W)} wires, {len(F)} flags, {len(S)} symbols")
