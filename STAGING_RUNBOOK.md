# Staging Runbook

## Purpose

Use staging to finish Phase 11 infrastructure checks while Phase 12 beta
academies exercise real operational workflows.

## Environment

1. Copy `.env.staging.example` to the staging environment secret store.
2. Set a unique `SECRET_KEY` with at least 32 bytes.
3. Start PostgreSQL and Redis with:

```powershell
docker compose -f compose.staging.yaml up -d
```

4. Install dependencies from the repository root:

```powershell
python -m pip install -r requirements.txt
```

5. Run the staging PostgreSQL validation:

```powershell
python scripts/validate_staging_postgres.py
```

The script requires `DATABASE_URL` to point to PostgreSQL. It runs
`flask --app wsgi db upgrade`, checks a live database connection, and verifies
the live/readiness health endpoints through the Flask app.

6. For manual verification, run the server and check:

```powershell
python app.py
curl http://localhost:5000/api/v1/health/live
curl http://localhost:5000/api/v1/health/ready
```

## CI Validation

The GitHub Actions workflow in `.github/workflows/ci.yml` runs:

- dependency installation from `requirements.txt`,
- Python compile checks,
- the full pytest suite,
- local operational CLI validation with `init-db`, `seed-demo`, and
  `smoke-check`,
- PostgreSQL migration validation against a clean Postgres 16 service,
- Redis availability through the staging environment configuration.

## Local Operational CLI

For development recovery or local smoke checks, run:

```powershell
python scripts/manage.py init-db
python scripts/manage.py seed-demo
python scripts/manage.py smoke-check
```

Equivalent npm wrappers are available:

```powershell
npm run init-db
npm run seed-demo
npm run smoke-check
```

## Beta Launch Checks

- Register limited beta academies through `/api/v1/beta/onboardings`.
- Activate only academies with named operational owners and success criteria.
- Capture parent, teacher, admin, performance, and bug feedback through
  `/api/v1/beta/feedback`.
- Review `/api/v1/beta/readiness` before expanding the cohort.

## Hardening Continuation

- Load testing: run sustained authenticated traffic against staging and watch
  request latency, rate-limit behavior, and database readiness.
- Redis/cache: verify repeated analytics calls expose cache hits and Redis is
  reachable before raising traffic.
- Backup: run `pg_dump` into `storage/staging-backups` and confirm the artifact
  is copied to the intended storage target.
- Recovery: restore the latest staging dump into a disposable PostgreSQL
  database and run readiness checks.
- WebSocket soak: run multiple authenticated Socket.IO clients and verify room
  authorization, event delivery, and reconnect behavior.

## Exit Criteria

- No open critical beta feedback.
- At least one active beta academy completes the agreed success criteria.
- Load, backup, recovery, and WebSocket soak results are recorded.
- Phase 9 frontend accessibility, skeleton loading, and animation polish are
  either complete or explicitly scheduled for the frontend track.
