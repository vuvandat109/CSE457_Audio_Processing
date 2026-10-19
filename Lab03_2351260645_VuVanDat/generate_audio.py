"""Generate SYNTHETIC Vietnamese speech. Never describe it as human recordings."""
from pathlib import Path
import argparse, subprocess, tempfile, json, hashlib, os
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
ROOT=Path(__file__).resolve().parent
WORDS={'mo':'mở','dong':'đóng','len':'lên','xuong':'xuống','dung':'dừng'}

def generate(executable='espeak-ng'):
    rng=np.random.default_rng(20261019); manifest=[]; used=set()
    # Independent synthesis calls/configurations, same TTS engine and base voice.
    for split,n in [('train',12),('val',4),('test',4),('unknown_val',4),('unknown_test',4)]:
        words=WORDS if not split.startswith('unknown') else ({'unknown':'xin chào'} if split=='unknown_val' else {'unknown':'cảm ơn'})
        for label,word in words.items():
            for i in range(n):
                while True:
                    speed=int(rng.integers(120,201)); pitch=int(rng.integers(35,66)); amp=int(rng.integers(85,111))
                    key=(word,speed,pitch,amp)
                    if key not in used: used.add(key); break
                with tempfile.TemporaryDirectory() as td:
                    raw=Path(td)/'raw.wav'
                    subprocess.run([executable,'-v','vi','-s',str(speed),'-p',str(pitch),'-a',str(amp),'-w',str(raw),word],check=True,capture_output=True)
                    y,sr=sf.read(raw)
                if y.ndim>1:y=y.mean(axis=1)
                from math import gcd
                g=gcd(sr,16000); y=resample_poly(y,16000//g,sr//g)
                active=np.flatnonzero(np.abs(y)>0.002)
                if len(active)==0:raise ValueError('Silent TTS')
                y=y[max(0,active[0]-160):min(len(y),active[-1]+161)]
                y=.85*y/max(abs(y))
                y=np.pad(y,(4800,4800))
                path=ROOT/'dataset'/split/label/f'{label}_{i+1:02d}.wav';path.parent.mkdir(parents=True,exist_ok=True)
                sf.write(path,y,16000,subtype='PCM_16')
                manifest.append(dict(path=str(path.relative_to(ROOT)),label=label,text=word,split=split,source='SYNTHETIC eSpeak NG vi',speed=speed,pitch=pitch,amplitude=amp,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    # Paired stress test. Noisy files are derivatives of test ONLY, never training examples.
    for row in list(manifest):
        if row['split']!='test':continue
        y,sr=sf.read(ROOT/row['path']); speech=y[4800:-4800]; rms=np.sqrt(np.mean(speech**2))
        noise=rng.normal(size=len(y)); noise*=rms/(10**(15/20)*np.sqrt(np.mean(noise**2)))
        z=np.clip(y+noise,-.99,.99)
        path=ROOT/row['path'].replace('/test/','/test_noise15/');path.parent.mkdir(parents=True,exist_ok=True)
        sf.write(path,z,sr,subtype='PCM_16')
        manifest.append(dict(path=str(path.relative_to(ROOT)),label=row['label'],split='test_noise15',source='synthetic test + white Gaussian noise, nominal active-speech SNR 15 dB',parent=row['path'],sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    (ROOT/'dataset/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    preview=[]
    for label in WORDS:
        y,_=sf.read(ROOT/f'dataset/test/{label}/{label}_01.wav');preview.extend([y,np.zeros(8000)])
    sf.write(ROOT/'Nghe_thu_5_lenh.wav',np.concatenate(preview),16000,subtype='PCM_16')
    print(f'Generated {len(manifest)} WAV files; all SYNTHETIC.')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--espeak',default='espeak-ng');a=p.parse_args();generate(a.espeak)
