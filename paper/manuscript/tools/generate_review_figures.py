#!/usr/bin/env python3
"""Review figures: read-only evidence, editable SVG and bilingual wrappers."""
from pathlib import Path
import argparse,json,hashlib,csv,html
import numpy as np
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator,LogLocator
from matplotlib.transforms import Bbox
from PIL import Image,ImageChops
import cairosvg

base=Path(__file__).resolve().parents[1]; out=base/'figures'
p=argparse.ArgumentParser();p.add_argument('--verification',type=Path,required=True);args=p.parse_args()
root=args.verification
sources=[root/'2026-10-28-pairing-strategies'/n for n in ['histogram_data.json','representative_worst.csv','pairing_mc.py']]+[root/'2026-10-28-terminal-noise'/n for n in ['terminal_sweep.csv','noise_summary.json','noise_budget.py']]
hashes={str(v):hashlib.sha256(v.read_bytes()).hexdigest() for v in sources}
mpl.rcParams.update({'font.family':'serif','font.serif':['Times New Roman'],'mathtext.fontset':'custom','mathtext.rm':'Times New Roman','mathtext.it':'Times New Roman:italic','mathtext.bf':'Times New Roman:bold','mathtext.cal':'Times New Roman','mathtext.fallback':None,'svg.fonttype':'none','pdf.fonttype':42,'font.size':7.3,'axes.labelsize':7.5,'axes.linewidth':.75,'axes.labelpad':1.5,'xtick.labelsize':7.3,'ytick.labelsize':7.3,'xtick.direction':'in','ytick.direction':'in','xtick.major.pad':1.5,'ytick.major.pad':1.5,'legend.fontsize':7.3,'legend.framealpha':1,'legend.edgecolor':'black','legend.fancybox':False,'lines.linewidth':.75})
C=['#000000','#e01b1b','#1f4fd8'];qa=[]
def new(log=False):
 f,a=plt.subplots(figsize=(7.5/2.54,5.625/2.54));f.subplots_adjust(left=.20,right=.97,bottom=.22,top=.96)
 a.tick_params(which='both',top=True,right=True,direction='in',length=2.2,width=.5);a.yaxis.set_minor_locator(AutoMinorLocator(2))
 if log:a.set_xscale('log');a.xaxis.set_minor_locator(LogLocator(base=10,subs=[np.sqrt(10)]))
 else:a.xaxis.set_minor_locator(AutoMinorLocator(2))
 return f,a

def save_group(figs,keys):
 # Shared physical crop keeps panels of each figure exactly equal in size.
 boxes=[]
 for f in figs:
  f.canvas.draw();renderer=f.canvas.get_renderer();boxes.append(f.get_tightbbox(renderer))
  for ax in f.axes:
   legend=ax.get_legend()
   if legend:
    box=legend.get_window_extent(renderer)
    for curve in ax.lines:
     pts=ax.transData.transform(curve.get_xydata());hits=(pts[:,0]>box.x0)&(pts[:,0]<box.x1)&(pts[:,1]>box.y0)&(pts[:,1]<box.y1)
     assert not hits.any(), 'Legend hides a plotted curve'
 box=Bbox.union(boxes)
 # Match PDF/SVG crop for both panels; trim a common raster border only.
 ims=[]
 for f,key in zip(figs,keys):
  for ext in ['svg','pdf','png']:
   f.savefig(out/(key+'.'+ext),bbox_inches=box,pad_inches=0,facecolor='white',dpi=600)
   if ext=='svg':
    path=out/(key+'.svg');path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines())+'\n')
  ims.append(Image.open(out/(key+'.png')).convert('RGB'))
 bounds=[ImageChops.difference(im,Image.new('RGB',im.size,'white')).getbbox() for im in ims]
 crop=(min(b[0] for b in bounds),min(b[1] for b in bounds),max(b[2] for b in bounds),max(b[3] for b in bounds))
 for im,f,key in zip(ims,figs,keys):
  im=im.crop(crop);im.save(out/(key+'.png'),dpi=(600,600));bb=ImageChops.difference(im,Image.new('RGB',im.size,'white')).getbbox();qa.append({'figure':key,'pixels':list(im.size),'ink_border':[bb[0],bb[1],im.width-bb[2],im.height-bb[3]],'canvas_cm':[7.5,5.625]});plt.close(f)
 assert len({tuple(v.size) for v in ims})==1

