import { useEffect, useMemo, useState } from "react";
import { api } from "../api";

// FullCalendar
import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";      // 月
import timeGridPlugin from "@fullcalendar/timegrid";    // 週/日
import interactionPlugin from "@fullcalendar/interaction"; // クリック/ドラッグ


export default function CalendarPage() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState(null);

  const loadEvents = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.fetchEvents();
      setEvents(data);
    } catch (e) {
      setError(e.message ?? "イベント取得に失敗しました");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEvents();
  }, []);

  const handleSync = async () => {
    try {
      setSyncing(true);
      setError(null);
      const data = await api.syncEvents();
      setEvents(data);
    } catch (e) {
      setError(e.message ?? "同期に失敗しました");
    } finally {
      setSyncing(false);
    }
  };

  // APIのevents → FullCalendar形式に変換
  const calendarEvents = useMemo(() => {
    return (events ?? []).map((ev) => ({
      id: String(ev.id),
      title: `${ev.company_name ? ev.company_name + " " : ""}${ev.title ?? ""}`.trim(),
      start: ev.start_at,          // ISO文字列のままでOK
      end: ev.end_at ?? undefined, // 無ければ省略
      extendedProps: ev,           // クリック時に元データ参照したいので保持
    }));
  }, [events]);

  const handleEventClick = (info) => {
    const ev = info.event.extendedProps; // 元のAPIイベント
    alert(
      `会社: ${ev.company_name ?? "-"}\nタイトル: ${ev.title}\n開始: ${ev.start_at}\n状態: ${ev.status}`
    );
  };

  return (
    <div className="page calendar-page">
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <h1 style={{ margin: 0 }}>就活カレンダー</h1>

        <button onClick={handleSync} disabled={syncing}>
          {syncing ? "同期中..." : "Gmailから同期"}
        </button>

        <button onClick={loadEvents} disabled={loading || syncing}>
          更新
        </button>
      </div>

      {error && <p style={{ color: "red" }}>{error}</p>}
      {loading && <p>読み込み中...</p>}

      <div style={{ marginTop: 16 }}>
        <FullCalendar
          plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
          initialView="dayGridMonth"
          headerToolbar={{
            left: "prev,next today",
            center: "title",
            right: "dayGridMonth,timeGridWeek,timeGridDay",
          }}
          locale="ja"
          timeZone="Asia/Tokyo"
          height="auto"
          events={calendarEvents}
          eventClick={handleEventClick}
          nowIndicator={true}
        />
      </div>
    </div>
  );
}
