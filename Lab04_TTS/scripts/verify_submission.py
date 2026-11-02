"""Verify real deliverables, independent exhaustive DP optimum, and offline inference."""
import sys,json,csv,itertools,socket,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import soundfile as sf
from src.common import *

def main():
    checks=[]
    rows=list(csv.DictReader((ROOT/'data'/'metadata.csv').open(encoding='utf-8-sig')))
    assert len(rows)==64
    for v in ('male','female'):
        for w in WORDS: assert sum(r['speaker']==v and r['label']==w for r in rows)==2
    checks.append('64 units; 16 labels x 2 candidates x 2 voices')
    paths=list((ROOT/'data'/'units').glob('*.wav'))+list((ROOT/'audio_output').rglob('*.wav'))
    for path in paths:
        info=sf.info(path);x,fs=sf.read(path)
        assert info.channels==1 and fs==16000 and info.subtype=='PCM_16',path
        assert np.isfinite(x).all() and len(x)>0 and np.max(np.abs(x))<1,path
        assert rms(x)>1e-5,path
    checks.append(f'{len(paths)} WAVs: mono/16k/PCM16, finite, nonempty, no full-scale clipping')
    assert normalize_text('MỜI khách hàng số 023 đến quầy 5!')==['mời','khách','hàng','số','không','hai','ba','đến','quầy','năm']
    try:normalize_text('xin chào')
    except ValueError:pass
    else:raise AssertionError('Out-of-domain input not rejected')
    checks.append('Normalization preserves leading zeros and rejects unsupported words')
    # Independent exhaustive enumeration of a complete 9-token sentence.
    for v in ('male','female'):
        inv=inventory(v);tokens=normalize_text(SENTENCES[0]);path,costfn,cands=select_units(tokens,inv)
        brute=min(costfn(list(p))['total_cost'] for p in itertools.product(range(2),repeat=len(tokens)))
        assert abs(costfn(path)['total_cost']-brute)<1e-8
        xs=[cands[j][k] for j,k in enumerate(path)]
        for ms in (0,5,15,30):
            y,_=concatenate(xs,ms)
            assert len(y)==sum(map(len,xs))-(len(xs)-1)*int(ms*SR/1000)
    checks.append('DP matches exhaustive optimum for both voices; all overlap lengths correct')
    results=list(csv.DictReader((ROOT/'results'/'unit_selection_costs.csv').open(encoding='utf-8-sig')))
    for v in ('male','female'):
        for s in ('1','2','3'):
            rs=[r for r in results if r['voice']==v and r['sentence_id']==s]
            fixed=next(float(r['total_cost']) for r in rs if r['method']=='fixed_candidate')
            best=next(float(r['total_cost']) for r in rs if r['method']=='dynamic_programming')
            assert best<=fixed+1e-8
            for backend in ('raw_concat','best_concat','hmm_tts','neural_tts'):
                assert (ROOT/'audio_output'/f'{v}_s{s}_{backend}.wav').exists()
            track=np.load(ROOT/'results'/f'{v}_s{s}_hmm_tracks.npz')
            assert len(track['f0'])==len(track['state']) and len(np.unique(track['state']))>10
    checks.append('All three sentences x two voices x four outputs; HMM state/F0 tracks present')
    from neural_tts_backend import synthesize
    original=socket.socket.connect
    def deny(*args,**kwargs):raise RuntimeError('Network disabled by offline verification')
    socket.socket.connect=deny
    try:
        for v in ('male','female'):
            y,_,_=synthesize(SENTENCES[0],v)
            assert len(y)>SR and np.isfinite(y).all()
    finally:socket.socket.connect=original
    checks.append('Both neural voices synthesize with socket connections blocked; no cached-audio fallback')
    assert len(list((ROOT/'figures').glob('*.png')))>=9
    checks.append('9 required/supporting figures exist')
    report={'status':'PASS','checks':checks,'wav_count':len(paths),
            'remaining_human_action':'Collect 5-10 real listeners and run evaluate_ratings.py; no fabricated MOS.',
            'subjective_audio_quality':'Not certified as indistinguishable from human speech.'}
    (ROOT/'results'/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
