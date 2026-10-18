"""最终冻结：三案均用真实 Zout（含负实部）与 peaking 硬门槛。"""
import json, math, os
import numpy as np
import r5_snap_r2 as S
import opt_round5 as o5

o5.FAST = False
GRADE = {2:'A', 3:'B', 4:'C'}
Afix = json.load(open('r5_r2_A_fixed.json', encoding='utf-8'))
fine = json.load(open('r5_r2_fine.json', encoding='utf-8'))
r1 = json.load(open('r5_candidates.json', encoding='utf-8'))
r1_by_n = {v['n_stages']: [(float(a),float(b),float(c)) for a,b,c in v['stages']] for v in r1.values()}

def retune(st, fc_t):
    lo,hi=0.005,800.
    for _ in range(60):
        m=math.sqrt(lo*hi)
        if o5.fc_dm([(r*m,a,b) for r,a,b in st])>fc_t: lo=m
        else: hi=m
    return [(r*math.sqrt(lo*hi),a,b) for r,a,b in st]

out = {}
for n,g in GRADE.items():
    print(f"\n{'='*70}\n方案 {g}（n={n}）\n{'='*70}")
    if n == 2:
        cont = [tuple(s) for s in Afix['continuous']]
        cur  = [tuple(s) for s in Afix['stages']]
        tag  = Afix['tag']
        e = S.evaluate(cont); ev = S.evaluate(cur)
        print(f"  [{tag}] 连续 des={e['design']:.4f} → 冻结 des={ev['design']:.4f}")
        print(f"     连续 {S.topo(cont)}\n     冻结 {S.topo(cur)}")
        best = (tag, cur, ev, cont, e)
    else:
        best = None
        for atag, cont in (('fine', [tuple(float(x) for x in s) for s in fine[str(n)]['stages']]),
                           ('r1@80k', retune(r1_by_n[n], 80e3)),
                           ('r1@75k', retune(r1_by_n[n], 75e3))):
            e = S.evaluate(cont)
            if not all(e['hard'].values()):
                print(f"  [{atag}] 硬约束不满足: {[k for k,v in e['hard'].items() if not v]}"); continue
            for lab, rtab in (('E24', S.R24), ('E96', S.R96)):
                cur_, ev_ = S.neighbor_search(S.snap(cont, rtab), rtab, span=1)
                ok = all(ev_['hard'].values())
                print(f"  [{atag}/{lab}] des={ev_['design']:.4f} npass={ev_['npass']} "
                      f"pk={ev_['pred']['peaking_db']:>5.1f} hard={ok}  {S.topo(cur_)}")
                if ok and (best is None or S.key(ev_) > S.key(best[2])):
                    best = (f'{atag}/{lab}', cur_, ev_, cont, e)
        tag, cur, ev, cont, e = best
        print(f"  ★ {g} 选中 {tag}: {S.topo(cur)}  des={ev['design']:.4f}")

    pred = ev['pred']; dims = ev['dims']; pf = ev['pass_']
    out[g] = {
        'grade': g, 'n_stages': n,
        'stages': [list(map(float,s)) for s in cur],
        'r_series': tag.split('/')[-1], 'c_series': 'E12', 'source': tag,
        'pred': pred, 'dims': dims, 'pass': pf,
        'hard': ev['hard'], 'design_score': ev['design'],
        'min_score': min(dims.values()),
        'continuous': {'stages': [list(map(float,s)) for s in cont],
                       'dims': e['dims'], 'pred': e['pred'], 'design': e['design']},
        'snap': {'source': tag, 'npass': ev['npass'],
                 'failing_dims': [k for k,v in pf.items() if not v],
                 'hard_ok': all(ev['hard'].values())},
        'physics': {k: (float(v) if isinstance(v,(int,float,np.floating)) else v)
                    for k,v in o5.physics_limits(cur).items()},
    }
    print(f"     D1={pred['A_dm']:.1f} D2={pred['A_cm']:.1f} D3={pred['A_mclk']:.1f} "
          f"dG={pred['dG_16k']:.3f} Vn={pred['V_n_lsb']:.2f} pk={pred['peaking_db']:.1f} "
          f"CMRR1%={pred['CMRR_pb_db']:.1f}")

json.dump(out, open('r5_candidates_r2.json','w',encoding='utf-8',newline='\n'),
          ensure_ascii=False, indent=2, default=float)
print("\n✓ 写入 r5_candidates_r2.json")
