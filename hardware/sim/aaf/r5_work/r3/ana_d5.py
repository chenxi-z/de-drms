import os, sys
sys.path.insert(0, r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf")
import numpy as np
import parse_r5 as P

D = r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf\r5_work\r3\probe_d5"
for nm in ("d5_nom_0ohm", "d5_wc_0ohm", "d5_wc_600k"):
    r = P.Raw(os.path.join(D, nm + ".raw"))
    t = np.array([v.real for v in r.cols[0]], float)
    p = np.array(r.col("V(pa2)"), float)
    n = np.array(r.col("V(na2)"), float)
    cm = 0.5 * (p + n)
    dm = p - n
    q = t > 0.7 * t[-1]
    seg_t = t[q]
    for label, y in (("cm", cm), ("dm", dm)):
        s = y[q]
        x = s - s.mean()
        fx = np.fft.rfftfreq(len(s), d=float(np.median(np.diff(seg_t))))
        X = np.abs(np.fft.rfft(x)) * 2 / len(x)
        k = int(np.argmax(X[1:])) + 1
        print("%-14s %s: mean=%9.6f  pp=%9.3f mV  f0=%7.1f kHz  amp=%8.3f mV"
              % (nm, label, s.mean(), s.ptp() * 1e3, fx[k] / 1e3, X[k] * 1e3))
    # growth of the envelope over the run
    win = 25e-6
    edges = np.arange(50e-6, t[-1], win)
    amp = []
    for e in edges:
        m = (t >= e) & (t < e + win)
        if m.sum() > 10:
            amp.append(np.ptp(cm[m]) * 1e3)
    if amp:
        print("     CM envelope (mV pp) vs time [50us + 25us steps]: "
              + " ".join("%.0f" % a for a in amp[:12]))
    print()

# settling attempt on the differential signal, plus raw node settling
r = P.Raw(os.path.join(D, "d5_nom_0ohm.raw"))
t = np.array([v.real for v in r.cols[0]], float)
p = np.array(r.col("V(pa2)"), float)
n = np.array(r.col("V(na2)"), float)
dm = p - n
print("last 5 samples of dm:", ["%.6f" % v for v in dm[-5:]])
print("dm last-90%%-window mean = %.6f  pp = %.3f mV"
      % (dm[t > 0.9 * t[-1]].mean(), dm[t > 0.9 * t[-1]].ptp() * 1e3))
