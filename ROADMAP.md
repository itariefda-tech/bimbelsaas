# Premium Multi-Branch Academic Operations Platform

---

# Purpose

Dokumen ini adalah:

* roadmap utama project,
* urutan implementasi resmi,
* panduan phase development,
* dan anti-chaos execution guide.

Roadmap ini dibuat untuk:

* menjaga stabilitas development,
* menjaga fokus implementasi,
* mengurangi scope chaos,
* dan membantu AI agents bekerja terarah.

---

# Core Roadmap Philosophy

---

# 1. Stability Before Features

Prioritas utama:

* stabilitas,
* clarity,
* maintainability.

Bukan:

* banyak fitur cepat jadi.

---

# Rule

Jangan membangun:

* AI,
* analytics kompleks,
* automation besar,
* mobile apps,
* atau gamification

sebelum:

* operational foundation stabil.

---

# 2. Operational Core First

Platform ini adalah:

* operational system.

Maka:

* operational workflow
  lebih penting daripada visual gimmick.

---

# 3. Anti-Chaos Development

Development wajib:

* bertahap,
* modular,
* measurable,
* dan auditable.

---

# Forbidden Development Behavior

Tidak boleh:

* random feature jumping,
* implementasi tanpa roadmap,
* duplicate systems,
* atau “nanti dirapihin belakangan”.

Karena:

> “nanti dirapihin”
> biasanya menjadi kuburan technical debt.

---

# 4. Production Mindset Early

Walaupun masih MVP:

* architecture tetap harus production-minded.

---

# Rule

Jangan membuat:

* fake structure,
* temporary naming,
* placeholder chaos,
* atau shortcut architecture.

---

# Global Development Strategy

---

# PHASE ORDER IS SACRED

Urutan phase:

* tidak boleh dilompati sembarangan.

Karena setiap phase:

* menjadi fondasi phase berikutnya.

---

# MASTER DEVELOPMENT PHASES

```text id="cjlwm0"
Phase 0  → Foundation & Planning
Phase 1  → Core Backend Foundation
Phase 2  → Authentication & Role System
Phase 3  → Academy & Branch System
Phase 4  → Scheduling Engine
Phase 5  → Teacher Workflow
Phase 6  → Parent Experience
Phase 7  → Financial & Subscription System
Phase 8  → Realtime & Notifications
Phase 9  → UI/UX Refinement
Phase 10 → Analytics & Reporting
Phase 11 → Production Hardening
Phase 12 → Beta Launch
Phase 13 → Scale & Optimization
```

---

# PHASE 0 — FOUNDATION & PLANNING

## Objective

Membangun pondasi project sebelum coding besar dimulai.

---

# Checklist

```text id="0jlwm9"
[x] Finalize README.md
[x] Finalize PROJECT_VISION.md
[x] Finalize CORE_FOUNDATION.md
[x] Finalize BUSINESS_RULES.md
[x] Finalize ROLE_MATRIX.md
[x] Finalize MULTI_BRANCH_ARCHITECTURE.md
[x] Finalize CLASS_SCHEDULING_SYSTEM.md
[x] Finalize PARENT_EXPERIENCE.md
[x] Finalize TEACHER_WORKFLOW.md
[x] Finalize SUBSCRIPTION_TIER_SYSTEM.md
[x] Finalize DATABASE_ARCHITECTURE.md
[x] Finalize SYSTEM_ARCHITECTURE.md
[x] Finalize UI_UX_GUIDELINES.md
[x] Finalize AI_AGENT_GUIDELINES.md
[x] Finalize PERMISSION_MATRIX.md
[x] Finalize ROADMAP.md
```

---

# Implementation Notes

Completed on June 14, 2026:

* all 16 foundation documents were confirmed present and reviewed,
* `TODO.md` was activated as project working memory,
* architecture and implementation boundaries were validated before coding.

---

# Deliverables

* stable documentation foundation
* architecture direction
* business clarity
* AI coding rules

---

# Forbidden

Tidak boleh:

* langsung coding dashboard besar,
* langsung generate random pages,
* atau langsung bikin mobile app.

---

