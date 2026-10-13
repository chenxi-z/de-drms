#!/usr/bin/env python3
"""Generate ccsource.asc - LTspice schematic, finalized DE-DRMS current source.
Layout v4 (user's compact arrangement): M2 shunt branch flows down from VSET rail,
Rsamp horizontal across T->S, opamp between load and M1, feedback channel y=736.
Pin offsets: res A(16,16) B(16,96) [R90: A right, B left]; voltage +(0,16) -(0,96);
nmos D(48,0) G(0,80) S(48,96); opamp invin(-32,48) noninvin(-32,80) out(32,64).
R90: (x-py, y+px). M90: (x+py, y+px)."""
W, F, S = [], [], []
def wire(x1, y1, x2, y2):
    assert x1 == x2 or y1 == y2, f"diagonal {x1},{y1}->{x2},{y2}"
    if (x1, y1) != (x2, y2): W.append(f"WIRE {x1} {y1} {x2} {y2}")
def hline(x1, x2, y): wire(x1, y, x2, y)
def vline(x, y1, y2): wire(x, y1, x, y2)
def flag(x, y, net): F.append(f"FLAG {x} {y} {net}")
def sym(name, x, y, rot, inst, val): S.append((name, x, y, rot, inst, val))

# ---- V1 + TA rail (y=64) ----
sym('voltage', 112, 272, 'R0', 'V1', '3.3')              # +(112,288) -(112,368)
vline(112, 64, 288); vline(112, 368, 416); flag(112, 416, '0')
hline(112, 384, 64)                                       # TA rail (ends at R1.A)
flag(112, 64, '3V3A'); flag(384, 64, '3V3A')

# ---- R1/R2 VSET divider (col x=384) ----
sym('res', 368, 48, 'R0', 'R1', '360k')                   # A(384,64) B(384,144)
sym('res', 368, 384, 'R0', 'R2', '200k')                  # A(384,400) B(384,480)
vline(384, 144, 272); vline(384, 272, 400); flag(300, 272, 'VSET')
hline(240, 384, 272)                                      # VSET left lead (to in+ channel)
vline(384, 480, 528); flag(384, 528, '0')

# ---- M2 shunt + Vdis + Rg (col x=592, flows down from VSET rail) ----
sym('nmos', 592, 240, 'R0', 'M2', 'nmosb')                # D(640,240) G(592,320) S(640,336)
hline(384, 640, 272); vline(640, 240, 272)                # drain up to VSET rail
vline(592, 320, 432); flag(656, 432, 'CURR_DIS')          # gate down; label on CURR_DIS rail
hline(592, 784, 432)                                      # CURR_DIS rail right to Rg.A
sym('voltage', 592, 496, 'R0', 'Vdis', 'PULSE(0 3.3 5m 10u 10u 5m 15m)')  # +(592,512) -(592,592)
vline(592, 432, 512)                                      # Vdis+ on gate rail (endpoint)
vline(592, 592, 640); flag(592, 640, '0')
vline(640, 336, 384); flag(640, 384, '0')
sym('res', 768, 416, 'R0', 'Rg', '1Meg')                  # A(784,432) B(784,512)
vline(784, 512, 560); flag(784, 560, '0')

# ---- Rsamp horizontal (T -> S), Rk1 vertical (col x=1216) ----
sym('res', 1216, 256, 'R90', 'Rsamp', '10k')              # B(1120,272) A(1200,272) horizontal
hline(1120, 1200, 272); hline(1200, 1648, 272)             # T rail split at Rsamp.A pin (pins need endpoints)
flag(1384, 272, 'T')                                       # T label mid-rail (horizontal)
vline(1200, 272, 304)                                     # Rsamp.A -> S node -> Rk1.A
flag(1200, 288, 'S')
sym('res', 1184, 288, 'R0', 'Rk1', '2')                   # A(1200,304) B(1200,384)
vline(1200, 384, 432)                                     # Rk1.B down to X rail

# ---- X rail: Rk1.B -> Vsm (M90) -> M1 drain ----
sym('nmos', 1472, 496, 'R0', 'M1', 'nmosb')               # D(1520,496) G(1472,576) S(1520,592)
sym('voltage', 1328, 432, 'M90', 'Vsm', '0')              # +(1344,432) -(1424,432)
hline(1200, 1344, 432); hline(1424, 1520, 432); vline(1520, 432, 496)
flag(1464, 432, 'X')

# ---- R3/R4 T-node bias (col x=1648, right of M1; T joins by net name) ----
sym('res', 1632, 176, 'R0', 'R3', '10k')                  # A(1648,192) B(1648,272)
flag(1648, 192, '3V3A')                                    # top pin joins 3V3A by net name
vline(1648, 272, 320); flag(1648, 296, 'T')                # R3.B -> R4.A, T node
sym('res', 1632, 304, 'R0', 'R4', '150k')                  # A(1648,320) B(1648,400)
vline(1648, 400, 448); flag(1648, 448, '0')

# ---- Rsense (col x=1520) ----
sym('res', 1504, 656, 'R0', 'Rsense', '150k')             # A(1520,672) B(1520,752)
vline(1520, 592, 672)                                     # M1.S -> Rsense.A
flag(1520, 656, 'B')
vline(1520, 752, 800); flag(1520, 800, '0')

# ---- Opamp U1 ----
sym('opamp', 1024, 608, 'R0', 'U1', 'opa333t3')           # in-(992,656) in+(992,688) out(1056,672)
# in- feed: B rail y=656 direct (through M1.S drop? no: rail spans 992..1520 at y=656,
# M1.S drop x=1520 ends at 656 = T-junction endpoint on rail)
hline(992, 1520, 656); flag(1264, 656, 'B')
# in+ feed: VSET -> x=240 -> y=736 -> x=992 -> pin (zero crossings)
vline(240, 272, 736); hline(240, 992, 736); vline(992, 688, 736)
flag(600, 736, 'VSET')
# out -> M1 gate (y=576)
vline(1056, 576, 672); hline(1056, 1472, 576); flag(1264, 576, 'VG')

# ---------------- emit ----------------
out = ["Version 4.1", "SHEET 1 1936 960"]
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
 "TEXT 112 880 Left 2 ;DE-DRMS constant current source (E.2/E.2.1): I = VSET/Rsense = 7.857uA",
 "TEXT 112 912 Left 2 ;VSET = 3.3V x 200k/560k (R1/R2) ; M1 BSS138 pass ; Rsense 150k source-to-GND",
 "TEXT 112 944 Left 2 ;T-node bias R3 10k + R4 150k (E.10#8) ; CURR_DIS: high -> M2 pulls VSET low",
 "TEXT 112 976 Left 2 ;U1 = macro opa333t3 (models.inc) ; Vsm = 0V ammeter ; Rg 1Meg = gate bleed (reset-safe)",
 "TEXT 112 1008 Left 2 ;Nets: 3V3A=analog rail ; VSET=1.179V ref ; T=sample top ; S=sample bottom ;",
 "TEXT 112 1040 Left 2 ;      X=M1 drain ; B=M1 source (=Rsense top, op-amp in-) ; VG=M1 gate",
 "TEXT 112 1104 Left 2 !.include models.inc",
 "TEXT 112 1136 Left 2 !.tran 15m",
 "TEXT 112 1168 Left 2 ;.ac dec 100 0.1 10meg",
]
open('ccsource.asc', 'w', encoding='ascii').write("\n".join(out) + "\n")
print(f"written: {len(W)} wires, {len(F)} flags, {len(S)} symbols")
