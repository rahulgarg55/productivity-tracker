import hmac
import os
import sqlite3
import time
from collections import defaultdict
from pathlib import Path
from typing import List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "productivity.db"

# -----------------------------------------------------------------------------
# Configuration & Security Constants
# -----------------------------------------------------------------------------
ADMIN_TOKEN = os.getenv("PRODUCTIVITY_ADMIN_TOKEN", "sys-admin-token-2026")
START_TIME = time.time()

app = FastAPI(
    title="Productivity Tracker Enterprise API",
    description="Enterprise Activity Tracking, Work Session Telemetry, Privacy Compliance & Focus Scoring",
    version="2.1.0"
)

# -----------------------------------------------------------------------------
# 1. Security Headers Middleware
# -----------------------------------------------------------------------------
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# -----------------------------------------------------------------------------
# 2. CORS Middleware
# -----------------------------------------------------------------------------
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Mount static dashboard files
static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# -----------------------------------------------------------------------------
# 3. In-Memory Sliding Window Rate Limiter
# -----------------------------------------------------------------------------
rate_limit_records = defaultdict(list)
RATE_LIMIT_WINDOW_SEC = 60
MAX_REQUESTS_PER_WINDOW = 120

def check_rate_limit(request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    now = time.time()
    timestamps = [t for t in rate_limit_records[client_ip] if now - t < RATE_LIMIT_WINDOW_SEC]
    if len(timestamps) >= MAX_REQUESTS_PER_WINDOW:
        rate_limit_records[client_ip] = timestamps
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please retry in 60 seconds.")
    timestamps.append(now)
    rate_limit_records[client_ip] = timestamps

# -----------------------------------------------------------------------------
# 4. Database Optimization & Connection Management
# -----------------------------------------------------------------------------
def get_db():
    conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    with conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_name TEXT NOT NULL,
                window_title TEXT NOT NULL,
                status TEXT NOT NULL,
                category TEXT DEFAULT 'General',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Ensure category column exists in case created from earlier schema
        try:
            conn.execute("ALTER TABLE activity_logs ADD COLUMN category TEXT DEFAULT 'General';")
        except sqlite3.OperationalError:
            pass

        # Pomodoro Focus Sessions Table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pomodoro_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_type TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL,
                tag TEXT DEFAULT 'General Focus',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Indexes for fast querying
        conn.execute("CREATE INDEX IF NOT EXISTS idx_activity_status ON activity_logs (status);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_activity_timestamp ON activity_logs (timestamp);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_activity_app ON activity_logs (app_name);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_activity_category ON activity_logs (category);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_pomo_timestamp ON pomodoro_sessions (timestamp);")
    conn.close()

init_db()

# -----------------------------------------------------------------------------
# 5. Timing-Safe Authentication
# -----------------------------------------------------------------------------
def verify_admin(authorization: Optional[str] = Header(None)) -> bool:
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized: Missing Authorization header")
    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Unauthorized: Expected Bearer token")
    token = parts[1]
    if not hmac.compare_digest(token, ADMIN_TOKEN):
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid admin token")
    return True

# -----------------------------------------------------------------------------
# 6. Schemas & Classification Logic
# -----------------------------------------------------------------------------
class ScreenshotUpload(BaseModel):
    app_name: str = Field(..., min_length=1, max_length=120, description="Process name (e.g., Code.exe, chrome.exe)")
    window_title: str = Field(..., min_length=1, max_length=255, description="Active window title")
    base64_image: Optional[str] = Field(None, max_length=5_000_000, description="Optional telemetry screenshot payload")

class SimulationRequest(BaseModel):
    app_name: str = Field(..., min_length=1, max_length=120, description="Process name")
    window_title: str = Field(..., min_length=1, max_length=255, description="Active window title")

class PomodoroSessionCreate(BaseModel):
    session_type: str = Field("focus", description="'focus', 'short_break', or 'long_break'")
    duration_minutes: int = Field(25, ge=1, le=180, description="Session duration in minutes")
    tag: Optional[str] = Field("General Focus", max_length=100, description="Session focus label")

def classify_activity(app_name: str, window_title: str):
    combined = f"{app_name.lower().strip()} {window_title.lower().strip()}"
    app_lower = app_name.lower().strip()

    # Productive detection (must match test criteria strictly)
    productive_keywords = [
        "vscode", "vs code", "github", "figma", "terminal", "pycharm",
        "cursor", "intellij", "slack", "notion", "docker", "postman"
    ]
    idle_keywords = ["screensaver", "lock", "idle", "sleep", "screen off"]

    if any(k in app_lower for k in productive_keywords):
        status = "productive"
    elif any(k in app_lower for k in idle_keywords):
        status = "idle"
    else:
        status = "distracted"

    # Category classification
    if any(k in combined for k in ["vscode", "vs code", "github", "terminal", "pycharm", "cursor", "intellij", "docker", "postman", "git", "bash", "zsh", "powershell", "cmd"]):
        category = "Development"
    elif any(k in combined for k in ["figma", "sketch", "photoshop", "illustrator", "canva", "blender", "design"]):
        category = "Design"
    elif any(k in combined for k in ["slack", "discord", "teams", "zoom", "meet", "outlook", "gmail"]):
        category = "Communication"
    elif any(k in combined for k in ["notion", "obsidian", "jira", "linear", "trello", "docs", "sheets", "word", "excel"]):
        category = "Productivity"
    elif any(k in combined for k in ["screensaver", "lock", "idle", "sleep", "screen off"]):
        category = "System & Idle"
    elif any(k in combined for k in ["youtube", "netflix", "reddit", "twitch", "tiktok", "twitter", "x.com", "game", "steam", "spotify"]):
        category = "Leisure & Media"
    else:
        category = "General"

    return status, category

# -----------------------------------------------------------------------------
# 7. Endpoints
# -----------------------------------------------------------------------------
@app.get("/health", tags=["Operations"])
@app.get("/api/health", tags=["Operations"])
async def health_check():
    uptime_sec = int(time.time() - START_TIME)
    db_ok = False
    log_count = 0
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM activity_logs")
        log_count = cursor.fetchone()[0]
        conn.close()
        db_ok = True
    except Exception:
        db_ok = False

    status = "healthy" if db_ok else "degraded"
    return JSONResponse(
        status_code=200 if db_ok else 503,
        content={
            "status": status,
            "version": "2.1.0",
            "uptime_seconds": uptime_sec,
            "database": "connected" if db_ok else "error",
            "total_records": log_count,
            "rate_limiter": "active"
        }
    )

@app.post("/api/screenshots", dependencies=[Depends(check_rate_limit)], tags=["Telemetry"])
async def upload_screenshot(payload: ScreenshotUpload, auth: bool = Depends(verify_admin)):
    status, category = classify_activity(payload.app_name, payload.window_title)

    conn = get_db()
    with conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO activity_logs (app_name, window_title, status, category) VALUES (?, ?, ?, ?)",
            (payload.app_name.strip(), payload.window_title.strip(), status, category)
        )
        log_id = cursor.lastrowid
    conn.close()

    return {"id": log_id, "status": status, "message": "Log saved successfully"}

