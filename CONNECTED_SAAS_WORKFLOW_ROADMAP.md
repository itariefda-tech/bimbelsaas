# Connected SaaS Workflow Roadmap

## Purpose

Roadmap ini khusus untuk menyelesaikan alur SaaS yang nyambung dari awal:

`register tenant -> setup bimbel -> setup role internal -> register guru/parent/murid -> jadwal pertama -> operasional harian -> approval -> reporting -> billing`

Tujuannya bukan menambah dashboard baru secara acak, tetapi membuat semua dashboard role punya konteks data dan alur kerja yang saling tersambung.

## Product Rule

Jangan mulai billing, tier, subscription, atau addon UI sebelum tenant, bimbel, role, guru, murid, parent, kelas, dan jadwal pertama bisa hidup sebagai satu alur end-to-end.

Billing tetap penting, tetapi menjadi fase akhir setelah operasional dasar benar-benar tersambung.

## Phase CW0 - Current Baseline

Status: completed baseline

Already available:

- Flask shell login/logout/dashboard.
- Seven role dashboards: Platform Owner, Academy Director, Branch Manager, Branch Admin, Teacher, Parent, Student.
- API foundation for academy, branch, identity, people, scheduling, attendance, parent experience, finance, subscription, realtime, analytics.
- Visual QA baseline through `npm run ui:quality`.
- Workflow baseline for Teacher, Parent, and Branch Admin dashboard panels.

Known gap:

- Dashboards are role-aware, but the user journey between them is not yet connected through UI forms.
- Tenant onboarding exists as backend capability, but not as a web workflow.

## Phase CW1 - Tenant Registration

Status: completed baseline

Objective:

Membuat tenant/academy pertama dari Platform Owner UI.

Primary role:

- Platform Owner

Workflow:

1. Platform Owner opens tenant onboarding.
2. Platform Owner creates academy.
3. Platform Owner defines academy identity: name, slug, timezone, currency.
4. System confirms tenant created.
5. New academy appears in Platform Owner tenant list.

Deliverables:

- Tenant registration form.
- Academy list for Platform Owner.
- Create academy success state.
- Duplicate slug error state.
- Invalid timezone/currency validation.
- Permission denied state for non-Platform Owner.
- Desktop/mobile screenshots in UI quality gate.

Acceptance criteria:

- [x] Tenant can be created from UI using existing `POST /api/v1/academies`.
- [x] Created tenant is visible in Platform Owner flow.
- [x] Non-Platform Owner cannot access tenant registration.
- [x] `npm run ui:quality` passes.
- [x] `python -m pytest -q` passes.

Implementation notes:

- `/tenants` now provides a Platform Owner-only tenant registration page.
- The form creates academy tenants through `AcademyService` so permission, validation, duplicate slug checks, and audit logging stay on the existing backend path.
- `backend/app/templates/tenants.html` renders the create form, tenant list, and next setup path.
- `scripts/ui_quality_gate.mjs` captures desktop/mobile tenant registration screenshots and creates a unique QA tenant from the UI.
- `backend/tests/test_web_security.py` covers tenant creation, duplicate slug handling, and non-Platform Owner denial.

## Phase CW2 - Initial Academy Setup

Status: completed baseline

Objective:

Membuat bimbel terasa siap dipakai setelah tenant dibuat.

Primary role:

- Platform Owner
- Academy Director

Workflow:

1. Configure academy profile.
2. Review timezone and currency.
3. Set logo or branding metadata if available.
4. Confirm academy operational readiness.

Deliverables:

- Academy profile/settings view.
- Edit academy name, slug, timezone, currency, logo URL.
- Read-only/suspended academy messaging.
- Empty/error/loading states.

Acceptance criteria:

- [x] Academy Director can view own academy settings.
- [x] Platform Owner can manage academy lifecycle.
- [x] Suspended/archived states are clear and non-chaotic.

Implementation notes:

