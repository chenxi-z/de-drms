import os, sys, subprocess, time
sys.path.insert(0, r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf")
import numpy as np
import parse_r5 as P

LT = r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
LIB = r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf\lib\OPAx388.LIB"


def run(name, text, timeout=240):
    open(name + ".net", "w", encoding="ascii", newline="\n").write(text)
    for f in (name + ".raw", name + ".log"):
        if os.path.exists(f):
            os.remove(f)
    t0 = time.time()
    try:
        subprocess.run([LT, "-b", "-ascii", name + ".net"], capture_output=True,
                       text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, "TIMEOUT", time.time() - t0
    return (P.Raw(name + ".raw") if os.path.exists(name + ".raw") else None), "", time.time() - t0


def znet(r1, c1, r2, c2, cd):
    """Measure Zout of the loaded follower: 1 A AC injection at fpa node."""
    L = ["* Zout with real load",
         ".include " + LIB,
         "Vcc vcc 0 DC 3.3",
         "Vee vee 0 DC 0",
         "Vp vp 0 DC 2.0 AC 0",
         "Xfa vp fpa vcc vee fpa OPAx388",
         "Iinj 0 fpa AC 1",
         "R1 fpa pa1 %s" % r1,
         "C1 pa1 0 %s" % c1,
         "R2 pa1 pa2 %s" % r2,
         "C2 pa2 0 %s" % c2,
         "Cd pa2 na2 %s" % cd,
         "Rin pa2 na2 130000",
         "Vn vn 0 DC 2.0 AC 0",
         "Xfb vn fna vcc vee fna OPAx388",
         "R1b fna na1 %s" % r1,
         "C1b na1 0 %s" % c1,
         "R2b na1 na2 %s" % r2,
         "C2b na2 0 %s" % c2,
         "Cpa pa2 0 5e-12", "Cna na2 0 5e-12",
         ".ac dec 3000 10 5Meg",
         ".options plotwinsize=0 reltol=1e-7 abstol=1e-13 vntol=1e-10 chgtol=1e-16",
         ".end"]
    return "\n".join(L) + "\n"


print("=== Zout of loaded follower (candidate A: R1=2.4,C1=100n,R2=13,C2=100n,Cd=18n) ===",
      flush=True)
raw, msg, dt = run("zout_load", znet(2.4, "1e-7", 13.0, "1e-7", "1.8e-8"))
if raw is None:
    print("FAIL", msg)
else:
    f = raw.f
    z = np.array(raw.col("V(fpa)"), complex)   # 1 A -> V = Z
    m = (f >= 1e3) & (f <= 2e6)
    re, im = z[m].real, z[m].imag
    print("   f[kHz]   Re(Z)     Im(Z)")
    for ft in (50e3, 100e3, 150e3, 185e3, 220e3, 280e3, 350e3, 500e3):
        i = int(np.argmin(abs(np.log10(f[m]) - np.log10(ft))))
        print("   %7.1f  %9.3f  %9.3f" % (f[m][i] / 1e3, re[i], im[i]))
    # find zero crossings of Im and check Re sign
    s = np.sign(im)
    zc = np.where(np.diff(s) != 0)[0]
    print("\n   Im(Z)=0 crossings:")
    for k in zc:
        print("     f=%8.1f kHz  Re(Z)=%+8.3f  -> %s"
              % (f[m][k] / 1e3, re[k], "UNSTABLE" if re[k] < 0 else "stable"))
    print("   min Re(Z) over band = %+0.3f ohm @ %.1f kHz"
          % (re.min(), f[m][int(np.argmin(re))] / 1e3))