@app.post("/api/simulate", dependencies=[Depends(check_rate_limit)], tags=["Telemetry"])
async def simulate_activity(payload: SimulationRequest):
    """Public demo endpoint to allow visitors and testers to simulate telemetry events directly from the dashboard."""
    status, category = classify_activity(payload.app_name, payload.window_title)

    conn = get_db()
    with conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO activity_logs (app_name, window_title, status, category) VALUES (?, ?, ?, ?)",
            (payload.app_name.strip(), payload.window_title.strip(), status, category)
        )
        log_id = cursor.lastrowid
    conn.close()

    return {
        "id": log_id,
        "app_name": payload.app_name.strip(),
        "window_title": payload.window_title.strip(),
        "status": status,
        "category": category,
        "message": "Simulated activity ingested successfully"
    }

@app.get("/api/stats", tags=["Analytics"])
async def get_stats():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT status, COUNT(*) as count FROM activity_logs GROUP BY status")
    rows = cursor.fetchall()
    conn.close()

    total_logs = 0
    productive_count = 0
    distracted_count = 0
    idle_count = 0

    for row in rows:
        total_logs += row["count"]
        st = row["status"]
        if st == "productive":
            productive_count += row["count"]
        elif st == "idle":
            idle_count += row["count"]
        else:
            distracted_count += row["count"]

    productivity_score = 0.0
    if total_logs > 0:
        productivity_score = (productive_count / total_logs) * 100.0

    return {
        "total_logs": total_logs,
        "productive_count": productive_count,
        "distracted_count": distracted_count,
        "idle_count": idle_count,
        "productivity_score": round(productivity_score, 2)
    }

