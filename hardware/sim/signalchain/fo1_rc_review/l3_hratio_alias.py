#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L3 系统层离线后处理：Hratio 幅相误差、R 比值误差、fMOD±offset 折叠风险。

口径（必须随结果一起读，任务书 §3.2）：
  - 这是「LTspice 交流族 CSV（模拟前端频响）× ADS131A02 手册 sinc³ 传递函数」的
    离线 Python 乘法后处理，不是 LTspice 直接仿真 ADC 数字内核。
  - sinc³ 复传递函数按 SBAS590E 口径（hardware/sim/aaf/r5_datasheet_facts.md §2）：
    fMOD=4.096 MHz、fDATA=128 kSPS、OSR=32（全局寄存器，两通道同设）。
  - 折叠（alias）计算把输入开关采样当作理想 fMOD 冲激采样（折叠增益 0 dB，最坏界）；
    孔径衰减未包含——手册未给有效孔径，属未验证参数，只给有界风险。
  - 不宣称「已验证混叠」。

输入（任务书指定交流族 CSV）：
  csv/t01_dm_ac.csv         H0(port=opa388)/H1(port=kelvin) 幅相 + D1@4.096M
  csv/t02_cm_ac.csv         Kelvin 结构性 CM→DM（in-band，sinc³ 不除）
  csv/t03_channel_match.csv Hratio(f) 幅相（ideal0ohm / real_src）
  csv/t10_group_delay.csv   模拟段群延迟
交叉核对（非任务书指定输入，仅作对拍）：
  csv/t09_ac_residual.csv   T09 在 fMOD±{1k,8k,16k} 实测模拟残差（P 线注入）

