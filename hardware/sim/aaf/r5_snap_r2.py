"""Round-5 第 2 轮：E24/E96 + E12 取整 + 邻域枚举（并行的轻量实现）。"""
import itertools, math
import opt_round5 as o5

E24 = [1.0,1.1,1.2,1.3,1.5,1.6,1.8,2.0,2.2,2.4,2.7,3.0,3.3,3.6,3.9,4.3,4.7,5.1,5.6,6.2,6.8,7.5,8.2,9.1]
E96 = [1.00,1.02,1.05,1.07,1.10,1.13,1.15,1.18,1.21,1.24,1.27,1.30,1.33,1.37,1.40,1.43,
 1.47,1.50,1.54,1.58,1.62,1.65,1.69,1.74,1.78,1.82,1.87,1.91,1.96,2.00,2.05,2.10,
 2.15,2.21,2.26,2.32,2.37,2.43,2.49,2.55,2.61,2.67,2.74,2.80,2.87,2.94,3.01,3.09,
 3.16,3.24,3.32,3.40,3.48,3.57,3.65,3.74,3.83,3.92,4.02,4.12,4.22,4.32,4.42,4.53,
 4.64,4.75,4.87,4.99,5.11,5.23,5.36,5.49,5.62,5.76,5.90,6.04,6.19,6.34,6.49,6.65,
 6.81,6.98,7.15,7.32,7.50,7.68,7.87,8.06,8.25,8.45,8.66,8.87,9.09,9.31,9.53,9.76]
E12 = [1.0,1.2,1.5,1.8,2.2,2.7,3.3,3.9,4.7,5.6,6.8,8.2]

def series(mant, lo, hi):
    vals=set()
    for d in range(int(math.floor(math.log10(lo)))-1, int(math.ceil(math.log10(hi)))+2):
        for m in mant:
            v=m*10.0**d
            if lo*0.999<=v<=hi*1.001: vals.add(round(v,15))
    return sorted(vals)

R24 = series(E24, 1.0, 5100.0)
R96 = series(E96, 1.0, 5100.0)
CT  = series(E12, 10e-12, 100e-9)

def nearest(v, table): return min(range(len(table)), key=lambda i: abs(table[i]-v))

def snap(st, rtab):
    return [(rtab[nearest(r,rtab)], CT[nearest(cg,CT)],
             CT[nearest(cd,CT)] if cd>0 else 0.0) for r,cg,cd in st]

def evaluate(st):
    pred = o5.predict(st); dims = o5.dim_scores(pred)
    pf = o5.pass_flags(dims, pred)
    return dict(st=list(st), pred=pred, dims=dims, pass_=pf,
                hard=o5.hard_checks(pred), design=o5.design_score(dims),
                npass=sum(pf.values()))

def key(e):
    return (all(e['hard'].values()), e['npass'], e['design'], min(e['dims'].values()))

def neighbor_search(base, rtab, span=1):
    """±span 档的**逐级独立**邻域（不取全笛卡尔，避免组合爆炸）：
    逐级单独扫 R×Cg 的 (2span+1)^2 组合，末级再扫 Cdiff，坐标下降 2 轮。"""
    n=len(base)
    cur=[tuple(s) for s in base]
    best=evaluate(cur)
    for _round in range(2):
        improved=False
        for i in range(n):
            r0,c0,d0=cur[i]
            ri=nearest(r0,rtab); ci=nearest(c0,CT); di=nearest(d0,CT) if d0>0 else None
            for dr in range(-span,span+1):
                for dc in range(-span,span+1):
                    for dd in ([0] if d0<=0 else range(-span,span+1)):
                        r=rtab[max(0,min(len(rtab)-1,ri+dr))]
                        c=CT[max(0,min(len(CT)-1,ci+dc))]
                        d=0.0 if d0<=0 else CT[max(0,min(len(CT)-1,di+dd))]
                        cand=list(cur); cand[i]=(r,c,d)
                        e=evaluate(cand)
                        if key(e)>key(best): best, cur, improved = e, cand, True
        if not improved: break
    return cur, best

def fmt_c(c):
    if c<=0: return "0"
    return f"{c*1e9:.4g}nF" if c>=1e-9 else f"{c*1e12:.4g}pF"

def topo(st):
    out=[]
    for r,cg,cd in st:
        s=f"{r:.4g}Ω/{fmt_c(cg)}"
        if cd>0: s+=f"+{fmt_c(cd)}"
        out.append(s)
    return " — ".join(out)
