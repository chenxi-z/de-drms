#!/usr/bin/env python3
"""Generate ccsource.asc - LTspice schematic, finalized DE-DRMS current source.
Layout v3: compact zones (left V1+VSET+shunt / mid T-bias / right load+M1+U1),
feedback routed adjacent to opamp, uniform 48px ground drops, zero mid-crossings.
Pin offsets: res A(16,16) B(16,96); voltage +(0,16) -(0,96); nmos D(48,0) G(0,80) S(48,96);
opamp invin(-32,48) noninvin(-32,80) out(32,64). M90: world=(x+py, y+px)."""
W, F, S = [], [], []
def wire(x1, y1, x2, y2):
    assert x1 == x2 or y1 == y2, f"diagonal {x1},{y1}->{x2},{y2}"
    if (x1, y1) != (x2, y2): W.append(f"WIRE {x1} {y1} {x2} {y2}")
def hline(x1, x2, y): wire(x1, y, x2, y)
def vline(x, y1, y2): wire(x, y1, x, y2)
def flag(x, y, net): F.append(f"FLAG {x} {y} {net}")
def sym(name, x, y, rot, inst, val): S.append((name, x, y, rot, inst, val))

# ---- V1 + TA rail ----
sym('voltage', 112, 368, 'R0', 'V1', '3.3')             # +(112,384) -(112,464)
vline(112, 160, 384); vline(112, 464, 512); flag(112, 512, '0')
hline(112, 384, 160); hline(384, 960, 160)               # TA rail (split at R1.A)
flag(112, 160, '3V3A'); flag(384, 160, '3V3A'); flag(960, 160, '3V3A')

# ---- R1/R2 VSET divider (col x=384) ----
sym('res', 368, 144, 'R0', 'R1', '360k')                 # A(384,160) B(384,240)
sym('res', 368, 480, 'R0', 'R2', '200k')                 # A(384,496) B(384,576)
vline(384, 240, 368); vline(384, 368, 496); flag(384, 368, 'VSET')
vline(384, 576, 624); flag(384, 624, '0')

# ---- M2 shunt + Vdis + Rg (col x=624, Rg right) ----
sym('nmos', 624, 464, 'R0', 'M2', 'nmosb')               # D(672,464) G(624,544) S(672,560)
vline(672, 368, 464); hline(384, 672, 368)                # drain up to VSET rail
vline(624, 544, 688); vline(624, 688, 736); flag(728, 688, 'CURR_DIS')  # gate down (split at branch point)
sym('voltage', 624, 720, 'R0', 'Vdis', 'PULSE(0 3.3 5m 10u 10u 5m 15m)')  # +(624,736) -(624,816)
vline(624, 816, 880); flag(624, 880, '0')
vline(672, 560, 608); flag(672, 608, '0')
hline(624, 832, 688)                                      # gate branch right at y=688 (above Vdis body 720..)
sym('res', 816, 672, 'R0', 'Rg', '1Meg')                  # A(832,688) B(832,768)
vline(832, 768, 816); flag(832, 816, '0')

# ---- R3/R4 T-node bias (col x=960) ----
sym('res', 944, 144, 'R0', 'R3', '10k')                  # A(960,160) B(960,240)
sym('res', 944, 480, 'R0', 'R4', '150k')                 # A(960,496) B(960,576)
vline(960, 240, 368); vline(960, 368, 496); flag(960, 368, 'T')
vline(960, 576, 640); flag(960, 640, '0')

# ---- Rsamp load + Rk1 (col x=1248) ----
sym('res', 1232, 304, 'R0', 'Rsamp', '10k')              # A(1248,320) B(1248,400)
hline(960, 1248, 368); vline(1248, 320, 368); flag(1248, 368, 'T')
sym('res', 1232, 480, 'R0', 'Rk1', '2')                  # A(1248,496) B(1248,576)
vline(1248, 400, 496); flag(1248, 448, 'S')