- `/academies/<academy_id>/setup` now provides an academy settings page after tenant registration.
- Platform Owner and Academy Director can edit academy name, slug, timezone, currency, and logo URL through `AcademyService`.
- Platform Owner can manage academy lifecycle status from the setup page.
- Suspended and archived academies show explicit read-only messaging, and non-platform roles cannot mutate suspended academy setup.
- `backend/tests/test_web_security.py` covers academy setup update, read-only suspended state, and permission behavior.

## Phase CW3 - Branch Setup

Status: completed baseline

Objective:

Membuat minimal satu cabang agar role branch-level punya scope nyata.

Primary role:

- Academy Director
- Branch Manager

Workflow:

1. Create branch.
2. Add branch name, code, address, timezone.
3. Set operational status.
4. Show branch in Director and Branch Manager dashboard context.

Deliverables:

- Branch creation form.
- Branch list/detail view.
- Branch edit/archive action.
- Branch operational status state.
- Permission denied for cross-branch access.

Acceptance criteria:

- [x] Academy Director can create and manage own branches.
- [x] Branch Manager sees assigned branch only.
- [x] Branch Admin cannot edit branch profile.

Implementation notes:

- The academy setup page now includes branch creation, branch list/detail, branch edit, operational status update, and archive actions.
- Branch creation and updates use `BranchService`, preserving validation, permission checks, status transitions, duplicate code handling, and audit logging.
- Branch Manager visibility remains branch-scoped through `BranchService.list_visible`.
- Branch Admin sees setup context but cannot create, edit, or archive branch profile data.
- `npm run ui:quality` includes desktop/mobile academy setup screenshots and mutates the setup flow by updating academy metadata and creating a branch.

## Phase CW4 - Internal Role Setup

Status: completed baseline

Objective:

Menghubungkan owner, director, manager, admin/asisten ke tenant dan branch.

Primary role:

- Platform Owner
- Academy Director

Role mapping:

- SaaS global owner: Platform Owner.
- Bimbel owner/head: Academy Director.
- Branch controller: Branch Manager.
- Assistant/admin operasional: Branch Admin.

Workflow:

1. Create or invite internal user.
2. Assign role.
3. Assign academy or branch scope.
4. Show role-specific dashboard access.

Deliverables:

- Internal user creation form.
- Role assignment form.
- Role list by academy/branch.
- Revoke role action.
- Multi-role visibility state.

Acceptance criteria:

- [x] User cannot receive invalid cross-academy or cross-branch assignment.
- [x] Dashboard navigation shows only active roles.
- [x] Role assignment is auditable.

Implementation notes:

- `/academies/<academy_id>/team` now provides internal team setup after academy and branch setup.
- Platform Owner and Academy Director can create academy-scoped internal users with an initial internal role.
- Existing internal users can receive additional Academy Director, Branch Manager, or Branch Admin assignments.
- Branch Manager and Branch Admin roles require branch scope; Academy Director remains academy-scoped.
- Active internal assignments are listed with role and academy/branch scope.
- Revoke role action uses `IdentityService.revoke_role`, preserving audit logging and active-role dashboard behavior.
- Invalid scope, duplicate role assignment, and permission denied states preserve entered form data.
- Branch Admin cannot manage internal roles.
- `backend/tests/test_web_security.py` covers create, assign, revoke, invalid scope, Academy Director access, and Branch Admin denial.
- `npm run ui:quality` captures desktop/mobile internal team screenshots and creates an internal branch admin from the UI.

## Phase CW5 - Teacher Registration

Status: completed baseline

Objective:

Mendaftarkan guru dan menghubungkannya ke branch.

Primary role:

- Academy Director
- Branch Manager
- Branch Admin

Workflow:

1. Create teacher user/profile.
2. Assign teacher to one or more branches.
3. Set active/employment status.
4. Teacher dashboard becomes meaningful.

Deliverables:

- Teacher creation form.
- Teacher branch assignment UI.
- Teacher list/detail.
- Active/ended assignment state.

Acceptance criteria:

- [x] Active teacher has at least one active branch assignment.
- [x] Teacher cannot see unrelated branch/class data.

Implementation notes:

