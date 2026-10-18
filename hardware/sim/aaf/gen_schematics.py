# -*- coding: utf-8 -*-
"""gen_schematics.py — 三个候选方案的图纸生成器
同一几何数据 → LTspice .asc（可打开运行）+ SVG 示意图（过门禁）+ @2x.png
LTspice 24 符号 PIN 表（实测 lib/sym/*.asy）：
  res: (16,16)/(16,96) 竖直；R90 后引脚 (x+96,y)/(x+16,y)（放置点 (x+112, y-16)）
  cap: (16,0)/(16,64) 竖直；voltage: (0,16)/(0,96) 竖直
"""
import subprocess, os, re

LT = r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
CHECKER = r"C:\Users\chenx\Desktop\de-drms\tools\svg_schematic_check.py"
NL = chr(10)
CRLF = chr(13) + chr(10)

CANDS = {
    "FIN1": {
        "cn": "方案 A · FIN1 二级（定稿推荐）",
        "spec": "DM@fMOD −123.5 dB · CM −105.5 · DM@MCLK −147.6 · 建立 0.01% 744 µs(wc) · 10 件/通道对",
        "stages": [(330, 47e-9, 47e-9), (2700, 6.8e-9, 5.6e-9)],
    },
    "V11": {
        "cn": "方案 B · V11 四级（加强保险位）",
        "spec": "DM@fMOD −153.7 dB · CM −129.9 · DM@MCLK −201.9 · 建立 0.01% 406 µs(wc) · 18 件/通道对",
        "stages": [(240, 6.8e-9, 0), (240, 6.8e-9, 10e-9), (240, 6.8e-9, 0), (240, 6.8e-9, 10e-9)],
    },
    "V10a": {
        "cn": "方案 C · V10a 六级（性能极限）",
        "spec": "DM@fMOD −199 dB · CM −171 · DM@MCLK −271 · 建立 0.01% 392 µs(wc) · 27 件/通道对",
        "stages": [(170, 4.7e-9, 0), (170, 4.7e-9, 6.8e-9), (170, 4.7e-9, 0),
                   (170, 4.7e-9, 6.8e-9), (170, 4.7e-9, 0), (170, 4.7e-9, 6.8e-9)],
    },
}

def fmtc(x):
    return f"{x*1e9:g}n"

def ymid(a, b):
    return (a + b) // 2

# ---------------- 几何 ----------------
def layout(stages):
    """每级基点 x_i：引脚 A=x_i+16、B=x_i+96；res SYMBOL at (x_i+112, y-16) R90；
    Ccm 挂引脚 A；Cdiff 桥跨级间线（xb = x_i+136）；级距 160"""
    yP, yN = 208, 408
    items = []
    wires = []
    x_src = 48
    x0 = 176
    wires.append((x_src, yP, x0 + 16, yP))
    wires.append((x_src, yN, x0 + 16, yN))
    x = x0
    for i, (r, ccm, cdf) in enumerate(stages):
        pa, pb = x + 16, x + 96
        items.append(("R", x + 112, yP, f"R{i+1}a", f"{r:g}"))
        items.append(("R", x + 112, yN, f"R{i+1}b", f"{r:g}"))
        items.append(("Ccm", pa, yP, f"C{i+1}a", fmtc(ccm)))
        items.append(("Ccm", pa, yN, f"C{i+1}b", fmtc(ccm)))
        xn = x + 160
        wires.append((pb, yP, xn + 16, yP))
        wires.append((pb, yN, xn + 16, yN))
        if cdf > 0:
            xb = x + 136
            items.append(("Cdiff", xb, 0, f"Cd{i+1}", fmtc(cdf)))
            wires.append((xb, yP, xb, ymid(yP, yN) - 32))
            wires.append((xb, ymid(yP, yN) + 32, xb, yN))
        x = xn
    out_x = x + 96 + 64
    wires.append((x + 96, yP, out_x, yP))
    wires.append((x + 96, yN, out_x, yN))
    return items, wires, (yP, yN, out_x)

