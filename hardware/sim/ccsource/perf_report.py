#!/usr/bin/env python3
"""cc2 恒流源性能套件报告：解析 ltspice-sim ASCII raw（步进 OP / 复数 AC / 暂态）。
再生成：先跑 cc2_dc/cc2_line/cc2_loop/cc2_psrr/cc2_loadstep/cc2_linestep 六个 .net（ltspice-sim run）。"""
import re, cmath, math

def parse_raw(path):
    txt = open(path).read().splitlines()
    vi, i = txt.index('Variables:'), txt.index('Values:')
    names = [v.split()[1] for v in txt[vi+1:i]]
    nv = len(names) - 1
    xs, data, cur, k, buf = [], [], None, 0, []
    for line in txt[i+1:]:
        s = line.strip()
        if not s: continue
        if re.match(r'^\d+\s+[-+0-9.eE]+(,[-+0-9.eE]+)?$', s):
            if cur is not None and k == nv: data.append(buf)
            cur = float(s.split()[1].split(',')[0]); xs.append(cur); buf = []; k = 0; continue
        if cur is not None and k < nv:
            parts = s.split(',')
            buf.append(complex(float(parts[0]), float(parts[1])) if len(parts) == 2 else float(s)); k += 1
    if cur is not None and k == nv: data.append(buf)
    return names, xs, data

def col(names, data, name):
    j = names[1:].index(name)
    return [d[j] for d in data]

print("="*70); print("① 负载调整率（R_sample 1k–130k @3.3V_A）")
names, xs, data = parse_raw('cc2_dc.raw')
RLs = [1,5,10,20,40,60,80,100,120,130]
iv = [c.real for c in col(names,data,'I(Vsm)')]
for rl, x in zip(RLs, iv): print(f"   R={rl:>4}kΩ  I={x*1e6:.6f} µA")
print(f"   → 极差 {(max(iv)-min(iv))*1e6:.6f} µA = {(max(iv)-min(iv))/min(iv)*100:.5f} %")

print("="*70); print("② 电压调整率（3.3V_A 3.20–3.40 V，RL=120k）")
names, xs, data = parse_raw('cc2_line.raw')
VSs = [3.20,3.25,3.30,3.35,3.40]
iv = [c.real for c in col(names,data,'I(Vsm)')]
for v, x in zip(VSs, iv): print(f"   V={v:.2f} V  I={x*1e6:.5f} µA")
print(f"   → 极差 {(max(iv)-min(iv))/min(iv)*100:.4f} %（=ΔVS/VS 精确 1:1——VSET 比例分压所致，")
print(f"     电流随轨线性跟踪；比值测量 V_sample/V_Rsense 中抵消，非精度误差项）")

print("="*70); print("③ 环路增益/相位裕度（RL=120k，运放输出串联注入）")
names, xs, data = parse_raw('cc2_loop.raw')
T = [-(a/b) for a, b in zip(col(names,data,'V(o1)'), col(names,data,'V(g)')) if abs(b) > 0]
fx = px = None
for j in range(len(T)-1):
    if abs(T[j]) >= 1 > abs(T[j+1]):
        l1, l2 = math.log10(abs(T[j])), math.log10(abs(T[j+1]))
        t = (0-l1)/(l2-l1)
        fx = 10**(math.log10(xs[j].real)+t*(math.log10(xs[j+1].real)-math.log10(xs[j].real)))
        p1 = cmath.phase(T[j])*180/math.pi; p2 = cmath.phase(T[j+1])*180/math.pi
        px = p1 + t*(p2-p1); break
print(f"   交越 fc ≈ {fx/1e3:.1f} kHz，相位裕度 PM = {180+px:.1f}°")
for f0 in (0.1, 10, 100, 1000):
    j = min(range(len(xs)), key=lambda k: abs(xs[k].real-f0))
    print(f"   |T| @{f0:<6} Hz = {20*math.log10(abs(T[j])):6.1f} dB")

print("="*70); print("④ 电源纹波响应（ΔI/I 每 1V 轨扰动，RL=120k）")
names, xs, data = parse_raw('cc2_psrr.raw')
Iv = col(names,data,'I(Vsm)')
for f0 in (10, 50, 100, 1e3, 1e4, 1e5):
    j = min(range(len(xs)), key=lambda k: abs(xs[k].real-f0))
    r = abs(Iv[j])/7.857e-6
    print(f"   @{f0:>7.0f} Hz: ΔI/I = {r:.4f}（{20*math.log10(r):+.1f} dB；参考：ratiometric 理论 1/3.3 = 0.3030）")

def tran_edges(path, viname, refname, threshold, settle=1e-3):
    names, xs, data = parse_raw(path)
    iv = [c.real for c in col(names,data,viname)]
    edges = []
    ref = [x.real for x in col(names,data,refname)]
    for j in range(1, len(ref)):
        if (ref[j-1] < threshold <= ref[j]) or (ref[j-1] > threshold >= ref[j]):
            edges.append((j, 'up' if ref[j] > ref[j-1] else 'down'))
    for j0, d in edges:
        post = iv[min(j0+400, len(iv)-1)]
        win = iv[max(0,j0-10):j0+400]
        pk = max(win, key=lambda v: abs(v-post))
        ts = None
        for jj in range(j0, len(xs)):
            if abs(iv[jj]-post) <= settle*post and jj+60 < len(xs) and all(abs(x-post) <= settle*post for x in iv[jj:jj+60]):
                ts = xs[jj]-xs[j0]; break
        tss = f"{ts*1e6:.1f} µs" if ts is not None else "窗口内未稳"
        print(f"   {d:>4} @t={xs[j0]*1e3:.3f}ms: {iv[max(0,j0-5)]*1e6:.4f}→{post*1e6:.4f} µA；"
              f"过渡峰值相对新稳态 {(pk-post)/post*100:+.3f} %；±0.1% 恢复 {tss}")

print("="*70); print("⑤ 负载阶跃暂态（10k↔120k，边沿 ~2µs，判稳=新稳态±0.1%）")
tran_edges('cc2_loadstep.raw', 'I(Vsm)', 'V(ctl)', 0.5)
print("="*70); print("⑥ 电源阶跃暂态（3.25↔3.35 V，边沿 20µs，判稳=新稳态±0.1%）")
tran_edges('cc2_linestep.raw', 'I(Vsm)', 'V(ta)', 3.3)
