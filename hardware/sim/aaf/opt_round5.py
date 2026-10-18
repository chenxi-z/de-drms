# -*- coding: utf-8 -*-
"""opt_round5.py — Round 5 抗混叠采集阶梯：十维理论预测 + Nelder-Mead 多起点求解

规格：docs/design/spec/2026-10-18-aa-driver-design.md（v4：§5 十维评分 / §4 架构 / §5.2 硬约束）
计划：docs/design/spec/2026-10-18-aa-driver-plan.md（Task 2 / Task 3）

把规格 §5.1 的 D1–D10 全部落到**理论预测**（不含 LTspice）：
  D1 A_dm@fMOD   D2 A_cm@fMOD   D3 A_dm@MCLK   D4 通带平坦度@16k   D5 容差最坏角建立
  D6 积分噪声    D7 容差敏感度    D8 CMRR@通带    D9 kickback 回稳   D10 群延迟平坦度

单位纪律（前战役踩过的坑，写成硬规则）：
  * ``settle_time()`` 返回 **秒**；与 µs 预算（500/900 µs）比较前**必须 ×1e6**。
  * ``predict()["t_settle_wc_s"]`` 与 ``group_delay_flat_s`` 保持 **秒**（引擎口径）；
    ``dim_scores()`` 内部统一换算后再与 µs 阈值比较。
  * LSB = 2 × 2.442 V / 2**24 = 290.98 nV（规格 §5.1 单位约定）。

新约束（规格 §3 + 计划 Task 2 Step 3）：fc ∈ [50 kHz, 80 kHz]（DM −3 dB 整体拐点，
由 16 kHz 平坦度 ≤0.5 dB 反推）；ΣR ≤5 kΩ；单电容 ≤100 nF；settle_wc ≤900 µs；ΔG@16k ≤0.5 dB。

拓扑（规格 §4 定稿）：每线 R_i + 对地 C_gnd,i 串联成阶梯；两线**末级**之间跨接 C_diff
（差分电容只允许出现在最后一级，落到引擎里即 ``stages[-1][2] = C_diff``）。

============ Round 5 第 2 轮修订（2026-10-18，口径纠正） ============

1. **评分 bug 修复**：第 1 轮 ``dim_scores()`` 把 D1/D2/D3/D5/D6/D8 全用 ``_lerp`` 线性插值，
   与规格 §5.1 的 ``min(x/满分,1)``（越大越好）/ ``min(满分/x,1)``（越小越好）不符。
   现已按 §5.1 逐条实现（见 ``dim_scores``）。

2. **源阻抗口径纠正（本轮核心）**：第 1 轮理论引擎把源内阻硬编码为 1 Ω，
   而真实 OPA388 跟随器闭环输出阻抗随频率变化：通带 ≈0.02–0.25 Ω、fMOD ≈34–42 Ω。
   1 Ω 恒定值在通带**过悲观**、在 fMOD **过乐观**，两端都错。
   现改用 M7 手册数据的复频模型：

       Z_o,cl(f) = Z_o,ol(f) / (1 + A_OL(f))          （单位增益跟随器，β = 1）
       Z_o,ol(f) ← SBOS777D Fig.6-25 逐点读数（查表 log-log 插值）
       A_OL(f)   = A0 / (1 + j·f/fp)，A0 = 148 dB，fp = GBW/A0 = 0.398 Hz

   注意 M7 文档里写的 "≈34 Ω @4.096 MHz" 是**标量除法** |Z_ol|/(1+|A|)；
   复频形式给出 |Z_cl| = 41.7 Ω（含 68° 相位），与 TI OPAx388 SPICE 模型
   1 mA 注入实测的 41.1 Ω **吻合到 1.5%**，故复频形式更可信（见 ``zout_cl``）。

3. **D6 噪声模型补全**：第 1 轮只算无源阶梯自身约翰逊噪声（≈0.97 LSB），
   漏掉跟随器输入噪声（器件定稿、不可改）。现按 V7/V9d 同构计入
   ``en,diff = √2 × 7.07 nV/√Hz = 9.905 nV/√Hz``（TI 模型 ``foll_noise.net`` 实测 9.905）。

4. **D8 用精确双线 MNA**：第 1 轮用 ``tol_r/tol_c`` 对单线 CM 传函做差分，
   在两线**完全相同器件**时是精确的（CM 模态两线解耦），但无法做逐元件随机失配。
   现改为 2×(n+1) 节点全 MNA，含 C_diff 与 130 kΩ 差分负载的耦合项，可做蒙特卡洛。
"""

from __future__ import annotations

import argparse
import json
import math
import os

import numpy as np
from scipy.linalg import eigh
from scipy.optimize import minimize

HERE = os.path.dirname(os.path.abspath(__file__))
FACTS_MD = os.path.join(HERE, "r5_datasheet_facts.md")

# ----------------------------------------------------------------------------
# 0. FACTS —— Task 1 的手册核实值（r5_datasheet_facts.md §1 python 代码块）
# ----------------------------------------------------------------------------

_FALLBACK_FACTS = {
    "MCLK_HZ": 16.384e6,
    "FMOD_HZ": 4.096e6,
    "FDATA_HZ": 128e3,
    "OSR": 32,
    "SINC3_F3DB_HZ": 33790.0,
    "SINC3_ATT_16K_DB": -0.67,
    "ADC_CS_PF": 3.5,
    "ADC_ZIN_OHM": 130e3,
    "ADC_RSW_OHM": None,
    "ADC_RSW_ASSUMPTION_OHM": 1.0,
    "ADC_SW_DUTY": 0.5,
    "ADC_SW_FREQ_HZ": 4.096e6,
    "OPA388_AOL_4M_DB": 7.0,
    "OPA388_GBW_HZ": 10e6,
}


def load_facts(path: str = FACTS_MD) -> dict:
    """从 Task 1 的 r5_datasheet_facts.md 抽出 FACTS 字典（缺失则回退同值副本）。"""
    facts = dict(_FALLBACK_FACTS)
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return facts
    i = text.find("```python")
    if i < 0:
        return facts
    j = text.find("```", i + 9)
    if j < 0:
        return facts
    ns: dict = {}
    try:
        exec(text[i + 9:j], ns)  # noqa: S102 —— 本仓库自有文档
    except Exception:
        return facts
    blk = ns.get("FACTS")
    if isinstance(blk, dict):
        facts.update(blk)
    return facts


FACTS = load_facts()

FMOD_HZ = float(FACTS["FMOD_HZ"])                 # 4.096 MHz
MCLK_HZ = float(FACTS["MCLK_HZ"])                 # 16.384 MHz
ADC_CS_F = float(FACTS["ADC_CS_PF"]) * 1e-12      # 3.5 pF（差分）
ADC_RSW = float(FACTS["ADC_RSW_ASSUMPTION_OHM"])  # 1 Ω（手册未给，规格 §7 缺省）
ADC_ZIN = float(FACTS["ADC_ZIN_OHM"])             # 130 kΩ 差分

LSB_V = 2.0 * 2.442 / 2 ** 24            # 290.98 nV（规格 §5.1）
K_B = 1.380649e-23
T_K = 298.15
R_SUM_MAX = 5e3
C_MAX = 100e-9
FC_LO, FC_HI = 50e3, 80e3
SETTLE_BUDGET_US = 900.0
SETTLE_BAND_V = 60e-6                     # 0.01% 建立带（单边；差分 2.4 Vpp → 120 µV）
DG_MAX_DB = 0.5                           # 通带平坦度硬门槛（D4 及格线）
KB_HALF_PERIOD_S = 0.5 / FMOD_HZ          # 122.07 ns

# 规格 §5.1 阈值（满分, 及格线）；D9 为二值维度
TH = {
    "D1": (120.0, 80.0), "D2": (100.0, 60.0), "D3": (150.0, 100.0),
    "D4": (0.05, 0.50), "D5": (500.0, 900.0), "D6": (0.3, 1.0),
    "D7": (0.01, 0.05), "D8": (100.0, 80.0), "D10": (1.0, 5.0),
}

# D8 的失配考核口径（规格 §5.1 D8「两线阶梯 1% 失配角」+ 本轮新增的配对筛选口径）
D8_MISMATCH = 0.01          # 规格原口径（V3：整条线 R/C ×1.01）
D8_MISMATCH_SEL = 5e-4      # 配对筛选后 0.05%（本轮新增评估口径）

# D5 的高源阻抗工况（规格 §5.1「样品 600 kΩ 端」）：
#   600 kΩ ∥ 跟随器输入电容 8.5 pF（OPAx388.LIB C_C_COM0/1 + C_C_DIFF，
#   与 gen_netlists_r5.py V4b 的悲观上界同口径）→ τ = 5.1 µs
HIGH_Z_PRE_RC = (600e3, 8.5e-12)

# 最小作用量维度：能在拓扑/参数层面推动的 8 维（D6/D8 由器件与匹配决定，见 §6）
ACTIONABLE = ("D1", "D2", "D3", "D4", "D5", "D7", "D9", "D10")


