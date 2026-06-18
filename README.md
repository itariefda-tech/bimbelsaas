# Premium Multi-Branch Academic Operations Platform

> Enterprise-grade SaaS platform for premium tutoring institutions, learning centers, and academic organizations with multi-branch operations, parent monitoring, scheduling management, invoicing, and operational control.

---

# Overview

Premium Multi-Branch Academic Operations Platform adalah sistem SaaS modern untuk lembaga pendidikan premium yang membutuhkan:

* multi branch management,
* parent transparency,
* academic operations control,
* teacher workflow management,
* scheduling stability,
* invoicing & subscription,
* dan operational anti-chaos system.

Platform ini dirancang untuk menangani operasional akademik kompleks dengan:

* ratusan murid,
* banyak guru,
* banyak cabang,
* jadwal padat,
* perubahan jadwal realtime,
* distribusi materi,
* dan kebutuhan monitoring premium.

---

# Core Vision

Membangun platform akademik premium yang:

* stabil,
* transparan,
* scalable,
* dan nyaman digunakan oleh seluruh pihak.

Sistem harus membantu:

* wali murid merasa tenang,
* guru merasa terbantu,
* admin tidak tenggelam dalam chaos,
* dan Academy Director dapat memonitor seluruh operasional dengan jelas.

---

# Platform Philosophy

## 1. Anti-Chaos Operations

Platform dirancang untuk mengurangi:

* jadwal bentrok,
* miskomunikasi,
* kehilangan materi,
* operational overload,
* dan konflik antar divisi.

---

## 2. Parent Trust System

Wali murid adalah user paling penting dalam pengalaman premium.

Platform harus memberikan:

* transparansi,
* monitoring valid,
* histori aktivitas,
* dan rasa aman terhadap proses belajar anak.

---

## 3. Teacher-Friendly Workflow

Guru dapat menangani:

* 100–200 murid,
* banyak kelas,
* lintas cabang,
* dan perubahan jadwal.

Sistem harus:

* cepat,
* minim klik,
* minim gangguan,
* dan fokus pada workflow harian.

---

## 4. Multi-Branch First Architecture

Platform dibangun dengan pendekatan:

* multi branch by default,
* bukan single branch yang dipaksa berkembang.

Semua branch:

* setara,
* independen,
* memiliki operasional sendiri,
* billing sendiri,
* dan admin sendiri.

---

## 5. SaaS Scalability

Platform dirancang sebagai:

* multi academy SaaS,
* bukan software single institution.

Satu platform dapat digunakan banyak academy dengan data terisolasi.

---

# System Hierarchy

```text id="8qek20"
Platform Owner
└── Academy
    ├── Academy Director
    ├── Branch Manager
    ├── Branch Admin
    ├── Teacher
    ├── Student
    └── Parent
```

---

# Main Roles

## Platform Owner

Pemilik platform SaaS.

Monitoring:

* academy subscriptions
* global revenue
* storage
* tenant activity
* platform health
* global analytics

---

## Academy Director

Pemilik atau kepala academy.

Mengontrol:

* seluruh branch academy,
* global academy performance,
* revenue,
* teacher monitoring,
* operational overview.

---

## Branch Manager

Mengelola operasional branch.

Fokus:

* branch KPI,
* scheduling stability,
* teacher management,
* operational approval.

---

## Branch Admin

Operator harian branch.

Fokus:

* scheduling,
* attendance,
* invoicing,
* class management,
* student administration.

---

## Teacher

Pengajar akademik.

Fokus:

* teaching workflow,
* attendance,
* lesson reporting,
* material access,
* student progress.

---

## Student

Peserta belajar.

Fokus:

* schedules,
* assignments,
* materials,
* attendance,
* academic progress.

---

## Parent

Wali murid.

Fokus:

* monitoring,
* invoicing,
* attendance visibility,
* child progress,
* academic trust layer.

---

# Core Features

## Academic Operations

* student registration
* placement test
* class assignment
* scheduling engine
* reschedule workflow
* attendance system

---

## Multi-Branch System

* branch isolation
* branch management
* cross branch teacher
* cross branch student access
* branch-level invoicing

---

## Parent Monitoring

* realtime activity feed
* attendance visibility
* lesson summaries
* academic progress
* schedule tracking

---

## Teacher Workflow

