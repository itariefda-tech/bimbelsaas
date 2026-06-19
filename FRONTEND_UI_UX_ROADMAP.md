# Frontend Final UI/UX Roadmap

## Decision

Frontend final masuk bertahap:

1. Polish Flask shell sebagai production control shell.
2. Mulai Next.js app setelah CI runner dan PostgreSQL staging validation hijau.

Alasan:

- Backend, auth, role, health, demo seed, dan dashboard minimal sudah hidup.
- Flask shell sudah cukup untuk operational smoke, internal beta, dan staging control.
- Next.js layak untuk produk final premium, tetapi sebaiknya tidak dimulai sebelum CI/staging runtime stabil.
- UI final harus role-aware, mobile-first, dan anti-chaos, bukan sekadar dekorasi.

## Product Experience Target

Platform harus terasa:

- calm premium,
- operationally dense but readable,
- role-aware,
- mobile-first untuk teacher, parent, dan student,
- fast untuk admin,
- trustworthy untuk parent,
- structured untuk director dan owner.

## Phase F0 - Frontend Foundation Lock

Status: completed

Objective:

Menetapkan fondasi visual dan interaction system sebelum memperluas halaman.

Deliverables:

- Design tokens final untuk color, spacing, radius, shadow, typography, status tone.
- Component inventory dari Flask shell yang sudah ada.
- Role dashboard information architecture.
- Responsive rules mobile/tablet/desktop.
- Accessibility checklist baseline.
- Copywriting tone guide untuk error, empty state, loading, dan confirmation.

Acceptance criteria:

- [x] Semua warna utama terdokumentasi.
- [x] Tidak ada one-note palette.
- [x] Card radius tetap maksimal 8px.
- [x] Button, badge, input, message, layout, dan nav punya pola konsisten.
- [x] Mobile role navigation tidak overflow secara merusak.

Implementation notes:

- `backend/app/static/css/mvp.css` now contains the initial token system for surface, text, line, status, shadow, and role dashboard tones.
- Flask templates use shared UI patterns for shell layout, login, role rail, metric cards, work panels, action buttons, messages, and errors.

## Phase F1 - Flask Shell Polish

Status: baseline implemented

Objective:

Membuat Flask shell cukup polished untuk internal beta, staging validation, dan stakeholder demo.

Scope:

- Login page premium but quiet.
- Topbar dan role navigation lebih profesional.
- Dashboard shell per role tidak lagi terasa sama.
- Empty/error state lebih manusiawi.
- Status badges dan KPI cards konsisten.
- Mobile layout lebih nyaman.
- CSRF/session security UI tetap tidak mengganggu.

Role-specific polish:

- Platform Owner: global SaaS health, academy count, beta readiness, system status.
- Academy Director: branch overview, revenue/attendance health, alerts.
- Branch Manager: today operations, schedule stability, teacher load.
- Branch Admin: quick actions, search entry, pending operations.
- Teacher: today timeline, next class, attendance shortcut, material shortcut.
- Parent: child overview, schedule, attendance, invoice, learning progress.
- Student: schedule, materials, simple learning status.

Decor direction:

- Use restrained academic premium surfaces.
- Use subtle line, shadow, and spacing rather than decorative blobs.
- Avoid gradient-heavy hero/dashboard styling.
- Avoid stock-like decoration.
- Use icons only when commands or status become clearer.

Acceptance criteria:

- [x] `/login`, `/dashboard`, `/dashboard/<role>`, 403, and 404 feel coherent.
- [x] Each role dashboard has at least one role-specific primary section.
- [x] Mobile viewport does not require horizontal page scrolling.
- [x] Text does not overlap or overflow controls.
- [x] `python scripts/manage.py smoke-check` passes.
- [x] `python -m pytest -q` passes after this phase.

Implementation notes:

- `backend/app/web.py` now builds role-specific dashboard context for metrics, role focus, quick actions, and status badges.
- `backend/app/templates/dashboard.html` renders a role-aware production control shell.
- `backend/app/templates/login.html` now presents the shell as a secure operations entry point.
- `backend/tests/test_web_security.py` includes coverage for the login foundation and role-specific dashboard polish.

