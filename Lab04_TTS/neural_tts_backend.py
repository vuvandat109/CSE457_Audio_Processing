"""Local Piper/VITS inference. No network requests and no cached-waveform fallback."""
import hashlib, json, os, time
from pathlib import Path
import numpy as np
from src.common import ROOT, SR, normalize_text, standardize
from scipy.signal import resample_poly

_VOICES={}

def restore_model(voice):
    path=ROOT/'models'/f'{voice}.onnx'
    manifest_path=ROOT/'models'/'manifest.json'
    if not path.exists():
        if not manifest_path.exists(): raise FileNotFoundError(f'Missing model: {path}')
        entry=json.loads(manifest_path.read_text(encoding='utf-8'))[voice]
        temporary=path.with_suffix('.tmp')
        with temporary.open('wb') as out:
            for name in entry['parts']:
                with (ROOT/'models'/name).open('rb') as src:
                    while block:=src.read(1024*1024): out.write(block)
        digest=hashlib.sha256(temporary.read_bytes()).hexdigest()
        if digest!=entry['sha256']:
            temporary.unlink(); raise ValueError('Model checksum mismatch; upload đủ các phần model.')
        temporary.replace(path)
    return path

def get_voice(voice='female'):
    if voice not in ('male','female'): raise ValueError('voice must be male/female')
    if voice not in _VOICES:
        from piper import PiperVoice
        from piper.config import PiperConfig
        import onnxruntime as ort
        opts=ort.SessionOptions(); opts.intra_op_num_threads=2; opts.inter_op_num_threads=1
        # Construct a constrained ONNX session; no unnecessary default session.
        model=restore_model(voice)
        p=PiperVoice(config=PiperConfig.from_dict(json.loads(Path(str(model)+'.json').read_text(encoding='utf-8'))),
                     session=ort.InferenceSession(str(model),sess_options=opts,providers=['CPUExecutionProvider']))
        _VOICES[voice]=p
    return _VOICES[voice]

def synthesize(text, voice='female', length_scale=1., noise_scale=.5, normalize=True):
    from piper import SynthesisConfig
    start=time.perf_counter()
    p=get_voice(voice)
    normalized=' '.join(normalize_text(text)) if normalize else text
    cfg=SynthesisConfig(length_scale=length_scale,noise_scale=noise_scale,noise_w_scale=.65)
    parts=[]
    for chunk in p.synthesize(normalized, syn_config=cfg):
        parts.append(chunk.audio_float_array)
    y=np.concatenate(parts).astype(float)
    fs=p.config.sample_rate
    if fs!=SR:
        from math import gcd
        g=gcd(fs,SR);y=resample_poly(y,SR//g,fs//g)
    y=standardize(y)
    return y,SR,{'latency_s':time.perf_counter()-start,'native_sr':fs,
                 'backend':'Piper/VITS offline ONNX CPU','voice':voice,
                 'text_spoken':normalized,'seeded':False}