输出：csv/l3_hratio_alias.csv
"""
import csv
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "csv")

FMOD = 4.096e6          # Hz, r5_datasheet_facts.md:30
FDATA = 128e3           # Hz, r5_datasheet_facts.md:31
OSR = 32                # r5_datasheet_facts.md:32
VREF = 2.442            # V, ADS131A02 内部基准
NBIT = 24
LSB_UV = VREF / (2 ** (NBIT - 1)) * 1e6   # 0.291 µV，与 t09_fold_check lsb_uv 一致
VSENSE_FS = 1.2         # V, 8µA×150k 全幅（CH1 信号）
VSAMPLE_47K = 8e-6 * 47e3  # 0.376 V（CH0 信号 @47k 样品标称样例）

CASES = ["FO1_BASE", "FO1_A", "FO1_B", "FO1_C"]
FSPOT = [0.0, 1e3, 8e3, 16e3]
FNAME = {0.0: "DC", 1e3: "1k", 8e3: "8k", 16e3: "16k"}


def sinc3(f):
    """ADS131A02 sinc³ 复传递函数（对 fMOD 归一，DC=1）。

    H(z) = [(1 - z^-OSR) / (OSR*(1 - z^-1))]^3, z = exp(j2πf/fMOD)
    零点位于 k·fDATA（= k·fMOD/OSR）；f→k·fMOD 处极限为 1。
    (1 - e^{-jx}) = 2j·sin(x/2)·e^{-jx/2} 闭式实现，避开 0/0。
    """
    if f == 0.0:
        return complex(1.0, 0.0)
    w = 2.0 * math.pi * f / FMOD
    num = complex(0.0, 1.0) * 2.0 * math.sin(w * OSR / 2.0) * complex(math.cos(-w * OSR / 2.0), math.sin(-w * OSR / 2.0))
    den = OSR * complex(0.0, 1.0) * 2.0 * math.sin(w / 2.0) * complex(math.cos(-w / 2.0), math.sin(-w / 2.0))
    if abs(den) < 1e-300:
        w2 = w + 1e-9
        den = OSR * complex(0.0, 1.0) * 2.0 * math.sin(w2 / 2.0) * complex(math.cos(-w2 / 2.0), math.sin(-w2 / 2.0))
    return (num / den) ** 3


def sinc3_db(f):
    return 20.0 * math.log10(abs(sinc3(f)) + 1e-300)


def sinc3_gd_us(f, df=1.0):
    """群延迟(µs) = -d(arg H)/df / 2π，中心差分。"""
    if f <= df:
        f = df
    a, b = sinc3(f - df), sinc3(f + df)
    p1 = math.atan2(a.imag, a.real)
    p2 = math.atan2(b.imag, b.real)
    dp = p2 - p1
    while dp > math.pi:
        dp -= 2 * math.pi
    while dp < -math.pi:
        dp += 2 * math.pi
    return -dp / (2 * math.pi) / (2 * df) * 1e6


def validate_sinc3():
    """对 r5_datasheet_facts.md 三个锚点自证实现。"""
    errs = []
    target = 10 ** (-3.0 / 20.0)
    lo, hi = 1.0, FDATA * 0.45
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if abs(sinc3(mid)) > target:
            lo = mid
        else:
            hi = mid
    f3db = 0.5 * (lo + hi)
    if abs(f3db - 33488.0) / 33488.0 > 0.01:
        errs.append("f3dB %.1f Hz vs 锚点 33488 Hz 偏差>1%%" % f3db)
    for f, ref in ((8e3, -0.17), (16e3, -0.67)):
        if abs(sinc3_db(f) - ref) > 0.01:
            errs.append("sinc3@%gHz %+.4f dB vs 锚点 %+.2f dB 偏差>0.01dB" % (f, sinc3_db(f), ref))
    gd0 = sinc3_gd_us(100.0, df=1.0)
    if abs(gd0 - 46.5 / FMOD * 1e6) > 0.02:
        errs.append("DC 群延迟 %.4f µs vs 闭式 11.3525 µs 不符" % gd0)
    if errs:
        raise AssertionError("sinc³ 实现自证失败: " + "; ".join(errs))
    return f3db, gd0


def read_csv(name):
    with open(os.path.join(CSV, name), newline="") as fh:
        return list(csv.DictReader(fh))


def fnum(s):
    return float(s) if s not in ("", None) else None


def wrap(r):
    rows.append(r)


rows = []
xcheck = []

def main():
    f3db, gd0 = validate_sinc3()
    print("[validate] sinc³ 过锚点自证: f3dB=%.1f Hz(锚33488), 8k=%+.4f dB, 16k=%+.4f dB, DC群延迟=%.4f µs(闭式 3·31/2/fMOD)" % (f3db, sinc3_db(8e3), sinc3_db(16e3), gd0))

    t01 = read_csv("t01_dm_ac.csv")
    t02 = read_csv("t02_cm_ac.csv")
    t03 = read_csv("t03_channel_match.csv")
    t10 = read_csv("t10_group_delay.csv")
    t09 = {(r["case"], float(r["f_inj_hz"])): fnum(r["resid_dm_db"]) for r in read_csv("t09_ac_residual.csv")}

    h0 = {r["case"]: r for r in t01 if r["port"] == "opa388"}
    h1 = {r["case"]: r for r in t01 if r["port"] == "kelvin"}
    t02k = {r["case"]: r for r in t02 if r["port"] == "kelvin"}
    t03d = {(r["case"], r["src"], r["f"]): r for r in t03}
    t10d = {(r["case"], r["channel"]): r for r in t10}

    # ---------- Block A: Hratio(f) 幅相（模拟 × sinc³ 复合） ----------
    for case in CASES:
        for src in ("real_src", "ideal0ohm"):
            for f in FSPOT:
                fn = FNAME[f]
                r3 = t03d[(case, src, fn)]
                hr_db = fnum(r3["Hratio_mag_dB"])
                hr_ph = fnum(r3["Hratio_ph_deg"])
                s_db = sinc3_db(f)
                h0a = fnum(r3["H0_mag_dB"])   # 与 Hratio 同源（t03），含 real_src 源阻抗
                h1a = fnum(r3["H1_mag_dB"])
                if f > 0 and src == "ideal0ohm":
                    # 消去演示仅在有复数相位数据的 ideal0ohm 行做（t01 ph_* 列为 0Ω 源）
                    p0 = math.radians(fnum(h0[case]["ph_%s_deg" % fn]))
                    p1 = math.radians(fnum(h1[case]["ph_%s_deg" % fn]))
                    c0 = 10 ** (h0a / 20) * complex(math.cos(p0), math.sin(p0))
                    c1 = 10 ** (h1a / 20) * complex(math.cos(p1), math.sin(p1))
                    S = sinc3(f)
                    rat_dig = 20 * math.log10(abs((c0 * S) / (c1 * S)))
                    ang = lambda c: math.degrees(math.atan2(c.imag, c.real))
                    ph_dig = ang((c0 * S) / (c1 * S))
                    canc_mag = abs(rat_dig - 20 * math.log10(abs(c0 / c1)))
                    dph = (ph_dig - ang(c0 / c1) + 180) % 360 - 180
                    canc_ph = abs(dph)
                else:
                    # real_src / DC：t01 无对应相位列（其 opa388 行是 0Ω 源），且 sinc³
                    # 在比值中精确消去 → dig 列 = t03 同源模拟值原样
                    rat_dig, ph_dig, canc_mag, canc_ph = hr_db, hr_ph, float("nan"), float("nan")
                wrap(dict(block="A_hratio", case=case, src=src, f=fn,
                          sinc3_dB="%+.4f" % s_db,
                          H0_ana_dB="%.4f" % h0a, H1_ana_dB="%.4f" % h1a,
                          Hratio_ana_dB="%+.5f" % hr_db, Hratio_ana_ph_deg="%+.4f" % hr_ph,
                          H0_dig_dB="%.4f" % (h0a + s_db), H1_dig_dB="%.4f" % (h1a + s_db),
                          Hratio_dig_dB="%+.5f" % rat_dig, Hratio_dig_ph_deg="%+.4f" % ph_dig,
                          R_err_ppm="%+.1f" % ((10 ** (hr_db / 20) - 1) * 1e6),
                          R_err_deg="%+.4f" % hr_ph,
                          sinc_cancel_resid_dB=("%.2e" % canc_mag) if canc_mag == canc_mag else "n/a",
                          note="sinc³ 两通道同设(全局 OSR)→比值中精确消去：ideal0ohm 行以复数乘除演示(残差见 sinc_cancel 列)，real_src 行 dig=ana(t01 无该源条件相位数据)；R_err=ΔR/R 幅度(ppm)/相位(deg)"))

            w = t03d[(case, src, "worst(1k-16k)")]
            wdb = fnum(w["Hratio_mag_dB"])
            wph = fnum(w["Hratio_ph_deg"])
            wrap(dict(block="A_hratio", case=case, src=src, f="worst(1k-16k)",
                      sinc3_dB="", H0_ana_dB="", H1_ana_dB="",
                      Hratio_ana_dB="%+.5f" % wdb, Hratio_ana_ph_deg="%+.4f" % wph,
                      H0_dig_dB="", H1_dig_dB="", Hratio_dig_dB="", Hratio_dig_ph_deg="",
                      R_err_ppm="%+.1f" % ((10 ** (wdb / 20) - 1) * 1e6),
                      R_err_deg="%+.4f" % wph,
                      sinc_cancel_resid_dB="",
                      note="|Hratio| p-p(dB) / |Δφ|max，t03 原口径；sinc³ 已消去"))

    # t01↔t03 一致性对拍
    bad = 0
    for case in CASES:
        for fn in ("1k", "8k", "16k"):
            d01 = fnum(h0[case]["g_%s_dB" % fn]) - fnum(h1[case]["g_%s_dB" % fn])
            d03 = fnum(t03d[(case, "ideal0ohm", fn)]["Hratio_mag_dB"])
            if abs(d01 - d03) > 0.001:
                bad += 1
                xcheck.append("WARN %s@%s: t01(H0-H1)=%+.5f vs t03=%+.5f" % (case, fn, d01, d03))
    if bad == 0:
        xcheck.append("t01(H0-H1) vs t03 Hratio 12 点全部 |Δ|<=0.001 dB OK")

    # ---------- Block B: 4.096MHz±{1k,8k,16k} 折叠风险（有界） ----------
    for case in CASES:
        for off in (0, 1e3, 8e3, 16e3):
            for sign in ("-", "+") if off else ("+",):
                finj = FMOD + (off if sign == "+" else -off)
                folded = abs(finj - round(finj / FMOD) * FMOD)
                s_fold = sinc3_db(folded) if folded > 0 else 0.0
                for port, d1 in (("CH0_opa388", fnum(h0[case]["D1_resid_dB"])),
                                 ("CH1_kelvin", fnum(h1[case]["D1_resid_dB"]))):
                    slope = 20 * math.log10(FMOD / finj)   # 一阶滚降斜率修正(理论估算)
                    resid = d1 + slope
                    total = resid + s_fold
                    uv100 = 0.1 * 10 ** (total / 20) * 1e6
                    ppm_ch1 = uv100 / VSENSE_FS
                    ppm_ch0 = uv100 / VSAMPLE_47K
                    t9 = t09.get((case, float("%.6g" % finj))) if port == "CH0_opa388" else None
                    t9s = "%+.3f" % t9 if t9 is not None else ""
                    if t9 is not None and port == "CH0_opa388" and abs(t9 - resid) > 0.15:
                        xcheck.append("WARN %s %.6f MHz CH0: L3斜率修正 %+.3f vs t09 实测 %+.3f dB" % (case, finj / 1e6, resid, t9))
                    note = "折叠至 %.3f kHz; analog_resid=t01 D1 %+0.3f dB + 斜率修正 %+0.3f dB(理论一阶滚降); 带内折回 dBc=analog+sinc3@folded; µV/100mV=%.1f; LSB/100mV=%.0f; R_err_ppm=ΔR/R per 100mV 注入@CH1(÷1.2V), CH0@47k 口径=%.1f ppm; sinc_cancel_resid_dB 列=t09 P线注入实测残差(仅 CH0 行, 同频点)" % (folded / 1e3, d1, slope, uv100, uv100 / LSB_UV, ppm_ch0)
                    wrap(dict(block="B_alias", case=case, src=port,
                              f="%.6fM" % (finj / 1e6),
                              sinc3_dB="%+.4f" % s_fold,
                              H0_ana_dB="%+.3f" % resid, H1_ana_dB="",
                              Hratio_ana_dB="", Hratio_ana_ph_deg="",
                              H0_dig_dB="%+.3f" % total, H1_dig_dB="",
                              Hratio_dig_dB="", Hratio_dig_ph_deg="",
                              R_err_ppm="%.1f" % ppm_ch1, R_err_deg="",
                              sinc_cancel_resid_dB=t9s,
                              note=note))

    # ---------- Block C: Kelvin 结构性 CM→DM 泄漏（in-band，sinc³ 不除） ----------
    for case in CASES:
        r2 = t02k[case]
        for fn, col, f in (("DC", "cmdm_dc_dB", 0.0), ("1k", "cmdm_1k_dB", 1e3),
                           ("8k", "cmdm_8k_dB", 8e3), ("16k", "cmdm_16k_dB", 16e3)):
            cmdm = fnum(r2[col])
            h1g = fnum(h1[case]["g_dc_dB"]) if fn == "DC" else fnum(h1[case]["g_%s_dB" % fn])
            ppm_per_Vcm = 10 ** ((cmdm - h1g) / 20) / VSENSE_FS * 1e6
            wrap(dict(block="C_cm_leak", case=case, src="CH1_kelvin_CMtoDM", f=fn,
                      sinc3_dB="%+.4f" % sinc3_db(f),
                      H0_ana_dB="", H1_ana_dB="%.4f" % h1g,
                      Hratio_ana_dB="", Hratio_ana_ph_deg="",
                      H0_dig_dB="", H1_dig_dB="",
                      Hratio_dig_dB="%+.3f" % cmdm, Hratio_dig_ph_deg="",
                      R_err_ppm="%.1f" % ppm_per_Vcm, R_err_deg="",
                      sinc_cancel_resid_dB="",
                      note="CM→DM=%+.2f dB(t02 kelvin 结构性); ΔR/R ppm per 1V CM=10^((CM→DM−H1)/20)/1.2V; sinc³ 同通道消去; CH0 对称网表为数值底非真实 CMRR"))

    # ---------- Block D: 群延迟复合（模拟 + sinc³） ----------
    for case in CASES:
        for ch, tcol in (("CH0", "CH0_opa388"), ("CH1", "CH1_kelvin")):
            r10 = t10d[(case, tcol)]
            for fn, f in (("1k", 1e3), ("8k", 8e3), ("16k", 16e3)):
                ta = fnum(r10["tau_%s_us" % fn])
                ts = sinc3_gd_us(f)
                wrap(dict(block="D_group_delay", case=case, src=ch, f=fn,
                          sinc3_dB="", H0_ana_dB="%.4f" % ta, H1_ana_dB="",
                          Hratio_ana_dB="", Hratio_ana_ph_deg="",
                          H0_dig_dB="%.4f" % (ta + ts), H1_dig_dB="",
                          Hratio_dig_dB="", Hratio_dig_ph_deg="",
                          R_err_ppm="", R_err_deg="",
                          sinc_cancel_resid_dB="%.4f" % ts,
                          note="tau_ana(t10,µs)+tau_sinc³(µs,数值微分); sinc³ 两通道相同→CH0-CH1 失配仍为模拟段值; D10 原口径仅评模拟段"))

    # ---------- 落盘 ----------
    out = os.path.join(CSV, "l3_hratio_alias.csv")
    cols = ["block", "case", "src", "f", "sinc3_dB", "H0_ana_dB", "H1_ana_dB",
            "Hratio_ana_dB", "Hratio_ana_ph_deg", "H0_dig_dB", "H1_dig_dB",
            "Hratio_dig_dB", "Hratio_dig_ph_deg", "R_err_ppm", "R_err_deg",
            "sinc_cancel_resid_dB", "note"]
    with open(out, "w", newline="") as fh:
        wtr = csv.DictWriter(fh, fieldnames=cols)
        wtr.writeheader()
        for r in rows:
            wtr.writerow(r)
    print("[write] %s (%d rows)" % (out, len(rows)))
    print("[xcheck] " + " | ".join(xcheck))

    print("")
    print("[summary] R 比值误差 worst(1k-16k, real_src):")
    for case in CASES:
        w = t03d[(case, "real_src", "worst(1k-16k)")]
        wdb, wph = fnum(w["Hratio_mag_dB"]), fnum(w["Hratio_ph_deg"])
        print("  %s: |Hratio| %+.5f dB (%+.1f ppm), dphi %+.4f deg" % (case, wdb, (10 ** (wdb / 20) - 1) * 1e6, wph))
    print("[summary] fMOD±16k 带内折回(每 100mV 注入):")
    for case in CASES:
        for tag, row in (("CH0", h0[case]), ("CH1", h1[case])):
            d1 = fnum(row["D1_resid_dB"])
            uv = 0.1 * 10 ** ((d1 + sinc3_db(16e3)) / 20) * 1e6
            print("  %s %s: D1=%+.2f dB -> %.1f µV (%.0f LSB, %+.1f ppm R@CH1口径)" % (case, tag, d1, uv, uv / LSB_UV, uv / VSENSE_FS))


if __name__ == "__main__":
    main()
