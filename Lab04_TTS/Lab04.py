"""Run all Lab 4 A-G experiments using the supplied offline assets.

Usage: python Lab04.py
       python Lab04.py --text "Mời khách hàng số 23 đến quầy 5." --voice male
"""
import argparse, csv, json, platform, time, importlib.metadata, shutil
import numpy as np
import librosa
import pyworld as pw
from src.common import *
from src import plots
from neural_tts_backend import synthesize,get_voice
from hmm_tts_backend import synthesize_hmm,train

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--text');ap.add_argument('--voice',choices=['male','female'],default='female')
    args=ap.parse_args()
    if args.text:
        y,sr,info=synthesize(args.text,args.voice)
        save(ROOT/'audio_output'/'custom_neural.wav',y)
        print(json.dumps(info,ensure_ascii=False,indent=2));return
    if not (ROOT/'data'/'metadata.csv').exists():
        raise FileNotFoundError('Thiếu inventory. Giải nén đầy đủ hoặc chạy scripts/prepare_inventory.py.')
    metadata=list(csv.DictReader((ROOT/'data'/'metadata.csv').open(encoding='utf-8-sig')))
    plots.stats(metadata)
    costs=[];xfades=[];latencies=[];tracks_for_plot=None;model_load=[];boundaries={}
    for voice in ('male','female'):
        inv=inventory(voice)
        if not (ROOT/'data'/'hmm_demo'/f'{voice}_gaussian_hmm.npz').exists():train(voice)
        begin=time.perf_counter();get_voice(voice)
        model_load.append({'voice':voice,'model_load_s':time.perf_counter()-begin})
        for sid,text in enumerate(SENTENCES,1):
            print(f'Processing {voice}, sentence {sid}: {text}',flush=True)
            tokens=normalize_text(text);choice,costfn,cands=select_units(tokens,inv)
            selected=[cands[j][k] for j,k in enumerate(choice)]
            baseline=[0]*len(tokens)
            for method,path in [('fixed_candidate',baseline),('dynamic_programming',choice)]:
                costs.append({'voice':voice,'sentence_id':sid,'method':method,
                              'candidate_path':' '.join(str(k+1) for k in path),**costfn(path)})
            raw,rb=concatenate([inv[t][0] for t in tokens])
            best,bb=concatenate(selected,15)
            save(ROOT/'audio_output'/f'{voice}_s{sid}_raw_concat.wav',raw)
            save(ROOT/'audio_output'/f'{voice}_s{sid}_best_concat.wav',best)
            boundaries[f'{voice}_s{sid}']={'tokens':tokens,'raw_s':rb,'best_s':bb,'candidate_path':[x+1 for x in choice]}
            for ms in (0,5,15,30):
                y,b=concatenate(selected,ms);jump,spec=boundary_metrics(y,b)
                save(ROOT/'audio_output'/'experiments'/f'{voice}_s{sid}_xfade_{ms:02d}ms.wav',y)
                xfades.append({'voice':voice,'sentence_id':sid,'crossfade_ms':ms,
                               'mean_sample_jump':jump,'spectral_mismatch':spec,'duration_s':len(y)/SR})
            yh,_,track=synthesize_hmm(text,voice)
            save(ROOT/'audio_output'/f'{voice}_s{sid}_hmm_tts.wav',yh)
            np.savez_compressed(ROOT/'results'/f'{voice}_s{sid}_hmm_tracks.npz',
                                **{k:v for k,v in track.items() if isinstance(v,np.ndarray)})
            write_csv(ROOT/'results'/f'{voice}_s{sid}_hmm_states.csv',track['durations'])
            # First inference is saved and separately identified; warm repeats below.
            yn,_,info=synthesize(text,voice)
            save(ROOT/'audio_output'/f'{voice}_s{sid}_neural_tts.wav',yn)
            mel=librosa.feature.melspectrogram(y=yn,sr=SR,n_fft=512,hop_length=160,n_mels=80)
            np.save(ROOT/'results'/f'{voice}_s{sid}_neural_mel.npy',librosa.power_to_db(mel,ref=np.max))
            for backend in ('concat','hmm','neural'):
                for repeat in range(3):
                    begin=time.perf_counter()
                    if backend=='concat':
                        ts=normalize_text(text);ch,_,cs=select_units(ts,inv)
                        y,_=concatenate([cs[j][k] for j,k in enumerate(ch)],15)
                    elif backend=='hmm': y,_,_=synthesize_hmm(text,voice)
                    else:y,_,_=synthesize(text,voice)
                    elapsed=time.perf_counter()-begin
                    latencies.append({'voice':voice,'sentence_id':sid,'backend':backend,
                        'repeat':repeat+1,'latency_s':elapsed,'audio_duration_s':len(y)/SR,
                        'rtf':elapsed/(len(y)/SR),'scope':'warm; text-to-array; no file I/O/model load'})
            if voice=='female' and sid==1:
                plots.boundaries(raw,best,rb,bb);tracks_for_plot=track
                dpraw,dpb=concatenate(selected,0)
                plots.isolated_boundary_spectra(dpraw,best,dpb,bb)
                plots.comparison([('Ghép nối DP + 15 ms',best),('HMM Gaussian + WORLD',yh),('Neural Piper/VITS',yn)])
                for name,x in [('raw_concat',raw),('best_concat',best),('hmm_tts',yh),('neural_tts',yn)]:
                    save(ROOT/'audio_output'/f'{name}.wav',x)
                prosody(best,text,voice)
    plots.cost_plot(costs,xfades);plots.hmm_plot(tracks_for_plot)
    for name,rows in [('unit_selection_costs',costs),('crossfade_metrics',xfades),
                      ('latency',latencies),('model_load',model_load)]:write_csv(ROOT/'results'/f'{name}.csv',rows)
    (ROOT/'results'/'boundaries.json').write_text(json.dumps(boundaries,ensure_ascii=False,indent=2),encoding='utf-8')
    env={'python':platform.python_version(),'platform':platform.platform(),'processor':platform.processor(),
         'onnx_threads':2,'device':'CPU','packages':{m:importlib.metadata.version(m) for m in
          ['numpy','scipy','librosa','soundfile','piper-tts','onnxruntime','pyworld']},
         'neural_model_revision':'df2a53e0b5c8039d17e642cc8d80fa03d59374b7',
         'subjective_evaluation':'pending real listeners; NO fabricated MOS/intelligibility',
         'crossfade_choice':'15 ms provisional compromise; confirm by listening; not optimized using invented ratings',
         'inventory_provenance':'synthetic neural voices, not microphone recordings; confounds backend comparison'}
    (ROOT/'results'/'environment.json').write_text(json.dumps(env,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Completed A-F/objective G. Listening test remains for real participants.',flush=True)

def prosody(x,text,voice):
    variants=[];rows=[]
    for rate in (.8,1.,1.2):
        y=librosa.effects.time_stretch(x,rate=rate)
        save(ROOT/'audio_output'/'experiments'/f'speed_{rate:.1f}.wav',y)
        variants.append((f'Speed {rate:.1f}× (phase vocoder)',y))
        rows.append({'operation':'speed','value':rate,'duration_s':len(y)/SR})
    # WORLD modifies only F0; retains extracted spectral envelope/ap (source-filter demo).
    xd=np.ascontiguousarray(x,dtype=np.float64)
    f0,t=pw.dio(xd,SR,frame_period=10,f0_floor=65,f0_ceil=500)
    f0=pw.stonemask(xd,f0,t,SR);sp=pw.cheaptrick(xd,f0,t,SR);ap=pw.d4c(xd,f0,t,SR)
    for semitone in (-2,0,2):
        ratio=2**(semitone/12)
        y=pw.synthesize(np.ascontiguousarray(f0*ratio),sp,ap,SR,frame_period=10)
        y=standardize(y,trim=False)
        save(ROOT/'audio_output'/'experiments'/f'pitch_{semitone:+d}st.wav',y)
        variants.append((f'Pitch {semitone:+d} semitone (WORLD)',y))
        rows.append({'operation':'pitch_semitone','value':semitone,'duration_s':len(y)/SR})
    plots.prosody(variants);write_csv(ROOT/'results'/'prosody.csv',rows)
    for scale in (.8,1.2):
        y,_,_=synthesize_hmm(text,voice,duration_scale=scale)
        save(ROOT/'audio_output'/'experiments'/f'hmm_duration_{scale:.1f}.wav',y)
    for scale in (.9,1.1):
        y,_,_=synthesize_hmm(text,voice,f0_scale=scale)
        save(ROOT/'audio_output'/'experiments'/f'hmm_f0_{scale:.1f}.wav',y)
    # Choose the longest usable voiced unit "mời"; cross-check pYIN with local autocorrelation.
    unit=inventory(voice)['mời'][0]
    pyf,voiced,_=librosa.pyin(unit,fmin=65,fmax=500,sr=SR,frame_length=1024,hop_length=80)
    valid=np.flatnonzero(np.isfinite(pyf))
    if not valid.size:raise RuntimeError('No voiced frame for F0 check')
    idx=valid[len(valid)//2];estimate=float(pyf[idx]);center=min(max(idx*80,512),len(unit)-512)
    seg=unit[center-512:center+512];seg=seg-seg.mean()
    ac=np.correlate(seg*np.hanning(len(seg)),seg*np.hanning(len(seg)),mode='full')[len(seg)-1:]
    lo=max(1,int(SR/estimate*.8));hi=int(SR/estimate*1.2)
    period=int(np.argmax(ac[lo:hi+1])+lo)
    check={'unit':f'{voice}_moi_01.wav','pyin_f0_hz':estimate,'period_samples':period,
           'fs_over_period_hz':SR/period,'relative_difference_pct':100*abs(SR/period-estimate)/estimate,
           'method':'pYIN plus autocorrelation near predicted period; local voiced frame, not independent ground truth'}
    (ROOT/'results'/'f0_check.json').write_text(json.dumps(check,ensure_ascii=False,indent=2),encoding='utf-8')
    plots.f0_check(unit,max(0,center-2*period),period,estimate)

if __name__=='__main__':main()
