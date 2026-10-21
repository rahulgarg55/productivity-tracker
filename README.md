# ProductivityFlow Enterprise ⚡

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI_0.143-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.12_%7C_3.14-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Database](https://img.shields.io/badge/Database-SQLite_WAL-003B57.svg?logo=sqlite&logoColor=white)](https://sqlite.org/)
[![Tests](https://img.shields.io/badge/Automated_Tests-19%20Passed-10b981.svg)](#-test-verification--code-quality)
[![Architecture](https://img.shields.io/badge/Architecture-Clean_API_+_Electron-blue.svg)](#-system-architecture)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

> **Enterprise activity monitoring, work session telemetry, domain categorization, and Pomodoro focus pacing platform.** Built with a high-throughput Python FastAPI backend, SQLite Write-Ahead Logging (WAL), interactive glassmorphic web dashboard, and a native Electron + TypeScript desktop companion.

---

## 🌐 Live Deployment & Interactive Access

| Environment | Access Link | Description |
| :--- | :--- | :--- |
| **Public Live Tunnel** | [https://coupled-shoes-towers-deposits.trycloudflare.com](https://coupled-shoes-towers-deposits.trycloudflare.com) | Live interactive dashboard with real-time telemetry simulator & analytics |
| **Interactive API Docs** | [https://coupled-shoes-towers-deposits.trycloudflare.com/docs](https://coupled-shoes-towers-deposits.trycloudflare.com/docs) | OpenAPI 3.1 / Swagger documentation for all telemetry and admin endpoints |
| **Local Host** | `http://localhost:8000` | Local development and testing server |

---

## 🚀 Key Features

### 1. Real-Time Telemetry & Contextual Classification
- **Automated Task Categorization**: Automatically categorizes active foreground windows into **Productive**, **Distracted**, or **Idle** states based on application context and window titles.
- **Domain Categories**: Groups activities across **Development** (*VS Code, Terminal, GitHub, Docker*), **Design** (*Figma, Blender, Canva*), **Communication** (*Slack, Teams, Discord*), **Productivity** (*Notion, Obsidian, Jira*), and **Leisure** (*YouTube, Netflix, Social Media*).
- **Interactive Simulator**: Web dashboard includes a 1-click telemetry simulation engine allowing reviewers and clients to test real-time ingestion without needing the desktop companion running.

### 2. Pomodoro Deep Focus Studio
- **Configurable Sprint Modes**: 25-minute Deep Work, 5-minute Short Break, and 15-minute Long Restoration sprints.
- **Synthesized Web Audio Alerts**: Custom dual-tone harmonic audio chime synthesized natively via Web Audio API without external audio file dependencies.
- **Focus Streak Tracking**: Daily focus sprint counter with persistent SQLite storage (`pomodoro_sessions`).

### 3. Glassmorphic Analytics Dashboard
- **Chart.js Visualizations**:
  - **Activity Split Doughnut Chart**: Live percentage breakdown of Productive vs. Distracted vs. Idle sessions.
  - **Domain Category Bar Chart**: Real-time frequency chart across technical and creative domains.
  - **Top Applications Leaderboard**: Ranked process usage with status pills.
- **Live Activity Feed Table**: Filterable by status (`All`, `Productive`, `Distracted`, `Idle`), with instant single-click log deletion and auto-refresh intervals.

### 4. Enterprise Security & Hardening
- **Timing-Safe Authentication**: Cryptographic constant-time comparison (`hmac.compare_digest`) on admin bearer tokens to eliminate timing-attack vulnerabilities.
- **Sliding-Window Rate Limiting**: In-memory rate limiter enforcing a strict 120 req/min budget per client IP with `HTTP 429` backoff protection.
- **OWASP Security Headers**: Enforces `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `X-XSS-Protection`, `Referrer-Policy`, and `Strict-Transport-Security`.

### 5. GDPR Privacy & Compliance
- **GDPR Article 15 (Right of Access)**: Immediate JSON export endpoint (`/api/privacy/export`) allowing users to download their entire telemetry record.
- **GDPR Article 17 (Right to Erasure)**: Configurable retention erasure endpoint (`/api/privacy/erase`) and instant history wipe capability.
- **Zero Keylogging Guarantee**: Transparent system tray notification; strictly captures process name and active window title with zero keyboard logging or covert surveillance.

---

## 🏛 System Architecture

```mermaid
flowchart TD
    subgraph Client Layer
        A["Electron Desktop Companion<br/>(TypeScript / SysTray)"] -->|POST /api/screenshots<br/>(HMAC Bearer Token)| C["FastAPI Enterprise Server"]
        B["Interactive Web Dashboard<br/>(HTML5 / Tailwind / Chart.js)"] -->|GET /api/stats<br/>GET /api/activities<br/>POST /api/simulate| C
    end

    subgraph Security & Middlewares
        C --> D["Security Headers Middleware<br/>(nosniff, SAMEORIGIN, HSTS)"]
        D --> E["In-Memory Sliding Rate Limiter<br/>(120 req/min/IP)"]
        E --> F["Timing-Safe HMAC Validator<br/>(hmac.compare_digest)"]
    end

    subgraph Core Processing Engine
        F --> G["Contextual Classifier<br/>(Dev / Design / Team / Leisure)"]
        G --> H["SQLite 3 Database<br/>(PRAGMA journal_mode=WAL)"]
    end

    subgraph Analytics & Compliance Hub
        H --> I["Focus Scoring Engine<br/>((Productive / Total) * 100)"]
        H --> J["Pomodoro Focus Session Ledger"]
        H --> K["GDPR Art. 15 Export & Art. 17 Erasure"]
    end
```

---

## 🛠 Tech Stack

- **Backend:** FastAPI, Python 3.12 / 3.14, Uvicorn (ASGI)
- **Database:** SQLite 3 with Write-Ahead Logging (`WAL`) mode & custom composite indexes
- **Validation:** Pydantic v2 schemas with strict field-length boundaries
- **Frontend Dashboard:** HTML5, Tailwind CSS, Chart.js, Lucide SVG, Web Audio API
- **Desktop Companion:** Electron, TypeScript, Node.js (`desktop/`)
- **Testing:** Pytest, HTTPX, Requests (19/19 passing test suite)
- **Containerization:** Docker (`Dockerfile`), Docker Compose (`docker-compose.yml`)

---

## 🧪 Test Verification & Code Quality

The project features a full test suite covering functional telemetry, timing-safe authentication, boundary input rejection, rate limiting, and GDPR compliance.

```bash
# Run the automated pytest suite:
python -m pytest tests/
```

### Verified Test Results (19 / 19 Passed):
- `tests/test_enterprise.py`:
  - `test_health_endpoint_healthy` ✅
  - `test_api_health_endpoint_healthy` ✅
  - `test_security_headers_present` ✅
  - `test_auth_timing_safe_token_rejection` ✅
  - `test_input_validation_empty_app_name` ✅
  - `test_input_validation_oversized_fields` ✅
  - `test_paginated_activities_endpoint` ✅
  - `test_privacy_notice_endpoint` ✅
  - `test_privacy_export_endpoint` ✅
  - `test_privacy_erase_endpoint` ✅
- `tests/test_outputs.py`:
  - `test_dashboard_loads` ✅
  - `test_unauthenticated_upload_rejected` ✅
  - `test_invalid_token_upload_rejected` ✅
  - `test_productive_upload_successful` ✅
  - `test_distracted_upload_successful` ✅
  - `test_idle_upload_successful` ✅
  - `test_delete_log` ✅
  - `test_reset_stats` ✅
  - `test_stats_aggregation_correct` ✅

---

## 🏃 Getting Started

### Prerequisites
- Python 3.10+ (tested on Python 3.12 and 3.14)
- Node.js 18+ (for desktop companion)

### 1. Server Setup
```bash
# Clone the repository
git clone https://github.com/rahulgarg55/productivity-tracker.git
cd productivity-tracker

# Install Python requirements
pip install -r environment/app/requirements.txt pytest

# Start the FastAPI server
python -m uvicorn environment.app.main:app --host 0.0.0.0 --port 8000
```
Open [http://localhost:8000](http://localhost:8000) in your browser.

### 2. Desktop Companion Setup (Optional)
```bash
cd desktop
npm install
npm run dev
```

---

## 📜 API Reference Summary

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Web analytics & focus pacing dashboard | No |
| `GET` | `/health` / `/api/health` | Operations status & database connectivity check | No |
| `POST` | `/api/screenshots` | Ingest active window telemetry | **Bearer Token** |
| `POST` | `/api/simulate` | Public demo telemetry simulator | No |
| `GET` | `/api/stats` | Aggregated productivity score & counts | No |
| `GET` | `/api/stats/categories` | Activity distribution across technical domains | No |
| `GET` | `/api/stats/top-apps` | Leaderboard of top detected processes | No |
| `GET` | `/api/activities` | Paginated telemetry feed with status filtering | No |
| `DELETE` | `/api/screenshots/{id}` | Delete a specific telemetry entry | **Bearer Token** |
| `DELETE` | `/api/stats/reset` | Purge all telemetry and reset stats | **Bearer Token** |
| `POST` | `/api/pomodoro/sessions` | Record a completed focus or break sprint | No |
| `GET` | `/api/pomodoro/stats` | Fetch today's focus sprint count and minutes | No |
| `GET` | `/api/privacy/notice` | GDPR transparency disclosure | No |
| `GET` | `/api/privacy/export` | GDPR Art. 15 full JSON data export | **Bearer Token** |
| `DELETE` | `/api/privacy/erase` | GDPR Art. 17 data retention purge | **Bearer Token** |

---

## 👤 Author & Architecture Lead

**Rahul Garg**  
- **GitHub:** [@rahulgarg55](https://github.com/rahulgarg55)  
- **Role:** Full Stack Engineer & Systems Architect  
- **Portfolio:** [Rahul Garg Portfolio](https://github.com/rahulgarg55)