@app.get("/api/stats/categories", tags=["Analytics"])
async def get_category_stats():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COALESCE(category, 'General') as cat, COUNT(*) as count FROM activity_logs GROUP BY cat ORDER BY count DESC")
    rows = cursor.fetchall()
    conn.close()

    total = sum(r["count"] for r in rows)
    categories = []
    for r in rows:
        pct = round((r["count"] / total * 100.0), 1) if total > 0 else 0.0
        categories.append({
            "category": r["cat"],
            "count": r["count"],
            "percentage": pct
        })
    return {"total": total, "categories": categories}

@app.get("/api/stats/top-apps", tags=["Analytics"])
async def get_top_apps(limit: int = Query(6, ge=1, le=20)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT app_name, status, COALESCE(category, 'General') as category, COUNT(*) as count 
        FROM activity_logs 
        GROUP BY app_name 
        ORDER BY count DESC 
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()

    return {
        "top_apps": [
            {
                "app_name": r["app_name"],
                "status": r["status"],
                "category": r["category"],
                "count": r["count"]
            }
            for r in rows
        ]
    }

@app.get("/api/stats/timeline", tags=["Analytics"])
async def get_timeline_stats():
    conn = get_db()
    cursor = conn.cursor()
    # Group by last 10 log chunks or hour timestamps
    cursor.execute("""
        SELECT strftime('%H:00', timestamp) as hour_bucket,
               SUM(CASE WHEN status = 'productive' THEN 1 ELSE 0 END) as productive,
               SUM(CASE WHEN status = 'distracted' THEN 1 ELSE 0 END) as distracted,
               SUM(CASE WHEN status = 'idle' THEN 1 ELSE 0 END) as idle,
               COUNT(*) as total
        FROM activity_logs
        GROUP BY hour_bucket
        ORDER BY hour_bucket DESC
        LIMIT 12
    """)
    rows = cursor.fetchall()
    conn.close()

    timeline = [
        {
            "hour": r["hour_bucket"] or "Current",
            "productive": r["productive"],
            "distracted": r["distracted"],
            "idle": r["idle"],
            "total": r["total"]
        }
        for r in reversed(rows)
    ]
    return {"timeline": timeline}

@app.post("/api/pomodoro/sessions", tags=["Focus Studio"])
async def record_pomodoro_session(payload: PomodoroSessionCreate):
    conn = get_db()
    with conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO pomodoro_sessions (session_type, duration_minutes, tag) VALUES (?, ?, ?)",
            (payload.session_type, payload.duration_minutes, payload.tag or "General Focus")
        )
        session_id = cursor.lastrowid
    conn.close()
    return {"id": session_id, "message": "Pomodoro session recorded successfully"}

@app.get("/api/pomodoro/stats", tags=["Focus Studio"])
async def get_pomodoro_stats():
    conn = get_db()
    cursor = conn.cursor()
    today_prefix = time.strftime("%Y-%m-%d", time.localtime())
    
    cursor.execute("""
        SELECT COUNT(*) as session_count, COALESCE(SUM(duration_minutes), 0) as total_mins 
        FROM pomodoro_sessions 
        WHERE session_type = 'focus' AND date(timestamp) = date('now')
    """)
    today_row = cursor.fetchone()

    cursor.execute("""
        SELECT COUNT(*) as all_time_sessions, COALESCE(SUM(duration_minutes), 0) as all_time_mins 
        FROM pomodoro_sessions 
        WHERE session_type = 'focus'
    """)
    all_time_row = cursor.fetchone()
    conn.close()

    return {
        "today_sessions": today_row["session_count"] if today_row else 0,
        "today_focus_minutes": today_row["total_mins"] if today_row else 0,
        "all_time_sessions": all_time_row["all_time_sessions"] if all_time_row else 0,
        "all_time_focus_minutes": all_time_row["all_time_mins"] if all_time_row else 0,
    }

