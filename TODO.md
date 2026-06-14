# TODO.md

## Current Phase

Phase 6 - Parent Experience

## Current Task

Continue Phase 6 with academic progress, invoice visibility, parent
notifications, and a final mobile-first parent response review.

## Completed In This Session

- [x] Confirm all 16 foundation documents are present.
- [x] Read and review all foundation documents.
- [x] Confirm `ROADMAP.md` is present.
- [x] Audit the repository and confirm it currently contains documentation only.
- [x] Complete and document Phase 0.
- [x] Scaffold the modular Flask backend.
- [x] Add environment and PostgreSQL development configuration.
- [x] Add SQLAlchemy models and Alembic migration support.
- [x] Add service and repository layer foundations.
- [x] Add tenant-aware audit logging.
- [x] Add standardized API responses and centralized error handling.
- [x] Add liveness and readiness health endpoints.
- [x] Add and run focused backend tests.
- [x] Update `README.md` and `ROADMAP.md`.
- [x] Add user identity, scoped role assignment, and auth session models.
- [x] Add short-lived access JWT and rotatable refresh JWT validation.
- [x] Add centralized permission grants and scope evaluation.
- [x] Add authentication and authorization middleware/decorators.
- [x] Add login, refresh, logout, and current-user API endpoints.
- [x] Add authentication and session audit events.
- [x] Add migration `0002` for the Phase 2 schema.
- [x] Add focused tests for multi-role, academy isolation, branch isolation,
  token rotation, replay revocation, and logout revocation.
- [x] Add Academy and Branch lifecycle models with soft archive behavior.
- [x] Bind user and role scopes to academy and branch foreign keys.
- [x] Add permission-protected Academy and Branch CRUD APIs.
- [x] Add status-aware authorization for suspended academies and
  non-operational branches.
- [x] Add migration `0003`.
- [x] Add cross-academy and cross-branch isolation tests.
- [x] Add Teacher profiles and explicit multi-branch assignments.
- [x] Add Student profiles with mandatory home branches.
- [x] Add default-deny Student cross-branch policy.
- [x] Add Teacher and Student profile APIs with scoped permissions.
- [x] Add branch summary counts for active teachers and students.
- [x] Add migration `0004` and profile isolation tests.
- [x] Re-read the Phase 4 scheduling, architecture, business rule, and
  permission documents.
- [x] Define the initial scheduling domain boundaries and validation order.
- [x] Add branch-scoped Class and Room models and APIs.
- [x] Add Class enrollment with capacity and cross-branch validation.
- [x] Add timezone-aware Schedule and operational Session models.
- [x] Implement ordered branch, teacher, room, student, class/time, and
  cross-branch conflict validation.
- [x] Add Schedule lifecycle synchronization and audit logs.
- [x] Add migration `0005`.
- [x] Add Phase 4 conflict, permission, and branch-isolation tests.
- [x] Add immutable Schedule change requests with original/proposed snapshots.
- [x] Enforce mandatory request and decision reasons.
- [x] Enforce requester-specific reschedule approval authority.
- [x] Re-run the full conflict pipeline at request and approval time.
- [x] Preserve original Schedules and create linked replacements on approval.
- [x] Audit reschedule request, approval/rejection, and replacement events.
- [x] Add migration `0006` and focused reschedule workflow tests.
- [x] Re-read Phase 5 teacher, attendance, database, and permission rules.
- [x] Add per-Student, per-Session attendance records and bulk draft updates.
- [x] Add complete-roster validation and Session attendance finalization.
- [x] Lock direct edits after finalization.
- [x] Add immutable finalized-attendance edit requests with mandatory reasons.
- [x] Enforce separate approval authority and prevent self-approval.
- [x] Audit attendance recording, edits, finalization, and decisions.
- [x] Add migration `0007` and focused attendance lifecycle tests.
- [x] Add date/timezone-aware Teacher Dashboard and Today Timeline.
- [x] Query only Sessions owned by the authenticated Teacher profile.
- [x] Return chronological multi-branch context and operational shortcuts.
- [x] Add structured Lesson Summary draft and publish lifecycle.
- [x] Add immutable published-summary edit requests and approval boundaries.
- [x] Audit Lesson Summary creation, publication, requests, and corrections.
- [x] Add migration `0008` and dashboard/lifecycle/isolation tests.
- [x] Add academy-wide Material records with immutable numbered versions.
- [x] Enforce draft, review, ready, distribution, and archive boundaries.
- [x] Add branch/Class material distribution with strict teacher isolation.
- [x] Add preview/download metadata without storage delivery shortcuts.
- [x] Add material readiness and notification badges to Teacher Dashboard.
- [x] Add bounded mobile-friendly material and notification responses.
- [x] Add deduplicated in-app notification boundary and read state.
- [x] Add migration `0009` and material/version/distribution tests.

## Skipped / Deferred Items

- [ ] Run the PostgreSQL stack locally.
  - Reason: Docker and a local PostgreSQL service are not installed in the current environment.
  - Depends on: Docker Desktop or PostgreSQL runtime availability.
  - Target phase: Phase 1 verification.
- [ ] Activate student cross-branch access.
  - Reason: Cross-branch student access is a premium feature and must not be
    activated without subscription entitlement.
  - Depends on: Phase 7 addon and feature-gating models.
  - Target phase: Phase 7.
- [ ] Expand branch analytics beyond active teacher/student counts.
  - Reason: Attendance, scheduling, invoice, and revenue data do not exist yet.
  - Depends on: Phases 4-7 operational data.
  - Target phase: Phase 10.