# ----------------------------------------------------------------------------
# 0b. OPA388 跟随器模型（M4 / M7）—— 本轮新增
# ----------------------------------------------------------------------------
# M7：SBOS777D Figure 6-25「开环输出阻抗 vs 频率」逐点读数（r5_datasheet_facts.md §7）
ZOUT_OL_M7 = [(1.0, 0.2), (16e3, 11.0), (100e3, 95.0), (400e3, 190.0),
              (1e6, 155.0), (2e6, 123.0), (4.096e6, 110.0), (10e6, 117.0)]
_ZOUT_LF = np.log(np.array([t[0] for t in ZOUT_OL_M7]))
_ZOUT_LZ = np.log(np.array([t[1] for t in ZOUT_OL_M7]))

OPA_A0 = 10 ** (148.0 / 20)      # 148 dB typ（SBOS777D p9 EC 表）
OPA_GBW = float(FACTS["OPA388_GBW_HZ"])
OPA_FP = OPA_GBW / OPA_A0        # 单极点模型 0.398 Hz

# 跟随器差分输入噪声（器件定稿，不可改）：
#   数据手册 7.07 nV/√Hz/器件（V_NSE NVR=7.07，TI 模型）→ 两器件不相关 → √2×7.07
#   本机 TI 模型 foll_noise.net 实测（互谱 V(fpa,fna)）：9.905 nV/√Hz，白噪至 2 MHz
EN_FOLL_DIFF = 9.905e-9

# 源模型选择：'opa388'（本轮默认，真实跟随器：Zout(f) + G(f)）
#             'ideal'（规格 §5.1 V1–V6 的 0 Ω 理想源）
#             'engine'（第 1 轮 opt_engine 的 1 Ω 硬编码，仅供回归对拍）
SOURCE_MODEL = "opa388"


def zout_open_loop(f):
    """开环输出阻抗（M7 查表，log-log 插值）。"""
    f = np.atleast_1d(np.asarray(f, dtype=float))
    return np.exp(np.interp(np.log(np.maximum(f, _ZOUT_LF[0])), _ZOUT_LF, _ZOUT_LZ))


def opa_open_loop_gain(f):
    """开环电压增益（单极点，148 dB / 10 MHz）。复数量，含 −90° 相位。"""
    f = np.atleast_1d(np.asarray(f, dtype=float))
    return OPA_A0 / (1.0 + 1j * f / OPA_FP)


# 复频闭环 Zout 表（TI OPAx388 模型 1 mA 注入实测，r5_zout_opa388_ti.json）
_ZTAB = None


def _ztab():
    global _ZTAB
    if _ZTAB is None:
        try:
            with open(os.path.join(HERE, "r5_zout_opa388_ti.json"), encoding="utf-8") as fh:
                d = json.load(fh)
            _ZTAB = (np.log(np.asarray(d["f_hz"], float)),
                     np.asarray(d["re_ohm"], float), np.asarray(d["im_ohm"], float))
        except OSError:
            _ZTAB = (np.log(np.array([10.0, 1e6, 2e7])),
                     np.array([1e-4, 5.0, 90.0]), np.array([0.0, 15.0, 55.0]))
    return _ZTAB


def zout_cl(f):
    """**闭环**输出阻抗（单位增益跟随器，β=1），复频查表。

    两个口径并存：
      * 解析式 ``Z_o,ol(f)/(1+A_OL(f))``（手册 M7 + 单极点 A_OL）—— 宏观趋势正确，
        fMOD 处给出 41.7 Ω @ 67.8°，与实测 41.1 Ω 吻合。
      * **实测表**（``r5_zout_opa388_ti.json``，TI 模型 1 mA 注入）—— 本函数用它，
        因为它保留了手册曲线看不到的中频**负实部**：100 kHz 处 Re(Z) = −0.9 Ω、
        275 kHz 处 −2.8 Ω。负实部是 TI 宏模型内部钳位/环路块在 A_OL→1 附近的产物，
        会让「阶梯 + 跟随器源阻抗」在某些 R·C 组合下形成**有源谐振**
        （A 案的 1.1Ω/100nF + 13Ω/100nF 在 283 kHz 处实测 +30.7 dB 峰值，
        积分噪声被抬到 75 LSB）。用手册解析式会漏掉这一类失稳：
        引擎预测 A 案无峰，LTspice 实测有峰。
      * 无表时回退解析式（行为与旧版一致）。
    """
    f = np.atleast_1d(np.asarray(f, dtype=float))
    lf, zr, zi = _ztab()
    l = np.log(np.clip(f, np.exp(lf[0]), np.exp(lf[-1])))
    return np.interp(l, lf, zr) + 1j * np.interp(l, lf, zi)


def follower_gain(f):
    """跟随器闭环电压增益 G(f) = A_OL/(1 + A_OL)（单位增益配置）。

    手册单极点模型：4.096 MHz → −0.68 dB（实测 TI 模型 −1.01 dB）、
    16.384 MHz → −5.66 dB（实测 −5.77 dB）。fMOD/MCLK 处的这一衰减**必须**计入
    D1/D3 —— 第 1 轮完全忽略（=1），会把 D3 高估约 5.7 dB。
    """
    f = np.atleast_1d(np.asarray(f, dtype=float))
    a = opa_open_loop_gain(f)
    return a / (1.0 + a)


def _source_z(f, source=None):
    """返回源阻抗复数组（Ω）。"""
    src = SOURCE_MODEL if source is None else source
    f = np.atleast_1d(np.asarray(f, dtype=float))
    if src == "opa388":
        return zout_cl(f)
    if src == "ideal":
        return np.full(f.shape, 1e-6)
    if src == "engine":
        return np.full(f.shape, 1.0)
    raise ValueError(f"unknown source model: {src}")


def _source_gain(f, source=None) -> np.ndarray:
    """返回源电压增益（复）。除 'opa388' 外均按理想 1.0。"""
    src = SOURCE_MODEL if source is None else source
    f = np.atleast_1d(np.asarray(f, dtype=float))
    if src == "opa388":
        return follower_gain(f)
    return np.ones(f.shape, dtype=complex)


# ----------------------------------------------------------------------------
# 1. 基础量测（向量化 MNA）
# ----------------------------------------------------------------------------

def _ladder_GC(stages, mode, tol_r: float = 0.0, tol_c: float = 0.0):
    """阶梯的 G（实，无源部分）与 C 对角线（实）。源节点 0，引脚节点 n。"""
    n = len(stages) + 1
    G = np.zeros((n, n))
    Cd = np.zeros(n)
    for i, (r, ccm, cdf) in enumerate(stages):
        rp = float(r) * (1.0 + tol_r)
        a, b = i, i + 1
        G[a, a] += 1.0 / rp; G[b, b] += 1.0 / rp
        G[a, b] -= 1.0 / rp; G[b, a] -= 1.0 / rp
        c_eff = float(ccm) * (1.0 + tol_c)
        if mode == "dm":
            c_eff += 2.0 * float(cdf) * (1.0 + tol_c)
        Cd[b] += c_eff
    if mode == "dm":
        G[n - 1, n - 1] += 1.0 / (ADC_ZIN / 2.0)     # 130 kΩ 差分 → 单线 65 kΩ 到虚地
    Cd[n - 1] += 5e-12                                # 引脚对地 5 pF
    Cd[0] += 1e-12                                    # 源节点走线寄生（与 opt_engine 一致）
    return G, Cd


def h_vec(stages, mode: str, freqs, tol_r: float = 0.0, tol_c: float = 0.0,
          source: str | None = None) -> np.ndarray:
    """批量传函：一次 MNA 分解，对整组频率求复数响应（输出 = 引脚节点）。

    源 = 理想电压源 1 V 串联 Z_source(f)（Norton 等效：注入 1/Z、节点 0 加 1/Z）。
    Z_source 默认按 OPA388 闭环输出阻抗随频率变化（见 ``zout_cl``）。
    """
    G, Cd = _ladder_GC(stages, mode, tol_r, tol_c)
    f = np.atleast_1d(np.asarray(freqs, dtype=float))
    w = 2.0 * math.pi * f
    Zs = _source_z(f, source)
    Gs = _source_gain(f, source)
    n = G.shape[0]
    A = G[None, :, :] + 1j * w[:, None, None] * np.diag(Cd)[None, :, :]
    A[:, 0, 0] += 1.0 / Zs
    rhs = np.zeros((len(f), n), dtype=complex)
    rhs[:, 0] = Gs / Zs
    v = np.linalg.solve(A, rhs[:, :, None])[:, :, 0]
    return v[:, -1]


def gain_db(stages, mode: str, f, tol_r: float = 0.0, tol_c: float = 0.0,
            source: str | None = None):
    """相对 DC（0.1 Hz）增益，dB；f 可为标量或数组。"""
    vals = h_vec(stages, mode, f, tol_r, tol_c, source) / h_vec(stages, mode, 0.1, tol_r, tol_c, source)[0]
    db = 20 * np.log10(np.abs(vals))
    return float(db[0]) if np.ndim(f) == 0 else db


_FC_GRID = np.logspace(2.0, 6.0, 180)          # 100 Hz ~ 1 MHz，0.0225 dec/点


