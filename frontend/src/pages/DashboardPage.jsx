// src/pages/DashboardPage.jsx
import React, { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { api } from "../api";
import { GmailConnectButton } from "../components/GmailConnectButton";

export default function DashboardPage() {
  const location = useLocation();
  const [user, setUser] = useState(null);
  const [gmailAuthorized, setGmailAuthorized] = useState(false);
  const [emails, setEmails] = useState([]);

  const fetchUser = async () => {
    try {
      const data = await api.getCurrentUser();
      setUser({
        google_id: data.google_id,
        email: data.email,
        name: data.name,
      });
      setGmailAuthorized(data.gmail_authorized);
    } catch (e) {
      setUser(null);
      setGmailAuthorized(false);
    }
  };

  useEffect(() => {
    fetchUser();
  }, []);

  // Gmail認証結果 (?gmail_auth=success) を拾う
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const gmailAuth = params.get("gmail_auth");

    if (gmailAuth === "success") {
      fetchUser();
    } else if (gmailAuth === "error") {
      alert("Gmail連携に失敗しました");
    }
  }, [location.search]);

  const handleFetchEmails = async () => {
    try {
      const data = await api.getEmails();
      setEmails(data.emails || []);
    } catch (e) {
      console.error(e);
      const detail = e.data && e.data.detail;
      if (e.status === 401 && detail && detail.needs_auth) {
        alert("まず Gmail を連携してください");
      } else if (e.status === 401) {
        alert("ログインしてください");
      } else {
        alert("メール取得に失敗しました");
      }
    }
  };

  return (
    <div>
      <h1>ダッシュボード</h1>

      {user ? (
        <>
          <p>ログイン中: {user.email}</p>
          <p>Gmail連携: {gmailAuthorized ? "済み" : "未連携"}</p>

          {!gmailAuthorized && <GmailConnectButton />}

          {gmailAuthorized && (
            <>
              <button onClick={handleFetchEmails}>メールを取得する</button>
              <ul>
                {emails.map((m) => (
                  <li key={m.id}>
                    <strong>{m.subject}</strong> — {m.from}
                    <div>{m.snippet}</div>
                  </li>
                ))}
              </ul>
            </>
          )}
        </>
      ) : (
        <p>ログインしていません</p>
      )}
    </div>
  );
}
