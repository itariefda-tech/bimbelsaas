import { execFileSync, spawn } from "node:child_process";
import { mkdirSync, statSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { chromium } from "@playwright/test";

const port = process.env.UI_QUALITY_PORT || "5055";
const baseURL = `http://127.0.0.1:${port}`;
const artifactDir = join(process.cwd(), "artifacts", "ui-quality");
const demoEmail = process.env.UI_QUALITY_EMAIL || "owner@example.com";
const demoPassword = process.env.UI_QUALITY_PASSWORD || "password123";
const teacherEmail = process.env.UI_QUALITY_TEACHER_EMAIL || "teacher@example.com";

const serverEnv = {
  ...process.env,
  APP_ENV: "development",
  DATABASE_URL: process.env.DATABASE_URL || "sqlite:///dev.db",
  FLASK_RUN_HOST: "127.0.0.1",
  FLASK_RUN_PORT: port,
  OBSERVABILITY_LOG_REQUESTS: "false",
};

const serverCode = [
  "import sys",
  "sys.path.insert(0, 'backend')",
  "from app import create_app",
  "from app.extensions import socketio",
  "app = create_app()",
  (
    "socketio.run(app, host='127.0.0.1', port="
    + Number(port)
    + ", debug=False, use_reloader=False, allow_unsafe_werkzeug=True)"
  ),
].join("; ");

mkdirSync(artifactDir, { recursive: true });
execFileSync("python", ["scripts/manage.py", "seed-demo"], {
  cwd: process.cwd(),
  env: serverEnv,
  stdio: "inherit",
});

const server = spawn("python", ["-c", serverCode], {
  cwd: process.cwd(),
  env: serverEnv,
  stdio: ["ignore", "pipe", "pipe"],
});

const failures = [];
const screenshots = [];

try {
  await waitForHealth();
  const browser = await chromium.launch();
  try {
    await runViewport(browser, {
      name: "desktop",
      width: 1440,
      height: 960,
      isMobile: false,
    });
    await runViewport(browser, {
      name: "mobile",
      width: 390,
      height: 844,
      isMobile: true,
    });
    await runTeacherViewport(browser, {
      name: "desktop",
      width: 1440,
      height: 960,
      isMobile: false,
    });
    await runTeacherViewport(browser, {
      name: "mobile",
      width: 390,
      height: 844,
      isMobile: true,
    });
  } finally {
    await browser.close();
  }

  const report = {
    ok: failures.length === 0,
    baseURL,
    screenshots,
    failures,
  };
  writeFileSync(
    join(artifactDir, "report.json"),
    `${JSON.stringify(report, null, 2)}\n`,
  );

  if (failures.length > 0) {
    console.error(JSON.stringify(report, null, 2));
    process.exitCode = 1;
  } else {
    console.log("UI quality gate passed.");
    console.log(JSON.stringify(report, null, 2));
  }
} finally {
  server.kill();
}

async function runTeacherViewport(browser, viewport) {
  const context = await browser.newContext({
    viewport: { width: viewport.width, height: viewport.height },
    isMobile: viewport.isMobile,
  });
  const page = await context.newPage();
  try {
    await page.goto(`${baseURL}/login`, { waitUntil: "networkidle" });
    await page.fill('input[name="email"]', teacherEmail);
    await page.fill('input[name="password"]', demoPassword);
    await page.click('button[type="submit"]');
    await page.waitForURL("**/dashboard/**");
    await expectText(page, "Teacher Dashboard", `${viewport.name} teacher dashboard title`);
    await expectText(page, "Today teaching flow", `${viewport.name} teacher workflow`);
    await expectText(page, "Next class", `${viewport.name} teacher next class`);
    await expectText(page, "Lesson summary", `${viewport.name} teacher lesson summary`);
    await expectNoHorizontalOverflow(page, `${viewport.name} teacher dashboard overflow`);
    await expectNamedButtons(page, `${viewport.name} teacher dashboard buttons`);
    await capture(page, `${viewport.name}-teacher-dashboard.png`);
  } finally {
    await context.close();
  }
}

async function runViewport(browser, viewport) {
  const context = await browser.newContext({
    viewport: { width: viewport.width, height: viewport.height },
    isMobile: viewport.isMobile,
  });
  const page = await context.newPage();
  try {
    await page.goto(`${baseURL}/login`, { waitUntil: "networkidle" });
    await expectText(page, "Secure operations shell", `${viewport.name} login title`);
    await expectNoHorizontalOverflow(page, `${viewport.name} login overflow`);
    await expectFormAccessibility(page, `${viewport.name} login form`);
    await expectKeyboardFocus(page, `${viewport.name} keyboard focus`);
    await capture(page, `${viewport.name}-login.png`);

    await page.fill('input[name="email"]', demoEmail);
    await page.fill('input[name="password"]', demoPassword);
    await page.click('button[type="submit"]');
    await page.waitForURL("**/dashboard/**");
    await expectText(page, "Platform Owner Dashboard", `${viewport.name} dashboard title`);
    await expectText(page, "Global SaaS command center", `${viewport.name} role focus`);
    await expectText(page, "Quick actions", `${viewport.name} quick actions`);
    await expectNoHorizontalOverflow(page, `${viewport.name} dashboard overflow`);
    await expectNamedButtons(page, `${viewport.name} dashboard buttons`);
    await capture(page, `${viewport.name}-dashboard.png`);
  } finally {
    await context.close();
  }
}

async function waitForHealth() {
  const deadline = Date.now() + 30_000;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`${baseURL}/health`);
      if (response.ok) {
        return;
      }
    } catch (_error) {
      await new Promise((resolve) => setTimeout(resolve, 500));
    }
  }
  throw new Error("Timed out waiting for Flask server health.");
}