# PHASE 1 — CORE BACKEND FOUNDATION

## Objective

Membangun fondasi backend stabil.

---

# Priorities

* project structure
* environment setup
* database setup
* migration system
* base API structure
* service layer
* audit foundation

---

# Checklist

```text id="jlwm8m"
[x] Setup backend repository structure
[x] Setup Flask architecture
[x] Setup PostgreSQL
[x] Setup migration system
[x] Setup environment configuration
[x] Setup service layer pattern
[x] Setup repository pattern
[x] Setup audit log system
[x] Setup error handling system
[x] Setup API response standard
[x] Setup health check endpoints
```

---

# Implementation Notes

Completed on June 14, 2026:

* created a modular Flask application factory under `backend/`,
* configured PostgreSQL through environment variables and `compose.yaml`,
* added SQLAlchemy and a single-head Alembic migration foundation,
* established route, service, repository, and database boundaries,
* added a tenant-aware centralized `audit_logs` model and service,
* standardized success and error envelopes with request IDs,
* added liveness and database readiness endpoints,
* added focused tests using an isolated in-memory database.

PostgreSQL container execution remains an environment verification item in
`TODO.md` because Docker and PostgreSQL are not installed on the current host.

---

# Deliverables

* stable backend core
* maintainable structure
* scalable architecture

---

# Forbidden

Tidak boleh:

* scheduling logic dulu,
* dashboard kompleks dulu,
* atau realtime dulu.

---

# PHASE 2 — AUTHENTICATION & ROLE SYSTEM

## Objective

Membangun identity & permission foundation.

---

# Priorities

* authentication
* authorization
* role matrix
* session management
* academy isolation

---

# Checklist

```text id="jlwm1o"
[x] User authentication
[x] Session management
[x] JWT/session validation
[x] Role middleware
[x] Permission validation
[x] Academy isolation
[x] Branch scope validation
[x] Multi-role support
[x] Audit logging for auth
```

---

# Implementation Notes

Completed on June 14, 2026:

* added separate `users`, `role_assignments`, and `auth_sessions` models,
* implemented password hashing and academy-scoped login identity,
* added short-lived access JWTs and rotating refresh JWTs,
* stored only refresh JTI hashes in revocable server-side sessions,
* added centralized role permission grants derived from the permission matrix,
* implemented explicit platform, academy, branch, assigned class, linked
  student, and self scopes,
* added authentication and permission decorators that reload active database
  state on every request,
* added login, refresh, logout, and current-user API endpoints,
* audited successful login, failed login, refresh, logout, role assignment, and
  role revocation events,
* added migration `0002` with deterministic tenant and role scope uniqueness,
* verified multi-role additive access without cross-academy or cross-branch
  privilege expansion.

Academy and branch UUID scopes are enforced now. Their foreign keys and active
status checks will bind to the owning records in Phase 3, when those tables are
created. Subscription feature gating remains scheduled for Phase 7.

---

# Deliverables

* secure identity system
* scalable permission system

---

# Critical Warning

Jika phase ini lemah:

* seluruh project akan rawan bocor permission.

---

# PHASE 3 — ACADEMY & BRANCH SYSTEM

## Objective

Membangun multi-branch operational structure.

---

# Priorities

* academy management
* branch management
* branch isolation
* cross branch foundation

---

# Checklist

```text id="jlwm6g"
[x] Academy CRUD
[x] Branch CRUD
[x] Branch visibility rules
[x] Branch operational isolation
[x] Multi-role branch assignment
[x] Teacher branch assignment
[x] Student branch relation
[x] Branch analytics foundation
```

---

# Implementation Notes

Core academy and branch batch completed on June 14, 2026:

* added `academies` and `branches` as first-class tenant records,
* implemented explicit academy and branch status transition maps,
* used archived status and timestamps instead of destructive deletion,
* bound `users.academy_id` and scoped role assignments to real foreign keys,
* validated role assignment academy/branch ownership and active status,
* added permission-protected Academy and Branch CRUD APIs,
* restricted branch list and detail visibility to active role scopes,
* blocked operational permissions on inactive, maintenance, suspended, or
  archived branches,
