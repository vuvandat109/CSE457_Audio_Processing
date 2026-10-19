"""CSE457 Lab 3 - complete A-H pipeline. All supplied audio is SYNTHETIC.
Run: python Lab03.py ; predict: python Lab03.py --predict dataset/test/mo/mo_01.wav
"""
from pathlib import Path
import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:
    os.environ.setdefault(key,'1')
import argparse, json, csv, time, pickle, warnings, platform, hashlib, io
from collections import Counter
import numpy as np
import librosa, soundfile as sf, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.spatial.distance import cdist
from scipy.special import logsumexp
from sklearn.metrics import accuracy_score, confusion_matrix, ConfusionMatrixDisplay
from hmmlearn.hmm import GaussianHMM
from threadpoolctl import threadpool_limits
from numba import njit
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results';FIG=OUT/'figures';LABELS=['mo','dong','len','xuong','dung']
CACHE={}

def dump(name,value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x)),encoding='utf-8')
def csvout(name,rows):
    if not rows:return
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with (OUT/name).open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
def savefig(name):
    plt.tight_layout()
    buffer=io.BytesIO();plt.savefig(buffer,format='png',dpi=160,bbox_inches='tight');plt.close()
    data=buffer.getvalue();assert len(data)>100
    (FIG/name).write_bytes(data)

def extract(path,dim=39,details=False):
    y,sr=librosa.load(str(path),sr=16000,mono=True)
    if len(y)<400 or not np.all(np.isfinite(y)) or max(abs(y))<1e-5:raise ValueError(f'Empty/invalid audio: {path}')
    y,idx=librosa.effects.trim(y,top_db=30,frame_length=400,hop_length=160)
    y=librosa.effects.preemphasis(y,coef=.97)
    mfcc=librosa.feature.mfcc(y=y,sr=sr,n_mfcc=13,n_fft=512,win_length=400,hop_length=160,window='hamming',n_mels=26,fmin=20,fmax=8000)
    if mfcc.shape[1]<3:raise ValueError('Too few frames for deltas')
    width=min(9,mfcc.shape[1] if mfcc.shape[1]%2 else mfcc.shape[1]-1)
    d1=librosa.feature.delta(mfcc,width=width,order=1);d2=librosa.feature.delta(mfcc,width=width,order=2)
    raw=np.vstack([mfcc,d1,d2])[:dim].T
    F=(raw-raw.mean(0))/(raw.std(0)+1e-8)
    assert F.shape[1]==dim and np.isfinite(F).all()
    return (F,[mfcc,d1,d2],idx) if details else F

def files(split):
    return [(p,label) for label in LABELS for p in sorted((ROOT/'dataset'/split/label).glob('*.wav'))]
def features(p,dim=39):
    key=(str(p),dim)
    if key not in CACHE:CACHE[key]=extract(p,dim)
    return CACHE[key]

def initialize(seqs,n=5,cov='diag',seed=0):
    D=seqs[0].shape[1];chunks=[np.vstack([np.array_split(s,n)[j] for s in seqs]) for j in range(n)]
    kw=dict(n_components=n,covariance_type=cov,n_iter=80,tol=1e-3,min_covar=1e-3,init_params='',params='tmc',random_state=seed,implementation='log')
    # Proper positive definite prior for full covariance; record in report.
    if cov=='full':kw.update(covars_prior=.1*np.eye(D),covars_weight=D+1)
    m=GaussianHMM(**kw);m.startprob_=np.eye(1,n,0).ravel()
    A=np.zeros((n,n))
    for i in range(n-1):A[i,i]=.7;A[i,i+1]=.3
    A[-1,-1]=1;m.transmat_=A
    m.means_=np.array([c.mean(0) for c in chunks])
    m.covars_=np.array([np.maximum(c.var(0),.05) for c in chunks]) if cov=='diag' else np.array([np.cov(c.T)+.05*np.eye(D) for c in chunks])
    return m

