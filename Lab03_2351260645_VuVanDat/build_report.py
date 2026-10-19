"""Build the six-page report from actual computed result files."""
from pathlib import Path
import json,csv
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER
from matplotlib.font_manager import findfont,FontProperties
R=Path(__file__).resolve().parent;S=json.loads((R/'results/summary.json').read_text());F=R/'results/figures'
for name,bold in [('DV',False),('DVB',True)]:pdfmetrics.registerFont(TTFont(name,findfont(FontProperties(family='DejaVu Sans',weight='bold' if bold else 'normal'))))
pdfmetrics.registerFontFamily('DV',normal='DV',bold='DVB',italic='DV',boldItalic='DVB')
styles={
 'title':ParagraphStyle('title',fontName='DVB',fontSize=22,leading=29,textColor=colors.HexColor('#15334D'),spaceAfter=16),
 'h1':ParagraphStyle('h1',fontName='DVB',fontSize=15,leading=21,textColor=colors.HexColor('#15334D'),spaceAfter=12),
 'h2':ParagraphStyle('h2',fontName='DVB',fontSize=11,leading=16,spaceBefore=9,spaceAfter=5),
 'body':ParagraphStyle('body',fontName='DV',fontSize=9.3,leading=14,spaceAfter=7),
 'small':ParagraphStyle('small',fontName='DV',fontSize=7.5,leading=10.5,spaceAfter=5),
 'cell':ParagraphStyle('cell',fontName='DV',fontSize=8,leading=11),
 'caption':ParagraphStyle('caption',fontName='DV',fontSize=8,leading=11,textColor=colors.HexColor('#435B6D'),spaceAfter=8)
}
story=[]
def p(t,style='body'):
    import re
    t=re.sub(r'(\d)(frame|state|mẫu|lệnh|chiều|từ|model|vòng|điểm|test|train|giây|chuỗi|file|phương|phần|câu|trang|bản|lượt|lớp|người)',r'\1 \2',t)
    story.append(Paragraph(t,styles[style]))
