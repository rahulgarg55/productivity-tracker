import requests
import pytest
import os
import uuid

BASE_URL = os.getenv("API_URL", "http://localhost:8000")
AUTH_TOKEN = "sys-admin-token-2026"

def headers(token=AUTH_TOKEN):
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

class TestProductivityAPI:

    def test_dashboard_loads(self):
        """Verify that the dashboard HTML loads correctly."""
        r = requests.get(f"{BASE_URL}/", timeout=5)
        assert r.status_code == 200
        assert "Productivity Tracker" in r.text

    def test_unauthenticated_upload_rejected(self):
        """Verify that missing auth token results in 401."""
        payload = {"app_name": "VS Code", "window_title": "test.py"}
        r = requests.post(f"{BASE_URL}/api/screenshots", json=payload, headers=headers(None), timeout=5)
        assert r.status_code == 401

    def test_invalid_token_upload_rejected(self):
        """Verify that invalid auth token results in 401."""
        payload = {"app_name": "VS Code", "window_title": "test.py"}
        r = requests.post(f"{BASE_URL}/api/screenshots", json=payload, headers=headers("bad-token"), timeout=5)
        assert r.status_code == 401

    def test_productive_upload_successful(self):
        """Verify that allowed apps (e.g., vscode) are classified as productive."""
        payload = {"app_name": "VS Code", "window_title": f"project_{uuid.uuid4().hex[:6]}"}
        r = requests.post(f"{BASE_URL}/api/screenshots", json=payload, headers=headers(), timeout=5)
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert data["status"] == "productive"

    def test_distracted_upload_successful(self):
        """Verify that non-allowed apps (e.g., youtube) are classified as distracted."""
        payload = {"app_name": "YouTube Browser", "window_title": "Funny Cats"}
        r = requests.post(f"{BASE_URL}/api/screenshots", json=payload, headers=headers(), timeout=5)
        assert r.status_code == 200
        assert r.json()["status"] == "distracted"

    def test_idle_upload_successful(self):
        """Verify that screensavers are classified as idle."""
        payload = {"app_name": "ScreenSaver", "window_title": "Idle"}
        r = requests.post(f"{BASE_URL}/api/screenshots", json=payload, headers=headers(), timeout=5)
        assert r.status_code == 200
        assert r.json()["status"] == "idle"

    def test_delete_log(self):
        """Verify that a specific log can be deleted."""
        payload = {"app_name": "Test Delete", "window_title": "Test"}
        r = requests.post(f"{BASE_URL}/api/screenshots", json=payload, headers=headers(), timeout=5)
        log_id = r.json()["id"]
        
        del_r = requests.delete(f"{BASE_URL}/api/screenshots/{log_id}", headers=headers(), timeout=5)
        assert del_r.status_code == 200
        
        # Verify it's gone by deleting again
        del_r2 = requests.delete(f"{BASE_URL}/api/screenshots/{log_id}", headers=headers(), timeout=5)
        assert del_r2.status_code == 404

    def test_reset_stats(self):
        """Verify that all logs can be cleared."""
        requests.post(f"{BASE_URL}/api/screenshots", json={"app_name": "Test", "window_title": "Test"}, headers=headers())
        reset_r = requests.delete(f"{BASE_URL}/api/stats/reset", headers=headers(), timeout=5)
        assert reset_r.status_code == 200
        
        stats_r = requests.get(f"{BASE_URL}/api/stats", timeout=5)
        assert stats_r.json()["total_logs"] == 0

    def test_stats_aggregation_correct(self):
        """Verify that the productivity score correctly calculates the percentage of productive tasks."""
        # Create unique apps to not conflict with previous runs
        # We will inject 3 productive and 1 distracted
        for _ in range(3):
            requests.post(f"{BASE_URL}/api/screenshots", json={"app_name": "github", "window_title": "PR"}, headers=headers())
        requests.post(f"{BASE_URL}/api/screenshots", json={"app_name": "reddit", "window_title": "scroll"}, headers=headers())
        
        r = requests.get(f"{BASE_URL}/api/stats", timeout=5)
        assert r.status_code == 200
        data = r.json()
        
        assert "total_logs" in data
        assert "productive_count" in data
        assert "distracted_count" in data
        
        total = data["total_logs"]
        prod = data["productive_count"]
        
        # Calculate expected score
        expected_score = (prod / total) * 100.0 if total > 0 else 0.0
        assert data["productivity_score"] == pytest.approx(expected_score, 0.1)