def train(n=5,dim=39,cov='diag',limit=None):
    models={};logs=[];t=time.perf_counter()
    for label in LABELS:
        paths=[p for p,l in files('train') if l==label][:limit]
        seqs=[features(p,dim) for p in paths];m=initialize(seqs,n,cov)
        with warnings.catch_warnings(record=True) as ws:
            warnings.simplefilter('always');m.fit(np.vstack(seqs),[len(s) for s in seqs])
        allowed=np.eye(n,dtype=bool)|np.eye(n,k=1,dtype=bool)
        assert np.all(m.transmat_[~allowed]==0),'Topology broken'
        assert np.allclose(m.transmat_.sum(1),1) and np.allclose(m.startprob_,np.eye(1,n,0).ravel())
        h=list(m.monitor_.history);delta=h[-1]-h[-2] if len(h)>1 else None
        status='tolerance' if delta is not None and 0<=delta<m.tol else ('decrease' if delta is not None and delta<0 else 'iteration_limit')
        logs.append(dict(label=label,iterations=len(h),status=status,last_delta=delta,history=h,startprob=m.startprob_.tolist(),transmat=m.transmat_.tolist(),warnings=[str(w.message) for w in ws]))
        models[label]=m
    return models,logs,time.perf_counter()-t

def evaluate(models,split,dim=39):
    rows=[]
    for p,true in files(split):
        F=features(p,dim);scores={l:float(models[l].score(F)) for l in LABELS}
        assert np.isfinite(list(scores.values())).all()
        rank=sorted(scores,key=scores.get,reverse=True)
        rows.append(dict(file=str(p.relative_to(ROOT)),true=true,pred=rank[0],frames=len(F),margin_frame=(scores[rank[0]]-scores[rank[1]])/len(F),**scores))
    return float(np.mean([r['true']==r['pred'] for r in rows])),rows

def cmplot(rows,name,title):
    fig,ax=plt.subplots(figsize=(4.5,4))
    ConfusionMatrixDisplay(confusion_matrix([r['true'] for r in rows],[r['pred'] for r in rows],labels=LABELS),display_labels=LABELS).plot(ax=ax,cmap='Blues',colorbar=False)
    ax.set_title(title);savefig(name)

@njit(cache=True)
def dtw_cost(C):
    n,m=C.shape;D=np.full((n+1,m+1),np.inf);L=np.zeros((n+1,m+1));D[0,0]=0
    for i in range(1,n+1):
        for j in range(1,m+1):
            vals=(D[i-1,j-1],D[i-1,j],D[i,j-1]);k=np.argmin(np.array(vals))
            ii,jj=((i-1,j-1),(i-1,j),(i,j-1))[k]
            D[i,j]=C[i-1,j-1]+D[ii,jj];L[i,j]=L[ii,jj]+1
    return D[n,m]/L[n,m]
def templates(limit=None):
    return [(features(p,13),label,p) for label in LABELS for p in [p for p,l in files('train') if l==label][:limit]]

def predict_dtw(F,temps):
    scores={l:np.inf for l in LABELS}
    for T,l,p in temps:scores[l]=min(scores[l],float(dtw_cost(cdist(F,T))))
    return min(scores,key=scores.get),scores

def dtw_eval(temps,split='test'):
    rows=[]
    for p,l in files(split):
        pred,sc=predict_dtw(features(p,13),temps);rows.append(dict(file=str(p.relative_to(ROOT)),true=l,pred=pred,**sc))
    return np.mean([r['true']==r['pred'] for r in rows]),rows

def lexicon_parser(path):
    result={}
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        line=line.split('#')[0].strip()
        if not line:continue
        word,*phones=line.split()
        if word in result or not phones:raise ValueError('Invalid lexicon line')
        result[word]=phones
    return result

def forward_viterbi_check(m,X):
    # Independent log-domain Forward/Viterbi implementation for validation.
    if m.covariance_type!='diag':raise ValueError('This check is diagonal only')
    var=np.array([np.diag(c) for c in m.covars_]);D=X.shape[1]
    B=-.5*(D*np.log(2*np.pi)+np.log(var).sum(1)[None,:]+(((X[:,None,:]-m.means_[None,:,:])**2)/var[None,:,:]).sum(2))
    with np.errstate(divide='ignore'):A=np.log(m.transmat_);pi=np.log(m.startprob_)
    alpha=pi+B[0];v=alpha.copy();back=np.zeros((len(X),m.n_components),int)
    for t in range(1,len(X)):
        alpha=B[t]+logsumexp(alpha[:,None]+A,axis=0)
        candidates=v[:,None]+A;back[t]=np.argmax(candidates,axis=0);v=B[t]+np.max(candidates,axis=0)
    q=np.zeros(len(X),int);q[-1]=v.argmax()
    for t in range(len(X)-1,0,-1):q[t-1]=back[t,q[t]]
    fw=float(logsumexp(alpha));vit=float(max(v));library_vit,path=m.decode(X,algorithm='viterbi')
    assert np.isclose(fw,m.score(X)) and np.isclose(vit,library_vit) and np.array_equal(q,path)
    assert fw>=vit-1e-6
    return dict(forward_loglik=fw,viterbi_logprob=vit,difference=fw-vit,match_library=True)

