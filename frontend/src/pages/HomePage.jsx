// frontend/src/pages/HomePage.jsx
import React, { useState, useMemo, useEffect } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

const TYPE_LABELS = ["すべて", "面接", "説明会", "その他"];
const TYPE_KEY = {
  面接: "interview",
  説明会: "briefing",
  その他: "other",
};

export default function HomePage() {
  const [query, setQuery] = useState("");
  const [activeType, setActiveType] = useState("すべて");
  const [sortKey, setSortKey] = useState("dateAsc");
  const [events, setEvents] = useState([]);
  const [loadingEvents, setLoadingEvents] = useState(false);
  const [error, setError] = useState(null);

  const loadEvents = async () => {
    try {
      setLoadingEvents(true);
      setError(null);
      const data = await api.fetchEvents(); // ← あなたの api.js に合わせる
      setEvents(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error("fetchEvents error", e);
      setError(e?.data?.detail || "予定の取得に失敗しました");
    } finally {
      setLoadingEvents(false);
    }
  };

  useEffect(() => {
    loadEvents();
  }, []);

  const filteredEvents = useMemo(() => {
    return events
      .filter((ev) => {
        if (activeType !== "すべて") {
          return ev.event_type === TYPE_KEY[activeType];
        }
        return true;
      })
      .filter((ev) => {
        if (!query.trim()) return true;
        const q = query.toLowerCase();
        return (
          (ev.title || "").toLowerCase().includes(q) ||
          (ev.company_name || "").toLowerCase().includes(q)
        );
      })
      .sort((a, b) => {
        const da = a.start_at ? new Date(a.start_at) : new Date(0);
        const db = b.start_at ? new Date(b.start_at) : new Date(0);
        return sortKey === "dateAsc" ? da - db : db - da;
      });
  }, [events, query, activeType, sortKey]);

  const handleDelete = async (evId, e) => {
    // Linkのクリック（遷移）を止める
    e.preventDefault();
    e.stopPropagation();

    const ok = window.confirm("この予定を削除します。よろしいですか？");
    if (!ok) return;

    // 体感を良くするため先にUIから消す（楽観更新）
    const prev = events;
    setEvents((cur) => cur.filter((x) => x.id !== evId));

    try {
      await api.deleteEvent(evId);
    } catch (err) {
      console.error("deleteEvent error", err);
      setError(err?.data?.detail || "削除に失敗しました");
      // 失敗したら戻す
      setEvents(prev);
    }
  };

  const handleEdit = (e) => {
    // Linkに任せて遷移したいけど、ボタンのクリックはカード全体のクリックと区別したい
    e.stopPropagation();
  };

  return (
    <div className="page">
      <div className="page-grid">
        {/* 右：登録済みイベント */}
        <section>
          <h2 className="section-title">予定一覧</h2>
          <p className="section-subtitle">
            登録した就活イベントを検索・絞り込みできます。
          </p>

          {/* 検索 & フィルタ（簡易：必要なら既存UIに合わせてOK） */}
          <div style={{ display: "grid", gap: 10, marginBottom: 12 }}>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="会社名 / タイトルで検索"
            />

            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {TYPE_LABELS.map((t) => (
                <button
                  key={t}
                  onClick={() => setActiveType(t)}
                  style={{
                    border: "1px solid #ddd",
                    background: activeType === t ? "#eef3ff" : "#fff",
                  }}
                >
                  {t}
                </button>
              ))}

              <select
                value={sortKey}
                onChange={(e) => setSortKey(e.target.value)}
                style={{ marginLeft: "auto" }}
              >
                <option value="dateAsc">日付が近い順</option>
                <option value="dateDesc">日付が遠い順</option>
              </select>
            </div>
          </div>

          {error && <p style={{ color: "red" }}>{String(error)}</p>}

          <div className="list-stack">
            {loadingEvents && (
              <div className="card">
                <div className="card-sub">予定を読み込み中です…</div>
              </div>
            )}

            {!loadingEvents &&
              filteredEvents.map((ev) => (
                <Link
                  key={ev.id}
                  to={`/events/${ev.id}`}
                  className="card card-link"
                  style={{ display: "block" }}
                >
                  <div className="card-meta">
                    {ev.start_at
                      ? new Date(ev.start_at).toLocaleString("ja-JP")
                      : "日時未設定"}
                  </div>

                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      gap: 8,
                      alignItems: "flex-start",
                    }}
                  >
                    <div style={{ minWidth: 0 }}>
                      <div className="card-title">{ev.title}</div>
                      <div className="card-sub">
                        {ev.company_name || "（会社名不明）"}
                      </div>
                    </div>

                    <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                      <span className={`badge-type badge-${ev.event_type}`}>
                        {ev.event_type}
                      </span>

                      {/* 編集：詳細ページへ */}
                      <button
                        onClick={handleEdit}
                        style={{
                          border: "1px solid #ddd",
                          background: "#fff",
                          padding: "6px 10px",
                          borderRadius: 8,
                        }}
                      >
                        編集
                      </button>

                      {/* 削除：その場で */}
                      <button
                        onClick={(e) => handleDelete(ev.id, e)}
                        style={{
                          border: "1px solid #f2b8b8",
                          background: "#fff",
                          padding: "6px 10px",
                          borderRadius: 8,
                        }}
                      >
                        削除
                      </button>
                    </div>
                  </div>
                </Link>
              ))}

            {!loadingEvents && filteredEvents.length === 0 && (
              <div className="card">
                <div className="card-sub">
                  条件に一致する予定がありません。検索条件や種別を変えてみてください。
                </div>
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
