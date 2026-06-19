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
const parentEmail = process.env.UI_QUALITY_PARENT_EMAIL || "parent@example.com";
const branchAdminEmail = process.env.UI_QUALITY_BRANCH_ADMIN_EMAIL || "admin@example.com";
const qaChecks = [];

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
    await runParentViewport(browser, {
      name: "desktop",
      width: 1440,
      height: 960,
      isMobile: false,
    });
    await runParentViewport(browser, {
      name: "mobile",
      width: 390,
      height: 844,
      isMobile: true,
    });
    await runBranchAdminViewport(browser, {
      name: "desktop",
      width: 1440,
      height: 960,
      isMobile: false,
    });
    await runBranchAdminViewport(browser, {
      name: "mobile",
      width: 390,
      height: 844,
      isMobile: true,
    });
    await runTenantViewport(browser, {
      name: "desktop",
      width: 1440,
      height: 960,
      isMobile: false,
      createTenant: true,
    });
    await runTenantViewport(browser, {
      name: "mobile",
      width: 390,
      height: 844,
      isMobile: true,
      createTenant: false,
    });
    await runAcademySetupViewport(browser, {
      name: "desktop",
      width: 1440,
      height: 960,
      isMobile: false,
      mutateSetup: true,
    });
    await runAcademySetupViewport(browser, {
      name: "mobile",
      width: 390,
      height: 844,
      isMobile: true,
      mutateSetup: false,
    });
    await runInternalTeamViewport(browser, {
      name: "desktop",
      width: 1440,
      height: 960,
      isMobile: false,
      mutateTeam: true,
    });
    await runInternalTeamViewport(browser, {
      name: "mobile",
      width: 390,
      height: 844,
      isMobile: true,
      mutateTeam: false,
    });
    await runProductionVisualQA(browser);
  } finally {
    await browser.close();
  }

  const report = {
    ok: failures.length === 0,
    baseURL,
    qaChecks,
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

async function runInternalTeamViewport(browser, viewport) {
  const context = await browser.newContext({
    viewport: { width: viewport.width, height: viewport.height },
    isMobile: viewport.isMobile,
  });
  const page = await context.newPage();
  try {
    const unique = `qa-team-${Date.now()}`;
    await login(page, demoEmail);
    await page.goto(`${baseURL}/tenants`, { waitUntil: "networkidle" });
    await page.fill('input[name="name"]', "QA Team Academy");
    await page.fill('input[name="slug"]', unique);
    await page.fill('input[name="timezone"]', "Asia/Jakarta");
    await page.fill('input[name="currency"]', "IDR");
    await page.click('.tenant-form button[type="submit"]');
    await page.waitForLoadState("networkidle");
    await page.locator(".tenant-item", { hasText: unique }).getByText("Continue setup").click();
    await page.waitForLoadState("networkidle");

    await page.fill('.branch-setup-form input[name="name"]', "QA Team Branch");
    await page.fill('.branch-setup-form input[name="code"]', `QTB${String(Date.now()).slice(-3)}`);
    await page.fill('.branch-setup-form input[name="timezone"]', "Asia/Jakarta");
    await page.fill('.branch-setup-form input[name="address"]', "Jakarta Barat");
    await page.click('.branch-setup-form button[type="submit"]');
    await page.waitForLoadState("networkidle");
    await page.getByText("Assign owner and assistant").click();
    await page.waitForLoadState("networkidle");

    await expectText(page, "Internal role setup", `${viewport.name} internal team title`);
    await expectText(page, "Invite internal operator", `${viewport.name} internal user form`);
    await expectText(page, "Existing internal user", `${viewport.name} role assignment form`);
    await expectText(page, "Active internal assignments", `${viewport.name} internal role list`);

    if (viewport.mutateTeam) {
      await page.fill('.internal-user-form input[name="full_name"]', "QA Branch Admin");
      await page.fill('.internal-user-form input[name="email"]', `${unique}@example.com`);
      await page.fill('.internal-user-form input[name="password"]', "password12345");
      await page.selectOption('.internal-user-form select[name="role"]', "branch_admin");
      const branchOptions = await page.locator('.internal-user-form select[name="branch_id"] option').all();
      if (branchOptions.length > 1) {
        await page.selectOption('.internal-user-form select[name="branch_id"]', { index: 1 });
      }
      await page.click('.internal-user-form button[type="submit"]');
      await page.waitForLoadState("networkidle");
      await expectText(page, "Internal user QA Branch Admin berhasil dibuat dan diberi role.", "internal user create success");
      await expectText(page, "QA Branch Admin", "created internal user visible");
      await expectText(page, "Branch Admin", "created internal role visible");
    }

    await expectNoHorizontalOverflow(page, `${viewport.name} internal team overflow`);
    await expectNoImportantTextOverflow(page, `${viewport.name} internal team important text overflow`);
    await expectNamedButtons(page, `${viewport.name} internal team buttons`);
    await capture(page, `${viewport.name}-internal-team.png`);
  } finally {
    await context.close();
  }
}

async function runAcademySetupViewport(browser, viewport) {
  const context = await browser.newContext({
    viewport: { width: viewport.width, height: viewport.height },
    isMobile: viewport.isMobile,
  });
  const page = await context.newPage();
  try {
    const unique = `qa-setup-${Date.now()}`;
    await login(page, demoEmail);
    await page.goto(`${baseURL}/tenants`, { waitUntil: "networkidle" });
    await page.fill('input[name="name"]', "QA Setup Academy");
    await page.fill('input[name="slug"]', unique);
    await page.fill('input[name="timezone"]', "Asia/Jakarta");
    await page.fill('input[name="currency"]', "IDR");
    await page.click('.tenant-form button[type="submit"]');
    await page.waitForLoadState("networkidle");
    await page.locator(".tenant-item", { hasText: unique }).getByText("Continue setup").click();
    await page.waitForLoadState("networkidle");
    await expectText(page, "Initial academy setup", `${viewport.name} academy setup title`);
    await expectText(page, "Create first branch", `${viewport.name} branch setup form`);
    await expectText(page, "After branch setup", `${viewport.name} setup next path`);

    if (viewport.mutateSetup) {
      await page.fill('.academy-setup-form input[name="name"]', "QA Setup Academy Updated");
      await page.fill('.academy-setup-form input[name="slug"]', `${unique}-updated`);
      await page.fill('.academy-setup-form input[name="timezone"]', "Asia/Jakarta");
      await page.fill('.academy-setup-form input[name="currency"]', "IDR");
      await page.fill('.academy-setup-form input[name="logo_url"]', "https://example.com/logo.png");
      await page.click('.academy-setup-form button[type="submit"]');
      await page.waitForLoadState("networkidle");
      await expectText(page, "Academy QA Setup Academy Updated berhasil diperbarui.", "academy setup update success");

      await page.fill('.branch-setup-form input[name="name"]', "QA Main Branch");
      await page.fill('.branch-setup-form input[name="code"]', "QAM");
      await page.fill('.branch-setup-form input[name="timezone"]', "Asia/Jakarta");
      await page.fill('.branch-setup-form input[name="address"]', "Jakarta Barat");
      await page.click('.branch-setup-form button[type="submit"]');
      await page.waitForLoadState("networkidle");
      await expectText(page, "Branch QA Main Branch berhasil dibuat.", "branch setup creation success");
      await expectText(page, "QAM / Asia/Jakarta / Jakarta Barat", "created branch visible");
    }

    await expectNoHorizontalOverflow(page, `${viewport.name} academy setup overflow`);
    await expectNoImportantTextOverflow(page, `${viewport.name} academy setup important text overflow`);
    await expectNamedButtons(page, `${viewport.name} academy setup buttons`);
    await capture(page, `${viewport.name}-academy-setup.png`);
  } finally {
    await context.close();
  }
}

async function runTenantViewport(browser, viewport) {
  const context = await browser.newContext({
    viewport: { width: viewport.width, height: viewport.height },
    isMobile: viewport.isMobile,
  });
  const page = await context.newPage();
  try {
    await login(page, demoEmail);
    await page.goto(`${baseURL}/tenants`, { waitUntil: "networkidle" });
    await expectText(page, "Tenant Registration", `${viewport.name} tenant registration title`);
    await expectText(page, "Academy identity", `${viewport.name} tenant form`);
    await expectText(page, "Registered academies", `${viewport.name} tenant list`);
    if (viewport.createTenant) {
      const unique = `qa-tenant-${Date.now()}`;
      await page.fill('input[name="name"]', "QA Tenant Academy");
      await page.fill('input[name="slug"]', unique);
      await page.fill('input[name="timezone"]', "Asia/Jakarta");
      await page.fill('input[name="currency"]', "IDR");
      await page.click('.tenant-form button[type="submit"]');
      await page.waitForLoadState("networkidle");
      await expectText(page, "Tenant QA Tenant Academy berhasil dibuat.", "tenant creation success");
      await expectText(page, unique, "created tenant visible in list");
    }
    await expectNoHorizontalOverflow(page, `${viewport.name} tenant registration overflow`);
    await expectNoImportantTextOverflow(page, `${viewport.name} tenant important text overflow`);
    await expectNamedButtons(page, `${viewport.name} tenant buttons`);
    await capture(page, `${viewport.name}-tenant-registration.png`);
  } finally {
    await context.close();
  }
}

async function runProductionVisualQA(browser) {
  const context = await browser.newContext({
    viewport: { width: 1280, height: 900 },
  });
  const page = await context.newPage();
  try {
    await page.goto(`${baseURL}/login`, { waitUntil: "networkidle" });
    await expectContrast(page, "production contrast baseline");
    await expectNoImportantTextOverflow(page, "login important text overflow");
    await expectKeyboardSequence(page, "login keyboard sequence", 3);

    await page.fill('input[name="email"]', demoEmail);
    await page.fill('input[name="password"]', "not-the-demo-password");
    await page.click('button[type="submit"]');
    await expectText(page, "Email atau password demo tidak valid.", "invalid login message");

    const csrfStatus = await page.evaluate(async () => {
      const response = await fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({
          email: "owner@example.com",
          password: "password123",
        }),
      });
      return response.status;
    });
    expectValue(csrfStatus === 400, "invalid csrf returns 400");

    await page.goto(`${baseURL}/missing-production-qa-page`, { waitUntil: "networkidle" });
    await expectText(page, "Error 404", "404 page title");
    await expectText(page, "Halaman yang diminta tidak ditemukan.", "404 page copy");
    await expectNoHorizontalOverflow(page, "404 overflow");
    await capture(page, "desktop-404.png");

    const apiResponse = await page.evaluate(async () => {
      const response = await fetch("/api/v1/production-qa-missing");
      const payload = await response.json();
      return { status: response.status, code: payload.error?.code || payload.code };
    });
    expectValue(
      apiResponse.status === 404 && apiResponse.code === "not_found",
      "api missing route returns structured 404",
    );

    await login(page, teacherEmail);
    await page.goto(`${baseURL}/dashboard/platform_owner`, { waitUntil: "networkidle" });
    await expectText(page, "Error 403", "forbidden page title");
    await expectText(page, "Role aktif Anda tidak memiliki akses", "forbidden page copy");
    await expectNoHorizontalOverflow(page, "403 overflow");
    await capture(page, "desktop-403.png");

    await login(page, demoEmail);
    await page.context().clearCookies();
    await page.goto(`${baseURL}/dashboard`, { waitUntil: "networkidle" });
    await expectText(page, "Secure operations shell", "session expiry returns login");

    await login(page, branchAdminEmail);
    await expectText(page, "Branch Admin Dashboard", "branch admin post-expiry login");
    await expectText(page, "Loading", "branch admin loading state copy");
    await expectNoImportantTextOverflow(page, "branch admin important text overflow");
    await expectKeyboardSequence(page, "branch admin keyboard sequence", 4);
  } finally {
    await context.close();
  }
}