* today teaching timeline
* quick attendance
* lesson reports
* teaching materials
* operational notifications

---

## Material Management

* module repository
* material versioning
* print queue
* archive management

---

## Financial System

* invoicing
* payment tracking
* overdue reminder
* branch financial reporting
* subscription management

---

## Communication System

* class group
* teacher announcements
* parent communication
* realtime notifications

---

# Multi-Branch Architecture

All branches are equal.

There is:

* no master branch,
* no superior branch,
* no dependent branch.

Each branch:

* has its own admin,
* has its own billing,
* has its own operational workflow.

Academy Director monitors all branches globally.

---

# Cross Branch System

Platform supports:

* teacher multi-branch assignment,
* student cross-branch access,
* premium branch access upgrades.

Scheduling engine must prevent:

* teacher conflicts,
* room conflicts,
* branch conflicts,
* overlapping schedules.

---

# Subscription & SaaS Model

## Academy Subscription

Academy subscribes to the platform as SaaS customer.

Included:

* branch operations
* teacher management
* scheduling
* invoicing
* parent monitoring

---

## Student / Parent Premium Tier

Optional premium upgrades:

* cross branch access
* advanced parent analytics
* premium reports
* enhanced monitoring

---

# Suggested Technology Stack

## Frontend

* Next.js
* React
* TailwindCSS

---

## Backend

* Python Flask
* Flask REST API
* Socket.IO

---

## Database

* PostgreSQL

---

## Infrastructure

* Docker
* Nginx
* Cloudflare
* Redis (future scaling)

---

# Simple Architecture

```text id="cn2a50"
+----------------------+
|      Frontend        |
|   Next.js / React    |
+----------+-----------+
           |
           v
+----------------------+
|     API Backend      |
|   Flask REST API     |
+----------+-----------+
           |
    +------+------+
    |             |
    v             v
+--------+   +-------------+
|Realtime|   | File Storage|
|SocketIO|   | Materials   |
+--------+   +-------------+
           |
           v
+----------------------+
|    PostgreSQL DB     |
+----------------------+
```

---

# Core Database Concepts

All critical data are isolated using:

```sql id="h6y9ee"
academy_id
branch_id
```

This applies to:

* students
* teachers
* schedules
* invoices
* attendance
* materials
* communications

---

# UI/UX Direction

Visual direction:

* premium academic
* elegant
* minimal chaos
* operationally fast
* mobile-first
* high readability

Suggested colors:

* navy
* ivory
* emerald
* gold
* soft dark themes

---

# Non-Functional Priorities

## High Priority

* scheduling stability
* realtime notification
* parent trust
* operational speed
* audit logging

---

## Medium Priority

* AI assistance
* smart analytics
* workflow automation

---

## Future Scalability

* mobile apps
* AI recommendation
* smart scheduling
* franchise academy support
* advanced analytics

---

# AI Agent / Codex Rules

This repository is AI-agent assisted.

All AI agents MUST:

* follow architecture,
* avoid duplicate logic,
* avoid orphan components,
* avoid hardcoded workflow,
* follow business rules,
* respect multi-branch isolation.

Detailed rules are documented inside:

`AI_AGENT_GUIDELINES.md`

---

# Backend Development

The backend foundation and Phase 2 authentication system live in `backend/`.

Local setup:

```powershell
docker compose up -d postgres
cd backend
python -m pip install -e ".[dev]"
flask --app wsgi db upgrade
flask --app wsgi run
```

Root-level convenience commands:

```powershell
python app.py
npm run dev
```

Both commands run the Flask/Socket.IO backend from `backend/`. This repository
does not include a frontend application yet, so `npm run dev` is only a backend
shortcut.

Core health endpoints:

```text
GET /api/v1/health/live
GET /api/v1/health/ready
```

Authentication endpoints:

```text
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
GET  /api/v1/auth/me
```

Academy and branch endpoints:

```text
GET    /api/v1/academies
POST   /api/v1/academies
GET    /api/v1/academies/{academy_id}
PATCH  /api/v1/academies/{academy_id}
DELETE /api/v1/academies/{academy_id}

GET    /api/v1/academies/{academy_id}/branches
POST   /api/v1/academies/{academy_id}/branches
GET    /api/v1/branches/{branch_id}
PATCH  /api/v1/branches/{branch_id}
DELETE /api/v1/branches/{branch_id}
GET    /api/v1/branches/{branch_id}/summary
```

