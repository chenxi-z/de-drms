#!/usr/bin/env python3
"""Exact checks for calibrated dynamic ratios and the P-minus-T step response.

The buffered sources are vP=I*R and vN=I*Rs. For normalized channel
kernels gP,gN the calibrated estimate is (gP*(IR))/(gN*I), in ohms.
Matched kernels reject arbitrary current changes for constant R; varying
R retains a current-dependent history average. This script checks algebra,
normalization, the signed delay term, and distinct step/impulse energies.
It performs no circuit simulation and modifies no historical evidence.
"""
import argparse
import json
from fractions import Fraction as F
from pathlib import Path
import mpmath as mp
import sympy as sp

x = sp.symbols('x')

def chain_poly(rs, qs, g):
    a, b = sp.Poly(1, x), sp.Poly(0, x)
    for r, q in zip(rs, qs):
        b = sp.Rational(r) * a + b
        a = a + sp.Poly(sp.Rational(q) * x, x) * b
    return a + sp.Rational(g) * b, a, b

def dc_delay(rs, qs, g):
    """D'_x(0)/D(0); multiply by Rstar*Cstar for seconds."""
    d = chain_poly(rs, qs, g)[0].as_expr()
    return sp.cancel(sp.diff(d, x).subs(x, 0) / d.subs(x, 0))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = {'checks': [], 'scope': 'Symbolic/reference calculations, not SPICE or physical measurements.'}
    def check(name, condition):
        assert bool(condition), name
        report['checks'].append({'name': name, 'pass': True})

    # Reference voltage includes Rs, so calibration removes its extra factor.
    ii, rr, rs = sp.symbols('I R Rs', nonzero=True)
    check('calibrated ratio has resistance units', sp.cancel(rs * ii * rr / (ii * rs)) == rr)

    # First moment expansion of the quotient, with Delta_tau=P minus N.
    eps = sp.symbols('eps')
    ip, rp, tp, tn = sp.symbols('Idot Rdot tauP tauN')
    quotient = (ii*rr - eps*tp*(ip*rr + ii*rp))/(ii-eps*tn*ip)
    first = sp.diff(quotient, eps).subs(eps, 0)
    target = -tp*rp - rr*(ip/ii)*(tp-tn)
    check('signed first-order moment term', sp.simplify(first-target) == 0)

    # A normalized-shape match need not be a raw-gain match.
    dp = chain_poly([F(1)], [F(1)], F(1, 10))[0].as_expr()
    dn = chain_poly([F(2)], [F(6, 11)], F(1, 10))[0].as_expr()
    check('normalized equality with different raw gains',
          sp.simplify(dp.subs(x, 0)/dp-dn.subs(x, 0)/dn) == 0 and sp.simplify(dp-dn) != 0)

    # Exact positive two-stage counterexample to varying-R current immunity.
    d = chain_poly([F(1), F(1)], [F(1), F(1)], F(1, 10))[0].as_expr()
    g = d.subs(x, 0)/d
    factor_const = sp.cancel(g.subs(x, 1))
    factor_exp = sp.cancel(g.subs(x, 2)/g.subs(x, 1))
    check('matched changing-R estimate depends on current history', factor_const != factor_exp)
    report['counterexample_dimensionless_beta_1'] = {
        'constant_current_Rhat_over_R': str(factor_const),
        'exponential_current_alpha_1_Rhat_over_R': str(factor_exp)}

    # Delay differences for the corrected three/four-stage transient matrix.
    report['last_reference_capacitor_plus10percent'] = []
    for n in [2, 3, 4]:
        qn = [F(1)]*n; qn[-1] = F(11, 10)
        delta = dc_delay([F(1)]*n, [F(1)]*n, F(1, 10)) - dc_delay([F(1)]*n, qn, F(1, 10))
        check(f'N{n} reference slower gives negative Delta_tau', delta < 0)
        report['last_reference_capacitor_plus10percent'].append({'N': n, 'delta_tau_P_minus_N_s': float(delta)*1e-5})

    # Actual P/T construction, both evaluated at the observation load g=.2.
    P = ([F(1), F(1)], [F(1), F(1)])
    T = ([F(18, 19), F(20, 19)], [F(361, 180), F(1, 2)])
    DP, AP, BP = chain_poly(*P, F(1, 5))
    DT, AT, BT = chain_poly(*T, F(1, 5))
    check('P/T exactly matched at g0=.1', chain_poly(*P, F(1, 10))[0] == chain_poly(*T, F(1, 10))[0])
    transfer = sp.cancel(1/DP.as_expr()-1/DT.as_expr())
    from_shift = sp.cancel(-F(1, 10)*(BP.as_expr()-BT.as_expr())/(DP.as_expr()*DT.as_expr()))
    check('load-shift sign equals P-minus-T output', sp.simplify(transfer-from_shift) == 0)
    check('positive step numerator', sp.simplify(transfer*DP.as_expr()*DT.as_expr()-x/10) == 0)
    report['P_minus_T_transfer_x'] = str(transfer)

    # Unit-step response residues belong to F(x)/x, not to F(x).
    mp.mp.dps = 60
    poles = [mp.mpf('-2.8'), (-8-mp.sqrt(29))/5, (-8+mp.sqrt(29))/5, mp.mpf('-.5')]
    den = sp.Poly(DP.as_expr()*DT.as_expr(), x)
    derivative = [mp.mpf(str(v)) for v in sp.Poly(sp.diff(den.as_expr(), x), x).all_coeffs()]
    residues = [mp.mpf('.1')/mp.polyval(derivative, p) for p in poles]
    step = lambda theta: sum(a*mp.exp(p*theta) for a,p in zip(residues,poles))
    slope = lambda theta: sum(a*p*mp.exp(p*theta) for a,p in zip(residues,poles))
    theta_peak = mp.findroot(slope, (mp.mpf('2.5'), mp.mpf('3.1')))
    scale = mp.mpf('1e-5')
    step_energy = scale*sum(a*b/(-(p+q)) for a,p in zip(residues,poles) for b,q in zip(residues,poles))
    quadrature = scale*mp.quad(lambda u: step(u)**2, [0, 1, 3, 10, mp.inf])
    check('step residue energy agrees with independent quadrature', abs(step_energy/quadrature-1) < mp.mpf('1e-30'))
    impulse_energy = sum(a*b*p*q/(-(p+q)*scale) for a,p in zip(residues,poles) for b,q in zip(residues,poles))
    report['P_minus_T_unit_step'] = {
        'peak_V_per_V': float(step(theta_peak)), 'peak_time_s': float(theta_peak*scale),
        'asymptotic_time_constant_s': float(-scale/max(poles)),
        'step_squared_integral_per_Vc2_s': float(step_energy),
        'impulse_squared_integral_per_s': float(impulse_energy),
        'poles_dimensionless': [float(p) for p in poles]}
    report['all_pass'] = True
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(exist_ok=True, parents=True)
        args.output.write_text(text+'\n')
    print(text)

if __name__ == '__main__':
    main()