# ---------------- .asc 生成 ----------------
def gen_asc(name, cand):
    stages = cand["stages"]
    items, wires, (yP, yN, out_x) = layout(stages)
    YMID = ymid(yP, yN)
    L = ["Version 4", "SHEET 1 1800 900"]
    L += ["SYMBOL voltage 48 192 R0", "SYMATTR InstName Vp",
          "SYMATTR Value PWL(0 -0.6  9.9u -0.6  10.4u 0.6  1.6m 0.6)",
          "SYMBOL voltage 48 392 R0", "SYMATTR InstName Vn",
          "SYMATTR Value PWL(0 0.6  9.9u 0.6  10.4u -0.6  1.6m -0.6)"]
    for (kind, x, y, ref, val) in items:
        if kind == "R":
            L += [f"SYMBOL res {x} {y - 16} R90", f"SYMATTR InstName {ref}", f"SYMATTR Value {val}"]
        elif kind == "Ccm":
            L += [f"SYMBOL cap {x - 16} {y} R0", f"SYMATTR InstName {ref}", f"SYMATTR Value {val}",
                  f"FLAG {x} {y + 64} AGND"]
        else:
            L += [f"SYMBOL cap {x - 16} {YMID - 32} R0", f"SYMATTR InstName {ref}", f"SYMATTR Value {val}"]
    wires.append((48, 288, 48, 320))
    wires.append((48, 488, 48, 520))
    for (x1, y1, x2, y2) in wires:
        L.append(f"WIRE {x1} {y1} {x2} {y2}")
    L += ["FLAG 48 320 0", "FLAG 48 520 0", "FLAG 48 208 sp", "FLAG 48 408 sn",
          f"FLAG {out_x} {yP} AIN0P", f"FLAG {out_x} {yN} AIN0N",
          f"TEXT {out_x - 60} 120 Left 2 !.tran 0 1.6m 0 200n"]
    open(f"{name}.asc", "w", newline=CRLF).write(CRLF.join(L) + CRLF)

# ---------------- SVG 生成 ----------------
def gen_svg(name, cand):
    stages = cand["stages"]
    items, wires, (yP, yN, out_x) = layout(stages)
    w = out_x + 250
    H = 720
    YMID = ymid(yP, yN)
    S = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{H}" viewBox="0 0 {w} {H}"',
         "     font-family=\"'Noto Sans CJK SC','Microsoft YaHei',sans-serif\">",
         '<rect width="100%" height="100%" fill="#ffffff"/>',
         f'<text x="36" y="52" font-size="24" font-weight="bold" fill="#111827">{cand["cn"]} — 抗混叠滤波（每通道对，ch1 同构）</text>',
         f'<text x="36" y="80" font-size="12.5" fill="#64748b">{cand["spec"]}</text>',
         f'<text x="{w-36}" y="104" font-size="11" fill="#94a3b8" text-anchor="end">C 全 C0G · R 1% · 四线同构（E 线镜像）· 2026-10-18</text>',
         f'<text x="120" y="{yP-14}" font-size="12" font-weight="bold" fill="#111827" text-anchor="end">跟随器输出 +</text>',
         f'<text x="120" y="{yN-14}" font-size="12" font-weight="bold" fill="#111827" text-anchor="end">跟随器输出 −</text>']
    for (x1, y1, x2, y2) in wires:
        color = "#374151"
        S.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="2"/>')
    for (kind, x, y, ref, val) in items:
        if kind == "R":
            S += [f'<rect x="{x+16}" y="{y-14}" width="80" height="28" rx="2" fill="#f1f5f9" stroke="#374151" stroke-width="1.8"/>',
                  f'<text x="{x+56}" y="{y-20}" font-size="12" font-weight="bold" fill="#374151" text-anchor="middle">{val}Ω</text>']
        elif kind == "Ccm":
            S += [f'<circle cx="{x}" cy="{y}" r="4" fill="#111827"/>',
                  f'<line x1="{x}" y1="{y}" x2="{x}" y2="{y+46}" stroke="#374151" stroke-width="2"/>',
                  f'<rect x="{x-14}" y="{y+46}" width="28" height="22" rx="2" fill="#f1f5f9" stroke="#374151" stroke-width="1.8"/>',
                  f'<text x="{x+22}" y="{y+62}" font-size="11" fill="#374151">{val}F</text>',
                  f'<line x1="{x}" y1="{y+68}" x2="{x}" y2="{y+78}" stroke="#374151" stroke-width="2"/>',
                  f'<line x1="{x-14}" y1="{y+78}" x2="{x+14}" y2="{y+78}" stroke="#374151" stroke-width="2.4"/>',
                  f'<line x1="{x-9}" y1="{y+84}" x2="{x+9}" y2="{y+84}" stroke="#374151" stroke-width="1.8"/>',
                  f'<line x1="{x-4}" y1="{y+90}" x2="{x+4}" y2="{y+90}" stroke="#374151" stroke-width="1.6"/>',
                  f'<text x="{x+18}" y="{y+90}" font-size="10" fill="#6b7280">AGND</text>']
        else:
            S += [f'<circle cx="{x}" cy="{yP}" r="4" fill="#111827"/>',
                  f'<circle cx="{x}" cy="{yN}" r="4" fill="#111827"/>',
                  f'<line x1="{x}" y1="{yP}" x2="{x}" y2="{YMID-30}" stroke="#2563eb" stroke-width="2"/>',
                  f'<rect x="{x-14}" y="{YMID-30}" width="28" height="22" rx="2" fill="#eff6ff" stroke="#2563eb" stroke-width="1.8"/>',
                  f'<line x1="{x}" y1="{YMID-8}" x2="{x}" y2="{YMID+8}" stroke="#2563eb" stroke-width="2"/>',
                  f'<rect x="{x-14}" y="{YMID+8}" width="28" height="22" rx="2" fill="#eff6ff" stroke="#2563eb" stroke-width="1.8"/>',
                  f'<line x1="{x}" y1="{YMID+30}" x2="{x}" y2="{yN}" stroke="#2563eb" stroke-width="2"/>',
                  f'<text x="{x+22}" y="{YMID+46}" font-size="11" font-weight="bold" fill="#2563eb">{val}F</text>']
    S += [f'<rect x="{out_x}" y="{yP-70}" width="170" height="{yN-yP+140}" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="2"/>',
          f'<text x="{out_x+85}" y="{yP-36}" font-size="14" font-weight="bold" fill="#1d4ed8" text-anchor="middle">ADS131A02</text>',
          f'<text x="{out_x+6}" y="{yP+4}" font-size="11" font-weight="bold" fill="#1e3a8a">AIN0P</text>',
          f'<text x="{out_x+6}" y="{yN+4}" font-size="11" font-weight="bold" fill="#1e3a8a">AIN0N</text>',
          f'<text x="{out_x+85}" y="{yN+40}" font-size="10" fill="#1e3a8a" text-anchor="middle">ch1 同构：B/E → AIN1P/AIN1N</text>']
    chain = " → ".join(f"{s[0]}Ω({fmtc(s[1])}‖{fmtc(s[2])}差分)" for s in stages)
    S += [f'<text x="36" y="{H-58}" font-size="11" fill="#374151">结构：跟随器输出 → {chain} → ADS131A02。级间/引脚节点各挂对地 Ccm，差分 Cd 跨两线（蓝色）。</text>',
          f'<text x="36" y="{H-36}" font-size="11" fill="#64748b">全部无源 R/C：C0G，四线同构（E 线镜像）；建立/衰减指标见 README 第四、五、六轮。</text>',
          '</svg>']
    return NL.join(S)

