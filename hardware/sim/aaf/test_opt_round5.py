# -*- coding: utf-8 -*-
"""test_opt_round5.py — Round 5 优化引擎自洽性测试

对应计划 Task 2 Step 1/Step 4：
  * FIN1 旧参数回归（DM@fMOD = −123.5 dB ±0.5）
  * 二级/三级/四级都能求解且通带平坦度达标（新 fc 约束下最易崩的维度）
  * 单位纪律：settle_time() 返回秒 → 与 µs 预算比较前必须 ×1e6
  * 高级量测（快速建立/噪声/CMRR/群延迟）与引擎/解析值一致

运行：cd hardware/sim/aaf && python -m pytest test_opt_round5.py -v
"""

import math

import numpy as np
import pytest

import opt_engine
import opt_round5 as o5

FIN1 = [(330.0, 47e-9, 47e-9), (2700.0, 6.8e-9, 5.6e-9)]
W9 = [(1000.0, 8.2e-9, 8.2e-9), (220.0, 15e-9, 10e-9)]


# ---------------------------------------------------------------- 回归测试

def test_engine_regression_fin1():
    """计划 Task 2 Step 1 指定回归：FIN1 二级 @fMOD 应为 −123.5 dB ±0.5。"""
    h = opt_engine.H(FIN1, mode="dm", f=4.096e6)
    assert abs(20 * math.log10(abs(h[0])) - (-123.5)) < 0.5


def test_engine_regression_fin1_other_dims():
    """FIN1 其余旧战役实测值在**引擎原口径**（rs=1 Ω）下的理论值。

    第 2 轮起默认源模型是真实 OPA388（source='opa388'），本条回归必须显式
    指定 source='engine' 才能对上旧战役的 1 Ω 镜像网表。
    """
    assert o5.gain_db(FIN1, "dm", 4.096e6, source="engine") == pytest.approx(-123.54, abs=0.5)
    assert o5.gain_db(FIN1, "cm", 4.096e6, source="engine") == pytest.approx(-105.54, abs=0.5)
    assert o5.gain_db(FIN1, "dm", 16.384e6, source="engine") == pytest.approx(-147.62, abs=0.5)


def test_engine_regression_w9():
    """W9（上一轮冠军）回归：DM −102.0 / CM −85.1 / MCLK −126.1 dB。"""
    assert o5.gain_db(W9, "dm", 4.096e6, source="engine") == pytest.approx(-101.98, abs=0.5)
    assert o5.gain_db(W9, "cm", 4.096e6, source="engine") == pytest.approx(-85.09, abs=0.5)
    assert o5.gain_db(W9, "dm", 16.384e6, source="engine") == pytest.approx(-126.06, abs=0.5)


# ------------------------------------------------------------ 引擎等价性

@pytest.mark.parametrize("stages", [FIN1, W9, [(3.33, 100e-9, 0.0)] * 4])
def test_h_vec_matches_engine(stages):
    """向量化 h_vec 在 source='engine'（rs=1 Ω、增益=1）下必须与 opt_engine.H 逐点一致。"""
    f = [0.1, 1e3, 16e3, 1e5, 4.096e6, 16.384e6]
    got = o5.h_vec(stages, "dm", f, source="engine")
    ref = np.array([opt_engine.H(stages, "dm", x)[0] for x in f])
    assert np.allclose(got, ref, rtol=1e-12, atol=0)


def test_h_vec_uses_real_follower_by_default():
    """默认源模型必须是真实 OPA388（Zout(f) + G(f)），且与 1 欧引擎口径不同。

    第 2 轮的核心口径纠正：fMOD 处 |Z_o,cl| 约 42 欧，远大于 1 欧。
    注意 FIN1/W9 在 fMOD 处已有 -120 dB 量级衰减，三种源模型在**那里**的差别不大
    （源阻抗被 3.3 kOhm 首级 R 淹没）；差别显著的是 R1 只有几欧的现代拓扑。
    """
    assert o5.SOURCE_MODEL == "opa388"
    # 现代拓扑：首级 R 只有几欧，fMOD 处 42 欧源阻抗就是主导项
    st = [(3.6, 1e-7, 0.0), (4.7, 8.2e-8, 0.0), (5.6, 4.7e-8, 0.0), (5.1, 3.9e-8, 2.7e-8)]
    a = o5.gain_db(st, "dm", 4.096e6, source="engine")
    b = o5.gain_db(st, "dm", 4.096e6)          # 默认 = 真实跟随器
    assert abs(a - b) > 3.0, "真实跟随器与 1 欧引擎口径应差 >3 dB，实测 %.2f" % (b - a)
    # 通带内跟随器近理想：16 kHz 处与理想源差 <0.6 dB（Gate G(f) 在 16 kHz 是 -0.005 dB，
    # 主要是 Z_o,cl 的 17 mohm 与首级 R 的比值可忽略；但 C 阶梯的 DC 增益被 1 pF 源寄生略拉）
    ideal = o5.gain_db(st, "dm", 16e3, source="ideal")
    real = o5.gain_db(st, "dm", 16e3)
    assert abs(ideal - real) < 0.6


