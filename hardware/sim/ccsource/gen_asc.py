#!/usr/bin/env python3
"""Generate ccsource.asc - LTspice schematic, finalized DE-DRMS current source.
Layout v7 (textbook signal flow): 3V3A rail on top with device top-pins TOUCHING it
(no upward wires); sample current path is one vertical column T->Rsamp->Rk1->Vsm->M1
->Rsense flowing downward; opamp feedback in bottom channels; zero crossings.
Pin offsets: res A(16,16) B(16,96); voltage +(0,16) -(0,96); nmos D(48,0) G(0,80) S(48,96);
opamp invin(-32,48) noninvin(-32,80) out(32,64). R90:(x-py,y+px) M90:(x+py,y+px).
RULE: device pins must land on wire ENDPOINTS (never mid-span)."""
W, F, S = [], [], []
def wire(x1, y1, x2, y2):
    assert x1 == x2 or y1 == y2, f"diagonal {x1},{y1}->{x2},{y2}"
    if (x1, y1) != (x2, y2): W.append(f"WIRE {x1} {y1} {x2} {y2}")
def hline(x1, x2, y): wire(x1, y, x2, y)
def vline(x, y1, y2): wire(x, y1, x, y2)
def flag(x, y, net): F.append(f"FLAG {x} {y} {net}")
def sym(name, x, y, rot, inst, val): S.append((name, x, y, rot, inst, val))

# ---- 3V3A rail y=64: V1 / R1 / R3 top pins TOUCH the rail ----
hline(112, 384, 64); hline(384, 1424, 64)
flag(112, 64, '3V3A'); flag(384, 64, '3V3A'); flag(1424, 64, '3V3A')

sym('voltage', 112, 80, 'R0', 'V1', '3.3')                # +(112,96) -(112,176)
vline(112, 64, 96)
vline(112, 176, 224); flag(112, 224, '0')

# ---- R1/R2 VSET divider (col x=384) ----
sym('res', 368, 48, 'R0', 'R1', '360k')                   # A(384,64) touches rail
sym('res', 368, 352, 'R0', 'R2', '200k')                  # A(384,368) B(384,448)
vline(384, 144, 240); vline(384, 240, 368); flag(384, 240, 'VSET')
vline(384, 448, 496); flag(384, 496, '0')

# ---- M2 shunt + Vdis + Rg (col x=592, hangs below VSET rail y=240) ----
hline(384, 640, 240)                                       # VSET rail right to M2.D column
sym('nmos', 592, 288, 'R0', 'M2', 'nmosb')                 # D(640,288) G(592,368) S(640,384)
vline(640, 240, 288)                                       # M2.D down-pin touches rail endpoint
vline(592, 368, 464); flag(656, 464, 'CURR_DIS')           # gate down (label on CURR_DIS rail)
hline(592, 784, 464)                                       # CURR_DIS rail right to Rg.A
sym('voltage', 592, 512, 'R0', 'Vdis', 'PULSE(0 3.3 5m 10u 10u 5m 15m)')  # +(592,528) -(592,608)
vline(592, 464, 528)                                       # Vdis+ hangs on rail endpoint
vline(592, 608, 656); flag(592, 656, '0')
vline(640, 384, 432); flag(640, 432, '0')
sym('res', 768, 448, 'R0', 'Rg', '1Meg')                   # A(784,464) B(784,544)
vline(784, 544, 592); flag(784, 592, '0')

# ---- R3/R4 T-node bias (col x=1424, top pin touches 3V3A rail) ----
sym('res', 1408, 48, 'R0', 'R3', '10k')                   # A(1424,64) touches rail
sym('res', 1408, 288, 'R0', 'R4', '150k')                 # A(1424,304) B(1424,384)
vline(1424, 144, 224); vline(1424, 224, 304)               # split at T node
vline(1424, 384, 432); flag(1424, 432, '0')                # R4.B to GND
flag(1288, 224, 'T')