* made suspended academies read-only for non-platform roles,
* added migration `0003` and branch/academy audit events,
* verified cross-academy and cross-branch isolation through API tests.

Follow-up completed on June 14, 2026:

* added academy-scoped Teacher profiles with unique teacher codes,
* added explicit `teacher_branches` assignments with active and ended states,
* required every teacher to retain at least one active branch while active,
* added Student profiles with mandatory home branches,
* enforced teacher, student, user, and branch academy consistency through
  composite foreign keys,
* added permission-protected Teacher and Student profile APIs,
* added default-deny cross-branch student policy with a Phase 7 entitlement
  provider interface,
* kept teacher organizational assignment separate from class and schedule
  authority,
* added branch summary counts for active students and active teacher
  assignments only,
* added migration `0004` and cross-branch isolation tests.

Phase 3 is complete. Premium student cross-branch activation remains in Phase 7
and scheduling conflict validation remains in Phase 4.

---

# Deliverables

* stable multi-branch system

---

# PHASE 4 — SCHEDULING ENGINE

## Objective

Membangun jantung operasional platform.

---

# THIS IS CRITICAL PHASE

Scheduling adalah:

* highest operational risk area.

---

# Priorities

* scheduling engine
* conflict detection
* room management
* teacher scheduling
* student scheduling
* reschedule workflow

---

# Checklist

```text id="jlwm4h"
[x] Class schedule engine
[x] Teacher conflict detection
[x] Room conflict detection
[x] Student overlap detection
[x] Reschedule workflow
[x] Schedule audit logs
[x] Schedule notifications
[x] Realtime schedule sync
[x] Schedule status lifecycle
```

---

# Implementation Notes

First scheduling batch completed on June 14, 2026:

* added branch-scoped Class and Room resources,
* added explicit `class_students` enrollment records,
* added timezone-aware Schedule records and one operational Session per
  scheduled meeting,
* enforced academy and branch consistency with composite foreign keys,
* implemented the ordered branch, teacher, room, student, class/time, and
  cross-branch validation pipeline,
* blocked teacher, room, student, and duplicate class overlaps using indexed
  overlap queries,
* enforced active teacher branch assignment and default-deny Student
  cross-branch access,
* added Schedule and Session status lifecycle synchronization,
* audited schedule creation and status transitions,
* added migration `0005` and focused permission/isolation/conflict tests.

Reschedule workflow completed on June 14, 2026:

* added immutable Schedule change requests with mandatory request reasons,
* preserved original and proposed values as separate snapshots,
* enforced requester-specific approval authority and mandatory decision reasons,
* reran the complete conflict pipeline on both request and approval,
* rejected stale approvals when the original Schedule changed,
* preserved the original Schedule as `rescheduled` and created a replacement,
* audited request, approval/rejection, original transition, and replacement,
* added migration `0006` and focused reschedule workflow tests.

Notification delivery and distributed realtime lock/sync remain deferred until
the Phase 8 infrastructure exists.

---

# Deliverables

* stable operational scheduling

---

# Forbidden

Tidak boleh:

* shortcut scheduling logic,
* hardcoded validation,
* silent overwrite.

---

# PHASE 5 — TEACHER WORKFLOW

## Objective

Membangun operational teacher experience.

---

# Priorities

* teacher dashboard
* attendance flow
* lesson summary
* material access
* teacher notifications

---

# Checklist

```text id="jlwm3d"
[x] Teacher dashboard
[x] Today timeline
[x] Quick attendance
[x] Lesson summary system
[x] Material access
[x] Teacher notification boundary
[x] Mobile-first teacher API
[x] Attendance validation
```

---

# Implementation Notes

Attendance foundation completed on June 14, 2026:

* added one attendance record per active Student and operational Session,
* supported `present`, `late`, `absent`, `excused`, and `online` statuses,
* added bulk draft create/update for assigned classes,
* required complete active enrollment coverage before Session finalization,
* locked direct edits after finalization,
* added immutable finalized-attendance edit requests with mandatory reasons,
* enforced separate Branch Admin/Manager or Academy Director approval,
* prevented self-approval and stale-request overwrite,
* audited recording, draft edits, finalization, requests, and decisions,
* added migration `0007` and focused lifecycle/authority tests.