def fc_dm(stages, source: str | None = None, npts: int | None = None) -> float:
    """DM −3 dB 频率（相对 DC 增益）。

    粗网格（180 点 / 0.0225 dec）定位**第一个**穿越点的区间，再在该区间内
    对 log f 做 24 步二分（每步一次单点 MNA 求解）。
    纯插值版误差可达 2–3%（DM 响应在 fc 附近并不光滑，跟随器的感性 Z_o 造成轻微纹波），
    故必须二分收尾；总耗时 ~1.2 ms，仍是逐点二分的 1/20。
    """
    f = _FC_GRID
    g = np.abs(h_vec(stages, "dm", f, source=source))
    g0 = abs(h_vec(stages, "dm", 0.1, source=source)[0])
    tgt = g0 / math.sqrt(2.0)
    idx = np.nonzero(g <= tgt)[0]
    if len(idx) == 0:
        return float(f[-1])
    i = int(idx[0])
    if i == 0:
        return float(f[0])
    lo, hi = float(f[i - 1]), float(f[i])
    for _ in range(24):
        mid = math.sqrt(lo * hi)
        if abs(h_vec(stages, "dm", mid, source=source)[0]) > tgt:
            lo = mid
        else:
            hi = mid
    return math.sqrt(lo * hi)


def fc_dm_bisect(stages, source: str | None = None, n_iter: int = 60) -> float:
    """逐点二分版（精度更高，用于校验 ``fc_dm``）。"""
    g0 = abs(h_vec(stages, "dm", 0.1, source=source)[0])
    tgt = g0 / math.sqrt(2.0)
    lo, hi = 1.0, 1e9
    for _ in range(n_iter):
        mid = math.sqrt(lo * hi)
        if abs(h_vec(stages, "dm", mid, source=source)[0]) > tgt:
            lo = mid
        else:
            hi = mid
    return math.sqrt(lo * hi)


def settle_time_fast(stages, mode="dm", band=SETTLE_BAND_V,
                     tol_r: float = 0.0, tol_c: float = 0.0,
                     rs: float | None = None, tmax=5e-3,
                     pre_rc: tuple | None = None) -> float:
    """0.01% 建立时间（广义特征分解 + 前置 RC 解析级联），返回 **秒**。

    ``pre_rc = (R_in, C_in)``：规格 §5.1 的**高源阻抗工况**（样品 600 kΩ 端）。
    该 RC 在跟随器**输入**侧，理想缓冲把它与阶梯完全隔离（输入不取电流），
    故整链可解析级联：

        v_in(t) = 1 − e^{−t/τ},  τ = R_in·C_in
        v_out(t) = [阶梯阶跃响应] − [阶梯对 e^{−t/τ} 的响应]
                 = v∞ + Σ a_i e^{−λ_i t}
                   − Σ a_i (e^{−t/τ} − e^{−λ_i t}) / (1/τ − λ_i)

    注意：把 600 kΩ **串进阶梯链**是错的（会与阶梯 DC 通路分压，
    并与阶梯总电容形成 600 kΩ×ΣC 的巨型时间常数）；LTspice V4b 网表也是
    「600 k ∥ 8.5 pF → 理想跟随器 Efa → 阶梯」，本函数与之一致。

    源阻抗取 **静态值** rs（默认 ``|Z_o,cl(fc)|``）。通带内 |Z_o,cl| < 0.25 Ω
    且近纯感性，对以 ~50 kHz 为主的极点影响 <2%（见 test）。
    """
    n = len(stages) + 1
    G = np.zeros((n, n))
    Cd = np.zeros(n)
    r_s = 1e-6 if rs is None else max(float(rs), 1e-9)
    G[0, 0] += 1.0 / r_s
    b = np.zeros(n)
    b[0] = 1.0 / r_s
    Cd[0] += 1e-12
    for i, (r, ccm, cdf) in enumerate(stages):
        rp = float(r) * (1.0 + tol_r)
        a, bb = i, i + 1
        G[a, a] += 1.0 / rp; G[bb, bb] += 1.0 / rp
        G[a, bb] -= 1.0 / rp; G[bb, a] -= 1.0 / rp
        c = float(ccm) * (1.0 + tol_c)
        if mode == "dm":
            c += 2.0 * float(cdf) * (1.0 + tol_c)
        Cd[bb] += c
    if mode == "dm":
        G[n - 1, n - 1] += 1.0 / (ADC_ZIN / 2.0)
    Cd[n - 1] += 5e-12

    vinf = np.linalg.solve(G, b)
    # G v = λ C v（对称正定）→ 实特征值；比 A = C⁻¹G 的非对称特征分解稳定得多。
    # λ 的数值噪声可能给出极小负值（1e-6 Ω 源电导造成 1e18 量级模态），一律钳到 0。
    lam, V = eigh(G, np.diag(Cd))
    lam = np.clip(lam, 0.0, None)
    a = V.T @ (Cd * vinf)                 # 阶跃响应：v_out(t) = vinf_out − Σ V[out,i]·a_i·e^{−λ_i t}
    a_out = a * V[-1, :]                  # 引脚节点上的模态系数
    v_inf_out = float(vinf[-1])

    if pre_rc is None:
        def err(t: float) -> float:
            return abs(v_inf_out - float(a_out @ np.exp(-lam * t)) - v_inf_out)
    else:
        r_in, c_in = float(pre_rc[0]), float(pre_rc[1])
        tau = max(r_in * c_in, 1e-15)
        inv_t = 1.0 / tau
        den = inv_t - lam
        den = np.where(np.abs(den) < 1e-9 * inv_t, 1e-9 * inv_t, den)
        amp = a_out * lam / den           # 对 e^{−t/τ} 输入项的模态系数

        def err(t: float) -> float:
            e_lam = np.exp(-lam * t)
            e_tau = math.exp(-inv_t * t)
            v_out = v_inf_out - float(a_out @ e_lam) - float(amp @ (e_lam - e_tau))
            return abs(v_out - v_inf_out)

    if err(0.0) <= band:
        return 0.0
    if err(tmax) > band:
        return float("inf")
    lo, hi = 0.0, tmax
    for _ in range(48):
        mid = 0.5 * (lo + hi)
        if err(mid) <= band:
            hi = mid
        else:
            lo = mid
    return hi


# 优化器内部用快速档（噪声积分点数 / MC 抽样数），最终冻结评估一律用完整档
FAST = False
NOISE_NPTS = 400
SIGMA_N = 40


def noise_breakdown_lsb(stages, f_lo: float = 0.1, f_hi: float | None = None,
                        npts: int | None = None) -> dict:
    """ADC 引脚积分噪声（0.1 Hz ~ fMOD/2），单位 LSB（差分，双线）。

    三项互相独立、功率相加：
      ① 无源阶梯（各级 R + 130 kΩ 差分负载）的约翰逊噪声 —— 逐电阻注入 4kTR 电流噪声，
         用 G/C 求各电阻到引脚的 NTF。源侧按理想电压源（Z=0）处理：跟随器输出阻抗
         在环路内，其热噪声已包含在 ② 的输入参考噪声里，不能重复计。
      ② **跟随器差分输入噪声**：en,diff = 9.905 nV/√Hz，白噪；
         输出参考 = en × √(∫|H(f)|² df) = en × √ENBW。
      ③ 跟随器电流噪声（~1.7 fA/√Hz）经阶梯阻抗 —— 量级 <1e-12，忽略（注明）。

    第 1 轮只算了 ①（≈0.97 LSB），**漏掉 ②**，而 ② 在真实器件下大 12.5×，
    是本轮 D6 结论反转的根源。
    """
    if f_hi is None:
        f_hi = FMOD_HZ / 2.0
    if npts is None:
        npts = 150 if FAST else NOISE_NPTS
    G, Cd = _ladder_GC(stages, "dm")
    n = G.shape[0]
    f = np.logspace(math.log10(f_lo), math.log10(f_hi), npts)
    w = 2.0 * math.pi * f
    A = G[None, :, :] + 1j * w[:, None, None] * np.diag(Cd)[None, :, :]
    A[:, 0, 0] += 1.0 / 1e-6                      # 理想源（短路）

    r_list, b_list = [], []
    for i, (r, _cg, _cd) in enumerate(stages):    # 各级串联 R
        v = np.zeros(n, complex); v[i] = 1.0; v[i + 1] = -1.0
        r_list.append(float(r)); b_list.append(v)
    v = np.zeros(n, complex); v[n - 1] = 1.0      # 130 kΩ/2 差分负载
    r_list.append(ADC_ZIN / 2.0); b_list.append(v)

    B = np.stack(b_list, axis=1)
    B = np.broadcast_to(B[None, :, :], (len(f), n, B.shape[1]))
    X = np.linalg.solve(A, B)
    ntf = X[:, -1, :] / np.array(r_list)[None, :]
    psd = (4 * K_B * T_K * np.array(r_list)[None, :] * np.abs(ntf) ** 2).sum(axis=1)
    # NTF 是**单线**口径（每线注入、引脚对地求响应），而 EN_FOLL_DIFF 已是**差分**口径
    # （两器件不相关合成）。两者相加前必须先统一：单线 → 差分 = ×√2。
    # 第 1 轮 integrated_noise_lsb 里的 ×√2 就是这个因子，重构时漏掉了。
    v_pass = math.sqrt(2.0) * math.sqrt(float(np.trapz(psd, f)))

    # ② 跟随器噪声：用真实源模型的 |H(f)|² 积分（含 Z_o,cl 的频率特性）
    h = h_vec(stages, "dm", f)
    h0 = h_vec(stages, "dm", 0.1)[0]
    g2 = np.abs(h / h0) ** 2
    enbw = float(np.trapz(g2, f))
    v_foll = EN_FOLL_DIFF * math.sqrt(enbw)

    v_tot = math.sqrt(v_pass ** 2 + v_foll ** 2)
    return {
        "lsb": v_tot / LSB_V,
        "lsb_passive": v_pass / LSB_V,
        "lsb_follower": v_foll / LSB_V,
        "v_rms_nv": v_tot * 1e9,
        "enbw_hz": enbw,
        "psd_passive_at_1k": float(math.sqrt(np.interp(1e3, f, psd))) * 1e9,
    }


