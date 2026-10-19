import os,sys,json,subprocess,time
sys.path.insert(0, os.path.abspath("/c/Users/chenx/Desktop/de-drms/hardware/sim/aaf") if False else os.path.abspath("../.."))
sys.path.insert(0, r"C:UsersenxDesktopde-drmshardwaresimaf")
import numpy as np
import parse_r5 as P
LT=r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
ROOT=os.path.abspath("../..")
LIB=os.path.join(ROOT,"lib","OPAx388.LIB")
D=os.path.abspath(".")
cand=json.load(open(os.path.join(ROOT,'r5_candidates_r2.json'),encoding='utf-8'))['A']
st=[(r*1.01,c*1.05,cd*1.05) for r,c,cd in cand['stages']]
def line(side,src,node,stg):
    out=[];prev=src
    for i,(r,cg,cd) in enumerate(stg,1):
        out.append(f"R{side}{i} {prev} {node}{i} {r:.10g}")
        out.append(f"C{side}{i} {node}{i} 0 {cg:.10g}")
        prev=f"{node}{i}"
    return out
def net(opts,tstop,tstep,src600=False):
    L=["* d5 probe",f".include {LIB}","Vcc vcc 0 DC 3.3","Vee vee 0 DC 0",
       "Vp vp 0 PULSE(2 3 10u 10n 10n 600u 2m)","Vn vn 0 PULSE(2 1 10u 10n 10n 600u 2m)"]
    if src600:
        L+=["Rsa vp fa 600k","Rsb vn fb 600k","Xfa fa fpa vcc vee fpa OPAx388","Xfb fb fna vcc vee fna OPAx388"]
    else:
        L+=["Xfa vp fpa vcc vee fpa OPAx388","Xfb vn fna vcc vee fna OPAx388"]
    L+=line("a","fpa","pa",st); L+=line("b","fna","na",st)
    L+=[f"Cd pa2 na2 {st[-1][2]:.10g}","Rin pa2 na2 130000","Cpa pa2 0 5e-12","Cna na2 0 5e-12"]
    L+=[".save V(pa2) V(na2) V(fpa) V(fna)",f".tran 0 {tstop} 0 {tstep}",opts,".end"]
    return "\n".join(L)+"\n"
def run(name,text,timeout=180):
    open(name+".net","w",encoding="ascii",newline="\n").write(text)
    raw=name+".raw"
    if os.path.exists(raw): os.remove(raw)
    t0=time.time()
    try: r=subprocess.run([LT,"-b","-ascii",name+".net"],capture_output=True,text=True,timeout=timeout)
    except subprocess.TimeoutExpired: return None,"TIMEOUT",time.time()-t0
    return (P.Raw(raw) if os.path.exists(raw) else None),(r.stdout or "")[-150:],time.time()-t0
def ana(raw):
    t=np.array([v.real for v in raw.cols[0]],float)
    p=np.array(raw.col('V(pa2)'),float); n=np.array(raw.col('V(na2)'),float); d=p-n
    m=t>=10e-6; tt,dd=t[m],d[m]; vf=float(dd[-1])
    out=np.where(np.abs(dd-vf)>200e-6)[0]
    ts=float((tt[out[-1]]-10e-6)*1e6) if len(out) else 0.0
    q=t>0.8*t[-1]
    return dict(tset_us=round(ts,2), final=round(vf,6), npts=len(t),
                tail_pp_mV=round(float((d[q].max()-d[q].min())*1e3),3),
                tail_err_uV=round(float(abs(vf-2.0)*1e6),3))
CFG=[
 ("c1_trap_5n",  ".options plotwinsize=0 reltol=1e-5 abstol=1e-11 vntol=1e-8 chgtol=1e-14 trtol=2","200u","5n",False),
 ("c2_trap_1n",  ".options plotwinsize=0 reltol=1e-5 abstol=1e-11 vntol=1e-8 chgtol=1e-14 trtol=2","200u","1n",False),
 ("c3_gear_5n",  ".options plotwinsize=0 method=gear reltol=1e-5 abstol=1e-11 vntol=1e-8 chgtol=1e-14 trtol=7","200u","5n",False),
 ("c4_default",  ".options plotwinsize=0","200u","10n",False),
]
for nm,op,tstop,tst,s6 in CFG:
    raw,msg,dt=run(nm,net(op,tstop,tst,s6))
    if raw is None: print(nm,"FAIL",msg,round(dt,1)); continue
    print(nm, ana(raw), f"{dt:.1f}s", flush=True)
