from pathlib import Path
import numpy as np
import pandas as pd
import librosa
import soundfile as sf
import matplotlib.pyplot as plt
from scipy.signal import lfilter
from sklearn.metrics import confusion_matrix, accuracy_score

FS=16000
FRAME_MS=25
HOP_MS=10
WIN=int(FS*FRAME_MS/1000)  # 400 samples
HOP=int(FS*HOP_MS/1000)    # 160 samples
NFFT=512
N_MELS=24
N_MFCC=13
ALPHA=0.97
LABELS=['khong','mot','hai','ba','bon']
VN={'khong':'không','mot':'một','hai':'hai','ba':'ba','bon':'bốn'}

def load_audio(path):
    y, _ = librosa.load(path, sr=FS, mono=True)
    return y.astype(np.float32)

def normalize_peak(y, peak=0.95):
    m=np.max(np.abs(y)) if len(y) else 0
    return y if m<1e-12 else (y/m*peak).astype(np.float32)

def frame_signal(y):
    if len(y)<WIN:
        y=np.pad(y,(0,WIN-len(y)))
    n=1+(len(y)-WIN)//HOP
    idx=np.arange(WIN)[None,:]+HOP*np.arange(n)[:,None]
    return y[idx]

def short_time_features(y):
    frames=frame_signal(y)
    w=np.hamming(WIN)[None,:]
    fw=frames*w
    energy=np.sum(fw**2,axis=1)
    magnitude=np.sum(np.abs(fw),axis=1)
    rms=np.sqrt(np.mean(fw**2,axis=1)+1e-12)
    signs=np.where(frames>=0,1,-1)
    zcr=np.sum(signs[:,1:] != signs[:,:-1],axis=1)/WIN
    loge=10*np.log10(energy+1e-12)
    times=(np.arange(len(energy))*HOP+WIN/2)/FS
    return times,energy,magnitude,rms,zcr,loge

def endpoint_detect(y, margin_ms=50, db_above_noise=10.0, use_zcr=True):
    times,energy,mag,rms,zcr,loge=short_time_features(y)
    # Estimate background from beginning/end frames (known to contain silence in this lab dataset)
    k=max(2,min(10,len(loge)//5))
    edge=np.r_[loge[:k],loge[-k:]]
    noise_db=float(np.median(edge))
    energy_thr=noise_db+db_above_noise
    active=np.flatnonzero(loge>energy_thr)
    if len(active)==0:
        return y.copy(),(0,len(y)),dict(noise_db=noise_db,energy_threshold_db=energy_thr,zcr_threshold=None)
    start,end=int(active[0]),int(active[-1])
    zthr=None
    if use_zcr:
        # Extend boundaries over nearby high-ZCR low-energy consonantal frames.
        edge_z=np.r_[zcr[:k],zcr[-k:]]
        zthr=float(np.mean(edge_z)+2*np.std(edge_z))
        max_extend=5
        for _ in range(max_extend):
            if start>0 and (zcr[start-1]>zthr or loge[start-1]>noise_db+4): start-=1
            else: break
        for _ in range(max_extend):
            if end+1<len(loge) and (zcr[end+1]>zthr or loge[end+1]>noise_db+4): end+=1
            else: break
    s=max(0,start*HOP-int(margin_ms*FS/1000))
    e=min(len(y),end*HOP+WIN+int(margin_ms*FS/1000))
    return y[s:e],(s,e),dict(noise_db=noise_db,energy_threshold_db=float(energy_thr),zcr_threshold=zthr)

def autocorrelation_pitch(y, fmin=70, fmax=350):
    # Use the highest-RMS frame as a simple voiced-frame example.
    frames=frame_signal(y)
    rms=np.sqrt(np.mean(frames**2,axis=1)+1e-12)
    x=frames[int(np.argmax(rms))]*np.hamming(WIN)
    x=x-np.mean(x)
    ac=np.correlate(x,x,mode='full')[WIN-1:]
    minlag=max(1,int(FS/fmax)); maxlag=min(len(ac)-1,int(FS/fmin))
    lag=minlag+int(np.argmax(ac[minlag:maxlag+1]))
    f0=FS/lag if lag>0 else np.nan
    return ac,lag,float(f0)

def mfcc_feature(y, add_delta=False):
    y=lfilter([1.0,-ALPHA],[1.0],y)  # pre-emphasis
    M=librosa.feature.mfcc(y=y,sr=FS,n_mfcc=N_MFCC,n_mels=N_MELS,n_fft=NFFT,
                           win_length=WIN,hop_length=HOP,window='hamming',center=False)
    M=M-np.mean(M,axis=1,keepdims=True)  # CMN, applied consistently
    if add_delta:
        width=min(9, M.shape[1] if M.shape[1]%2 else M.shape[1]-1)
        width=max(3,width)
        D=librosa.feature.delta(M,width=width,mode='nearest')
        M=np.vstack([M,D])
    return M.T.astype(np.float32)  # (T,D)

def local_distance_matrix(X,Y):
    return np.linalg.norm(X[:,None,:]-Y[None,:,:],axis=2)

def dtw_distance(X,Y):
    C=local_distance_matrix(X,Y)
    N,M=C.shape
    D=np.full((N+1,M+1),np.inf,dtype=float); D[0,0]=0.0
    back=np.zeros((N+1,M+1,2),dtype=int)
    for i in range(1,N+1):
        for j in range(1,M+1):
            candidates=((D[i-1,j],i-1,j),(D[i,j-1],i,j-1),(D[i-1,j-1],i-1,j-1))
            best,pi,pj=min(candidates,key=lambda z:z[0])
            D[i,j]=C[i-1,j-1]+best
            back[i,j]=(pi,pj)
    path=[]; i,j=N,M
    while i>0 or j>0:
        path.append((max(i-1,0),max(j-1,0)))
        i,j=back[i,j]
    path.reverse()
    return float(D[N,M]/max(len(path),1)),path,C,D[1:,1:]

def extract(path, trim=True, add_delta=False):
    y=load_audio(path)
    if trim: y,_,_=endpoint_detect(y)
    return mfcc_feature(y,add_delta=add_delta)

def build_templates(root, trim=True, add_delta=False, n_train=3):
    root=Path(root); templates={lab:[] for lab in LABELS}
    for lab in LABELS:
        files=sorted((root/lab).glob('*.wav'))[:n_train]
        for f in files: templates[lab].append(extract(f,trim=trim,add_delta=add_delta))
    return templates

def recognize(path,templates,trim=True,add_delta=False):
    X=extract(path,trim=trim,add_delta=add_delta)
    scores={lab:min(dtw_distance(X,R)[0] for R in refs) for lab,refs in templates.items()}
    ordered=dict(sorted(scores.items(),key=lambda kv:kv[1]))
    return next(iter(ordered)),ordered

def evaluate(dataset_root, trim=True, add_delta=False, n_train=3):
    root=Path(dataset_root); templates=build_templates(root,trim,add_delta,n_train)
    rows=[]; yt=[]; yp=[]
    for lab in LABELS:
        for f in sorted((root/lab).glob('*.wav'))[n_train:]:
            pred,scores=recognize(f,templates,trim,add_delta)
            items=list(scores.items())
            rows.append(dict(file=f.name,true_label=lab,pred_label=pred,
                top1_label=items[0][0],top1_score=items[0][1],
                top2_label=items[1][0],top2_score=items[1][1],
                top3_label=items[2][0],top3_score=items[2][1]))
            yt.append(lab); yp.append(pred)
    return float(accuracy_score(yt,yp)),confusion_matrix(yt,yp,labels=LABELS),pd.DataFrame(rows),templates