def integrated_noise_lsb(stages, npts: int | None = None) -> float:
    """兼容第 1 轮接口：返回总积分噪声（LSB，含跟随器）。"""
    return noise_breakdown_lsb(stages, npts=npts)["lsb"]


# ----------------------------------------------------------------------------
# 1b. D8 —— 精确双线 MNA（CM 激励 → 差分输出）
# ----------------------------------------------------------------------------

def _two_line(pa_stages, pb_stages):
    """构造两线并联的大 MNA (G, C 矩阵, 源节点索引)。

    线 A 节点 0..n，线 B 节点 n..2n（n = len(stages)+1）；C 为**完整矩阵**
    （C_diff 跨接两线末级，因此非对角元非零）。
    """
    n = len(pa_stages) + 1
    G = np.zeros((2 * n, 2 * n))
    C = np.zeros((2 * n, 2 * n))
    for off, st in ((0, pa_stages), (n, pb_stages)):
        for i, (r, ccm, _cdf) in enumerate(st):
            a, b = off + i, off + i + 1
            G[a, a] += 1.0 / r; G[b, b] += 1.0 / r
            G[a, b] -= 1.0 / r; G[b, a] -= 1.0 / r
            C[b, b] += float(ccm)                 # CM 模态：C_diff 两端等电位，不载流
        C[off + n - 1, off + n - 1] += 5e-12
    pin_a, pin_b = n - 1, 2 * n - 1
    cd = float(pa_stages[-1][2])
    if cd > 0:
        # C_diff 跨接两线末级。两线完全相同时它不载流（CM 模态），
        # 但失配工况下两端不再等电位，必须作为完整矩阵项保留。
        C[pin_a, pin_a] += cd
        C[pin_b, pin_b] += cd
        C[pin_a, pin_b] -= cd
        C[pin_b, pin_a] -= cd
    G[pin_a, pin_a] += 1.0 / ADC_ZIN              # 130 kΩ 差分负载
    G[pin_b, pin_b] += 1.0 / ADC_ZIN
    G[pin_a, pin_b] -= 1.0 / ADC_ZIN
    G[pin_b, pin_a] -= 1.0 / ADC_ZIN
    return G, C, (0, n), (pin_a, pin_b)


def _two_line_cm_dm(pa_stages, pb_stages, freqs, source: str | None = None):
    """返回 (cm, dm) 复数数组：cm = (Vp+Vn)/2，dm = Vp−Vn（共模激励 1 V）。

    注意：共模激励下 C_diff 与 130 kΩ 差分负载理论上都不载流，但两线**不完全相同**时
    （D8 的失配工况）它们会承接不平衡电流 —— 故这里保留完整的耦合项，
    这是第 1 轮 ``tol_r/tol_c`` 单线差分近似无法表达的部分。
    """
    G, C, (ia, ib), (pin_a, pin_b) = _two_line(pa_stages, pb_stages)
    f = np.atleast_1d(np.asarray(freqs, dtype=float))
    w = 2.0 * math.pi * f
    Zs = _source_z(f, source)
    A = G[None, :, :] + 1j * w[:, None, None] * C[None, :, :]
    A[:, ia, ia] += 1.0 / Zs
    A[:, ib, ib] += 1.0 / Zs
    rhs = np.zeros((len(f), G.shape[0]), dtype=complex)
    rhs[:, ia] = 1.0 / Zs
    rhs[:, ib] = 1.0 / Zs
    v = np.linalg.solve(A, rhs[:, :, None])[:, :, 0]
    vp, vn = v[:, pin_a], v[:, pin_b]
    return (vp + vn) / 2.0, vp - vn


def _scaled_line(stages, kr: float, kc: float):
    return [(float(r) * kr, float(c) * kc, float(cd) * kc) for r, c, cd in stages]


def cmrr_two_line(stages, mism: float = D8_MISMATCH, f_lo: float = 10.0,
                  f_hi: float = 16e3, npts: int = 40, source: str | None = None) -> float:
    """CMRR @通带最差值（10 Hz~16 kHz）：整线失配（两条线 R/C 各 ×(1+mism)）。

    这是规格 §5.1 D8 的 V3 口径（两线阶梯 1% 失配角）。用**精确双线 MNA**，
    含 C_diff 与 130 kΩ 负载的耦合（两线不同时二者都会载流）。
    """
    f = np.logspace(math.log10(f_lo), math.log10(f_hi), npts)
    cm, dm = _two_line_cm_dm(stages, _scaled_line(stages, 1.0 + mism, 1.0 + mism), f, source)
    r = np.abs(cm) / np.maximum(np.abs(dm), 1e-300)
    return float(np.min(20.0 * np.log10(r)))


def cmrr_mc_percentile(stages, tol: float = 1e-3, n: int = 200, q: float = 0.95,
                       f_lo: float = 10.0, f_hi: float = 16e3, npts: int = 25,
                       seed: int = 20261018, source: str | None = None) -> dict:
    """逐元件独立失配的蒙特卡洛 CMRR 分布（D8 的「统计口径」）。

    每个 R / C 独立取 (1 + u·tol)，u ~ U(−1,1)（与 D7 的 MC 同构）。
    q=0.95 → 返回**最差 5% 分位**（即 95% 的板子在它之上）。
    """
    rng = np.random.default_rng(seed)
    f = np.logspace(math.log10(f_lo), math.log10(f_hi), npts)
    vals = []
    for _ in range(n):
        st_b = []
        for r, cg, cd in stages:
            st_b.append((float(r) * (1 + rng.uniform(-tol, tol)),
                         float(cg) * (1 + rng.uniform(-tol, tol)),
                         float(cd) * (1 + rng.uniform(-tol, tol))))
        cm, dm = _two_line_cm_dm(stages, st_b, f, source)
        vals.append(float(np.min(20 * np.log10(np.abs(cm) / np.maximum(np.abs(dm), 1e-300)))))
    v = np.array(vals)
    return {"median_db": float(np.median(v)), "p_worst_db": float(np.quantile(v, 1 - q)),
            "p_best_db": float(np.quantile(v, q)), "tol": tol, "n": n}


def cmrr_required_mismatch(stages, target_db: float = 80.0,
                           lo: float = 1e-6, hi: float = 0.05) -> float:
    """反解：要在通带最差频点达到 target_db，两线整线失配需 ≤ 多少。"""
    for _ in range(50):
        mid = math.sqrt(lo * hi)
        if cmrr_two_line(stages, mism=mid) >= target_db:
            lo = mid
        else:
            hi = mid
    return math.sqrt(lo * hi)


def sigma_dg_db(stages, tol_r: float = 0.01, tol_c: float = 0.05,
                n: int = 40, seed: int = 20261018) -> float:
    """D7：逐元件独立均匀抽样的 16 kHz 增益偏差标准差（dB）。

    第 1 轮用的是「各元件单点 +tol 扰动的 RSS 代理」，系统性过估 2.2–3.2×
    （r5_report.md §3.2 已指出）。本轮改为与 V5 同构的逐元件独立 MC。
    """
    rng = np.random.default_rng(seed)
    base = gain_db(stages, "dm", 16e3)
    vals = np.empty(n)
    for k in range(n):
        st = [(float(r) * (1 + rng.uniform(-tol_r, tol_r)),
               float(cg) * (1 + rng.uniform(-tol_c, tol_c)),
               float(cd) * (1 + rng.uniform(-tol_c, tol_c)))
              for r, cg, cd in stages]
        vals[k] = gain_db(st, "dm", 16e3) - base
    return float(np.std(vals, ddof=1))


def group_delay_us(stages, f_lo=0.1, f_hi=16e3, npts=120, source: str | None = None) -> tuple:
    """D10：0.1 Hz~16 kHz 群延迟变化量 Δτ（µs），返回 (Δτ, τ@0.1Hz)。"""
    f = np.logspace(math.log10(f_lo), math.log10(f_hi), npts)
    h = h_vec(stages, "dm", f, source=source)
    tau = -np.gradient(np.unwrap(np.angle(h)), 2 * math.pi * f)
    return float((tau.max() - tau.min()) * 1e6), float(tau[0] * 1e6)


