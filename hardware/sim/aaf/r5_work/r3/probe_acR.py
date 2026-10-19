import os, sys, subprocess, time
sys.path.insert(0, r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf")
import numpy as np
import parse_r5 as P
LT = r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
LIB = r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf\lib\OPAx388.LIB"
def run(name, text, timeout=240):
    open(name + ".net", "w", encoding="ascii", newline="\n").write(text)
    for f in (name+".raw", name+".log"):
        if os.path.exists(f): os.remove(f)
    t0=time.time()
    try: subprocess.run([LT,"-b","-ascii",name+".net"],capture_output=True,text=True,timeout=timeout)
    except subprocess.TimeoutExpired: return None,"TIMEOUT",time.time()-t0
    return (P.Raw(name+".raw") if os.path.exists(name+".raw") else None),"",time.time()-t0
def ac_net(r1,c1):
    return "\n".join(["* closed loop ac","%" if 0 else ".include "+LIB,
        "Vcc vcc 0 DC 3.3","Vee vee 0 DC 0","Vp vp 0 DC 2.0 AC 1",
        "Xfa vp fpa vcc vee fpa OPAx388",
        "R1 fpa pa1 %s"%r1,"C1 pa1 0 %s"%c1,
        ".ac dec 2000 100 3Meg",
        ".options plotwinsize=0 reltol=1e-7 abstol=1e-13 vntol=1e-10 chgtol=1e-16",
        ".end"])+"\n"
print("=== closed-loop AC peak at pin node vs R_iso (C=100n) ===",flush=True)
for r1 in (2.4,3.0,3.5,4.0,5.0,6.8,10.0,13.0):
    raw,msg,dt=run("acR_%s"%r1, ac_net(r1,"1e-7"))
    if raw is None: print("  R=%s FAIL %s"%(r1,msg)); continue
    f=raw.f; y=np.array(raw.col("V(pa1)"),complex)
    m=(f>=100)&(f<=2.5e6); g=20*np.log10(np.abs(y[m])/abs(y[0]))
    i=int(np.argmax(g)); ph=np.unwrap(np.angle(y[m]))*180/np.pi
    print("  R=%5.1f : peak %+7.2f dB @ %8.0f Hz (phase %+7.1f deg)"%(r1,g[i],f[m][i],ph[i]),flush=True)
