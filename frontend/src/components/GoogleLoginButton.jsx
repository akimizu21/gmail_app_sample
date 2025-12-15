// src/components/GoogleLoginButton.jsx
import React from "react";
import { GoogleLogin } from "@react-oauth/google";
import { api } from "../api";

export function GoogleLoginButton({ onLoggedIn }) {
  const handleSuccess = async (credentialResponse) => {
    try {
      const token = credentialResponse.credential;
      if (!token) return;

      const data = await api.loginWithGoogle(token);

      // 親に通知（ユーザー情報と Gmail連携状況）
      onLoggedIn(data.user, data.gmail_authorized);
    } catch (e) {
      console.error(e);
      alert("ログインに失敗しました");
    }
  };

  return (
    <GoogleLogin
      onSuccess={handleSuccess}
      onError={() => {
        alert("Googleログインに失敗しました");
      }}
    />
  );
}