# 噪声增益峰阈值：无源阶梯 + 跟随器感性 Z_o 在 A_OL→1 附近可能形成有源谐振。
# 超过 +6 dB 即视为稳定性缺陷（A 案曾实测 +30.7 dB @283 kHz，积分噪声 12→75 LSB）。
PEAK_MAX_DB = 6.0


def peaking_db(stages, f_lo: float = 1.0, f_hi: float = 2e6, npts: int = 500) -> tuple:
    """差分传函相对 DC 的最大增益（dB）与所在频率。>0 表示有峰（有源谐振）。"""
    f = np.logspace(math.log10(f_lo), math.log10(f_hi), npts)
    h = h_vec(stages, "dm", f)
    g0 = abs(h_vec(stages, "dm", 0.1)[0])
    g = 20.0 * np.log10(np.abs(h) / g0)
    i = int(np.argmax(g))
    return float(g[i]), float(f[i])


def kickback_ns(stages) -> tuple:
    """D9 代理：返回 (τ_kb_ns, droop, 是否回稳)。

    采样瞬间 C_S 从引脚本地电容（末级 C_gnd + 2·C_diff + C_PIN）抽电荷：
      τ     = (R_sw + R_last)·C_S     —— 回稳到 0.01% 需 ~9.2τ ≤ 122 ns
      droop = C_S/(C_S + C_pin)       —— 必须 ≤ 0.01%（即 C_pin ≥ 35 nF）
    注意：加大 C_diff 只会**增大** C_pin（droop 变小）并让 R_last 变小（τ 变小），
    对 D9 双向有利；D9 不是「加大末级电容」的代价项。
    """
    r_last = float(stages[-1][0])
    c_pin = float(stages[-1][1]) + 2.0 * float(stages[-1][2]) + 5e-12
    tau = (ADC_RSW + r_last) * ADC_CS_F
    droop = ADC_CS_F / (ADC_CS_F + c_pin)
    ok = (9.2 * tau <= KB_HALF_PERIOD_S) and (droop <= 1e-4)
    return tau * 1e9, droop, bool(ok)


# ----------------------------------------------------------------------------
# 2. 十维预测 + 评分（规格 §5.1）
# ----------------------------------------------------------------------------

_PRED_CACHE: dict = {}
_PRED_CACHE_MAX = 20000


def predict(stages, source: str | None = None, with_mc: bool = False) -> dict:
    """规格 §5.1 十维理论预测值 + 硬约束量（时间量单位：秒）。

    结果按 (级数, 参数, 源模型, FAST) 缓存 —— Nelder-Mead 会反复试探相邻顶点，
    缓存把重复评估从 ~28 ms 压到 ~1 µs（实测整体提速 35%）。
    """
    stages = [tuple(map(float, s)) for s in stages]
    ck = (tuple((round(a, 9), round(b, 15), round(c, 15)) for a, b, c in stages),
          source or SOURCE_MODEL, FAST, with_mc)
    if not with_mc and ck in _PRED_CACHE:
        return dict(_PRED_CACHE[ck])
    fc = fc_dm(stages, source=source)
    a_dm = -float(gain_db(stages, "dm", FMOD_HZ, source=source))
    a_cm = -float(gain_db(stages, "cm", FMOD_HZ, source=source))
    a_mclk = -float(gain_db(stages, "dm", MCLK_HZ, source=source))
    dg16 = abs(float(gain_db(stages, "dm", 16e3, source=source)))
    rs_settle = max(abs(zout_cl(fc)[0]), 1e-4)
    t_settle_s = settle_time_fast(stages, "dm", SETTLE_BAND_V, tol_r=0.01, tol_c=0.05,
                                  rs=rs_settle)
    t_settle_hz = settle_time_fast(stages, "dm", SETTLE_BAND_V, tol_r=0.01, tol_c=0.05,
                                   rs=rs_settle, pre_rc=HIGH_Z_PRE_RC)
    nb = noise_breakdown_lsb(stages)
    sig = sigma_dg_db(stages, n=(16 if FAST else SIGMA_N))
    cmrr_1pct = cmrr_two_line(stages, mism=D8_MISMATCH, source=source)
    cmrr_sel = cmrr_two_line(stages, mism=D8_MISMATCH_SEL, source=source)
    dtau_us, tau0_us = group_delay_us(stages, source=source)
    pk_db, pk_hz = peaking_db(stages)
    tau_kb_ns, droop, kb_ok = kickback_ns(stages)
    out = {
        # —— 计划 Task 2 接口要求的六个键（dB / 秒）——
        "A_dm": a_dm,
        "A_cm": a_cm,
        "A_mclk": a_mclk,
        "dG_16k": dg16,
        "t_settle_wc_s": t_settle_s,
        "group_delay_flat_s": dtau_us * 1e-6,
        # —— 其余维度与硬约束量 ——
        "f_c_hz": fc,
        "t_settle_highz_s": t_settle_hz,
        "V_n_lsb": nb["lsb"],
        "V_n_lsb_passive": nb["lsb_passive"],
        "V_n_lsb_follower": nb["lsb_follower"],
        "enbw_hz": nb["enbw_hz"],
        "sigma_dG_db": sig,
        "CMRR_pb_db": cmrr_1pct,
        "CMRR_pb_db_sel005": cmrr_sel,
        "tau_kb_ns": tau_kb_ns,
        "kickback_droop": droop,
        "kickback_ok": kb_ok,
        "peaking_db": pk_db,
        "peaking_f_hz": pk_hz,
        "peaking_ok": pk_db <= PEAK_MAX_DB,
        "tau_dc_us": tau0_us,
        "r_sum_ohm": float(sum(s[0] for s in stages)),
        "c_max_f": float(max([c for s in stages for c in (s[1], s[2])] or [0.0])),
        "n_parts": 2 * len(stages) + sum(2 if s[1] > 0 else 0 for s in stages)
                   + sum(1 if s[2] > 0 else 0 for s in stages),
        "rs_settle_ohm": rs_settle,
        "zout_fmod_ohm": float(abs(zout_cl(FMOD_HZ)[0])),
        "source_model": (SOURCE_MODEL if source is None else source),
    }
    if not with_mc:
        if len(_PRED_CACHE) > _PRED_CACHE_MAX:
            _PRED_CACHE.clear()
        _PRED_CACHE[ck] = dict(out)
    if with_mc:
        out["CMRR_mc_1pct"] = cmrr_mc_percentile(stages, tol=0.01)
        out["CMRR_mc_01pct"] = cmrr_mc_percentile(stages, tol=1e-3)
        out["CMRR_mc_005pct"] = cmrr_mc_percentile(stages, tol=5e-4)
    return out


def d5_worst_us(pred: dict) -> float:
    """D5 取值：规格 §5.1「测试须覆盖高源阻抗工况（样品 600 kΩ 端）」→ 取两者较大。"""
    return 1e6 * max(pred["t_settle_wc_s"], pred.get("t_settle_highz_s",
                                                     pred["t_settle_wc_s"]))


def _score_ratio(x: float, full: float) -> float:
    """§5.1 越大越好：min(x/满分, 1)。"""
    if not np.isfinite(x) or x <= 0:
        return 0.0
    return float(min(x / full, 1.0))


def _score_inverse(x: float, full: float) -> float:
    """§5.1 越小越好：min(满分/x, 1)。"""
    if not np.isfinite(x) or x <= 0:
        return 0.0
    return float(min(full / x, 1.0))


def _lerp(x: float, full: float, bare: float, higher_is_better: bool = False) -> float:
    """full 处 1.0、bare 处 0.0，中间线性（**仅 D4/D7/D10** 的规格插值方式）。"""
    if higher_is_better:
        if x >= full:
            return 1.0
        if x < bare:
            return 0.0
        return (x - bare) / (full - bare)
    if x <= full:
        return 1.0
    if x > bare:
        return 0.0
    return 1.0 - (x - full) / (bare - full)


def dim_scores(pred: dict) -> dict:
    """把预测值折成 D1–D10 的 [0,1] 分（规格 §5.1 归一化逐条实现）。

    **第 1 轮 bug 修复**：原实现对 D1/D2/D3/D5/D6/D8 也调 ``_lerp``（线性插值到及格线），
    而 §5.1 明写这三类用 ``min(x/满分,1)`` / ``min(满分/x,1)``。本函数逐条按 §5.1 实现：
        D1/D2/D3/D8  → min(x/满分, 1)          （越大越好）
        D5/D6        → min(满分/x, 1)          （越小越好）
        D4/D7/D10    → 两段线性（0.05→1.0、0.5→0.0 等）
        D9           → 二值
    """
    t_us = d5_worst_us(pred)                    # 秒 → µs（含 600 kΩ 高阻工况）
    vn = pred["V_n_lsb"]
    return {
        "D1": _score_ratio(pred["A_dm"], TH["D1"][0]),
        "D2": _score_ratio(pred["A_cm"], TH["D2"][0]),
        "D3": _score_ratio(pred["A_mclk"], TH["D3"][0]),
        "D4": _lerp(pred["dG_16k"], *TH["D4"]),
        "D5": _score_inverse(t_us, TH["D5"][0]),
        "D6": _score_inverse(vn, TH["D6"][0]),
        "D7": _lerp(pred["sigma_dG_db"], *TH["D7"]),
        "D8": _score_ratio(pred["CMRR_pb_db"], TH["D8"][0]),
        "D9": 1.0 if pred["kickback_ok"] else 0.0,
        "D10": _lerp(pred["group_delay_flat_s"] * 1e6, *TH["D10"]),
    }