- `/academies/<academy_id>/teachers` now provides the connected Teacher Registration page after internal role setup.
- Academy Director, Branch Manager, and Branch Admin can create teacher profiles within their permitted branch scope.
- Teacher creation can also create and link a login user, while class-scoped Teacher role assignment remains deferred until class setup creates a real teaching scope.
- Teacher detail shows profile fields, visible branch assignments, and active/ended assignment state.
- Ending an assignment uses `TeacherService.remove_branch`, preserving the rule that a teacher must keep at least one active branch assignment.
- Invalid cross-branch creation or assignment attempts are denied through existing permission checks.
- `backend/tests/test_web_security.py` covers teacher user/profile creation, branch assignment ending, branch-scoped list visibility, and cross-branch denial.
- `npm run ui:quality` captures desktop/mobile teacher registration screenshots and creates a teacher from the UI.

## Phase CW6 - Class And Room Setup

Status: completed baseline

Objective:

Membuat resource akademik dasar sebelum murid dijadwalkan.

Primary role:

- Branch Admin
- Branch Manager

Workflow:

1. Create room.
2. Create class.
3. Assign teacher.
4. Prepare class for enrollment and scheduling.

Deliverables:

- Room create/list/edit UI.
- Class create/list/edit UI.
- Teacher assignment selector.
- Capacity/status metadata if available.

Acceptance criteria:

- [x] Branch-scoped resources stay isolated.
- [x] Conflict-prone data is validated before schedule creation.

Implementation notes:

- `/academies/<academy_id>/classes` now provides the connected Class And Room Setup page after teacher registration.
- Academy Director, Branch Manager, and Branch Admin can create rooms and classes within their permitted branch scope.
- Room creation uses `RoomService`, preserving branch active-state validation, duplicate room code checks, audit logging, and `CLASS_MANAGE` permission behavior.
- Class creation uses `ClassService`, preserving branch active-state validation, duplicate class code checks, capacity metadata, audit logging, and `CLASS_MANAGE` permission behavior.
- Branch-scoped users only see rooms and classes from visible branches, and cross-branch create attempts are denied by existing authorization checks.
- Teacher assignment to class remains deferred until class-scoped role assignment and schedule creation are connected in the next workflow phases.
- `backend/tests/test_web_security.py` covers room/class creation, branch-scoped visibility, and cross-branch denial.
- `npm run ui:quality` captures desktop/mobile class and room setup screenshots and creates a room and class from the UI.

## Phase CW7 - Student Registration

Status: completed baseline

Objective:

Mendaftarkan murid dan menempatkannya ke branch/class.

Primary role:

- Branch Admin
- Academy Director

Workflow:

1. Create student profile.
2. Assign home branch.
3. Enroll student into class.
4. Student dashboard becomes meaningful.

Deliverables:

- Student create form.
- Student list/detail.
- Class enrollment UI.
- Home branch state.

Acceptance criteria:

- [x] Student belongs to one academy and home branch.
- [x] Student dashboard shows own schedule/material/progress once schedule exists.

Implementation notes:

- `/academies/<academy_id>/students` now provides the connected Student Registration page after class and room setup.
- Academy Director, Branch Manager, and Branch Admin can create student profiles within their permitted branch scope.
- Student creation can also create and link a login user while preserving existing `StudentService` validation, duplicate code checks, active branch checks, permission checks, and audit logging.
- Student detail shows profile fields, home branch state, optional login linkage, and active class enrollment state.
- Class enrollment uses `ClassService.enroll_student`, preserving capacity checks, active class validation, branch access rules, duplicate enrollment protection, and audit logging.
- Branch-scoped users only see students, classes, and enrollments from visible branches, and cross-branch create attempts are denied by existing authorization checks.
- `backend/tests/test_web_security.py` covers student user/profile creation, class enrollment, branch-scoped list visibility, and cross-branch denial.
- `npm run ui:quality` captures desktop/mobile student registration screenshots and creates a student plus class enrollment from the UI.

## Phase CW8 - Parent Registration And Child Link

Status: completed baseline

Objective:

Mendaftarkan parent dan menghubungkannya ke student.

Primary role:

