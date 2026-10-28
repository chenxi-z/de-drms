#!/usr/bin/env python3
"""Original dynamic-response figures from corrected, immutable native evidence.
Style adapted from executed howtoSCI tpl_curve_matrix and generate_figures.py.
No simulator is launched and no archived evidence is modified.
"""
from pathlib import Path
import argparse, json, hashlib, re
import numpy as np
from numpy.polynomial import Polynomial as Poly
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
from PIL import Image, ImageChops

BASE=Path(__file__).resolve().parents[1];OUT=BASE/'figures';OUT.mkdir(exist_ok=True)
a=argparse.ArgumentParser();a.add_argument('--verification',type=Path);args=a.parse_args()
V=args.verification or Path(json.loads(Path('/tmp/paper-qoder-ltspice-active.json').read_text())['root']).parent
C=V/'2026-10-28-codex-audit/dynamic-corrections';DYN=V/'2026-10-28-dynamic'
SHA={};QA=[];METRICS={}
COL=['#000000','#e01b1b','#1f4fd8']
mpl.rcParams.update({'font.family':'serif','font.serif':['Times New Roman'],'mathtext.fontset':'custom','mathtext.rm':'Times New Roman','mathtext.it':'Times New Roman:italic','mathtext.bf':'Times New Roman:bold','mathtext.cal':'Times New Roman','mathtext.fallback':None,'svg.fonttype':'none','pdf.fonttype':42,'font.size':7.3,'axes.labelsize':7.5,'axes.linewidth':.75,'axes.labelpad':1.5,'xtick.labelsize':7.3,'ytick.labelsize':7.3,'xtick.direction':'in','ytick.direction':'in','xtick.major.size':2.2,'ytick.major.size':2.2,'xtick.major.width':.5,'ytick.major.width':.5,'xtick.major.pad':1.5,'ytick.major.pad':1.5,'legend.fontsize':7.3,'legend.framealpha':1,'legend.edgecolor':'black','legend.fancybox':False,'legend.handlelength':1.2,'legend.columnspacing':.6,'lines.linewidth':.75,'savefig.dpi':600})

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 SHA[str(p)]=h.hexdigest();return h.hexdigest()

summary=json.loads((C/'results.json').read_text());sha(C/'results.json')
for row in summary['cases']:
 if row['id'] in ['N3_matched_exp_a0','N3_matched_exp_a1000','N4_matched_exp_a0','N4_matched_exp_a1000','N4_mismatch_sine']:
  for ext,h in row['sha256'].items():assert sha(C/row['id']/('case'+ext))==h

def curves(name):
 p=C/name/'curves.npz';sha(p);z=np.load(p);return {k:z[k] for k in z.files}
def denom(n,last_q=1):
 """Dimensionless grounded-ladder determinant, all r=1 and g=.1."""
 d0=Poly([1]);d1=Poly([2,1])
 for j in range(2,n+1):
  dj=Poly([1.1 if j==n else 2,last_q if j==n else 1])*d1-d0;d0,d1=d1,dj
 return d1

def new():
 fig,ax=plt.subplots(figsize=(7.5/2.54,5.625/2.54));fig.subplots_adjust(left=.19,right=.97,bottom=.19,top=.97)
 ax.tick_params(which='both',top=True,right=True,direction='in');ax.xaxis.set_minor_locator(AutoMinorLocator(2));ax.yaxis.set_minor_locator(AutoMinorLocator(2));return fig,ax

