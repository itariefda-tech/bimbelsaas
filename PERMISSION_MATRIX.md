# Premium Multi-Branch Academic Operations Platform

---

# Purpose

Dokumen ini mendefinisikan:

* permission detail,
* access control,
* visibility scope,
* action authority,
* approval rules,
* dan restriction rules.

Dokumen ini menjadi turunan teknis dari:

* `ROLE_MATRIX.md`
* `BUSINESS_RULES.md`
* `MULTI_BRANCH_ARCHITECTURE.md`

Semua authorization di backend, frontend, API, realtime event, dan AI-generated implementation wajib mengikuti dokumen ini.

---

# Core Permission Principles

---

# 1. Backend Is The Permission Authority

Frontend boleh menyembunyikan tombol dan menu.

Tetapi keputusan final tetap di backend.

---

# Rule

Setiap API wajib memvalidasi:

* user identity,
* active role,
* academy scope,
* branch scope,
* subscription status,
* dan permission action.

---

# Forbidden

Tidak boleh ada permission yang hanya divalidasi di frontend.

---

# 2. Least Privilege By Default

User hanya diberi akses sesuai kebutuhan kerja.

---

# Rule

Jika sebuah role tidak disebut eksplisit memiliki permission,
maka default-nya:

```text
DENY
```

---

# 3. Visibility Is Not Edit Permission

Boleh melihat data tidak berarti boleh mengubah data.

---

# Example

Parent:

* boleh melihat attendance anak,
* tidak boleh mengubah attendance.

Academy Director:

* boleh melihat seluruh laporan branch,
* tidak otomatis menjadi operator attendance.

---

# 4. Scope Is Mandatory

Setiap permission wajib memiliki scope.

---

# Main Scopes

```text
platform
academy
branch
assigned_class
linked_student
self
```

---

# Scope Meaning

| Scope          | Meaning                                        |
| -------------- | ---------------------------------------------- |
| platform       | seluruh platform SaaS                          |
| academy        | seluruh academy dan seluruh branch di dalamnya |
| branch         | hanya branch yang ditugaskan                   |
| assigned_class | hanya class yang ditugaskan                    |
| linked_student | hanya student yang terhubung                   |
| self           | hanya data milik sendiri                       |

---

# 5. Multi-Role Is Additive But Still Scoped

User dapat memiliki lebih dari satu role.

Permission user adalah gabungan permission role aktif,
tetapi tetap dibatasi oleh scope.

---

# Example

User memiliki:

* branch_manager untuk Branch Meruya
* teacher untuk Branch Puri

Maka user:

* dapat mengelola Branch Meruya sebagai manager,
* dapat mengajar class assigned di Branch Puri,
* tidak otomatis menjadi manager Branch Puri.

---

# Role List

Official roles:

```text
platform_owner
academy_director
branch_manager
branch_admin
teacher
student
parent
```

---

# Permission Levels

Permission menggunakan pola:

```text
view
create
edit
delete
approve
export
manage
```

---

# Global Permission Summary

| Module              | Platform Owner  | Academy Director | Branch Manager        | Branch Admin          | Teacher               | Parent                | Student               |
| ------------------- | --------------- | ---------------- | --------------------- | --------------------- | --------------------- | --------------------- | --------------------- |
| Platform Management | manage          | no               | no                    | no                    | no                    | no                    | no                    |
| Academy Settings    | view/manage     | manage           | no                    | no                    | no                    | no                    | no                    |
| Branch Management   | view/manage     | view/manage      | view limited          | no                    | no                    | no                    | no                    |
| User Management     | manage          | manage academy   | manage branch         | manage branch limited | no                    | no                    | no                    |
| Student Records     | view            | view academy     | view branch           | manage branch         | view assigned         | view linked           | view self             |
| Parent Records      | view            | view academy     | view branch           | manage branch         | view limited          | self                  | no                    |
| Teacher Records     | view            | view academy     | view branch           | view branch           | self                  | view assigned teacher | view assigned teacher |
| Class Management    | view            | view academy     | manage branch         | manage branch         | view assigned         | view linked child     | view enrolled         |
| Scheduling          | view            | view academy     | approve/manage branch | create/manage branch  | request/view assigned | view linked child     | view enrolled         |
| Attendance          | view            | view academy     | view/approve edit     | create/edit branch    | create assigned       | view linked child     | view self             |
| Lesson Summary      | view            | view academy     | view branch           | view branch           | create/edit assigned  | view linked child     | view self             |
| Materials           | view            | manage academy   | view branch           | request/use branch    | upload/use assigned   | view linked child     | view assigned         |
| Invoicing           | view platform   | view academy     | view branch           | manage branch         | no                    | view/pay linked       | no                    |
| Payments            | view platform   | view academy     | view branch           | confirm branch        | no                    | upload proof          | no                    |
| Subscription        | manage platform | view academy     | no                    | no                    | no                    | buy addon             | no                    |
| Communication       | view audit      | view academy     | manage branch         | manage branch         | communicate assigned  | communicate linked    | communicate enrolled  |
| Reports             | view platform   | view academy     | view branch           | view limited          | view own              | view linked child     | view self             |
| Audit Logs          | view platform   | view academy     | view branch           | view limited          | view own actions      | no                    | no                    |

