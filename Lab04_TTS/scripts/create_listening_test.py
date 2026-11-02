"""Blind, randomized offline listening form; real responses only."""
import sys,json,random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.common import ROOT,SENTENCES,write_csv

def main():
    rng=random.Random(45704);clips=[]
    for voice in ('male','female'):
        for sid,text in enumerate(SENTENCES,1):
            for backend,suffix in [('concat','best_concat'),('hmm','hmm_tts'),('neural','neural_tts')]:
                clips.append({'voice':voice,'sentence_id':sid,'backend':backend,'text':text,
                              'path':f'audio_output/{voice}_s{sid}_{suffix}.wav'})
        for ms in (0,5,15,30):
            clips.append({'voice':voice,'sentence_id':1,'backend':f'crossfade_{ms:02d}ms',
                          'text':SENTENCES[0],
                          'path':f'audio_output/experiments/{voice}_s1_xfade_{ms:02d}ms.wav'})
    rng.shuffle(clips)
    for i,r in enumerate(clips,1):r['clip_id']=f'C{i:02d}'
    write_csv(ROOT/'results'/'listening_key.csv',clips)
    public=[{'clip_id':r['clip_id'],'path':r['path']} for r in clips]
    template='''<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Lab 4 - Phiếu nghe mù</title><style>body{font:16px system-ui;max-width:850px;margin:40px auto;padding:16px;background:#f5f7fa;color:#182738}article{background:white;border:1px solid #ccd7e0;border-radius:10px;padding:18px;margin:15px 0}audio{width:100%}input,select,button{padding:10px;margin:6px}input[type=text]{width:85%}button{background:#174c75;color:white;border:0;border-radius:6px;cursor:pointer}label{display:block}small{color:#536678}</style>
<h1>Lab 4: Phiếu nghe thử</h1><p>Nghe bằng tai nghe trong phòng yên tĩnh. Không xem tên backend hoặc câu gốc trước khi ghi lời nghe được. Đây là âm thanh tổng hợp cho bài học, có hai giọng nam/nữ.</p>
<p>Chấm độ tự nhiên và liền mạch: 1 rất kém, 2 kém, 3 trung bình, 4 tốt, 5 rất tốt. Viết cả câu bạn nghe được; không đoán theo câu mẫu.</p>
<label>Mã người nghe (không cần họ tên): <input id="listener" placeholder="VD: L01" required></label>
<p><small>26 clip: 18 clip so sánh backend và 8 clip cross-fade cùng candidate. Có thể nghỉ giữa các clip. Không có điểm điền sẵn.</small></p><div id="clips"></div>
<button onclick="download()">Tải ratings.csv</button><p id="status"></p>
<script>const clips=__CLIPS__;
function options(){return '<option value="">Chọn điểm</option>'+[1,2,3,4,5].map(v=>`<option>${v}</option>`).join('')}
document.getElementById('clips').innerHTML=clips.map(c=>`<article id="${c.clip_id}"><h2>Clip ${c.clip_id}</h2><audio controls preload="none" src="${c.path}"></audio><label>Câu nghe được: <input type="text" class="transcript" autocomplete="off"></label><label>Độ tự nhiên: <select class="naturalness">${options()}</select></label><label>Độ liền mạch: <select class="continuity">${options()}</select></label></article>`).join('');
function quote(x){return '"'+String(x).replaceAll('"','""')+'"'}
function download(){let id=document.getElementById('listener').value.trim();if(!id){alert('Nhập mã người nghe');return}let rows=[['listener_id','clip_id','naturalness','continuity','transcript']];for(let c of clips){let el=document.getElementById(c.clip_id);let n=el.querySelector('.naturalness').value,k=el.querySelector('.continuity').value,t=el.querySelector('.transcript').value.trim();if(n&&k&&t)rows.push([id,c.clip_id,n,k,t]);}if(rows.length===1){alert('Chưa có clip được đánh giá đầy đủ');return}let blob=new Blob(['\\ufeff'+rows.map(r=>r.map(quote).join(',')).join('\\r\\n')],{type:'text/csv;charset=utf-8'});let a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='ratings_'+id.replace(/[^a-zA-Z0-9_-]/g,'')+'.csv';a.click();document.getElementById('status').textContent='Đã xuất '+(rows.length-1)+' lượt đánh giá. Gửi file CSV cho người tổng hợp.';setTimeout(()=>URL.revokeObjectURL(a.href),1000)}
</script></html>'''
    (ROOT/'listening_test.html').write_text(template.replace('__CLIPS__',json.dumps(public,ensure_ascii=False)),encoding='utf-8')
    write_csv(ROOT/'ratings.csv',[],['listener_id','clip_id','naturalness','continuity','transcript'])
if __name__=='__main__':main()