async function runBranchAdminViewport(browser, viewport) {
  const context = await browser.newContext({
    viewport: { width: viewport.width, height: viewport.height },
    isMobile: viewport.isMobile,
  });
  const page = await context.newPage();
  try {
    await login(page, branchAdminEmail);
    await expectText(page, "Branch Admin Dashboard", `${viewport.name} branch admin dashboard title`);
    await expectText(page, "Branch admin operations flow", `${viewport.name} branch admin workflow`);
    await expectText(page, "Find the student, parent, class, or invoice first", `${viewport.name} branch admin search`);
    await expectText(page, "Branch admin operational states", `${viewport.name} branch admin states`);
    await expectText(page, "Outside branch scope", `${viewport.name} branch admin permission state`);
    await expectNoHorizontalOverflow(page, `${viewport.name} branch admin dashboard overflow`);
    await expectNoImportantTextOverflow(page, `${viewport.name} branch admin important text overflow`);
    await expectNamedButtons(page, `${viewport.name} branch admin dashboard buttons`);
    await capture(page, `${viewport.name}-branch-admin-dashboard.png`);
  } finally {
    await context.close();
  }
}

async function runParentViewport(browser, viewport) {
  const context = await browser.newContext({
    viewport: { width: viewport.width, height: viewport.height },
    isMobile: viewport.isMobile,
  });
  const page = await context.newPage();
  try {
    await login(page, parentEmail);
    await expectText(page, "Parent Dashboard", `${viewport.name} parent dashboard title`);
    await expectText(page, "Monitoring flow", `${viewport.name} parent workflow`);
    await expectText(page, "Activity feed", `${viewport.name} parent activity feed`);
    await expectText(page, "Parent trust states", `${viewport.name} parent states`);
    await expectText(page, "Only linked students are visible", `${viewport.name} parent permission state`);
    await expectNoHorizontalOverflow(page, `${viewport.name} parent dashboard overflow`);
    await expectNoImportantTextOverflow(page, `${viewport.name} parent important text overflow`);
    await expectNamedButtons(page, `${viewport.name} parent dashboard buttons`);
    await capture(page, `${viewport.name}-parent-dashboard.png`);
  } finally {
    await context.close();
  }
}

