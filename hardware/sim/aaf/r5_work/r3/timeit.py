import os,subprocess,time,sys
LT=r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
D=r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf\r5_work\r3"
for nm in ("r5_A_r3_v9a","r5_A_r3_v9pk","r5_A_r3_v9d","r5_A_r3_v9dn","r5_A_r3_v9p_m0.01_pair","r5_A_r3_v9k_ron1","r5_A_r3_v9c"):
    for ext in (".raw",".log"):
        q=os.path.join(D,nm+ext)
        if os.path.exists(q): os.remove(q)
    t0=time.time()
    try:
        r=subprocess.run([LT,"-b","-ascii",nm+".net"],cwd=D,capture_output=True,text=True,timeout=240)
        rc=r.returncode
    except subprocess.TimeoutExpired:
        print(nm,"TIMEOUT >240s"); continue
    dt=time.time()-t0
    raw=os.path.join(D,nm+".raw")
    sz=os.path.getsize(raw)/1e6 if os.path.exists(raw) else -1
    print(f"{nm:32s} rc={rc} {dt:7.1f}s raw={sz:8.1f}MB", flush=True)
