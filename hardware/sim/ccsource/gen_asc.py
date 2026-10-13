#!/usr/bin/env python3
"""Generate ccsource.asc - LTspice schematic of the finalized DE-DRMS current source.
Layout v2 (readability): horizontal labels (default windows), 256px column pitch,
short per-drop ground flags, signal left-to-right.
Pin offsets: res A(16,16) B(16,96); voltage +(0,16) -(0,96); nmos D(48,0) G(0,80) S(48,96);
opamp (OpAmps/opamp.asy) invin(-32,48) noninvin(-32,80) out(32,64). M90: (x+py, y+px)."""
W, F, S = [], [], []
def wire(x1, y1, x2, y2):
    assert x1 == x2 or y1 == y2, f"diagonal {x1},{y1}->{x2},{y2}"
    if (x1, y1) != (x2, y2): W.append(f"WIRE {x1} {y1} {x2} {y2}")
def hline(x1, x2, y): wire(x1, y, x2, y)
def vline(x, y1, y2): wire(x, y1, x, y2)
def flag(x, y, net): F.append(f"FLAG {x} {y} {net}")
def sym(name, x, y, rot, inst, val):
    S.append((name, x, y, rot, inst, val))

TA = 160                       # top rail (3.3V_A)

# --- V1 supply ---
sym('voltage', 112, 368, 'R0', 'V1', '3.3')            # +(112,384) -(112,464)
vline(112, 160, 384); vline(112, 464, 528)
hline(112, 384, TA)                                    # TA rail segment 1
hline(384, 960, TA)                                    # TA rail segment 2 (split at R1.A)
flag(112, TA, 'TA'); flag(384, TA, 'TA'); flag(960, TA, 'TA')
flag(112, 528, '0')

# --- R1/R2 VSET divider (column x=384) ---
sym('res', 368, 144, 'R0', 'R1', '360k')               # A(384,160) B(384,240)
sym('res', 368, 480, 'R0', 'R2', '200k')               # A(384,496) B(384,576)
vline(384, 240, 368); vline(384, 368, 496)              # split at VSET node
flag(384, 368, 'VSET')
vline(384, 576, 640); flag(384, 640, '0')

# --- M2 CURR_DIS + Vdis + Rg (column x=624) ---
sym('nmos', 624, 464, 'R0', 'M2', 'nmosb')             # D(672,464) G(624,544) S(672,560)
vline(672, 368, 464); hline(384, 672, 368)              # drain to VSET rail
sym('voltage', 624, 656, 'R0', 'Vdis', 'PULSE(0 3.3 5m 10u 10u 5m 15m)')  # +(624,672) -(624,752)
vline(624, 544, 672); flag(624, 672, 'VDIS')            # gate down to Vdis+ (pin flag)
vline(672, 560, 624); flag(672, 624, '0')               # source to GND
vline(624, 752, 816); flag(624, 816, '0')               # Vdis- to GND
# Rg gate pulldown, routed via x=592 (clear of Vdis body x=624..672)
sym('res', 768, 944, 'R0', 'Rg', '1meg')               # A(784,960) B(784,1040)
hline(592, 624, 544)                                    # gate stub left
vline(592, 544, 960); hline(592, 784, 960)              # down and across to Rg.A
vline(784, 1040, 1104); flag(784, 1104, '0')

# --- R3/R4 T-node bias (column x=960) ---
sym('res', 944, 144, 'R0', 'R3', '10k')                # A(960,160) B(960,240)
sym('res', 944, 480, 'R0', 'R4', '150k')               # A(960,496) B(960,576)
vline(960, 240, 368); vline(960, 368, 496)
flag(960, 368, 'T')
vline(960, 576, 640); flag(960, 640, '0')

# --- Rsamp load + Rk1 (column x=1248) ---
sym('res', 1232, 304, 'R0', 'Rsamp', '10k')            # A(1248,320) B(1248,400)
hline(960, 1248, 368); vline(1248, 320, 368)            # T rail to Rsamp top
flag(1248, 368, 'T')
sym('res', 1232, 480, 'R0', 'Rk1', '2')                # A(1248,496) B(1248,576)
vline(1248, 400, 496); flag(1248, 448, 'SN')

# --- X rail: Rk1.B -> Vsm (ammeter, M90) -> M1 drain ---
sym('nmos', 1552, 656, 'R0', 'M1', 'nmosb')            # D(1600,656) G(1552,736) S(1600,752)
sym('voltage', 1408, 624, 'M90', 'Vsm', '0')           # +(1424,624) -(1504,624)
vline(1248, 576, 624)
hline(1248, 1424, 624)                                  # Rk1.B -> Vsm(+)
hline(1504, 1600, 624); vline(1600, 624, 656)           # Vsm(-) -> M1 drain
flag(1600, 624, 'X')

# --- Rsense source-to-GND (column x=1568) ---
sym('res', 1552, 848, 'R0', 'Rsense', '150k')          # A(1568,864) B(1568,944)
vline(1600, 752, 816); vline(1600, 816, 864); hline(1568, 1600, 864)
flag(1600, 816, 'B'); flag(1568, 864, 'B')
vline(1568, 944, 1008); flag(1568, 1008, '0')

# --- Opamp U1: in+=VSET, in-=B, out=M1 gate ---
sym('opamp', 1104, 688, 'R0', 'U1', 'opa333t3')        # in-(1072,736) in+(1072,768) out(1136,752)
# in+ feed: VSET -> left x=240 -> down y=880 -> right x=1008 -> up y=768 -> pin
hline(240, 384, 368); vline(240, 368, 880); hline(240, 1008, 880)
vline(1008, 768, 880); hline(1008, 1072, 768)
flag(240, 368, 'VSET'); flag(1072, 768, 'VSET')
# in- feed: B tap -> rail y=816 -> left x=1040 -> up y=736 -> pin (x=1040 crosses in+ mid-span: no join)
hline(1040, 1600, 816); vline(1040, 736, 816); hline(1040, 1072, 736)
flag(1072, 736, 'B')
# out -> M1 gate
hline(1136, 1552, 752); vline(1552, 736, 752); flag(1552, 736, 'VG')

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
 "TEXT 112 1200 Left 2 ;DE-DRMS constant current source (E.2/E.2.1): I = VSET/Rsense = 7.857uA",
 "TEXT 112 1232 Left 2 ;VSET = 3.3V x 200k/560k (R1/R2) ; M1 BSS138 pass ; Rsense 150k source-to-GND",
 "TEXT 112 1264 Left 2 ;T-node bias R3 10k + R4 150k (E.10#8) ; CURR_DIS: Vdis high -> M2 pulls VSET low",
 "TEXT 112 1296 Left 2 ;U1 = behavioral macro opa333t3 (models.inc) ; Vsm = 0V ammeter (probe I(Vsm))",
 "TEXT 112 1360 Left 2 !.include models.inc",
 "TEXT 112 1392 Left 2 !.tran 15m",
 "TEXT 112 1424 Left 2 ;.ac dec 100 0.1 10meg",
]
open('ccsource.asc', 'w', encoding='ascii').write("\n".join(out) + "\n")
print(f"written: {len(W)} wires, {len(F)} flags, {len(S)} symbols")