---

# Detailed Permission Matrix

---

# 1. Platform Management

| Action                   | Platform Owner | Academy Director | Branch Manager | Branch Admin | Teacher | Parent | Student |
| ------------------------ | -------------- | ---------------- | -------------- | ------------ | ------- | ------ | ------- |
| View global platform KPI | YES            | NO               | NO             | NO           | NO      | NO     | NO      |
| Manage academy accounts  | YES            | NO               | NO             | NO           | NO      | NO     | NO      |
| Manage SaaS plans        | YES            | NO               | NO             | NO           | NO      | NO     | NO      |
| Suspend academy          | YES            | NO               | NO             | NO           | NO      | NO     | NO      |
| View system health       | YES            | NO               | NO             | NO           | NO      | NO     | NO      |

---

# 2. Academy Management

| Action                      | Platform Owner | Academy Director | Branch Manager | Branch Admin | Teacher | Parent  | Student |
| --------------------------- | -------------- | ---------------- | -------------- | ------------ | ------- | ------- | ------- |
| View academy profile        | YES            | YES              | LIMITED        | LIMITED      | LIMITED | LIMITED | LIMITED |
| Edit academy branding       | YES            | YES              | NO             | NO           | NO      | NO      | NO      |
| Edit academy settings       | YES            | YES              | NO             | NO           | NO      | NO      | NO      |
| View academy-wide reports   | YES            | YES              | NO             | NO           | NO      | NO      | NO      |
| Manage academy subscription | YES            | YES/LIMITED      | NO             | NO           | NO      | NO      | NO      |

---

# 3. Branch Management

| Action               | Platform Owner | Academy Director | Branch Manager | Branch Admin | Teacher     | Parent      | Student     |
| -------------------- | -------------- | ---------------- | -------------- | ------------ | ----------- | ----------- | ----------- |
| View all branches    | YES            | YES              | NO             | NO           | NO          | NO          | NO          |
| View assigned branch | YES            | YES              | YES            | YES          | YES/LIMITED | YES/LIMITED | YES/LIMITED |
| Create branch        | YES            | YES              | NO             | NO           | NO          | NO          | NO          |
| Edit branch profile  | YES            | YES              | YES/LIMITED    | NO           | NO          | NO          | NO          |
| Archive branch       | YES            | YES              | NO             | NO           | NO          | NO          | NO          |

---

# 4. User & Role Management

| Action                       | Platform Owner | Academy Director | Branch Manager | Branch Admin | Teacher | Parent | Student |
| ---------------------------- | -------------- | ---------------- | -------------- | ------------ | ------- | ------ | ------- |
| Create platform user         | YES            | NO               | NO             | NO           | NO      | NO     | NO      |
| Create academy user          | YES            | YES              | NO             | NO           | NO      | NO     | NO      |
| Create branch user           | YES            | YES              | YES            | YES/LIMITED  | NO      | NO     | NO      |
| Assign academy director role | YES            | YES/LIMITED      | NO             | NO           | NO      | NO     | NO      |
| Assign branch manager role   | YES            | YES              | NO             | NO           | NO      | NO     | NO      |
| Assign branch admin role     | YES            | YES              | YES/LIMITED    | NO           | NO      | NO     | NO      |
| Assign teacher role          | YES            | YES              | YES            | YES          | NO      | NO     | NO      |
| Assign parent/student role   | YES            | YES              | YES            | YES          | NO      | NO     | NO      |
| Remove role                  | YES            | YES              | YES/LIMITED    | NO           | NO      | NO     | NO      |

