// frontend/src/pages/EmailReviewPage.jsx
import React from "react";
import { useParams, useNavigate } from "react-router-dom";
import { mockEmails } from "../mockData";

export default function EmailReviewPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const emailId = Number(id);
  const email = mockEmails.find((e) => e.id === emailId);

  if (!email) {
    return <div className="page">メールが見つかりませんでした。</div>;
  }

  const handleRegister = () => {
    alert("ここで予定を登録する想定です（モック）");
    navigate("/");
  };

  return (
    <div className="page">
      <section className="card">
        <h2 className="section-title">メールから予定登録</h2>
        <p className="section-subtitle">
          メール本文から日程・会社名などを抽出し、カレンダー用の予定として登録する画面です。
        </p>

        <div className="card" style={{ marginBottom: 12 }}>
          <div className="card-meta">{email.from}</div>
          <div className="card-title">{email.subject}</div>
          <div className="card-sub">{email.receivedAt}</div>
        </div>

        <div className="field">
          <label className="field-label">会社名</label>
          <input
            className="field-input"
            defaultValue="（メール解析から自動抽出予定）"
          />
        </div>

        <div className="field">
          <label className="field-label">イベント種別</label>
          <select className="field-select" defaultValue="面接">
            <option>面接</option>
            <option>説明会</option>
            <option>その他</option>
          </select>
        </div>

        <div className="field">
          <label className="field-label">日付</label>
          <input className="field-input" type="date" />
        </div>

        <div className="field" style={{ display: "flex", gap: 8 }}>
          <div style={{ flex: 1 }}>
            <label className="field-label">開始時間</label>
            <input className="field-input" type="time" />
          </div>
          <div style={{ flex: 1 }}>
            <label className="field-label">終了時間</label>
            <input className="field-input" type="time" />
          </div>
        </div>

        <button onClick={handleRegister} className="btn btn-primary">
          この内容で予定を登録（モック）
        </button>
      </section>
    </div>
  );
}
