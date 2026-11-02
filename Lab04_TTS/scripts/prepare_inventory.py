"""Create 64 synthetic units: 16 labels x 2 candidates x 2 designed voices."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.common import *
from neural_tts_backend import synthesize, get_voice

def main():
    rows=[]
    for voice in ('male','female'):
        get_voice(voice)
        for word in WORDS:
            for candidate in (1,2):
                relative=f'data/units/{voice}_{SLUG[word]}_{candidate:02d}.wav'
                path=ROOT/relative
                if not path.exists():
                    y,_,_=synthesize(word,voice,length_scale=1 if candidate==1 else 1.06,
                                     noise_scale=.45 if candidate==1 else .6)
                    save(path,y)
                x=load(path)
                rows.append(dict(label=word,speaker=voice,candidate=candidate,
                                 duration_s=len(x)/SR,rms=rms(x),sample_rate=SR,
                                 channels=1,subtype='PCM_16',file_path=relative,
                                 source='synthetic Piper/VITS; NOT human recording'))
                print(voice,word,candidate,round(len(x)/SR,3),flush=True)
    write_csv(ROOT/'data'/'metadata.csv',rows)
if __name__=='__main__':main()
