# TODO.md

## Current Focus

Frontend Final UI/UX

## Current Phase

Phase F5 - Role Workflow Expansion

## Current Task

Menyambungkan workflow SaaS end-to-end mulai dari tenant registration sebelum melanjutkan role workflow panel lain, sambil menunda Next.js app sampai CI runner dan PostgreSQL staging validation hijau.

## Completed In This Session

- [x] Membaca dokumen pondasi wajib: README, vision, foundation, business rules, role matrix, multi-branch architecture, scheduling, parent, teacher, subscription, database, system architecture, UI/UX, AI guidelines, roadmap, dan TODO lama.
- [x] Audit struktur folder project.
- [x] Audit root `app.py`, Flask factory, config, API health, auth API, model inti, migration, dependency, dan assets.
- [x] Membuat `RUNNABLE_MVP_CHECKLIST.md`.
- [x] Menulis hasil audit awal ke `RUNNABLE_MVP_CHECKLIST.md`.
- [x] Mengaktifkan `TODO.md` sebagai working memory recovery.
- [x] Perbaiki config development agar SQLite lokal menjadi default MVP.
- [x] Tambahkan root `requirements.txt`.
- [x] Tambahkan route root `/health`.
- [x] Tambahkan web login/logout/dashboard shell yang memakai model dan role existing.
- [x] Tambahkan templates dan static CSS minimal.
- [x] Tambahkan script init/seed demo idempotent.
- [x] Jalankan `python scripts/init_demo.py` untuk membuat database demo lokal.
- [x] Buktikan login demo dan dashboard role dengan Flask test client.
- [x] Buktikan real local server smoke untuk `/health` dan `/login`.
- [x] Update `RUNNABLE_MVP_CHECKLIST.md` dengan hasil recovery.
- [x] Tambahkan GitHub Actions CI untuk install dependency, compile, full pytest, dan staging PostgreSQL validation.
- [x] Tambahkan `scripts/validate_staging_postgres.py` untuk menjalankan migration upgrade dan health checks di PostgreSQL staging-like environment.
- [x] Tambahkan `npm run staging:validate` sebagai wrapper validasi staging.
- [x] Update `STAGING_RUNBOOK.md` dengan alur validasi PostgreSQL/Redis dan CI.
- [x] Tambahkan CLI resmi `python scripts/manage.py init-db`.
- [x] Tambahkan CLI resmi `python scripts/manage.py seed-demo`.
- [x] Tambahkan CLI resmi `python scripts/manage.py smoke-check`.
- [x] Tambahkan npm wrapper `init-db`, `seed-demo`, dan `smoke-check`.
- [x] Tambahkan validasi CLI lokal ke GitHub Actions.
- [x] Push commit `9e35eae` ke `origin/main`.
- [x] Cek GitHub Actions run `27768742612`.
- [x] Cek GitHub Actions run `27768880118` untuk commit `dd0de21`.
- [x] Tambahkan CSRF token per session untuk login form.
- [x] Tambahkan CSRF token per session untuk logout form.
- [x] Tambahkan default session cookie `HttpOnly` dan `SameSite=Lax`.
- [x] Tambahkan production/staging guard untuk mematikan demo login hints dan demo seed.
- [x] Jadikan demo password bisa dikonfigurasi via environment.
- [x] Update smoke-check CLI agar mengikuti CSRF login flow.
- [x] Tambahkan `backend/tests/test_web_security.py`.
- [x] Putuskan frontend final strategy: polish Flask shell dulu, mulai Next.js setelah CI/staging hijau.
- [x] Tambahkan `FRONTEND_UI_UX_ROADMAP.md`.
- [x] Selesaikan Phase F0 frontend foundation lock.
- [x] Implement baseline Phase F1 Flask shell polish.
- [x] Tambahkan role-specific dashboard metrics, focus panels, dan quick actions.
- [x] Tambahkan UI regression coverage untuk login foundation dan dashboard polish.
- [x] Implement Phase F2 UI quality gate dengan Playwright.
- [x] Tambahkan screenshot desktop/mobile untuk login dan dashboard.
- [x] Tambahkan accessibility baseline checks untuk label input, focus, overflow, dan button names.
- [x] Tambahkan UI quality artifacts report di `artifacts/ui-quality/report.json`.
- [x] Tambahkan `npm run ui:quality`.
- [x] Implement Phase F3 Next.js readiness gate.
- [x] Tambahkan `npm run frontend:readiness`.
- [x] Tambahkan readiness report di `artifacts/frontend-readiness/report.json`.
- [x] Dokumentasikan auth/session strategy untuk Next.js.
- [x] Mulai Phase F5 role workflow expansion.
- [x] Implement baseline Teacher daily workflow panel di Flask dashboard.
- [x] Tambahkan desktop/mobile UI quality coverage untuk Teacher dashboard.
- [x] Implement baseline Parent monitoring workflow panel di Flask dashboard.
- [x] Tambahkan parent trust states untuk empty, loading, error, dan permission denied.
- [x] Tambahkan desktop/mobile UI quality coverage untuk Parent dashboard.
- [x] Implement baseline Branch admin operational workflow panel di Flask dashboard.
- [x] Tambahkan branch admin operational states untuk empty, loading, error, dan permission denied.
- [x] Tambahkan desktop/mobile UI quality coverage untuk Branch Admin dashboard.
- [x] Selesaikan Phase F6 Production Visual QA baseline untuk Flask shell.
- [x] Perluas `npm run ui:quality` dengan `qaChecks` untuk contrast, keyboard, invalid login, invalid CSRF, 403, 404, API error, session expiry, overflow, dan screenshot baseline.
- [x] Tambahkan `CONNECTED_SAAS_WORKFLOW_ROADMAP.md` untuk urutan tenant -> setup bimbel -> role -> guru/parent/murid -> schedule -> operasional -> billing.
- [x] Reprioritaskan `FRONTEND_UI_UX_ROADMAP.md` agar next sprint menjadi Tenant Registration, bukan Branch Manager approval dulu.
- [x] Implement Phase CW1 Tenant Registration baseline.
- [x] Tambahkan Platform Owner-only `/tenants` page dengan tenant list dan create academy form.
- [x] Tambahkan web coverage untuk create tenant, duplicate slug, dan non-Platform Owner denied.
- [x] Tambahkan desktop/mobile UI quality coverage untuk tenant registration.
- [x] Implement Phase CW2 Initial Academy Setup baseline.
- [x] Tambahkan `/academies/<academy_id>/setup` untuk edit profil academy, locale, logo URL, dan lifecycle status.
- [x] Tambahkan suspended/archived read-only messaging untuk academy setup.
- [x] Implement Phase CW3 Branch Setup baseline.
- [x] Tambahkan branch create/list/edit/status/archive flow dari academy setup page.
- [x] Tambahkan web coverage untuk academy update, suspended read-only, branch create/edit/archive, dan Branch Admin denied.
- [x] Tambahkan desktop/mobile UI quality coverage untuk academy setup dan branch creation.
- [x] Implement Phase CW4 Internal Role Setup baseline.
- [x] Tambahkan `/academies/<academy_id>/team` untuk create internal user, assign role, list assignment, dan revoke role.
- [x] Tambahkan scope handling untuk Academy Director, Branch Manager, dan Branch Admin.
- [x] Tambahkan web coverage untuk create, assign, revoke, invalid scope, Academy Director access, dan Branch Admin denied.
- [x] Tambahkan desktop/mobile UI quality coverage untuk internal team setup.
- [x] Implement Phase CW5 Teacher Registration baseline.
- [x] Tambahkan `/academies/<academy_id>/teachers` untuk create teacher, list/detail, branch assignment, dan ended assignment state.
- [x] Tambahkan web coverage untuk teacher user/profile creation, branch assignment ending, branch-scoped visibility, dan cross-branch denial.
- [x] Tambahkan desktop/mobile UI quality coverage untuk teacher registration.
- [x] Implement Phase CW6 Class And Room Setup baseline.
- [x] Tambahkan `/academies/<academy_id>/classes` untuk room create/list/edit dan class create/list/edit dalam branch scope.
- [x] Tambahkan web coverage untuk room/class creation, branch-scoped visibility, dan cross-branch denial.
- [x] Tambahkan desktop/mobile UI quality coverage untuk class and room setup.
- [x] Implement Phase CW7 Student Registration baseline.
- [x] Tambahkan `/academies/<academy_id>/students` untuk create student, list/detail, dan class enrollment.
- [x] Tambahkan web coverage untuk student user/profile creation, class enrollment, branch-scoped visibility, dan cross-branch denial.
- [x] Tambahkan desktop/mobile UI quality coverage untuk student registration.
- [x] Implement Phase CW8 Parent Registration And Child Link baseline.
- [x] Tambahkan `/academies/<academy_id>/parents` untuk create parent, child link, multi-child support, dan revoke link.
- [x] Tambahkan web coverage untuk parent creation, multi-child link, link revoke, branch-scoped visibility, cross-branch denial, dan revoked/unlinked access denial.
- [x] Tambahkan desktop/mobile UI quality coverage untuk parent registration.
- [x] Implement Phase CW9 First Schedule Creation baseline.
- [x] Tambahkan `/academies/<academy_id>/schedules` untuk create schedule, conflict validation result, list/detail, dan session operational context.
- [x] Tambahkan dashboard visibility untuk schedule di Teacher, Student, Parent, Branch Admin, Branch Manager, dan Academy Director.
- [x] Tambahkan web coverage untuk schedule creation, conflict result UI, branch-scope denial, dan role dashboard visibility.
- [x] Tambahkan desktop/mobile UI quality coverage untuk schedule creation.

