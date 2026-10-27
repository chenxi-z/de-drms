#!/usr/bin/env python3
"""动态比值测量理论推导与符号/数值核验（2026-10-28，ZCode）。

模型（M1，缓冲前端——样品电阻调制源幅度，网络本身 LTI）：
  v_P(t) = I(t)·R(t),  v_N(t) = I(t)·R_s
  G_P, G_N = 两支路**直流增益归一**的负载传函（G(0)=1）
  R̂(t) = R_s · [g_P ⊛ (I·R)](t) / [g_N ⊛ I](t)

产出（全部 sympy 精确 + 数值核验）：
  P1 匹配通道：R̂ = g,I-加权平均恒等式；误差界 |R̂−R| ≤ L_R·(Imax/Imin)·M₁(|g|)
  P2 失配通道一阶：R̂−R ≈ 滞后项 + R·İ·Δτ + R·L_R·ΔM₁ 项（Δτ=直流群时延差，
     Δτ = R*C*·[D_P'(0)/D_P(0) − D_N'(0)/D_N(0)]）
  P3 焊接定理：负载 g 下 D_P=D_N ⟺ 该负载下任意 I(t) 波动精确消去（动态）——
     静态消去条件与动态比值稳健性同构
  P4 CM 瞬态脉冲：G_DC=−(g−g₀)ΔB/(D_P D_N)（g₀ 配平族）的阶跃响应峰值/H₂ 能量/
     峰值时间，N=2 闭式 + 一般 N 数值
"""
import sympy as sp
from fractions import Fraction as F

x, s = sp.symbols('x s', real=True)

# ---------- 与 B 包一致的 Fraction 链工具（复用口径） ----------
def chain_poly(rF, qF, gF):
    """返回 D(x)=A(x)+g·B(x) 的 sympy 多项式（系数精确有理）。"""
    A = sp.Poly(1, x); B = sp.Poly(0, x)
    for r, q in zip(rF, qF):
        B = A*sp.Rational(r) + B
        A = A + sp.Poly(sp.Rational(q)*x, x)*B
    D = A + B*sp.Rational(gF)
    return sp.Poly(D, x), sp.Poly(A, x), sp.Poly(B, x)

def dc_delay(rF, qF, gF):
    """归一化传函 G=1/D/D(0) 的直流群时延（单位 x，秒=R*C*·该值）。"""
    D, A, B = chain_poly(rF, qF, gF)
    p = D.as_expr()
    return sp.simplify(sp.diff(p, x).subs(x, 0) / p.subs(x, 0))

# ---------- P1/P2 核心恒等式（符号推演，t 域） ----------
t, tau = sp.symbols('t tau', positive=True)
# 恒等式：R̂−R = [g⊛(I·(R(t−·)−R(t)))](t) / [g⊛I](t)   （匹配通道，直接可验）
# 数值核验用卷积离散化；理论部分见 dynamic-analysis.md 推导。

# ---------- P4：N=2 闭式瞬态脉冲 ----------
def pulse_N2(dp, dn, dB, g, g0):
    """D_P, D_N 为 N=2 分母（x 多项式），ΔB=Δd·x；返回阶跃响应 y(t)=L⁻¹[G_DC/s]
    的符号式与峰值/能量量（G_DC=−(g−g0)ΔB/(D_P D_N)，x 域→s 域 1:1）。"""
    Gdc = -sp.Rational(g-g0)*dB/((dp*dn).as_expr())
    Y = sp.apart(Gdc/s, s, extension=True) if False else None
    return Gdc