async function runTeacherViewport(browser, viewport) {
  const context = await browser.newContext({
    viewport: { width: viewport.width, height: viewport.height },
    isMobile: viewport.isMobile,
  });
  const page = await context.newPage();
  try {
    await login(page, teacherEmail);
    await expectText(page, "Teacher Dashboard", `${viewport.name} teacher dashboard title`);
    await expectText(page, "Today teaching flow", `${viewport.name} teacher workflow`);
    await expectText(page, "Next class", `${viewport.name} teacher next class`);
    await expectText(page, "Lesson summary", `${viewport.name} teacher lesson summary`);
    await expectNoHorizontalOverflow(page, `${viewport.name} teacher dashboard overflow`);
    await expectNoImportantTextOverflow(page, `${viewport.name} teacher important text overflow`);
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

    await login(page, demoEmail);
    await expectText(page, "Platform Owner Dashboard", `${viewport.name} dashboard title`);
    await expectText(page, "Global SaaS command center", `${viewport.name} role focus`);
    await expectText(page, "Quick actions", `${viewport.name} quick actions`);
    await expectNoHorizontalOverflow(page, `${viewport.name} dashboard overflow`);
    await expectNoImportantTextOverflow(page, `${viewport.name} dashboard important text overflow`);
    await expectNamedButtons(page, `${viewport.name} dashboard buttons`);
    await capture(page, `${viewport.name}-dashboard.png`);
  } finally {
    await context.close();
  }
}

