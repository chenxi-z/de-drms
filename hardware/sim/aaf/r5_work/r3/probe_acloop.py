import os, sys, subprocess, time
sys.path.insert(0, r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf")
import numpy as np
import parse_r5 as P

LT = r"C:\Users\chenx\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
LIB = r"C:\Users\chenx\Desktop\de-drms\hardware\sim\aaf\lib\OPAx388.LIB"


def run(name, text, timeout=200):
    open(name + ".net", "w", encoding="ascii", newline="\n").write(text)
    raw = name + ".raw"
    if os.path.exists(raw):
        os.remove(raw)
    t0 = time.time()
    try:
        subprocess.run([LT, "-b", "-ascii", name + ".net"], capture_output=True,
                       text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, "TIMEOUT", time.time() - t0
    return (P.Raw(raw) if os.path.exists(raw) else None), "", time.time() - t0


def ac_net(r1, c1):
    L = ["* ac closed loop probe",
         ".include " + LIB,
         "Vcc vcc 0 DC 3.3",
         "Vee vee 0 DC 0",
         "Vp vp 0 DC 2.0 AC 1",
         "Xfa vp fpa vcc vee fpa OPAx388",
         "R1 fpa pa1 %s" % r1,
         "C1 pa1 0 %s" % c1,
         ".ac dec 800 100 3Meg",
         ".options plotwinsize=0 reltol=1e-6 abstol=1e-12 vntol=1e-9 chgtol=1e-15",
         ".end"]
    return "\n".join(L) + "\n"


print("=== closed-loop AC: source -> pin, with R_iso + C_L ===", flush=True)
for r1, c1 in ((2.4, 100e-9), (2.4, 10e-9), (13.0, 100e-9), (1000.0, 10e-9)):
    raw, msg, dt = run("acl_r%s_c%s" % (r1, c1), ac_net(r1, c1))
    if raw is None:
        print("  R=%s C=%s FAIL %s" % (r1, c1, msg)); continue
    f = raw.f
    y = np.array(raw.col("V(pa1)"), complex)
    m = f <= 2.5e6
    ff, yy = f[m], y[m]
    mag = 20 * np.log10(np.abs(yy))
    i = int(np.argmax(mag))
    # phase relative to DC
    ph = np.unwrap(np.angle(yy))
    ph = (ph - ph[0]) * 180 / np.pi
    print("  R=%7.1f C=%6.1fn : peak %+6.2f dB @ %7.1f Hz  phase there %+8.1f deg"
          % (r1, c1 * 1e9, mag[i], ff[i], ph[i]), flush=True)