def pass_flags(dims: dict, pred: dict) -> dict:
    """逐维是否达到「及格线」（低于及格线 = 淘汰）。"""
    return {
        "D1": pred["A_dm"] >= TH["D1"][1],
        "D2": pred["A_cm"] >= TH["D2"][1],
        "D3": pred["A_mclk"] >= TH["D3"][1],
        "D4": pred["dG_16k"] <= TH["D4"][1],
        "D5": d5_worst_us(pred) <= TH["D5"][1],
        "D6": pred["V_n_lsb"] <= TH["D6"][1],
        "D7": pred["sigma_dG_db"] <= TH["D7"][1],
        "D8": pred["CMRR_pb_db"] >= TH["D8"][1],
        "D9": pred["kickback_ok"],
        "D10": pred["group_delay_flat_s"] * 1e6 <= TH["D10"][1],
    }


def margin_ratios(pred: dict) -> dict:
    """相对及格线的裕量比（1.0 = 恰在及格线，>1 越好）—— 仅供优化器使用。"""
    t_us = d5_worst_us(pred)
    dtau_us = pred["group_delay_flat_s"] * 1e6
    tau_kb_s = pred["tau_kb_ns"] * 1e-9
    kb_ratio = min(9.2 * tau_kb_s / KB_HALF_PERIOD_S,
                   pred["kickback_droop"] / 1e-4)
    return {
        "D1": pred["A_dm"] / TH["D1"][1],
        "D2": pred["A_cm"] / TH["D2"][1],
        "D3": pred["A_mclk"] / TH["D3"][1],
        "D4": TH["D4"][1] / max(pred["dG_16k"], 1e-9),
        "D5": TH["D5"][1] / max(t_us, 1e-9),
        "D6": TH["D6"][1] / max(pred["V_n_lsb"], 1e-9),
        "D7": TH["D7"][1] / max(pred["sigma_dG_db"], 1e-9),
        "D8": pred["CMRR_pb_db"] / TH["D8"][1],
        "D9": 1.0 / max(kb_ratio, 1e-9),
        "D10": TH["D10"][1] / max(dtau_us, 1e-9),
    }


def hard_checks(pred: dict) -> dict:
    """规格 §5.2 工程约束 + 计划 Task 2 的新 fc 约束。"""
    return {
        # 数值容差 0.05%：fc 由 build_from_x 二分命中，残余误差 ~1e-5 Hz（8 位有效），
        # 严格 `<= FC_HI` 会把 fc=80000.0008 判为越界 —— 那是浮点噪声，不是设计越界。
        "fc_in_range": FC_LO * (1 - 5e-4) <= pred["f_c_hz"] <= FC_HI * (1 + 5e-4),
        "r_sum": pred["r_sum_ohm"] <= R_SUM_MAX,
        "c_max": pred["c_max_f"] <= C_MAX,
        "settle": d5_worst_us(pred) <= SETTLE_BUDGET_US,
        "dG_16k": pred["dG_16k"] <= DG_MAX_DB,
        "cdiff_layout": True,     # 结构由参数化保证：C_diff 只在末级
        "peaking": pred["peaking_db"] <= PEAK_MAX_DB,   # 跟随器感性 Z_o 不得与阶梯形成谐振
    }


def score_of(stages, source: str | None = None) -> tuple:
    """返回 (min(D1..D10), pred, dims)。"""
    pred = predict(stages, source=source)
    dims = dim_scores(pred)
    return min(dims.values()), pred, dims


def design_score(dims: dict) -> float:
    """仅对 **可作用维度**（ACTIONABLE）的满分比取 capped 幂平均（p=8 ≈ min）。

    返回 **越大越好** 的分数 ∈ [0,1]（1.0 = 8 维全满分）。
    D6 / D8 在本规格下由器件噪声与元件匹配决定，与阶梯拓扑几乎无关
    （见 ``physics_limits``），若纳入 min 会使三个方案全部并列在同一常数上，
    优化器失去分辨力。故求解器只在这 8 维上做短板制。
    """
    vals = np.clip(np.array([dims[k] for k in ACTIONABLE], dtype=float), 0.0, 1.0)
    return softmin(vals, 32.0)


def physics_limits(stages=None) -> dict:
    """本轮新增：把 D6/D8 的「物理不可能」量化为可复核的数字。

    D6：给定跟随器差分噪声 9.905 nV/√Hz，要达到 1 LSB(=291 nV) 需要
        ENBW ≤ (291/9.905)² = 863 Hz。而 D4 要求 16 kHz 处 ≤0.5 dB，
        阶梯 fc 必须 ≥ ~45 kHz ⇒ ENBW ≥ ~80 kHz。二者相差 ~11×。
        即使换成**理想砖墙**在 16 kHz 截止：Vn = 9.905×√16000 = 1253 nV = 4.31 LSB，
        仍然超 1 LSB 的及格线 4.3 倍 ⇒ D6 与 D4 在本器件下不可同时满足。
    D8：CMRR 随失配 −20 dB/decade（r5_report §2.3 实测标定）。
        1 % → ~46 dB；要 80 dB 需 ≤ ~0.02 %，是本规格「两线 1 % 失配角」的 1/50。
    """
    f_need = (LSB_V * TH["D6"][1] / EN_FOLL_DIFF) ** 2
    f_full = (LSB_V * TH["D6"][0] / EN_FOLL_DIFF) ** 2
    brick = EN_FOLL_DIFF * math.sqrt(16e3) / LSB_V
    out = {
        "D6_en_foll_nv": EN_FOLL_DIFF * 1e9,
        "D6_enbw_for_pass_hz": f_need,
        "D6_enbw_for_full_hz": f_full,
        "D6_brickwall_16k_lsb": brick,
        "D6_brickwall_16k_pass": brick <= TH["D6"][1],
    }
    if stages is not None:
        out["CMRR_1pct_db"] = cmrr_two_line(stages, mism=D8_MISMATCH)
        out["CMRR_005pct_db"] = cmrr_two_line(stages, mism=D8_MISMATCH_SEL)
        out["CMRR_req_mismatch"] = cmrr_required_mismatch(stages, TH["D8"][1])
        out["D6_lsb_model"] = noise_breakdown_lsb(stages)["lsb"]
    return out


def rank_key(rec) -> tuple:
    """候选排序键：先看过了几维及格线，再看 min，再看均分（短板制下的稳定化）。"""
    pf = pass_flags(rec["dims"], rec["pred"])
    n_pass = sum(pf.values())
    mean = float(np.mean(list(rec["dims"].values())))
    return (n_pass, rec["meta"]["min_score"], mean)


# ----------------------------------------------------------------------------
# 3. 求解器：fc 精确参数化 + Nelder-Mead 多起点
# ----------------------------------------------------------------------------
# 设计变量 x 维度 = 2n + 2：
#   x[0:n]      ln R_i            （Ω）
#   x[n:2n]     ln C_gnd,i        （F）
#   x[2n]       ln C_diff         （F，末级跨接）
#   x[2n+1]     ln fc_target      （Hz）
# fc 由「全体 R 同比缩放」精确命中（RC 网络 fc 与 R 成反比，缩放不改变曲线形状），
# 这样每条候选都严格满足 fc∈[50k,80k]，优化器只需处理其余约束。

