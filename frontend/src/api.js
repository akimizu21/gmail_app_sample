// src/api.js
const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

async function apiFetch(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    // ★ これがないと Cookie（セッション）が保存・送信されない
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  let data = {};
  try {
    data = await res.json();
  } catch (e) {
    // JSONじゃないレスポンスは無視
  }

  if (!res.ok) {
    throw { status: res.status, data };
  }

  return data;
}

export const api = {
  loginWithGoogle(token) {
    return apiFetch("/api/auth/google", {
      method: "POST",
      body: JSON.stringify({ token }),
    });
  },

  logout() {
    return apiFetch("/api/auth/logout", { method: "POST" });
  },

  getCurrentUser() {
    return apiFetch("/api/user");
  },

  getGmailAuthorizeUrl() {
    return apiFetch("/api/gmail/authorize");
  },

  getEmails() {
    return apiFetch("/api/gmail");
  },
};


// frontend/src/api.js

const BASE_URL = "http://localhost:8000";

async function fetchJson(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    credentials: "include", // ← セッションCookie必須
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  const data = await res.json().catch(() => null);

  if (!res.ok) {
    const err = new Error("API error");
    err.status = res.status;
    err.data = data;
    throw err;
  }

  return data;
}