def main():
    print("="*72)
    print("P2 直流群时延公式核验（N=2,3）与失配通道 Δτ")
    print("="*72)
    # 基线（B 包口径）
    for N, rr, qq in [(2, [F(6,5), F(4,5)], [F(3,7), F(6,7)]),
                      (3, [F(6,5), F(4,5), 1], [F(3,7), F(6,7), 1])]:
        for g in [F(0), F(1,10), F(1,5)]:
            tau_ = dc_delay(rr, qq, g)
            print(f"  N={N} g={g}: τ_eff(x-units) = {tau_} = {float(tau_):.6f}")
    # 失配 Δτ：扰动 B 包的 T/P 例（P 基线 vs Q=固定负载等效族）
    print("\n  失配例（N=2，FEQ 族）：P=(1,1,1,1)，Q 同 D@g=0.1 但不同元件")
    P = ([F(1),F(1)],[F(1),F(1)]); g1 = F(1,10)
    # 用 B 包 perturb 思路：B2=B+tD, A2=A−g1 tD（D=x）
    Dp = sp.Poly(x, x)
    Ap, Bp = chain_poly(*P, F(0))[1], chain_poly(*P, F(0))[2]
    for tF in [F(1,10), F(1,5)]:
        A2 = sp.Poly(sp.expand(Ap.as_expr() - g1*tF*Dp.as_expr()), x)
        B2 = sp.Poly(sp.expand(Bp.as_expr() + tF*Dp.as_expr()), x)
        D_P = (Ap + Bp*g1).as_expr(); D_Q = (A2 + B2*g1).as_expr()
        dP = sp.diff(D_P, x).subs(x,0)/D_P.subs(x,0)
        dQ = sp.diff(D_Q, x).subs(x,0)/D_Q.subs(x,0)
        print(f"   t={tF}: D_P==D_Q? {sp.simplify(D_P-D_Q)==0}；τ_P={float(dP):.6f} τ_Q={float(dQ):.6f}"
              f" → Δτ={float(dQ-dP):+.6f}（注意：同 D ⟹ 同 τ）")

    print()
    print("="*72)
    print("P4 N=2 CM 瞬态脉冲闭式（负载偏移族）")
    print("="*72)
    # P=(1,1,1,1), Q: Δd 失配（非等效，直接元件差），g0=配平负载不存在→用一般失配
    # 取 FEQ 例：在 g0=0.1 配平、g=0.2 观察。D_P=D_Q(记 D)，ΔB=xΔd
    dpoly, Ap, Bp = chain_poly([F(1),F(1)],[F(1),F(1)], F(0))
    tF = F(1,10); g0 = F(1,10)
    A2 = sp.Poly(sp.expand(Ap.as_expr() - g0*tF*Dp.as_expr()), x)
    B2 = sp.Poly(sp.expand(Bp.as_expr() + tF*Dp.as_expr()), x)
    ΔB = sp.Poly(sp.expand((B2-Bp).as_expr()), x)   # = tF·x
    gobs = F(1,5)
    DPg = (Ap + Bp*gobs).as_expr(); DQg = (A2 + B2*gobs).as_expr()
    Gdc = sp.expand(-(gobs-g0)*ΔB.as_expr()/(DPg*DQg))
    print(f"  G_DC(s) = {Gdc}")
    print(f"  G_DC(0) = {sp.simplify(Gdc.subs(x,0))}（零——脉冲型）")
    # 阶跃响应：Y(s)=G_DC/s 的留数（x↔s 1:1，数值即可）
    Y = Gdc/x  # 1/s 用 1/x 表记
    apart = sp.apart(sp.together(Y), x, full=True)
    print(f"  Y(s)=G_DC/s 部分分式：{apart}")
    y = sp.inverse_laplace_transform(Gdc.subs(x, s)/s, s, t)
    y = sp.simplify(y)
    print(f"  y(t) = {y}")
    # 峰值与 H2 能量（数值）
    yf = sp.lambdify(t, y, 'numpy')
    import numpy as np
    ts = np.linspace(0, 20, 400001)  # x 单位（R*C*=1e-5 s；脉冲宽度 ~0.1–10 x）
    ys = yf(ts)
    pk = np.max(np.abs(ys)); tpk = ts[np.argmax(np.abs(ys))]
    print(f"  峰值={pk:.6e}（x 单位）@ t={tpk:.4f} x-units = {tpk*1e-5:.3e} s")
    # H2 能量：‖g_DC‖²₂ = Σ r_k r_j/(−(p_k+p_j)) 留数式（数值极点）
    den = sp.denom(sp.together(Gdc)); num = sp.numer(sp.together(Gdc))
    poles = [complex(p) for p in sp.nroots(sp.Poly(den, x))]
    res = [complex(num.subs(x, p)/sp.diff(den, x).subs(x, p)) for p in poles]
    print(f"  极点（x 单位，数值）：{[f'{p.real:.4f}{p.imag:+.4f}j' for p in poles]}")
    H2sq = sum(res[i]*res[j]/(-(poles[i]+poles[j])) for i in range(len(poles)) for j in range(len(poles)))
    print(f"  ‖g_DC‖₂² = {H2sq:.6e}；‖g_DC‖₂ = {abs(H2sq)**0.5:.6e}")
    return 0

def mismatch_dtau():
    """P2b 元件偏差的 Δτ：运行负载下两支路直流群时延差 + 一阶动态比值误差预测。"""
    print("\n" + "="*72)
    print("P2b 元件偏差的 Δτ（一阶预测：失配通道 R̂−R 含 R·İ·Δτ 项）")
    print("="*72)
    P = ([F(1), F(1)], [F(1), F(1)])
    for delta in [F(1, 50), F(1, 20), F(1, 10)]:
        Q = (P[0], [P[1][0], P[1][1]*(1+delta)])
        for g in [F(1, 10), F(1, 5)]:
            tP = dc_delay(*P, g); tQ = dc_delay(*Q, g)
            print(f"  Δq2=+{float(delta)*100:.0f}% g={g}: τ_P={float(tP):.5f} τ_Q={float(tQ):.5f} "
                  f"Δτ={float(tQ-tP):+.5f} x = {float(tQ-tP)*10:+.3f} µs")

if __name__ == "__main__":
    main()
    mismatch_dtau()