def build_from_x(x, n: int):
    """x → (stages, fc_target)。R 等比缩放使整体 DM −3 dB 精确等于 fc_target。

    **R 下限 1 Ω 是硬约束**（规格 §5.2 C5「1% 起步（E24）」；E24 最小档 = 1 Ω）。
    第 2 轮求解中曾出现 R=0.2 Ω 的退化解：此时跟随器输出阻抗（通带 0.02–0.25 Ω、
    fMOD 处 42 Ω）反而成了「串阻」，D1 掉到 54 dB、且不可制造 —— 故必须夹住。

    缩放律：fc 随 R 全局缩放 s 单调下降（在 R ≳ 3×|Z_o,cl(fc)| 的区间内严格成立）。
    实现为「先按 1/R 律试算 → 核对 → 偏差 >3% 时在对数区间内扫描 + 二分」，
    因为 R 掉到只剩几欧时源阻抗会接管，1/R 律失效。
    """
    r = np.exp(np.clip(np.asarray(x[:n], float), math.log(1.0), math.log(R_SUM_MAX)))
    cg = np.exp(np.clip(np.asarray(x[n:2 * n], float), math.log(1e-12), math.log(C_MAX)))
    cd = math.exp(min(max(float(x[2 * n]), math.log(1e-12)), math.log(C_MAX)))
    # fc_target **硬夹在规格 §3 的 [50, 80] kHz**：上一版夹在 [10k, 500k]，
    # 优化器会跑到 149 kHz 换取 D1/D2/D3（那违反 §3 频率规划，且 D4 只剩 0.11 dB 余量），
    # 然后用罚函数"付费"——NM 用罚函数斗不过收益，最终产出不可用解。
    fc_t = math.exp(min(max(float(x[2 * n + 1]), math.log(FC_LO)), math.log(FC_HI)))
    base = [(float(r[i]), float(cg[i]), 0.0) for i in range(n - 1)]
    base.append((float(r[-1]), float(cg[-1]), cd))

    def fcv(sv: float) -> float:
        return fc_dm([(rr * sv, a, b) for rr, a, b in base])

    # s 的可行区间：min(R_i)·s ≥ 1 Ω 且 ΣR ≤ 5 kΩ
    s_min = 1.0 / min(rr for rr, _a, _b in base)
    s_max = R_SUM_MAX / sum(rr for rr, _a, _b in base)
    s_max = max(s_max, s_min * 1.0001)

    s = 1.0
    for _ in range(3):
        sv = float(np.clip(s, s_min, s_max))
        s *= fcv(sv) / fc_t
        s = float(np.clip(s, s_min, s_max))

    # fc(s) 在 s 全域**不是**单调的（跟随器感性 Z_o 造成纹波与弱谐振），
    # 但落在 ±10% 的窄窗内是单调的。故：
    #   ① 3 次缩放律试算（在 R ≫ |Z_o,cl| 时精确）
    #   ② 若残差 >0.5%，在 ±30% 窗口内扫描 13 点找跨越，再二分
    #   ③ 最后窄窗二分保证 |Δfc/fc| < 0.2%
    if abs(fcv(s) / fc_t - 1.0) > 0.005:
        grid = np.exp(np.linspace(math.log(max(s * 0.7, s_min)),
                                  math.log(min(s * 1.3, s_max)), 13))
        vals = np.array([fcv(g) for g in grid])
        k = int(np.argmin(np.abs(vals - fc_t)))
        lo = float(grid[max(0, k - 1)])
        hi = float(grid[min(len(grid) - 1, k + 1)])
        s = float(grid[k])
        if (fcv(lo) - fc_t) * (fcv(hi) - fc_t) <= 0:
            for _ in range(22):
                mid = math.sqrt(lo * hi)
                if fcv(mid) > fc_t:
                    lo = mid
                else:
                    hi = mid
            s = math.sqrt(lo * hi)
    # ③ 窄窗终校：即使残差已很小也做一次（20 次单点求值 ≈ 0.4 ms）
    lo2, hi2 = s * 0.995, s * 1.005
    f_lo, f_hi = fcv(lo2), fcv(hi2)
    if (f_lo - fc_t) * (f_hi - fc_t) <= 0:
        for _ in range(20):
            mid = math.sqrt(lo2 * hi2)
            if fcv(mid) > fc_t:
                lo2 = mid
            else:
                hi2 = mid
        s = math.sqrt(lo2 * hi2)
    s = max(s, s_min)        # 终校可能把 s 压到 s_min 之下（lo2 = s*0.995），再夹一次
    return [(rr * s, a, b) for rr, a, b in base], fc_t


def power_mean(vals, p: float = 8.0) -> float:
    """广义幂平均 M_p = (mean(x^p))^(1/p)。

    ⚠ p>0 时 M_p → **max**，p<0 时才 → **min**（第 1 轮写成 p=8 却当 min 用，
    实际是在优化「最好那一维」，这是本轮查出的第二个求解器 bug）。
    短板制请用 ``softmin``（p<0）。
    """
    v = np.clip(np.asarray(vals, dtype=float), 0.0, None)
    return float((np.mean(v ** p)) ** (1.0 / p))


def softmin(vals, p: float = 32.0) -> float:
    """短板制的平滑近似：负次幂平均（p<0 时 → min）。

    p=−32 时，若某维 = 0.371 其余 = 1.0：结果 0.364（真 min = 0.371），
    而 p=+8 的正幂平均给出 0.997（≈ max）——量级差别在此。
    """
    v = np.clip(np.asarray(vals, dtype=float), 1e-4, 1.0)
    return float(np.mean(v ** (-p)) ** (-1.0 / p))


def objective(x, n: int) -> float:
    if not np.all(np.isfinite(x)):
        return 10.0
    stages, fc_t = build_from_x(x, n)
    cg = [s[1] for s in stages]
    cd = stages[-1][2]
    pen = 0.0
    if max(cg) > C_MAX:
        pen += 3.0 * (math.log(max(cg) / C_MAX)) ** 2
    if cd > C_MAX:
        pen += 3.0 * (math.log(cd / C_MAX)) ** 2
    if not (FC_LO * 0.999 <= fc_t <= FC_HI * 1.001):
        pen += 3.0 * (math.log(max(fc_t, FC_LO) / FC_HI)) ** 2
    if sum(s[0] for s in stages) > R_SUM_MAX:
        pen += 3.0 * (math.log(sum(s[0] for s in stages) / R_SUM_MAX)) ** 2
    try:
        pred = predict(stages)
    except Exception:
        return 10.0
    hard = hard_checks(pred)
    viol = 0.0
    if not hard["r_sum"]:
        viol += 2.0 * (pred["r_sum_ohm"] / R_SUM_MAX - 1.0)
    if not hard["settle"]:
        viol += 2.0 * (d5_worst_us(pred) / SETTLE_BUDGET_US - 1.0)
    if not hard["dG_16k"]:
        viol += 4.0 * (pred["dG_16k"] - DG_MAX_DB)
    # 目标：可作用 8 维（ACTIONABLE）的 capped 裕量幂平均；D6/D8 见 design_score 说明。
    # 取负号 —— scipy 的 NM 求最小。
    dims = dim_scores(pred)
    return -design_score(dims) + viol + pen


def uniform_start(n: int, fc_target: float, cg: float, cd: float) -> list:
    """均匀阶梯起点：R 用 fc 反解（利用 R ∝ 1/fc 的精确缩放律）。"""
    base = [(1.0, cg, 0.0) for _ in range(n - 1)] + [(1.0, cg, cd)]
    r = fc_dm(base) / fc_target
    return [r] * n + [cg] * n + [cd] + [fc_target]


def initial_points(n: int, rng: np.random.Generator, n_starts: int,
                   anchor: list | None = None) -> list:
    """确定性起点：fc × C_gnd × C_diff 网格 + 几何阶梯 + 种子随机扰动。

    ``anchor``（本轮新增）：上一轮的冻结参数 —— 从它出发的一个起点，
    保证「以第 1 轮解为起点重新求解」。
    """
    grid = []
    for fc_t in (50e3, 60e3, 70e3, 80e3):
        for cg in (100e-9, 47e-9):
            for cd in (47e-9, 10e-9):
                grid.append(uniform_start(n, fc_t, cg, cd))
    pts = [grid[(i * 3) % len(grid)] for i in range(max(n_starts, 1))]
    for ratio in (3.0, 10.0):         # 前级大 R、末级小 R（FIN1 型几何递减）
        base = uniform_start(n, 62e3, 68e-9, 33e-9)
        rr = [base[i] / (ratio ** (i - (n - 1) / 2.0)) for i in range(n)]
        pts.append(rr + base[n:])
    if anchor is not None:
        pts.insert(0, _pack(anchor, fc_dm(anchor)).tolist())
    for _ in range(3):
        b = np.array(pts[int(rng.integers(0, len(pts)))], dtype=float)
        z = np.log(np.maximum(b, 1e-15)) + rng.normal(0, 0.6, size=len(b))
        pts.append(np.exp(z).tolist())
    return pts


def _pack(stages, fc_t: float) -> np.ndarray:
    n = len(stages)
    return np.array([math.log(max(s[0], 1e-12)) for s in stages]
                    + [math.log(max(s[1], 1e-18)) for s in stages]
                    + [math.log(max(stages[-1][2], 1e-18)), math.log(fc_t)])


