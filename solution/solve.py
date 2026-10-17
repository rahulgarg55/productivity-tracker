#!/usr/bin/env python3
import requests
import time

BASE_URL = "http://localhost:8000"

def wait_for_health():
    for _ in range(15):
        try:
            r = requests.get(f"{BASE_URL}/")
            if r.status_code == 200:
                print("Backend is healthy")
                return True
        except Exception:
            pass
        time.sleep(1)
    return False

def patch_backend():
    print("Patching main.py with fixes...")
    with open("environment/app/main.py", "r") as f:
        content = f.read()
    
    # Fix 1: Authentication
    content = content.replace(
        '# Bug 1: Missing Authentication check.',
        'authorization: str = Header(None)\n    if authorization != "Bearer sys-admin-token-2026":\n        raise HTTPException(status_code=401)'
    )
    content = content.replace(
        'async def upload_screenshot(payload: ScreenshotUpload):',
        'async def upload_screenshot(payload: ScreenshotUpload, authorization: str = Header(None)):'
    )
    
    # Fix 2: Categorization
    content = content.replace(
        '# Bug 2: Broken Categorization Logic\n    # Always marks as distracted\n    status = "distracted"',
        'productive_apps = ["vscode", "github", "figma", "terminal"]\n    idle_apps = ["screensaver", "lock", "idle"]\n    if any(app in app_name for app in productive_apps):\n        status = "productive"\n    elif any(app in app_name for app in idle_apps):\n        status = "idle"\n    else:\n        status = "distracted"'
    )
    
    # Fix 3: Aggregation
    content = content.replace(
        'productivity_score = (distracted_count / total_logs) * 100.0',
        'productivity_score = (productive_count / total_logs) * 100.0'
    )
    
    with open("environment/app/main.py", "w") as f:
        f.write(content)
        
    print("Patched.")

if __name__ == "__main__":
    patch_backend()
    print("Please restart the backend service. (e.g., docker compose restart main)")
    print("If running via harness, the harness will automatically reload it if Uvicorn has --reload, or restart the container.")
