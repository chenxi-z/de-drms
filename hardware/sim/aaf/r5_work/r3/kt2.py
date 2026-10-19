import os,sys,subprocess,time
sys.path.insert(0,r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf")
import numpy as np, parse_r5 as P
LT=r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
D=r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf\r5_work\r3"
for ext in (".raw",".log"):
    q=os.path.join(D,"r5_A_r3_v9k_ron1"+ext)
    if os.path.exists(q): os.remove(q)
t0=time.time()
try:
    subprocess.run([LT,"-b","-ascii","r5_A_r3_v9k_ron1.net"],cwd=D,capture_output=True,text=True,timeout=240)
    print("rc ok %.1fs"%(time.time()-t0))
except subprocess.TimeoutExpired:
    print("TIMEOUT 240s")
q=os.path.join(D,"r5_A_r3_v9k_ron1.raw")
if os.path.exists(q):
    print("raw",os.path.getsize(q)/1e6,"MB")
    try:
        r=P.Raw(q); t=np.array([v.real for v in r.cols[0]],float)
        print("npts",len(t),"tmax",t[-1])
    except Exception as e: print("parse",e)
