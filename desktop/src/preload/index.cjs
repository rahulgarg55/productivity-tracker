const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("productivityAPI", {
  getStatus: () => ipcRenderer.invoke("telemetry:get-status"),
  clockIn: () => ipcRenderer.invoke("session:clock-in"),
  pause: () => ipcRenderer.invoke("session:pause"),
  clockOut: () => ipcRenderer.invoke("session:clock-out"),
  getStats: () => ipcRenderer.invoke("api:get-stats"),
  getActivities: (params) => ipcRenderer.invoke("api:get-activities", params),
  exportTelemetry: () => ipcRenderer.invoke("api:export-telemetry"),
  eraseTelemetry: (days) => ipcRenderer.invoke("api:erase-telemetry", days),
  getPrivacyNotice: () => ipcRenderer.invoke("api:privacy-notice"),
  minimizeWindow: () => ipcRenderer.invoke("window:minimize"),
  closeWindow: () => ipcRenderer.invoke("window:close"),
  openExternal: (url) => ipcRenderer.invoke("shell:open-external", url),
  onTelemetryUpdate: (callback) => {
    ipcRenderer.on("telemetry:update", (_e, data) => callback(data));
  }
});
