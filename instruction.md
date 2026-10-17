# Productivity Tracker System

The Productivity Tracker backend is a Python FastAPI application running on `http://localhost:8000`. The source code is located at `/app`. It uses an in-memory SQLite database to store user activity data.

## Objective

Several critical API endpoints are broken or have security vulnerabilities. Your task is to fix them so that the full integration test suite passes. The frontend dashboard is functional but relies on the backend API working correctly.

Restart the backend service after making code changes.

## Problem Description

The backend application currently has a few key issues that need to be resolved:

- **Authentication is missing:** The screenshot upload endpoint (`POST /api/screenshots`) is completely open. It needs to be secured with an authorization token. 
- **Categorization is incorrect:** When screenshots are uploaded, the app attempts to categorize the activity based on the app name. However, it currently misclassifies many activities. You will need to fix the logic so it correctly identifies productive, idle, and distracted activities based on the app name. The test suite contains cases that will guide you on the expected rules.
- **Statistics are wrong:** The dashboard relies on the `/api/stats` endpoint to show productivity trends, but the aggregation logic is flawed. The productivity score is currently calculating the wrong percentage, and the API response structure is missing expected fields. You will need to fix the calculation and ensure the output matches what the tests expect.
- **Web Dashboard:** Ensure the root route (`GET /`) properly serves the dashboard UI.

Run the test suite to discover the exact expected behavior, token values, and response structures required to pass all checks.