---

# 5. Student Records

| Action                           | Platform Owner | Academy Director | Branch Manager | Branch Admin | Teacher | Parent       | Student |
| -------------------------------- | -------------- | ---------------- | -------------- | ------------ | ------- | ------------ | ------- |
| View all students in platform    | YES            | NO               | NO             | NO           | NO      | NO           | NO      |
| View all students in academy     | YES            | YES              | NO             | NO           | NO      | NO           | NO      |
| View students in assigned branch | YES            | YES              | YES            | YES          | LIMITED | NO           | NO      |
| View assigned students           | YES            | YES              | YES            | YES          | YES     | NO           | NO      |
| View linked child record         | NO             | NO               | NO             | NO           | NO      | YES          | NO      |
| View own student profile         | NO             | NO               | NO             | NO           | NO      | NO           | YES     |
| Create student                   | YES            | YES              | YES            | YES          | NO      | REQUEST ONLY | NO      |
| Edit student profile             | YES            | YES              | YES            | YES          | NO      | LIMITED      | LIMITED |
| Archive student                  | YES            | YES              | YES            | YES          | NO      | NO           | NO      |

---

# 6. Parent Records

| Action                           | Platform Owner | Academy Director | Branch Manager | Branch Admin | Teacher | Parent        | Student |
| -------------------------------- | -------------- | ---------------- | -------------- | ------------ | ------- | ------------- | ------- |
| View parent records academy-wide | YES            | YES              | NO             | NO           | NO      | NO            | NO      |
| View parent records branch       | YES            | YES              | YES            | YES          | LIMITED | NO            | NO      |
| Create parent account            | YES            | YES              | YES            | YES          | NO      | SELF REGISTER | NO      |
| Link parent to student           | YES            | YES              | YES            | YES          | NO      | REQUEST ONLY  | NO      |
| Edit parent contact              | YES            | YES              | YES            | YES          | NO      | SELF          | NO      |
| Unlink parent from student       | YES            | YES              | YES            | YES          | NO      | REQUEST ONLY  | NO      |

---

# 7. Teacher Records

| Action                     | Platform Owner | Academy Director | Branch Manager | Branch Admin | Teacher      | Parent  | Student |
| -------------------------- | -------------- | ---------------- | -------------- | ------------ | ------------ | ------- | ------- |
| View teacher academy-wide  | YES            | YES              | NO             | NO           | NO           | NO      | NO      |
| View teacher branch        | YES            | YES              | YES            | YES          | LIMITED      | LIMITED | LIMITED |
| Create teacher             | YES            | YES              | YES            | YES          | NO           | NO      | NO      |
| Edit teacher profile       | YES            | YES              | YES            | YES          | SELF LIMITED | NO      | NO      |
| Assign teacher to branch   | YES            | YES              | YES            | YES/LIMITED  | NO           | NO      | NO      |
| Remove teacher from branch | YES            | YES              | YES            | YES/LIMITED  | NO           | NO      | NO      |
| View teacher workload      | YES            | YES              | YES            | YES          | SELF         | NO      | NO      |

---

# 8. Class Management

| Action                     | Platform Owner | Academy Director | Branch Manager | Branch Admin | Teacher | Parent       | Student      |
| -------------------------- | -------------- | ---------------- | -------------- | ------------ | ------- | ------------ | ------------ |
| View classes platform-wide | YES            | NO               | NO             | NO           | NO      | NO           | NO           |
| View classes academy-wide  | YES            | YES              | NO             | NO           | NO      | NO           | NO           |
| View branch classes        | YES            | YES              | YES            | YES          | LIMITED | LIMITED      | LIMITED      |
| Create class               | YES            | YES              | YES            | YES          | NO      | NO           | NO           |
| Edit class                 | YES            | YES              | YES            | YES          | NO      | NO           | NO           |
| Assign teacher to class    | YES            | YES              | YES            | YES          | NO      | NO           | NO           |
| Enroll student to class    | YES            | YES              | YES            | YES          | NO      | REQUEST ONLY | REQUEST ONLY |
| Archive class              | YES            | YES              | YES            | YES          | NO      | NO           | NO           |

