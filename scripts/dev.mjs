import { spawn } from "node:child_process";

const port = process.env.FLASK_RUN_PORT || "5000";
const url =
  process.env.DEV_OPEN_URL || `http://127.0.0.1:${port}/api/v1/health/live`;

setTimeout(() => {
  const opener =
    process.platform === "win32"
      ? spawn("cmd", ["/c", "start", "", url], {
          detached: true,
          stdio: "ignore",
        })
      : process.platform === "darwin"
        ? spawn("open", [url], { detached: true, stdio: "ignore" })
        : spawn("xdg-open", [url], { detached: true, stdio: "ignore" });
  opener.unref();
}, 2000);

const server = spawn("python", ["app.py"], {
  env: process.env,
  stdio: "inherit",
});

server.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 0);
});
