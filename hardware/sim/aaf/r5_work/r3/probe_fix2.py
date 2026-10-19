import os,sys,subprocess,time
sys.path.insert(0,r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf")
import numpy as np, parse_r5 as P, gen_netlists_r3 as G3
LT=r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
D=r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf\r5_work\r3"
def run(name,text,timeout=300):
    open(os.path.join(D,name+".net"),"w",encoding="ascii",newline="\n").write(text)
    for ext in (".raw",".log"):
        q=os.path.join(D,name+ext)
        if os.path.exists(q): os.remove(q)
    t0=time.time()
    try: subprocess.run([LT,"-b","-ascii",name+".net"],cwd=D,capture_output=True,text=True,timeout=timeout)
    except subprocess.TimeoutExpired: return None,time.time()-t0
    q=os.path.join(D,name+".raw")
    return (P.Raw(q) if os.path.exists(q) else None),time.time()-t0
print("=== stabilized R_iso: AC + settle (200us window, 5ns step) ===", flush=True)
for r1 in (10.0,13.0,22.0):
    cand={"stages":[(r1,1e-7,0.0),(13.0,1e-7,1.8e-8)]}
    # AC first (fast)
    raw,dt=run("fxa_%s"%r1, G3.v9a_ac(cand,tag="fxa"),timeout=120)
    if raw:
        f=raw.f
        def g(ft):
            a=P.interp_at(raw,ft,"V(pa2)"); b=P.interp_at(raw,ft,"V(na2)")
            return P.db(a-b)
        dc=g(0.1)
        print(" R1=%5.1f AC: D1=%7.2f dB  D3=%7.2f dB  D4=%.4f dB"
              %(r1,-(g(4.096e6)-dc),-(g(16.384e6)-dc),abs(g(16e3)-dc)),flush=True)
    # transient
    txt=G3.v9c_tran({"stages":[(r1*1.01,1e-7*1.05,0.0),(13.0*1.01,1e-7*1.05,1.8e-8*1.05)]},
                    tag="fx",tstop="200u",tstep="5n")
    raw,dt=run("fx_%s"%r1,txt,timeout=260)
    if raw is None:
        print(" R1=%5.1f TR TRAN TIMEOUT %.0fs"%(r1,dt),flush=True); continue
    t=np.array([v.real for v in raw.cols[0]],float)
    p=np.array(raw.col("V(pa2)"),float); n=np.array(raw.col("V(na2)"),float); d=p-n
    ts,_,_=P.settle_us(raw,2,band=200e-6)
    q=t>0.8*t[-1]
    print(" R1=%5.1f TR: settle=%8.2f us  tail_pp=%9.4f mV  final=%.6f  (%.0fs)"
          %(r1,ts,d[q].ptp()*1e3,d[-1],dt),flush=True)