def h(t):p(t,'h2')
def table(headers,rows,widths=None):
    content=[[Paragraph(escape(str(v)),styles['cell']) for v in row] for row in [headers]+rows]
    t=Table(content,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#DFEBF2')),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#99B0C0')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F5F8FA')])]))
    story.append(t);story.append(Spacer(1,8))
def img(name,w=470,h=None):
    from PIL import Image as PI
    with PI.open(F/name) as im:iw,ih=im.size
    story.append(Image(str(F/name),width=w,height=h or w*ih/iw));story.append(Spacer(1,4))
def pair(a,b,w=235):
    from PIL import Image as PI
    ims=[]
    for n in [a,b]:
        with PI.open(F/n) as im:x,y=im.size
        ims.append(Image(str(F/n),width=w,height=w*y/x))
    story.append(Table([ims],colWidths=[245,245]));story.append(Spacer(1,6))
def pct(x):return f'{100*x:.0f}%'
def readcsv(n):return list(csv.DictReader((R/'results'/n).open(encoding='utf-8-sig')))
def page(title):story.append(PageBreak());p(title,'h1')

p('CSE457 • XỬ LÝ ÂM THANH VÀ TIẾNG NÓI','small')
p('LAB 03<br/>Nhận dạng tiếng nói<br/>với Gaussian HMM','title')
p('Báo cáo thực nghiệm • 5 lệnh tiếng Việt • 19/10/2026','caption')
p('<b>Phạm vi dữ liệu:</b> toàn bộ âm thanh được tổng hợp bằng eSpeak NG 1.51, giọng vi. Đây là thực nghiệm trên dữ liệu máy tạo, không phải bản ghi giọng người thật. Kết quả không chứng minh hiệu năng trên người nói mới hoặc trong ứng dụng thực tế.')
h('1. Mục tiêu và tổ chức dữ liệu')
p('Xây dựng một whole-word HMM cho mỗi lệnh mở, đóng, lên, xuống, dừng; phân tích likelihood, Viterbi, Baum–Welch; so sánh DTW; minh họa lexicon, bigram và độ bền khi có nhiễu.')
table(['Tập','Số WAV','Vai trò'],[['Train','60 (12/lệnh)','Fit model; không chứa test'],['Validation','20 (4/lệnh)','So sánh số state và hiệu chỉnh reject'],['Test sạch','20 (4/lệnh)','Đánh giá độc lập với fit'],['Test nhiễu','20','Dẫn xuất paired từ test, SNR15dB'],['Unknown val/test','4 + 4','Hai nội dung ngoài từ vựng khác nhau'],['Probe chẩn đoán','1','Dẫn xuất validation; minh họa LM, không tính accuracy']],[95,100,295])
p('Mỗi WAV mono, 16kHz, PCM16; có0,3s im lặng đầu/cuối. Mỗi mẫu gốc là một lần gọi TTS riêng với tốc độ120–200, pitch35–65, amplitude85–110; seed20261019. Kiểm tra SHA-256 không có file trùng byte trong train/val/test. Các tập vẫn cùng engine và giọng nền nên độ độc lập còn hạn chế.')
h('2. Front-end và cấu hình baseline')
p('Trim30dB → pre-emphasis0,97 → MFCC13 (26mel, FFT512, Hamming25ms, hop10ms) → Δ13 + Δ²13 → T×39 → CMVN riêng từng utterance. Delta dùng hồi quy tối đa9frame, giảm cửa sổ nếu chuỗi ngắn. Kiểm tra shape và NaN/inf cho mọi file.')
p('Baseline đặt trước: 5state/từ, covariance diag, π=[1,0,0,0,0], self-loop0,7 và next-state0,3; state cuối self-loop1. Khởi tạo Gaussian theo5đoạn thời gian đều nhau. Fit truyền lengths để giữ ranh giới utterance. Cập nhật A, mean, covariance; giữ π cố định. Sau fit kiểm tra các cạnh cấm vẫn bằng0.')
p('Mã nguồn: Lab03.py. Dữ liệu: dataset/. Kiểm chứng: dataset_audit.csv, training_log.json. Heatmap MFCC/Δ/Δ² cho mở và xuống nằm trong results/figures/.','caption')

page('3. Huấn luyện và thí nghiệm E1–E3')
table(['Thí nghiệm / cấu hình','Train','Val','Test'],[[e['experiment']+' / '+e['config'],pct(e['train_accuracy']) if 'train_accuracy' in e else '—',pct(e['val_accuracy']),pct(e['test_accuracy'])] for e in S['experiments'] if 'test_accuracy' in e],[265,75,75,75])
p('E1: 3/5/7state đều đạt100% trên validation và test tổng hợp sạch. Quy tắc chọn theo validation, hòa thì chọn ít state hơn, trả về3state. Báo cáo vẫn giữ baseline5state đúng cấu hình sư phạm; không chọn tham số từ test. Điểm accuracy bão hòa nên chưa chứng minh7state tốt hơn hay3state bị underfit.')
p('E2: 13 và39chiều cùng đạt100%; chưa quan sát lớp nào cải thiện về accuracy khi thêm delta. Hai heatmap cho thấy chuyển tiếp phổ theo thời gian khác nhau giữa các từ, nhưng bằng chứng phân biệt phải dựa vào đánh giá, không chỉ hình ảnh.')
full=next(e for e in S['experiments'] if e['experiment']=='E3' and e['config'].startswith('full'))
diag=next(e for e in S['experiments'] if e['experiment']=='E3' and e['config']=='diag')
p(f"E3: score đúng lớp trung bình/frame của diag là {diag['mean_train_true_loglik_frame']:.2f} (train) và {diag['mean_test_true_loglik_frame']:.2f} (test); full là {full['mean_train_true_loglik_frame']:.2f} và {full['mean_test_true_loglik_frame']:.2f}. Full có khoảng cách train–test lớn hơn dù accuracy vẫn100%, gợi ý độ nhạy/khớp quá sát phân phối train. Đây chưa phải bằng chứng đầy đủ về khả năng khái quát hóa. Full dùng prior0,1I, weightD+1 để tránh suy biến.")
img('convergence.png',450)
p('Hình1. Lịch sử EM của5model baseline. Likelihood liên tục là mật độ nên log-likelihood có thể dương; không diễn giải như xác suất của một điểm.','caption')
status='; '.join(f"{r['label']}: {r['iterations']}vòng, {r['status']}" for r in S['training_statuses'])
p('Trạng thái dừng thực tế: '+status+'. Một số log có delta âm nhỏ; mã lưu nguyên cảnh báo và phân biệt giảm likelihood với hội tụ theo tolerance. Baum–Welch là tối ưu cục bộ; không đảm bảo nghiệm tốt nhất.')

page('4. Likelihood, Viterbi và đánh giá sạch')
rows=readcsv('scores_test.csv');sel=[next(r for r in rows if r['true']==l) for l in ['mo','dong','dung']]
table(['Test','mo','dong','len','xuong','dung'],[[Path(r['file']).name]+[f"{float(r[l]):.1f}" for l in ['mo','dong','len','xuong','dung']] for r in sel],[100,78,78,78,78,78])
p('Bảng1. Log-likelihood Forward của3test với5model; score lớn nhất quyết định nhãn. scores_test.csv chứa đầy đủ20mẫu và margin top1–top2/frame. Chia mọi score cho cùngT không đổi argmax trong một utterance.','caption')
p(f"Baseline đúng20/20mẫu sạch ({pct(S['test_accuracy'])}); mỗi lớp4mẫu. Mỗi lỗi tương ứng5điểm phần trăm, nên quy mô test này chưa cho ước lượng ổn định. Không chuyển likelihood thành phần trăm confidence.")
pair('cm_hmm.png','cm_dtw.png',210)
p('Hình2. Confusion matrix HMM39 và DTW13 trên cùng20mẫu test sạch.','caption')
pair('viterbi_mo.png','viterbi_xuong.png',235)
p('Hình3. Hai Viterbi path chỉ tự lặp hoặc tiến một state. Duration xấp xỉ số frame ở state×10ms; không mặc định state là một phoneme. Chi tiết từng state: state_durations.csv.','caption')
checks=S['forward_checks']
p('Kiểm chứng độc lập bằng logsumexp/DP: '+ '; '.join(f"{Path(c['file']).name}: Forward={c['forward_loglik']:.2f}, Viterbi={c['viterbi_logprob']:.2f}" for c in checks)+'. Cả likelihood, score Viterbi và toàn bộ path khớp thư viện; Forward không nhỏ hơn Viterbi.')

page('5. DTW, mismatch và unknown (E4–E5)')
table(['Mô hình','Sạch','Nhiễu15dB','Fit/template (s)','Score/test (ms)'],[[r['model'],pct(r['accuracy']),pct(r['noise_accuracy']),f"{r['fit_or_template_s']:.4f}",f"{r['test_score_ms']:.3f}"] for r in S['timing']],[95,65,85,125,120])
p('Đo một thread, median3lượt sau warmup; loại trừ trích đặc trưng. DTW chỉ lưu template nên thời gian dựng template không tương đương học tham số. Cả hai dùng cùng train/test; DTW13 so HMM39 phản ánh hai pipeline, chưa cô lập riêng thuật toán. E2 có HMM13 để đối chiếu. Với2/6/12train mỗi lớp, cả hai cùng100% trên test sạch; dữ liệu tổng hợp quá dễ để kết luận nhu cầu mẫu.')
pair('cm_noise.png','score_distribution.png',225)
p('Hình4. HMM trên test nhiễu và phân bố score/frame của đúng lớp/sai lớp trên test sạch. “Sai lớp” là4model không khớp nhãn cho mỗi utterance, không phải các mẫu bị dự đoán sai.','caption')
p('Ví dụ dong_01.wav khi thêm nhiễu: HMM dự đoán xuống, DTW dự đoán đúng đóng. HMM giảm100%→20% (80điểm phần trăm), DTW giảm100%→60% (40điểm). Nhiễu nền có thể khiến trim giữ nhiều frame silence hơn, đồng thời làm biến dạng phổ và delta; Gaussian học từ âm sạch trở nên không phù hợp. Đây là giải thích khả dĩ, chưa có ablation tách riêng lỗi endpoint khỏi lỗi acoustic.')
p('Dữ liệu noisy được tạo từ test sạch, không đưa vào fit. Nhiễu trắng15dB là một phép stress có kiểm soát, không đại diện mọi tiếng ồn ngoài đời. Chưa thực hiện speaker-independent vì không có người nói thật.')
r=S['reject']
p(f"Unknown: chọn τ={r['threshold']:.2f} trên maximum log-likelihood/frame bằng validation known20 + OOV4. Với test sạch, false reject={pct(r['known_test_false_reject'])}; OOV test khác nội dung được reject4/4. Mẫu quá nhỏ, đều là TTS; chưa đủ để xem threshold này là hiệu chỉnh cho triển khai thực tế.")
p('Hướng cải thiện: thu giọng thật đa dạng, bổ sung noise augmentation chỉ ở train, kiểm tra VAD tốt hơn, tune trên validation và mở rộng OOV. Không dùng kết quả test để điều chỉnh rồi tiếp tục báo cáo như test độc lập.')

page('6. Lexicon và bigram re-ranking (E6)')
p('<b>Lexicon:</b> file lexicon.txt theo WORD PHONE_1…PHONE_K, parser xuất dict và kiểm tra thiếu/trùng từ. Bộ ký hiệu là quy ước minh họa tự soạn có token thanh điệu, chưa phải inventory giảng viên. Whole-word model hiện tại không phụ thuộc lexicon; không huấn luyện phone HMM. Khi có model phone, nối chúng theo thứ tự lexicon để tạo model từ và xử lý transition ở ranh giới.')
p('<b>Corpus:</b> 24chuỗi lệnh mô phỏng. Đếm unigram, bigram và context có successor; add-k=0,5. P(w|prev)=(C(prev,w)+0,5)/(C_out(prev)+0,5×5). Không mô hình EOS; dùng C_out thay vì unigram ở mẫu số để hàng xác suất tổng bằng1. Corpus cũng chưa phải dữ liệu giảng viên cung cấp.')
probe=json.loads((R/'results/probe_metadata.json').read_text())
p(f"<b>Utterance mơ hồ:</b> tạo probe từ {probe['parent']} bằng nhiễu {probe['snr_db']:.2f}dB. Quét mức nhiễu trên validation chỉ để tìm ví dụ có margin nhỏ; không dùng probe để fit, chọn threshold hoặc tính accuracy. Hai acoustic candidate đầu cách {probe['margin_frame']:.4f} log-unit/frame. Nhãn gốc {probe['true']}, acoustic dự đoán {probe['pred']}.")
p('Score tổng = logP(X|w)/T + λLM×logP(w|previous). Previous-word là giả định để khảo sát độ nhạy, không phải ngữ cảnh thực thu. Thử0;0,1;0,3;1 và thêm3;10;30;100 để quan sát giới hạn LM quá mạnh.')
lm=readcsv('lm_rerank.csv');changes=readcsv('lm_changes.csv');probe_changes=[r for r in changes if 'probe' in r['file']]
fixed=[r for r in probe_changes if r['effect']=='corrected']
prev=fixed[0]['previous'] if fixed else (probe_changes[0]['previous'] if probe_changes else 'mo')
chosen=[r for r in lm if r['previous']==prev and float(r['lambda_lm']) in [0,.1,.3,1,10,100]]
table([f'Previous={prev}','0','0,1','0,3','1','10','100'],[['Dự đoán']+[r['pred'] for r in chosen]],[130,60,60,60,60,60,60])
cor=[r for r in changes if r['effect']=='corrected'];harm=[r for r in changes if r['effect']=='harmed']
if cor:
    c=cor[0];p(f"Ví dụ LM sửa lỗi trong phép thử ngữ cảnh giả định: {Path(c['file']).name}, previous={c['previous']}, λ={c['lambda_lm']}: {c['old']}→{c['new']} (nhãn {c['true']}). Không coi đây là mức cải thiện accuracy trên một corpus tiếng nói liên tục.")
else:p('Không quan sát trường hợp sửa lỗi trong các ngữ cảnh/λ đã thử. Báo cáo giữ nguyên kết quả, không tạo số liệu cải thiện giả.')
if harm:
    c=harm[0];p(f"Ví dụ LM gây lỗi: {Path(c['file']).name}, previous={c['previous']}, λ={c['lambda_lm']}: {c['old']}→{c['new']} dù nhãn đúng là {c['true']}. Prior mạnh và context không phù hợp có thể lấn át bằng chứng âm học.")
img('lm_sensitivity.png',430)
p('Hình5. Độ nhạy score theo λ, minh họa riêng previous=mo. Đây chỉ là re-ranking từ tách rời; chưa tìm đồng thời word boundaries và chuỗi từ.','caption')

page('7. Trả lời câu hỏi và kết luận')
answers=[
('Forward/Viterbi','Forward dùng tổng (logsumexp ở miền log) trên mọi đường; Viterbi dùng max và backtrack để tìm đường trạng thái tốt nhất.'),
('γ và ξ','γ là trách nhiệm của state với frame; ξ là trách nhiệm cạnh i→j giữa hai frame. E-step tính kỳ vọng; M-step cập nhật tham số từ các trách nhiệm này.'),
('Nghiệm xấu của EM','Khởi tạo không tốt, quá ít dữ liệu, quá nhiều state, covariance suy biến, silence/nhiễu và mất cân bằng đều có thể gây nghiệm xấu. EM chỉ tối ưu cục bộ.'),
('Diag so với full','D=39: diag có39 phương sai/state, full có780 phần tử độc lập. Full cần nhiều dữ liệu hơn; kể cả nhiều frame, các frame gần nhau vẫn tương quan.'),
('Vai trò delta','Transition mô tả chuỗi state; delta đưa xu hướng phổ lân cận vào emission ở mỗi frame. Thêm chiều không bảo đảm tăng accuracy.'),
('Lexicon','Whole-word5lệnh không cần lexicon để fit. Phone/subword HMM cần ánh xạ từ sang đơn vị phát âm hoặc cơ chế tương đương khi tạo model/mạng từ.'),
('Nói chậm','Self-loop cho phép lưu lại state nhiều frame. Duration là mô hình ngầm đơn giản; state cuối self-loop1 không tự quyết định thời điểm kết thúc.'),
('Chuẩn hóa theoT','Cùng utterance thìT không đổi giữa model, argmax giữ nguyên. Score/frame hữu ích cho threshold; khi cộng LM, cần tune λ theo thang điểm đã chọn.'),
('Hai kiểu alignment','DTW căn chỉnh frame với template bằng chi phí khoảng cách; Viterbi căn frame với state học từ nhiều mẫu bằng xác suất. Cả hai dùng quy hoạch động.'),
('Unknown','Argmax luôn chọn một lớp trong vocabulary. Reject theo max-score/frame hoặc margin; chọn ngưỡng bằng validation có OOV, đánh giá false accept/reject riêng.')]
for i,(a,b) in enumerate(answers,1):p(f'<b>{i}. {a}.</b> {b}')
h('Kết luận và phạm vi hoàn thành')
p('Đã chạy A–H, E1–E6; lưu5model, bảng likelihood20mẫu, heatmap, confusion matrices,2Viterbi paths, so sánh DTW và thí nghiệm LM. Kết quả sạch bão hòa100% nhưng mismatch giảm mạnh, cho thấy dữ liệu TTS không đủ để kết luận tính ứng dụng. Cần thay giọng thật và lexicon/corpus chuẩn nếu giảng viên yêu cầu. Bản giải thích10câu đầy đủ nằm trong CAU_HOI_BAO_CAO.md.')
h('Nguồn và cách tái lập')
p('Đề CSE457 Lab3 (11trang) do người dùng cung cấp; hmmlearn API/tutorial: https://hmmlearn.readthedocs.io/en/stable/ ; eSpeak NG: https://github.com/espeak-ng/espeak-ng . Công thức và yêu cầu theo đề; số liệu do mã chạy trên bộ synthetic kèm theo.','small')
p('Chạy: python -m pip install -r requirements.txt → python Lab03.py → python build_report.py. Không cần eSpeak khi dùng WAV có sẵn. Seed generator20261019, probe901; phiên bản thư viện ghi trong requirements.txt/summary.json. README và DOI_CHIEU_YEU_CAU.md hướng dẫn đầy đủ.','small')

def footer(canvas,doc):
    canvas.saveState();canvas.setStrokeColor(colors.HexColor('#CCD9E2'));canvas.line(42,40,553,40);canvas.setFont('DV',7);canvas.setFillColor(colors.HexColor('#536B7C'));canvas.drawString(42,27,'CSE457 • LAB03 | DỮ LIỆU GIỌNG TỔNG HỢP');canvas.drawRightString(553,27,f'{doc.page} / 6');canvas.restoreState()
doc=SimpleDocTemplate(str(R/'Bao_cao_Lab03.pdf'),pagesize=(595.28,841.89),rightMargin=48,leftMargin=48,topMargin=38,bottomMargin=52,title='Lab03 - Gaussian HMM - Du lieu tong hop',author='Bao cao thuc nghiem')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print('Created',R/'Bao_cao_Lab03.pdf')