@pytest.mark.parametrize("stages", [FIN1, W9, [(3.33, 100e-9, 0.0)] * 4])
def test_settle_time_fast_matches_engine(stages):
    """快速建立时间（对称广义特征分解）必须与 opt_engine.settle_time（expm）一致。

    opt_engine 的源内阻固定 1 欧，故这里显式传 rs=1.0 做同口径对拍。
    """
    for tol_r, tol_c in ((0.0, 0.0), (0.01, 0.05)):
        # opt_engine 的 tol_r 同时作用于**源内阻**（rs=1*(1+tol_r)），
        # 而 o5 的 rs 是独立参数 → 对拍时须手动代入同一个 rs
        a = o5.settle_time_fast(stages, "dm", o5.SETTLE_BAND_V, tol_r, tol_c,
                                rs=1.0 * (1 + tol_r))
        b = opt_engine.settle_time(stages, "dm", o5.SETTLE_BAND_V, tol_r, tol_c)
        assert a == pytest.approx(b, rel=1e-6)


def test_settle_time_includes_600k_high_z_case():
    """§5.1 D5 点名的 600 kΩ 高源阻抗工况必须比 0 Ω 基线更慢（tau = 600k x 8.5p = 5.1 us）。"""
    st = [(3.6, 1e-7, 0.0), (4.7, 8.2e-8, 0.0), (5.6, 4.7e-8, 0.0), (5.1, 3.9e-8, 2.7e-8)]
    base = o5.settle_time_fast(st, "dm", o5.SETTLE_BAND_V, 0.01, 0.05, rs=0.3)
    hz = o5.settle_time_fast(st, "dm", o5.SETTLE_BAND_V, 0.01, 0.05, rs=0.3,
                             pre_rc=o5.HIGH_Z_PRE_RC)
    assert np.isfinite(hz) and hz > base
    assert 40e-6 < hz < 70e-6, "应与 LTspice V4b 的 52 us 同量级，实测 %.1f us" % (hz * 1e6)


def test_settle_time_units_are_seconds():
    """单位纪律：settle_time() 返回秒；FIN1 容差最坏角 ≈720 µs（不是 720 s）。"""
    t = opt_engine.settle_time(FIN1, "dm", 60e-6, tol_r=0.01, tol_c=0.05)
    assert 100e-6 < t < 2e-3, f"返回值应为秒，得到 {t}"
    assert t * 1e6 == pytest.approx(720.5, rel=0.02)


def test_settle_band_matches_001pct():
    """0.01% 建立带 = 60 µV（单边，差分 2.4 Vpp）。"""
    assert o5.SETTLE_BAND_V == pytest.approx(60e-6)


# ---------------------------------------------------------------- 量测自洽

def test_noise_model_matches_kT_C():
    """**无源部分**对单级 RC 应回到噪声带宽 x kT/C 的差分式 sqrt(2)*sqrt(kT/C)。

    第 2 轮起 noise_breakdown_lsb 把跟随器噪声单列（lsb_follower），
    故这里只对 lsb_passive 做 kT/C 校验 —— 旧版直接用总量，会被 9.9 nV/rtHz
    的跟随器项淹没（该项与 C 无关，不满足 kT/C 关系）。
    """
    old = o5.ADC_ZIN
    try:
        o5.ADC_ZIN = 1e15                      # 去掉 ADC 负载
        # 只取 fc 远低于积分上限 fMOD/2 = 2.048 MHz 的用例：1 kΩ/1 nF 的 fc=158 kHz，
        # 其 ENBW 有 5% 落在积分上限之外，会系统性偏低（不是模型错，是积分截断）
        for R, C in ((10e3, 100e-9), (10e3, 10e-9), (100.0, 1e-6)):
            nb = o5.noise_breakdown_lsb([(R, C, 0.0)], npts=4000)
            v = nb["lsb_passive"] * o5.LSB_V
            ktc = math.sqrt(o5.K_B * o5.T_K / C)
            assert v == pytest.approx(math.sqrt(2.0) * ktc, rel=0.10)
    finally:
        o5.ADC_ZIN = old