Academy and branch deletion is a soft archive operation. Status changes follow
explicit lifecycle transitions, and branch-level users only receive records
covered by their active role assignments.

Teacher and student foundation endpoints:

```text
GET    /api/v1/academies/{academy_id}/teachers
POST   /api/v1/branches/{branch_id}/teachers
GET    /api/v1/academies/{academy_id}/teachers/{teacher_id}
PATCH  /api/v1/academies/{academy_id}/teachers/{teacher_id}
DELETE /api/v1/academies/{academy_id}/teachers/{teacher_id}
POST   /api/v1/academies/{academy_id}/teachers/{teacher_id}/branches/{branch_id}
DELETE /api/v1/academies/{academy_id}/teachers/{teacher_id}/branches/{branch_id}

GET    /api/v1/academies/{academy_id}/students
POST   /api/v1/branches/{branch_id}/students
GET    /api/v1/academies/{academy_id}/students/{student_id}
PATCH  /api/v1/academies/{academy_id}/students/{student_id}
DELETE /api/v1/academies/{academy_id}/students/{student_id}
GET    /api/v1/academies/{academy_id}/students/{student_id}/branch-access/{branch_id}
```

Teacher branch assignments are explicit and may span multiple active branches.
Students always have one mandatory home branch. Non-home branch access remains
default-deny until Phase 7 supplies an active entitlement provider.

Scheduling foundation endpoints:

```text
GET  /api/v1/branches/{branch_id}/classes
POST /api/v1/branches/{branch_id}/classes
POST /api/v1/branches/{branch_id}/classes/{class_id}/students/{student_id}

GET  /api/v1/branches/{branch_id}/rooms
POST /api/v1/branches/{branch_id}/rooms

GET   /api/v1/branches/{branch_id}/schedules
POST  /api/v1/branches/{branch_id}/schedules
PATCH /api/v1/branches/{branch_id}/schedules/{schedule_id}/status

GET  /api/v1/branches/{branch_id}/schedules/{schedule_id}/reschedule-requests
POST /api/v1/branches/{branch_id}/schedules/{schedule_id}/reschedule-requests
POST /api/v1/branches/{branch_id}/reschedule-requests/{request_id}/approve
POST /api/v1/branches/{branch_id}/reschedule-requests/{request_id}/reject
```

Schedule creation runs a fixed validation pipeline for branch scope, teacher
assignment and overlap, room availability and overlap, Student overlap,
duplicate class time, and cross-branch entitlement. Every Schedule creates one
operational Session and writes an audit record. Datetimes must include an
offset and are stored as timezone-aware UTC values with the IANA timezone kept
for local presentation.

Reschedule requests preserve immutable original/proposed snapshots and require
reasons. Approval authority follows the requester role, reruns the full
conflict pipeline, marks the original Schedule as `rescheduled`, and creates a
new replacement Schedule instead of overwriting history.

Attendance workflow endpoints:

```text
GET  /api/v1/branches/{branch_id}/sessions/{session_id}/attendance
PUT  /api/v1/branches/{branch_id}/sessions/{session_id}/attendance
POST /api/v1/branches/{branch_id}/sessions/{session_id}/attendance/finalize

POST /api/v1/branches/{branch_id}/attendances/{attendance_id}/edit-requests
POST /api/v1/branches/{branch_id}/attendance-edit-requests/{request_id}/approve
POST /api/v1/branches/{branch_id}/attendance-edit-requests/{request_id}/reject
```

Attendance is stored per Student and Session. Draft sheets support bulk updates
for quick teacher operation. Finalization requires every active class Student,
locks direct edits, and routes later corrections through immutable,
reason-backed approval requests with full audit history.

Teacher dashboard and lesson summary endpoints:

```text
GET /api/v1/teacher/dashboard?date=YYYY-MM-DD&timezone=Asia/Jakarta

GET  /api/v1/branches/{branch_id}/sessions/{session_id}/lesson-summary
PUT  /api/v1/branches/{branch_id}/sessions/{session_id}/lesson-summary
POST /api/v1/branches/{branch_id}/sessions/{session_id}/lesson-summary/publish

POST /api/v1/branches/{branch_id}/lesson-summaries/{summary_id}/edit-requests
POST /api/v1/branches/{branch_id}/lesson-summary-edit-requests/{request_id}/approve
POST /api/v1/branches/{branch_id}/lesson-summary-edit-requests/{request_id}/reject
```