- Branch Admin
- Academy Director

Workflow:

1. Create parent user/profile.
2. Link parent to student.
3. Parent sees child overview only.
4. Parent dashboard becomes meaningful.

Deliverables:

- Parent create form.
- Parent-student link UI.
- Multi-child support baseline.
- Link revoke state.

Acceptance criteria:

- [x] Parent sees linked children only.
- [x] Revoked links remove visibility.
- [x] Parent cannot access other student data.

Implementation notes:

- `/academies/<academy_id>/parents` now provides the connected Parent Registration And Child Link page after student registration.
- Academy Director, Branch Manager, and Branch Admin can create parent login users and link them to visible students within permitted branch scope.
- Parent creation uses `IdentityService.create_user` and `IdentityService.assign_role` with `Role.PARENT` and `ScopeType.LINKED_STUDENT`, preserving existing parent profile activation, `ParentStudent` link creation, scope validation, audit logging, and parent dashboard permissions.
- Parent detail shows parent login identity, relationship metadata, active/inactive child links, and a multi-child link form.
- Link revoke uses `IdentityService.revoke_role`, preserving role revocation audit logging and setting `ParentStudent.relationship_status` inactive.
- Branch-scoped users only see parents linked to visible students, and cross-branch parent creation/link attempts are denied by existing authorization checks.
- `backend/tests/test_web_security.py` covers parent user/profile creation, multi-child link, link revoke, branch-scoped list visibility, cross-branch denial, and parent API denial for revoked/unlinked students.
- `npm run ui:quality` captures desktop/mobile parent registration screenshots and creates a parent-child link from the UI.

## Phase CW9 - First Schedule Creation

Status: completed baseline

Objective:

Menghubungkan tenant, branch, teacher, class, room, student, parent, dan dashboard melalui jadwal pertama.

Primary role:

- Branch Admin
- Branch Manager

Workflow:

1. Create schedule.
2. Select class, teacher, room, date/time.
3. Run conflict validation.
4. Create operational sessions.
5. Schedule appears in Teacher, Student, Parent, Branch Admin, and Branch Manager dashboards.

Deliverables:

- Schedule creation form.
- Conflict result UI.
- Schedule list/detail.
- Dashboard visibility for created schedule.
- Reschedule entry point deferred to CW11 approval workflow.
- Cancelled/rescheduled state deferred to CW11 approval workflow.

Acceptance criteria:

- [x] Conflict checks are visible and understandable.
- [x] Created schedule updates role dashboards.
- [x] Parent and student see schedule after linking/enrollment.

Implementation notes:

- `/academies/<academy_id>/schedules` now provides the connected First Schedule Creation page after parent-child linking.
- Branch Admin, Branch Manager, and Academy Director can create schedules within permitted branch scope through `ScheduleService`.
- Schedule creation selects branch, class, teacher, room, date/time, timezone, and draft/scheduled status.
- Conflict validation uses `ScheduleValidationService`, preserving teacher overlap, room overlap/capacity, class overlap, student overlap, branch active-state, and cross-branch checks.
- Created schedules also create an operational `ClassSession` through the existing service path.
- Schedule list/detail shows class, teacher, room, status, session state, and time window.
- Teacher, Student, Parent, Branch Admin, Branch Manager, and Academy Director dashboards now expose a dashboard-ready upcoming schedule panel when visible schedules exist.
- Branch-scoped users only see and create schedules inside visible branch scope; cross-branch creation is denied by existing authorization checks.
- `backend/tests/test_web_security.py` covers schedule creation, detail, conflict result UI, branch scope denial, and dashboard visibility for Branch Manager, Teacher, Student, and Parent.
- `npm run ui:quality` captures desktop/mobile schedule creation screenshots and creates a schedule from the UI.

## Phase CW10 - Daily Operations

Status: completed baseline

Objective:

Membuat kegiatan harian berjalan setelah jadwal ada.

Primary roles:

- Teacher
- Branch Admin
- Parent
- Student

Workflow:

1. Teacher opens today timeline.
2. Teacher records attendance.
3. Teacher publishes lesson summary.
4. Materials and homework become visible.
5. Parent and student see updates.