def save(fig,key):
 fig.canvas.draw();renderer=fig.canvas.get_renderer();hits=0;coll=[]
 for ax in fig.axes:
  texts=[t for t in ax.texts if t.get_visible() and t.get_text()]
  for i,t in enumerate(texts):
   for u in texts[i+1:]:
    if t.get_window_extent(renderer).overlaps(u.get_window_extent(renderer)):coll.append([t.get_text(),u.get_text()])
  leg=ax.get_legend()
  if leg is not None:
   b=leg.get_window_extent(renderer)
   for ln in ax.lines:
    pp=ax.transData.transform(ln.get_xydata());hits+=int(np.sum((pp[:,0]>b.x0)&(pp[:,0]<b.x1)&(pp[:,1]>b.y0)&(pp[:,1]<b.y1)))
 assert not coll and hits==0,(key,coll,hits)
 for ext in ['svg','pdf','png']:fig.savefig(OUT/(key+'.'+ext),bbox_inches='tight',pad_inches=0,facecolor='white',dpi=600)
 im=Image.open(OUT/(key+'.png')).convert('RGB');bb=ImageChops.difference(im,Image.new('RGB',im.size,'white')).getbbox();im=im.crop(bb);im.save(OUT/(key+'.png'),dpi=(600,600));bb=ImageChops.difference(im,Image.new('RGB',im.size,'white')).getbbox();border=[bb[0],bb[1],im.width-bb[2],im.height-bb[3]];assert border==[0,0,0,0]
 ss=(OUT/(key+'.svg')).read_text();sizes=[float(v) for v in re.findall(r'font-size:\s*([0-9.]+)px',ss)]+[float(v) for v in re.findall(r'font:\s*([0-9.]+)px',ss)];assert sizes and min(sizes)>=5
 markers=[ln for ax in fig.axes for ln in ax.lines if ln.get_marker() not in [None,'None','none','']];assert not any(ln.get_clip_on() for ln in markers)
 QA.append({'figure':key,'canvas_cm':[7.5,5.625],'png_pixels':list(im.size),'border_pixels':border,'actual_svg_min_glyph_pt':min(sizes),'annotation_collisions':coll,'legend_curve_samples_intersected':hits,'marker_artist_clip_flags':[ln.get_clip_on() for ln in markers],'svg_editable_text':'<text' in ss});plt.close(fig)

# Fig08: two distinct current histories weight an identical changing resistance differently.
fig,ax=new();t=np.linspace(.002,.003,1001);tm=np.linspace(.00205,.00295,10)
for n,color,marker in [(3,COL[0],'o'),(4,COL[1],'s')]:
 d=denom(n);beta=200.;alpha=1000.;exact=10000*np.exp(beta*t)*(d(alpha*1e-5)/d((alpha+beta)*1e-5)-d(0)/d(beta*1e-5))
 lo=curves(f'N{n}_matched_exp_a0');hi=curves(f'N{n}_matched_exp_a1000');native=np.interp(tm,hi['time'],hi['ratio'])-np.interp(tm,lo['time'],lo['ratio'])
 ax.plot(t*1e3,exact,color=color,label=f'N = {n}')
 ax.plot(tm*1e3,native,ls='none',marker=marker,ms=2.8,mfc='white',mec=color,mew=.6,clip_on=False)
 at25=10000*np.exp(.5)*(d(.01)/d(.012)-d(0)/d(.002));METRICS[f'N{n}_current_history_difference_2p5ms_ohm']=float(at25);METRICS[f'N{n}_D_coefficients_ascending']=d.coef.tolist();METRICS[f'N{n}_markers_max_abs_native_vs_analytic_ohm']=float(np.max(abs(native-np.interp(tm,t,exact))))
ax.set(xlim=(2,3),ylim=(0,15),xlabel='Time (ms)',ylabel='Current-history ratio difference (Ω)');ax.legend(loc='upper left',ncol=2);save(fig,'Fig_08_dynamic_weighting')

# Fig09: exact sinusoidal steady-state phasors and first-moment truncation.
z=curves('N4_mismatch_sine');t=np.linspace(.02,.04,2001);w=2*np.pi*100;dp=denom(4);dn=denom(4,1.1)
pout=1e5*(1/dp(0)+.2*np.imag(np.exp(1j*w*t)/dp(1j*w*1e-5)))
nout=1e4*(1/dn(0)+.2*np.imag(np.exp(1j*w*t)/dn(1j*w*1e-5)))
exact=1e4*pout/nout-1e5;dt=(dp.coef[1]/dp(0)-dn.coef[1]/dn(0))*1e-5
first=-1e5*dt*.2*w*np.cos(w*t)/(1+.2*np.sin(w*t));tm=np.linspace(.0201,.0399,35);native=np.interp(tm,z['time'],z['ratio'])-1e5
METRICS['N4_delta_tau_P_minus_N_s']=float(dt);METRICS['N4_first_order_relative_RMS']=float(np.sqrt(np.mean((first-exact)**2))/np.sqrt(np.mean(exact**2)))
tz=z['time'];pp=1e5*(1/dp(0)+.2*np.imag(np.exp(1j*w*tz)/dp(1j*w*1e-5)));nn=1e4*(1/dn(0)+.2*np.imag(np.exp(1j*w*tz)/dn(1j*w*1e-5)));ez=1e4*pp/nn-1e5;fz=-1e5*dt*.2*w*np.cos(w*tz)/(1+.2*np.sin(w*tz))
METRICS['N4_exact_phasor_vs_archived_exact_max_ohm']=float(np.max(abs(ez-(z['exact']-1e5))))
METRICS['N4_exact_phasor_vs_native_max_ohm']=float(np.max(abs(ez-(z['ratio']-1e5))))
METRICS['N4_first_order_relative_RMS_at_native_times']=float(np.sqrt(np.mean((fz-ez)**2))/np.sqrt(np.mean(ez**2)))
assert METRICS['N4_exact_phasor_vs_archived_exact_max_ohm']<1e-7
fig,ax=new();ax.plot(t*1e3,exact,color=COL[0],label='Exact');ax.plot(t*1e3,first,color=COL[1],label='Moment');ax.plot(tm*1e3,native,ls='none',marker='o',ms=2.6,mfc='white',mec=COL[2],mew=.6,clip_on=False,label='LTspice');ax.set(xlim=(20,40),ylim=(-42,55),xlabel='Time (ms)',ylabel='Resistance-ratio error (Ω)');ax.legend(loc='upper center',ncol=3);save(fig,'Fig_09_dynamic_slew')

