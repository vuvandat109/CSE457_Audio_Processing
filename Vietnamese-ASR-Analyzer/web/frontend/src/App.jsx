import { useEffect, useMemo, useState } from "react";
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

function getStatus(item) {
  if (item?.status === "Đúng" || item?.status === "correct") return "correct";
  if (item?.status === "Sai" || item?.status === "incorrect") return "incorrect";
  if (item?.status === "Lỗi" || item?.status === "failed") return "failed";
  if (Array.isArray(item?.errors) && item.errors.length > 0) return "incorrect";
  return "correct";
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

          {/* So sánh câu chuẩn & Whisper */}
          <div>
            <h3 className="drawer-section-title">So sánh văn bản</h3>
            <div className="sentence-compare">
              <div className="sentence sentence--ref">
                <span className="sentence-label">Chuẩn (Ground Truth)</span>
                <p>{data.ground_truth ?? data.reference ?? data.cau_chuan ?? "-"}</p>
              </div>

              <div className="sentence sentence--pred">
                <span className="sentence-label">Whisper Nhận dạng</span>
                <p>{data.prediction ?? data.whisper ?? data.whisper_text ?? "-"}</p>
              </div>
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
                  const hasDiff = word.reference !== word.prediction;
                  return (
                    <div key={index} className={`word ${hasDiff ? "word-diff" : ""}`}>
                      <div className="word-pair">
                        <span className="ref-word">{word.reference}</span>
                        <span className="arrow">→</span>
                        <span className="word-pred">{word.prediction}</span>
                        {hasDiff && (
                          <span className="error-type-tag">Sai khác âm</span>
                        )}
                      </div>

                      <div className="alignment-card">
                        <table className="phoneme-table">
                          <thead>
                            <tr>
                              <th>Thành phần</th>
                              <th>Chuẩn</th>
                              <th>Whisper</th>
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
  const [audioList, setAudioList] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const [error, setError] = useState("");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // =====================================================
  // LOAD DATA
  // =====================================================
  useEffect(() => {
    Promise.all([
      axios.get(`${API}/api/statistics`),
      axios.get(`${API}/api/audio-list`)
    ])
      .then(([stat, audio]) => {
        setStatistics(stat.data);
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
  }, []);

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

    return data;
  }, [audioList, filter, search]);

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
            <span>Whisper VN v3 • Sẵn sàng</span>
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

          {/* AUDIO LIST TABLE */}
          <section className="section">
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
                    tableData.map((item, index) => {
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
                                `${API}/api/audio-detail/${encodeURIComponent(
                                  item.audio
                                )}`
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