# ---------------- 主流程 ----------------
for name, cand in CANDS.items():
    gen_asc(name, cand)
    svgf = f"图纸_{name}_抗混叠.svg"
    open(svgf, "w", encoding="utf-8", newline=NL).write(gen_svg(name, cand))
    r = subprocess.run(["python", CHECKER, svgf, "--font", r"C:\Windows\Fonts\msyh.ttc"],
                       capture_output=True, text=True)
    verdict = [l for l in r.stdout.splitlines() if l.startswith("结论")]
    print(name, verdict[0] if verdict else "checker 无输出")
    if verdict and "PASS" not in verdict[0]:
        print(r.stdout[-1200:])

import re
from PIL import Image
for name in CANDS:
    svgf = f"图纸_{name}_抗混叠.svg"
    svg = open(svgf, encoding="utf-8").read()
    m = re.search(r'width="(\d+)" height="(\d+)"', svg)
    w, h = m.group(1), m.group(2)
    html = ('<!doctype html><html><head><meta charset="utf-8">'
            '<style>html,body{margin:0;padding:0}svg{display:block}</style></head><body>'
            + svg + '</body></html>')
    open(".tmp_r.html", "w", encoding="utf-8").write(html)
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--force-device-scale-factor=2",
                    f"--screenshot={os.path.abspath(f'图纸_{name}_抗混叠@2x.png')}",
                    f"--window-size={w},{h}", "--default-background-color=FFFFFFFF",
                    "file:///" + os.path.abspath(".tmp_r.html").replace("\\", "/")],
                   capture_output=True, timeout=120)
    print(name, "png", Image.open(f"图纸_{name}_抗混叠@2x.png").size)
if os.path.exists(".tmp_r.html"):
    os.remove(".tmp_r.html")
