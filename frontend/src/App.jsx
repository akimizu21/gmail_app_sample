// src/App.jsx
import React from "react";
import { Routes, Route, Link, useLocation } from "react-router-dom";

import LoginPage from "./pages/LoginPage";
import HomePage from "./pages/HomePage";
import CalendarPage from "./pages/CalendarPage";
import EmailReviewPage from "./pages/EmailReviewPage";
import EventDetailPage from "./pages/EventDetailPage";
import DashboardPage from "./pages/DashboardPage"; // ★ これ追加

function Header() {
  const location = useLocation();

  if (location.pathname === "/login") {
    return null;
  }

  const isActive = (path) => location.pathname === path;

  return (
    <header className="app-header">
      <div className="app-title">
        Job Sync
        <span>就活予定整理アプリ</span>
      </div>
      <nav className="nav-links">
        <Link
          to="/"
          className={`nav-link ${isActive("/") ? "nav-link-active" : ""}`}
        >
          ホーム
        </Link>
        <Link
          to="/calendar"
          className={`nav-link ${
            isActive("/calendar") ? "nav-link-active" : ""
          }`}
        >
          カレンダー
        </Link>
        <Link
          to="/dashboard"
          className={`nav-link ${
            isActive("/dashboard") ? "nav-link-active" : ""
          }`}
        >
          ダッシュボード
        </Link>
        <Link
          to="/login"
          className={`nav-link ${
            isActive("/login") ? "nav-link-active" : ""
          }`}
        >
          ログイン
        </Link>
      </nav>
    </header>
  );
}

export default function App() {
  return (
    <div className="app-root">
      <div className="app-shell">
        <Header />

        <main className="page">
          <Routes>
            <Route path="/login" element={<LoginPage />} />

            <Route path="/" element={<HomePage />} />
            <Route path="/calendar" element={<CalendarPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />

            <Route path="/emails/:id" element={<EmailReviewPage />} />
            <Route path="/events/:id" element={<EventDetailPage />} />

            <Route path="*" element={<HomePage />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
