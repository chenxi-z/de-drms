#!/usr/bin/env python3
"""Reproducible analytical/native-LTspice artwork; adapted from howtoSCI tpl_curve_matrix.
Run with system python3. Native simulation evidence is read-only and located via --evidence.
"""
from pathlib import Path
import argparse, json, hashlib, math, ast, re
import numpy as np
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
from matplotlib.ticker import AutoMinorLocator, LogLocator
from PIL import Image, ImageChops

BASE=Path(__file__).resolve().parents[1]; OUT=BASE/'figures'; OUT.mkdir(exist_ok=True)
p=argparse.ArgumentParser();p.add_argument('--evidence',type=Path);args=p.parse_args()
ROOT=args.evidence or Path(json.loads(Path('/tmp/paper-qoder-ltspice-active.json').read_text())['root'])
A=ROOT/'A_N1_termination'; cases=json.loads((A/'results/spice_results.json').read_text())['cases']
mpl.rcParams.update({'font.family':'serif','font.serif':['Times New Roman'],'mathtext.fontset':'custom','mathtext.rm':'Times New Roman','mathtext.it':'Times New Roman:italic','mathtext.bf':'Times New Roman:bold','mathtext.cal':'Times New Roman','mathtext.fallback':None,'svg.fonttype':'none','pdf.fonttype':42,'font.size':7.3,'axes.labelsize':7.5,'axes.linewidth':.75,'axes.labelpad':1.5,'xtick.labelsize':7.3,'ytick.labelsize':7.3,'xtick.direction':'in','ytick.direction':'in','xtick.major.size':2.2,'ytick.major.size':2.2,'xtick.major.width':.5,'ytick.major.width':.5,'xtick.major.pad':1.5,'ytick.major.pad':1.5,'legend.fontsize':7.3,'legend.framealpha':1,'legend.edgecolor':'black','legend.fancybox':False,'lines.linewidth':.75,'savefig.dpi':600})
COL=['#000000','#e01b1b','#1f4fd8']; SHA={}; QA=[]

