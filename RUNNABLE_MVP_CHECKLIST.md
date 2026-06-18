# RUNNABLE_MVP_CHECKLIST.md

## Goal

Membuat aplikasi bisa berjalan end-to-end secara minimal:
- server running,
- database siap,
- login bisa,
- dashboard role tampil,
- tidak ada fatal error.

---

## Phase A - Project Audit

- [x] Cek struktur folder project
- [x] Cek apakah backend Flask sudah ada
- [x] Cek apakah `app.py` tersedia
- [x] Cek apakah application factory tersedia
- [x] Cek dependency Python
- [x] Cek file konfigurasi environment
- [x] Cek database config
- [x] Cek frontend/templates/static assets
- [x] Cek command running yang benar

### Output

Audit awal 2026-06-18:
- Project memiliki root docs lengkap, root `app.py`, folder `backend/`, `backend/app/`, migrations, tests, dan scripts.
- Backend Flask application factory tersedia di `backend/app/__init__.py` dengan SQLAlchemy, Flask-Migrate, Socket.IO, API v1, error handler, request context, dan rate limiter.
- Root `app.py` sudah mencoba menjalankan backend Socket.IO dari `backend/`.
- Dependency Python ada di `backend/pyproject.toml`, tetapi belum ada root `requirements.txt`.
- `.env.example` tersedia, namun default database masih PostgreSQL sehingga kurang cocok untuk Runnable MVP lokal tanpa Docker/PostgreSQL.
- Database models dan migration chain sudah besar sampai `0013`, tetapi belum ada command bootstrap SQLite/demo data yang sederhana.
- API health tersedia di `/api/v1/health/live` dan `/api/v1/health/ready`, tetapi belum ada root `GET /health` sesuai target MVP.
- Tidak ditemukan frontend app. Belum ada Flask templates/static untuk login page dan dashboard role minimal.
- Command target tetap `python app.py`, tetapi perlu recovery config, init DB, seed, dan smoke flow agar benar-benar runnable lokal.

---

## Phase B - Server Boot Recovery

- [x] Pastikan ada entry point aplikasi
- [x] Pastikan command run resmi tersedia
- [x] Pastikan error import diperbaiki
- [x] Pastikan route health check tersedia
- [x] Pastikan server bisa start tanpa crash

### Output

Completed on June 18, 2026:
- Root `app.py` loads `.env`/`.env.example`, points Python imports to `backend/`, creates the Flask app, and runs Socket.IO.
- Official command is `python app.py`.
- Root `GET /health` returns 200.
- Smoke test against a real local server returned 200 for `/health` and `/login`.

---

## Phase C - Environment & Dependency Recovery

- [x] Pastikan `requirements.txt` tersedia
- [x] Pastikan dependency minimal lengkap
- [x] Pastikan `.env.example` tersedia
- [x] Pastikan konfigurasi development aman
- [x] Pastikan instruksi install jelas di README

### Output

Completed on June 18, 2026:
- Root `requirements.txt` is available for local MVP installation.
- `.env.example` defaults to `APP_ENV=development` and `DATABASE_URL=sqlite:///dev.db`.
- Production config still rejects SQLite, weak secrets, disabled rate limiting, and missing Redis.

---

## Phase D - Database Boot Recovery

- [x] Pastikan database bisa dibuat
- [x] Pastikan tabel minimal tersedia
- [x] Pastikan migration/init database tersedia
- [x] Pastikan seed data demo tersedia
- [x] Pastikan academy demo tersedia
- [x] Pastikan branch demo tersedia
- [x] Pastikan role demo tersedia
- [x] Pastikan user demo tersedia

### Output

Completed on June 18, 2026:
- `python scripts/init_demo.py` creates the SQLite development database with `db.create_all()`.
- Demo academy, branch, subscription, role assignments, teacher, parent, and student records are seeded idempotently.
- Demo password for all seeded users is `password123`.

---

## Phase E - Minimal Auth Recovery

- [x] Login page tersedia
- [x] Logout tersedia
- [x] Session/JWT berjalan
- [x] Role user terbaca
- [x] Redirect dashboard sesuai role
- [x] Unauthorized access ditangani