---

# 9. Scheduling

| Action                     | Platform Owner | Academy Director | Branch Manager | Branch Admin | Teacher      | Parent       | Student      |
| -------------------------- | -------------- | ---------------- | -------------- | ------------ | ------------ | ------------ | ------------ |
| View schedule academy-wide | YES            | YES              | NO             | NO           | NO           | NO           | NO           |
| View schedule branch       | YES            | YES              | YES            | YES          | LIMITED      | LIMITED      | LIMITED      |
| View assigned schedule     | YES            | YES              | YES            | YES          | YES          | LINKED CHILD | OWN          |
| Create schedule            | YES            | YES              | YES            | YES          | NO           | NO           | NO           |
| Edit schedule              | YES            | YES              | YES            | YES          | NO           | NO           | NO           |
| Request reschedule         | YES            | YES              | YES            | YES          | YES          | REQUEST ONLY | REQUEST ONLY |
| Approve reschedule         | YES            | YES              | YES            | YES/LIMITED  | NO           | NO           | NO           |
| Cancel schedule            | YES            | YES              | YES            | YES          | REQUEST ONLY | NO           | NO           |

---

# 10. Attendance

| Action                       | Platform Owner | Academy Director | Branch Manager | Branch Admin | Teacher      | Parent       | Student |
| ---------------------------- | -------------- | ---------------- | -------------- | ------------ | ------------ | ------------ | ------- |
| View attendance academy-wide | YES            | YES              | NO             | NO           | NO           | NO           | NO      |
| View attendance branch       | YES            | YES              | YES            | YES          | LIMITED      | NO           | NO      |
| View assigned attendance     | YES            | YES              | YES            | YES          | YES          | LINKED CHILD | OWN     |
| Create attendance            | NO             | NO               | YES/LIMITED    | YES          | YES          | NO           | NO      |
| Edit attendance before final | NO             | NO               | YES            | YES          | YES/LIMITED  | NO           | NO      |
| Edit finalized attendance    | NO             | YES/LIMITED      | YES/APPROVE    | YES/REQUEST  | REQUEST ONLY | NO           | NO      |
| Finalize attendance          | NO             | NO               | YES            | YES          | YES          | NO           | NO      |

---

# 11. Lesson Summary

| Action                           | Platform Owner | Academy Director | Branch Manager | Branch Admin | Teacher      | Parent       | Student |
| -------------------------------- | -------------- | ---------------- | -------------- | ------------ | ------------ | ------------ | ------- |
| View lesson summary academy-wide | YES            | YES              | NO             | NO           | NO           | NO           | NO      |
| View branch lesson summary       | YES            | YES              | YES            | YES          | LIMITED      | NO           | NO      |
| View assigned/linked summary     | YES            | YES              | YES            | YES          | YES          | LINKED CHILD | OWN     |
| Create lesson summary            | NO             | NO               | NO             | NO           | YES          | NO           | NO      |
| Edit lesson summary draft        | NO             | NO               | NO             | YES/LIMITED  | YES          | NO           | NO      |
| Edit published summary           | NO             | YES/LIMITED      | YES/APPROVE    | YES/REQUEST  | REQUEST ONLY | NO           | NO      |
| Publish lesson summary           | NO             | NO               | YES/LIMITED    | YES/LIMITED  | YES          | NO           | NO      |

---

# 12. Materials & Print Queue

| Action                   | Platform Owner | Academy Director | Branch Manager | Branch Admin | Teacher     | Parent  | Student |
| ------------------------ | -------------- | ---------------- | -------------- | ------------ | ----------- | ------- | ------- |
| View material repository | YES            | YES              | YES            | YES          | YES         | LIMITED | LIMITED |
| Upload material          | YES            | YES              | YES/LIMITED    | YES/LIMITED  | YES/LIMITED | NO      | NO      |
| Approve material         | YES            | YES              | YES/LIMITED    | NO           | NO          | NO      | NO      |
| Archive material         | YES            | YES              | YES/LIMITED    | NO           | NO          | NO      | NO      |
| Request print            | NO             | YES              | YES            | YES          | YES         | NO      | NO      |
| Manage print queue       | YES            | YES              | YES            | YES          | NO          | NO      | NO      |
| Mark printed/distributed | NO             | NO               | YES            | YES          | NO          | NO      | NO      |

