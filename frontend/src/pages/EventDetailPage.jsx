// frontend/src/pages/EventDetailPage.jsx
import React from "react";
import { useParams } from "react-router-dom";
import { mockEvents } from "../mockData";

export default function EventDetailPage() {
  const { id } = useParams();
  const eventId = Number(id);
  const ev = mockEvents.find((e) => e.id === eventId);

  if (!ev) {
    return <div className="page">イベントが見つかりませんでした。</div>;
  }

  return (
    <div className="page">
      <section className="card">
        <h2 className="section-title">イベント詳細</h2>

        <div className="card" style={{ marginTop: 8 }}>
          <div className="card-meta">
            {ev.date} {ev.time}
          </div>
          <div className="card-title">{ev.title}</div>
          <div className="card-sub">
            {ev.company} ／ {ev.type}
          </div>
          <div className="card-sub" style={{ marginTop: 6 }}>
            場所：{ev.location}
          </div>
          <div className="card-sub" style={{ marginTop: 10 }}>
            ※本番ではここから編集・削除、元メールへのリンク表示などを行う予定です。
          </div>
        </div>
      </section>
    </div>
  );
}
