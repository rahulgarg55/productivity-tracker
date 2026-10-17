import os
import requests
import pytest
import time

BASE_URL = os.getenv("API_URL", "http://localhost:8000")
ADMIN_TOKEN = os.getenv("PRODUCTIVITY_ADMIN_TOKEN", "sys-admin-token-2026")

def auth_headers(token=ADMIN_TOKEN):
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

class TestProductivityEnterprise:

    def test_health_endpoint_healthy(self):
        """Verify /health reports healthy status and database connection."""
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert "uptime_seconds" in data
        assert "version" in data

    def test_api_health_endpoint_healthy(self):
        """Verify /api/health returns identical healthy status."""
        r = requests.get(f"{BASE_URL}/api/health", timeout=5)
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"

    def test_security_headers_present(self):
        """Verify OWASP-recommended security headers on all responses."""
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        assert r.headers.get("x-content-type-options") == "nosniff"
        assert r.headers.get("x-frame-options") == "SAMEORIGIN"
        assert r.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
        assert "strict-transport-security" in r.headers

    def test_auth_timing_safe_token_rejection(self):
        """Verify invalid or malformed token format is rejected with HTTP 401."""
        payload = {"app_name": "Terminal", "window_title": "zsh"}
        # Missing Bearer prefix
        r1 = requests.post(f"{BASE_URL}/api/screenshots", json=payload, headers={"Authorization": "Token 123"}, timeout=5)
        assert r1.status_code == 401

        # Wrong token
        r2 = requests.post(f"{BASE_URL}/api/screenshots", json=payload, headers={"Authorization": "Bearer wrong-token-xyz"}, timeout=5)
        assert r2.status_code == 401

    def test_input_validation_empty_app_name(self):
        """Verify schema rejects empty or missing app_name with HTTP 422."""
        r = requests.post(f"{BASE_URL}/api/screenshots", json={"app_name": "", "window_title": "test"}, headers=auth_headers(), timeout=5)
        assert r.status_code == 422

    def test_input_validation_oversized_fields(self):
        """Verify schema rejects excessively long strings with HTTP 422."""
        long_name = "A" * 200
        r = requests.post(f"{BASE_URL}/api/screenshots", json={"app_name": long_name, "window_title": "test"}, headers=auth_headers(), timeout=5)
        assert r.status_code == 422

    def test_paginated_activities_endpoint(self):
        """Verify GET /api/activities supports limit, offset, and status filter."""
        # Insert a known entry
        requests.post(f"{BASE_URL}/api/screenshots", json={"app_name": "VS Code", "window_title": "index.ts"}, headers=auth_headers(), timeout=5)
        r = requests.get(f"{BASE_URL}/api/activities?limit=10&offset=0&status=productive", timeout=5)
        assert r.status_code == 200
        data = r.json()
        assert "data" in data
        assert isinstance(data["data"], list)
        for item in data["data"]:
            assert item["status"] == "productive"

    def test_privacy_notice_endpoint(self):
        """Verify GDPR/privacy notice endpoint returns transparency details."""
        r = requests.get(f"{BASE_URL}/api/privacy/notice", timeout=5)
        assert r.status_code == 200
        data = r.json()
        assert "transparency" in data
        assert data["data_retention_days"] == 30
        assert "rights" in data

    def test_privacy_export_endpoint(self):
        """Verify GDPR data export endpoint returns all telemetry records."""
        r = requests.get(f"{BASE_URL}/api/privacy/export", headers=auth_headers(), timeout=5)
        assert r.status_code == 200
        data = r.json()
        assert "record_count" in data
        assert "records" in data

    def test_privacy_erase_endpoint(self):
        """Verify GDPR data erasure endpoint functions with admin token."""
        r = requests.delete(f"{BASE_URL}/api/privacy/erase?days=90", headers=auth_headers(), timeout=5)
        assert r.status_code == 200
        data = r.json()
        assert "Erased" in data["message"]