---

# 13. Invoicing & Payments

| Action                        | Platform Owner | Academy Director | Branch Manager | Branch Admin | Teacher | Parent | Student |
| ----------------------------- | -------------- | ---------------- | -------------- | ------------ | ------- | ------ | ------- |
| View SaaS billing             | YES            | YES/LIMITED      | NO             | NO           | NO      | NO     | NO      |
| View academy financial report | YES            | YES              | NO             | NO           | NO      | NO     | NO      |
| View branch invoices          | YES            | YES              | YES            | YES          | NO      | NO     | NO      |
| Create academic invoice       | NO             | NO               | YES            | YES          | NO      | NO     | NO      |
| Edit invoice draft            | NO             | YES/LIMITED      | YES            | YES          | NO      | NO     | NO      |
| Cancel invoice                | NO             | YES/LIMITED      | YES/APPROVE    | YES/REQUEST  | NO      | NO     | NO      |
| View linked invoice           | NO             | NO               | NO             | NO           | NO      | YES    | NO      |
| Upload payment proof          | NO             | NO               | NO             | NO           | NO      | YES    | NO      |
| Confirm payment               | NO             | NO               | YES            | YES          | NO      | NO     | NO      |

---

# 14. Subscription & Addons

| Action                        | Platform Owner | Academy Director | Branch Manager | Branch Admin | Teacher | Parent | Student     |
| ----------------------------- | -------------- | ---------------- | -------------- | ------------ | ------- | ------ | ----------- |
| Manage SaaS plans             | YES            | NO               | NO             | NO           | NO      | NO     | NO          |
| Activate academy subscription | YES            | NO               | NO             | NO           | NO      | NO     | NO          |
| View academy subscription     | YES            | YES              | NO             | NO           | NO      | NO     | NO          |
| Buy student premium addon     | NO             | NO               | NO             | NO           | NO      | YES    | NO          |
| View addon status             | YES            | YES              | YES/LIMITED    | YES/LIMITED  | NO      | YES    | YES/LIMITED |
| Cancel addon                  | YES            | YES/LIMITED      | NO             | NO           | NO      | YES    | NO          |

---

# 15. Communication

| Action                      | Platform Owner | Academy Director | Branch Manager | Branch Admin | Teacher      | Parent       | Student      |
| --------------------------- | -------------- | ---------------- | -------------- | ------------ | ------------ | ------------ | ------------ |
| View communication audit    | YES            | YES              | YES/LIMITED    | YES/LIMITED  | NO           | NO           | NO           |
| Create academy announcement | YES            | YES              | NO             | NO           | NO           | NO           | NO           |
| Create branch announcement  | NO             | YES              | YES            | YES          | NO           | NO           | NO           |
| Create class announcement   | NO             | YES              | YES            | YES          | YES          | NO           | NO           |
| Send class message          | NO             | NO               | LIMITED        | LIMITED      | YES          | YES/LIMITED  | YES/LIMITED  |
| Moderate communication      | YES            | YES              | YES            | YES          | NO           | NO           | NO           |
| Delete message              | YES            | YES              | YES            | YES          | SELF LIMITED | SELF LIMITED | SELF LIMITED |

---

# 16. Reports & Analytics

| Report               | Platform Owner | Academy Director | Branch Manager | Branch Admin | Teacher  | Parent       | Student |
| -------------------- | -------------- | ---------------- | -------------- | ------------ | -------- | ------------ | ------- |
| Platform MRR         | YES            | NO               | NO             | NO           | NO       | NO           | NO      |
| Academy Growth       | YES            | YES              | NO             | NO           | NO       | NO           | NO      |
| Branch Performance   | YES            | YES              | YES            | LIMITED      | NO       | NO           | NO      |
| Teacher Workload     | YES            | YES              | YES            | YES          | SELF     | NO           | NO      |
| Student Progress     | YES            | YES              | YES            | YES          | ASSIGNED | LINKED CHILD | SELF    |
| Attendance Analytics | YES            | YES              | YES            | YES          | ASSIGNED | LINKED CHILD | SELF    |
| Financial Analytics  | YES            | YES              | YES/LIMITED    | LIMITED      | NO       | NO           | NO      |

