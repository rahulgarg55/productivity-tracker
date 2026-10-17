import { app, BrowserWindow, Tray, Menu, ipcMain, globalShortcut, shell, nativeImage } from "electron";
import path from "node:path";
import fs from "node:fs";
import http from "node:http";
import { fileURLToPath } from "node:url";
import { ProductivityEngine, TelemetryStatus } from "./engine.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

let mainWindow: BrowserWindow | null = null;
let tray: Tray | null = null;
const engine = new ProductivityEngine();

function resolveAsset(subpath: string): string {
  const distPath = path.resolve(__dirname, "..", subpath);
  if (fs.existsSync(distPath)) return distPath;
  const srcPath = path.resolve(__dirname, "../../src", subpath);
  if (fs.existsSync(srcPath)) return srcPath;
  return distPath;
}

function updateTray(status: TelemetryStatus) {
  if (!tray) return;
  const label = `${status.focusScore}% Focus • ${status.category.toUpperCase()}`;
  tray.setToolTip(`ProductivityFlow: ${label} (${status.state})`);
}

async function createWindow() {
  mainWindow = new BrowserWindow({
    width: 500,
    height: 760,
    minWidth: 440,
    minHeight: 600,
    resizable: true,
    frame: true,
    show: true,
    title: "ProductivityFlow Enterprise Desktop Agent",
    backgroundColor: "#090d16",
    webPreferences: {
      preload: resolveAsset("preload/index.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  const htmlPath = resolveAsset("renderer/index.html");
  await mainWindow.loadFile(htmlPath);

  mainWindow.on("close", (event) => {
    if (!app.isQuitting) {
      event.preventDefault();
      mainWindow?.hide();
    }
  });
}

function createTray() {
  // 16x16 tray icon representation in base64 (Cyan/Blue gauge icon)
  const icon = nativeImage.createFromBuffer(
    Buffer.from(
      "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAWElEQVR42mNk+M/wHwNGBkaG/1gwA5CGEaMGGhmgGDGQ4oG5FhljaGIgwzBoYhi/YYD4nwkO+hgwDGAk1xBMzYgB6JpB/h/kGIZhGDEAY9kZRg5o1QAA411V4V6Z7K0AAAAASUVORK5CYII=",
      "base64"
    )
  );

  tray = new Tray(icon);
  tray.setToolTip("ProductivityFlow Desktop Agent — Ready");

  const contextMenu = Menu.buildFromTemplate([
    {
      label: "Open ProductivityFlow Agent",
      click: () => {
        mainWindow?.show();
        mainWindow?.focus();
      },
    },
    { type: "separator" },
    {
      label: "Clock In / Start Tracking",
      click: async () => {
        await engine.startSession();
      },
    },
    {
      label: "Take Break / Pause",
      click: () => {
        engine.pauseSession();
      },
    },
    {
      label: "Clock Out / Stop",
      click: () => {
        engine.stopSession();
      },
    },
    { type: "separator" },
    {
      label: "Export GDPR Telemetry",
      click: async () => {
        mainWindow?.show();
        mainWindow?.focus();
        mainWindow?.webContents.send("telemetry:trigger-export");
      },
    },
    { type: "separator" },
    {
      label: "Quit Agent",
      click: () => {
        app.isQuitting = true;
        app.quit();
      },
    },
  ]);

  tray.setContextMenu(contextMenu);
  tray.on("double-click", () => {
    mainWindow?.show();
    mainWindow?.focus();
  });
}

function makeApiRequest(apiPath: string, method: string = "GET", body?: any): Promise<any> {
  return new Promise((resolve, reject) => {
    const postData = body ? JSON.stringify(body) : null;
    const headers: Record<string, string | number> = {
      "Content-Type": "application/json",
      "Authorization": "Bearer sys-admin-token-2026",
    };
    if (postData) {
      headers["Content-Length"] = Buffer.byteLength(postData);
    }
    const options: http.RequestOptions = {
      hostname: "localhost",
      port: 8000,
      path: apiPath,
      method,
      headers,
      timeout: 3000,
    };

    const req = http.request(options, (res) => {
      let data = "";
      res.on("data", (chunk) => (data += chunk));
      res.on("end", () => {
        try {
          resolve(JSON.parse(data));
        } catch {
          resolve({ status: res.statusCode, raw: data });
        }
      });
    });

    req.on("error", (err) => resolve({ error: err.message, offline: true }));
    req.on("timeout", () => {
      req.destroy();
      resolve({ error: "Request timed out", offline: true });
    });

    if (postData) req.write(postData);
    req.end();
  });
}

declare global {
  namespace Electron {
    interface App {
      isQuitting?: boolean;
    }
  }
}

app.whenReady().then(async () => {
  // Listen for engine telemetry updates and push to renderer & tray
  engine.setOnUpdate((status) => {
    updateTray(status);
    mainWindow?.webContents.send("telemetry:update", status);
  });

  // IPC Handlers
  ipcMain.handle("telemetry:get-status", () => {
    return engine.getStatus();
  });

  ipcMain.handle("session:clock-in", async () => {
    await engine.startSession();
    return engine.getStatus();
  });

  ipcMain.handle("session:pause", () => {
    engine.pauseSession();
    return engine.getStatus();
  });

  ipcMain.handle("session:clock-out", () => {
    engine.stopSession();
    return engine.getStatus();
  });

  ipcMain.handle("api:get-stats", async () => {
    return makeApiRequest("/api/stats");
  });

  ipcMain.handle("api:get-activities", async (_e, params?: { limit?: number; offset?: number }) => {
    const limit = params?.limit || 20;
    const offset = params?.offset || 0;
    return makeApiRequest(`/api/activities?limit=${limit}&offset=${offset}`);
  });

  ipcMain.handle("api:export-telemetry", async () => {
    return makeApiRequest("/api/privacy/export");
  });

  ipcMain.handle("api:erase-telemetry", async (_e, days: number = 30) => {
    return makeApiRequest(`/api/privacy/erase?days=${days}`, "DELETE");
  });

  ipcMain.handle("api:privacy-notice", async () => {
    return makeApiRequest("/api/privacy/notice");
  });

  ipcMain.handle("window:minimize", () => {
    mainWindow?.minimize();
  });

  ipcMain.handle("window:close", () => {
    mainWindow?.hide();
  });

  ipcMain.handle("shell:open-external", (_e, url: string) => {
    return shell.openExternal(url);
  });

  // Global hotkey: Ctrl+Shift+P (or Cmd+Shift+P)
  globalShortcut.register("CommandOrControl+Shift+P", () => {
    if (mainWindow) {
      if (!mainWindow.isVisible()) {
        mainWindow.show();
      }
      mainWindow.focus();
    }
  });

  createTray();
  await createWindow();
  // Auto-start active session
  await engine.startSession();
});

app.on("will-quit", () => {
  globalShortcut.unregisterAll();
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    // Keep alive in tray
  }
});