The dashboard returns only Sessions belonging to the authenticated Teacher
profile, ordered across branches with class, room, student count, attendance,
lesson-summary state, and action shortcuts. Lesson summaries support draft
updates, publication locking, and audited correction approval.

Material and notification boundary endpoints:

```text
GET  /api/v1/academies/{academy_id}/materials
POST /api/v1/branches/{branch_id}/classes/{class_id}/materials
POST /api/v1/branches/{branch_id}/classes/{class_id}/materials/{material_id}/versions
POST /api/v1/branches/{branch_id}/classes/{class_id}/materials/{material_id}/versions/{version_id}/submit
POST /api/v1/academies/{academy_id}/materials/{material_id}/versions/{version_id}/approve
PUT  /api/v1/branches/{branch_id}/classes/{class_id}/materials/{material_id}/distribution
GET  /api/v1/branches/{branch_id}/classes/{class_id}/materials

GET   /api/v1/notifications
PATCH /api/v1/notifications/{notification_id}/read
```

Materials are academy-wide identities with immutable numbered file versions.
Only reviewed and approved versions may be distributed to a branch/Class.
Teacher access remains assigned-Class scoped. Preview/download endpoints expose
validated storage metadata; binary serving and signed URLs remain delegated to
the future storage provider.

The notification system stores deduplicated in-app events and read state,
queues durable delivery records, and synchronizes scoped Socket.IO events.
External push/email providers remain pluggable delivery channels.

Parent experience endpoints:

```text
GET /api/v1/parent/dashboard
GET /api/v1/parent/children
GET /api/v1/parent/children/{student_id}/overview
GET /api/v1/parent/children/{student_id}/attendance
GET /api/v1/parent/children/{student_id}/lesson-summaries
GET /api/v1/parent/children/{student_id}/schedule
```

Parent-child relationships are explicit and synchronized with active
`parent`/`linked_student` assignments. Attendance history exposes finalized
sessions only, lesson summaries expose published records only, and schedule
responses retain cancelled or rescheduled states for transparent monitoring.

Authorization rules:

* user identity is separate from role assignments,
* users may hold multiple active roles,
* every role assignment has an explicit platform, academy, branch, assigned
  class, linked student, or self scope,
* access JWTs are short-lived and refresh JWTs rotate through revocable
  server-side sessions,
* role and permission state is loaded from the database on every authenticated
  request rather than trusted from JWT claims,
* backend routes use centralized permission grants and scoped authorization
  decorators.

Run backend checks:

```powershell
cd backend
python -m pytest
python -m compileall -q app tests migrations
```

Run local operational CLI checks from the repository root:

```powershell
python scripts/manage.py init-db
python scripts/manage.py seed-demo
python scripts/manage.py smoke-check
```

Equivalent npm wrappers:

```powershell
npm run init-db
npm run seed-demo
npm run smoke-check
```

Run PostgreSQL staging validation when PostgreSQL/Redis are available:

```powershell
python scripts/validate_staging_postgres.py
```

---

# Current Development Status

Current phase:

* Phase 0 documentation foundation completed
* Phase 1 core backend foundation completed
* Phase 2 authentication and role system completed
* Phase 3 academy, branch, teacher, and student foundation completed
* Phase 4 operational scheduling and reschedule workflow completed
* Phase 5 attendance lifecycle and edit approval foundation completed
* Phase 5 teacher dashboard and lesson summary lifecycle completed
* Phase 5 material access and notification boundary completed
* Phase 6 premium parent experience completed
* Phase 7 financial, subscription, addon, and feature-gating foundation completed
* Phase 8 Socket.IO, realtime outbox, notification queue, and sync completed
* Phase 9 backend UI/UX support completed
* Phase 10 analytics and reporting foundation completed
* Phase 11 backend production hardening completed
* Phase 12 backend beta launch preparation completed
* Phase 13 backend scale and optimization foundation completed
* next: Run staging beta cohort, Redis/queue validation, and infrastructure tests

---

# Main Goal

Build a calm, premium, scalable academic ecosystem where:

* parents trust the academy,
* teachers feel supported,
* admins remain organized,
* and operations stay stable even under heavy daily activity.
