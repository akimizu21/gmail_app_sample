// src/pages/LoginPage.jsx
import React from "react";
import { useNavigate } from "react-router-dom";
import { GoogleLogin } from "@react-oauth/google";
import { api } from "../api";

export default function LoginPage() {
  const navigate = useNavigate();

  const handleGoogleLogin = async (credentialResponse) => {
    try {
      const token = credentialResponse.credential;
      if (!token) {
        alert("Googleログインに失敗しました");
        return;
      }

      // ★ FastAPI に送信 → セッション作成
      const data = await api.loginWithGoogle(token);

      console.log("ログイン成功:", data);

      // 成功したらダッシュボードへ
      navigate("/dashboard");
    } catch (err) {
      console.error(err);
      alert("ログイン中にエラーが発生しました");
    }
  };

  return (
    <div className="login-root">
      <div className="login-shell">
        <div className="login-card">
          {/* ロゴ */}
          <div className="login-icon">
            <span className="login-icon-sparkle">✶</span>
          </div>

          <h1 className="login-title">JobSync</h1>
          <p className="login-subtitle">
            Gmail と連携して、就活の面接・説明会の日程をまとめて管理します。
          </p>

          {/* ▼ Googleログインボタン */}
          <div style={{ marginTop: "20px" }}>
            <GoogleLogin
              onSuccess={handleGoogleLogin}
              onError={() => {
                alert("Googleログインに失敗しました");
              }}
            />
          </div>

          <div className="login-note">
            <div className="login-security">
              <span className="login-security-icon">🛡</span>
              <span>Google OAuth による安全な認証を利用しています。</span>
            </div>
            <p className="login-terms">
              ログインすることで、利用規約に同意したものとみなされます。
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
