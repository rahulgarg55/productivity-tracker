import sqlite3
from pathlib import Path
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Productivity Tracker API",
    description="Enterprise Activity Tracking, Work Session Telemetry & Productivity Score Intelligence",
    version="2.0.0"
)

# Mount static files for the dashboard
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

DB_PATH = BASE_DIR / "productivity.db"

# Database setup
def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            app_name TEXT NOT NULL,
            window_title TEXT NOT NULL,
            status TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

class ScreenshotUpload(BaseModel):
    app_name: str
    window_title: str
    base64_image: Optional[str] = None

@app.post("/api/screenshots")
async def upload_screenshot(payload: ScreenshotUpload, authorization: Optional[str] = Header(None)):
    # 1. Authentication check
    if not authorization or authorization != "Bearer sys-admin-token-2026":
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid or missing bearer token")
    
    # 2. Activity Categorization Logic
    app_lower = payload.app_name.lower().strip()
    productive_keywords = ["vscode", "vs code", "github", "figma", "terminal", "pycharm", "cursor", "intellij", "slack"]
    idle_keywords = ["screensaver", "lock", "idle", "sleep"]
    
    if any(k in app_lower for k in productive_keywords):
        status = "productive"
    elif any(k in app_lower for k in idle_keywords):
        status = "idle"
    else:
        status = "distracted"
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO activity_logs (app_name, window_title, status) VALUES (?, ?, ?)",
        (payload.app_name, payload.window_title, status)
    )
    log_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {"id": log_id, "status": status, "message": "Log saved"}

@app.get("/api/stats")
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

@app.delete("/api/screenshots/{log_id}")
async def delete_log(log_id: int, authorization: Optional[str] = Header(None)):
    if not authorization or authorization != "Bearer sys-admin-token-2026":
        raise HTTPException(status_code=401, detail="Unauthorized")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM activity_logs WHERE id = ?", (log_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    if not deleted:
        raise HTTPException(status_code=404, detail="Log not found")
    return {"message": "Log deleted"}

@app.delete("/api/stats/reset")
async def reset_stats(authorization: Optional[str] = Header(None)):
    if not authorization or authorization != "Bearer sys-admin-token-2026":
        raise HTTPException(status_code=401, detail="Unauthorized")
    conn = get_db()
    conn.execute("DELETE FROM activity_logs")
    conn.commit()
    conn.close()
    return {"message": "All stats reset"}

@app.get("/")
async def serve_dashboard():
    html_path = BASE_DIR / "static" / "index.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Dashboard UI not found")
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
    return HTMLResponse(content=html, status_code=200)
