"""Shared, offline DSP utilities. All saved teaching audio: mono 16 kHz PCM16."""
from pathlib import Path
import csv, re, unicodedata
import numpy as np
import soundfile as sf
from scipy import signal

ROOT = Path(__file__).resolve().parents[1]
SR = 16000
WORDS = ['mời','khách','hàng','số','không','một','hai','ba','bốn','năm','sáu','bảy','tám','chín','đến','quầy']
SLUGS = ['moi','khach','hang','so','khong','mot','hai','ba','bon','nam','sau','bay','tam','chin','den','quay']
SLUG = dict(zip(WORDS, SLUGS))
DIGIT = dict(zip('0123456789', WORDS[4:14]))
SENTENCES = ['Mời khách hàng số 23 đến quầy 5.',
             'Mời khách hàng số 108 đến quầy 2.',
             'Mời khách hàng số 479 đến quầy 6.']

def normalize_text(text):
    """Queue IDs are read digit by digit, including leading zeros."""
    text = unicodedata.normalize('NFC', text).lower()
    text = re.sub(r'[^\w\s]', ' ', text, flags=re.UNICODE)
    out = []
    for tok in text.split():
        if re.fullmatch(r'[0-9]+', tok): out.extend(DIGIT[c] for c in tok)
        elif tok in SLUG: out.append(tok)
        else: raise ValueError(f'Token ngoài miền hỗ trợ: {tok!r}. Chỉ dùng thông báo xếp hàng.')
    if not out: raise ValueError('Văn bản rỗng.')
    return out

def rms(x): return float(np.sqrt(np.mean(np.asarray(x, dtype=float)**2) + 1e-12))

def load(path):
    x, sr = sf.read(path, dtype='float64')
    if x.ndim == 2: x = x.mean(axis=1)
    if sr != SR:
        from math import gcd
        g = gcd(sr, SR); x = signal.resample_poly(x, SR//g, sr//g)
    return x

def standardize(x, target=.08, trim=True):
    x = np.asarray(x, dtype=float).copy()
    x -= x.mean()
    if trim:
        # Energy trimming with 15 ms context; do not remove interior consonants.
        env = np.sqrt(np.convolve(x*x, np.ones(160)/160, mode='same'))
        active = np.flatnonzero(env > max(env.max()*.035, 1e-5))
        if active.size:
            x = x[max(0,active[0]-240):min(len(x),active[-1]+241)]
    x *= min(target/rms(x), .97/(np.max(np.abs(x))+1e-12))
    return x

def save(path, x, sr=SR):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    x = np.asarray(x)
    if not np.isfinite(x).all(): raise ValueError('NaN/Inf audio')
    if np.max(np.abs(x), initial=0) >= 1:
        x = x * .98/np.max(np.abs(x))
    sf.write(path, x, sr, subtype='PCM_16')

def write_csv(path, rows, fields=None):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None: fields = list(rows[0])
    with path.open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)

def inventory(voice):
    return {word:[load(ROOT/'data'/'units'/f'{voice}_{SLUG[word]}_{i:02d}.wav')
                  for i in (1,2)] for word in WORDS}

def crossfade(a, b, n):
    n = min(int(n), len(a), len(b))
    if n <= 0: return np.concatenate([a,b])
    ramp = np.linspace(0,1,n)
    return np.concatenate([a[:-n], (1-ramp)*a[-n:]+ramp*b[:n], b[n:]])

def concatenate(xs, ms=0):
    y = xs[0].copy(); starts=[0]; boundaries=[]; n=int(SR*ms/1000)
    for x in xs[1:]:
        overlap=min(n,len(y),len(x)); start=len(y)-overlap
        boundaries.append((start+overlap/2)/SR); starts.append(start)
        y = crossfade(y,x,overlap)
    return y, boundaries

def edge_spectrum(x, side):
    n=400  # 25 ms
    seg=x[-n:] if side=='right' else x[:n]
    seg=np.pad(seg,(0,max(0,n-len(seg))))
    return 20*np.log10(np.maximum(np.abs(np.fft.rfft(seg*np.hanning(n),n=512)),1e-8))

def join_cost(a,b):
    return float(np.mean((edge_spectrum(a,'right')-edge_spectrum(b,'left'))**2))

def select_units(tokens, inv, weight=.02):
    """True Viterbi/DP path search with duration/RMS target and spectral join cost."""
    candidates=[inv[t] for t in tokens]
    target=[]
    for xs in candidates:
        ds=np.array([len(x)/SR for x in xs]); rs=np.array([rms(x) for x in xs])
        # Candidate 1 supplies the canonical word-specific duration target.
        # Unlike a two-candidate midpoint, this does not make both costs equal.
        target.append(((ds-ds[0])/.05)**2+((rs-.08)/.02)**2)
    dp=[target[0].copy()]; back=[None]
    for j in range(1,len(tokens)):
        matrix=np.array([[dp[-1][i]+weight*join_cost(a,b)
                          for b in candidates[j]] for i,a in enumerate(candidates[j-1])])
        back.append(np.argmin(matrix,axis=0)); dp.append(target[j]+matrix.min(axis=0))
    choice=[int(np.argmin(dp[-1]))]
    for j in range(len(tokens)-1,0,-1): choice.append(int(back[j][choice[-1]]))
    choice.reverse()
    def costs(path):
        tc=sum(target[j][k] for j,k in enumerate(path))
        jc=sum(join_cost(candidates[j][path[j]],candidates[j+1][path[j+1]]) for j in range(len(path)-1))
        return {'target_cost':float(tc),'join_cost':float(jc),'total_cost':float(tc+weight*jc)}
    return choice, costs, candidates

def boundary_metrics(y,bounds):
    """Objective proxies only, not MOS or a complete measure of continuity."""
    jumps=[]; specs=[]
    for t in bounds:
        p=int(round(t*SR))
        if p>400 and p+400<len(y):
            jumps.append(abs(y[p]-y[p-1])); specs.append(join_cost(y[:p],y[p:]))
    return float(np.mean(jumps)),float(np.mean(specs))