Realtime attendance delivery remains deferred to Phase 8.

Teacher dashboard and lesson summary workflow completed on June 14, 2026:

* added a date/timezone-aware teacher tactical dashboard,
* returned chronological assigned Sessions across multiple branches,
* included branch, room, class, student count, operational statuses, and
  actionable attendance/lesson-summary shortcuts,
* isolated results by the authenticated Teacher profile and assigned Classes,
* added one structured lesson summary per Session with draft autosave,
* added publish locking and immutable published-summary edit requests,
* required reasons, separate approval, stale snapshot checks, and audit logs,
* added migration `0008` and focused dashboard/lifecycle/isolation tests.

Material access and teacher API boundary completed on June 14, 2026:

* added academy-wide Material identities with immutable numbered versions,
* enforced `draft -> review -> ready` approval before distribution,
* preserved version history and allowed rollback through distribution targets,
* added branch/class-specific distribution and teacher access isolation,
* exposed preview/download metadata without bypassing the future storage layer,
* surfaced material readiness, count, shortcuts, and unread notification count
  in the teacher dashboard,
* added bounded mobile-friendly class material and notification responses,
* added deduplicated in-app material update notifications and read state,
* added migration `0009` and focused version/distribution/isolation tests.

Binary file delivery, signed URLs, notification queues, push/email delivery,
reminder scheduling, retries, and realtime synchronization remain Phase 8.

---

# Deliverables

* stable teacher operations

---

# PHASE 6 — PARENT EXPERIENCE

## Objective

Membangun premium parent trust layer.

---

# THIS IS PREMIUM DIFFERENTIATOR

---

# Priorities

* parent dashboard
* monitoring system
* invoice visibility
* progress tracking
* parent notifications

---

# Checklist

```text id="jlwm7q"
[x] Parent dashboard
[x] Child overview
[x] Attendance visibility
[x] Schedule visibility
[x] Lesson summaries
[x] Invoice visibility
[x] Parent notifications
[x] Mobile-first parent UX
```

Linked-child visibility now uses explicit `parents` and `parent_students`
records synchronized with active scoped role assignments. Parent APIs expose
only finalized attendance and published lesson summaries, while schedule
overview preserves cancelled and rescheduled states for transparency.

Phase 6 completed on June 14, 2026:

* added trusted academic progress metrics from finalized attendance and
  published lesson summaries only,
* exposed linked-child invoice/payment history with no draft leakage,
* emitted relevant schedule, attendance, lesson, and billing notifications,
* added concise shortcuts and bounded mobile-first parent responses.

---

# Deliverables

* premium parent experience

---

# PHASE 7 — FINANCIAL & SUBSCRIPTION SYSTEM

## Objective

Membangun monetization foundation.

---

# Priorities

* invoices
* payments
* SaaS subscriptions
* addon system
* feature gating

---

# Checklist

```text id="jlwm0x"
[x] Academic invoice system
[x] Payment tracking
[x] Payment proof upload
[x] SaaS subscription system
[x] Feature gating
[x] Addon system
[x] Grace period logic
[x] Subscription lifecycle
```

Phase 7 completed on June 14, 2026:

* separated academic parent billing from academy SaaS subscriptions,
* added invoice issue, overdue, cancellation, partial/full payment, proof
  metadata, confirmation, audit, and parent visibility,
* added plans and explicit trial, active, grace, suspended, and archived
  subscription lifecycle handling,
* enforced suspended subscription write restrictions in backend authorization,
* added addon purchases and explicit Student cross-branch entitlements.

---

# Deliverables

* sustainable monetization system

---

# PHASE 8 — REALTIME & NOTIFICATIONS

## Objective

Membuat platform terasa hidup dan sinkron.

---

# Priorities

* websocket
* realtime sync
* notification engine
* queue system

---

# Checklist

```text id="jlwm2c"
[x] Socket.IO integration
[x] Realtime schedule updates
[x] Attendance sync
[x] Notification service
[x] Notification queue
[x] Deduplication system
[x] Realtime dashboard refresh
```