def raw(case):
 path=A/cases[case]['rec']['raw']; SHA[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
 assert SHA[str(path)]==cases[case]['rec']['raw_sha256']
 lines=path.read_text().splitlines();nv=int(next(l.split(':')[1] for l in lines if l.startswith('No. Variables:')));np_=int(next(l.split(':')[1] for l in lines if l.startswith('No. Points:')));vi=lines.index('Variables:');names=[lines[vi+i+1].split()[1] for i in range(nv)];vals=[s for s in lines[lines.index('Values:')+1:] if s.strip()];data={s:[] for s in names}
 for k in range(np_):
  for j,name in enumerate(names):data[name].append(complex(*map(float,vals[k*nv+j].split()[-1].split(','))))
 return {k.lower():np.asarray(v) for k,v in data.items()}

def new(log=True):
 fig,ax=plt.subplots(figsize=(7.5/2.54,5.625/2.54));fig.subplots_adjust(left=.19,right=.97,bottom=.19,top=.97)
 ax.tick_params(which='both',top=True,right=True,direction='in');ax.yaxis.set_minor_locator(AutoMinorLocator(2))
 if log:ax.set_xscale('log');ax.xaxis.set_minor_locator(LogLocator(base=10,subs=[np.sqrt(10)]))
 else:ax.xaxis.set_minor_locator(AutoMinorLocator(2))
 return fig,ax

def save(fig,key):
 fig.canvas.draw();renderer=fig.canvas.get_renderer();texts=[t for ax in fig.axes for t in ax.texts if t.get_visible() and t.get_text()]; collisions=[]
 for i,t in enumerate(texts):
  for u in texts[i+1:]:
   if t.get_window_extent(renderer).overlaps(u.get_window_extent(renderer)):collisions.append([t.get_text(),u.get_text()])
 assert not collisions,(key,collisions)
 legend_curve_hits=0
 for ax in fig.axes:
  legend=ax.get_legend()
  if legend is not None:
   box=legend.get_window_extent(renderer)
   for curve in ax.lines:
    pts=ax.transData.transform(curve.get_xydata())
    legend_curve_hits+=int(np.sum((pts[:,0]>box.x0)&(pts[:,0]<box.x1)&(pts[:,1]>box.y0)&(pts[:,1]<box.y1)))
 assert legend_curve_hits==0,(key,'legend overlaps curve',legend_curve_hits)
 for ext in ['svg','pdf','png']:fig.savefig(OUT/(key+'.'+ext),bbox_inches='tight',pad_inches=0,facecolor='white',dpi=600)
 im=Image.open(OUT/(key+'.png')).convert('RGB');bb=ImageChops.difference(im,Image.new('RGB',im.size,'white')).getbbox();assert bb
 im.crop(bb).save(OUT/(key+'.png'),dpi=(600,600));im=Image.open(OUT/(key+'.png')).convert('RGB');bb2=ImageChops.difference(im,Image.new('RGB',im.size,'white')).getbbox();border=(bb2[0],bb2[1],im.width-bb2[2],im.height-bb2[3]);assert border==(0,0,0,0)
 svgtext=(OUT/(key+'.svg')).read_text()
 svg_sizes=[float(v) for v in re.findall(r'font-size:\s*([0-9.]+)px',svgtext)]
 svg_sizes += [float(v) for v in re.findall(r'font:\s*([0-9.]+)px',svgtext)]
 assert svg_sizes and min(svg_sizes)>=5,(key,'SVG glyph below 5pt floor',min(svg_sizes))
 marker_artists=[curve for ax in fig.axes for curve in ax.lines if curve.get_marker() not in [None,'None','none','']]
 marker_clipflags=[curve.get_clip_on() for curve in marker_artists]
 if key in ['Fig_03_termination_transfer','Fig_05_load_specific_match','Fig_06_bridge_gains','Fig_07_bridge_cmrr']:assert not any(marker_clipflags),(key,'marker artist clipped')
 QA.append({'figure':key,'canvas_cm':[7.5,5.625],'png_pixels':list(im.size),'border_pixels':border,'annotation_text_collisions':collisions,'legend_curve_samples_intersected':legend_curve_hits,'actual_svg_min_glyph_pt':min(svg_sizes),'marker_artist_clip_flags':marker_clipflags,'svg_editable_text':'<text' in (OUT/(key+'.svg')).read_text()});plt.close(fig)

# All components in SI units; normalized coefficients are explicit manuscript quantities.
f=np.logspace(1,7,901);x=2j*np.pi*f*1e-5
coeff={'P':(3,1,2,1),'Q':(3,1,5,2),'T':(2.9,1,2,2)}
def H(key,g=0,xx=x):
 a,b,c,d=coeff[key];return 1/(1+g*c+(a+g*d)*xx+b*xx**2)
def Z(key,g=0):
 a,b,c,d=coeff[key];z=1e3*(c+d*x)/(1+a*x+b*x*x);return z/(1+g*z/1e3)
def db(v):return 20*np.log10(abs(v))

# 1. Both grounded branches and the actual optional output bridge.
fig,ax=new(False);ax.set_axis_off();ax.set_xlim(-.4,8);ax.set_ylim(-.7,6.2)
def line(xs,ys,color='black',ls='-'):ax.plot(xs,ys,color=color,lw=.75,ls=ls)
def res(x1,x2,y,label):
 mid=(x1+x2)/2;line([x1,mid-.38],[y,y]);ax.add_patch(Rectangle((mid-.38,y-.14),.76,.28,fill=False,lw=.75));line([mid+.38,x2],[y,y]);ax.text(mid,y+.25,label,ha='center',va='bottom')
def ground(x,y):
 line([x,x],[y,y-.18]);line([x-.18,x+.18],[y-.18,y-.18]);line([x-.12,x+.12],[y-.26,y-.26]);line([x-.055,x+.055],[y-.34,y-.34])
def cap(x,y,label,side=1):
 line([x,x],[y,y-.63]);line([x-.2,x+.2],[y-.63,y-.63]);line([x-.2,x+.2],[y-.75,y-.75]);line([x,x],[y-.75,y-1.15]);ground(x,y-1.15);ax.text(x+side*.3,y-.73,label,ha='left' if side>0 else 'right',va='center')
for y,tag in [(5,'P'),(1.9,'N')]:
 ax.text(-.3,y+.08,'$v_{'+tag+'}$',ha='left',va='bottom');line([0,.55],[y,y]);res(.55,2.7,y,'$R_{1'+tag+'}$');res(2.7,5.0,y,'$R_{2'+tag+'}$');line([5,7.2],[y,y]);cap(2.7,y,'$C_{1'+tag+'}$');cap(5.0,y,'$C_{2'+tag+'}$',-1)
 for xx in [2.7,5,6.5]:ax.add_patch(Circle((xx,y),.045,color='black'))
 line([6.5,6.5],[y,y-.4]);ax.add_patch(Rectangle((6.36,y-.98),.28,.58,fill=False,lw=.75));line([6.5,6.5],[y-.98,y-1.15]);ground(6.5,y-1.15);ax.text(6.78,y-.65,'$R_{L'+tag+'}$',ha='left',va='center');ax.text(5.3,y+.22,'$v_{o'+tag+'}$',ha='left',va='bottom')
# Bridge between output nodes, routed outside grounded shunts.
line([7.2,7.65,7.65],[5,5,3.58],COL[2],':');line([7.45,7.85],[3.58,3.58],COL[2]);line([7.45,7.85],[3.43,3.43],COL[2]);line([7.65,7.65,7.2],[3.43,1.9,1.9],COL[2],':');ax.text(7.35,3.05,'$C_d$',ha='right',color=COL[2]);save(fig,'Fig_01_circuit')

# 2. Positive components occupy the strict wedge between two rays.
fig,ax=new(False);dd=np.linspace(.001,3.4,1000);disc=9*dd**2-4*dd**2;cl=(3*dd-np.sqrt(disc))/2;ch=(3*dd+np.sqrt(disc))/2
ax.fill_between(dd,cl,ch,color='#dfe8f8');ax.plot(dd,cl,color=COL[0],label='c = (3 − √5)d / 2');ax.plot(dd,ch,color=COL[1],label='c = (3 + √5)d / 2');ax.plot(1,2,'s',color=COL[0],ms=3,mfc='white');ax.plot(2,5,'o',color=COL[1],ms=3,mfc='white');ax.annotate('P',(1,2),xytext=(5,0),textcoords='offset points',fontsize=7.3);ax.annotate('Q',(2,5),xytext=(5,0),textcoords='offset points',fontsize=7.3);ax.set(xlim=(0,3.4),ylim=(0,9),xlabel='$d$ (normalized)',ylabel='$c$ (normalized)');ax.tick_params(which='both',top=True,right=True,direction='in');ax.xaxis.set_minor_locator(AutoMinorLocator(2));ax.yaxis.set_minor_locator(AutoMinorLocator(2));ax.legend(loc='upper left',fontsize=7.3);save(fig,'Fig_02_positive_region')

# 3. Identical open transfer is separated by a specified resistive load.
fig,ax=new();styles=[('P',0,'P = Q, open',COL[0]),('P',.1,'P, 10 kΩ',COL[1]),('Q',.1,'Q, 10 kΩ',COL[2])]
errors={}
for key,g,label,color in styles:
 ax.plot(f,db(H(key,g)),color=color,label=label)
 case='a_'+key.lower()+('_oc' if g==0 else '_10k');ds=raw(case);ff=ds['frequency'].real;vv=ds['v(out)'];xx=2j*np.pi*ff*1e-5;errors[case]=float(max(abs(vv-H(key,g,xx))));sel=np.arange(0,len(ff),12);ax.plot(ff[sel],db(vv[sel]),ls='none',marker='o',ms=2.6,mfc='white',mec=color,mew=.5,clip_on=False)
ax.set(xlim=(10,1e7),ylim=(-115,5),xlabel='Frequency (Hz)',ylabel='Voltage gain (dB)');ax.legend(loc='lower left');save(fig,'Fig_03_termination_transfer')

# 4. Equal voltage transfer retains different driving-point impedances.
fig,ax=new()
for key,color in zip(['P','Q','T'],COL):ax.plot(f,abs(Z(key))/1e3,color=color,label=key)
ax.set(xlim=(10,1e7),xlabel='Frequency (Hz)',ylabel='$|Z_0|$ (kΩ)',ylim=(0,5.3));ax.legend(loc='upper right',ncol=1);save(fig,'Fig_04_output_impedance')

# 5. A 10k design loses exact equality at 5k: directly plot relative transfer.
fig,ax=new()
for g,color,label in [(.1,COL[0],'10 kΩ'),(.2,COL[1],'5 kΩ')]:
 ax.plot(f,db(H('T',g)/H('P',g)),color=color,label=label)
 dp=raw('a_p_'+('10k' if g==.1 else '5k'));dt=raw('a_t_'+('10k' if g==.1 else '5k'));ff=dp['frequency'].real;sel=np.arange(0,len(ff),12);ax.plot(ff[sel],db(dt['v(out)'][sel]/dp['v(out)'][sel]),ls='none',marker='o',ms=2.6,mfc='white',mec=color,mew=.5,clip_on=False)
ax.set(xlim=(10,1e7),ylim=(-.30,.035),xlabel='Frequency (Hz)',ylabel=r'$20\log_{10}|H_T/H_P|$ (dB)');ax.legend(loc='lower left',ncol=1);save(fig,'Fig_05_load_specific_match')

# 6. Actual output bridge modifies differential and common-to-differential gains.
hp,hn=H('P',.1),H('Q',.1);D=1+2j*np.pi*f*820e-12*(Z('P',.1)+Z('Q',.1));gdd=(hp+hn)/2;gdc=hp-hn
fig,ax=new()
for y,label,color,marker in [(gdd,'DM, 0 pF',COL[0],None),(gdd/D,'DM, 820 pF',COL[0],'o'),(gdc,'CM → DM, 0 pF',COL[1],None),(gdc/D,'CM → DM, 820 pF',COL[1],'o')]:
 ax.plot(f,db(y),color=color,label=label if marker is None else None)
 if marker:ax.plot(f[::100],db(y[::100]),color=color,ls='none',marker=marker,ms=2.5,mfc='white',mew=.5,clip_on=False,label=label)
ax.set(xlim=(10,1e7),ylim=(-200,5),xlabel='Frequency (Hz)',ylabel='Differential-output gain (dB)');ax.legend(loc='lower left',fontsize=7.3);save(fig,'Fig_06_bridge_gains')

# 7. Native bridge traces agree with the same analytical CMRR ratio.
fig,ax=new();ratio=gdd/gdc;ax.plot(f,db(ratio),color=COL[0],label='0 / 820 pF (analytic)');cm=raw('v2_pq_10k_cd_cm');dm=raw('v2_pq_10k_cd_dm');ff=cm['frequency'].real;native=(dm['v(op)']-dm['v(on)'])/(cm['v(op)']-cm['v(on)']);sel=np.arange(0,len(ff),8);ax.plot(ff[sel],db(native[sel]),ls='none',marker='o',ms=2.8,mfc='white',mec=COL[1],mew=.6,label='820 pF (LTspice)',clip_on=False);ax.set(xlim=(10,1e7),ylim=(0,80),xlabel='Frequency (Hz)',ylabel='CMRR (dB)');ax.legend(loc='upper left',fontsize=7.3);save(fig,'Fig_07_bridge_cmrr')

(OUT/'provenance.json').write_text(json.dumps({'evidence_root':str(ROOT),'native_raw_sha256':SHA,'analytical_vs_native_max_complex_error':errors,'qa':QA,'template':'howtoSCI/templates/tpl_curve_matrix.py (executed baseline in build/figure-qa; single-panel adaptation here)','notes':['All traces are analytical models or existing LTspice evidence, not measurements.','The region uses a=3,b=1; strict boundaries are excluded.','One figure environment per independently cropped panel; no mixed-size panel group.']},indent=2))
print(json.dumps({'figures':len(QA),'max_native_error':max(errors.values()),'borders':[q['border_pixels'] for q in QA]}))
