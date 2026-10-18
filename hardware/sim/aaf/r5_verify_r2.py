"""第 2 轮冻结参数的 LTspice 真实 OPA388 验证（V9a/b/d + V9f）。"""
import json, os, subprocess, sys
import numpy as np
import gen_netlists_r5 as G
import parse_r5 as P

LTSPICE = r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
OUT = os.path.abspath('r5_work/r2')
os.makedirs(OUT, exist_ok=True)
cands = json.load(open('r5_candidates_r2.json', encoding='utf-8'))

def run(net_text, name):
    path = os.path.join(OUT, name + '.net')
    with open(path, 'w', encoding='ascii', newline='\n') as fh:
        fh.write(net_text.replace('lib/OPAx388.LIB', '../../lib/OPAx388.LIB'))
    raw = path[:-4] + '.raw'
    if os.path.exists(raw): os.remove(raw)
    p = subprocess.run([LTSPICE, '-b', '-ascii', os.path.basename(path)], cwd=OUT,
                       capture_output=True, text=True, timeout=600)
    if not os.path.exists(raw):
        return None, (p.stdout or '')[-400:] + (p.stderr or '')[-400:]
    return P.Raw(raw), None

res = {}
for g in ('A','B','C'):
    c = dict(cands[g]); c['stages'] = [tuple(s) for s in c['stages']]
    ns = len(c['stages'])
    r = {}
    # V9a DM AC
    raw, err = run(G.gen_v9a(c, tag=f'{g}9a'), f'r2_{g}_v9a')
    if raw:
        f = np.asarray(raw.f, float)
        v = np.asarray(raw.col(f'V(pa{ns})'), complex) - np.asarray(raw.col(f'V(na{ns})'), complex)
        g0 = abs(v[0])
        at = lambda t: float(20*np.log10(abs(v[np.argmin(abs(f-t))])/g0))
        r['D1_lt'] = -at(4.096e6); r['D3_lt'] = -at(16.384e6); r['D4_lt'] = abs(at(16e3))
    else:
        r['v9a_err'] = err
    # V9b CM AC
    raw, err = run(G.gen_v9b(c, tag=f'{g}9b'), f'r2_{g}_v9b')
    if raw:
        f = np.asarray(raw.f, float)
        v = np.asarray(raw.col(f'V(pa{ns})'), complex)
        r['D2_lt'] = -float(20*np.log10(abs(v[np.argmin(abs(f-4.096e6))])/abs(v[0])))
    else:
        r['v9b_err'] = err
    # V9d noise
    raw, err = run(G.gen_v9d(c, tag=f'{g}9d'), f'r2_{g}_v9d')
    if raw:
        f = np.asarray(raw.f, float); d = np.abs(np.asarray(raw.col('v(onoise)'), float))
        tot = float(np.sqrt(np.trapz(d**2, f)))
        r['D6_nv'] = tot*1e9; r['D6_lsb'] = tot/290.98e-9
    else:
        r['v9d_err'] = err
    # V9f settle @600k
    raw, err = run(G.gen_v9f(c, tag=f'{g}9f'), f'r2_{g}_v9f')
    if raw:
        pass
    r['_err_f'] = err
    res[g] = r
    print(g, {k: (round(v,3) if isinstance(v,float) else v) for k,v in r.items()}, flush=True)

json.dump(res, open('r5_r2_ltspice.json','w',encoding='utf-8'), ensure_ascii=False, indent=2)
