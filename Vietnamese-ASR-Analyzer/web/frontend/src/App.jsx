import { useEffect, useMemo, useRef, useState } from "react";



import axios from "axios";



import {



  Bar,



  BarChart,



  Cell,



  ResponsiveContainer,



  Tooltip,



  XAxis,



  YAxis



} from "recharts";



import "./App.css";







// =====================================================



// CONFIG



// =====================================================



const API = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";







// =====================================================



// LABELS & THEME



// =====================================================



const ERROR_LABELS = {



  tone_error: "Sai thanh điệu",



  nucleus_error: "Sai âm chính",



  initial_consonant_error: "Sai phụ âm đầu",



  final_consonant_error: "Sai âm cuối",



  missing_word: "Mất từ",



  merge_word: "Gộp từ",



  split_word: "Tách từ",



  extra_word: "Thêm từ"



};







const STATUS_LABEL = {



  correct: "✓ Đúng",



  incorrect: "✗ Sai",



  failed: "⚠ Lỗi"



};







const STATUS_CLASS = {



  correct: "status-correct",



  incorrect: "status-incorrect",



  failed: "status-failed"



};







const CHART_COLORS = [



  "#0f5c63",



  "#c62845",



  "#ca8a04",



  "#16824b",



  "#7c3aed",



  "#2563eb",



  "#d97706",



  "#059669"



];







// =====================================================



// HELPERS



// =====================================================



function translateError(value) {



  return ERROR_LABELS[value] ?? value;



}







function percent(value) {



  if (value === null || value === undefined || value === "") return "-";



  const number = Number(value);



  if (!Number.isFinite(number)) return "-";



  return (number * 100).toFixed(2) + "%";



}







function isLikelyHallucination(item) {
  if (!item) return false;

  const wer = Number(item.wer);
  const reference = String(
    item.ground_truth ?? item.reference ?? item.cau_chuan ?? ""
  ).trim();
  const prediction = String(
    item.prediction ?? item.whisper ?? item.whisper_text ?? ""
  ).trim();

  const refWords = reference ? reference.split(/\s+/).length : 0;
  const predWords = prediction ? prediction.split(/\s+/).length : 0;

  if (Number.isFinite(wer) && wer > 1) return true;

  return (
    refWords > 0 &&
    predWords >= refWords * 3 &&
    predWords - refWords >= 5
  );
}



function getStatus(item) {



  if (item?.status === "Đúng" || item?.status === "correct") return "correct";



  if (item?.status === "Sai" || item?.status === "incorrect") return "incorrect";



  if (item?.status === "Lỗi" || item?.status === "failed") return "failed";



  if (Array.isArray(item?.errors) && item.errors.length > 0) return "incorrect";



  return "correct";



}



function renderWordDiff(words, side) {
  if (!Array.isArray(words) || words.length === 0) {
    return null;
  }

  return (
    <span
      style={{
        display: "flex",
        flexWrap: "wrap",
        gap: "6px",
        alignItems: "center",
        lineHeight: 1.9
      }}
    >
      {words.map((word, index) => {
        const ref =
          word?.reference === null || word?.reference === undefined
            ? ""
            : String(word.reference).trim();

        const pred =
          word?.prediction === null || word?.prediction === undefined
            ? ""
            : String(word.prediction).trim();

        const isInsertion = !ref && !!pred;
        const isDeletion = !!ref && !pred;
        const isSubstitution = !!ref && !!pred && ref !== pred;
        const isEqual = !!ref && !!pred && ref === pred;

        const value = side === "reference" ? ref : pred;

        if (!value) {
          return null;
        }

        let background = "rgba(34, 197, 94, 0.12)";
        let border = "rgba(34, 197, 94, 0.28)";
        let color = "#15803d";
        let title = "Đúng";

        if (isSubstitution) {
          background = "rgba(245, 158, 11, 0.14)";
          border = "rgba(245, 158, 11, 0.34)";
          color = "#b45309";
          title = "Thay thế";
        }

        if (isDeletion && side === "reference") {
          background = "rgba(239, 68, 68, 0.14)";
          border = "rgba(239, 68, 68, 0.34)";
          color = "#b91c1c";
          title = "Mất từ";
        }

        if (isInsertion && side === "prediction") {
          background = "rgba(139, 92, 246, 0.14)";
          border = "rgba(139, 92, 246, 0.34)";
          color = "#7c3aed";
          title = "Thêm từ";
        }

        if (!isEqual && !isSubstitution && !isDeletion && !isInsertion) {
          background = "rgba(100, 116, 139, 0.10)";
          border = "rgba(100, 116, 139, 0.24)";
          color = "inherit";
        }

        return (
          <span
            key={`${side}-${index}`}
            title={title}
            style={{
              display: "inline-flex",
              alignItems: "center",
              padding: "2px 7px",
              borderRadius: "7px",
              border: `1px solid ${border}`,
              background,
              color,
              fontWeight: isEqual ? 600 : 700,
              whiteSpace: "nowrap"
            }}
          >
            {value}
          </span>
        );
      })}
    </span>
  );
}


function WordDiffLegend() {
  const itemStyle = {
    display: "inline-flex",
    alignItems: "center",
    gap: "5px",
    fontSize: "12px"
  };

  const dot = (background, border) => ({
    width: "12px",
    height: "12px",
    borderRadius: "4px",
    background,
    border: `1px solid ${border}`,
    display: "inline-block"
  });

  return (
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        gap: "12px",
        marginTop: "10px",
        color: "var(--text-soft)"
      }}
    >
      <span style={itemStyle}>
        <span
          style={dot(
            "rgba(34, 197, 94, 0.12)",
            "rgba(34, 197, 94, 0.28)"
          )}
        />
        Đúng
      </span>

      <span style={itemStyle}>
        <span
          style={dot(
            "rgba(245, 158, 11, 0.14)",
            "rgba(245, 158, 11, 0.34)"
          )}
        />
        Thay thế
      </span>

      <span style={itemStyle}>
        <span
          style={dot(
            "rgba(239, 68, 68, 0.14)",
            "rgba(239, 68, 68, 0.34)"
          )}
        />
        Mất từ
      </span>

      <span style={itemStyle}>
        <span
          style={dot(
            "rgba(139, 92, 246, 0.14)",
            "rgba(139, 92, 246, 0.34)"
          )}
        />
        Thêm từ
      </span>
    </div>
  );
}







// =====================================================



// STAT CARD COMPONENT



// =====================================================



function StatCard({ title, value, icon, variant = "primary" }) {



  return (



    <div className={`card card--${variant}`}>



      <div className="card-header-line">



        <span className="card-icon">{icon}</span>



        <h3>{title}</h3>



      </div>



      <strong>{value}</strong>



    </div>



  );



}







// =====================================================



// DETAIL DRAWER COMPONENT



// =====================================================