Deliverables:

- Attendance UI.
- Lesson summary UI.
- Material visibility UI.
- Parent/student activity state.

Acceptance criteria:

- [x] Parent only sees finalized/published information.
- [x] Teacher cannot edit locked records without request flow.
- [x] Student view stays simple and learning-focused.

Implementation notes:

- `/academies/<academy_id>/sessions/<session_id>/daily-operations` now provides the connected daily operations page from a created schedule session.
- Teachers and Branch Admins can save attendance drafts, finalize attendance, save lesson summary drafts, and publish lesson summaries through the existing attendance and lesson summary services.
- Locked finalized attendance and published lesson summaries expose correction request forms instead of direct mutation.
- Parent and Student dashboards only show finalized attendance and published summaries; draft/private operational data stays internal.
- Branch Admin, Branch Manager, and Teacher dashboards now show daily operation completion state for upcoming sessions.
- `backend/tests/test_web_security.py` covers attendance save/finalize, summary draft/publish, locked correction entry points, and parent/student public visibility.
- `npm run ui:quality` captures desktop/mobile daily operations screenshots through the schedule flow.

## Phase CW11 - Approval Workflow

Status: completed baseline

Objective:

Membuat perubahan operasional tetap aman dan auditable.

Primary roles:

- Branch Manager
- Academy Director
- Teacher
- Branch Admin

Workflow:

1. Teacher/Admin requests reschedule or correction.
2. Branch Manager reviews.
3. Manager approves/rejects with reason.
4. Dashboards update with final state.

Deliverables:

- Reschedule approval queue.
- Attendance correction queue.
- Lesson summary correction queue.
- Approval/rejection detail.
- Stale request state.

Acceptance criteria:

- [x] Self-approval is blocked.
- [x] Decision reason is required.
- [x] Stale approval is blocked.
- [x] Branch Manager dashboard has desktop/mobile coverage.

Implementation notes:

- `/academies/<academy_id>/approvals` now provides a branch-scoped approval queue for reschedule requests, attendance corrections, and lesson summary corrections.
- Schedule detail now exposes reschedule requests, request history, and a direct link to daily operations.
- Approval decisions route through existing `RescheduleService`, `AttendanceService`, and `LessonSummaryService` methods so stale checks, permission checks, audit data, and status transitions stay centralized.
- Reschedule self-approval is explicitly blocked in `RescheduleService`.
- Decision forms require a reason and record approve/reject outcomes in the request history.
- `backend/tests/test_web_security.py` covers Branch Manager queue visibility and approve/reject decisions across reschedule, attendance, and lesson summary requests.
- `npm run ui:quality` includes desktop/mobile Branch Manager dashboard coverage.

## Phase CW12 - Notification Center

Status: completed baseline

Objective:

Membuat event penting terlihat tanpa membuat UI ramai.

Primary roles:

- All roles, role-scoped

Workflow:

1. Schedule change creates notification.
2. Attendance/lesson/invoice updates create relevant notification.
3. User sees unread and priority grouping.
4. User marks notifications read.

Deliverables:

- Notification inbox.
- Unread count.
- Priority grouping.
- Empty/error/loading states.

Acceptance criteria:

- [x] Notifications are role-scoped.
- [x] Parent notifications are not spammy.
- [x] Teacher/admin notifications stay operational.

Implementation notes:

- `/notifications` now provides a web notification inbox for the authenticated user, backed by the existing `NotificationService`.
- The topbar shows a Notification Center entry with unread count when the current user has unread notifications.
- Notification Center supports all/unread filtering, priority summary, empty state, payload context, and per-item mark-read.
- Mark-read uses CSRF protection and recipient-scoped lookup, so users cannot mark another recipient's notification.
- Existing event emitters continue to deduplicate notifications through `dedup_key`.
- `backend/tests/test_web_security.py` covers web inbox listing, unread badge, recipient-visible payload, and mark-read behavior.
- `npm run ui:quality` captures desktop/mobile notification center screenshots and overflow checks.