async function login(page, email) {
  await page.context().clearCookies();
  await page.goto(`${baseURL}/login`, { waitUntil: "networkidle" });
  await page.fill('input[name="email"]', email);
  await page.fill('input[name="password"]', demoPassword);
  await page.click('button[type="submit"]');
  await page.waitForURL("**/dashboard/**");
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
  } else {
    qaChecks.push({ name: label, ok: true });
  }
}

function expectValue(ok, label) {
  if (!ok) {
    failures.push(`${label}: expected condition to be true.`);
  } else {
    qaChecks.push({ name: label, ok: true });
  }
}

async function expectNoHorizontalOverflow(page, label) {
  const overflow = await page.evaluate(() => {
    const doc = document.documentElement;
    return doc.scrollWidth - doc.clientWidth;
  });
  if (overflow > 1) {
    failures.push(`${label}: horizontal overflow is ${overflow}px.`);
  } else {
    qaChecks.push({ name: label, ok: true });
  }
}

async function expectNoImportantTextOverflow(page, label) {
  const offenders = await page.evaluate(() => {
    const selector = [
      "button",
      "a",
      ".metric-card",
      ".workflow-item",
      ".state-item",
      ".tenant-item",
      ".branch-item",
      ".branch-summary",
      ".team-item",
      ".team-scope",
      ".tenant-actions",
      ".status-notice",
      ".empty-state",
      ".focus-item",
      ".user-block",
      ".message",
    ].join(",");
    return [...document.querySelectorAll(selector)]
      .filter((element) => {
        const style = window.getComputedStyle(element);
        if (style.display === "none" || style.visibility === "hidden") {
          return false;
        }
        return element.scrollWidth - element.clientWidth > 1;
      })
      .map((element) => ({
        tag: element.tagName.toLowerCase(),
        className: element.className,
        text: element.textContent.trim().slice(0, 80),
        overflow: element.scrollWidth - element.clientWidth,
      }));
  });
  if (offenders.length > 0) {
    failures.push(`${label}: ${JSON.stringify(offenders)}`);
  } else {
    qaChecks.push({ name: label, ok: true });
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
  } else {
    qaChecks.push({ name: label, ok: true });
  }
}