function DetailPanel({ data, onClose }) {



  if (!data) return null;







  const errors = data.errors ?? data.error_types ?? [];



  const words = data.word_analysis ?? data.phoneme_analysis ?? [];







  return (



    <div className="drawer-overlay" onClick={onClose}>



      <div className="drawer" onClick={(e) => e.stopPropagation()}>



        <div className="drawer-header">



          <div>



            <h2>Chi tiết phân tích Audio</h2>



            <div className="drawer-audio">



              <span className="file-badge">🎵 {data.audio}</span>



            </div>



          </div>



          <button className="close-btn" onClick={onClose} title="Đóng panel">



            ✕ Đóng



          </button>



        </div>







        <div className="drawer-body">



          {/* Trình phát Audio */}



          <div className="audio-player-wrapper">



            <audio



              controls



              className="audio-player"



              src={`${API}/audio/${encodeURIComponent(data.audio ?? "")}`}



            >



              Trình duyệt không hỗ trợ phát âm thanh.



            </audio>



          </div>







          {/* Chỉ số WER / CER */}



          <div className="metrics">



            <dl>



              <dt>WER (Word Error Rate)</dt>



              <dd className={Number(data.wer) > 0.2 ? "metric-bad" : "metric-good"}>



                {percent(data.wer)}



              </dd>



            </dl>



            <dl>



              <dt>CER (Char Error Rate)</dt>



              <dd className={Number(data.cer) > 0.2 ? "metric-bad" : "metric-good"}>



                {percent(data.cer)}



              </dd>



            </dl>



          </div>







          {isLikelyHallucination(data) && (








            <div








              style={{








                marginTop: "14px",








                padding: "10px 12px",








                borderRadius: "10px",








                background: "rgba(198, 40, 69, 0.10)",








                border: "1px solid rgba(198, 40, 69, 0.28)",








                color: "#b4233e",








                fontWeight: 700








              }}








            >








              ⚠ Hallucination nghiêm trọng — mô hình sinh ra lượng từ bất thường so với câu chuẩn.








            </div>








          )}









          {/* So sánh câu chuẩn & mô hình đang chọn */}



          <div>



            <h3 className="drawer-section-title">So sánh văn bản</h3>



            <div className="sentence-compare">



              <div className="sentence sentence--ref">

                <span className="sentence-label">Chuẩn (Ground Truth)</span>

                <div style={{ marginTop: "8px" }}>
                  {words.length > 0
                    ? renderWordDiff(words, "reference")
                    : (
                      <p>
                        {data.ground_truth ??
                          data.reference ??
                          data.cau_chuan ??
                          "-"}
                      </p>
                    )}
                </div>

              </div>


              <div className="sentence sentence--pred">

                <span className="sentence-label">
                  {data.model_name ?? "ASR"} Nhận dạng
                </span>

                <div style={{ marginTop: "8px" }}>
                  {words.length > 0
                    ? renderWordDiff(words, "prediction")
                    : (
                      <p>
                        {data.prediction ??
                          data.whisper ??
                          data.whisper_text ??
                          "-"}
                      </p>
                    )}
                </div>

              </div>

              {words.length > 0 && <WordDiffLegend />}



            </div>



          </div>







          {/* Nhãn lỗi phát hiện */}



          <div>



            <h3 className="drawer-section-title">Phân loại lỗi phát hiện</h3>



            <div className="error-tags-wrapper">



              {errors.length > 0 ? (



                errors.map((error, index) => (



                  <span key={index} className="error-badge">



                    ● {translateError(error)}



                  </span>



                ))



              ) : (



                <span className="no-error-badge">✓ Không phát hiện lỗi</span>



              )}



            </div>



          </div>







          {/* Chi tiết âm vị */}



          <div>



            <h3 className="drawer-section-title">Chi tiết lỗi âm vị từng từ</h3>



            {words.length > 0 ? (



              <div className="words">



                {words.map((word, index) => {



                  const referenceWord =
                    word.reference === null || word.reference === undefined
                      ? ""
                      : String(word.reference);

                  const predictionWord =
                    word.prediction === null || word.prediction === undefined
                      ? ""
                      : String(word.prediction);

                  const isInsertion =
                    referenceWord.trim() === "" && predictionWord.trim() !== "";

                  const isDeletion =
                    predictionWord.trim() === "" && referenceWord.trim() !== "";

                  const hasDiff = referenceWord !== predictionWord;

                  return (



                    <div key={index} className={`word ${hasDiff ? "word-diff" : ""}`}>



                      <div className="word-pair">



                        <span className="ref-word">
                          {referenceWord.trim() === "" ? "∅" : referenceWord}
                        </span>

                        <span className="arrow">→</span>

                        <span className="word-pred">
                          {predictionWord.trim() === "" ? "∅" : predictionWord}
                        </span>

                        {hasDiff && (
                          <span className="error-type-tag">
                            {isInsertion
                              ? "Thêm từ"
                              : isDeletion
                              ? "Mất từ"
                              : "Sai khác âm"}
                          </span>
                        )}



                      </div>







                      {!isInsertion && !isDeletion ? (
                      <div className="alignment-card">
                        <table className="phoneme-table">



                          <thead>



                            <tr>



                              <th>Thành phần</th>



                              <th>Chuẩn</th>



                              <th>{data.model_name ?? "ASR"}</th>



                              <th>Đánh giá</th>



                            </tr>



                          </thead>



                          <tbody>



                            {[



                              { label: "Âm đầu", key: "initial" },



                              { label: "Âm chính", key: "nucleus" },



                              { label: "Âm cuối", key: "final" },



                              { label: "Thanh điệu", key: "tone" }



                            ].map((part) => {



                              const refVal = word.detail?.[part.key]?.reference ?? "-";



                              const predVal = word.detail?.[part.key]?.prediction ?? "-";



                              const isMatch = refVal === predVal;







                              return (



                                <tr key={part.key}>



                                  <td>{part.label}</td>



                                  <td>{refVal}</td>



                                  <td>{predVal}</td>



                                  <td className={isMatch ? "correct-cell" : "error-cell"}>



                                    {isMatch ? "✓ Khớp" : "✗ Sai"}



                                  </td>



                                </tr>



                              );



                            })}



                          </tbody>



                        </table>



                      </div>
                      ) : (
                        <div
                          className="alignment-card"
                          style={{
                            padding: "12px",
                            color: "var(--text-soft)",
                            fontSize: "13px"
                          }}
                        >
                          {isInsertion
                            ? "Lỗi thêm từ (Insertion): không phân tích âm vị vì phía câu chuẩn không có từ tương ứng."
                            : "Lỗi mất từ (Deletion): không phân tích âm vị vì phía nhận dạng không có từ tương ứng."}
                        </div>
                      )}




                    </div>



                  );



                })}



              </div>



            ) : (



              <div className="empty">Không có dữ liệu phân tích âm chi tiết</div>



            )}



          </div>



        </div>



      </div>



    </div>



  );



}







// =====================================================



// MAIN COMPONENT



// =====================================================



