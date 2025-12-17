// frontend/src/pages/EventDetailPage.jsx
import React, { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { api } from "../api";

const TYPE_OPTIONS = [
  { value: "interview", label: "面接" },
  { value: "briefing", label: "説明会" },
  { value: "other", label: "その他" },
];

function toInputDateTimeValue(isoOrDate) {
  // FastAPIが返すISO文字列(例: 2025-12-10T14:00:00+09:00)を
  // <input type="datetime-local"> 用に "YYYY-MM-DDTHH:mm" にする
  if (!isoOrDate) return "";
  const d = new Date(isoOrDate);
  const pad = (n) => String(n).padStart(2, "0");
  const yyyy = d.getFullYear();
  const mm = pad(d.getMonth() + 1);
  const dd = pad(d.getDate());
  const hh = pad(d.getHours());
  const mi = pad(d.getMinutes());
  return `${yyyy}-${mm}-${dd}T${hh}:${mi}`;
}

function fromInputDateTimeValue(v) {
  // datetime-local は timezone を持たないので、
  // そのまま new Date() でローカル(=JST)として解釈される想定。
  // FastAPI へは ISO 文字列で返す（tz付きになる）
  if (!v) return null;
  return new Date(v).toISOString();
}

export default function EventDetailPage() {
  const { id } = useParams();
  const eventId = Number(id);
  const navigate = useNavigate();

  const [ev, setEv] = useState(null);
  const [loading, setLoading] = useState(true);

  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const [error, setError] = useState(null);

  // 編集フォーム（ev をロードしたら初期化）
  const [form, setForm] = useState({
    company_name: "",
    title: "",
    event_type: "other",
    start_at: "",
    end_at: "",
    location: "",
    memo: "",
    status: "scheduled",
  });

  const dirty = useMemo(() => {
    if (!ev) return false;
    const same =
      (form.company_name || "") === (ev.company_name || "") &&
      (form.title || "") === (ev.title || "") &&
      (form.event_type || "") === (ev.event_type || "") &&
      (form.status || "") === (ev.status || "") &&
      (form.location || "") === (ev.location || "") &&
      (form.memo || "") === (ev.memo || "") &&
      (form.start_at || "") === toInputDateTimeValue(ev.start_at) &&
      (form.end_at || "") === toInputDateTimeValue(ev.end_at);
    return !same;
  }, [ev, form]);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await api.getEvent(eventId);
        setEv(data);

        setForm({
          company_name: data.company_name || "",
          title: data.title || "",
          event_type: data.event_type || "other",
          start_at: toInputDateTimeValue(data.start_at),
          end_at: toInputDateTimeValue(data.end_at),
          location: data.location || "",
          memo: data.memo || "",
          status: data.status || "scheduled",
        });
      } catch (e) {
        console.error(e);
        const msg =
          e?.data?.detail ||
          e?.data?.message ||
          "イベントの取得に失敗しました";
        setError(msg);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [eventId]);

  const onChange = (key) => (e) => {
    setForm((prev) => ({ ...prev, [key]: e.target.value }));
  };

  const handleSave = async () => {
    if (!ev) return;

    // PATCHなので「変更分だけ送る」方式にする（失敗しにくい）
    const payload = {};
    if ((form.company_name || "") !== (ev.company_name || ""))
      payload.company_name = form.company_name || null;
    if ((form.title || "") !== (ev.title || "")) payload.title = form.title;
    if ((form.event_type || "") !== (ev.event_type || ""))
      payload.event_type = form.event_type;
    if ((form.status || "") !== (ev.status || "")) payload.status = form.status;
    if ((form.location || "") !== (ev.location || ""))
      payload.location = form.location || null;
    if ((form.memo || "") !== (ev.memo || "")) payload.memo = form.memo || null;

    const startIso = fromInputDateTimeValue(form.start_at);
    const endIso = fromInputDateTimeValue(form.end_at);

    // start_at は必須なので空は許さない
    if (!startIso) {
      setError("開始日時（start_at）は必須です。");
      return;
    }
    if (toInputDateTimeValue(ev.start_at) !== form.start_at) {
      payload.start_at = startIso;
    }
    if (toInputDateTimeValue(ev.end_at) !== form.end_at) {
      payload.end_at = endIso; // null もあり
    }

    if (Object.keys(payload).length === 0) {
      setError(null);
      return;
    }

    try {
      setSaving(true);
      setError(null);
      const updated = await api.updateEvent(eventId, payload);
      setEv(updated);
      // フォームも同期
      setForm({
        company_name: updated.company_name || "",
        title: updated.title || "",
        event_type: updated.event_type || "other",
        start_at: toInputDateTimeValue(updated.start_at),
        end_at: toInputDateTimeValue(updated.end_at),
        location: updated.location || "",
        memo: updated.memo || "",
        status: updated.status || "scheduled",
      });
    } catch (e) {
      console.error(e);
      const msg =
        e?.data?.detail || e?.data?.message || "保存に失敗しました";
      setError(msg);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!ev) return;
    const ok = window.confirm("この予定を削除します。よろしいですか？");
    if (!ok) return;

    try {
      setDeleting(true);
      setError(null);
      await api.deleteEvent(eventId);
      navigate("/", { replace: true }); // Homeへ戻す（必要なら /calendar でもOK）
    } catch (e) {
      console.error(e);
      const msg =
        e?.data?.detail || e?.data?.message || "削除に失敗しました";
      setError(msg);
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="page">
        <div className="card">
          <div className="card-sub">読み込み中…</div>
        </div>
      </div>
    );
  }

  if (!ev) {
    return <div className="page">イベントが見つかりませんでした。</div>;
  }

  return (
    <div className="page">
      <section className="card">
        <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
          <div>
            <h2 className="section-title">イベント詳細 / 編集</h2>
            <div className="card-sub">
              <Link to="/" className="link">
                ← ホームへ
              </Link>
            </div>
          </div>

          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <button onClick={handleSave} disabled={saving || deleting || !dirty}>
              {saving ? "保存中..." : "保存"}
            </button>
            <button
              onClick={handleDelete}
              disabled={saving || deleting}
              style={{ background: "#fff", border: "1px solid #ddd" }}
            >
              {deleting ? "削除中..." : "削除"}
            </button>
          </div>
        </div>

        {error && (
          <div className="card" style={{ marginTop: 12, border: "1px solid #f3c" }}>
            <div style={{ color: "red" }}>{String(error)}</div>
          </div>
        )}

        <div className="card" style={{ marginTop: 12 }}>
          <div className="card-meta">
            作成: {new Date(ev.created_at).toLocaleString("ja-JP")} / 更新:{" "}
            {new Date(ev.updated_at).toLocaleString("ja-JP")}
          </div>

          <div style={{ display: "grid", gap: 12, marginTop: 12 }}>
            <div style={{ display: "grid", gap: 6 }}>
              <div className="card-sub">会社名</div>
              <input
                value={form.company_name}
                onChange={onChange("company_name")}
                placeholder="例）Sky株式会社"
              />
            </div>

            <div style={{ display: "grid", gap: 6 }}>
              <div className="card-sub">タイトル</div>
              <input value={form.title} onChange={onChange("title")} />
            </div>

            <div style={{ display: "grid", gap: 6 }}>
              <div className="card-sub">種別</div>
              <select value={form.event_type} onChange={onChange("event_type")}>
                {TYPE_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>

            <div style={{ display: "grid", gap: 6 }}>
              <div className="card-sub">状態</div>
              <select value={form.status} onChange={onChange("status")}>
                <option value="scheduled">scheduled</option>
                <option value="cancelled">cancelled</option>
                <option value="done">done</option>
              </select>
            </div>

            <div style={{ display: "grid", gap: 6 }}>
              <div className="card-sub">開始日時</div>
              <input
                type="datetime-local"
                value={form.start_at}
                onChange={onChange("start_at")}
              />
            </div>

            <div style={{ display: "grid", gap: 6 }}>
              <div className="card-sub">終了日時（任意）</div>
              <input
                type="datetime-local"
                value={form.end_at}
                onChange={onChange("end_at")}
              />
            </div>

            <div style={{ display: "grid", gap: 6 }}>
              <div className="card-sub">場所</div>
              <input
                value={form.location}
                onChange={onChange("location")}
                placeholder="オンライン / 東京ビッグサイト など"
              />
            </div>

            <div style={{ display: "grid", gap: 6 }}>
              <div className="card-sub">メモ</div>
              <textarea
                value={form.memo}
                onChange={onChange("memo")}
                rows={4}
                placeholder="URL、持ち物、注意点など"
              />
            </div>

            <div className="card-sub" style={{ marginTop: 6 }}>
              source: <b>{ev.source}</b> / email_id: {ev.email_id ?? "-"}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
