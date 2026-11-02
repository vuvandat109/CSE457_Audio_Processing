"""Compute real-listener MOS and normalized word accuracy from exported CSV.

python scripts/evaluate_ratings.py path/to/ratings.csv
No sample scores, no ASR proxy presented as human intelligibility.
"""
import sys,csv,json,unicodedata,re
from collections import defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.common import ROOT,normalize_text,write_csv

def edit_distance(a,b):
    prev=list(range(len(b)+1))
    for i,x in enumerate(a,1):
        cur=[i]
        for j,y in enumerate(b,1):cur.append(min(cur[-1]+1,prev[j]+1,prev[j-1]+(x!=y)))
        prev=cur
    return prev[-1]

def normalized_words(text):
    out=[]
    text=unicodedata.normalize('NFC',text.lower())
    for tok in re.sub(r'[^\w\s]',' ',text).split():
        if re.fullmatch('[0-9]+',tok):out.extend(normalize_text(tok))
        else:out.append(tok)
    return out

def main():
    if len(sys.argv)<2:raise SystemExit('Usage: python scripts/evaluate_ratings.py ratings.csv [ratings2.csv ...]')
    rows=[]
    for path in sys.argv[1:]:rows.extend(csv.DictReader(open(path,encoding='utf-8-sig')))
    key={r['clip_id']:r for r in csv.DictReader((ROOT/'results'/'listening_key.csv').open(encoding='utf-8-sig'))}
    seen=set();groups=defaultdict(list)
    for r in rows:
        if not r.get('listener_id','').strip():continue
        if not r.get('naturalness') or not r.get('continuity') or not r.get('transcript'):continue
        pair=(r['listener_id'].strip(),r['clip_id'])
        if pair in seen:raise ValueError(f'Duplicate listener/clip: {pair}')
        seen.add(pair)
        for f in ('naturalness','continuity'):
            if not 1<=int(r[f])<=5:raise ValueError('Ratings must be 1..5')
        ref=normalized_words(key[r['clip_id']]['text'])
        hyp=normalized_words(r['transcript'])
        r['word_errors']=edit_distance(ref,hyp);r['reference_words']=len(ref)
        k=key[r['clip_id']];groups[(k['voice'],k['backend'])].append(r)
    if not groups:raise SystemExit('Chưa có đánh giá thật hợp lệ. Không tạo MOS giả.')
    result=[]
    for (voice,backend),rs in sorted(groups.items()):
        errors=sum(r['word_errors'] for r in rs);total=sum(r['reference_words'] for r in rs)
        result.append({'voice':voice,'backend':backend,'n_ratings':len(rs),
            'n_listeners':len(set(r['listener_id'] for r in rs)),
            'mos_naturalness':sum(int(r['naturalness']) for r in rs)/len(rs),
            'mos_continuity':sum(int(r['continuity']) for r in rs)/len(rs),
            'word_accuracy_pct':100*(1-errors/total),
            'word_errors_S_D_I':errors,'reference_words':total})
    write_csv(ROOT/'results'/'subjective_results.csv',result)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    print('Word accuracy = 100*(1-(S+D+I)/N); có thể âm khi chèn quá nhiều từ. Không phải exact sentence accuracy.')

if __name__=='__main__':main()