def test_follower_noise_dominates():
    """跟随器差分噪声（9.905 nV/rtHz）必须主导总噪声 —— 这是第 1 轮漏掉的那一项。"""
    st = [(3.6, 1e-7, 0.0), (4.7, 8.2e-8, 0.0), (5.6, 4.7e-8, 0.0), (5.1, 3.9e-8, 2.7e-8)]
    nb = o5.noise_breakdown_lsb(st)
    assert nb["lsb_follower"] > 5.0 * nb["lsb_passive"], nb
    assert nb["lsb"] > max(nb["lsb_follower"], nb["lsb_passive"])


def test_cmrr_matches_two_line_mna():
    """CM 模态下两线解耦——用两线全 MNA 复核引擎的 tol_r/tol_c 口径。"""
    st = [(3.33, 100e-9, 0.0)] * 4
    n, m = len(st), len(st) + 1
    G = np.zeros((2 * m, 2 * m))
    C = np.zeros((2 * m, 2 * m))
    for line in range(2):
        off = 0 if line == 0 else m
        tr = 0.01 if line == 0 else 0.0
        tc = 0.01 if line == 0 else 0.0
        G[off, off] += 1.0 / (1.0 * (1 + tr))
        C[off, off] += 1e-12
        for i, (r, cg, _cd) in enumerate(st):
            rv = r * (1 + tr)
            a, b = off + i, off + i + 1
            G[a, a] += 1 / rv; G[b, b] += 1 / rv
            G[a, b] -= 1 / rv; G[b, a] -= 1 / rv
            C[b, b] += cg * (1 + tc)
    a, b = m - 1, 2 * m - 1
    G[a, a] += 1 / 130e3; G[b, b] += 1 / 130e3
    G[a, b] -= 1 / 130e3; G[b, a] -= 1 / 130e3
    C[a, a] += 5e-12; C[b, b] += 5e-12
    # 引擎的源是「电压源 1 V + 内阻 Rs」，等效为向节点 0 注入 1/Rs 的电流
    rhs = np.zeros(2 * m); rhs[0] = 1.0 / 1.01; rhs[m] = 1.0
    f = 16e3
    v = np.linalg.solve(G + 1j * 2 * math.pi * f * C, rhs)
    cm = (v[a] + v[b]) / 2
    dm = v[a] - v[b]
    two_line = -20 * math.log10(abs(dm) / abs(cm))
    # 第 2 轮起用精确双线 MNA（cmrr_two_line），与上面的手工两线 MNA 同口径
    # 手工网表里两线的**源内阻**也带 1% 失配（rhs[0]=1/1.01），而 cmrr_two_line 的
    # 源阻抗对两线相同（跟随器输出阻抗不受电阻容差影响）→ 两者差 0.48 dB 属口径差异。
    assert o5.cmrr_two_line(st, mism=0.01, f_lo=f, f_hi=f, npts=1,
                            source="engine") == pytest.approx(two_line, abs=0.6)


def test_fc_scaling_law():
    """R 等比缩放 ⇒ 极点频率近似等比反向移动（fc ∝ 1/R）。

    不是严格恒等式：引擎的源内阻 RS=1 Ω 与 130 kΩ 差分负载**不随 R 缩放**。
    在 R≫RS、R≪65 kΩ 的区间（本例 R=100 Ω）偏差约 2%；
    ``build_from_x()`` 用 3 次「缩放 + 复测」把 fc 收敛到目标 2% 内。
    """
    base = [(300.0, 1e-9, 0.0)] * 3 + [(300.0, 1e-9, 0.2e-9)]
    f0 = o5.fc_dm(base)
    # 缩短 R 会把 fc 抬高；R=300 Ω 时 fc=54 kHz，再缩 20 倍即到 1 MHz 量级
    assert 40e3 < f0 < 80e3, f0
    for s in (0.5, 0.25, 0.1):
        st = [(r * s, c, d) for r, c, d in base]
        # R 缩到 30 Ω 量级时已与 |Z_o,cl| 同量级，1/R 律有 10-20% 偏差（物理事实，非 bug）
        assert o5.fc_dm(st) == pytest.approx(f0 / s, rel=0.20)


def test_build_from_x_hits_fc_target():
    """参数化必须让 fc 精确落入目标（新 fc 约束是硬门槛）。"""
    n = 4
    x = ([math.log(2.0)] * n + [math.log(60e-9)] * n
         + [math.log(30e-9), math.log(65e3)])
    stages, fc_t = o5.build_from_x(x, n)
    assert fc_t == pytest.approx(65e3)
    assert o5.fc_dm(stages) == pytest.approx(65e3, rel=0.02)


# ------------------------------------------------------------ 评分与约束

