# ProductivityFlow Enterprise Desktop Agent ⚡

A real-time Electron + TypeScript companion application and workforce focus telemetry agent for Productivity Tracker. Seamlessly connects to the FastAPI enterprise server, categorizes foreground application telemetry, calculates live focus scores, and provides comprehensive GDPR Article 15/17 compliance.

## Key Features

- **Live Active Window Telemetry**: Continuously monitors foreground process activity on Windows (e.g., `Code.exe`, `Cursor.exe`, `Slack.exe`, `WindowsTerminal.exe`), classifying activity into `Productive`, `Distracted`, or `Idle`.
- **Real-Time Focus Gauge**: Circular SVG progress gauge displaying real-time productivity percentage, session timer, and breakdown metrics (Productive vs Distracted vs Idle duration).
- **FastAPI Telemetry Stream**: Regularly transmits telemetry pulses to the backend at `http://localhost:8000/api/screenshots` with timing-safe HMAC Bearer authentication (`sys-admin-token-2026`).
- **System Tray Integration**:
  - Live tooltip with focus percentage and current active category.
  - Quick Clock In, Pause, and Clock Out controls.
  - Global hotkey (`Ctrl+Shift+P`) to summon the agent instantly from anywhere.
- **GDPR Article 15 & 17 Governance Hub**:
  - Direct 1-click JSON export of all personal telemetry logs (`/api/privacy/export`).
  - Right-to-erasure trigger (`/api/privacy/erase`) allowing users to purge telemetry history older than 30 days.
  - Transparent system tray notification; zero keystroke logging or audio capture.
- **Enterprise Profile & Identity**: Authenticated as Rahul Garg (`rahul@northstardigital.com`), Systems Architect, Northstar Digital.

## Quick Start

### Development Mode
```bash
# In the root repository:
npm run desktop:dev

# Or in desktop/:
cd desktop
npm run dev
```

### Build & Packaging
```bash
# Build TypeScript and bundle assets:
npm run desktop:build

# Generate standalone desktop installer:
cd desktop
npm run pack
# or
npm run dist
```
