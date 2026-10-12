#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""svg_schematic_check.py — 电路/架构示意图（SVG）交付前自动体检。

为什么需要它：示意图的典型缺陷（标签重叠/溢出、缺字渲染成豆腐块、
箭头被 markerUnits 放大、三路交汇漏结点、不该连的线交叉处画了结点）
肉眼很难逐张确认，且改一处容易破坏另一处。本脚本把这些检查一次性跑完，
可作为提交前的门禁：有 ERROR 时退出码非 0。

用法:
    python3 tools/svg_schematic_check.py docs/design/diagram/xxx.svg
    python3 tools/svg_schematic_check.py xxx.svg --font /path/to/font.ttc
    python3 tools/svg_schematic_check.py xxx.svg --no-font-check   # 无 PIL 时

检查项:
    1. XML 是否合法
    2. 文本包围盒：两两重叠、超出 viewBox（中文字宽按 1.0 em、西文 0.56 em 估算）
    3. 缺字（豆腐块）：用 PIL 渲染每个非 ASCII 字符，与私用区字符位图比对
    4. marker 缩放陷阱：未写 markerUnits="userSpaceOnUse" 的箭头会随 stroke-width 放大
    5. 结点审计：三路交汇处必须有点；交叉处不该有点（符号内部元素只提示不报错）

约定（与本仓库 docs/design/diagram/ 下的图一致）:
    class="w/wr"   普通导线 / 电源轨·母线
    class="gw/ow"  高亮电流路径（绿=测量、橙=校准）
    class="gd"     灰虚线（未选中支路）
    class="p"      紫色虚线控制线
    class="sym"    符号内部线条（刀臂、二极管、接地/电源符号）——不做结点判定
    结点用 <circle fill!="#ffffff"> 画；器件端子用白底圆（会被忽略）