def test_dim_scores_ranges_and_thresholds():
    """十维分数必须落在 [0,1]，且阈值两侧行为与规格 §5.1 一致。"""
    pred = o5.predict([(8.0, 100e-9, 0.0)] * 4)
    dims = o5.dim_scores(pred)
    assert set(dims) == {f"D{i}" for i in range(1, 11)}
    assert all(0.0 <= v <= 1.0 for v in dims.values())
    # D4：≤0.05 dB 满分，>0.5 dB 归零
    assert o5.dim_scores({**pred, "dG_16k": 0.04})["D4"] == 1.0
    assert o5.dim_scores({**pred, "dG_16k": 0.51})["D4"] == 0.0
    # D1：§5.1 = min(x/120, 1)（不是线性插值到及格线；第 1 轮写成 _lerp 是 bug）
    assert o5.dim_scores({**pred, "A_dm": 120.0})["D1"] == 1.0
    assert o5.dim_scores({**pred, "A_dm": 60.0})["D1"] == pytest.approx(0.5)
    assert o5.dim_scores({**pred, "A_dm": 79.9})["D1"] == pytest.approx(79.9 / 120)
    # D6：§5.1 = min(0.3/x, 1)
    assert o5.dim_scores({**pred, "V_n_lsb": 0.3})["D6"] == 1.0
    assert o5.dim_scores({**pred, "V_n_lsb": 0.6})["D6"] == pytest.approx(0.5)
    assert o5.dim_scores({**pred, "V_n_lsb": 3.0})["D6"] == pytest.approx(0.1)


def test_predict_keys_contract():
    """计划 Task 2 的接口契约：pred 必须含六个指定键，时间单位为秒。"""
    pred = o5.predict([(8.0, 100e-9, 0.0)] * 4)
    for key in ("A_dm", "A_cm", "A_mclk", "dG_16k", "t_settle_wc_s", "group_delay_flat_s"):
        assert key in pred
    assert 1e-6 < pred["t_settle_wc_s"] < 1e-2        # 秒
    assert pred["group_delay_flat_s"] < 1e-4          # 秒


def test_hard_checks_flag_fc_violation():
    """fc 越界必须被 hard_checks 判为不满足（新约束的核心）。"""
    slow = [(1000.0, 10e-9, 0.0), (1000.0, 10e-9, 5e-9)]        # fc≈12 kHz
    fast = [(0.05, 47e-9, 0.0), (0.05, 47e-9, 5e-9)]             # fc≫80 kHz
    assert o5.hard_checks(o5.predict(slow))["fc_in_range"] is False
    assert o5.hard_checks(o5.predict(fast))["fc_in_range"] is False


def test_kickback_proxy_rejects_small_bucket():
    """D9 代理：引脚本地电容不足 35 nF（droop>0.01%）必须判不及格。"""
    _, _, ok_big = o5.kickback_ns([(10.0, 47e-9, 0.0), (10.0, 47e-9, 22e-9)])
    _, _, ok_small = o5.kickback_ns([(10.0, 1e-9, 0.0), (10.0, 1e-9, 0.5e-9)])
    assert ok_big is True
    assert ok_small is False


# -------------------------------------------------------------- 求解器测试

@pytest.mark.parametrize("n_stages", [2, 3, 4])
def test_solve_candidate_contract(n_stages):
    """solve_candidate 的结构契约 + 硬约束（含新 fc 区间）。

    ``maxiter=40`` 只是契约冒烟测试，**不保证**收敛到可行解 —— 因此断言分两层：
    结构（级数/三元组/fc 夹紧/ΣR/单电容）必须永远成立；
    "全部硬约束满足"只在 ``meta['feasible']`` 为真时才有意义。
    """
    r = o5.solve_candidate(n_stages, seed=0, maxiter=40, n_starts=2)
    assert len(r["stages"]) == n_stages
    assert all(len(s) == 3 for s in r["stages"])
    assert o5.FC_LO * (1 - 5e-4) <= r["pred"]["f_c_hz"] <= o5.FC_HI * (1 + 5e-4)
    assert r["pred"]["r_sum_ohm"] <= o5.R_SUM_MAX
    assert r["pred"]["c_max_f"] <= o5.C_MAX
    assert all(s[2] == 0.0 for s in r["stages"][:-1]), "C_diff 只允许末级"
    if r["meta"]["feasible"]:
        assert all(o5.hard_checks(r["pred"]).values()), r["meta"]["hard"]


def test_solve_candidate_respects_r_minimum():
    """R 不得低于 1 Ω（E24 最小档）：低于此值时跟随器输出阻抗反成串阻，且不可制造。"""
    r = o5.solve_candidate(3, seed=0, maxiter=40, n_starts=2)
    assert min(s[0] for s in r["stages"]) >= 1.0 - 1e-9