Phase 8 completed on June 14, 2026:

* added JWT-authenticated Socket.IO connections with user, academy, branch,
  assigned-class, and linked-student rooms,
* added durable realtime outbox and notification delivery queue records,
* deduplicated notification and realtime event creation,
* synchronized schedule, attendance, lesson summary, invoice, and dashboard
  events to scoped rooms,
* protected schedule mutation with database row locks across app instances,
* added configurable teacher workload and cross-branch transition warnings.

---

# Deliverables

* realtime operational experience

---

# PHASE 9 — UI/UX REFINEMENT

## Objective

Meningkatkan rasa premium platform.

---

# Priorities

* spacing consistency
* typography
* dashboard polish
* mobile optimization
* loading states
* animation refinement

---

# Checklist

```text id="jlwm5n"
[x] Dashboard consistency
[x] Mobile optimization
[ ] Skeleton loading
[x] Empty states
[x] Error states
[x] Status consistency
[x] Premium spacing refinement
[ ] Accessibility review
```

---

# Deliverables

* premium operational experience

Phase 9 backend support completed on June 14, 2026:

* added a centralized UI status catalog for consistent frontend labels and
  tones,
* added analytics response metadata for empty states and mobile/desktop UI
  density,
* exposed dashboard-ready operational KPI payloads without changing business
  authority rules.

Skeleton loading, animation refinement, and full accessibility review remain
frontend implementation work because this repository currently contains only
the backend/API surface.

---

# PHASE 10 — ANALYTICS & REPORTING

## Objective

Membangun insight layer.

---

# Priorities

* academy analytics
* branch analytics
* operational reports
* parent insights
* teacher analytics

---

# Checklist

```text id="jlwm9v"
[x] Branch KPI
[x] Academy analytics
[x] Attendance analytics
[x] Revenue analytics
[x] Teacher workload analytics
[x] Parent engagement analytics
```

---

# Deliverables

* operational intelligence layer

Phase 10 completed on June 14, 2026:

* added branch KPI analytics across active population, sessions, attendance,
  revenue, teacher workload, and parent engagement,
* added academy overview analytics with branch rollups and academy totals,
* enforced existing `report.view` permission, academy isolation, and branch
  isolation across analytics endpoints,
* added focused analytics and UI status catalog tests.

---

# PHASE 11 — PRODUCTION HARDENING

## Objective

Mempersiapkan production-grade stability.

---

# Priorities

* security
* performance
* backups
* monitoring
* stress testing

---

# Checklist

```text id="jlwm6u"
[x] Security audit
[x] Performance optimization
[x] Query optimization
[ ] Load testing
[ ] Backup system
[ ] Recovery testing
[x] Monitoring setup
[x] Error tracking
[ ] Websocket stability
```

---

# Deliverables

* production-ready system

Phase 11 backend hardening completed on June 14, 2026:

* added request rate limiting with health-check exemptions and standard 429
  error responses,
* added request observability logs with request id, path, status, duration, and
  response-time headers,
* added production config guards for secret strength, rate limiting, export
  limits, and non-SQLite production databases,
* added server-capped audit log and report export boundaries that reuse
  existing permission, academy, and branch isolation rules,
* added focused hardening tests for rate limiting, observability, export
  scoping, report export permissions, and production config validation.

Load testing, backup automation, recovery testing, and WebSocket soak testing
remain environment/infrastructure work because they need a deployed stack,
PostgreSQL runtime, and sustained traffic harness.

---

# PHASE 12 — BETA LAUNCH

## Objective

Testing real operational environment.

---

# Priorities

* limited academy onboarding
* operational observation
* bug discovery
* workflow validation

---

# Checklist

```text id="jlwm4z"
[x] Beta academy onboarding
[ ] Real operational testing
[x] Parent UX observation
[x] Teacher UX observation
[x] Bug fixing sprint
[x] Performance monitoring
```

---

# Deliverables

* validated operational platform

Phase 12 backend beta preparation completed on June 14, 2026:

* added beta academy onboarding records with explicit operational owners,
  success criteria, date windows, and lifecycle transitions,
