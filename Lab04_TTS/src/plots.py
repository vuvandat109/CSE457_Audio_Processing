import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
from src.common import ROOT,SR

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,
                     'axes.spines.right':False,'figure.dpi':120})

def finish(fig,name):
    fig.tight_layout();fig.savefig(ROOT/'figures'/name,dpi=150,bbox_inches='tight');plt.close(fig)

def spectrogram(ax,x,title,bounds=()):
    f,t,z=signal.stft(x,SR,nperseg=400,noverlap=320,nfft=512)
    db=20*np.log10(np.maximum(np.abs(z),1e-7));im=ax.pcolormesh(t,f,db,shading='auto',cmap='magma',vmin=-80,vmax=-15)
    ax.set(ylim=(0,6000),xlabel='Thời gian (s)',ylabel='Tần số (Hz)',title=title)
    for b in bounds:ax.axvline(b,c='cyan',lw=.6,alpha=.8)
    return im

def stats(metadata):
    fig,axs=plt.subplots(1,2,figsize=(10,3))
    for voice,color in [('male','#2269a6'),('female','#b14a78')]:
        rows=[r for r in metadata if r['speaker']==voice]
        axs[0].hist([float(r['duration_s']) for r in rows],bins=12,alpha=.6,label=voice,color=color)
        axs[1].hist([float(r['rms']) for r in rows],bins=np.linspace(0,.1,21),alpha=.6,label=voice,color=color)
    axs[0].set(xlabel='Thời lượng unit (s)',ylabel='Số file',title='64 unit / 16 nhãn / 2 giọng')
    axs[1].set(xlabel='RMS',ylabel='Số file',title='Mức biên độ sau chuẩn hóa',xlim=(0,.1))
    for ax in axs:ax.legend()
    finish(fig,'01_inventory_stats.png')

def boundaries(raw,best,rb,bb):
    fig,axs=plt.subplots(2,2,figsize=(11,6))
    for row,(x,bounds,name) in enumerate([(raw,rb,'Ghép thẳng'),(best,bb,'DP + cross-fade 15 ms')]):
        axs[row,0].plot(np.arange(len(x))/SR,x,lw=.5)
        for t in bounds:axs[row,0].axvline(t,c='red',alpha=.5,lw=.7)
        axs[row,0].set(title=name,xlabel='Thời gian (s)',ylabel='Biên độ')
        spectrogram(axs[row,1],x,name,bounds)
    finish(fig,'02_waveform_spectrogram.png')
    fig,axs=plt.subplots(2,2,figsize=(10,5))
    for col,idx in enumerate([0,1]):
        for row,(x,bounds,name) in enumerate([(raw,rb,'Raw'),(best,bb,'Best')]):
            p=round(bounds[idx]*SR);half=640;seg=x[max(0,p-half):p+half]
            axs[row,col].plot((np.arange(len(seg))-min(p,half))/SR*1000,seg,lw=.7)
            axs[row,col].axvline(0,c='red',ls='--');axs[row,col].set(title=f'{name}: biên {idx+1}',xlabel='ms quanh biên',ylabel='Biên độ')
    finish(fig,'03_two_boundary_details.png')

def cost_plot(rows,xfade):
    fig,axs=plt.subplots(1,2,figsize=(11,3.4))
    rr=[r for r in rows if r['sentence_id']==1]
    names=[f"{r['voice']}\n{r['method']}" for r in rr]
    axs[0].bar(names,[r['total_cost'] for r in rr],color=['#aaa','#2269a6','#aaa','#b14a78'])
    axs[0].set(title='Target + 0.02 × join cost',ylabel='Tổng chi phí (câu 1)')
    for v in ('male','female'):
        rs=[r for r in xfade if r['voice']==v and r['sentence_id']==1]
        axs[1].plot([r['crossfade_ms'] for r in rs],[r['spectral_mismatch'] for r in rs],'o-',label=v)
    axs[1].set(title='Chỉ số phổ ở tâm biên sau ghép',xlabel='Cross-fade (ms)',ylabel='MSE log-spectrum (dB²)')
    axs[1].legend();finish(fig,'04_selection_crossfade.png')

def hmm_plot(track):
    fig,axs=plt.subplots(3,1,figsize=(11,6),sharex=True)
    t=track['time_s']; f=track['f0'].copy();f[f==0]=np.nan
    axs[0].plot(t,f,c='#2269a6');axs[0].set(ylabel='F0 (Hz)',title='HMM Gaussian 5 state/unit + WORLD (female, câu 1)')
    axs[1].plot(t,track['static_logspec_1khz'],label='Mean theo state',alpha=.6)
    axs[1].plot(t,track['logspec_1khz'],label='Static + delta generation',lw=1)
    axs[1].set(ylabel='Log power tại 1 kHz');axs[1].legend()
    axs[2].step(t,track['state'],where='post');axs[2].set(xlabel='Thời gian (s)',ylabel='State ID')
    finish(fig,'05_hmm_tracks.png')

def comparison(outputs):
    fig,axs=plt.subplots(3,1,figsize=(10,7))
    for ax,(name,x) in zip(axs,outputs):spectrogram(ax,x,name)
    finish(fig,'06_backend_comparison.png')

def prosody(xs):
    fig,axs=plt.subplots(2,3,figsize=(12,6))
    for ax,(name,x) in zip(axs.flat,xs):spectrogram(ax,x,name)
    finish(fig,'07_prosody.png')

def f0_check(x,start,period,estimate):
    fig,ax=plt.subplots(figsize=(10,2.8));n=min(5*period,len(x)-start)
    ax.plot(np.arange(n)/SR*1000,x[start:start+n]);
    for i in range(6):ax.axvline(i*period/SR*1000,c='red',alpha=.4)
    ax.set(xlabel='Thời gian tương đối (ms)',ylabel='Biên độ',title=f'Kiểm tra chu kỳ: Np={period} mẫu; Fs/Np={SR/period:.2f} Hz; ước lượng F0={estimate:.2f} Hz')
    finish(fig,'08_f0_period_check.png')

def isolated_boundary_spectra(raw,best,rb,bb):
    fig,axs=plt.subplots(2,2,figsize=(10,5))
    for col,idx in enumerate([0,1]):
        for row,(x,bounds,name) in enumerate([(raw,rb,'DP + 0 ms'),(best,bb,'DP + 15 ms')]):
            t=bounds[idx];p=round(t*SR);left=max(0,p-1600);right=min(len(x),p+1600)
            spectrogram(axs[row,col],x[left:right],f'{name}: biên {idx+1}',[(p-left)/SR])
    finish(fig,'09_two_boundary_spectrograms.png')