def test_two_stage_passband_flatness():
    """计划 Task 2 Step 1 的断言：二级解的通带平坦度必须达标（≤0.5 dB）。"""
    r = o5.solve_candidate(2, seed=0, maxiter=40, n_starts=2)
    assert r["pred"]["dG_16k"] <= 0.5


def test_solve_candidate_is_deterministic():
    """同 seed 必须复现（结果可审计、可复算）。"""
    a = o5.solve_candidate(3, seed=0, maxiter=12, n_starts=1)
    b = o5.solve_candidate(3, seed=0, maxiter=12, n_starts=1)
    assert a["stages"] == b["stages"]
    assert a["pred"]["A_dm"] == pytest.approx(b["pred"]["A_dm"], rel=1e-9)


def test_candidate_has_cdiff_only_on_last_stage():
    """结构约束（规格 §4）：C_diff 只出现在末级跨接。"""
    r = o5.solve_candidate(3, seed=0, maxiter=10, n_starts=1)
    assert all(s[2] == 0.0 for s in r["stages"][:-1])


def test_rank_key_prefers_more_passing_dims():
    """排序键：先比「过线维数」，再比 min（短板制）。"""
    good = {"pred": {"A_dm": 130, "A_cm": 110, "A_mclk": 160, "dG_16k": 0.04,
                     "t_settle_wc_s": 100e-6, "V_n_lsb": 0.2, "sigma_dG_db": 0.005,
                     "CMRR_pb_db": 110, "kickback_ok": True,
                     "group_delay_flat_s": 0.5e-6},
            "dims": {k: 1.0 for k in [f"D{i}" for i in range(1, 11)]},
            "meta": {"min_score": 1.0}}
    poor = {"pred": {"A_dm": 90, "A_cm": 70, "A_mclk": 120, "dG_16k": 0.3,
                     "t_settle_wc_s": 700e-6, "V_n_lsb": 0.9, "sigma_dG_db": 0.04,
                     "CMRR_pb_db": 85, "kickback_ok": True,
                     "group_delay_flat_s": 4e-6},
            "dims": {k: 0.2 for k in [f"D{i}" for i in range(1, 11)]},
            "meta": {"min_score": 0.2}}
    assert o5.rank_key(good) > o5.rank_key(poor)


# ------------------------------------------------------------- 物理天花板

def test_kt_c_ceiling_note():
    """D6 的全 1.0（≤0.3 LSB）在现有 C≤100 nF 约束下不可达 —— 记录物理下限。"""
    c_max_pin = 3 * o5.C_MAX                     # 单级最多 C_gnd + 2·C_diff
    v_min = math.sqrt(2) * math.sqrt(o5.K_B * o5.T_K / c_max_pin)
    assert v_min / o5.LSB_V > 0.3, "若此断言失败说明约束或 LSB 定义变了，需复核 D6 阈值"


def test_cmrr_1pct_mismatch_ceiling():
    """D8 及格线 80 dB 与 §5.1a「两线 1% 失配角」自相矛盾（量级 40-55 dB）。

    用真实跟随器口径（cmrr_two_line 默认 source='opa388'）。
    """
    for st in ([(8.0, 100e-9, 0.0)] * 4, [(3.33, 100e-9, 0.0)] * 4,
               [(2.4, 1e-7, 0.0), (13.0, 1e-7, 18e-9)]):
        cmrr = o5.cmrr_two_line(st, mism=0.01)
        assert 30.0 < cmrr < 60.0, cmrr
        assert cmrr < o5.TH["D8"][1], "若 1% 失配下 CMRR 仍能过 80 dB，说明口径已变"
        req = o5.cmrr_required_mismatch(st, 80.0)
        assert req < 0.002, "80 dB 需失配 <=%.4f%%，应为 0.0x%% 量级" % (req * 100)


def test_peaking_is_a_hard_constraint():
    """跟随器感性 Z_o 与阶梯的谐振必须被 hard_checks 拦下（A 案实测 +30.7 dB @283 kHz）。"""
    bad = [(1.1, 100e-9, 0.0), (13.0, 100e-9, 27e-9)]
    p = o5.predict(bad)
    assert p["peaking_db"] > o5.PEAK_MAX_DB, p["peaking_db"]
    assert o5.hard_checks(p)["peaking"] is False
    good = [(2.4, 100e-9, 0.0), (13.0, 100e-9, 18e-9)]
    assert o5.hard_checks(o5.predict(good))["peaking"] is True