## Phase CW13 - Reporting And Oversight

Status: completed baseline

Objective:

Membuat data operasional menjadi insight setelah workflow berjalan.

Primary roles:

- Academy Director
- Branch Manager
- Platform Owner

Workflow:

1. Branch health rollup.
2. Attendance consistency.
3. Schedule stability.
4. Teacher workload.
5. Parent engagement.
6. Academy reporting.

Deliverables:

- Branch Manager report view.
- Academy Director reporting workflow.
- Platform Owner operational overview.
- Export entry points if needed.

Acceptance criteria:

- [x] Reports are scoped by academy/branch permission.
- [x] Director sees academy-wide rollup.
- [x] Manager sees assigned branch only.

Implementation notes:

- `/academies/<academy_id>/reports` now provides a Branch Manager report view for visible/reportable branches.
- Academy Director users now see academy-wide branch rollup totals and a branch comparison table from the same report page.
- The report uses `AnalyticsService.branch_kpi`, keeping Flask UI and analytics API metrics aligned.
- `AnalyticsService.academy_overview` aggregates attendance consistency, schedule stability, teacher workload, and parent engagement across academy branches.
- Branch report covers attendance consistency, schedule stability, teacher workload, and parent engagement.
- Schedule stability now includes cancelled/rescheduled sessions and a stability rate in branch KPI.
- Parent engagement now counts notifications sent to active parent links in the branch instead of relying on notification payload branch metadata.
- Dashboard headers expose an `Open reports` link when the active role has a reportable branch scope.
- `backend/tests/test_web_security.py` covers Branch Manager report access using schedule, finalized attendance, published summary, and parent notification data.
- `backend/tests/test_web_security.py` covers Academy Director report access, academy-wide rollup, branch comparison, and parent engagement counts across branches.
- `backend/tests/test_analytics_api.py` continues to validate analytics API behavior.
- `npm run ui:quality` captures desktop/mobile Branch Manager and Academy Director report screenshots.

## Phase CW14 - SaaS Billing, Tier, Subscription, Addon

Status: future

Objective:

Menambahkan monetization setelah operasional dasar tersambung.

Primary roles:

- Platform Owner
- Academy Director

Workflow:

1. Trial starts after tenant onboarding.
2. Plan selected or assigned.
3. Subscription status shown.
4. Grace/suspended state displayed.
5. Addons and feature gating become visible.

Deliverables:

- Plan management view.
- Academy subscription detail.
- Trial/grace/suspended banners.
- Addon purchase/activation UI.
- Feature-gated empty/denied states.

Acceptance criteria:

- Billing is transparent and not confusing.
- Suspended mode is readable but blocks restricted operations.
- Feature gating is backend-validated and visible in UI.

## Recommended Immediate Sprint

Continue with **Phase CW14 - SaaS Billing, Tier, Subscription, Addon**.

Tenant, academy, branch, internal roles, teachers, rooms, classes, students, parent-child links, first schedule, daily operations, approval workflow, notification center, and scoped reporting now have a connected Flask UI path. The next step is making subscription state visible without disturbing the operational workflow.

Initial implementation target:

- Trial/grace/suspended subscription state on academy surfaces.
- Plan detail and addon placeholders from existing subscription tier rules.
- Backend-validated feature gating surfaced in the UI.
- Billing access scoped to Platform Owner and Academy Director.
- Platform Owner operational overview remains deferred until billing state is readable.

## Definition Of Connected Done

The connected SaaS workflow is considered usable when:

- A tenant can be created from UI.
- A branch can be created under that tenant.
- Internal roles can be assigned.
- Teacher, student, and parent records can be created and linked.
- First class and schedule can be created.
- Daily attendance and lesson summary can be completed from the schedule session.
- Operational corrections and reschedule requests can be approved or rejected with a reason.
- Role-scoped notifications can be viewed and marked read.
- Branch Manager and Academy Director can view scoped operational reports.
- Teacher, parent, student, admin, manager, director, and owner dashboards all show data created through the same flow.
- Billing/subscription UI is added only after the operational chain is alive.
