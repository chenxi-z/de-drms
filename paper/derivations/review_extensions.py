#!/usr/bin/env python3
"""Independent exact-response calculations for review tasks T3/T4/T5/T7.

Run from any directory; --output writes a new report, never simulation inputs.
"""
import sys,json,argparse
from pathlib import Path
import numpy as np
import sympy as s
import mpmath as mp
sys.path.insert(0,str(Path(__file__).resolve().parent))
from handoff_audit import chain,moments,x
mp.mp.dps=70
g=s.Rational(1,10);T=1e-5

def fun(n,last=False):
 q=[s.Integer(1)]*n
 if last:q[-1]=s.Rational(11,10)
 a,b=chain([s.Integer(1)]*n,q);d=s.Poly(a+g*b,x)
 return d

def step(d,t):
 coef=[mp.mpf(str(z)) for z in d.all_coeffs()]
 poles=mp.polyroots(coef,maxsteps=1000,error=False)
 d0=mp.mpf(str(d.nth(0)));dc=[coef[i]*(len(coef)-1-i) for i in range(len(coef)-1)]
 return 1+sum(d0/(p*mp.polyval(dc,p))*mp.exp(p*mp.mpf(str(t))/mp.mpf('0.00001')) for p in poles)

out={'sinusoidal':[],'matched':[],'steps':[],'position_N4':[]}
for n in [3,4]:
 dp,dn=fun(n),fun(n,True)
 tp,mp2=moments([s.Integer(1)]*n,[s.Integer(1)]*n,g)
 q=[s.Integer(1)]*(n-1)+[s.Rational(11,10)]
 tn,mn2=moments([s.Integer(1)]*n,q,g)
 tp,tn,mp2,mn2=map(float,[tp,tn,mp2,mn2]);tp*=T;tn*=T;mp2*=T*T;mn2*=T*T
 t=np.linspace(.02,.04,20001);w=2*np.pi*100;I=1+.2*np.sin(w*t);h=.2*w*np.cos(w*t)/I;j=-.2*w*w*np.sin(w*t)/I
 H=lambda d:complex(d.nth(0))/complex(d.eval(1j*w*T))
 hp,hn=H(dp),H(dn)
 exact=1e5*.2*np.imag((hp-hn)*np.exp(1j*w*t))/(1+.2*np.imag(hn*np.exp(1j*w*t)))
 first=-1e5*(tp-tn)*h
 second=first+1e5*((mp2-mn2)*j/2-tn*(tp-tn)*h*h)
 rms=lambda z:float(np.sqrt(np.mean(z*z)))
 R=1e4*np.exp(.5)
 D=lambda z:float(dp.eval(z))
 G=lambda z:float(dp.nth(0))/D(z)
 r0=R*G(.002);r1=R*G(.012)/G(.01)
 out['sinusoidal'].append({'N':n,'delta_mu2_us2':(mp2-mn2)*1e12,'first_relative_RMS':rms(exact-first)/rms(exact),'second_relative_RMS':rms(exact-second)/rms(exact)})
 out['matched'].append({'N':n,'true_R':R,'error_alpha0':r0-R,'history_difference':r1-r0,'bound_alpha0':200*R*tp})
 lo,hi=mp.mpf('.0001'),mp.mpf('.002')
 for k in range(70):
  mid=(lo+hi)/2;err=step(dp,mid)/step(dn,mid)-1
  if err>mp.mpf('0.00001'):lo=mid
  else:hi=mid
 out['steps'].append({'N':n,'computed_crossing_10ppm_us':float(hi*1e6),'early_relative_error_at_0.1us':float(step(dp,mp.mpf('1e-7'))/step(dn,mp.mpf('1e-7'))-1)})
for k in range(4):
 q=[s.Integer(1)]*4;q[k]=s.Rational(11,10)
 tau=moments([s.Integer(1)]*4,[s.Integer(1)]*4,g)[0]
 out['position_N4'].append(float(tau-moments([s.Integer(1)]*4,q,g)[0])*10)
out['noise_equivalent_bits_1p2V_span']=[float(np.log2(1.2/(np.sqrt(12)*z*1e-6))) for z in [.578669,.561937,.552486,.546836]]
# Independent frequency-domain noise integration, source suppressed.
kB=1.380649e-23;theta=300.;freq=np.geomspace(10.,1e5,40001)
out['independent_noise_integration']=[]
for n in range(1,5):
 K=np.zeros((n,n))
 for j in range(n):
  K[j,j]+=.001
  if j:
   K[j-1,j-1]+=.001;K[j,j-1]-=.001;K[j-1,j]-=.001
 K[-1,-1]+=.0001
 Y=K[None,:,:]+2j*np.pi*freq[:,None,None]*np.eye(n)[None,:,:]*1e-8
 rhs=np.zeros((len(freq),n,1));rhs[:,-1,0]=1
 z=np.linalg.solve(Y,rhs)[:,-1,0]
 total=4*kB*theta*z.real;load=4*kB*theta*.0001*abs(z)**2
 ladder=np.sqrt(np.trapezoid(total-load,freq));allnoise=np.sqrt(np.trapezoid(total,freq))
 out['independent_noise_integration'].append({'N':n,'ladder_uVrms':ladder*1e6,'including_load_uVrms':allnoise*1e6})

def coeffmap(v):
 n=len(v)//2;a=np.array([1.+0j]);b=np.array([0.+0j])
 for r,q in zip(v[:n],v[n:]):
  b=np.polynomial.polynomial.polyadd(r*a,b)
  a=np.polynomial.polynomial.polyadd(a,np.r_[0,q*b])
 return np.r_[a[1:],b]
out['dimensionless_coefficient_Jacobian_cond2']=[]
for n in [2,4,6,8,10,12]:
 J=np.empty((2*n,2*n))
 for j in range(2*n):
  v=np.ones(2*n,dtype=complex);v[j]+=1e-20j;J[:,j]=coeffmap(v).imag/1e-20
 out['dimensionless_coefficient_Jacobian_cond2'].append({'N':n,'cond2':float(np.linalg.cond(J))})
out['PQ_zero_frequency_strong_load_CMRR_dB']=float(20*np.log10(7/6))
parser=argparse.ArgumentParser()
parser.add_argument('--output',type=Path)
args=parser.parse_args()
if args.output:
 args.output.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