## Skipped / Deferred Items

- [ ] PostgreSQL local runtime.
  - Reason: Docker/PostgreSQL CLI tidak tersedia di host ini, jadi validasi nyata lokal belum bisa dijalankan.
  - Depends on: Docker Desktop atau PostgreSQL service jika ingin mode production-like.
  - Target: Staging/infrastructure validation.
- [ ] GitHub Actions runner execution.
  - Reason: GitHub reported: "The job was not started because your account is locked due to a billing issue."
  - Depends on: GitHub account/repository billing unlock.
  - Target: CI validation.
- [ ] Frontend Next.js penuh.
  - Reason: Diputuskan menjadi fase berikutnya setelah CI runner dan PostgreSQL staging validation hijau.
  - Depends on: Billing GitHub selesai, CI hijau, staging PostgreSQL/Redis tervalidasi.
  - Target: Customer-facing production app.

## Known Issues

- [ ] Full `python -m pytest -q` lulus, tetapi butuh sekitar 3 menit 15 detik pada host ini; CI perlu timeout realistis atau profiling untuk mempercepat.
- [ ] SQLite local dev memakai `db.create_all()` untuk recovery MVP; staging/production tetap perlu validasi migration chain PostgreSQL.
- [ ] Flask web shell sudah baseline-polished; Phase F5 masih memperluas workflow role satu per satu.
- [ ] Staging Docker/PostgreSQL/Redis belum divalidasi secara nyata di host ini karena Docker tidak tersedia; CI workflow sudah menyiapkan validasi dengan service Postgres/Redis.
- [ ] GitHub Actions belum bisa hijau karena runner tidak start akibat billing issue, bukan karena test/code failure.
- [ ] Phase F3 readiness gate implemented, tetapi keputusan mulai Next.js masih blocked oleh CI/staging eksternal.
- [ ] Phase F5 masih berlanjut, tetapi urutan eksekusi sekarang mengikuti `CONNECTED_SAAS_WORKFLOW_ROADMAP.md`.
- [ ] Next workflow utama adalah Phase CW10 - Daily Operations.
- [ ] Cross-browser sign-off selain Chromium masih release activity eksternal jika CI nanti memasang Firefox/WebKit.