def solve_candidate(n_stages: int, seed: int = 0, maxiter: int = 220,
                    n_starts: int = 3, verbose: bool = False,
                    anchor: list | None = None) -> dict:
    """给定级数的多起点 Nelder-Mead 求解。

    返回 {"stages": [(R, C_gnd, C_diff), ...], "pred": {...}, "dims": {...}, "meta": {...}}
    """
    rng = np.random.default_rng(seed)
    starts = initial_points(n_stages, rng, n_starts, anchor=anchor)
    tried = []
    for k, s0 in enumerate(starts):
        x0 = np.asarray(s0, dtype=float)
        if not np.all(np.isfinite(x0)) or np.any(x0 <= 0):
            continue
        res = minimize(objective, x0, args=(n_stages,),
                       method="Nelder-Mead",
                       options={"maxiter": maxiter, "xatol": 1e-3, "fatol": 1e-4})
        stages, _ = build_from_x(res.x, n_stages)
        mm, pred, dims = score_of(stages)
        rec = {"stages": stages, "pred": pred, "dims": dims,
               "meta": {"n_stages": n_stages, "seed": seed,
                        "min_score": mm, "feasible": all(hard_checks(pred).values()),
                        "design": design_score(dims),
                        "start": k, "f_obj": float(res.fun), "n_starts": len(starts),
                        "hard": hard_checks(pred)}}
        tried.append(rec)
        if verbose:
            print(f"    start#{k:02d} min={mm:.3f} design={rec['meta']['design']:.3f} "
                  f"fc={pred['f_c_hz']/1e3:5.1f}k ΣR={pred['r_sum_ohm']:6.1f} "
                  f"DM={pred['A_dm']:5.1f} CM={pred['A_cm']:5.1f} "
                  f"dG={pred['dG_16k']:.3f} Vn={pred['V_n_lsb']:.2f} "
                  f"feasible={rec['meta']['feasible']}")
    feas = [r for r in tried if r["meta"]["feasible"]]
    if feas:
        feas.sort(key=lambda r: (r["meta"]["design"], rank_key(r)), reverse=True)
        best = feas[0]
    else:
        # 全不可行时按**罚函数值**排序（越小越好），否则会在越界角里挑到最深的 fc
        tried.sort(key=lambda r: r["meta"]["f_obj"])
        best = tried[0]
    out = {
        "stages": [(round(float(r), 6), float(cg), float(cd)) for r, cg, cd in best["stages"]],
        "pred": best["pred"],
        "dims": best["dims"],
        "meta": dict(best["meta"]),
    }
    out["meta"]["all_starts"] = [
        {"start": r["meta"]["start"], "min_score": r["meta"]["min_score"],
         "design": r["meta"]["design"],
         "f_c_hz": r["pred"]["f_c_hz"], "feasible": r["meta"]["feasible"],
         "stages": [[float(a), float(b), float(c)] for a, b, c in r["stages"]]}
        for r in tried
    ]
    return out


# ----------------------------------------------------------------------------
# 4. 报告
# ----------------------------------------------------------------------------

DIM_LABEL = {
    "D1": "A_dm@fMOD(dB)", "D2": "A_cm@fMOD(dB)", "D3": "A_mclk(dB)", "D4": "ΔG16k(dB)",
    "D5": "t_settle(µs)", "D6": "Vn(LSB)", "D7": "σΔG(dB)", "D8": "CMRR(dB)",
    "D9": "kickback", "D10": "Δτ(µs)",
}


def _dim_value(dim: str, pred: dict) -> float:
    return {
        "D1": pred["A_dm"], "D2": pred["A_cm"], "D3": pred["A_mclk"], "D4": pred["dG_16k"],
        "D5": d5_worst_us(pred), "D6": pred["V_n_lsb"],
        "D7": pred["sigma_dG_db"], "D8": pred["CMRR_pb_db"],
        "D9": 1.0 if pred["kickback_ok"] else 0.0,
        "D10": pred["group_delay_flat_s"] * 1e6,
    }[dim]


def short_topo(stages) -> str:
    out = []
    for r, cg, cd in stages:
        s = f"{r:.2f}Ω/{cg*1e9:.0f}n"
        s += f"+{cd*1e9:.0f}nd" if cd > 0 else ""
        out.append(s)
    return "—".join(out)


def print_front(results: list) -> None:
    print("\n=== 帕累托前沿（理论预测，真实跟随器口径） ===")
    hdr = (f"{'级':>2} {'min':>5} {'des':>5} {'过线':>4} {'fc/kHz':>6} {'ΣR/Ω':>7} {'A_dm':>6} "
           f"{'A_cm':>6} {'A_mk':>6} {'ΔG16k':>6} {'ts/µs':>6} {'Vn':>5} {'σΔG':>6} "
           f"{'CMRR':>5} {'Δτ/µs':>6}  拓扑")
    print(hdr)
    for r in sorted(results, key=lambda z: (z["meta"]["n_stages"],
                                            tuple(-v for v in rank_key(z)))):
        p, d = r["pred"], r["dims"]
        npass = sum(pass_flags(d, p).values())
        print(f"{r['meta']['n_stages']:>2} {r['meta']['min_score']:>5.3f} "
              f"{design_score(d):>5.3f} {npass:>3}/10 "
              f"{p['f_c_hz']/1e3:>6.1f} {p['r_sum_ohm']:>7.1f} {p['A_dm']:>6.1f} "
              f"{p['A_cm']:>6.1f} {p['A_mclk']:>6.1f} {p['dG_16k']:>6.3f} "
              f"{p['t_settle_wc_s']*1e6:>6.0f} {p['V_n_lsb']:>5.2f} {p['sigma_dG_db']:>6.3f} "
              f"{p['CMRR_pb_db']:>5.1f} {p['group_delay_flat_s']*1e6:>6.2f}  {short_topo(r['stages'])}")


def print_dims(rec: dict) -> None:
    p, d = rec["pred"], rec["dims"]
    pf = pass_flags(d, p)
    line = "  ".join(
        f"{k}:{_dim_value(k, p):.3g}{'' if pf[k] else '×'}({d[k]:.2f})" for k in
        ("D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10"))
    print("   " + line)


def source_sensitivity(stages) -> dict:
    """诊断：同一组参数在 0 Ω 理想源 / 1 Ω 引擎 / 真实跟随器三个口径下的关键量。"""
    out = {}
    for name in ("ideal", "engine", "opa388"):
        out[name] = {
            "A_dm": -float(gain_db(stages, "dm", FMOD_HZ, source=name)),
            "A_cm": -float(gain_db(stages, "cm", FMOD_HZ, source=name)),
            "A_mclk": -float(gain_db(stages, "dm", MCLK_HZ, source=name)),
            "dG_16k": abs(float(gain_db(stages, "dm", 16e3, source=name))),
            "f_c_hz": fc_dm(stages, source=name),
        }
    out["zout_fmod_ohm"] = float(abs(zout_cl(FMOD_HZ)[0]))
    out["zout_16k_ohm"] = float(abs(zout_cl(16e3)[0]))
    return out


def run_all(maxiter: int = 220, starts: int = 3, anchors: dict | None = None) -> list:
    results = []
    for n in (2, 3, 4):
        print(f"\n--- {n} 级求解（Nelder-Mead × {starts} 起点，fc∈[50,80] kHz，真实跟随器）---")
        anchor = None
        if anchors and str(n) in anchors:
            anchor = [(float(a), float(b), float(c)) for a, b, c in anchors[str(n)]]
        r = solve_candidate(n, seed=0, maxiter=maxiter, n_starts=starts,
                            verbose=True, anchor=anchor)
        print(f"  → min={r['meta']['min_score']:.3f}  design={r['meta']['design']:.3f}  "
              f"fc={r['pred']['f_c_hz']/1e3:.1f} kHz  ΣR={r['pred']['r_sum_ohm']:.1f} Ω  "
              f"{short_topo(r['stages'])}")
        print_dims(r)
        print(f"     hard={r['meta']['hard']}")
        if not r["meta"]["feasible"]:
            print("     ⚠ 未找到满足全部硬约束的解")
        results.append(r)
    print_front(results)
    print("\n=== 源阻抗口径敏感性（ideal 0Ω / engine 1Ω / opa388 真实） ===")
    for r in results:
        s = source_sensitivity(r["stages"])
        print(f"  {r['meta']['n_stages']} 级: A_dm  "
              f"{s['ideal']['A_dm']:.1f} / {s['engine']['A_dm']:.1f} / {s['opa388']['A_dm']:.1f} dB"
              f"   dG16k {s['ideal']['dG_16k']:.3f} / {s['engine']['dG_16k']:.3f} / "
              f"{s['opa388']['dG_16k']:.3f} dB")
    lim = physics_limits(results[-1]["stages"])
    print("\n=== 物理极限（本轮新增） ===")
    for k, v in lim.items():
        print(f"  {k}: {v}")
    return results


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Round 5 十维理论优化（三案，第 2 轮真实跟随器口径）")
    ap.add_argument("--maxiter", type=int, default=220)
    ap.add_argument("--starts", type=int, default=3)
    ap.add_argument("--json", default="")
    ap.add_argument("--anchor", default="r5_candidates.json",
                    help="上一轮冻结参数（作为额外起点）；空串=不用")
    args = ap.parse_args(argv)
    anchors = None
    if args.anchor and os.path.exists(os.path.join(HERE, args.anchor)):
        with open(os.path.join(HERE, args.anchor), encoding="utf-8") as fh:
            data = json.load(fh)
        anchors = {str(v["n_stages"]): v["stages"] for v in data.values()}
        print(f"锚点（上一轮冻结参数）: { {k: short_topo(v) for k, v in anchors.items()} }")
    results = run_all(args.maxiter, args.starts, anchors)
    if args.json:
        out = {str(r["meta"]["n_stages"]): r for r in results}
        with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(out, fh, ensure_ascii=False, indent=2)
        print(f"\n已写出 {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