## Phase F2 - Frontend Quality Gates

Status: completed

Objective:

Menambahkan guard agar UI polish tidak regresi.

Deliverables:

- [x] Playwright smoke test untuk login dan dashboard.
- [x] Screenshot checks desktop/mobile.
- [x] Accessibility baseline checks.
- [x] Contrast review for tokens and status badges.
- [x] Form state checks: default, invalid CSRF, invalid login, success login.

Acceptance criteria:

- [x] Desktop and mobile screenshots are nonblank and visually stable.
- [x] Login and dashboard E2E pass locally.
- [x] Critical keyboard navigation works.
- [x] Buttons and links have visible focus states.

Implementation notes:

- `scripts/ui_quality_gate.mjs` seeds demo data, starts Flask without the development reloader, runs Playwright against desktop and mobile viewports, saves screenshots, and writes `artifacts/ui-quality/report.json`.
- `npm run ui:quality` is the official local command.
- CI now installs Playwright Chromium, runs the UI gate, and uploads `artifacts/ui-quality`.

## Phase F3 - Next.js Readiness Gate

Status: implemented, externally blocked

Objective:

Memulai Next.js hanya setelah backend deployment confidence cukup.

Entry criteria:

- [ ] GitHub Actions billing issue selesai.
- [ ] CI workflow hijau.
- [ ] PostgreSQL staging validation hijau.
- [x] Backend API contract untuk dashboard role stabil.
- [x] Auth/session or token strategy untuk Next.js diputuskan.
- [x] Design tokens dari Flask shell final cukup untuk diport.

Implementation notes:

- `scripts/frontend_readiness_gate.mjs` audits F0-F2 evidence, runs local commands, writes `artifacts/frontend-readiness/report.json`, and reports whether Next.js may start.
- `npm run frontend:readiness` is the local non-strict readiness report command.
- CI runs the readiness gate in strict mode only after PostgreSQL staging validation.
- Current decision remains blocked because GitHub Actions billing and PostgreSQL staging validation are external gates.

Auth/session strategy for Next.js:

- Keep Flask shell session auth as the internal/staging control plane.
- Build the future Next.js app as a customer-facing client using backend auth APIs and short-lived access tokens.
- Do not trust frontend role claims; reload role and permission state from backend APIs.
- Keep CSRF/session protection for Flask forms and use explicit API auth boundaries for Next.js.

Decision options:

- Next.js as full app shell: best for product-grade UX and future frontend velocity.
- Flask shell remains internal console: best for admin/staging/ops fallback.

Recommended direction:

- Keep Flask shell as internal/staging control plane.
- Build Next.js as customer-facing production app once staging is green.

## Phase F4 - Next.js App Foundation

Status: future

Objective:

Membangun frontend produk final dengan architecture yang siap tumbuh.

Deliverables:

- Next.js app scaffold.
- API client with typed response boundaries.
- Auth flow decision and implementation.
- Shared design tokens mirrored from Flask shell.
- Role-based route groups.
- Layout system: desktop sidebar/topbar, mobile bottom navigation.
- Component library: button, input, badge, card, table, tabs, modal, toast, skeleton.
- Error/empty/loading states.

Acceptance criteria:

- Role dashboards render from real backend data or stable dashboard endpoints.
- Mobile teacher/parent/student flows are first-class.
- CI includes frontend lint/test/build.
- Playwright smoke covers login and role dashboard.

## Phase F5 - Role Workflow Expansion

Status: in progress, reprioritized by connected SaaS workflow

Objective:

Membuat UI bukan hanya dashboard, tapi workflow utama yang usable.

Connected workflow note:

- `CONNECTED_SAAS_WORKFLOW_ROADMAP.md` is now the execution order for making dashboards connect end-to-end.
- Tenant registration and academy setup must happen before adding more isolated role workflow panels.
- Billing, tier, subscription, and addon UI should come after the tenant -> branch -> role -> teacher/student/parent -> schedule chain is alive.