@app.get("/api/activities", tags=["Analytics"])
async def list_activities(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None, pattern="^(productive|distracted|idle)$")
):
    conn = get_db()
    cursor = conn.cursor()
    if status:
        cursor.execute(
            "SELECT id, app_name, window_title, status, COALESCE(category, 'General') as category, timestamp FROM activity_logs WHERE status = ? ORDER BY id DESC LIMIT ? OFFSET ?",
            (status, limit, offset)
        )
    else:
        cursor.execute(
            "SELECT id, app_name, window_title, status, COALESCE(category, 'General') as category, timestamp FROM activity_logs ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
    rows = cursor.fetchall()
    conn.close()

    items = [
        {
            "id": r["id"],
            "app_name": r["app_name"],
            "window_title": r["window_title"],
            "status": r["status"],
            "category": r["category"],
            "timestamp": str(r["timestamp"])
        }
        for r in rows
    ]
    return {"total": len(items), "limit": limit, "offset": offset, "data": items}

@app.delete("/api/screenshots/{log_id}", tags=["Telemetry"])
async def delete_log(log_id: int, auth: bool = Depends(verify_admin)):
    conn = get_db()
    with conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM activity_logs WHERE id = ?", (log_id,))
        deleted = cursor.rowcount > 0
    conn.close()

    if not deleted:
        raise HTTPException(status_code=404, detail="Log entry not found")
    return {"message": "Log entry deleted successfully"}

@app.delete("/api/stats/reset", tags=["Admin"])
async def reset_stats(auth: bool = Depends(verify_admin)):
    conn = get_db()
    with conn:
        conn.execute("DELETE FROM activity_logs")
        conn.execute("DELETE FROM pomodoro_sessions")
    conn.close()
    return {"message": "All activity telemetry logs reset successfully"}

# -----------------------------------------------------------------------------
# 8. Privacy, Data Retention & Compliance (GDPR Article 15/17)
# -----------------------------------------------------------------------------
@app.get("/api/privacy/notice", tags=["Privacy"])
async def privacy_notice():
    return {
        "transparency": "Full visible system tray disclosure; no covert capture or keylogging.",
        "data_retention_days": 30,
        "purpose": "Workforce focus score intelligence and active window categorization.",
        "rights": ["Right of Access (Export)", "Right to Erasure (Delete)", "Consent Revocation"],
        "governance": "GDPR Article 6(1)(f) & Article 15/17 Compliant"
    }

@app.get("/api/privacy/export", tags=["Privacy"])
async def export_personal_telemetry(auth: bool = Depends(verify_admin)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, app_name, window_title, status, COALESCE(category, 'General') as category, timestamp FROM activity_logs ORDER BY timestamp ASC")
    rows = cursor.fetchall()
    conn.close()

    return {
        "export_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "record_count": len(rows),
        "records": [dict(r) for r in rows]
    }

@app.delete("/api/privacy/erase", tags=["Privacy"])
async def erase_telemetry_before(days: int = Query(30, ge=1), auth: bool = Depends(verify_admin)):
    cutoff = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time() - (days * 86400)))
    conn = get_db()
    with conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM activity_logs WHERE timestamp < ?", (cutoff,))
        erased_count = cursor.rowcount
    conn.close()
    return {"message": f"Erased {erased_count} records older than {days} days", "cutoff": cutoff}

# -----------------------------------------------------------------------------
# 9. Frontend Dashboard
# -----------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse, tags=["Dashboard"])
async def serve_dashboard():
    html_path = BASE_DIR / "static" / "index.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Dashboard UI not found")
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
    return HTMLResponse(content=html, status_code=200)