---

# Approval Matrix

---

# Reschedule Approval

| Requester      | Approver                         |
| -------------- | -------------------------------- |
| Teacher        | Branch Admin / Branch Manager    |
| Branch Admin   | Branch Manager                   |
| Branch Manager | Self / Academy Director optional |
| Parent         | Branch Admin / Branch Manager    |
| Student        | Branch Admin / Branch Manager    |

---

# Attendance Edit Approval

| Condition                | Approver                                  |
| ------------------------ | ----------------------------------------- |
| Before finalization      | Teacher / Branch Admin                    |
| After finalization       | Branch Manager / Branch Admin with reason |
| Sensitive dispute        | Branch Manager                            |
| Academy-level escalation | Academy Director                          |

---

# Invoice Cancellation Approval

| Condition        | Approver                                     |
| ---------------- | -------------------------------------------- |
| Draft invoice    | Branch Admin                                 |
| Issued invoice   | Branch Manager                               |
| Paid invoice     | Academy Director / Branch Manager with audit |
| Disputed invoice | Academy Director                             |

---

# Material Approval

| Action           | Approver                          |
| ---------------- | --------------------------------- |
| Upload draft     | Teacher / Admin                   |
| Publish material | Academy Director / Branch Manager |
| Archive material | Academy Director / Branch Manager |
| Print request    | Branch Admin / Branch Manager     |

---

# Cross Branch Permission Rules

---

# Teacher Cross Branch

Teacher dapat lintas branch hanya jika:

* tercatat di `teacher_branches`,
* status assignment aktif,
* tidak ada conflict jadwal.

---

# Student Cross Branch

Student dapat lintas branch hanya jika:

* memiliki `student_branch_access`,
* addon aktif,
* jadwal valid,
* branch target aktif.

---

# Parent Cross Branch Visibility

Parent dapat melihat aktivitas lintas branch anak hanya jika:

* student memiliki cross branch access aktif.

---

# Subscription-Aware Permissions

Beberapa permission bergantung pada:

* academy subscription,
* student premium addon,
* feature gating.

---

# Rule

Jika subscription tidak aktif:

* premium feature harus blocked di backend.

---

# Suspended Academy Behavior

Jika academy suspended:

Allowed:

* view limited data
* renew subscription
* export critical data, jika policy mengizinkan

Blocked:

* create new schedules
* create new invoices
* activate new classes
* invite new users

---

# Audit Requirements

Semua action berikut wajib audit log:

* role assignment
* permission changes
* schedule changes
* reschedule approval
* attendance edits
* invoice edits
* payment confirmation
* material approval
* communication moderation
* subscription changes

---

# API Authorization Rule

Setiap endpoint wajib mengecek minimal:

```text
1. authenticated user
2. active academy
3. active role
4. requested action
5. requested scope
6. subscription status
7. branch access
```

---

# Realtime Permission Rule

Realtime event wajib scoped.

Tidak boleh broadcast event ke:

* user tanpa academy access,
* user tanpa branch access,
* user tanpa linked student,
* user tanpa assigned class.

---

# Frontend Visibility Rule

Frontend menu/tombol harus mengikuti permission matrix.

Tetapi frontend visibility:

* hanya UX helper,
* bukan security authority.

---

# AI Agent Rules

AI-generated implementation wajib:

* membaca permission matrix,
* tidak hardcode role check kasar,
* tidak membuat permission global liar,
* tidak bypass backend authorization,
* dan tidak membuat frontend-only security.

---

# Forbidden AI Behaviors

AI agents dilarang:

* membuat `if role == admin` tanpa scope,
* membuat akses branchless,
* membuat query tanpa academy_id,
* membuat query tanpa branch_id untuk data branch,
* membuat permission berbeda antara frontend dan backend,
* membuat bypass untuk demo.

---

# Final Permission Statement

Permission system harus:

* explicit,
* scoped,
* auditable,
* subscription-aware,
* branch-aware,
* dan aman dari role leakage.

Setiap access harus menjawab:

```text
Siapa user ini?
Role aktifnya apa?
Scope-nya di mana?
Action apa yang diminta?
Apakah subscription mengizinkan?
Apakah branch/academy sesuai?
Apakah perlu approval?
```