Priority order:

1. Connected tenant registration and setup workflow. - see `CONNECTED_SAAS_WORKFLOW_ROADMAP.md`
2. Branch manager approval workflow.
3. Academy director reporting workflow.
4. Platform owner SaaS operation workflow.
5. Student learning workspace.
6. Billing, tier, subscription, and addon UI.

Deliverables per workflow:

- Primary dashboard.
- Detail page.
- Action flow.
- Empty state.
- Error state.
- Loading/skeleton state.
- Mobile state.
- Permission denied state.

Implementation notes:

- Teacher dashboard now includes a `Today teaching flow` panel with next class, attendance, and lesson summary steps.
- Parent dashboard now includes a `Monitoring flow` with child overview, activity feed, schedule, invoice, and progress steps.
- Parent dashboard also includes trust state coverage for empty, loading, error, and permission denied states.
- Branch admin dashboard now includes a `Branch admin operations flow` for search, schedule, attendance support, invoice support, and pending operations.
- Branch admin dashboard also includes operational state coverage for empty, loading, error, and permission denied states.
- Tenant registration now has a Platform Owner-only `/tenants` page with create academy form, tenant list, duplicate slug handling, and permission denied coverage.
- Academy setup now has `/academies/<academy_id>/setup` with academy profile editing, lifecycle status visibility, suspended/archived read-only messaging, and first branch setup.
- Branch setup now supports create, list/detail, edit, operational status update, and archive actions from the academy setup page.
- Internal role setup now has `/academies/<academy_id>/team` with internal user creation, role assignment, active assignment list, revoke action, and scope/permission states.
- `npm run ui:quality` captures teacher, parent, branch admin, tenant registration, academy setup, and internal team screenshots in desktop and mobile viewports.
- `backend/tests/test_web_security.py` includes server-side coverage for teacher daily workflow, parent monitoring workflow, and branch admin operational workflow panels.

## Phase F6 - Production Visual QA

Status: completed for Flask shell baseline

Objective:

Mempersiapkan UI untuk beta/public production.

Checklist:

- [x] Cross-browser baseline: automated Chromium review in CI/local gate.
- [x] Mobile viewport review.
- [x] Keyboard navigation.
- [x] Color contrast.
- [x] Loading and slow network state copy.
- [x] Long text and localized copy overflow.
- [x] API error handling.
- [x] Session expiry handling.
- [x] Role access and navigation stability.
- [x] Unauthorized and forbidden states.
- [x] Screenshot baseline.

Implementation notes:

- `scripts/ui_quality_gate.mjs` now writes explicit `qaChecks` into `artifacts/ui-quality/report.json`.
- The gate covers login, Platform Owner, Teacher, Parent, Branch Admin, 403, and 404 screenshots.
- Production visual QA now verifies contrast token pairs, critical keyboard traversal, invalid login, invalid CSRF, structured API 404, session expiry, forbidden role access, horizontal overflow, and important text overflow.
- Cross-browser production sign-off beyond Chromium remains an external release activity if CI later installs Firefox/WebKit; the automated Flask shell baseline is complete and repeatable.

## Immediate Next Sprint

Recommended sprint: Phase CW5 - Teacher Registration from `CONNECTED_SAAS_WORKFLOW_ROADMAP.md`.

Tasks:

- Add teacher user/profile creation form.
- Add teacher list/detail view.
- Add teacher branch assignment UI.
- Add active/ended assignment state.
- Add invalid cross-branch assignment and permission denied states.
- Add Flask web coverage and Playwright desktop/mobile screenshots for teacher registration.

## Definition of Done

Frontend Final Phase is considered production-near when:

- Flask shell is polished enough for internal operations.
- CI is green after billing unblock.
- PostgreSQL staging validation passes.
- Security baseline remains green.
- Next.js decision is re-evaluated with staging confidence.
- UI roadmap acceptance criteria are checked phase by phase.
