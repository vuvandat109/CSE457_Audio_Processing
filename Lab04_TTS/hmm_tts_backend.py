"""Educational, supervised left-to-right Gaussian HMM + WORLD parameter generation.

Five states per word; equal temporal segmentation is the supplied state alignment.
This is a small word-context-independent demo, NOT a full HTS/context-dependent system.
No waveform selection is used at inference; only Gaussian sufficient statistics.
Static/delta parameter generation uses a first-difference operator and a banded solve.
"""
import json, time
import numpy as np
from scipy.linalg import solve_banded
import pyworld as pw
from src.common import ROOT, SR, WORDS, inventory, normalize_text, standardize

FRAME_MS=10.; NSTATES=5

def analyze(x):
    x=np.ascontiguousarray(x,dtype=np.float64)
    f0,t=pw.dio(x,SR,frame_period=FRAME_MS,f0_floor=65,f0_ceil=500)
    f0=pw.stonemask(x,f0,t,SR)
    sp=pw.cheaptrick(x,f0,t,SR)
    ap=pw.d4c(x,f0,t,SR)
    # Continuous log-F0 is interpolated only for fitting; voiced probability is separate.
    voiced=f0>0; lf=np.full(len(f0),np.log(150.))
    if voiced.any(): lf=np.interp(np.arange(len(f0)),np.flatnonzero(voiced),np.log(f0[voiced]))
    c=np.column_stack([lf,np.log(np.maximum(sp,1e-10)),ap])
    return c,voiced.astype(float),sp.shape[1]

def train(voice):
    inv=inventory(voice); params={}; info={'voice':voice,'states_per_word':NSTATES,
        'frame_ms':FRAME_MS,'alignment':'equal-duration supervised segmentation',
        'estimation':'Gaussian state means/variances; not Baum-Welch',
        'source':'64 synthetic Piper units; two candidates per word per voice'}
    for wi,word in enumerate(WORDS):
        obs=[]; deltas=[]; vuv=[]; durations=[]
        for x in inv[word]:
            c,v,k=analyze(x)
            d=np.vstack([np.zeros((1,c.shape[1])),np.diff(c,axis=0)])
            groups=np.array_split(np.arange(len(c)),NSTATES)
            obs.append([c[g] for g in groups]);deltas.append([d[g] for g in groups])
            vuv.append([v[g] for g in groups]);durations.append([len(g) for g in groups])
        for s in range(NSTATES):
            cs=np.concatenate([o[s] for o in obs]);ds=np.concatenate([d[s] for d in deltas])
            dur=float(np.mean([d[s] for d in durations]));self_prob=max(0.,1.-1./dur)
            prefix=f'w{wi}_s{s}_'
            for key,val in {'mean':cs.mean(0),'var':np.maximum(cs.var(0),1e-3),
                'delta_mean':ds.mean(0),'delta_var':np.maximum(ds.var(0),1e-3),
                'voiced_prob':np.mean(np.concatenate([v[s] for v in vuv])),
                'duration':dur,'self_prob':self_prob}.items(): params[prefix+key]=val
    params['spectral_bins']=k
    directory=ROOT/'data'/'hmm_demo'; directory.mkdir(exist_ok=True)
    np.savez_compressed(directory/f'{voice}_gaussian_hmm.npz',**params)
    (directory/f'{voice}_model_info.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
    return params

def generate_static_delta(mu,var,delta_mu,delta_var,strength=1.):
    """ML trajectory: minimize static + delta Gaussian negative log likelihood.

    D c[t] = c[t]-c[t-1], t>=1; omit first dynamic observation.
    Q=diag(1/var)+D.T diag(strength/delta_var) D is tridiagonal.
    """
    n,d=mu.shape; out=np.empty_like(mu)
    for k in range(d):
        a=1./var[:,k]; b=strength/delta_var[1:,k]
        diag=a.copy();diag[:-1]+=b;diag[1:]+=b
        rhs=a*mu[:,k];rhs[:-1]-=b*delta_mu[1:,k];rhs[1:]+=b*delta_mu[1:,k]
        ab=np.zeros((3,n));ab[1]=diag;ab[0,1:]=-b;ab[2,:-1]=-b
        out[:,k]=solve_banded((1,1),ab,rhs)
    return out

def synthesize_hmm(text,voice='female',duration_scale=1.,f0_scale=1.,smoothing=True):
    start=time.perf_counter();tokens=normalize_text(text)
    path=ROOT/'data'/'hmm_demo'/f'{voice}_gaussian_hmm.npz'
    p=dict(np.load(path)) if path.exists() else train(voice)
    means=[];variances=[];dm=[];dv=[];voiced=[];states=[];labels=[];durations=[]
    for word in tokens:
        wi=WORDS.index(word)
        for s in range(NSTATES):
            pre=f'w{wi}_s{s}_';n=max(1,round(float(p[pre+'duration'])*duration_scale))
            # Expected dwell time 1/(1-a_ss); rounded for deterministic generation.
            durations.append({'label':word,'state':s,'frames':n,
                              'a_self':float(p[pre+'self_prob'])})
            for seq,key in [(means,'mean'),(variances,'var'),(dm,'delta_mean'),(dv,'delta_var')]:
                seq.extend([p[pre+key]]*n)
            voiced.extend([float(p[pre+'voiced_prob'])>=.5]*n)
            states.extend([wi*NSTATES+s]*n);labels.extend([f'{word}:{s}']*n)
    mu=np.array(means);k=int(p['spectral_bins'])
    c=generate_static_delta(mu,np.array(variances),np.array(dm),np.array(dv)) if smoothing else mu
    f0=np.where(voiced,np.exp(np.clip(c[:,0],np.log(65),np.log(500)))*f0_scale,0.)
    sp=np.exp(np.clip(c[:,1:1+k],-23,10));ap=np.clip(c[:,1+k:],.001,1.)
    y=pw.synthesize(np.ascontiguousarray(f0),np.ascontiguousarray(sp),
                    np.ascontiguousarray(ap),SR,frame_period=FRAME_MS)
    y=standardize(y,trim=False)
    tracks={'time_s':np.arange(len(f0))*FRAME_MS/1000,'f0':f0,'state':np.array(states),
            'logspec_1khz':c[:,1+round(1000/(SR/2)*(k-1))],
            'static_logspec_1khz':mu[:,1+round(1000/(SR/2)*(k-1))],
            'durations':durations,'labels':labels,'latency_s':time.perf_counter()-start}
    return y,SR,tracks