### Output

Completed on June 18, 2026:
- `/login` renders a minimal demo login page.
- `/login` POST uses the existing `AuthService` and stores access/refresh tokens in session.
- `/logout` clears session and calls existing logout flow when authenticated.
- `/dashboard` redirects to the first active role.
- `/dashboard/<role>` rejects unavailable roles with 403.

---

## Phase F - Minimal Dashboard Shell

- [x] Platform Owner dashboard placeholder
- [x] Academy Director dashboard placeholder
- [x] Branch Manager dashboard placeholder
- [x] Branch Admin dashboard placeholder
- [x] Teacher dashboard placeholder
- [x] Parent dashboard placeholder
- [x] Student dashboard placeholder
- [x] Role-based navigation minimal

### Output

Completed on June 18, 2026:
- `backend/app/templates/dashboard.html` renders a role-aware dashboard shell.
- Dashboard context includes academy name, branch scope, branch count, user identity, and active role navigation.

---

## Phase G - Minimal Frontend Shell

- [x] Base layout tersedia
- [x] Header/topbar tersedia
- [x] Sidebar atau mobile nav tersedia
- [x] Static CSS/JS termuat
- [x] Halaman tidak blank
- [x] Error page minimal tersedia

### Output

Completed on June 18, 2026:
- Minimal templates are available in `backend/app/templates/`.
- Minimal CSS is available in `backend/app/static/css/mvp.css`.
- HTML pages render through Flask without requiring a separate frontend app.

---

## Phase H - Smoke Test

- [x] Server running
- [x] Health check OK
- [x] Login demo berhasil
- [x] Dashboard role tampil
- [x] Static files termuat
- [x] Tidak ada error 500
- [x] Tidak ada import error
- [x] Tidak ada migration fatal error

### Output

Verified on June 18, 2026:
- `python -m compileall app.py backend/app scripts` passed.
- `python scripts/init_demo.py` passed.
- Flask test client returned: `/health` 200, `/login` 200, login POST 302, `/dashboard` 302, `/dashboard/platform_owner` 200.
- Real local server smoke returned 200 for `/health` and `/login`.
- Targeted pytest suites passed:
  - `backend/tests/test_phase11_hardening.py`: 10 passed.
  - `backend/tests/test_beta_launch_api.py backend/tests/test_analytics_api.py backend/tests/test_scale_optimization_api.py`: 12 passed.
- Full `python -m pytest -q` passed in about 3 minutes 15 seconds on this host.

---

## Phase I - CI & PostgreSQL Staging Validation

- [x] GitHub Actions CI tersedia
- [x] CI menjalankan dependency install
- [x] CI menjalankan compile check
- [x] CI menjalankan full pytest suite
- [x] CI menjalankan local operational CLI smoke
- [x] CI menyediakan PostgreSQL service
- [x] CI menyediakan Redis service
- [x] Script PostgreSQL staging validation tersedia
- [x] CLI resmi `init-db` tersedia
- [x] CLI resmi `seed-demo` tersedia
- [x] CLI resmi `smoke-check` tersedia
- [x] Runbook staging diperbarui
- [ ] Validasi PostgreSQL staging dijalankan di host lokal/staging nyata
- [ ] GitHub Actions runner berhasil dijalankan setelah billing issue selesai

### Output

Completed on June 18, 2026:
- `.github/workflows/ci.yml` runs compile, full tests, and PostgreSQL staging validation.
- `scripts/validate_staging_postgres.py` requires PostgreSQL `DATABASE_URL`, runs `flask --app wsgi db upgrade`, checks database connectivity, and verifies live/readiness health endpoints.
- `scripts/manage.py` provides official local commands: `init-db`, `seed-demo`, and `smoke-check`.
- npm wrappers are available: `npm run init-db`, `npm run seed-demo`, and `npm run smoke-check`.
- `npm run staging:validate` wraps the staging validation script.
- `STAGING_RUNBOOK.md` documents the repeatable staging validation flow.
- Commit `9e35eae` was pushed to `origin/main`.
- GitHub Actions run `27768742612` was created for the pushed commit.

