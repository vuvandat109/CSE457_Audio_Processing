"""Build an 8-page Vietnamese report from actual measured CSV/JSON files."""
import sys,csv,json,html,statistics
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.common import ROOT, SR, SENTENCES
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

def main():
    font_dir=Path('/usr/share/fonts/truetype/dejavu')
    if not font_dir.exists():
        import matplotlib
        font_dir=Path(matplotlib.get_data_path())/'fonts'/'ttf'
    for name,file in [('DV','DejaVuSans.ttf'),('DVB','DejaVuSans-Bold.ttf')]:
        pdfmetrics.registerFont(TTFont(name,str(font_dir/file)))
    pdfmetrics.registerFontFamily('DV',normal='DV',bold='DVB',italic='DV',boldItalic='DVB')
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='TextVN',fontName='DV',fontSize=9.1,leading=13.4,spaceAfter=7))
    styles.add(ParagraphStyle(name='TitleVN',fontName='DVB',fontSize=20,leading=26,textColor=colors.HexColor('#173e60'),spaceAfter=10))
    styles.add(ParagraphStyle(name='HeadingVN',fontName='DVB',fontSize=13,leading=18,spaceBefore=8,spaceAfter=8,textColor=colors.HexColor('#173e60')))
    styles.add(ParagraphStyle(name='SmallVN',fontName='DV',fontSize=7.4,leading=10,spaceAfter=5))
    styles.add(ParagraphStyle(name='EqVN',fontName='DV',fontSize=9,leading=14,backColor=colors.HexColor('#eef3f8'),borderPadding=6,spaceBefore=3,spaceAfter=10))
    story=[]
    def p(text,style='TextVN'):story.append(Paragraph(text,styles[style]))
    def h(text):p(text,'HeadingVN')
    def equation(text):p(html.escape(text).replace('\n','<br/>'),'EqVN')
    def image(name,width=505):
        path=ROOT/'figures'/name;i=ImageReader(str(path));w,hh=i.getSize()
        story.append(Image(str(path),width=width,height=width*hh/w));story.append(Spacer(1,5))
    def table(rows,widths=None):
        cells=[[Paragraph(html.escape(str(x)),styles['SmallVN']) for x in row] for row in rows]
        t=Table(cells,colWidths=widths or [505/len(rows[0])]*len(rows[0]),repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e5eef5')),('VALIGN',(0,0),(-1,-1),'TOP'),
          ('GRID',(0,0),(-1,-1),.4,colors.HexColor('#c7d1da')),('LEFTPADDING',(0,0),(-1,-1),6),
          ('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
        story.append(t);story.append(Spacer(1,8))
    def page():story.append(PageBreak())
    def csvrows(name):return list(csv.DictReader((ROOT/'results'/name).open(encoding='utf-8-sig')))
    meta=list(csv.DictReader((ROOT/'data'/'metadata.csv').open(encoding='utf-8-sig')))
    cost=csvrows('unit_selection_costs.csv');xf=csvrows('crossfade_metrics.csv');lat=csvrows('latency.csv')
    f0=json.loads((ROOT/'results'/'f0_check.json').read_text(encoding='utf-8'))
    env=json.loads((ROOT/'results'/'environment.json').read_text(encoding='utf-8'))
    verify=json.loads((ROOT/'results'/'verification.json').read_text(encoding='utf-8'))

    p('LAB 04 | TỔNG HỢP TIẾNG NÓI','TitleVN')
    p('<b>CSE457 - Trường Đại học Thủy Lợi</b><br/>Sinh viên: Vũ Văn Đạt | Chủ đề: Mini TTS thông báo xếp hàng')
    h('1. Mục tiêu, phạm vi và dữ liệu')
    p('Xây dựng pipeline text normalization → word-unit → prosody → backend → waveform; so sánh ghép nối, Gaussian HMM và neural Piper/VITS. Cùng ba câu test, mỗi câu được sinh bằng hai giọng nam/nữ. Không huấn luyện neural TTS từ đầu.')
    p('<b>Nguồn âm thanh:</b> 64 unit tổng hợp bằng neural Piper/VITS: 16 nhãn × 2 candidate × 2 giọng thiết kế (nam diemdam, nữ altotram). Đây <b>không phải bản thu microphone của người thật</b>; không bảo đảm không thể phân biệt với giọng người. Nếu giảng viên yêu cầu tự thu, phải thay inventory bằng bản thu có đồng ý sử dụng.')
    table([['Thuộc tính','Cấu hình / kết quả'],['Inventory','16 nhãn; 32 WAV/giọng; tổng 64 WAV'],['Định dạng','Mono, 16 kHz, PCM 16-bit'],['Duration unit',f"{min(float(r['duration_s']) for r in meta):.3f}–{max(float(r['duration_s']) for r in meta):.3f} s"],['Chuẩn hóa','Bỏ DC, trim năng lượng với context 15 ms; RMS mục tiêu 0.08, peak ≤0.97']], [105,400])
    image('01_inventory_stats.png')
    h('2. Chuẩn hóa văn bản')
    p('Unicode NFC, lowercase, bỏ dấu câu, tách token. Mã số đọc từng chữ số và giữ số 0 đầu: 023 → không hai ba. Câu “Mời khách hàng số 23 đến quầy 5” thành 9 token: mời / khách / hàng / số / hai / ba / đến / quầy / năm. Token ngoài miền được báo lỗi.')
    equation('d = N/Fs; RMS = sqrt(mean(x[n]^2)); y[n] = g*x[n]')
    p('N là số mẫu, Fs là mẫu/giây; 4800/16000 = 0.3 s. Gain g hướng tới RMS 0.08 nhưng bị giới hạn bởi peak. Histogram RMS gần một mức là hệ quả có chủ đích của normalization. Metadata giữ nhãn, speaker, duration, RMS, candidate, đường dẫn và nguồn.', 'SmallVN')
    page()

    h('3. Ghép nối cơ bản và chọn chuỗi unit')
    p('Baseline luôn lấy candidate 1 và nối trực tiếp; lưu raw_concat.wav. Bản cải tiến chọn candidate bằng dynamic programming rồi cross-fade 15 ms; lưu best_concat.wav. Có các bản riêng theo giọng/câu. Không trộn nam và nữ trong cùng một câu.')
    h('3.1. Target cost và join cost')
    equation('Ct = ((d-d_ref)/0.05)^2 + ((R-0.08)/0.02)^2')
    p('d_ref là duration candidate 1 của cùng nhãn; 0.05 s và 0.02 là thang chuẩn hóa thiết kế, không phải phương sai đo. Ví dụ minh họa d=0.35 s, d_ref=0.30 s, R=0.09: Ct=1²+0.5²=1.25. Do chuẩn hóa RMS, thành phần duration chi phối target trong bộ dữ liệu này.')
    equation('L[k] = 20*log10(max(abs(FFT(x*w))[k], 1e-8))\nCjoin = mean_k((L_left[k]-L_right[k])^2)')
    p('Mỗi biên lấy 25 ms = 400 mẫu, cửa sổ Hann, FFT 512, 257 bin không âm. Join cost là MSE log-spectrum (dB²). Ví dụ minh họa hai vector [-20,-30,-40] và [-22,-29,-35] cho (4+1+25)/3=10 dB². Không coi cost này là điểm naturalness.')
    equation('Ctotal = sum(Ct) + 0.02*sum(Cjoin)\nDj(k) = Ct(j,k) + min_i[D(j-1,i) + 0.02*Cjoin(i,k)]')
    p('Khởi tạo D1=Ct; lưu argmin ở từng bước rồi truy vết từ candidate cuối có cost nhỏ nhất. Với J token và M candidate, DP có O(JM²); vét cạn O(M^J). Kiểm tra độc lập đã vét cạn đủ 2^9 đường/câu 1 cho hai giọng và xác nhận cùng nghiệm tối ưu.')
    h('3.2. Kết quả thực tế - câu 1')
    rows=[['Giọng / phương pháp','Target','Join','Tổng']]
    for r in cost:
        if r['sentence_id']=='1':rows.append([f"{r['voice']} / {'fixed' if r['method']=='fixed_candidate' else 'DP'}",f"{float(r['target_cost']):.3f}",f"{float(r['join_cost']):.2f}",f"{float(r['total_cost']):.2f}"])
    table(rows,[205,85,110,105])
    for v in ('male','female'):
        r=[x for x in cost if x['voice']==v and x['sentence_id']=='1'];a=float(r[0]['total_cost']);b=float(r[1]['total_cost'])
        p(f"{v}: tổng cost giảm {(a-b)/a*100:.2f}%. DP chấp nhận một phần lệch duration để đổi lấy đường nối có chi phí thấp hơn. Đây là kết quả hàm mục tiêu, chưa chứng minh MOS tăng.")
    p('Đường candidate cụ thể và kết quả cả ba câu có trong results/unit_selection_costs.csv. Không chọn độc lập từng từ theo target cost vì có thể làm join toàn câu xấu đi.', 'SmallVN')
    page()

    h('4. Cross-fade, waveform và biên ghép')
    equation('y[n] = (1-alpha[n])*a_tail[n] + alpha[n]*b_head[n]\nalpha[n] = n/(N-1); N = Fs*t_ms/1000')
    p('Ở 16 kHz, 0/5/15/30 ms tương ứng 0/80/240/480 mẫu. Ví dụ alpha=.25, a=.8, b=.4 → y=.7. Với 9 unit, cross-fade 15 ms rút ngắn tổng 8×.015=.12 s. Không cộng lại phần overlap hai lần.')
    image('02_waveform_spectrogram.png',480)
    p('Hình trên: vạch đỏ/cyan là biên unit. Baseline so với DP+15 ms thay cả candidate lẫn smoothing. Hình 03 và 09 trong gói phóng to ít nhất hai biên; hình 09 giữ cùng chuỗi DP để tách riêng ảnh hưởng cross-fade.', 'SmallVN')
    table([['Nữ, câu 1','Jump một mẫu','Spectral MSE (dB²)']]+[[f"{r['crossfade_ms']} ms",f"{float(r['mean_sample_jump']):.6f}",f"{float(r['spectral_mismatch']):.2f}"] for r in xf if r['voice']=='female' and r['sentence_id']=='1'],[140,170,195])
    p('Các proxy không giảm đơn điệu: thay vùng overlap cũng thay nội dung phổ quanh tâm biên. 15 ms là cấu hình minh họa, chưa kết luận tốt nhất theo người nghe. Cross-fade dài có thể che burst/phụ âm; cần nghe mù các WAV 0/5/15/30 ms trước khi chọn cuối cùng.')
    page()

    h('5. Prosody và source–filter')
    equation('F0 = Fs/Np; pitch_ratio = 2^(semitone/12)\nTout = Tin/speed; X(z) = E(z)H(z)')
    p(f"Trên unit nữ ‘mời’, pYIN ước lượng F0={f0['pyin_f0_hz']:.2f} Hz; tự tương quan quanh chu kỳ dự đoán tìm Np={f0['period_samples']} mẫu. Fs/Np=16000/{f0['period_samples']}={f0['fs_over_period_hz']:.2f} Hz; lệch tương đối {f0['relative_difference_pct']:.2f}%. Đây là kiểm tra nhất quán cục bộ, không phải đo ground truth độc lập.")
    p('Speed .8/1/1.2 dùng phase vocoder của librosa, cố giữ pitch; speed>1 làm câu ngắn. Pitch -2/0/+2 semitone dùng WORLD: giữ spectral envelope và aperiodicity, nhân F0 với 0.8909/1/1.1225. Ví dụ F0=160 Hz thành 142.54/160/179.59 Hz. Không gọi các thí nghiệm này là cài đặt TD-PSOLA hoặc WSOLA.')
    image('07_prosody.png',505)
    p('Nguồn E biểu diễn rung dây thanh/nhiễu; H biểu diễn cộng hưởng đường thanh. F0 quyết định khoảng harmonic, formant liên quan đỉnh của envelope. Đổi F0 không bắt buộc dịch mọi formant. Đổi tốc độ phát file đơn thuần sẽ đổi cả thời lượng và toàn phổ, có thể tạo âm sắc “chipmunk”. WORLD cũng có artifact do phân tích/vocoder, nhất là vùng vô thanh và thanh điệu khó.')
    h('Kiểm tra và diễn giải')
    p('Đọc results/prosody.csv để đối chiếu duration; nghe WAV speed và pitch trong experiments. Hình 08 chỉ rõ gần năm chu kỳ trên waveform. Đánh giá nội dung số phải ưu tiên hơn cảm giác dễ chịu. Không suy ra intelligibility từ việc các dải phổ trông tương tự.')
    page()

    h('6. HMM chạy ở chế độ generation')
    p('Mỗi từ có 5 state trái-sang-phải; hai candidate được căn chỉnh bằng chia đều thời gian. WORLD phân tích mỗi 10 ms: continuous log-F0, log spectral envelope, aperiodicity; voiced probability được học riêng. Mỗi state lưu Gaussian mean/variance của static và delta, duration trung bình và self-loop. Đây là supervised demo, không phải huấn luyện Baum-Welch/HTS đầy đủ.')
    equation('a_self = 1 - 1/mean_duration_frames\nO* = argmax_O P(O | Gaussian states, state sequence)')
    p('Chuỗi token xác định chuỗi state. Demo dùng kỳ vọng thời lượng geometric 1/(1-a_self), làm tròn theo frame; không gọi kỳ vọng là mode. Inference chỉ dùng thống kê tham số, không lấy lại waveform candidate.')
    equation('J(c) = sum((c-mu)^2/v) + sum((D*c-mu_delta)^2/v_delta)\nD*c[t] = c[t]-c[t-1], t >= 1')
    p('Đạo hàm J bằng 0 cho hệ ba đường chéo: [diag(1/v)+Dᵀdiag(1/v_delta)D]c=mu/v+Dᵀ(mu_delta/v_delta). Bộ giải sinh một trajectory thống nhất giữa static và delta, rồi WORLD phát waveform. Variance floor=0.001 tránh chia 0. Delta ràng buộc các frame lân cận, giảm nhảy state nhưng vẫn có thể oversmooth.')
    image('05_hmm_tracks.png',490)
    p('Track phổ tại 1 kHz là log-power envelope, không phải F1. Đường mean state và đường generation được vẽ cùng nhau. Thử duration .8/1.2 và F0 .9/1.1 có WAV riêng; scaling duration đổi số frame, scaling F0 chỉ nhân các frame voiced. Dữ liệu ít và thiếu context làm HMM còn có thể robotic.', 'SmallVN')
    page()

    h('7. Neural TTS offline và so sánh khách quan')
    p('Piper/VITS ONNX: text chuẩn hóa → eSpeak NG phonemization → VITS latent/acoustic generation + neural waveform decoder. Đây là kiến trúc tích hợp, không giả định model trả mel intermediate. Mel 80 bin lưu trong results được <b>tính lại từ waveform đầu ra</b> bằng librosa, không gọi là mel nội bộ model.')
    p('Hai model riêng (22,050 Hz gốc) được resample về 16 kHz; model card và revision khóa trong models/manifest.json. Không gọi API online, không fallback phát audio có sẵn. Kiểm tra socket-block xác nhận cả hai giọng vẫn sinh được câu.')
    rows=[['Giọng / backend','Latency warm TB (ms)','RTF TB']]
    for v in ('male','female'):
        for b in ('concat','hmm','neural'):
            rs=[r for r in lat if r['voice']==v and r['backend']==b]
            rows.append([f'{v} / {b}',f"{statistics.mean(float(r['latency_s']) for r in rs)*1000:.2f}",f"{statistics.mean(float(r['rtf']) for r in rs):.4f}"])
    table(rows,[190,180,135])
    p('54 phép đo: 3 lần warm × 3 câu × 2 giọng × 3 backend. Đo text-to-array gồm generation và hậu xử lý, loại model load và I/O WAV. Inventory được nạp sẵn; HMM đọc model tham số trong mỗi call. Thời gian load neural được lưu riêng. Latency này phụ thuộc máy, không phải cam kết tốc độ máy người học.', 'SmallVN')
    rows=[['Backend','Dữ liệu/model (xấp xỉ)','Naturalness / intelligibility']]
    units=sum(p.stat().st_size for p in (ROOT/'data'/'units').glob('*.wav'))/1024**2
    hm=sum(p.stat().st_size for p in (ROOT/'data'/'hmm_demo').glob('*.npz'))/1024**2
    rows.extend([['Concat',f'{units:.2f} MiB inventory, 2 giọng','Chờ người nghe thật'],['HMM',f'{hm:.2f} MiB tham số, 2 giọng','Chờ người nghe thật'],['Neural','121.15 MiB ONNX, 2 giọng; chưa tính runtime','Chờ người nghe thật']])
    table(rows,[75,235,195])
    image('06_backend_comparison.png',300)
    p(f"Môi trường: Python {env['python']}, ONNX CPU 2 thread/model; các version đầy đủ ở environment.json. Cùng nguồn neural dùng tạo unit và HMM nên so sánh bị phụ thuộc nguồn, không đại diện benchmark corpus người thật.", 'SmallVN')
    page()

    h('8. Thiết kế nghe thử và trả lời câu hỏi 1–5')
    equation('MOS = sum(rating)/K; rating thuộc {1,2,3,4,5}\nIntelligibility (%) = 100*N_correct/N_total')
    p('<b>Chưa thu điểm người nghe.</b> Phiếu listening_test.html che nhãn backend, xáo trộn 26 clip: 18 clip backend (3 câu × 2 giọng × 3 backend) và 8 clip cross-fade câu 1 (4 mức × 2 giọng, cùng candidate). Mời 5–10 người, tai nghe, phòng yên tĩnh, chép lời trước khi biết câu gốc, chấm tự nhiên/liền mạch riêng. ratings.csv chỉ có header, không có điểm giả.')
    p('Script evaluate_ratings.py tổng hợp CSV thật, tính MOS theo backend/giọng và word accuracy từ edit distance S/D/I. Không xem nhiều clip của cùng một người là các người nghe độc lập. Bảng đánh giá chủ quan cần cập nhật sau thí nghiệm. Đánh giá khách quan hiện có không thay thế phép nghe này.')
    h('Câu 1. Đoạn tự nhiên nhưng câu ghép kém tự nhiên?')
    p('Mỗi đoạn có pitch, energy, pha và context riêng. Khi ghép, các chuyển tiếp thiếu coarticulation và đường ngữ điệu toàn câu; âm lượng/phổ có thể nhảy. Làm mượt biên không tự tạo được prosody đúng. Trong bài này unit còn là giọng tổng hợp, phải ghi đúng nguồn.')
    h('Câu 2. Target cost và join cost khác nhau?')
    p('Target đo phù hợp candidate với duration/RMS/context mục tiêu; join đo độ tương thích ở hai đầu. Chỉ tối ưu join có thể chọn duration/ngữ điệu sai, thậm chí ưu tiên vùng rất nhỏ tiếng. Cần cân bằng hai cost và tìm chuỗi toàn cục.')
    h('Câu 3. Cross-fade quá dài làm mờ phụ âm?')
    p('Burst và chuyển tiếp của phụ âm thường ngắn; pha trộn quá dài có thể che burst, suy giảm phụ âm yếu và rút nhịp. Vì vậy phải thử 0/5/15/30 ms, nghe cùng chuỗi candidate thay vì mặc định overlap dài hơn luôn tốt hơn.')
    h('Câu 4. F0 và formant?')
    p('F0 gắn với chu kỳ nguồn, formant gắn với cộng hưởng đường thanh. Cùng một nguyên âm có thể phát ở nhiều cao độ. Đổi cả phổ bằng sample-rate playback thay cả source và filter; nguồn–lọc giúp giải thích vì sao cần tách chúng.')
    h('Câu 5. PSOLA và buzziness?')
    p('PSOLA nhân cửa sổ quanh pitch epoch rồi đặt lại ở synthesis epoch. Epoch gần hơn làm pitch cao; xa hơn làm pitch thấp. Lặp/drop frame đổi duration. Voiced fricative có thành phần noise; lặp noise theo nhịp đều tạo tuần hoàn giả, gây buzzy. Epoch sai còn tạo sai pha.')
    page()

    h('9. Trả lời câu hỏi 6–10 và kết luận')
    h('Câu 6. Delta giúp HMM trơn như thế nào?')
    p('Delta ràng buộc biến thiên giữa frame. Generation tối ưu static và dynamic đồng thời, tránh chọn mean state từng frame độc lập. Chỉ thêm cột delta mà không đưa vào nghiệm likelihood không bảo đảm trơn. Trơn quá mức cũng có thể làm mất động học tiếng nói.')
    h('Câu 7. Vì sao cần inventory lớn?')
    p('Một từ/phone có nhiều hiện thực theo context trước/sau, vị trí câu, trọng âm, pitch và tốc độ. Nhiều candidate giúp tìm đoạn gần mục tiêu hơn và giảm sửa tín hiệu. Đổi lại tăng dung lượng, công gán nhãn và chi phí tìm kiếm. Hai candidate trong Lab chỉ đủ minh họa.')
    h('Câu 8. Concatenative và neural khác nhau?')
    p('Concatenative chọn/phát waveform có sẵn; neural học ánh xạ text/phoneme sang latent/acoustic representation và waveform. Hệ ghép phụ thuộc độ phủ context, dễ lộ biên; neural phụ thuộc model/dữ liệu và có thể phát âm sai, bỏ/lặp từ hoặc tạo artifact. Tài nguyên/latency phải đo, không kết luận phổ quát.')
    h('Câu 9. Vì sao không tải model tùy ý trong giờ Lab?')
    p('Khác model/ngôn ngữ/version/speaker/device làm so sánh thiếu kiểm soát. Download lẫn vào latency và phụ thuộc mạng. Cần chuẩn bị offline trước, giữ config, revision và hash; kiểm tra quyền sử dụng. Gói này đã chứa model parts, không tải model khi chạy inference.')
    h('Câu 10. MOS cao nhưng intelligibility thấp dùng ở đâu?')
    p('Nếu MOS hỏi độ tự nhiên, giọng dễ chịu vẫn có thể đọc sai. Không phù hợp xếp hàng, trợ năng đọc hay thông báo an toàn. Chỉ có thể cân nhắc hiệu ứng giọng/lời giả nền không mang thông tin quan trọng, với người dùng biết giới hạn. Ứng dụng của Lab phải ưu tiên đúng mã số/quầy.')
    h('Kết luận và phần cần hoàn tất bằng người thật')
    p(f"Pipeline đã sinh {verify['wav_count']} WAV hợp lệ (gồm inventory và kết quả), 9 hình, model HMM/ONNX, cost/latency thực tế; DP đã khớp vét cạn, inference neural đã qua kiểm tra chặn mạng. Các kết quả khách quan hỗ trợ phân tích, chưa chứng nhận naturalness giống người hoặc mức nghe đúng. Cần thu lượt nghe thật, cập nhật bảng MOS/intelligibility trước khi nộp bản đánh giá hoàn chỉnh; thay inventory nếu môn học bắt buộc người thu thực.")
    h('Tài liệu và tính tái lập')
    p('[1] Đề Lab 4 CSE457, tài liệu người học cung cấp. [2] Huang, Acero & Hon (2001), Spoken Language Processing, Ch.14–16. [3] Rabiner & Schafer (2010), Theory and Applications of Digital Speech Processing. [4] Piper: github.com/OHF-Voice/piper1-gpl. [5] Model card: huggingface.co/vnhellboy/vietnamese-piper-voices, revision df2a53e0b5c8039d17e642cc8d80fa03d59374b7. [6] PyWORLD/WORLD, GitHub JeremyCCHsu và mmorise. [7] librosa 0.11.0 documentation.', 'SmallVN')
    p('Model card ghi license other, lineage có dữ liệu research-only; không tuyên bố trọng số dùng thương mại tự do. Code, công thức chi tiết, đáp án đầy đủ, môi trường, SHA-256 và hướng dẫn GitHub có trong gói. Tính ngẫu nhiên của neural generation có thể làm waveform khác khi chạy lại.', 'SmallVN')

    def footer(c,doc):
        c.setStrokeColor(colors.HexColor('#ced9e3'));c.line(42,38,553,38)
        c.setFont('DV',8);c.setFillColor(colors.HexColor('#50667a'))
        c.drawString(42,25,'CSE457 | Lab 04 - Mini TTS | Vũ Văn Đạt')
        c.drawRightString(553,25,f'Trang {doc.page}')
    path=ROOT/'report'/'Bao_cao_Lab04.pdf'
    doc=SimpleDocTemplate(str(path),pagesize=(595.28,841.89),rightMargin=42,leftMargin=42,
                          topMargin=35,bottomMargin=48,title='Lab 04 - Tổng hợp tiếng nói',author='Vũ Văn Đạt')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    print(path)

if __name__=='__main__':main()
