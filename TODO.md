# TODO.md

## Current Focus

Production Readiness

## Current Phase

Post-Recovery Stabilization

## Current Task

Memperkuat Runnable MVP menuju staging dan production readiness: migration validation, full test stabilization, CI, frontend decision, deployment, observability, dan security hardening.

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

## Skipped / Deferred Items

- [ ] PostgreSQL local runtime.
  - Reason: Docker/PostgreSQL CLI tidak tersedia di host ini, jadi validasi nyata lokal belum bisa dijalankan.
  - Depends on: Docker Desktop atau PostgreSQL service jika ingin mode production-like.
  - Target: Staging/infrastructure validation.
- [ ] Frontend Next.js penuh.
  - Reason: Repository saat ini backend/API; MVP hanya butuh Flask web shell minimal.
  - Depends on: Keputusan frontend app.
  - Target: Frontend implementation follow-up.

## Known Issues

- [ ] Full `python -m pytest -q` lulus, tetapi butuh sekitar 3 menit 15 detik pada host ini; CI perlu timeout realistis atau profiling untuk mempercepat.
- [ ] SQLite local dev memakai `db.create_all()` untuk recovery MVP; staging/production tetap perlu validasi migration chain PostgreSQL.
- [ ] Flask web shell masih minimal, bukan frontend produk final.
- [ ] Staging Docker/PostgreSQL/Redis belum divalidasi secara nyata di host ini karena Docker tidak tersedia; CI workflow sudah menyiapkan validasi dengan service Postgres/Redis.

## Next Actions

- [ ] Profil durasi full test suite dan pecah CI menjadi lane cepat serta lane lengkap.
- [x] Tambahkan CI workflow untuk install, compile, full tests, dan PostgreSQL staging validation.
- [x] Tambahkan script validasi migration chain di PostgreSQL staging-like environment.
- [ ] Jalankan workflow CI di GitHub dan pastikan service Postgres/Redis lulus pada runner.
- [ ] Jalankan `python scripts/validate_staging_postgres.py` di mesin lokal/staging yang memiliki Docker atau PostgreSQL.
- [x] Tambahkan command CLI resmi untuk `init-db`, `seed-demo`, dan `smoke-check`.
- [ ] Putuskan frontend final: lanjut Flask shell sebagai admin MVP atau mulai Next.js app.
- [ ] Tambahkan production deployment checklist: secret management, Redis, rate limit, backup, monitoring, log retention, dan rollback.
- [ ] Tambahkan minimal E2E test untuk login web dan dashboard role.
- [ ] Audit security session cookie, CSRF untuk form web, dan password/credential policy sebelum beta publik.

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