"""

from __future__ import annotations

import argparse
import math
import re
import subprocess
import sys
import unicodedata
import xml.etree.ElementTree as ET

WIRE_CLASSES = {"w", "wr", "gw", "ow", "gd", "p", "sym"}
DEFAULT_FONTS = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
]
CJK_FACTOR, LATIN_FACTOR = 1.0, 0.56  # 字宽估算系数（× font-size）


def err(msg: str) -> None:
    print(f"  [ERROR] {msg}")


def warn(msg: str) -> None:
    print(f"  [WARN ] {msg}")


def info(msg: str) -> None:
    print(f"  [info ] {msg}")


# ---------------------------------------------------------------- 文本

def text_items(src: str):
    """返回 [(x0, y0, w, h, text, line_no)]，坐标为估算包围盒左上角。"""
    items = []
    for m in re.finditer(r"<text([^>]*)>(.*?)</text>", src, re.S):
        attrs, inner = m.group(1), m.group(2)
        line = src[: m.start()].count("\n") + 1

        def g(key, default=None):
            mm = re.search(key + r'="([^"]*)"', attrs)
            return mm.group(1) if mm else default

        x, y = float(g("x", 0)), float(g("y", 0))
        fs = float(g("font-size", 12))
        anchor = g("text-anchor", "start")

        text, cur = "", fs
        for part in re.split(r"(<tspan[^>]*>|</tspan>)", inner):
            if part.startswith("<tspan"):
                mm = re.search(r'font-size="([\d.]+)"', part)
                cur = float(mm.group(1)) if mm else fs
            elif part == "</tspan>":
                cur = fs
            elif part:
                text += part
        if not text.strip():
            continue
        width = sum(
            (CJK_FACTOR if unicodedata.east_asian_width(c) in "WF" else LATIN_FACTOR) * fs
            for c in text
        )
        x0 = x - width / 2 if anchor == "middle" else (x - width if anchor == "end" else x)
        items.append((x0, y - fs * 0.82, width, fs * 1.05, text.strip(), line))
    return items


def check_text(src, vb, tol=25.0):
    items = text_items(src)
    bad = 0
    for i, a in enumerate(items):
        if a[0] < vb[0] - 1 or a[0] + a[2] > vb[0] + vb[2] + 1 or a[1] < vb[1] - 1 or a[1] + a[3] > vb[1] + vb[3] + 1:
            err(f"文本越界 L{a[5]}: {a[4][:32]!r} box=({a[0]:.0f},{a[1]:.0f},{a[2]:.0f},{a[3]:.0f})")
            bad += 1
        for b in items[i + 1:]:
            ix = min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0])
            iy = min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1])
            if ix > 0 and iy > 0 and ix * iy > tol:
                err(f"文本重叠 L{a[5]}/L{b[5]}: {a[4][:24]!r} <-> {b[4][:24]!r} (重叠 {ix*iy:.0f}px²)")
                bad += 1
    print(f"  文本 {len(items)} 个，重叠/越界 {bad} 处")
    return bad


def _clip_chord(p0, p1, rect):
    """Liang–Barsky：返回线段落在 rect 内的弦长，无交返回 0。"""
    x0, y0, x1, y1 = rect
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, p0[0] - x0), (dx, x1 - p0[0]), (-dy, p0[1] - y0), (dy, y1 - p0[1])):
        if p == 0:
            if q < 0:
                return 0.0
        else:
            t = q / p
            if p < 0:
                t0 = max(t0, t)
            else:
                t1 = min(t1, t)
            if t0 > t1:
                return 0.0
    return math.hypot(dx, dy) * (t1 - t0)


def check_text_vs_wires(src, inset=2.0, min_chord=3.5):
    """文字被导线/矩形边框穿过（逐字素 ink 包围盒 vs 线段，含缩进判定，避免只擦边）。"""
    items = text_items(src)
    obstacles = []
    for m in re.finditer(r"<line([^>]*)/>", src):
        a = m.group(1)
        g = lambda k: (re.search(k + r'="(-?[\d.]+)"', a) or [None, None])[1]
        if None in (g("x1"), g("y1"), g("x2"), g("y2")):
            continue
        obstacles.append(((float(g("x1")), float(g("y1"))), (float(g("x2")), float(g("y2"))),
                          f"line L{src[:m.start()].count(chr(10)) + 1}"))
    for m in re.finditer(r'<polyline([^>]*)/>', src):
        a = m.group(1)
        pts = re.search(r'points="([^"]*)"', a)
        if not pts:
            continue
        nums = [float(v) for v in re.findall(r"-?[\d.]+", pts.group(1))]
        ln = src[: m.start()].count("\n") + 1
        for i in range(0, len(nums) - 2, 2):
            obstacles.append(((nums[i], nums[i + 1]), (nums[i + 2], nums[i + 3]), f"polyline L{ln}"))
    for m in re.finditer(r'<path d="M([\d.]+),([\d.]+) Q[^"]*?([\d.]+),([\d.]+)"', src):
        obstacles.append(((float(m.group(1)), float(m.group(2))), (float(m.group(3)), float(m.group(4))),
                          f"hop L{src[:m.start()].count(chr(10)) + 1}"))
    for m in re.finditer(r"<rect([^>]*)/>", src):
        a = m.group(1)
        try:
            x = float(re.search(r'x="(-?[\d.]+)"', a).group(1))
            y = float(re.search(r'y="(-?[\d.]+)"', a).group(1))
            w = float(re.search(r'width="([\d.]+)"', a).group(1))
            h = float(re.search(r'height="([\d.]+)"', a).group(1))
        except AttributeError:
            continue
        ln = src[: m.start()].count("\n") + 1
        for p0, p1 in (((x, y), (x + w, y)), ((x + w, y), (x + w, y + h)),
                       ((x + w, y + h), (x, y + h)), ((x, y + h), (x, y))):
            obstacles.append((p0, p1, f"rect边框 L{ln}"))

    bad = 0
    for (tx, ty, tw, th, text, line) in items:
        box = (tx + inset, ty + inset, tx + tw - inset, ty + th - inset)
        if box[2] <= box[0] or box[3] <= box[1]:
            continue
        hits = set()
        for p0, p1, tag in obstacles:
            if _clip_chord(p0, p1, box) > min_chord:
                hits.add(tag.split()[0] + " " + tag.split()[1])
        if hits:
            err(f"文字被线穿过 L{line}: {text[:26]!r} ← {', '.join(sorted(hits)[:3])}")
            bad += 1
    print(f"  文字被线穿过 {bad} 处")
    return bad


# ---------------------------------------------------------------- 字形

def find_font(explicit=None):
    if explicit:
        return explicit
    for p in DEFAULT_FONTS:
        try:
            open(p, "rb").close()
            return p
        except OSError:
            continue
    try:
        out = subprocess.run(["fc-match", "-f", "%{file}", "Noto Sans CJK SC"],
                             capture_output=True, text=True, timeout=10).stdout.strip()
        return out or None
    except Exception:
        return None


def check_glyphs(src, font_path):
    """渲染每个非 ASCII 字符，与私用区字符位图比对 → 相同即为豆腐块。"""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        warn("未安装 PIL，跳过缺字检查")
        return 0
    if not font_path:
        warn("未找到中文字体，跳过缺字检查")
        return 0
    try:
        f = ImageFont.truetype(font_path, 32)
    except OSError as e:
        warn(f"字体加载失败（{e}），跳过缺字检查")
        return 0

    def bitmap(ch):
        im = Image.new("L", (48, 48), 0)
        ImageDraw.Draw(im).text((4, 4), ch, font=f, fill=255)
        return im.tobytes()

    missing_ref = bitmap("\ue123")  # 私用区，字体通常无此字形
    bad_chars = {}
    for m in re.finditer(r"<text[^>]*>(.*?)</text>", src, re.S):
        body = re.sub(r"<[^>]+>", "", m.group(1))
        for ch in body:
            if ord(ch) < 128 or ch in bad_chars:
                continue
            if bitmap(ch) == missing_ref:
                bad_chars[ch] = ord(ch)
    for ch, cp in bad_chars.items():
        err(f"缺字（会渲染成豆腐块）: {ch!r} U+{cp:04X}")
    print(f"  缺字检查 {len(bad_chars)} 个（字体 {font_path.split('/')[-1]}）")
    return len(bad_chars)


# ---------------------------------------------------------------- marker

def check_markers(src):
    bad = 0
    markers = re.findall(r"<marker([^>]*)>(.*?)</marker>", src, re.S)
    if not markers:
        return 0
    # 统计每个 marker 被哪些线宽的元素引用
    widths = {}
    for m in re.finditer(r'<[^>]*?(?:marker-end|marker-start)="url\(#([^)]+)\)"[^>]*>', src):
        el, name = m.group(0), m.group(1)
        wm = re.search(r'stroke-width="([\d.]+)"', el)
        widths.setdefault(name, set()).add(float(wm.group(1)) if wm else 1.0)
    for attrs, body in markers:
        name = (re.search(r'id="([^"]+)"', attrs) or [None, "?"])[1]
        if 'markerUnits="userSpaceOnUse"' in attrs:
            continue
        nums = [float(v) for v in re.findall(r"-?[\d.]+", body)]
        xs = nums[0::2]
        length = (max(xs) - min(xs)) if xs else 8.0
        scale = max(widths.get(name, {1.0}))
        eff = length * scale
        if scale >= 3:
            err(f'marker #{name} 未设 markerUnits="userSpaceOnUse"：'
                f'箭头随引用线宽 {scale:g} 放大到约 {eff:.0f}px（明显过大），改用固定尺寸')
            bad += 1
        elif scale >= 2:
            warn(f'marker #{name} 按线宽 {scale:g} 放大到约 {eff:.0f}px，'
                 f'尚可但建议改 markerUnits="userSpaceOnUse" 固定尺寸')
        else:
            info(f'marker #{name} 未固定尺寸（放大 {scale:g}×，约 {eff:.0f}px），影响很小')
    print(f"  marker {len(markers)} 个，明显放大 {bad} 个")
    return bad


# ---------------------------------------------------------------- 结点

def segments(src):
    """收集带 class 的连线为线段；返回 [(x1,y1,x2,y2,class,line_no)]。"""
    segs = []
    for m in re.finditer(r"<line([^>]*)/>", src):
        a = m.group(1)
        cm = re.search(r'class="([^"]*)"', a)
        if not cm or cm.group(1) not in WIRE_CLASSES:
            continue
        vals = {}
        for k in ("x1", "y1", "x2", "y2"):
            mm = re.search(k + r'="(-?[\d.]+)"', a)
            if not mm:
                break
            vals[k] = float(mm.group(1))
        else:
            segs.append((vals["x1"], vals["y1"], vals["x2"], vals["y2"],
                         cm.group(1), src[: m.start()].count("\n") + 1))
    for m in re.finditer(r'<polyline([^>]*)/>', src):
        a = m.group(1)
        cm = re.search(r'class="([^"]*)"', a)
        pts = re.search(r'points="([^"]*)"', a)
        if not cm or cm.group(1) not in WIRE_CLASSES or not pts:
            continue
        nums = [float(v) for v in re.findall(r"-?[\d.]+", pts.group(1))]
        line = src[: m.start()].count("\n") + 1
        for i in range(0, len(nums) - 2, 2):
            segs.append((nums[i], nums[i + 1], nums[i + 2], nums[i + 3], cm.group(1), line))
    # 二次贝塞尔“跳线”按直线桥接处理（跨越不连接处画的小弧）
    for m in re.finditer(r'<path d="M([\d.]+),([\d.]+) Q[^"]*?([\d.]+),([\d.]+)"', src):
        segs.append((float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4)),
                     "w", src[: m.start()].count("\n") + 1))
    return segs


def dots(src):
    pts = []
    for m in re.finditer(r"<circle([^>]*)/>", src):
        a = m.group(1)
        fill = (re.search(r'fill="([^"]*)"', a) or [None, "#000"])[1]
        r = re.search(r'r="([\d.]+)"', a)
        if fill.lower() == "#ffffff" or not r or float(r.group(1)) > 6:
            continue  # 白底圆 = 器件端子，不是结点
        cx = re.search(r'cx="(-?[\d.]+)"', a)
        cy = re.search(r'cy="(-?[\d.]+)"', a)
        if cx and cy:
            pts.append((float(cx.group(1)), float(cy.group(1))))
    return pts


def on_seg(px, py, s, tol=0.6):
    x1, y1, x2, y2 = s[:4]
    dx, dy = x2 - x1, y2 - y1
    l2 = dx * dx + dy * dy
    if l2 == 0:
        return None
    t = ((px - x1) * dx + (py - y1) * dy) / l2
    if not (-1e-9 <= t <= 1 + 1e-9):
        return None
    if math.hypot(px - (x1 + t * dx), py - (y1 + t * dy)) > tol:
        return None
    return t


def check_junctions(src):
    segs, ds = segments(src), dots(src)
    if not segs:
        print("  未识别到带 class 的导线（本图可能用 <path> 画线）→ 跳过结点判定")
        return 0
    bad = 0
    # 三路交汇：一条线的端点落在另一条线内部 → 必须有结点
    for i, s in enumerate(segs):
        for px, py in ((s[0], s[1]), (s[2], s[3])):
            for j, t in enumerate(segs):
                if i == j:
                    continue
                tt = on_seg(px, py, t)
                if tt is None or tt < 1e-6 or tt > 1 - 1e-6:
                    continue
                has_dot = any(math.hypot(px - dx, py - dy) <= 3.5 for dx, dy in ds)
                if not has_dot:
                    if "sym" in (s[4], t[4]):
                        info(f"符号内部交汇无结点 ({px:.0f},{py:.0f}) L{s[5]}/{t[5]}（多半是接地/电源符号，可忽略）")
                    else:
                        err(f"三路交汇漏结点 ({px:.0f},{py:.0f}) L{s[5]}[{s[4]}] 落在 L{t[5]}[{t[4]}] 上")
                        bad += 1
    # 星形交汇：≥3 条线段的端点落在同一点 → 必须有结点
    clusters = {}
    for i, s in enumerate(segs):
        for p in ((s[0], s[1]), (s[2], s[3])):
            clusters.setdefault((round(p[0], 1), round(p[1], 1)), set()).add(i)
    for (px, py), idxs in clusters.items():
        if len(idxs) < 3:
            continue  # 两线相接 = 正常转角，无需结点
        if any(math.hypot(px - dx, py - dy) <= 3.5 for dx, dy in ds):
            continue
        kinds = {segs[i][4] for i in idxs}
        if "sym" in kinds:
            info(f"符号内部星形交汇无结点 ({px:.0f},{py:.0f})（符号内元素，可忽略）")
        else:
            err(f"星形交汇漏结点 ({px:.0f},{py:.0f})：{len(idxs)} 条线在此相接"
                f"（L{','.join(str(segs[i][5]) for i in sorted(idxs)[:4])}）")
            bad += 1

    # 交叉：两条线的内部相交 → 正常情况下不应有结点
    def inter(a, b):
        x1, y1, x2, y2 = a[:4]
        x3, y3, x4, y4 = b[:4]
        d = (x2 - x1) * (y4 - y3) - (y2 - y1) * (x4 - x3)
        if abs(d) < 1e-9:
            return None
        tt = ((x3 - x1) * (y4 - y3) - (y3 - y1) * (x4 - x3)) / d
        u = ((x3 - x1) * (y2 - y1) - (y3 - y1) * (x2 - x1)) / d
        if 1e-6 < tt < 1 - 1e-6 and 1e-6 < u < 1 - 1e-6:
            return (x1 + tt * (x2 - x1), y1 + tt * (y2 - y1))
        return None

    n_cross = 0
    for i in range(len(segs)):
        for j in range(i + 1, len(segs)):
            p = inter(segs[i], segs[j])
            if not p:
                continue
            n_cross += 1
            if any(math.hypot(p[0] - dx, p[1] - dy) <= 3.5 for dx, dy in ds):
                if "sym" in (segs[i][4], segs[j][4]):
                    info(f"控制线搭在开关刀臂上 ({p[0]:.0f},{p[1]:.0f}) L{segs[i][5]}/{segs[j][5]}（有意为之）")
                else:
                    err(f"交叉处有结点 = 疑似短路 ({p[0]:.0f},{p[1]:.0f}) "
                        f"L{segs[i][5]}[{segs[i][4]}] × L{segs[j][5]}[{segs[j][4]}]")
                    bad += 1
    print(f"  线段 {len(segs)} 条，结点 {len(ds)} 个，交叉 {n_cross} 处，问题 {bad} 个")
    return bad


# ---------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description="SVG 示意图交付前体检")
    ap.add_argument("svg")
    ap.add_argument("--font", help="用于缺字检查的字体文件")
    ap.add_argument("--no-font-check", action="store_true")
    args = ap.parse_args()

    src = open(args.svg, encoding="utf-8").read()
    print(f"检查 {args.svg}\n")

    errors = 0
    print("[1] XML 合法性")
    try:
        ET.parse(args.svg)
        print("  OK")
    except ET.ParseError as e:
        err(f"XML 解析失败: {e}")
        return 1

    vb = re.search(r'viewBox="([-\d.\s,]+)"', src)
    if vb:
        v = [float(x) for x in re.split(r"[\s,]+", vb.group(1).strip())]
        box = (v[0], v[1], v[2], v[3])
    else:
        w = re.search(r'width="(\d+)"', src)
        h = re.search(r'height="(\d+)"', src)
        box = (0, 0, float(w.group(1)) if w else 0, float(h.group(1)) if h else 0)

    print("\n[2] 文本包围盒")
    errors += check_text(src, box)

    print("\n[2b] 文字被导线/边框穿过")
    errors += check_text_vs_wires(src)

    print("\n[3] 字形缺字")
    errors += 0 if args.no_font_check else check_glyphs(src, find_font(args.font))

    print("\n[4] marker 缩放")
    errors += check_markers(src)

    print("\n[5] 结点与交叉")
    errors += check_junctions(src)

    print(f"\n结论: {'PASS' if errors == 0 else f'FAIL（{errors} 处 ERROR，需修复）'}")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
