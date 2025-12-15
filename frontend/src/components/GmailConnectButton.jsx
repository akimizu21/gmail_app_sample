// src/components/GmailConnectButton.jsx
import React from "react";
import { api } from "../api";

export function GmailConnectButton({ disabled }) {
  const handleConnect = async () => {
    try {
      const data = await api.getGmailAuthorizeUrl();
      if (data.authorization_url) {
        // Googleの同意画面へリダイレクト
        window.location.href = data.authorization_url;
      } else {
        alert("認証URLの取得に失敗しました");
      }
    } catch (e) {
      console.error(e);
      if (e.status === 401) {
        alert("まずアプリにログインしてください");
      } else {
        alert("Gmail連携の開始に失敗しました");
      }
    }
  };

  return (
    <button onClick={handleConnect} disabled={disabled}>
      Gmail を連携する
    </button>
  );
}