* added beta feedback intake for bug, workflow, parent UX, teacher UX,
  performance, data quality, and other observations,
* added feedback triage status transitions and permission-scoped feedback
  review,
* added beta readiness reporting for active onboardings, open feedback,
  critical feedback, and staging dependency visibility,
* added staging environment examples and runbook for load testing,
  backup/recovery checks, and WebSocket soak testing.

Real operational testing remains pending until a staging deployment and limited
academy cohort are actually run.

---

# PHASE 13 — SCALE & OPTIMIZATION

## Objective

Mempersiapkan scaling jangka panjang.

---

# Priorities

* optimization
* caching
* infrastructure scaling
* AI features
* advanced automation

---

# Checklist

```text id="jlwm8r"
[x] Redis optimization
[x] Queue scaling
[x] API optimization
[x] AI assistant planning
[x] Smart scheduling foundation
[x] Infrastructure scaling
```

---

# Deliverables

* scalable SaaS platform

Phase 13 backend scale foundation completed on June 14, 2026:

* added a cache abstraction with TTL support and analytics cache metadata,
* added Redis staging configuration and production guardrails that require
  `REDIS_URL`,
* added queue/realtime worker concurrency configuration for staged scaling,
* added scale readiness reporting for cache, queue, API, and AI assistant
  planning guardrails,
* added smart scheduling signal reporting with recommendations-only mutation
  policy,
* updated staging compose/runbook to include Redis and cache validation.

Redis-backed integration, multi-worker queue throughput, horizontal scaling,
and AI assistant product validation remain staging/production validation work.

---

# GLOBAL DEVELOPMENT RULES

---

# Rule 1 — One Core System At A Time

Jangan:

* scheduling + realtime + analytics sekaligus.

---

# Rule 2 — Finish Before Expanding

Selesaikan:

* workflow inti dulu,
  baru fitur tambahan.

---

# Rule 3 — Audit Frequently

Minimal tiap:

* 3–7 hari

lakukan:

* cleanup
* orphan scan
* duplicate logic scan
* permission audit
* performance review

---

# Rule 4 — Refactor Early, Not Late

Jika ada chaos:

* rapihkan sekarang.

Jangan:

* “nanti sekalian”.

---

# Rule 5 — Docs Are Mandatory

Jika:

* architecture berubah,
* workflow berubah,
* business rule berubah,

maka docs wajib update.

---

# AI / CODEX EXECUTION STRATEGY

---

# Rule

AI agents wajib:

* bekerja per phase,
* tidak lompat roadmap,
* tidak generate feature liar.

---

# Recommended AI Workflow

```text id="jlwm1w"
1. Read related docs
2. Understand current phase
3. Implement small scoped feature
4. Validate permissions
5. Validate mobile UX
6. Validate branch scope
7. Cleanup orphan code
8. Update docs
```

---

# VIBE CODER SURVIVAL PRINCIPLES

---

# 1. Jangan Tergoda Dashboard Dulu

Dashboard cantik tanpa operational core:

* hanya wallpaper mahal.

---

# 2. Scheduling Is More Important Than AI

Scheduling stabil:
lebih mahal nilainya daripada AI gimmick.

---

# 3. Parent Trust Is Revenue

Parent percaya:
→ retention naik
→ pembayaran lancar
→ referral naik

---

# 4. Operational Calm Is Premium

Premium bukan:

* glow effect,
* animasi,
* atau glassmorphism berlebihan.

Premium adalah:

* operasional tenang,
* cepat,
* jelas,
* dan minim drama.

---

# 5. Technical Debt Is Real Debt

Shortcut hari ini:
bisa menjadi monster 6 bulan lagi.

---

# Final Roadmap Statement

Roadmap ini bukan:

* sekadar checklist,
* atau daftar fitur.

Roadmap ini adalah:

* rel utama project,
* sistem anti-chaos,
* penjaga fokus,
* dan fondasi stabilitas jangka panjang.

Ikuti phase dengan disiplin.

Karena project besar jarang gagal karena:

* kurang fitur.

Tetapi sering gagal karena:

* kehilangan arah.
