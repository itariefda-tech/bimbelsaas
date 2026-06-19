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

Status: future

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

- Active teacher has at least one active branch assignment.
- Teacher cannot see unrelated branch/class data.

## Phase CW6 - Class And Room Setup

Status: future

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

- Branch-scoped resources stay isolated.
- Conflict-prone data is validated before schedule creation.

## Phase CW7 - Student Registration

Status: future

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

- Student belongs to one academy and home branch.
- Student dashboard shows own schedule/material/progress once schedule exists.

## Phase CW8 - Parent Registration And Child Link

Status: future

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

- Parent sees linked children only.
- Revoked links remove visibility.
- Parent cannot access other student data.

## Phase CW9 - First Schedule Creation

Status: future

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
- Reschedule entry point.
- Cancelled/rescheduled state.

Acceptance criteria:

- Conflict checks are visible and understandable.
- Created schedule updates role dashboards.
- Parent and student see schedule after linking/enrollment.

## Phase CW10 - Daily Operations

Status: future

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

- Parent only sees finalized/published information.
- Teacher cannot edit locked records without request flow.
- Student view stays simple and learning-focused.

## Phase CW11 - Approval Workflow

Status: future

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

- Self-approval is blocked.
- Decision reason is required.
- Stale approval is blocked.
- Branch Manager dashboard has desktop/mobile coverage.

## Phase CW12 - Notification Center

Status: future

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

- Notifications are role-scoped.
- Parent notifications are not spammy.
- Teacher/admin notifications stay operational.

## Phase CW13 - Reporting And Oversight

Status: future

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

- Reports are scoped by academy/branch permission.
- Director sees academy-wide rollup.
- Manager sees assigned branch only.

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

Continue with **Phase CW5 - Teacher Registration**.

Tenant, academy, branch, and internal roles now have a connected Flask UI path. The next step is creating teacher profiles and linking them to branch scope so schedules can later select real teachers instead of seeded demo users.

Initial implementation target:

- Teacher user/profile creation form.
- Teacher list/detail view.
- Teacher branch assignment UI.
- Active/ended assignment state.
- Permission denied and invalid cross-branch assignment states.

## Definition Of Connected Done

The connected SaaS workflow is considered usable when:

- A tenant can be created from UI.
- A branch can be created under that tenant.
- Internal roles can be assigned.
- Teacher, student, and parent records can be created and linked.
- First class and schedule can be created.
- Teacher, parent, student, admin, manager, director, and owner dashboards all show data created through the same flow.
- Billing/subscription UI is added only after the operational chain is alive.
