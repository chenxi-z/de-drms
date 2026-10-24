#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scistyle.py — DE-DRMS 示意图统一排版模块（SCI/A4 单栏规格）

所有 docs/design/diagram/*.svg 生成器共用：
  - 视图框 800×800，白底，无边框网格底纹
  - 字体：ASCII → Times New Roman，中文/符号 → Noto Serif CJK SC（cairosvg 无逐字形回退，
    必须按字符脚本拆 run，见 _runs）
  - 字号下限 11 pt（标题 20–22，轴题/标签 12–14，正文/注释 11–12）
  - 上下标用独立定位 <text>，不用 dy-tspan（cairosvg 对 anchor=middle 的 tspan 会逐段独立居中叠印）
  - 门禁：python3 tools/svg_schematic_check.py <svg>（文本重叠/穿线/越界/缺字/结点五项）
"""
import unicodedata

INK = "#1a1a1a"        # 主框/导线（SCI 黑）
GRID = "#eceff3"       # 极浅网格
BLUE = "#1F4FD8"       # 数字/测量链
GREEN = "#059669"      # 模拟/测量电流路径
ORANGE = "#EA580C"     # 校准/开关
RED = "#DC2626"        # 告警/禁用
PURPLE = "#7C3AED"     # 控制线（虚线）
GRAY = "#556070"       # 次要标注
THRESH = "#2C3E70"     # 设计要求/门限

F_LAT = "Times New Roman, serif"
F_CJK = "'Noto Serif CJK SC','Noto Serif SC',serif"


def w_est(t, fs):
    """估宽：与 tools/svg_schematic_check.py 同系数（CJK 1.0×fs，其余 0.56×fs）。"""
    return sum((1.0 if unicodedata.east_asian_width(c) in "WF" else 0.56) * fs for c in t)


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _runs(t):
    """按脚本拆 run：ASCII → 西文字体，非 ASCII → CJK 字体。"""
    out = []
    for c in t:
        f = F_LAT if c.isascii() else F_CJK
        if out and out[-1][1] == f:
            out[-1][0] += c
        else:
            out.append([c, f])
    return out


def _emit(x, y, t, fs, fill, w):
    out, cx = [], x
    for rt, rf in _runs(t):
        if not rt:
            continue
        rtx = (" " + rt[1:]) if rt[0] == " " else rt   # 段首空格防 SVG 空白折叠
        out.append(f'<text x="{cx:.1f}" y="{y:.1f}" font-size="{fs:.1f}" fill="{fill}"'
                   f' text-anchor="start" font-weight="{w}" font-family="{rf}">{esc(rtx)}</text>')
        cx += w_est(rt, fs)
    return "".join(out)


def T(x, y, s, fs=12, fill="#374151", anchor="start", w="normal"):
    """纯文本（无下标），anchor 支持 start/middle/end。"""
    return rich(x, y, [(s, "")], fs, fill, anchor, w)


def rich(x, y, segs, fs=12, fill="#374151", anchor="start", w="normal"):
    """含上下标的富文本：segs = [(文本, ""|"sub"|"sup")]。
    逐段独立 <text>，x 按估宽推进；middle/end 由总宽反推起点。
    下标 fs×0.72、基线下移 0.24×fs；上标 fs×0.72、基线上移 0.36×fs。"""
    total = sum(w_est(t, fs * 0.72 if st else fs) for t, st in segs)
    if anchor == "middle":
        x -= total / 2
    elif anchor == "end":
        x -= total
    out = []
    for t, st in segs:
        if t:
            s = fs * 0.72 if st else fs
            dy = {"": 0.0, "sub": 0.24 * fs, "sup": -0.36 * fs}[st]
            out.append(_emit(x, y + dy, t, s, fill, w))
        x += w_est(t, fs * 0.72 if st else fs)
    return "".join(out)


def head(title, subtitle, date="2026-10-23"):
    """标准头部：标题 22 bold + 副标题 13 + 右上角日期 11。"""
    return [
        T(34, 40, title, 22, "#111827", w="bold"),
        T(34, 64, subtitle, 13, "#475569"),
        T(766, 40, date, 11, "#94a3b8", "end"),
    ]


def frame(x, y, w, h, lw=1.3, stroke=INK):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="{stroke}" stroke-width="{lw}"/>'