# Fig10: streaming only selected columns; explicit native Offset is applied.
p=DYN/'cases/T2_cm_pulse/case.raw';sha(p);sha(p.with_suffix('.net'));sha(p.with_suffix('.log'))
def stream_pulse(path):
 meta={};rows=[]
 with path.open(errors='replace') as f:
  for line in f:
   ss=line.strip()
   if ss=='Variables:':break
   if ':' in ss:k,v=ss.split(':',1);meta[k]=v.strip()
  nv=int(meta['No. Variables']);n=int(meta['No. Points']);names=[next(f).split()[1].lower() for _ in range(nv)];assert next(f).strip()=='Values:';offset=float(meta.get('Offset',0));ip=names.index('v(outp)');it=names.index('v(outt)');itme=names.index('time')
  for k in range(n):
   vals={}
   for j in range(nv):
    ss=next(f)
    if j in [itme,ip,it]:vals[j]=float(ss.split()[-1])
   tt=vals[itme]+offset-.0010005
   if 0<=tt<=150e-6:rows.append([tt,vals[ip]-vals[it]])
  assert not f.read(1)
 return np.asarray(rows),meta
native,meta=stream_pulse(p);poly=Poly([1.4,3.2,1])*Poly([1.4,3.3,1]);poles=poly.roots();res=.1/poly.deriv()(poles);TR=10e-9;T=1e-5

def finite_ramp(tt):
 tt=np.asarray(tt);theta=np.maximum(tt,0)/T;out=np.zeros_like(tt)
 for pole,a in zip(poles,res):
  early=(T/TR)*a/pole*np.expm1(pole*theta)
  late=(T/TR)*a/pole*np.exp(pole*theta)*(-np.expm1(-pole*TR/T))
  out+=np.where(tt<TR,early,late)
 return out

t=np.linspace(0,150e-6,1801);exact=finite_ramp(t);tm=np.linspace(.1e-6,149.9e-6,31);vals=np.interp(tm,native[:,0],native[:,1]);fig,ax=new();ax.plot(t*1e6,exact*1e3,color=COL[0],label='Finite-ramp model');ax.plot(tm*1e6,vals*1e3,ls='none',marker='o',ms=2.7,mfc='white',mec=COL[1],mew=.6,clip_on=False,label='LTspice');ax.set(xlim=(0,150),ylim=(-.3,11.5),xlabel='Time after edge start (μs)',ylabel=r'$v_{oP}-v_{oT}$ (mV)');ax.legend(loc='upper right',fontsize=7.3);save(fig,'Fig_10_dynamic_pulse')
k=np.argmax(native[:,1]);METRICS['T2_native_peak_mV']=float(native[k,1]*1e3);METRICS['T2_native_peak_elapsed_us']=float(native[k,0]*1e6);METRICS['T2_selected_native_points']=len(native);METRICS['T2_raw_offset_s']=float(meta.get('Offset',0));METRICS['T2_finite_ramp_native_max_abs_residual_V']=float(np.max(abs(native[:,1]-finite_ramp(native[:,0]))));METRICS['T2_poles_normalized']=poles.tolist();METRICS['T2_step_residues']=res.tolist()
assert METRICS['T2_native_peak_mV']>9 and METRICS['T2_native_peak_mV']<9.3
(OUT/'provenance_dynamic.json').write_text(json.dumps({'verification_root':str(V),'source_sha256':SHA,'method':'Independent analytic determinant/phasor/finite-ramp pole evaluation, immutable archived curves and streamed native ASCII pulse output; no simulation run.','metrics':METRICS,'qa':QA},indent=2)+'\n')
print(json.dumps(METRICS,indent=2))
