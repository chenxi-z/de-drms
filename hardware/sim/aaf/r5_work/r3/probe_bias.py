import os,sys,json,subprocess,time
sys.path.insert(0, r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf")
import numpy as np, parse_r5 as P
LT=r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
ROOT=r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf"
LIB=os.path.join(ROOT,"lib","OPAx388.LIB")
cand=json.load(open(os.path.join(ROOT,'r5_candidates_r2.json'),encoding='utf-8'))['A']
st_nom=[tuple(map(float,s)) for s in cand['stages']]
st=[(r*1.01,c*1.05,cd*1.05) for r,c,cd in st_nom]
def line(side,src,node,stg):
    out=[];prev=src
    for i,(r,cg,cd) in enumerate(stg,1):
        out.append(f"R{side}{i} {prev} {node}{i} {r:.10g}")
        out.append(f"C{side}{i} {node}{i} 0 {cg:.10g}")
        prev=f"{node}{i}"
    return out
def run(name,text,timeout=240):
    open(name+".net","w",encoding="ascii",newline="\n").write(text)
    raw=name+".raw"
    if os.path.exists(raw): os.remove(raw)
    t0=time.time()
    try: r=subprocess.run([LT,"-b","-ascii",name+".net"],capture_output=True,text=True,timeout=timeout)
    except subprocess.TimeoutExpired: return None,"TIMEOUT",time.time()-t0
    return (P.Raw(raw) if os.path.exists(raw) else None),(r.stdout or "")[-150:],time.time()-t0

# AC at various DC bias points (both lines same DC) -> peaking vs bias
def ac_net(va, vb):
    L=["* ac bias probe",f".include {LIB}","Vcc vcc 0 DC 3.3","Vee vee 0 DC 0",
       f"Vp vp 0 DC {va} AC 0.5",f"Vn vn 0 DC {vb} AC -0.5",
       "Xfa vp fpa vcc vee fpa OPAx388","Xfb vn fna vcc vee fna OPAx388"]
    L+=line("a","fpa","pa",st_nom); L+=line("b","fna","na",st_nom)
    L+=[f"Cd pa2 na2 {st_nom[-1][2]:.10g}","Rin pa2 na2 130000","Cpa pa2 0 5e-12","Cna na2 0 5e-12",
        ".ac dec 600 1 3Meg",".options plotwinsize=0 reltol=1e-6 abstol=1e-12 vntol=1e-9 chgtol=1e-15",".end"]
    return "\n".join(L)+"\n"
print("=== AC peaking vs DC bias (nominal params) ===")
for va,vb in ((2.0,2.0),(2.5,2.5),(2.75,2.75),(2.9,2.9),(3.0,3.0),(2.2,1.8),(2.6,1.4),(2.9,1.1),(3.0,1.0)):
    raw,msg,dt=run(f"acb_{va}_{vb}",ac_net(va,vb))
    if raw is None: print(f"  bias {va}/{vb}: FAIL {msg}"); continue
    f=raw.f; p=np.array(raw.col('V(pa2)'),complex); n=np.array(raw.col('V(na2)'),complex)
    d=p-n; g=20*np.log10(np.abs(d)/abs(d[0]))
    m=(f>1)&(f<2.5e6)
    i=np.argmax(g[m])
    print(f"  bias {va}/{vb} V: peak {g[m][i]:+.2f} dB @ {f[m][i]/1e3:.0f} kHz | -3dB@{f[m][np.argmax(g[m]<-3)]/1e3:.1f}k")