- [ ] Enforce subscription-aware feature gating in authorization decisions.
  - Reason: Subscription lifecycle and addon models belong to Phase 7.
  - Depends on: Academy subscription and feature entitlement models.
  - Target phase: Phase 7.
- [ ] Realtime schedule lock validation and event synchronization.
  - Reason: Redis/Socket.IO locking and scoped realtime delivery belong to
    Phase 8; Phase 4 will expose an explicit no-op lock boundary only when the
    reschedule workflow requires it.
  - Depends on: Realtime infrastructure and distributed lock provider.
  - Target phase: Phase 8.
- [ ] Teacher transition-time and workload warnings.
  - Reason: Travel-time configuration and workload policy thresholds are not
    defined yet; overlap and branch collision remain hard blockers now.
  - Depends on: Academy scheduling policy configuration and Phase 5 workload
    workflow.
  - Target phase: Phase 5.

## Next Actions

- [x] Re-read Phase 3 in `ROADMAP.md` and the academy/branch architecture docs.
- [x] Add Academy and Branch models with status lifecycles and soft-delete
  behavior.
- [x] Bind users and role assignments to academy and branch foreign keys.
- [x] Add academy and branch repositories and services with mandatory scope
  filters.
- [x] Implement permission-protected Academy and Branch CRUD APIs.
- [x] Add branch visibility and operational isolation tests.
- [x] Add migration `0003` and verify the full migration chain.
- [x] Add Teacher profile and explicit `teacher_branches` assignments.
- [x] Add Student profile with mandatory home branch.
- [x] Define the non-premium branch relation boundary without implementing
  Phase 7 addon logic.
- [x] Add minimal branch dimension/count queries only where source data exists.
- [x] Re-read the Phase 4 scheduling and permission documents.
- [x] Implement Class, Room, Session, and Schedule lifecycle models.
- [x] Implement the ordered conflict validation pipeline.
- [x] Add permission-protected Class, Room, enrollment, and Schedule APIs.
- [x] Add migration `0005` and scheduling isolation/conflict tests.
- [x] Preserve teacher branch assignment and Student home/cross-branch policy
  as scheduling prerequisites.
- [x] Define immutable Schedule change records for reschedule requests.
- [x] Implement request and approval authority with mandatory reasons.
- [x] Re-run the full conflict pipeline against proposed reschedule values.
- [x] Preserve the original Schedule instead of silently overwriting it.
- [x] Re-read Phase 5, teacher workflow, attendance, and permission documents.
- [x] Define Attendance lifecycle and finalization/edit approval boundaries.
- [x] Add teacher-scoped dashboard and assigned Session queries.
- [x] Implement lesson summary lifecycle without Phase 8 delivery.
- [x] Implement versioned material records and class/branch distribution.
- [x] Add teacher-safe material preview/download metadata and readiness status.
- [x] Complete mobile-first teacher API response review.
- [x] Re-read Phase 6 parent, linked-child, and permission documents.
- [x] Add explicit parent profiles and multi-child relationship records.
- [x] Synchronize linked-student role assignment and relationship lifecycle.
- [x] Implement linked-child dashboard and overview visibility.
- [x] Expose finalized attendance history without draft leakage.
- [x] Expose published lesson summaries without draft leakage.
- [x] Add parent schedule overview including cancelled/rescheduled states.
- [x] Enforce linked-child and academy isolation across parent endpoints.
- [ ] Define academic progress metrics from trusted finalized records.
- [ ] Add invoice visibility after the Phase 7 financial foundation exists.
- [ ] Add parent notification events without Phase 8 delivery shortcuts.
- [ ] Complete the mobile-first parent API response review.

## Notes

- Backend is the source of truth for business rules, permissions, tenant scope,
  branch scope, and subscription validation.
- The required dependency flow is route -> service -> repository -> database.
- Operational entities must remain academy-aware and branch-aware.
- Phase 3 final test result: 41 passed with 88% application coverage.
- Phase 4 final test result: 54 passed.
- Phase 5 attendance foundation test result: 59 passed.
- Phase 5 dashboard and lesson summary result: 63 passed.
- Phase 5 final result: 66 passed.
- Phase 6 parent visibility foundation result: 69 passed.
- Migration graph has one valid head: `0010`.
- App metadata now includes `teachers`, `teacher_branches`, and `students`.
- Authentication must not use a rigid role column or checks such as
  `if role == admin`; permissions are additive and scope-bound.
- JWT role claims will not be authorization authority. Each authenticated
  request reloads the active user, session, and role assignments from the
  database so role changes and revocation take effect immediately.
- Auth scope foreign keys and active academy/branch validation are now active.
- Student non-home branch access remains blocked unless the future Phase 7
  entitlement provider returns an explicit grant.
- Teacher branch assignment is organizational only; class and schedule
  authority begins in Phase 4.
- Platform owner permissions follow the detailed matrix and do not inherit
  forbidden daily operational actions such as attendance creation or academic
  invoice creation.
- Teacher branch assignment grants organizational placement only. Class and
  schedule authority remains deferred to Phase 4.
- Student cross-branch policy is default-deny. Only the home branch is valid
  until a future Phase 7 entitlement provider explicitly grants another branch.
- Initial scheduling validation order is branch, teacher, room, student,
  class/time conflict, cross-branch entitlement, then future realtime lock.
- Structural time validation happens before the pipeline so invalid intervals
  never reach overlap queries.
- `schedules` stores the planned calendar slot; `class_sessions` stores the
  operational meeting state. The initial one-to-one relation avoids attendance
  or lesson-summary records without a real Session.
