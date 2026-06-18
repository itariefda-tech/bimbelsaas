import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const artifactDir = join(process.cwd(), "artifacts", "frontend-readiness");
const reportPath = join(artifactDir, "report.json");
const requiredFiles = [
  "FRONTEND_UI_UX_ROADMAP.md",
  "backend/app/static/css/mvp.css",
  "backend/app/templates/base.html",
  "backend/app/templates/login.html",
  "backend/app/templates/dashboard.html",
  "backend/app/web.py",
  "scripts/ui_quality_gate.mjs",
  "scripts/validate_staging_postgres.py",
  "package-lock.json",
];

mkdirSync(artifactDir, { recursive: true });

const checks = [];
checkFiles();
checkRoadmapStatus();
checkUiQualityReport();
checkLocalCommands();
checkExternalGates();
checkArchitectureDecision();

const blockers = checks.filter((item) => !item.ok && item.severity === "blocker");
const warnings = checks.filter((item) => !item.ok && item.severity === "warning");
const readyForNextJs = blockers.length === 0;

const report = {
  ready_for_nextjs: readyForNextJs,
  decision: readyForNextJs
    ? "Next.js app foundation may start."
    : "Keep Flask shell as the control plane and resolve blockers before starting Next.js.",
  blockers: blockers.map((item) => item.name),
  warnings: warnings.map((item) => item.name),
  checks,
};

writeFileSync(reportPath, `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify(report, null, 2));

if (!readyForNextJs && process.env.FRONTEND_READINESS_STRICT === "true") {
  process.exitCode = 1;
}

function checkFiles() {
  for (const file of requiredFiles) {
    checks.push({
      name: `required file exists: ${file}`,
      ok: existsSync(join(process.cwd(), file)),
      severity: "blocker",
    });
  }
}

function checkRoadmapStatus() {
  const roadmap = read("FRONTEND_UI_UX_ROADMAP.md");
  checks.push({
    name: "F0 marked completed",
    ok: roadmap.includes("## Phase F0") && roadmap.includes("Status: completed"),
    severity: "blocker",
  });
  checks.push({
    name: "F1 baseline implemented",
    ok: roadmap.includes("## Phase F1") && roadmap.includes("Status: baseline implemented"),
    severity: "blocker",
  });
  checks.push({
    name: "F2 marked completed",
    ok: roadmap.includes("## Phase F2") && roadmap.includes("Status: completed"),
    severity: "blocker",
  });
  checks.push({
    name: "F3 documents Next.js entry criteria",
    ok:
      roadmap.includes("GitHub Actions billing issue selesai")
      && roadmap.includes("PostgreSQL staging validation hijau")
      && roadmap.includes("Auth/session or token strategy"),
    severity: "blocker",
  });
}

function checkUiQualityReport() {
  const reportFile = join(process.cwd(), "artifacts", "ui-quality", "report.json");
  if (!existsSync(reportFile)) {
    checks.push({
      name: "UI quality report exists",
      ok: false,
      severity: "blocker",
    });
    return;
  }
  const report = JSON.parse(readFileSync(reportFile, "utf8"));
  const screenshots = report.screenshots || [];
  checks.push({
    name: "UI quality report passed",
    ok: report.ok === true,
    severity: "blocker",
  });
  checks.push({
    name: "desktop and mobile screenshots captured",
    ok:
      screenshots.some((item) => item.filename === "desktop-login.png")
      && screenshots.some((item) => item.filename === "desktop-dashboard.png")
      && screenshots.some((item) => item.filename === "mobile-login.png")
      && screenshots.some((item) => item.filename === "mobile-dashboard.png"),
    severity: "blocker",
  });
}

function checkLocalCommands() {
  checks.push(run("npm ci", npmCommand(), ["ci"]));
  checks.push(run("UI quality gate", npmCommand(), ["run", "ui:quality"]));
  checks.push(run("Python compile", "python", [
    "-m",
    "compileall",
    "app.py",
    "backend/app",
    "backend/tests",
    "backend/migrations",
    "scripts",
  ]));
}

function checkExternalGates() {
  checks.push({
    name: "GitHub Actions runner is unblocked and green",
    ok: process.env.GITHUB_ACTIONS_GREEN === "true",
    severity: "blocker",
    detail: "Set GITHUB_ACTIONS_GREEN=true only after the remote CI runner completes successfully.",
  });
  checks.push({
    name: "PostgreSQL staging validation is green",
    ok: process.env.POSTGRES_STAGING_VALIDATED === "true",
    severity: "blocker",
    detail: "Set POSTGRES_STAGING_VALIDATED=true only after scripts/validate_staging_postgres.py passes against staging PostgreSQL.",
  });
}

function checkArchitectureDecision() {
  const roadmap = read("FRONTEND_UI_UX_ROADMAP.md");
  checks.push({
    name: "Flask shell remains internal control plane",
    ok: roadmap.includes("Keep Flask shell as internal/staging control plane"),
    severity: "warning",
  });
  checks.push({
    name: "Next.js customer-facing app is explicitly gated",
    ok: roadmap.includes("Build Next.js as customer-facing production app once staging is green"),
    severity: "warning",
  });
}

function run(name, command, args) {
  try {
    const invocation = commandInvocation(command, args);
    execFileSync(invocation.command, invocation.args, {
      cwd: process.cwd(),
      env: {
        ...process.env,
        APP_ENV: "development",
        DATABASE_URL: process.env.DATABASE_URL || "sqlite:///dev.db",
        OBSERVABILITY_LOG_REQUESTS: "false",
      },
      stdio: "pipe",
    });
    return { name, ok: true, severity: "blocker" };
  } catch (error) {
    return {
      name,
      ok: false,
      severity: "blocker",
      detail: String(error.message || error),
    };
  }
}

function npmCommand() {
  return process.platform === "win32" ? "npm.cmd" : "npm";
}

function commandInvocation(command, args) {
  if (process.platform === "win32" && command.endsWith(".cmd")) {
    return {
      command: "cmd.exe",
      args: ["/d", "/s", "/c", ["npm", ...args].join(" ")],
    };
  }
  return { command, args };
}

function read(file) {
  return readFileSync(join(process.cwd(), file), "utf8");
}