Local limitation:
- Docker is not installed on this host, so the PostgreSQL/Redis service validation could not be executed locally.
- The script was compile-checked and verified to reject non-PostgreSQL `DATABASE_URL`.
- GitHub Actions did not start the job because GitHub reported an account billing issue, so the runner could not prove the workflow yet.

---

## Phase J - Web Security Hardening

- [x] Login form memakai CSRF token per session
- [x] Logout form memakai CSRF token per session
- [x] POST login tanpa CSRF ditolak
- [x] Session cookie default `HttpOnly`
- [x] Session cookie default `SameSite=Lax`
- [x] Production/staging mematikan demo login hints
- [x] Production/staging mematikan demo seed
- [x] Demo password bisa dikonfigurasi via environment
- [x] Smoke-check CLI mendukung CSRF flow
- [x] Test web security tersedia

### Output

Completed on June 18, 2026:
- `backend/app/web.py` validates CSRF tokens for `/login` and `/logout`.
- `backend/app/templates/login.html` and `backend/app/templates/base.html` include CSRF hidden fields.
- `backend/app/config.py` sets safer session cookie defaults and rejects demo mode in production.
- `scripts/init_demo.py` refuses demo seeding when `DEMO_SEED_ENABLED` is disabled.
- `scripts/manage.py smoke-check` now performs a browser-like CSRF login flow.
- `backend/tests/test_web_security.py` verifies CSRF rejection, valid CSRF login, cookie defaults, and production demo guardrails.

Verified on June 18, 2026:
- `python -m compileall app.py backend/app backend/tests backend/migrations scripts` passed.
- `python scripts/manage.py seed-demo` passed.
- `python scripts/manage.py smoke-check` passed.
- `python -m pytest backend/tests/test_web_security.py -q` passed.
- `python -m pytest -q` passed.

---

## Phase K - Frontend Final Strategy

- [x] Flask shell polish dipilih sebagai fase frontend langsung
- [x] Next.js app ditunda sampai CI/staging hijau
- [x] UI/UX polish roadmap tersedia
- [x] Phase F0 frontend foundation lock selesai
- [x] Baseline Phase F1 Flask shell polish diimplementasikan
- [x] Role-specific dashboard sections tersedia
- [x] UI screenshot/accessibility quality gates tersedia
- [x] Phase F3 Next.js readiness gate tersedia
- [ ] Phase F3 external blockers selesai
- [x] Phase F5 Teacher daily workflow baseline tersedia

### Output

Completed on June 18, 2026:
- `FRONTEND_UI_UX_ROADMAP.md` defines the frontend final strategy.
- Decision: keep Flask shell as internal/staging production control shell.
- Decision: start Next.js after GitHub Actions billing is resolved and PostgreSQL staging validation passes.
- `backend/app/static/css/mvp.css` now defines the first UI token and shell styling baseline.
- `backend/app/web.py` now provides role-specific dashboard metrics, focus panels, quick actions, and status badges.
- `backend/app/templates/login.html` and `backend/app/templates/dashboard.html` now render a more polished control shell.
- `scripts/ui_quality_gate.mjs` runs Playwright desktop/mobile E2E checks and writes UI artifacts.
- `npm run ui:quality` passed locally and produced desktop/mobile login/dashboard screenshots.
- `scripts/frontend_readiness_gate.mjs` audits whether Next.js can safely start and writes `artifacts/frontend-readiness/report.json`.
- Teacher dashboard now includes a daily workflow panel for next class, attendance, and lesson summary.
- Immediate next sprint: Phase F5 Parent monitoring workflow or resolve F3 external blockers.

---

## Skipped / Deferred

Format:
- Item:
- Reason:
- Dependency:
- Target follow-up:

---

## Official Run Command

Target command resmi:

```bash
python app.py
```

Command ini sudah terverifikasi untuk development lokal setelah `python scripts/init_demo.py`.

---

## Demo Credentials

All seeded demo users use password `password123`:

- `owner@example.com`
- `director@example.com`
- `manager@example.com`
- `admin@example.com`
- `teacher@example.com`
- `parent@example.com`
- `student@example.com`