## Next Actions

- [ ] Profil durasi full test suite dan pecah CI menjadi lane cepat serta lane lengkap.
- [x] Tambahkan CI workflow untuk install, compile, full tests, dan PostgreSQL staging validation.
- [x] Tambahkan script validasi migration chain di PostgreSQL staging-like environment.
- [ ] Jalankan workflow CI di GitHub dan pastikan service Postgres/Redis lulus pada runner.
- [ ] Jalankan `python scripts/validate_staging_postgres.py` di mesin lokal/staging yang memiliki Docker atau PostgreSQL.
- [x] Tambahkan command CLI resmi untuk `init-db`, `seed-demo`, dan `smoke-check`.
- [x] Putuskan frontend final: lanjut polish Flask shell dulu, Next.js setelah CI/staging hijau.
- [x] Implement baseline Phase F1 Flask shell polish dari `FRONTEND_UI_UX_ROADMAP.md`.
- [x] Tambahkan role-specific dashboard sections untuk semua role.
- [x] Tambahkan UI quality gates untuk desktop/mobile screenshot dan accessibility baseline.
- [ ] Tambahkan production deployment checklist: secret management, Redis, rate limit, backup, monitoring, log retention, dan rollback.
- [ ] Resolve external F3 blockers: GitHub Actions billing, CI green, PostgreSQL staging validation.
- [ ] Setelah F3 unblocked, mulai Phase F4 Next.js App Foundation.
- [x] Lanjutkan Phase F5 Parent monitoring workflow.
- [x] Lanjutkan Phase F5 Branch admin operational workflow.
- [x] Lanjutkan Phase CW1 Tenant Registration.
- [x] Lanjutkan Phase CW2 Initial Academy Setup.
- [x] Lanjutkan Phase CW3 Branch Setup.
- [x] Lanjutkan Phase CW4 Internal Role Setup.
- [x] Lanjutkan Phase CW5 Teacher Registration.
- [x] Lanjutkan Phase CW6 Class And Room Setup.
- [x] Lanjutkan Phase CW7 Student Registration.
- [x] Lanjutkan Phase CW8 Parent Registration And Child Link.
- [x] Lanjutkan Phase CW9 First Schedule Creation.
- [ ] Lanjutkan Phase CW10 Daily Operations.
- [ ] Setelah CW1-CW10 hidup, lanjutkan Phase F5 Branch manager approval workflow sebagai Phase CW11.
- [x] Selesaikan Phase F6 Production Visual QA baseline.
- [ ] Rekomendasi next step: implement Phase CW10 Daily Operations sambil tetap unblock GitHub Actions billing dan PostgreSQL staging validation.
- [ ] Tambahkan minimal E2E test untuk login web dan dashboard role.
- [x] Audit security session cookie, CSRF untuk form web, dan password/credential policy sebelum beta publik.