# ---- X rail: Rk1.B -> Vsm -> M1 drain ----
sym('nmos', 1552, 656, 'R0', 'M1', 'nmosb')              # D(1600,656) G(1552,736) S(1600,752)
sym('voltage', 1408, 624, 'M90', 'Vsm', '0')             # +(1424,624) -(1504,624)
vline(1248, 576, 624)
hline(1248, 1424, 624); hline(1504, 1600, 624); vline(1600, 624, 656)
flag(1552, 624, 'X')

# ---- Rsense (col x=1568) ----
sym('res', 1552, 848, 'R0', 'Rsense', '150k')            # A(1568,864) B(1568,944)
vline(1600, 752, 864); hline(1568, 1600, 864)            # M1.S stub split at B rail y=864
flag(1300, 864, 'B')
vline(1568, 944, 992); flag(1568, 992, '0')

# ---- Opamp U1 (between load column and M1) ----
sym('opamp', 1104, 688, 'R0', 'U1', 'opa333t3')          # in-(1072,736) in+(1072,768) out(1136,752)
# in+ feed: VSET -> x=240 -> y=936 -> x=1072 -> pin (zero crossings)
hline(240, 384, 368); vline(240, 368, 936); hline(240, 1072, 936); vline(1072, 768, 936)
flag(240, 368, 'VSET'); flag(900, 768, 'VSET')
# in- feed: B rail y=864; drop at x=1040 (parallel to in+ rise at x=1072, NOT collinear)
hline(1040, 1072, 736); vline(1040, 736, 864); hline(1040, 1600, 864)
flag(1072, 736, 'B')
# out -> M1 gate (y=800)
vline(1136, 752, 800); hline(1136, 1552, 800); vline(1552, 736, 800); flag(1344, 800, 'VG')

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
for name, x, y, rot, inst, val in S:
    out.append(f"SYMBOL {name} {x} {y} {rot}")
    out.append(f"SYMATTR InstName {inst}")
    out.append(f"SYMATTR Value {val}")
out += [
 "TEXT 112 1168 Left 2 ;DE-DRMS constant current source (E.2/E.2.1): I = VSET/Rsense = 7.857uA",
 "TEXT 112 1200 Left 2 ;VSET = 3.3V x 200k/560k (R1/R2) ; M1 BSS138 pass ; Rsense 150k source-to-GND",
 "TEXT 112 1232 Left 2 ;T-node bias R3 10k + R4 150k (E.10#8) ; CURR_DIS: Vdis high -> M2 pulls VSET low",
 "TEXT 112 1264 Left 2 ;U1 = behavioral macro opa333t3 (models.inc) ; Vsm = 0V ammeter (probe I(Vsm))",
 "TEXT 112 1296 Left 2 ;Rg 1Meg = gate bleed: PB10 floating/high-Z -> gate=0 -> M2 OFF -> excitation ON (reset-safe)",
 "TEXT 112 1296 Left 2 ;",
 "TEXT 112 1296 Left 2 ;Nets: 3V3A=analog rail ; VSET=1.179V ref ; T=sample top (biased 3.0V) ; S=sample bottom ;",
 "TEXT 112 1296 Left 2 ;      X=M1 drain ; B=M1 source (=Rsense top, op-amp in-) ; VG=M1 gate ; CURR_DIS=shunt gate",
 "TEXT 112 1296 Left 2 ;Feedback: U1.in+ = VSET (from divider, routed along bottom) ; U1.in- = B (short rail y=864)",
 "TEXT 112 1328 Left 2 !.include models.inc",
 "TEXT 112 1360 Left 2 !.tran 15m",
 "TEXT 112 1392 Left 2 ;.ac dec 100 0.1 10meg",
]
open('ccsource.asc', 'w', encoding='ascii').write("\n".join(out) + "\n")
print(f"written: {len(W)} wires, {len(F)} flags, {len(S)} symbols")
