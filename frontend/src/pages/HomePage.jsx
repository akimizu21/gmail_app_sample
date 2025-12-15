// frontend/src/pages/HomePage.jsx
import React, { useState, useMemo, useEffect } from "react";
import { Link } from "react-router-dom";
import { api } from "../api"; // ★ 追加

const TYPE_LABELS = ["すべて", "面接", "説明会", "その他"];
const TYPE_KEY = {
  面接: "面接",
  説明会: "説明会",
  その他: "その他",
};

export default function HomePage() {
  const [query, setQuery] = useState("");
  const [activeType, setActiveType] = useState("すべて");
  const [sortKey, setSortKey] = useState("dateAsc");
  const [events, setEvents] = useState([]);
  const [loadingEvents, setLoadingEvents] = useState(false);

  // ★ マウント時に API からイベントを取得
  useEffect(() => {
    const load = async () => {
      try {
        setLoadingEvents(true);
        const data = await api.getEvents();
        setEvents(data); // data は EventRead[] の想定
      } catch (e) {
        console.error("getEvents error", e);
        // 必要ならエラーメッセージを state で持つ
      } finally {
        setLoadingEvents(false);
      }
    };
    load();
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

  return (
    <div className="page">
      <div className="page-grid">
        {/* 左：未処理メール（ここはまだ mock のままでもOK） */}
        {/* ... 省略 ... */}

        {/* 右：登録済みイベント（一覧＋検索＋フィルタ） */}
        <section>
          <h2 className="section-title">予定一覧</h2>
          <p className="section-subtitle">
            登録した就活イベントを検索・絞り込みできます。
          </p>

          {/* 検索ボックス & タブ & ソートは既存のままでOK */}

          {/* イベント一覧 */}
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
                    }}
                  >
                    <div>
                      <div className="card-title">{ev.title}</div>
                      <div className="card-sub">
                        {ev.company_name || "（会社名不明）"}
                      </div>
                    </div>
                    <span className={`badge-type badge-${ev.event_type}`}>
                      {ev.event_type}
                    </span>
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