def run():
    OUT.mkdir(exist_ok=True);FIG.mkdir(exist_ok=True);(ROOT/'models').mkdir(exist_ok=True)
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False})
    # Validate actual bytes, independent of manifest labels.
    hashes={};audit=[]
    for split in ['train','val','test']:
        for p,label in files(split):
            info=sf.info(p);assert info.samplerate==16000 and info.channels==1 and info.subtype=='PCM_16'
            h=hashlib.sha256(p.read_bytes()).hexdigest();assert h not in hashes,'Duplicate audio bytes across core split';hashes[h]=str(p)
            F=features(p);audit.append(dict(file=str(p.relative_to(ROOT)),split=split,label=label,seconds=info.duration,frames=len(F),dim=F.shape[1],sha256=h))
    csvout('dataset_audit.csv',audit)
    print('A: audio audited; features finite, T x 39',flush=True)
    for label in ['mo','xuong']:
        p=ROOT/f'dataset/train/{label}/{label}_01.wav';F,blocks,idx=extract(p,details=True)
        fig,axs=plt.subplots(3,1,figsize=(7,5))
        for ax,M,title in zip(axs,blocks,['MFCC (13)','Delta (13)','Delta-delta (13)']):
            im=ax.imshow(M,origin='lower',aspect='auto',cmap='magma');ax.set_ylabel(title);fig.colorbar(im,ax=ax,shrink=.8)
        axs[-1].set_xlabel('Frame (10 ms hop)');fig.suptitle(f'SYNTHETIC {label}: raw features before CMVN');savefig(f'features_{label}.png')
    models,logs,train_seconds=train();dump('training_log.json',logs)
    for row in logs:
        print(row['label'], 'startprob=', row['startprob'], 'transmat=\n',np.round(row['transmat'],3),flush=True)
    train_acc,trainrows=evaluate(models,'train');val_acc,valrows=evaluate(models,'val');test_acc,testrows=evaluate(models,'test');noise_acc,noiserows=evaluate(models,'test_noise15')
    for name,rows in [('train',trainrows),('val',valrows),('test',testrows),('noise15',noiserows)]:csvout(f'scores_{name}.csv',rows)
    cmplot(testrows,'cm_hmm.png',f'HMM clean synthetic test: {test_acc:.0%}')
    cmplot(noiserows,'cm_noise.png',f'HMM noise 15 dB: {noise_acc:.0%}')
    with (ROOT/'models/hmm_5state_39d.pkl').open('wb') as f:pickle.dump(dict(models=models,labels=LABELS,dim=39,source='synthetic',feature_config='utterance CMVN, 25ms/10ms, n_fft512, 26mel'),f)
    plt.figure(figsize=(7,3.2))
    for l in logs:plt.plot(l['history'],label=l['label'])
    plt.xlabel('EM iteration');plt.ylabel('Training log-likelihood');plt.legend(ncol=5);savefig('convergence.png')
    durations=[];checks=[]
    for label in ['mo','xuong']:
        p=ROOT/f'dataset/test/{label}/{label}_01.wav';F=features(p);lp,path=models[label].decode(F,algorithm='viterbi')
        assert np.all(np.diff(path)>=0)
        checks.append(dict(file=str(p.relative_to(ROOT)),**forward_viterbi_check(models[label],F)))
        for s in range(5):durations.append(dict(file=p.name,state=s,frames=int(sum(path==s)),duration_ms=int(sum(path==s))*10))
        plt.figure(figsize=(7,2.6));plt.step(np.arange(len(path))*.01,path,where='post');plt.yticks(range(5));plt.xlabel('Time relative to trimmed audio (s)');plt.ylabel('State');plt.title(f'Viterbi: {label}, log-prob={lp:.1f}');savefig(f'viterbi_{label}.png')
    csvout('state_durations.csv',durations);dump('forward_viterbi_checks.json',checks)
    print('B-D: baseline trained and evaluated',flush=True)
    experiments=[];configs={5:(models,logs,train_seconds)}
    for n in [3,5,7]:
        mm,ll,tt=configs[5] if n==5 else train(n=n);configs[n]=(mm,ll,tt)
        va,_=evaluate(mm,'val');te,_=evaluate(mm,'test');tr,_=evaluate(mm,'train')
        experiments.append(dict(experiment='E1',config=f'{n} states',train_accuracy=tr,val_accuracy=va,test_accuracy=te,train_s=tt,statuses=';'.join(l['status'] for l in ll)))
        dump(f'training_{n}states.json',ll)
    # Pick using validation only; fixed pedagogical 5-state baseline remains report reference.
    selected=min(experiments,key=lambda r:(-r['val_accuracy'],int(r['config'].split()[0])))['config']
    m13,l13,t13=train(dim=13);a13,r13=evaluate(m13,'test',dim=13);v13,_=evaluate(m13,'val',dim=13)
    csvout('scores_mfcc13.csv',r13);cmplot(r13,'cm_mfcc13.png',f'MFCC13 HMM: {a13:.0%}')
    experiments.extend([dict(experiment='E2',config='MFCC13',val_accuracy=v13,test_accuracy=a13,train_s=t13),dict(experiment='E2',config='MFCC39',val_accuracy=val_acc,test_accuracy=test_acc,train_s=train_seconds)])
    try:
        mf,lf,tf=train(cov='full');af,rf=evaluate(mf,'test');vf,_=evaluate(mf,'val');at,rt=evaluate(mf,'train')
        csvout('scores_full_test.csv',rf);csvout('scores_full_train.csv',rt);dump('training_full.json',lf)
        experiments.append(dict(experiment='E3',config='full regularized',train_accuracy=at,val_accuracy=vf,test_accuracy=af,train_s=tf,mean_train_true_loglik_frame=float(np.mean([r[r['true']]/r['frames'] for r in rt])),mean_test_true_loglik_frame=float(np.mean([r[r['true']]/r['frames'] for r in rf]))))
    except (ValueError,np.linalg.LinAlgError) as e:experiments.append(dict(experiment='E3',config='full failed',error=str(e)))
    experiments.append(dict(experiment='E3',config='diag',train_accuracy=train_acc,val_accuracy=val_acc,test_accuracy=test_acc,mean_train_true_loglik_frame=float(np.mean([r[r['true']]/r['frames'] for r in trainrows])),mean_test_true_loglik_frame=float(np.mean([r[r['true']]/r['frames'] for r in testrows]))))
    print('E1-E3: state, feature and covariance experiments complete',flush=True)
    temps=templates();dtw_cost(np.ones((3,3))) # warm JIT; not timed as prediction
    da,dr=dtw_eval(temps);csvout('scores_dtw.csv',dr);cmplot(dr,'cm_dtw.png',f'DTW clean synthetic test: {da:.0%}')
    nd,ndr=dtw_eval(temps,'test_noise15');csvout('scores_dtw_noise.csv',ndr)
    def bench(fun):
        fun();times=[]
        for _ in range(3):
            t=time.perf_counter();fun();times.append((time.perf_counter()-t)/len(testrows)*1000)
        return float(np.median(times))
    ht=bench(lambda:evaluate(models,'test'));dt=bench(lambda:dtw_eval(temps))
    t=time.perf_counter();templates();template_s=time.perf_counter()-t
    compare=[dict(model='HMM39',accuracy=test_acc,noise_accuracy=noise_acc,train_per_class=12,fit_or_template_s=train_seconds,test_score_ms=ht),dict(model='DTW13',accuracy=float(da),noise_accuracy=float(nd),train_per_class=12,fit_or_template_s=template_s,test_score_ms=dt)]
    csvout('dtw_vs_hmm.csv',compare)
    disagreements=[]
    for split,hr,dd in [('clean',testrows,dr),('noise15',noiserows,ndr)]:
        for h,d in zip(hr,dd):
            if h['pred']!=d['pred']:disagreements.append(dict(condition=split,file=h['file'],true=h['true'],hmm=h['pred'],dtw=d['pred'],hmm_correct=h['true']==h['pred'],dtw_correct=d['true']==d['pred']))
    csvout('disagreements.csv',disagreements)
    # DTW alignment for a representative test utterance and its nearest true-class template.
    p=ROOT/'dataset/test/mo/mo_01.wav';F=features(p,13)
    candidates=[(dtw_cost(cdist(F,T)),T,pp) for T,l,pp in temps if l=='mo'];_,T,tp=min(candidates,key=lambda r:r[0]);C=cdist(F,T)
    D,wp=librosa.sequence.dtw(C=C)
    plt.figure(figsize=(5,4));plt.imshow(C,origin='lower',aspect='auto',cmap='magma');plt.plot(wp[:,1],wp[:,0],color='cyan');plt.xlabel('Template frame');plt.ylabel('Test frame');plt.title('DTW warping path: mo');savefig('dtw_path.png')
    scarcity=[]
    for count in [2,6,12]:
        mm= models if count==12 else train(limit=count)[0]
        aa,_=evaluate(mm,'test');ad,_=dtw_eval(templates(count));scarcity.append(dict(train_per_class=count,hmm_accuracy=aa,dtw_accuracy=float(ad)))
    csvout('sample_size.csv',scarcity)
    print('E4-E5: DTW and mismatch evaluated',flush=True)
    lex=lexicon_parser(ROOT/'lexicon.txt');assert set(lex)==set(LABELS);dump('lexicon_parsed.json',lex)
    unigram=Counter();bigram=Counter();context=Counter()
    for line in (ROOT/'corpus.txt').read_text().splitlines():
        if not line.strip() or line.startswith('#'):continue
        ws=line.split();assert set(ws)<=set(LABELS);unigram.update(ws)
        for a,b in zip(['<s>']+ws[:-1],ws):bigram[a,b]+=1;context[a]+=1
    # Denominator is outgoing context count, NOT token unigram count at sentence ends.
    def prob(a,b):return (bigram[a,b]+.5)/(context[a]+.5*len(LABELS))
    for a in ['<s>']+LABELS:assert np.isclose(sum(prob(a,b) for b in LABELS),1)
    dump('lm_counts.json',dict(unigram=dict(unigram),context=dict(context),bigram={a+'|'+b:c for (a,b),c in bigram.items()},k=.5))
    # Diagnostic near-boundary probe derived ONLY from validation. SNR search is
    # for a teaching example, never model/threshold selection or reported accuracy.
    probe_path=ROOT/'dataset/probe/ambiguous.wav';probe_path.parent.mkdir(exist_ok=True)
    best=None;rng=np.random.default_rng(901)
    for label in LABELS:
        src=ROOT/f'dataset/val/{label}/{label}_01.wav';y,sr=sf.read(src)
        rms=np.sqrt(np.mean(y[4800:-4800]**2));noise=rng.normal(size=len(y));noise/=np.sqrt(np.mean(noise**2))
        for snr in np.linspace(10,50,161):
            z=np.clip(y+noise*rms/(10**(snr/20)),-.99,.99)
            sf.write(probe_path,z,sr,subtype='PCM_16');F=extract(probe_path)
            scores={l:float(models[l].score(F)) for l in LABELS};rank=sorted(scores,key=scores.get,reverse=True)
            gap=(scores[rank[0]]-scores[rank[1]])/len(F)
            if best is None or gap<best[0]:best=(gap,z.copy(),dict(file=str(probe_path.relative_to(ROOT)),true=label,pred=rank[0],frames=len(F),margin_frame=gap,**scores),dict(parent=str(src.relative_to(ROOT)),snr_db=float(snr),purpose='Validation-derived diagnostic selected for small acoustic margin; excluded from accuracy and tuning.'))
    sf.write(probe_path,best[1],16000,subtype='PCM_16');candidate=best[2]
    dump('probe_metadata.json',dict(**best[3],**candidate));lmrows=[]
    for prev in ['<s>']+LABELS:
        for weight in [0,.1,.3,1,3,10,30,100]:
            sc={l:candidate[l]/candidate['frames']+weight*np.log(prob(prev,l)) for l in LABELS};pred=max(sc,key=sc.get)
            lmrows.append(dict(file=candidate['file'],true=candidate['true'],previous=prev,lambda_lm=weight,pred=pred,acoustic_pred=candidate['pred'],**sc))
    csvout('lm_rerank.csv',lmrows)
    # Across all test utterances, contexts are hypothetical sensitivity probes, not known real contexts.
    transitions=[]
    for r in testrows+[candidate]:
        for prev in ['<s>']+LABELS:
            for weight in [.1,.3,1,3,10,30,100]:
                sc={l:r[l]/r['frames']+weight*np.log(prob(prev,l)) for l in LABELS};pred=max(sc,key=sc.get)
                if pred!=r['pred']:transitions.append(dict(file=r['file'],true=r['true'],previous=prev,lambda_lm=weight,old=r['pred'],new=pred,effect='corrected' if pred==r['true'] else ('harmed' if r['pred']==r['true'] else 'still_wrong')))
    csvout('lm_changes.csv',transitions)
    plt.figure(figsize=(7,3))
    for l in LABELS:plt.plot([0,.1,.3,1,3,10,30,100],[candidate[l]/candidate['frames']+w*np.log(prob('mo',l)) for w in [0,.1,.3,1,3,10,30,100]],label=l)
    plt.xscale('symlog',linthresh=.1);plt.xlabel('LM weight (hypothetical previous word = mo)');plt.ylabel('Combined score');plt.legend(ncol=5);savefig('lm_sensitivity.png')
    # Calibrate rejection with validation only, including distinct OOV phrases.
    def unknown(split):
        rows=[]
        for p in sorted((ROOT/'dataset'/split/'unknown').glob('*.wav')):
            F=features(p);v=[models[l].score(F)/len(F) for l in LABELS];rows.append(dict(file=str(p.relative_to(ROOT)),max_score=max(v)))
        return rows
    uv=unknown('unknown_val');ut=unknown('unknown_test');kv=[max(r[l] for l in LABELS)/r['frames'] for r in valrows]
    vals=sorted(set(kv+[r['max_score'] for r in uv]));thresholds=[vals[0]-1]+[(a+b)/2 for a,b in zip(vals,vals[1:])]+[vals[-1]+1]
    def ba(th):return .5*(np.mean(np.array(kv)>=th)+np.mean(np.array([r['max_score'] for r in uv])<th))
    threshold=max(thresholds,key=lambda th:(ba(th),-th))
    kr=[max(r[l] for l in LABELS)/r['frames'] for r in testrows]
    reject=dict(threshold=float(threshold),validation_balanced_accuracy=float(ba(threshold)),known_test_false_reject=float(np.mean(np.array(kr)<threshold)),unknown_test_reject_rate=float(np.mean(np.array([r['max_score'] for r in ut])<threshold)),unknown_val=uv,unknown_test=ut,limitation='Only 4 validation OOV and 4 test OOV samples; synthetic phrases; not a calibrated real-world unknown detector.')
    dump('reject_threshold.json',reject)
    correct=[r[r['true']]/r['frames'] for r in testrows];wrong=[r[l]/r['frames'] for r in testrows for l in LABELS if l!=r['true']]
    plt.figure(figsize=(6,3));plt.hist(correct,bins=10,alpha=.7,label='True-class scores (20)');plt.hist(wrong,bins=15,alpha=.6,label='Wrong-class scores (80)');plt.xlabel('Log-likelihood / frame');plt.ylabel('Count');plt.legend();savefig('score_distribution.png')
    csvout('experiments.csv',experiments)
    summary=dict(source='All audio SYNTHETIC eSpeak NG; NOT human recordings.',counts={'train':60,'validation':20,'test':20,'noise_test_derivatives':20,'unknown_val':4,'unknown_test':4,'diagnostic_probe':1},train_accuracy=train_acc,val_accuracy=val_acc,test_accuracy=test_acc,noise_accuracy=noise_acc,baseline='fixed 5-state 39D diag',selected_states_validation_only=selected,dtw_accuracy=float(da),dtw_noise_accuracy=float(nd),timing=compare,experiments=experiments,scarcity=scarcity,disagreements=disagreements,lm_candidate=candidate,lm_changes_counts=dict(Counter(r['effect'] for r in transitions)),reject=reject,forward_checks=checks,training_statuses=logs,environment=dict(python=platform.python_version(),numpy=np.__version__,librosa=librosa.__version__,hmmlearn=__import__('hmmlearn').__version__))
    dump('summary.json',summary)
    print(json.dumps({k:summary[k] for k in ['test_accuracy','noise_accuracy','dtw_accuracy','dtw_noise_accuracy','selected_states_validation_only']},indent=2),flush=True)
    print('Completed A-H. See results/summary.json and README.md',flush=True)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--predict');args=ap.parse_args()
    with threadpool_limits(limits=1):
        if args.predict:
            # Load only trusted local pickle files.
            with (ROOT/'models/hmm_5state_39d.pkl').open('rb') as f:bundle=pickle.load(f)
            F=extract(Path(args.predict));scores={l:float(m.score(F)) for l,m in bundle['models'].items()};rank=sorted(scores,key=scores.get,reverse=True)
            reject=json.loads((OUT/'reject_threshold.json').read_text());pred=rank[0] if scores[rank[0]]/len(F)>=reject['threshold'] else 'unknown'
            print(json.dumps(dict(prediction=pred,closed_set_prediction=rank[0],log_likelihood=scores,frames=len(F),note='Scores are NOT calibrated confidence percentages.'),ensure_ascii=False,indent=2))
        else:run()
if __name__=='__main__':main()