hist=json.loads(sources[0].read_text())['groups']
f1,a=new();groups=['naive','per-stage-tau','uniform-ratio'];vals=[hist[k+'|raw']['values_sorted_db'] for k in groups]
v=a.violinplot(vals,positions=[1,2,3],widths=.65,showextrema=False)
for body,c in zip(v['bodies'],C):body.set_facecolor(c);body.set_edgecolor(c);body.set_alpha(.17)
for j,(data,c) in enumerate(zip(vals,C),1):
 lo,med,hi=np.percentile(data,[5,50,95]);a.plot([j,j],[lo,hi],color=c,lw=1.2);a.plot(j,med,'o',mfc='white',mec=c,ms=3.4,mew=.6)
a.set(xticks=[1,2,3],xticklabels=['Independent','Exact stage RC','Same-direction'],ylim=(20,105),xlim=(.4,3.6),ylabel='Minimum raw CMRR (dB)');a.tick_params(axis='x',labelsize=6.5)
f2,a=new(True);rows=list(csv.DictReader(sources[1].open()))
for key,c in zip(groups,C):
 rr=[r for r in rows if r['strategy']==key and r['convention']=='raw'];a.plot([float(r['freq_Hz']) for r in rr],[float(r['CMRR_dB']) for r in rr],color=c,label={'naive':'Independent','per-stage-tau':'Exact stage RC','uniform-ratio':'Same-direction'}[key])
a.set(xlim=(10,1e7),ylim=(20,110),xlabel='Frequency (Hz)',ylabel='Raw CMRR (dB)');a.legend(loc='upper left')
save_group([f1,f2],['Fig_13a_pairing_distribution','Fig_13b_pairing_curves'])

rows=list(csv.DictReader(sources[3].open()));gs=sorted(set(float(r['g']) for r in rows));f1,a1=new(True);f2,a2=new(True)
# Three fixed colors and distinct line styles identify the finite-load sweep.
styles=['-', '--', ':','-.','-', '--', ':','-.']
for j,g in enumerate(gs[1:]):
 rr=[r for r in rows if float(r['g'])==g];ff=np.array([float(r['freq_Hz']) for r in rr]);cm=np.array([float(r['CMRR_dB']) for r in rr]);dd=np.array([float(r['G_DD_mag']) for r in rr]);label='1e6' if g==1e6 else f'{g:g}'
 a1.plot(ff,cm,color=C[j%3],ls=styles[j],label=label);a2.plot(ff,20*np.log10(dd),color=C[j%3],ls=styles[j],label=label)
a1.set(xlim=(10,1e7),ylim=(0,145),xlabel='Frequency (Hz)',ylabel='Raw CMRR (dB)');a1.legend(loc='upper left',ncol=2,title='g',fontsize=6.5,title_fontsize=7.3)
a2.set(xlim=(10,1e7),ylim=(-205,2),xlabel='Frequency (Hz)',ylabel='Differential signal gain (dB)');a2.legend(loc='center left',bbox_to_anchor=(.01,.63),ncol=2,title='g',fontsize=6.0,title_fontsize=6.5)
save_group([f1,f2],['Fig_14a_terminal_cmrr','Fig_14b_terminal_gain'])

