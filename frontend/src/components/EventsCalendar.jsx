import React, { useEffect, useMemo, useState } from "react";
import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";
import timeGridPlugin from "@fullcalendar/timegrid";
import interactionPlugin from "@fullcalendar/interaction";
import listPlugin from "@fullcalendar/list";

export default function EventsCalendar() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/events/", {
        credentials: "include",
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setEvents(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const fcEvents = useMemo(() => {
    return events.map((e) => ({
      id: String(e.id),
      title: `${e.company_name ?? ""}${e.company_name ? " " : ""}${e.title}`,
      start: e.start_at,
      end: e.end_at ?? undefined,
      extendedProps: e,
    }));
  }, [events]);

  return (
    <div style={{ padding: 12 }}>
      <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8 }}>
        <h2 style={{ margin: 0 }}>就活カレンダー</h2>

        <button onClick={load} disabled={loading}>
          {loading ? "更新中..." : "再読み込み"}
        </button>

        <button
          onClick={async () => {
            await fetch("http://127.0.0.1:8000/api/events/sync", {
              method: "POST",
              credentials: "include",
            });
            await load();
          }}
        >
          Gmailから同期
        </button>
      </div>

      <FullCalendar
        plugins={[dayGridPlugin, timeGridPlugin, listPlugin, interactionPlugin]}
        initialView="dayGridMonth"
        headerToolbar={{
          left: "prev,next today",
          center: "title",
          right: "dayGridMonth,timeGridWeek,timeGridDay,listWeek",
        }}
        locale="ja"
        height="auto"
        events={fcEvents}
        eventClick={(info) => {
          const e = info.event.extendedProps;
          alert(
            [
              `会社: ${e.company_name ?? "-"}`,
              `タイトル: ${e.title}`,
              `開始: ${e.start_at}`,
              `状態: ${e.status}`,
            ].join("\n")
          );
        }}
      />
    </div>
  );
}