async function expectKeyboardSequence(page, label, tabCount) {
  const focused = [];
  for (let index = 0; index < tabCount; index += 1) {
    await page.keyboard.press("Tab");
    focused.push(await page.evaluate(() => {
      const active = document.activeElement;
      if (!active || active === document.body) {
        return null;
      }
      const rect = active.getBoundingClientRect();
      return {
        tag: active.tagName.toLowerCase(),
        text: active.textContent.trim(),
        name: active.getAttribute("name"),
        visible: rect.width > 0 && rect.height > 0,
      };
    }));
  }
  if (focused.some((item) => !item?.visible)) {
    failures.push(`${label}: tab sequence produced a non-visible focus target.`);
  } else {
    qaChecks.push({ name: label, ok: true, focused });
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
  qaChecks.push({ name: label, ok: true });
}

async function expectContrast(page, label) {
  const checks = await page.evaluate(() => {
    const probe = document.createElement("div");
    document.body.appendChild(probe);
    const pairs = [
      ["--ink", "--surface", 7],
      ["--muted", "--surface", 4.5],
      ["--emerald", "--emerald-soft", 4.5],
      ["--danger", "--danger-soft", 4.5],
      ["--navy", "--navy-soft", 7],
    ];

    function resolve(variable) {
      probe.style.color = `var(${variable})`;
      return window.getComputedStyle(probe).color;
    }

    function channel(value) {
      const match = value.match(/rgba?\(([^)]+)\)/);
      return match[1].split(",").slice(0, 3).map((part) => Number(part.trim()));
    }

    function linear(value) {
      const normalized = value / 255;
      return normalized <= 0.03928
        ? normalized / 12.92
        : ((normalized + 0.055) / 1.055) ** 2.4;
    }

    function luminance(rgb) {
      const [red, green, blue] = rgb.map(linear);
      return 0.2126 * red + 0.7152 * green + 0.0722 * blue;
    }

    function ratio(foreground, background) {
      const lighter = Math.max(luminance(foreground), luminance(background));
      const darker = Math.min(luminance(foreground), luminance(background));
      return (lighter + 0.05) / (darker + 0.05);
    }

    const results = pairs.map(([foreground, background, minimum]) => {
      const actual = ratio(channel(resolve(foreground)), channel(resolve(background)));
      return {
        foreground,
        background,
        minimum,
        actual: Number(actual.toFixed(2)),
        ok: actual >= minimum,
      };
    });
    probe.remove();
    return results;
  });
  const failed = checks.filter((item) => !item.ok);
  if (failed.length > 0) {
    failures.push(`${label}: ${JSON.stringify(failed)}`);
  } else {
    qaChecks.push({ name: label, ok: true, checks });
  }
}