## Recovery Notes

Runnable MVP recovery selesai pada June 18, 2026. Command lokal:

```bash
python scripts/init_demo.py
python app.py
```

Demo users:
- `owner@example.com`
- `director@example.com`
- `manager@example.com`
- `admin@example.com`
- `teacher@example.com`
- `parent@example.com`
- `student@example.com`

All demo users use password `password123`.

Jangan menambah fitur besar sebelum production readiness baseline stabil. Gunakan role assignment existing (`Role`, `ScopeType`, `RoleAssignment`) dan model existing (`Academy`, `Branch`, `User`) supaya tidak membuat auth/dashboard duplikat. Development boleh SQLite untuk bootstrapping lokal; production guard tetap melarang SQLite.


-------------
CW13 - Academy Director Reporting Workflow selesai baseline. Academy Director sekarang punya academy-wide branch rollup, tabel perbandingan cabang untuk attendance consistency, schedule stability, teacher workload, dan parent engagement, plus coverage backend dan UI quality gate desktop/mobile.

Lanjut berikutnya: CW14 - SaaS Billing, Tier, Subscription, Addon. Fokus awalnya subscription state yang terlihat jelas di UI: trial/grace/suspended banner, plan detail, addon placeholder, dan backend-validated feature gating untuk Platform Owner + Academy Director.
