"""Split models into <20 MB tracked parts for browser uploads; restore is offline."""
import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.common import ROOT

def main():
    manifest={}
    for voice in ('male','female'):
        path=ROOT/'models'/f'{voice}.onnx'
        if not path.exists():
            from neural_tts_backend import restore_model
            path=restore_model(voice)
        data=path.read_bytes();names=[]
        for index,start in enumerate(range(0,len(data),16*1024*1024),1):
            name=f'{voice}.onnx.part{index:02d}';(path.parent/name).write_bytes(data[start:start+16*1024*1024]);names.append(name)
        manifest[voice]={'parts':names,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),
            'source_repo':'vnhellboy/vietnamese-piper-voices',
            'source_revision':'df2a53e0b5c8039d17e642cc8d80fa03d59374b7',
            'source_voice':'diemdam' if voice=='male' else 'altotram'}
    (ROOT/'models'/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('Saved 8 parts < 20 MB, configs and checksums. Original ONNX are ignored by git.')
if __name__=='__main__':main()