export default function App() {



  const [statistics, setStatistics] = useState(null);

  const [modelComparison, setModelComparison] = useState(null);

  const [activeModel, setActiveModel] = useState("whisper");

  const activeModelName =
    activeModel === "phowhisper"
      ? "PhoWhisper base"
      : activeModel === "wav2vec2"
        ? "Wav2Vec2 Vietnamese"
        : "Whisper base";



  const [audioList, setAudioList] = useState([]);



  const [selected, setSelected] = useState(null);



  const [loading, setLoading] = useState(true);



  const [search, setSearch] = useState("");



  const [filter, setFilter] = useState("all");



  const [error, setError] = useState("");



  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);



  const [currentPage, setCurrentPage] = useState(1);

  const [pageSize, setPageSize] = useState(20);

  const [werFilter, setWerFilter] = useState("all");

  const [errorFilter, setErrorFilter] = useState("all");

  const [sortBy, setSortBy] = useState("default");


  const [testAudioFile, setTestAudioFile] = useState(null);
  const [testGroundTruth, setTestGroundTruth] = useState("");
  const [testResult, setTestResult] = useState(null);
  const [testLoading, setTestLoading] = useState(false);
  const [testError, setTestError] = useState("");

  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [recordedAudioUrl, setRecordedAudioUrl] = useState("");

  const mediaRecorderRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const recordedChunksRef = useRef([]);
  const recordingTimerRef = useRef(null);







  // =====================================================



  // LOAD DATA



  // =====================================================



  useEffect(() => {



    Promise.all([



      axios.get(`${API}/api/statistics?model=${activeModel}`),



      axios.get(`${API}/api/audio-list?model=${activeModel}`),

      axios.get(`${API}/api/model-comparison`)



    ])



      .then(([stat, audio, comparison]) => {



        setStatistics(stat.data);

        setModelComparison(comparison.data);



        const list = Array.isArray(audio.data)



          ? audio.data



          : (audio.data?.data ?? []);



        setAudioList(list);



      })



      .catch(() => {



        setError("Không kết nối được backend. Vui lòng kiểm tra server API.");



      })



      .finally(() => {



        setLoading(false);



      });



  }, [activeModel]);







  useEffect(() => {
    return () => {
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
      }

      if (mediaStreamRef.current) {
        mediaStreamRef.current
          .getTracks()
          .forEach((track) => track.stop());
      }

      if (recordedAudioUrl) {
        URL.revokeObjectURL(recordedAudioUrl);
      }
    };
  }, [recordedAudioUrl]);


  function formatRecordingTime(totalSeconds) {
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;

    return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
  }


  async function startRecording() {
    if (
      !navigator.mediaDevices ||
      !navigator.mediaDevices.getUserMedia ||
      typeof MediaRecorder === "undefined"
    ) {
      setTestError(
        "Trình duyệt này không hỗ trợ thu âm trực tiếp bằng micro."
      );
      return;
    }

    try {
      setTestError("");
      setTestResult(null);

      if (recordedAudioUrl) {
        URL.revokeObjectURL(recordedAudioUrl);
        setRecordedAudioUrl("");
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });

      mediaStreamRef.current = stream;
      recordedChunksRef.current = [];

      const preferredMimeTypes = [
        "audio/webm;codecs=opus",
        "audio/webm",
        "audio/ogg;codecs=opus"
      ];

      const mimeType = preferredMimeTypes.find(
        (type) => MediaRecorder.isTypeSupported(type)
      );

      const recorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream);

      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          recordedChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = () => {
        const finalMimeType =
          recorder.mimeType || mimeType || "audio/webm";

        const extension = finalMimeType.includes("ogg")
          ? "ogg"
          : "webm";

        const blob = new Blob(
          recordedChunksRef.current,
          { type: finalMimeType }
        );

        const file = new File(
          [blob],
          `microphone_${Date.now()}.${extension}`,
          { type: finalMimeType }
        );

        const url = URL.createObjectURL(blob);

        setRecordedAudioUrl(url);
        setTestAudioFile(file);

        if (mediaStreamRef.current) {
          mediaStreamRef.current
            .getTracks()
            .forEach((track) => track.stop());

          mediaStreamRef.current = null;
        }
      };

      recorder.start(250);

      setRecordingSeconds(0);
      setIsRecording(true);

      recordingTimerRef.current = setInterval(() => {
        setRecordingSeconds((seconds) => seconds + 1);
      }, 1000);

    } catch (err) {
      setTestError(
        err?.name === "NotAllowedError"
          ? "Bạn chưa cấp quyền sử dụng micro. Hãy cho phép trình duyệt truy cập micro rồi thử lại."
          : `Không thể mở micro: ${err?.message ?? "Lỗi không xác định"}`
      );
    }
  }


  function stopRecording() {
    const recorder = mediaRecorderRef.current;

    if (
      recorder &&
      recorder.state !== "inactive"
    ) {
      recorder.stop();
    }

    if (recordingTimerRef.current) {
      clearInterval(recordingTimerRef.current);
      recordingTimerRef.current = null;
    }

    setIsRecording(false);
  }


  function clearRecordedAudio() {
    if (isRecording) {
      stopRecording();
    }

    if (recordedAudioUrl) {
      URL.revokeObjectURL(recordedAudioUrl);
    }

    setRecordedAudioUrl("");
    setTestAudioFile(null);
    setRecordingSeconds(0);
    setTestResult(null);
    setTestError("");
  }


  async function handleTestAudio(event) {
    event.preventDefault();

    if (!testAudioFile) {
      setTestError("Vui lòng chọn một file audio.");
      return;
    }

    setTestLoading(true);
    setTestError("");
    setTestResult(null);

    const formData = new FormData();

    formData.append(
      "file",
      testAudioFile
    );

    formData.append(
      "model",
      activeModel
    );

    formData.append(
      "ground_truth",
      testGroundTruth.trim()
    );

    try {
      const response = await axios.post(
        `${API}/api/test-audio`,
        formData
      );

      setTestResult(
        response.data
      );
    } catch (err) {
      setTestError(
        err?.response?.data?.detail ??
          "Không thể nhận dạng audio. Kiểm tra backend và model."
      );
    } finally {
      setTestLoading(false);
    }
  }



  // =====================================================



  // FILTER TABLE



  // =====================================================



  const tableData = useMemo(() => {

    let data = [...audioList];



    if (filter !== "all") {

      data = data.filter((item) => getStatus(item) === filter);

    }



    if (search.trim()) {

      const key = search.toLowerCase();

      data = data.filter((item) =>

        (item.audio ?? "").toLowerCase().includes(key)

      );

    }



    if (werFilter !== "all") {

      data = data.filter((item) => {

        const werValue = Number(item.wer);

        if (!Number.isFinite(werValue)) return false;



        if (werFilter === "zero") return werValue === 0;

        if (werFilter === "lt20") return werValue > 0 && werValue < 0.2;

        if (werFilter === "20to50") return werValue >= 0.2 && werValue <= 0.5;

        if (werFilter === "gt50") return werValue > 0.5;
        if (werFilter === "hallucination") return isLikelyHallucination(item);

        return true;

      });

    }



    if (errorFilter !== "all") {

      data = data.filter((item) =>

        Array.isArray(item.errors) && item.errors.includes(errorFilter)

      );

    }



    if (sortBy === "wer_desc") {

      data.sort((a, b) => Number(b.wer ?? -1) - Number(a.wer ?? -1));

    } else if (sortBy === "wer_asc") {

      data.sort((a, b) => Number(a.wer ?? 999) - Number(b.wer ?? 999));

    } else if (sortBy === "cer_desc") {

      data.sort((a, b) => Number(b.cer ?? -1) - Number(a.cer ?? -1));

    } else if (sortBy === "cer_asc") {

      data.sort((a, b) => Number(a.cer ?? 999) - Number(b.cer ?? 999));

    }



    return data;

  }, [audioList, filter, search, werFilter, errorFilter, sortBy]);



  // =====================================================

  // PAGINATION

  // =====================================================



  const totalPages = Math.max(

    1,

    Math.ceil(tableData.length / pageSize)

  );



  const paginatedData = useMemo(() => {

    const start = (currentPage - 1) * pageSize;

    return tableData.slice(start, start + pageSize);

  }, [tableData, currentPage, pageSize]);



  useEffect(() => {

    setCurrentPage(1);

  }, [search, filter, pageSize, werFilter, errorFilter, sortBy]);



  useEffect(() => {

    if (currentPage > totalPages) {

      setCurrentPage(totalPages);

    }

  }, [currentPage, totalPages]);









  // Đếm số lượng theo trạng thái



  const counts = useMemo(() => {



    return {



      all: audioList.length,



      incorrect: audioList.filter((i) => getStatus(i) === "incorrect").length,



      correct: audioList.filter((i) => getStatus(i) === "correct").length



    };



  }, [audioList]);







  // =====================================================



  // CHART DATA



  // =====================================================



  const chartData = useMemo(() => {



    return Object.entries(statistics?.error_distribution ?? {}).map(



      ([name, value]) => ({



        name: translateError(name),



        rawName: name,



        value



      })



    );



  }, [statistics]);

  const sdiData = useMemo(() => {
    const wordCounts = statistics?.word_error_counts ?? {};

    return [
      { name: "Thay thế (S)", value: Number(wordCounts.substitutions ?? 0) },
      { name: "Mất từ (D)", value: Number(wordCounts.deletions ?? 0) },
      { name: "Thêm từ (I)", value: Number(wordCounts.insertions ?? 0) }
    ];
  }, [statistics]);

  const modelMetricData = useMemo(() => {
    return (modelComparison?.models ?? []).map((model) => ({
      name: model.name,
      WER: Number(model.average_wer ?? 0) * 100,
      CER: Number(model.average_cer ?? 0) * 100,
      "Corpus WER": Number(model.corpus_wer ?? 0) * 100
    }));
  }, [modelComparison]);

  const modelSdiData = useMemo(() => {
    return (modelComparison?.models ?? []).map((model) => ({
      name: model.name,
      S: Number(model.substitutions ?? 0),
      D: Number(model.deletions ?? 0),
      I: Number(model.insertions ?? 0)
    }));
  }, [modelComparison]);









  // =====================================================



  // LOADING STATE



  // =====================================================



  if (loading) {



    return (



      <div className="loading">



        <div className="loading-spinner"></div>



        <span>Đang tải dữ liệu phân tích ASR...</span>



      </div>



    );



  }







  // =====================================================



  // RENDER APP



  // =====================================================



  return (



    <div className="app-layout">



      {/* SIDEBAR */}



      <aside className={`sidebar ${sidebarCollapsed ? "collapsed" : ""}`}>



        <div className="sidebar-logo">



          <span className="logo-icon">🎙️</span>



          <div className="logo-text">



            <strong>ASR</strong> Analyzer



          </div>



        </div>







        <nav className="sidebar-nav">



          <button className="nav-item active">



            <span className="nav-icon">📊</span>



            <span>Tổng quan</span>



          </button>



          <button className="nav-item" onClick={() => setFilter("incorrect")}>



            <span className="nav-icon">⚠️</span>



            <span>Mẫu cần sửa ({counts.incorrect})</span>



          </button>



          <button className="nav-item" onClick={() => setFilter("correct")}>



            <span className="nav-icon">✅</span>



            <span>Mẫu đạt chuẩn ({counts.correct})</span>



          </button>



        </nav>







        <div className="sidebar-footer">



          <div className="model-badge">



            <span className="dot"></span>



            <span>{activeModelName} • Sẵn sàng</span>



          </div>



        </div>



      </aside>







      {/* MAIN CONTAINER */}



      <div className={`main-wrapper ${sidebarCollapsed ? "expanded" : ""}`}>



        {/* TOPBAR */}



        <header className="topbar">



          <button



            className="menu-btn"



            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}



            title="Đóng / Mở Sidebar"



          >



            ☰



          </button>



          <div className="topbar-title">



            <h1>Vietnamese ASR Error Analyzer</h1>



            <p className="subtitle">



              Bảng điều khiển & Đánh giá sai sót mô hình nhận dạng tiếng Việt



            </p>



          </div>



          <div
            style={{
              marginLeft: "auto",
              display: "flex",
              alignItems: "center",
              gap: "8px"
            }}
          >
            <span
              style={{
                fontSize: "13px",
                color: "var(--text-soft)",
                fontWeight: 600
              }}
            >
              Mô hình:
            </span>

            <select
              value={activeModel}
              onChange={(e) => {
                setActiveModel(e.target.value);
                setSelected(null);
                setCurrentPage(1);
              }}
              style={{
                border: "1px solid var(--line)",
                background: "var(--surface)",
                color: "var(--text)",
                padding: "8px 12px",
                borderRadius: "var(--radius-sm)",
                fontFamily: "inherit",
                fontSize: "13px",
                fontWeight: 600,
                cursor: "pointer"
              }}
            >
              <option value="whisper">Whisper base</option>
              <option value="phowhisper">PhoWhisper base</option>
              <option value="wav2vec2">Wav2Vec2 Vietnamese</option>
            </select>
          </div>

        </header>







        {/* CONTENT */}



        <main className="content">



          {error && (



            <div className="error-banner">



              <span>⚠️ {error}</span>



              <button className="error-dismiss" onClick={() => setError("")}>



                ×



              </button>



            </div>



          )}







          {/* CARDS GRID */}



          <section className="cards">



            <StatCard



              icon="📁"



              title="Tổng Audio"



              value={statistics?.total_audio ?? 0}



              variant="primary"



            />



            <StatCard



              icon="⚡"



              title="Tổng lỗi âm"



              value={statistics?.total_error ?? 0}



              variant="danger"



            />



            <StatCard



              icon="📉"



              title="WER trung bình"



              value={percent(statistics?.average_wer)}



              variant="warning"



            />



            <StatCard



              icon="🎯"



              title="CER trung bình"



              value={percent(statistics?.average_cer)}



              variant="info"



            />
            <StatCard
              icon="🧮"
              title="Corpus WER"
              value={percent(statistics?.corpus_wer)}
              variant="warning"
            />

            <StatCard
              icon="🔁"
              title="Thay thế (S)"
              value={statistics?.word_error_counts?.substitutions ?? 0}
              variant="danger"
            />

            <StatCard
              icon="➖"
              title="Mất từ (D)"
              value={statistics?.word_error_counts?.deletions ?? 0}
              variant="warning"
            />

            <StatCard
              icon="➕"
              title="Thêm từ (I)"
              value={statistics?.word_error_counts?.insertions ?? 0}
              variant="info"
            />

            <StatCard
              icon="⚠️"
              title="Hallucination"
              value={statistics?.hallucination?.count ?? 0}
              variant="danger"
            />





            <StatCard



              icon="✨"



              title="Câu chuẩn xác"



              value={statistics?.correct_sentence ?? 0}



              variant="success"



            />



            <StatCard



              icon="❌"



              title="Câu có lỗi"



              value={statistics?.incorrect_sentence ?? 0}



              variant="danger"



            />



          </section>







          {/* CHARTS SECTION */}



          <section className="section chart-section">



            <div className="section-header">



              <h2>📊 Phân bố các loại lỗi tiếng Việt</h2>



              <span className="badge-count">



                {chartData.length} nhóm lỗi thống kê



              </span>



            </div>



            <div className="chart-box">



              <ResponsiveContainer width="100%" height="100%">



                <BarChart data={chartData} margin={{ top: 20, right: 20, bottom: 20, left: 0 }}>



                  <XAxis



                    dataKey="name"



                    tick={{ fill: "#64748b", fontSize: 12 }}



                    interval={0}



                    angle={-15}



                    textAnchor="end"



                  />



                  <YAxis tick={{ fill: "#64748b", fontSize: 12 }} />



                  <Tooltip



                    contentStyle={{



                      background: "#ffffff",



                      borderRadius: "8px",



                      boxShadow: "0 8px 24px rgba(0,0,0,0.12)",



                      border: "1px solid #e2e8f0"



                    }}



                  />



                  <Bar dataKey="value" radius={[6, 6, 0, 0]}>



                    {chartData.map((_, index) => (



                      <Cell



                        key={index}



                        fill={CHART_COLORS[index % CHART_COLORS.length]}



                      />



                    ))}



                  </Bar>



                </BarChart>



              </ResponsiveContainer>



            </div>



          </section>







          {/* MODEL COMPARISON */}
          <section className="section chart-section">
            <div className="section-header">
              <h2>🤖 So sánh mô hình ASR</h2>
              <span className="badge-count">
                {modelComparison?.total_models ?? 0} mô hình
              </span>
            </div>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
                gap: "16px",
                marginBottom: "18px"
              }}
            >
              {(modelComparison?.models ?? []).map((model) => {
                const isBest =
                  modelComparison?.best?.average_wer === model.key &&
                  modelComparison?.best?.average_cer === model.key &&
                  modelComparison?.best?.corpus_wer === model.key;

                return (
                  <div
                    key={model.key}
                    className="card"
                    style={{
                      padding: "18px",
                      border: isBest
                        ? "2px solid var(--success)"
                        : "1px solid var(--line)"
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        gap: "10px",
                        alignItems: "center",
                        marginBottom: "14px"
                      }}
                    >
                      <strong style={{ fontSize: "16px" }}>{model.name}</strong>
                      {isBest && (
                        <span className="no-error-badge">🏆 Tốt nhất</span>
                      )}
                    </div>

                    <div
                      style={{
                        display: "grid",
                        gridTemplateColumns: "1fr 1fr",
                        gap: "10px",
                        fontSize: "13px"
                      }}
                    >
                      <div>
                        <span style={{ color: "var(--text-soft)" }}>WER TB</span>
                        <div style={{ fontWeight: 700, fontSize: "18px" }}>
                          {percent(model.average_wer)}
                        </div>
                      </div>

                      <div>
                        <span style={{ color: "var(--text-soft)" }}>CER TB</span>
                        <div style={{ fontWeight: 700, fontSize: "18px" }}>
                          {percent(model.average_cer)}
                        </div>
                      </div>

                      <div>
                        <span style={{ color: "var(--text-soft)" }}>
                          Corpus WER
                        </span>
                        <div style={{ fontWeight: 700, fontSize: "18px" }}>
                          {percent(model.corpus_wer)}
                        </div>
                      </div>

                      <div>
                        <span style={{ color: "var(--text-soft)" }}>
                          Hallucination
                        </span>
                        <div style={{ fontWeight: 700, fontSize: "18px" }}>
                          {model.hallucination_count ?? 0}
                        </div>
                      </div>
                    </div>

                    <div
                      style={{
                        marginTop: "14px",
                        paddingTop: "12px",
                        borderTop: "1px solid var(--line)",
                        fontSize: "13px",
                        color: "var(--text-soft)"
                      }}
                    >
                      S / D / I:{" "}
                      <strong style={{ color: "var(--text)" }}>
                        {model.substitutions ?? 0} / {model.deletions ?? 0} /{" "}
                        {model.insertions ?? 0}
                      </strong>
                    </div>
                  </div>
                );
              })}
            </div>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))",
                gap: "18px"
              }}
            >
              <div className="chart-box">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={modelMetricData}
                    margin={{ top: 20, right: 20, bottom: 20, left: 0 }}
                  >
                    <XAxis
                      dataKey="name"
                      tick={{ fill: "#64748b", fontSize: 12 }}
                    />
                    <YAxis
                      tick={{ fill: "#64748b", fontSize: 12 }}
                      tickFormatter={(value) => `${value}%`}
                    />
                    <Tooltip
                      formatter={(value) => `${Number(value).toFixed(2)}%`}
                      contentStyle={{
                        background: "#ffffff",
                        borderRadius: "8px",
                        boxShadow: "0 8px 24px rgba(0,0,0,0.12)",
                        border: "1px solid #e2e8f0"
                      }}
                    />
                    <Bar dataKey="WER" fill={CHART_COLORS[0]} radius={[5, 5, 0, 0]} />
                    <Bar dataKey="CER" fill={CHART_COLORS[1]} radius={[5, 5, 0, 0]} />
                    <Bar
                      dataKey="Corpus WER"
                      fill={CHART_COLORS[2]}
                      radius={[5, 5, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="chart-box">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={modelSdiData}
                    margin={{ top: 20, right: 20, bottom: 20, left: 0 }}
                  >
                    <XAxis
                      dataKey="name"
                      tick={{ fill: "#64748b", fontSize: 12 }}
                    />
                    <YAxis tick={{ fill: "#64748b", fontSize: 12 }} />
                    <Tooltip
                      contentStyle={{
                        background: "#ffffff",
                        borderRadius: "8px",
                        boxShadow: "0 8px 24px rgba(0,0,0,0.12)",
                        border: "1px solid #e2e8f0"
                      }}
                    />
                    <Bar dataKey="S" fill={CHART_COLORS[3]} radius={[5, 5, 0, 0]} />
                    <Bar dataKey="D" fill={CHART_COLORS[4]} radius={[5, 5, 0, 0]} />
                    <Bar dataKey="I" fill={CHART_COLORS[5]} radius={[5, 5, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div style={{ overflowX: "auto", marginTop: "18px" }}>
              <table>
                <thead>
                  <tr>
                    <th>Mô hình</th>
                    <th>WER TB</th>
                    <th>CER TB</th>
                    <th>Corpus WER</th>
                    <th>S</th>
                    <th>D</th>
                    <th>I</th>
                    <th>Hallucination</th>
                  </tr>
                </thead>
                <tbody>
                  {(modelComparison?.models ?? []).map((model) => (
                    <tr key={`compare-${model.key}`}>
                      <td><strong>{model.name}</strong></td>
                      <td>{percent(model.average_wer)}</td>
                      <td>{percent(model.average_cer)}</td>
                      <td>{percent(model.corpus_wer)}</td>
                      <td>{model.substitutions ?? 0}</td>
                      <td>{model.deletions ?? 0}</td>
                      <td>{model.insertions ?? 0}</td>
                      <td>{model.hallucination_count ?? 0}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>



          {/* S / D / I CHART */}
          <section className="section chart-section">
            <div className="section-header">
              <h2>🧩 Phân rã lỗi từ theo S / D / I</h2>
              <span className="badge-count">
                Corpus WER: {percent(statistics?.corpus_wer)}
              </span>
            </div>

            <div className="chart-box">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={sdiData}
                  margin={{ top: 20, right: 20, bottom: 20, left: 0 }}
                >
                  <XAxis
                    dataKey="name"
                    tick={{ fill: "#64748b", fontSize: 12 }}
                    interval={0}
                  />
                  <YAxis tick={{ fill: "#64748b", fontSize: 12 }} />
                  <Tooltip
                    contentStyle={{
                      background: "#ffffff",
                      borderRadius: "8px",
                      boxShadow: "0 8px 24px rgba(0,0,0,0.12)",
                      border: "1px solid #e2e8f0"
                    }}
                  />
                  <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                    {sdiData.map((_, index) => (
                      <Cell
                        key={index}
                        fill={CHART_COLORS[index % CHART_COLORS.length]}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>



          {/* LIVE AUDIO TEST */}
          <section className="section">
            <div className="section-header">
              <h2>🎤 Test audio mới trực tiếp</h2>
              <span className="badge-count">
                {activeModelName}
              </span>
            </div>

            <form
              onSubmit={handleTestAudio}
              style={{
                display: "grid",
                gap: "14px"
              }}
            >
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns:
                    "repeat(auto-fit, minmax(260px, 1fr))",
                  gap: "14px"
                }}
              >
                <div>
                  <div
                    style={{
                      fontSize: "13px",
                      fontWeight: 700,
                      marginBottom: "7px"
                    }}
                  >
                    Nguồn audio
                  </div>

                  <div className="audio-source-panel">
                    <input
                      type="file"
                      accept="audio/*,.wav,.mp3,.m4a,.flac,.ogg,.webm,.aac"
                      onChange={(e) => {
                        const file = e.target.files?.[0] ?? null;

                        if (recordedAudioUrl) {
                          URL.revokeObjectURL(recordedAudioUrl);
                          setRecordedAudioUrl("");
                        }

                        setTestAudioFile(file);
                        setRecordingSeconds(0);
                        setTestResult(null);
                        setTestError("");
                      }}
                      className="audio-file-input"
                    />

                    <div className="mic-divider">
                      <span>hoặc</span>
                    </div>

                    <div className="mic-recorder">
                      <div className="mic-recorder-main">
                        <div
                          className={
                            isRecording
                              ? "mic-status mic-status--recording"
                              : "mic-status"
                          }
                        >
                          <span className="mic-status-dot" />

                          <span>
                            {isRecording
                              ? `Đang thu ${formatRecordingTime(recordingSeconds)}`
                              : recordedAudioUrl
                                ? `Đã thu ${formatRecordingTime(recordingSeconds)}`
                                : "Thu trực tiếp bằng micro"}
                          </span>
                        </div>

                        <div className="mic-actions">
                          {!isRecording ? (
                            <button
                              type="button"
                              className="mic-btn mic-btn--start"
                              onClick={startRecording}
                              disabled={testLoading}
                            >
                              🎙️ Bắt đầu thu
                            </button>
                          ) : (
                            <button
                              type="button"
                              className="mic-btn mic-btn--stop"
                              onClick={stopRecording}
                            >
                              ⏹ Dừng thu
                            </button>
                          )}

                          {recordedAudioUrl && !isRecording && (
                            <button
                              type="button"
                              className="mic-btn mic-btn--clear"
                              onClick={clearRecordedAudio}
                              disabled={testLoading}
                            >
                              ✕ Thu lại
                            </button>
                          )}
                        </div>
                      </div>

                      {isRecording && (
                        <div className="recording-wave" aria-hidden="true">
                          {Array.from({ length: 18 }).map((_, index) => (
                            <span
                              key={index}
                              style={{
                                animationDelay: `${index * 0.055}s`
                              }}
                            />
                          ))}
                        </div>
                      )}

                      {recordedAudioUrl && !isRecording && (
                        <div className="recorded-preview">
                          <audio
                            controls
                            src={recordedAudioUrl}
                          />

                          <span className="recorded-ready">
                            ✓ Bản thu đã sẵn sàng để nhận dạng
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                <div>
                  <div
                    style={{
                      fontSize: "13px",
                      fontWeight: 700,
                      marginBottom: "7px"
                    }}
                  >
                    Model nhận dạng
                  </div>

                  <select
                    value={activeModel}
                    onChange={(e) => {
                      setActiveModel(
                        e.target.value
                      );
                      setSelected(null);
                      setCurrentPage(1);
                      setTestResult(null);
                    }}
                    style={{
                      width: "100%",
                      border: "1px solid var(--line)",
                      background: "var(--surface)",
                      color: "var(--text)",
                      padding: "10px 12px",
                      borderRadius: "10px",
                      fontFamily: "inherit",
                      fontSize: "14px",
                      fontWeight: 600
                    }}
                  >
                    <option value="whisper">
                      Whisper base
                    </option>
                    <option value="phowhisper">
                      PhoWhisper base
                    </option>
                    <option value="wav2vec2">
                      Wav2Vec2 Vietnamese
                    </option>
                  </select>
                </div>
              </div>

              <div>
                <div
                  style={{
                    fontSize: "13px",
                    fontWeight: 700,
                    marginBottom: "7px"
                  }}
                >
                  Ground Truth
                  <span
                    style={{
                      fontWeight: 400,
                      color: "var(--text-soft)"
                    }}
                  >
                    {" "}
                    (không bắt buộc)
                  </span>
                </div>

                <textarea
                  value={testGroundTruth}
                  onChange={(e) =>
                    setTestGroundTruth(
                      e.target.value
                    )
                  }
                  placeholder="Nhập câu chuẩn nếu muốn tính WER/CER và phân tích lỗi..."
                  rows={3}
                  style={{
                    width: "100%",
                    resize: "vertical",
                    padding: "11px 12px",
                    border: "1px solid var(--line)",
                    borderRadius: "10px",
                    background: "var(--surface)",
                    color: "var(--text)",
                    fontFamily: "inherit",
                    fontSize: "14px",
                    boxSizing: "border-box"
                  }}
                />
              </div>

              <div>
                <button
                  type="submit"
                  disabled={
                    testLoading ||
                    !testAudioFile
                  }
                  style={{
                    border: "none",
                    borderRadius: "10px",
                    padding: "10px 18px",
                    fontWeight: 700,
                    cursor:
                      testLoading || !testAudioFile
                        ? "not-allowed"
                        : "pointer",
                    opacity:
                      testLoading || !testAudioFile
                        ? 0.6
                        : 1
                  }}
                >
                  {testLoading
                    ? "⏳ Đang nhận dạng..."
                    : recordedAudioUrl
                      ? "✨ Nhận dạng bản thu"
                      : "🎙️ Nhận dạng audio"}
                </button>
              </div>
            </form>

            {testError && (
              <div
                style={{
                  marginTop: "14px",
                  padding: "12px",
                  borderRadius: "10px",
                  background:
                    "rgba(239, 68, 68, 0.10)",
                  border:
                    "1px solid rgba(239, 68, 68, 0.28)",
                  color: "#b91c1c"
                }}
              >
                {testError}
              </div>
            )}

            {testResult && (
              <div
                style={{
                  marginTop: "18px",
                  display: "grid",
                  gap: "14px"
                }}
              >
                <div
                  style={{
                    display: "flex",
                    flexWrap: "wrap",
                    gap: "10px"
                  }}
                >
                  <span className="file-badge">
                    {testResult.model_name}
                  </span>

                  <span className="badge-count">
                    ⏱ {Number(
                      testResult.processing_seconds ?? 0
                    ).toFixed(2)}s
                  </span>

                  {testResult.has_ground_truth && (
                    <>
                      <span className="badge-count">
                        WER: {percent(testResult.wer)}
                      </span>

                      <span className="badge-count">
                        CER: {percent(testResult.cer)}
                      </span>
                    </>
                  )}
                </div>

                {testResult.has_ground_truth && (
                  <div className="sentence sentence--ref">
                    <span className="sentence-label">
                      Chuẩn (Ground Truth)
                    </span>

                    <div style={{ marginTop: "8px" }}>
                      {Array.isArray(
                        testResult.word_analysis
                      ) &&
                      testResult.word_analysis.length > 0
                        ? renderWordDiff(
                            testResult.word_analysis,
                            "reference"
                          )
                        : (
                          <p>
                            {testResult.ground_truth}
                          </p>
                        )}
                    </div>
                  </div>
                )}

                <div className="sentence sentence--pred">
                  <span className="sentence-label">
                    {testResult.model_name} Nhận dạng
                  </span>

                  <div style={{ marginTop: "8px" }}>
                    {testResult.has_ground_truth &&
                    Array.isArray(
                      testResult.word_analysis
                    ) &&
                    testResult.word_analysis.length > 0
                      ? renderWordDiff(
                          testResult.word_analysis,
                          "prediction"
                        )
                      : (
                        <p>
                          {testResult.prediction || "(Không nhận dạng được văn bản)"}
                        </p>
                      )}
                  </div>
                </div>

                {testResult.has_ground_truth &&
                  Array.isArray(
                    testResult.word_analysis
                  ) &&
                  testResult.word_analysis.length > 0 && (
                    <WordDiffLegend />
                  )}

                {!testResult.has_ground_truth && (
                  <div
                    style={{
                      fontSize: "13px",
                      color: "var(--text-soft)"
                    }}
                  >
                    Nhập Ground Truth để hệ thống tính WER/CER
                    và phân tích lỗi tiếng Việt.
                  </div>
                )}
              </div>
            )}
          </section>


          {/* AUDIO LIST TABLE */}



          <section className="section">



                        <div
              style={{
                marginBottom: "12px",
                padding: "10px 12px",
                borderRadius: "10px",
                border: "1px solid var(--line)",
                background: "var(--surface)",
                display: "flex",
                alignItems: "center",
                gap: "8px",
                fontSize: "13px"
              }}
            >
              <strong>Mô hình đang xem:</strong>
              <span className="file-badge">
                {activeModelName}
              </span>
            </div>

<div className="section-header">



              <h2>📑 Danh sách mẫu Audio kiểm thử</h2>



              <input



                className="search"



                placeholder="🔍 Tìm tên file audio..."



                value={search}



                onChange={(e) => setSearch(e.target.value)}



              />



            </div>







            <div className="filter">



              <button



                className={filter === "all" ? "active" : ""}



                onClick={() => setFilter("all")}



              >



                Tất cả <span className="filter-count">{counts.all}</span>



              </button>



              <button



                className={filter === "incorrect" ? "active" : ""}



                onClick={() => setFilter("incorrect")}



              >



                Có lỗi <span className="filter-count">{counts.incorrect}</span>



              </button>



              <button



                className={filter === "correct" ? "active" : ""}



                onClick={() => setFilter("correct")}



              >



                Đúng chuẩn <span className="filter-count">{counts.correct}</span>



              </button>



            </div>









            <div

              className="advanced-filter"

              style={{

                display: "flex",

                gap: "10px",

                flexWrap: "wrap",

                alignItems: "center",

                marginBottom: "16px"

              }}

            >

              <select

                value={werFilter}

                onChange={(e) => setWerFilter(e.target.value)}

                style={{

                  border: "1px solid var(--line)",

                  background: "var(--surface)",

                  color: "var(--text)",

                  padding: "8px 12px",

                  borderRadius: "var(--radius-sm)",

                  fontFamily: "inherit",

                  fontSize: "13px"

                }}

              >

                <option value="all">Tất cả WER</option>

                <option value="zero">WER = 0%</option>

                <option value="lt20">WER &lt; 20%</option>

                <option value="20to50">WER 20% - 50%</option>

                <option value="gt50">WER &gt; 50%</option>
                <option value="hallucination">⚠ Hallucination</option>

              </select>



              <select

                value={errorFilter}

                onChange={(e) => setErrorFilter(e.target.value)}

                style={{

                  border: "1px solid var(--line)",

                  background: "var(--surface)",

                  color: "var(--text)",

                  padding: "8px 12px",

                  borderRadius: "var(--radius-sm)",

                  fontFamily: "inherit",

                  fontSize: "13px"

                }}

              >

                <option value="all">Tất cả loại lỗi</option>

                <option value="tone_error">Sai thanh điệu</option>

                <option value="initial_consonant_error">Sai phụ âm đầu</option>

                <option value="nucleus_error">Sai âm chính</option>

                <option value="final_consonant_error">Sai âm cuối</option>

                <option value="missing_word">Mất từ</option>

                <option value="extra_word">Thêm từ</option>

                <option value="merge_word">Gộp từ</option>

                <option value="split_word">Tách từ</option>

              </select>



              <select

                value={sortBy}

                onChange={(e) => setSortBy(e.target.value)}

                style={{

                  border: "1px solid var(--line)",

                  background: "var(--surface)",

                  color: "var(--text)",

                  padding: "8px 12px",

                  borderRadius: "var(--radius-sm)",

                  fontFamily: "inherit",

                  fontSize: "13px"

                }}

              >

                <option value="default">Sắp xếp mặc định</option>

                <option value="wer_desc">WER cao → thấp</option>

                <option value="wer_asc">WER thấp → cao</option>

                <option value="cer_desc">CER cao → thấp</option>

                <option value="cer_asc">CER thấp → cao</option>

              </select>



              <button

                type="button"

                onClick={() => {

                  setWerFilter("all");

                  setErrorFilter("all");

                  setSortBy("default");

                  setSearch("");

                  setFilter("all");

                }}

                style={{

                  border: "1px solid var(--line)",

                  background: "var(--surface)",

                  color: "var(--text)",

                  padding: "8px 12px",

                  borderRadius: "var(--radius-sm)",

                  fontFamily: "inherit",

                  fontSize: "13px",

                  cursor: "pointer"

                }}

              >

                Xóa bộ lọc

              </button>



              <span

                style={{

                  marginLeft: "auto",

                  color: "var(--text-soft)",

                  fontSize: "12.5px"

                }}

              >

                Kết quả: {tableData.length} mẫu

              </span>

            </div>



<div className="table-container">



              <table>



                <thead>



                  <tr>



                    <th>Audio</th>



                    <th>WER</th>



                    <th>CER</th>



                    <th>Trạng thái</th>



                    <th>Chi tiết lỗi</th>



                  </tr>



                </thead>



                <tbody>



                  {tableData.length > 0 ? (



                    paginatedData.map((item, index) => {



                      const werNum = Number(item.wer);



                      const werPercent = Number.isFinite(werNum) ? Math.min(werNum * 100, 100) : 0;



                      const werColor =



                        werPercent === 0



                          ? "var(--success)"



                          : werPercent < 30



                          ? "var(--warning)"



                          : "var(--danger)";







                      return (



                        <tr



                          key={item.audio ?? index}



                          onClick={async () => {



                            try {



                              const res = await axios.get(



                                `${API}/api/audio-detail/${encodeURIComponent(item.audio)}?model=${activeModel}`



                              );



                              setSelected(res.data?.data ?? res.data);



                            } catch (err) {



                              console.error(err);



                              setError("Không tải được chi tiết audio");



                            }



                          }}



                        >



                          <td className="audio-cell">



                            <strong>{item.audio}</strong>

                            {isLikelyHallucination(item) && (
                              <span
                                style={{
                                  display: "inline-block",
                                  marginLeft: "8px",
                                  padding: "3px 7px",
                                  borderRadius: "999px",
                                  background: "rgba(198, 40, 69, 0.10)",
                                  border: "1px solid rgba(198, 40, 69, 0.28)",
                                  color: "#b4233e",
                                  fontSize: "11px",
                                  fontWeight: 700,
                                  whiteSpace: "nowrap"
                                }}
                              >
                                ⚠ Hallucination
                              </span>
                            )}



                          </td>



                          <td>



                            <div className="wer-cell">



                              <div className="wer-bar">



                                <span



                                  style={{



                                    width: `${werPercent}%`,



                                    background: werColor



                                  }}



                                ></span>



                              </div>



                              <span>{percent(item.wer)}</span>



                            </div>



                          </td>



                          <td>{percent(item.cer)}</td>



                          <td>



                            <span className={STATUS_CLASS[getStatus(item)]}>



                              {STATUS_LABEL[getStatus(item)]}



                            </span>



                          </td>



                          <td>



                            {(item.errors ?? []).map((error, idx) => (



                              <span className="error-badge" key={idx}>



                                {translateError(error)}



                              </span>



                            ))}



                          </td>



                        </tr>



                      );



                    })



                  ) : (



                    <tr>



                      <td colSpan="5" className="empty">



                        Không tìm thấy audio nào khớp với bộ lọc



                      </td>



                    </tr>



                  )}



                </tbody>



              </table>



            </div>



            <div

              className="pagination"

              style={{

                marginTop: "16px",

                display: "flex",

                justifyContent: "space-between",

                alignItems: "center",

                gap: "12px",

                flexWrap: "wrap"

              }}

            >

              <div

                className="pagination-info"

                style={{

                  color: "var(--text-soft)",

                  fontSize: "13px"

                }}

              >

                Hiển thị{" "}

                {tableData.length === 0

                  ? 0

                  : (currentPage - 1) * pageSize + 1}

                {" - "}

                {Math.min(currentPage * pageSize, tableData.length)}

                {" / "}

                {tableData.length} mẫu

              </div>



              <div

                className="pagination-controls"

                style={{

                  display: "flex",

                  alignItems: "center",

                  gap: "8px",

                  flexWrap: "wrap"

                }}

              >

                <select

                  value={pageSize}

                  onChange={(e) => {

                    setPageSize(Number(e.target.value));

                    setCurrentPage(1);

                  }}

                  style={{

                    border: "1px solid var(--line)",

                    background: "var(--surface)",

                    color: "var(--text)",

                    padding: "7px 12px",

                    borderRadius: "var(--radius-sm)",

                    fontFamily: "inherit",

                    fontSize: "13px"

                  }}

                >

                  <option value={20}>20 / trang</option>

                  <option value={50}>50 / trang</option>

                  <option value={100}>100 / trang</option>

                </select>



                <button

                  type="button"

                  disabled={currentPage === 1}

                  onClick={() =>

                    setCurrentPage((page) => Math.max(1, page - 1))

                  }

                  style={{

                    border: "1px solid var(--line)",

                    background: "var(--surface)",

                    color: "var(--text)",

                    padding: "7px 12px",

                    borderRadius: "var(--radius-sm)",

                    fontFamily: "inherit",

                    fontSize: "13px",

                    cursor: currentPage === 1 ? "not-allowed" : "pointer",

                    opacity: currentPage === 1 ? 0.45 : 1

                  }}

                >

                  ← Trước

                </button>



                <span

                  style={{

                    fontSize: "13px",

                    color: "var(--text-soft)"

                  }}

                >

                  Trang {currentPage} / {totalPages}

                </span>



                <button

                  type="button"

                  disabled={currentPage === totalPages}

                  onClick={() =>

                    setCurrentPage((page) =>

                      Math.min(totalPages, page + 1)

                    )

                  }

                  style={{

                    border: "1px solid var(--line)",

                    background: "var(--surface)",

                    color: "var(--text)",

                    padding: "7px 12px",

                    borderRadius: "var(--radius-sm)",

                    fontFamily: "inherit",

                    fontSize: "13px",

                    cursor:

                      currentPage === totalPages

                        ? "not-allowed"

                        : "pointer",

                    opacity:

                      currentPage === totalPages

                        ? 0.45

                        : 1

                  }}

                >

                  Sau →

                </button>

              </div>

            </div>





          </section>



        </main>



      </div>







      {/* DETAIL DRAWER */}



      {selected && (



        <DetailPanel data={selected} onClose={() => setSelected(null)} />



      )}



    </div>



  );



}