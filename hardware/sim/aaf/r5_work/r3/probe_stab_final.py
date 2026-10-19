import os,sys,subprocess,time
sys.path.insert(0,r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf")
import numpy as np, parse_r5 as P, gen_netlists_r3 as G3
LT=r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
D=r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf\r5_work\r3"
def run(name,text,timeout=420):
    open(os.path.join(D,name+".net"),"w",encoding="ascii",newline="\n").write(text)
    for ext in (".raw",".log"):
        q=os.path.join(D,name+ext)
        if os.path.exists(q): os.remove(q)
    t0=time.time()
    try: subprocess.run([LT,"-b","-ascii",name+".net"],cwd=D,capture_output=True,text=True,timeout=timeout)
    except subprocess.TimeoutExpired: return None,time.time()-t0
    q=os.path.join(D,name+".raw")
    return (P.Raw(q) if os.path.exists(q) else None),time.time()-t0
print("=== transient at stabilized R_iso (nominal, 200us, gear 20n) ===",flush=True)
for r1 in (10.0,13.0):
    txt=G3.v9c_tran({"stages":[(r1,1e-7,0.0),(13.0,1e-7,1.8e-8)]},tag="sf",tstop="200u",tstep="20n")
    txt=txt.replace(".options plotwinsize=0 method=trap reltol=1e-5 abstol=1e-11 vntol=1e-8 chgtol=1e-14 trtol=2",
                    ".options plotwinsize=0 method=gear reltol=1e-5 abstol=1e-11 vntol=1e-8 chgtol=1e-14 trtol=3")
    raw,dt=run("sf_%s"%r1,txt,timeout=400)
    if raw is None: print(" R1=%5.1f TIMEOUT %.0fs"%(r1,dt),flush=True); continue
    t=np.array([v.real for v in raw.cols[0]],float)
    p=np.array(raw.col("V(pa2)"),float); n=np.array(raw.col("V(na2)"),float); d=p-n
    ts,_,_=P.settle_us(raw,2,band=200e-6); q=t>0.8*t[-1]
    print(" R1=%5.1f npts=%6d settle=%8.2f us tail_pp=%9.4f mV  (%.0fs)"
          %(r1,len(t),ts,d[q].ptp()*1e3,dt),flush=True)
