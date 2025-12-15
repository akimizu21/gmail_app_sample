// frontend/src/pages/CalendarPage.jsx
import React from "react";
import { mockEvents } from "../mockData";

export default function CalendarPage() {
  return (
    <div className="page">
      <section>
        <h2 className="section-title">カレンダー（プロトタイプ）</h2>
        <p className="section-subtitle">
          本番では月表示のカレンダーを実装予定です。現状は簡易的に、日付ごとのイベントを一覧で確認できます。
        </p>

        <div className="list-stack">
          {mockEvents.map((ev) => (
            <div key={ev.id} className="card">
              <div className="card-meta">
                {ev.date} {ev.time}
              </div>
              <div className="card-title">{ev.title}</div>
              <div className="card-sub">
                {ev.company} ／ {ev.type} ／ {ev.location}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
