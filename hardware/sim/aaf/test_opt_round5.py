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
    """FIN1 其余旧战役实测值（README 第四轮表）在引擎下的理论值。"""
    assert o5.gain_db(FIN1, "dm", 4.096e6) == pytest.approx(-123.54, abs=0.5)
    assert o5.gain_db(FIN1, "cm", 4.096e6) == pytest.approx(-105.54, abs=0.5)
    assert o5.gain_db(FIN1, "dm", 16.384e6) == pytest.approx(-147.62, abs=0.5)


def test_engine_regression_w9():
    """W9（上一轮冠军）回归：DM −102.0 / CM −85.1 / MCLK −126.1 dB。"""
    assert o5.gain_db(W9, "dm", 4.096e6) == pytest.approx(-101.98, abs=0.5)
    assert o5.gain_db(W9, "cm", 4.096e6) == pytest.approx(-85.09, abs=0.5)
    assert o5.gain_db(W9, "dm", 16.384e6) == pytest.approx(-126.06, abs=0.5)


# ------------------------------------------------------------ 引擎等价性

@pytest.mark.parametrize("stages", [FIN1, W9, [(3.33, 100e-9, 0.0)] * 4])
def test_h_vec_matches_engine(stages):
    """向量化 h_vec 必须与 opt_engine.H 逐点一致（相对误差 <1e-12）。"""
    f = [0.1, 1e3, 16e3, 1e5, 4.096e6, 16.384e6]
    got = o5.h_vec(stages, "dm", f)
    ref = np.array([opt_engine.H(stages, "dm", x)[0] for x in f])
    assert np.allclose(got, ref, rtol=1e-12, atol=0)


@pytest.mark.parametrize("stages", [FIN1, W9, [(3.33, 100e-9, 0.0)] * 4])
def test_settle_time_fast_matches_engine(stages):
    """快速建立时间（特征分解）必须与 opt_engine.settle_time（expm）一致。"""
    for tol_r, tol_c in ((0.0, 0.0), (0.01, 0.05)):
        a = o5.settle_time_fast(stages, "dm", o5.SETTLE_BAND_V, tol_r, tol_c)
        b = opt_engine.settle_time(stages, "dm", o5.SETTLE_BAND_V, tol_r, tol_c)
        assert a == pytest.approx(b, rel=1e-6)


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
    """噪声模型对单级 RC 应回到噪声带宽 × kT/C 的差分式 √(2)·√(kT/C)。"""
    old = o5.ADC_ZIN
    try:
        o5.ADC_ZIN = 1e15                      # 去掉 ADC 负载
        for R, C in ((10e3, 100e-9), (1e3, 1e-9), (100.0, 1e-6)):
            v = o5.integrated_noise_lsb([(R, C, 0.0)], npts=4000) * o5.LSB_V
            ktc = math.sqrt(o5.K_B * o5.T_K / C)
            assert v == pytest.approx(math.sqrt(2.0) * ktc, rel=0.10)
    finally:
        o5.ADC_ZIN = old


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
    assert o5.cmrr_passband_db(st, f_lo=f, f_hi=f, npts=1) == pytest.approx(two_line, abs=0.2)


def test_fc_scaling_law():
    """R 等比缩放 ⇒ 极点频率近似等比反向移动（fc ∝ 1/R）。

    不是严格恒等式：引擎的源内阻 RS=1 Ω 与 130 kΩ 差分负载**不随 R 缩放**。
    在 R≫RS、R≪65 kΩ 的区间（本例 R=100 Ω）偏差约 2%；
    ``build_from_x()`` 用 3 次「缩放 + 复测」把 fc 收敛到目标 2% 内。
    """
    base = [(100.0, 1e-9, 0.0)] * 3 + [(100.0, 1e-9, 0.2e-9)]
    f0 = o5.fc_dm(base)
    assert f0 > 100e3, "该用例应落在 R≫RS（100 Ω vs 1 Ω）、fc 高的区间"
    for s in (0.25, 4.0):
        st = [(r * s, c, d) for r, c, d in base]
        assert o5.fc_dm(st) == pytest.approx(f0 / s, rel=0.05)


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
    # D1：≥120 dB 满分，<80 dB 归零
    assert o5.dim_scores({**pred, "A_dm": 120.0})["D1"] == 1.0
    assert o5.dim_scores({**pred, "A_dm": 79.9})["D1"] == 0.0


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
    """solve_candidate 的结构契约 + 硬约束（含新 fc 区间）。"""
    r = o5.solve_candidate(n_stages, seed=0, maxiter=40, n_starts=2)
    assert len(r["stages"]) == n_stages
    assert all(len(s) == 3 for s in r["stages"])
    assert r["pred"]["f_c_hz"] >= o5.FC_LO
    assert r["pred"]["f_c_hz"] <= o5.FC_HI
    assert r["pred"]["r_sum_ohm"] <= o5.R_SUM_MAX
    assert r["pred"]["c_max_f"] <= o5.C_MAX
    assert all(o5.hard_checks(r["pred"]).values()), r["meta"]["hard"]


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
    """D8 及格线 80 dB 与 §5.1a「两线 1% 失配角」自相矛盾（量级 ≈37–47 dB）。"""
    for st in ([(8.0, 100e-9, 0.0)] * 4, [(3.33, 100e-9, 0.0)] * 4):
        cmrr = o5.cmrr_passband_db(st, mism=0.01)
        assert 30.0 < cmrr < 50.0, cmrr
        assert cmrr < o5.TH["D8"][1], "若 1% 失配下 CMRR 仍能过 80 dB，说明口径已变"