# Diagrams use repository schematic styling and editable text. Separate EN/ZH
# assets avoid shrinking bilingual labels below the readable size.
def diagram(key,zh):
 parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="620" viewBox="0 0 1400 620">','<defs><marker id="arrow" markerUnits="userSpaceOnUse" markerWidth="10" markerHeight="9" refX="9" refY="4.5" orient="auto"><path d="M0,0 L9,4.5 L0,9 Z" fill="#374151"/></marker></defs>','<rect width="1400" height="620" fill="white"/>']
 def text(x,y,t,size=22,color='#111827',anchor='middle'):
  parts.append(f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="Noto Sans CJK SC" font-size="{size}" fill="{color}">{html.escape(t)}</text>')
 def rect(x,y,w,h,fill='#f1f5f9',stroke='#374151',dash=''):
  parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="2"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>')
 def line(x1,y1,x2,y2):parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#374151" stroke-width="2" marker-end="url(#arrow)"/>')
 if key==11:
  text(700,50,'比值测量的信号路径与分析平面' if zh else 'Signal paths and analysis planes for ratio measurement',28)
  labels=[('恒流激励','Current excitation'),('样品 / 参考','Sample / reference'),('独立缓冲','Independent buffers'),('双 RC 梯形','Two RC ladders'),('同步采样','Paired sampling'),('直流校准与比值','DC gain / ratio')]
  xs=[35,265,495,725,955,1185]
  for j,(cn,en) in enumerate(labels):
   rect(xs[j],200,180,110,'#eff6ff' if j==3 else '#f1f5f9');text(xs[j]+90,245,cn if zh else en,17);text(xs[j]+90,280,['I(t)','IR(t), IRs','vP, vN','HP, HN','uP, uN','R_est(t)'][j],21)
   if j<5:line(xs[j]+180,255,xs[j+1]-5,255)
  rect(705,125,220,235,'none','#2563eb','8 6');text(815,105,'本文网络分析段' if zh else 'Network analysis plane',21,'#2563eb')
  text(700,420,'缓冲器位于梯形之前；两通道独立；传感电阻改变源幅值。' if zh else 'Buffers precede independent ladders; sensor resistance changes the source amplitude.',21)
  text(700,465,'负载与探头在输出平面计入；跨接电容另用耦合节点模型。' if zh else 'Loads and probes enter at the output plane; a bridge requires a coupled-node model.',21)
  text(700,555,'分别评估差分输出与校准后的电阻比值。' if zh else 'Evaluate differential output and the calibrated resistance ratio separately.',18,'#2563eb')
 else:
  text(700,50,'从元件差异到两类可观测误差' if zh else 'Component differences and two distinct output observables',28)
  rect(40,220,240,100);text(160,260,'元件与负载差异' if zh else 'Tolerance / loading',17);text(160,295,'ΔA(x), ΔB(x)',22)
  rect(365,220,275,100,'#eff6ff');text(502,260,'两通道响应不同' if zh else 'Unequal channel responses',18);text(502,295,'HP(s), HN(s)',22);line(280,270,360,270)
  rect(760,100,590,150,'#eff6ff');text(1055,140,'差分输出：共模泄漏' if zh else 'Differential output: common-mode leakage',21);text(1055,185,'GDC = HP − HN',23);text(1055,220,'直流增益相等：阶跃 → 衰减脉冲' if zh else 'Equal DC gains: step → decaying pulse',20)
  rect(760,350,590,150,'#f1f5f9');text(1055,390,'校准比值：响应核失配' if zh else 'Calibrated ratio: unequal normalized kernels',21);text(1055,435,'R_est = [gP * (IR)] / [gN * I]',23);text(1055,470,'Δτ 与 Δμ2；分母须非零' if zh else 'Delay / second-moment differences; nonzero denominator',19)
  # Independent connectors do not imply the differential pulse equals ratio error.
  parts.append('<path d="M640,255 H700 V175 H755 M640,285 H700 V425 H755" fill="none" stroke="#374151" stroke-width="2" marker-end="url(#arrow)"/>')
  text(700,570,'两种输出分别计算；共模泄漏脉冲不能直接替代电阻比值误差。' if zh else 'Evaluate each observable separately; a leakage pulse is not the resistance-ratio error.',21,'#2563eb')
 parts.append('</svg>');suffix='zh' if zh else 'en';path=out/f'Fig_{key:02d}_{suffix}.svg';path.write_text('\n'.join(parts));cairosvg.svg2png(url=str(path),write_to=str(path.with_name(path.stem+'@2x.png')),scale=2);cairosvg.svg2pdf(url=str(path),write_to=str(path.with_suffix('.pdf')))
for n in [11,12]:
 for zh in [False,True]:diagram(n,zh)

captions={11:('Signal flow for the buffered ratio model. The highlighted block is the passive network analyzed by the coefficient equations; loads and probe admittances enter at the network output plane. The sensor changes the upstream source amplitude.','缓冲后比值模型的信号路径。高亮块为系数方程分析的无源网络，负载与探头导纳在其输出平面计入；传感电阻改变上游源幅值。','system-plane'),12:('Two consequences of channel differences. Common-mode leakage concerns a differential output; calibrated resistance concerns the quotient of two filtered signals. Each observable requires a separate excitation and transfer model; * denotes convolution and R_est denotes the calibrated estimate.','通道差异的两类后果。共模泄漏针对差分输出，校准电阻针对两个滤波信号之商；两者各有激励与传递模型，*表示卷积，R_est表示校准估计值。','mismatch-observables'),13:('Synthetic pairing populations at $g=0.1$. Distributions of minimum raw CMRR across 145 frequencies from 10 Hz to 10 MHz (left), and the worst sample from each population (right). Each population has 5000 draws; points and bars show medians and 5th--95th percentiles. The stage-product population imposes exact trimming, whereas same-direction scaling multiplies both R and C by the same factor. The populations have different correlation constraints.','在 $g=0.1$ 下的合成配对总体：10 Hz至10 MHz共145频点中最小原始CMRR的分布（左）及各总体最差样本（右）。各总体5000次抽样，点及竖线为中位数与5至95百分位。逐级乘积总体施加精确调配，同向缩放则将R与C乘以同一因子；各总体的相关约束不同。','pairing-populations'),14:('Termination sweep of the uncoupled P/Q construction ($C_d=0$). Raw CMRR (left) and absolute differential signal gain (right). Eight finite conductances are shown; $g=10^6$ approximates the strong-load limit. At $g=0$, the two branches agree exactly and the mathematical CMRR is unbounded. The plot omits the open-circuit curve. Increased rejection in the stop band accompanies strong signal attenuation.','未跨接电容的P/Q构造（$C_d=0$）的端接扫描：原始CMRR（左）与绝对差模信号增益（右）。图示八个有限电导，其中 $g=10^6$ 近似强负载极限。$g=0$ 时两支路精确相等、数学CMRR无界，因此未画该曲线。阻带中抑制比上升伴随明显信号衰减。','terminal-sweep')}
for n,(en,zh,label) in captions.items():
 for lang,cap in [('en',en),('zh',zh)]:
  cap=cap.replace('R_est',r'$R_{\mathrm{est}}$').replace('* denotes',r'$\ast$ denotes').replace('*表示',r'$\ast$表示')
  if n<13:imgs=f'\\includegraphics[width=\\linewidth]{{figures/Fig_{n:02d}_{lang}.pdf}}'
  else:
   keys=['Fig_13a_pairing_distribution','Fig_13b_pairing_curves'] if n==13 else ['Fig_14a_terminal_cmrr','Fig_14b_terminal_gain']
   imgs='\n'.join('\\includegraphics[width=0.49\\linewidth]{figures/'+key+'.pdf}' for key in keys)
  (out/f'fig{n:02d}-{lang}.tex').write_text('\\begin{figure}[htbp]\n\\centering\n'+imgs+'\n\\caption{'+cap+'}\n\\label{fig:'+label+'}\n\\end{figure}\n')
(out/'review-provenance.json').write_text(json.dumps({'sources_sha256':hashes,'artwork_qa':qa,'scope':'Synthetic populations and ideal-network calculations; no measurements.'},indent=2)+'\n')
print(json.dumps(qa,indent=2))
