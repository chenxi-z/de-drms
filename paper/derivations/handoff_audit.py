#!/usr/bin/env python3
"""Exact audit of the 2026-10-28 handoff; no historical outputs are changed."""
import argparse
import json
from pathlib import Path
import sympy as s

x = s.symbols('x')


def chain(r, q):
    a, b = s.Poly(1, x), s.Poly(0, x)
    for ri, qi in zip(r, q):
        b = ri*a+b
        a = a+s.Poly(x*qi, x)*b
    return a.as_expr(), b.as_expr()


def moments(r, q, g):
    a, b = chain(r, q)
    d = s.Poly(a+g*b, x)
    tau = s.cancel(d.nth(1)/d.nth(0))
    mu2 = s.cancel(2*(tau**2-d.nth(2)/d.nth(0)))
    return tau, mu2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()
    checks = []
    def check(name, truth):
        assert bool(truth), name
        checks.append(name)
    g = s.Rational(1, 10)
    k = s.symbols('k', positive=True)
    for n in range(1, 7):
        a, b = chain([s.Integer(1)]*n, [s.Integer(1)]*n)
        ak, bk = chain([k]*n, [1/k]*n)
        check(f'N{n}: reciprocal impedance scaling preserves A and scales B',
              s.expand(ak-a) == 0 and s.expand(bk-k*b) == 0)
        am, bm = chain([k]*n, [k]*n)
        check(f'N{n}: same-direction scaling changes time scale',
              s.expand(am-a.subs(x,k*k*x)) == 0 and
              s.expand(bm-k*b.subs(x,k*k*x)) == 0)
    for n in range(1, 13):
        tau, _ = moments([s.Integer(1)]*n, [s.Integer(1)]*n, g)
        formula = (s.Rational(n*(n+1),2)+g*s.Rational(n*(n*n-1),6))/(1+g*n)
        check(f'N{n}: finite-load delay closed form', tau == formula)
        qn = [s.Integer(1)]*(n-1)+[s.Rational(11,10)]
        taun, _ = moments([s.Integer(1)]*n, qn, g)
        check(f'N{n}: last-cap +10% delay difference',
              s.cancel(tau-taun+s.Rational(n,n+10)) == 0)
    r = s.symbols('r', positive=True)
    q = (r+10)/(11*r)
    a, b = chain([r], [q])
    d = a+g*b
    check('N1 calibrated family', s.cancel(d/d.subs(x,0)-(1+10*x/11)) == 0)
    a0,b0 = chain([s.Integer(1)]*2,[s.Integer(1)]*2)
    qa=(217+s.sqrt(6769))/288
    qb=(217-s.sqrt(6769))/480
    aa,ba=chain([s.Integer(2)]*2,[qa,qb])
    dp=a0+g*b0
    da=aa+g*ba
    check('N2 calibrated family witness',
          s.simplify(da/da.subs(x,0)-dp/dp.subs(x,0)) == 0)
    check('N2 witness has different raw DC gains', da.subs(x,0) != dp.subs(x,0))
    # A repeated pole cannot be an eigenvalue of an irreducible symmetric
    # tridiagonal RC conductance pencil. The proof is recorded in the audit note.
    check('rejected handoff example has a repeated pole', s.discriminant((1+x)**3,x) == 0)
    tp, mp = moments([s.Integer(1)]*2,[s.Integer(1)]*2,g)
    tn, mn = moments([s.Integer(2),s.Integer(1)], [s.Rational(3,2),s.Rational(7,360)],g)
    check('equal delay does not imply equal second moment', tp == tn and mp != mn)
    eps=s.symbols('eps')
    ii,rr=s.symbols('I R',nonzero=True)
    i1,i2,r1,r2,tp2,tn2,mp2,mn2=s.symbols('I1 I2 R1 R2 tauP tauN muP muN')
    numerator=ii*rr-eps*tp2*(i1*rr+ii*r1)+eps**2*mp2*(i2*rr+2*i1*r1+ii*r2)/2
    denominator=ii-eps*tn2*i1+eps**2*mn2*i2/2
    coefficient=s.diff(numerator/denominator,eps,2).subs(eps,0)/2
    target=mp2*r2/2+(mp2-tp2*tn2)*i1*r1/ii+rr*((mp2-mn2)*i2/(2*ii)-tn2*(tp2-tn2)*(i1/ii)**2)
    check('complete second-order temporal quotient including denominator terms',s.simplify(coefficient-target)==0)
    report = {'scope':'Exact rational/symbolic calculations; no physical measurements.',
              'pass_count':len(checks),'checks':checks,
              'normalized_N2_witness_CMRR_dB':float(20*s.log(s.Rational(13,2),10)),
              'equal_delay_counterexample':{'tau_over_T':str(tp),
                  'Delta_mu2_over_T2':str(mp-mn)},
              'decision':'B: distinguish reciprocal impedance scaling from same-direction R/C scaling before engineering recommendations.'}
    if args.output:
        args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