async function capture(page, filename) {
  const path = join(artifactDir, filename);
  await page.screenshot({ path, fullPage: false, timeout: 60_000 });
  const size = statSync(path).size;
  screenshots.push({ filename, size });
  if (size < 5_000) {
    failures.push(`${filename} looks too small to be a valid screenshot.`);
  }
}

async function expectText(page, text, label) {
  const visible = await page.getByText(text, { exact: false }).first().isVisible();
  if (!visible) {
    failures.push(`${label}: expected visible text "${text}".`);
  }
}

async function expectNoHorizontalOverflow(page, label) {
  const overflow = await page.evaluate(() => {
    const doc = document.documentElement;
    return doc.scrollWidth - doc.clientWidth;
  });
  if (overflow > 1) {
    failures.push(`${label}: horizontal overflow is ${overflow}px.`);
  }
}

async function expectFormAccessibility(page, label) {
  const result = await page.evaluate(() => {
    const inputs = [...document.querySelectorAll("input")];
    return inputs.map((input) => ({
      type: input.getAttribute("type") || "text",
      name: input.getAttribute("name"),
      labelled: Boolean(input.labels?.length) || Boolean(input.getAttribute("aria-label")),
    }));
  });
  for (const item of result) {
    if (item.type !== "hidden" && item.name !== "_csrf_token" && !item.labelled) {
      failures.push(`${label}: input "${item.name}" has no label.`);
    }
  }
}

async function expectKeyboardFocus(page, label) {
  await page.keyboard.press("Tab");
  const focused = await page.evaluate(() => {
    const active = document.activeElement;
    if (!active || active === document.body) {
      return false;
    }
    const rect = active.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  });
  if (!focused) {
    failures.push(`${label}: first tab did not produce visible focus.`);
  }
}

async function expectNamedButtons(page, label) {
  const buttons = await page.evaluate(() => {
    return [...document.querySelectorAll("button")].map((button) => ({
      text: button.textContent.trim(),
      aria: button.getAttribute("aria-label") || "",
    }));
  });
  for (const button of buttons) {
    if (!button.text && !button.aria) {
      failures.push(`${label}: found a button without accessible name.`);
    }
  }
}