# ---- sample current path: T rail -> Rsamp -> Rk1 -> Vsm -> M1 -> Rsense (col x=1152) ----
hline(1152, 1424, 224)                                     # T rail: Rsamp.A (left end) to R3.B column
sym('res', 1136, 208, 'R0', 'Rsamp', '10k')                # A(1152,224) touches T rail left end; B(1152,304)=S
vline(1152, 304, 368)
sym('res', 1136, 352, 'R0', 'Rk1', '2')                    # A(1152,368) B(1152,448)=X
vline(1152, 448, 512)
sym('voltage', 1152, 496, 'R0', 'Vsm', '0')                # +(1152,512) -(1152,592) ammeter
vline(1152, 592, 624)
sym('nmos', 1104, 624, 'R0', 'M1', 'nmosb')                # D(1152,624) G(1104,704) S(1152,720)
vline(1152, 720, 784)
sym('res', 1136, 768, 'R0', 'Rsense', '150k')              # A(1152,784)=B node; B(1152,864)
vline(1152, 864, 912); flag(1152, 912, '0')
flag(1152, 336, 'S')                                       # S label on Rsamp.B drop segment? no: use node
# (S node is the Rsamp.B/Rk1.A junction on the main column; label placed on that vertical, reads vertically)

# ---- Opamp U1 + feedback (three parallel channels y=704/736/768, zero crossings) ----
sym('opamp', 896, 624, 'R0', 'U1', 'opa333t3')             # in-(864,672) in+(864,704) out(928,688)
# inputs connect BY NET FLAGS on pins (no traces) - cleanest opamp wiring
flag(864, 672, 'B'); flag(864, 704, 'VSET')
# B node marker on M1.S drop (joins in- by net name)
vline(1152, 720, 736); vline(1152, 736, 784); flag(1152, 736, 'B')
# out -> M1 gate (y=704)
vline(928, 688, 704); hline(928, 1104, 704); flag(1000, 704, 'VG')

# ---------------- emit ----------------
out = ["Version 4.1", "SHEET 1 1936 1080"]
seen = set()
def emit(l):
    p = l.split()
    key = tuple(sorted([tuple(p[1:3]), tuple(p[3:5])])) if l.startswith('WIRE') else \
          (('F', p[1], p[2]) if l.startswith('FLAG') else (l,))
    if key in seen: return
    seen.add(key); out.append(l)
for l in W: emit(l)
for l in F: emit(l)
for name, x, y, rot, inst, val in S:
    out.append(f"SYMBOL {name} {x} {y} {rot}")
    out.append(f"SYMATTR InstName {inst}")
    out.append(f"SYMATTR Value {val}")
out += [
 "TEXT 112 1080 Left 2 ;DE-DRMS constant current source (E.2/E.2.1): I = VSET/Rsense = 7.857uA",
 "TEXT 112 1112 Left 2 ;VSET = 3.3V x 200k/560k (R1/R2) ; M1 BSS138 pass ; Rsense 150k source-to-GND",
 "TEXT 112 1144 Left 2 ;T-node bias R3 10k + R4 150k (E.10#8) ; CURR_DIS: high -> M2 pulls VSET low",
 "TEXT 112 1176 Left 2 ;U1 = macro opa333t3 (models.inc) ; Vsm = 0V ammeter ; Rg 1Meg = gate bleed (reset-safe)",
 "TEXT 112 1208 Left 2 ;Nets: 3V3A=analog rail ; VSET=1.179V ref ; T=sample top ; S=sample bottom ;",
 "TEXT 112 1240 Left 2 ;      X=M1 drain ; B=M1 source (=Rsense top, op-amp in-) ; VG=M1 gate",
 "TEXT 112 1304 Left 2 !.include models.inc",
 "TEXT 112 1336 Left 2 !.tran 15m",
 "TEXT 112 1368 Left 2 ;.ac dec 100 0.1 10meg",
]
open('ccsource.asc', 'w', encoding='ascii').write("\n".join(out) + "\n")
print(f"written: {len(W)} wires, {len(F)} flags, {len(S)} symbols")
