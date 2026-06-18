# TODO.md

## Current Focus

Frontend Final UI/UX

## Current Phase

Phase F1 - Flask Shell Polish

## Current Task

Memoles Flask shell sebagai production control shell sambil menunda Next.js app sampai CI runner dan PostgreSQL staging validation hijau.

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
- [ ] Flask web shell masih minimal, sekarang menjadi target polish Phase F1.
- [ ] Staging Docker/PostgreSQL/Redis belum divalidasi secara nyata di host ini karena Docker tidak tersedia; CI workflow sudah menyiapkan validasi dengan service Postgres/Redis.
- [ ] GitHub Actions belum bisa hijau karena runner tidak start akibat billing issue, bukan karena test/code failure.

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
