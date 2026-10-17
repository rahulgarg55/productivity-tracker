import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, "..");
const src = path.join(root, "src");
const dist = path.join(root, "dist");

function copyDir(srcDir, destDir) {
  if (!fs.existsSync(destDir)) {
    fs.mkdirSync(destDir, { recursive: true });
  }
  const entries = fs.readdirSync(srcDir, { withFileTypes: true });
  for (const entry of entries) {
    const srcPath = path.join(srcDir, entry.name);
    const destPath = path.join(destDir, entry.name);
    if (entry.isDirectory()) {
      copyDir(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

// Ensure renderer files are copied
const rendererSrc = path.join(src, "renderer");
const rendererDist = path.join(dist, "renderer");
if (fs.existsSync(rendererSrc)) {
  copyDir(rendererSrc, rendererDist);
}

// Copy preload script if present
const preloadSrc = path.join(src, "preload", "index.cjs");
const preloadDist = path.join(dist, "preload", "index.cjs");
if (fs.existsSync(preloadSrc)) {
  fs.mkdirSync(path.dirname(preloadDist), { recursive: true });
  fs.copyFileSync(preloadSrc, preloadDist);
}

console.log("[copy-assets] ProductivityFlow desktop assets synced to dist/ successfully.");
