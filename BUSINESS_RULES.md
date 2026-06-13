# Premium Multi-Branch Academic Operations Platform

---

# Purpose

Dokumen ini mendefinisikan:

* aturan bisnis,
* workflow operasional,
* logic sistem,
* dan batasan perilaku platform.

Semua:

* backend,
* frontend,
* database,
* realtime system,
* notification,
* dan AI-generated implementation

WAJIB mengikuti business rules di dokumen ini.

---

# Global Business Principles

---

# 1. Multi-Branch By Default

Semua academy dianggap:

* memiliki banyak branch,
* walaupun secara realita hanya menggunakan satu branch.

---

# Rule

Semua operational entities wajib:

* memiliki branch scope,
* memahami branch visibility,
* dan mengikuti branch isolation.

---

# Required Scope

Semua data berikut wajib mempertimbangkan:

* academy_id
* branch_id

Data:

* students
* teachers
* schedules
* invoices
* classes
* attendance
* payments
* notifications
* communication

---

# 2. Branch Equality Principle

Tidak ada:

* branch utama,
* branch pusat,
* branch superior.

Semua branch:

* setara,
* independen,
* memiliki operasional sendiri.

---

# Rule

Branch memiliki:

* admin sendiri,
* invoice sendiri,
* kelas sendiri,
* jadwal sendiri,
* operasional sendiri.

Academy Director hanya memiliki:

* global visibility,
* monitoring authority,
* dan operational overview.

---

# 3. Academy Structure Rules

## Platform Structure

```text id="n4ijvy"
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

# 4. Multi-Role User Rules

Satu user dapat memiliki:

* lebih dari satu role.

Contoh:

* Academy Director + Branch Manager
* Branch Manager + Branch Admin

---

# Rule

Role harus:

* modular,
* additive,
* dan permission-based.

Role gabungan statis dilarang.

---

# Forbidden

```text id="r6hgt7"
AcademyDirectorAndAdmin
```

---

# Required

```text id="k6mww4"
roles:
- academy_director
- branch_admin
```

---

# 5. Parent Account Rules

Parent adalah:

* payer utama,
* decision maker,
* dan monitoring authority.

---

# Rule

Parent wajib dapat:

* melihat jadwal anak,
* melihat attendance,
* melihat lesson summary,
* melihat invoice,
* melihat payment status,
* menerima notification penting.

---

# Parent Restrictions

Parent tidak boleh:

* mengubah attendance,
* mengubah lesson report,
* mengubah academic records,
* atau mengedit teacher workflow.

---

# 6. Student Account Rules

Student adalah:

* learning participant,
* bukan operational authority.

---

# Rule

Student dapat:

* melihat schedule,
* melihat materials,
* melihat assignments,
* melihat progress,
* mengikuti class communication.

---

# Student Restrictions

Student tidak boleh:

* mengubah invoice,
* mengubah attendance,
* mengubah operational schedule,
* atau mengakses parent billing.

---

# 7. Teacher Rules

Teacher adalah:

* operational teaching role.

---

# Teacher Permissions

Teacher dapat:

* melihat assigned classes,
* input attendance,
* membuat lesson summary,
* upload materials,
* memberikan assignments,
* melihat student progress.

---

# Teacher Restrictions

Teacher tidak boleh:

* mengedit invoice,
* menghapus academic records,
* mengubah academy settings,
* atau mengakses branch financial reports.

---

# 8. Cross Branch Teacher Rules

Teacher dapat:

* mengajar di lebih dari satu branch.

---

# Rule

Semua teacher assignment wajib:

* branch-aware,
* schedule-aware,
* conflict-aware.

---

# Required Conflict Detection

Platform wajib mendeteksi:

* overlapping schedule,
* duplicate class time,
* cross branch collision.

---

# 9. Student Cross Branch Rules

Default student:

* hanya memiliki akses ke home branch.

---

# Premium Upgrade Rule

Cross branch access:

* adalah fitur premium,
* membutuhkan subscription upgrade.

Biaya upgrade:

* ditanggung parent/student.

---

# Cross Branch Access Includes

* class enrollment lintas branch
* schedule visibility lintas branch
* attendance lintas branch
* teacher access lintas branch

---

# 10. Academy Director Rules

Academy Director memiliki:

* global academy visibility,
* seluruh branch visibility,
* global reporting access.

---

# Academy Director Permissions

Dapat:

* melihat seluruh branch,
* melihat global revenue,
* melihat operational analytics,
* melihat teacher performance,
* melihat student statistics.

---

# Academy Director Restrictions

Tidak wajib menjadi:

* operator harian,
* scheduler utama,
* atau attendance operator.

---

# 11. Branch Manager Rules

Branch Manager fokus pada:

* branch operational control,
* teacher coordination,
* schedule approval,
* branch KPI monitoring.

---

# Branch Manager Permissions

Dapat:

* melihat branch reports,
* approve reschedule,
* melihat teacher load,
* mengelola branch operations.

---

# Branch Manager Restrictions

Tidak boleh:

* mengakses branch lain,
* mengakses academy global billing,
* atau mengubah platform settings.

---

# 12. Branch Admin Rules

Branch Admin adalah:

* operational executor.

---

# Branch Admin Permissions

Dapat:

* membuat class,
* mengatur jadwal,
* mengelola attendance,
* membuat invoice,
* mengelola student administration.

---

# Branch Admin Restrictions

Tidak boleh:

* mengubah academy-wide settings,
* mengakses branch lain,
* atau mengubah subscription plans.

---

# 13. Scheduling Rules

Scheduling adalah:

* core operational engine.

---

# Scheduling Principles

Scheduling wajib:

* realtime,
* conflict-aware,
* branch-aware,
* teacher-aware,
* student-aware.

---

# Forbidden Scheduling Behavior

Tidak boleh:

* double booking teacher,
* double booking room,
* overlapping class,
* silent reschedule.

---

# Required Schedule Events

Semua perubahan jadwal wajib:

* tercatat,
* memiliki audit log,
* mengirim notification.

---

# 14. Attendance Rules

Attendance adalah:

* academic trust record.

---

# Attendance Permissions

Attendance hanya dapat:

* dibuat teacher,
* atau branch admin.

---

# Attendance Lock Rule

Attendance yang sudah finalized:

* tidak boleh diedit sembarangan.

Edit attendance wajib:

* memiliki reason,
* tercatat audit log.

---

# 15. Lesson Summary Rules

Setiap class session wajib memiliki:

* lesson summary,
* attendance status,
* dan optional teacher note.

---

# Parent Visibility Rule

Parent wajib dapat melihat:

* lesson summary,
* progress activity,
* dan attendance history.

---

# 16. Material Management Rules

Semua materials:

* dikelola secara academy-wide,
* bukan branch-isolated.

---

# Material Lifecycle

```text id="lq4x2k"
Draft
→ Review
→ Ready
→ Print Queue
→ Distributed
→ Archived
```

---

# Material Rules

Semua material wajib:

* memiliki version,
* upload history,
* uploader identity,
* dan archive capability.

---

# 17. Print Queue Rules

Print queue wajib:

* centralized,
* traceable,
* dan priority-aware.

---

# Required Print Data

* material
* branch target
* quantity
* requested by
* print status
* deadline

---

# 18. Invoice Rules

Invoice bersifat:

* branch-specific,
* student-specific.

---

# Invoice Scope

Invoice dibuat:

* oleh branch,
* untuk student/parent.

---

# Invoice Visibility

Parent dapat:

* melihat invoice,
* melihat payment history,
* upload payment proof.

---

# Invoice Restrictions

Teacher tidak boleh:

* mengakses invoice management.

---

# 19. SaaS Subscription Rules

Academy adalah:

* SaaS customer platform.

---

# SaaS Billing Scope

Platform billing:

* terpisah dari academic invoice.

---

# Platform Subscription Includes

* academy subscription
* branch operations
* teacher management
* scheduling engine
* operational dashboards

---

# Premium Addon Rules

Premium features:

* dapat dijual terpisah,
* dapat berupa addon subscription.

---

# Example Premium Addons

* cross branch student
* advanced analytics
* premium reports
* enhanced monitoring

---

# 20. Notification Rules

Notification harus:

* relevan,
* penting,
* dan operationally useful.

---

# Required Notification Events

* schedule changes
* attendance alerts
* invoice due
* payment confirmation
* class cancellation
* operational announcements

---

# Forbidden Notification Behavior

Tidak boleh:

* spam,
* duplicate,
* irrelevant alerts,
* notification flooding.

---

# 21. Communication Rules

Communication wajib:

* terstruktur,
* operationally focused,
* dan traceable.

---

# Communication Channels

* class group
* teacher announcements
* parent communication
* operational notices

---

# Forbidden Communication Rules

Platform tidak boleh menjadi:

* social media,
* random chat platform,
* atau unmoderated communication system.

---

# 22. Audit Log Rules

Semua perubahan penting wajib memiliki:

* actor identity,
* timestamp,
* change detail,
* dan reason.

---

# Required Audit Areas

* schedule changes
* attendance edits
* invoice updates
* payment confirmation
* permission changes
* material updates

---

# 23. Mobile-First Operational Rules

Semua workflow penting wajib:

* usable on mobile,
* thumb-friendly,
* readable,
* dan low-friction.

---

# Required Mobile Priorities

* attendance
* schedule
* notification
* parent monitoring
* teacher workflow

---

# 24. AI Agent Rules

AI-generated implementation wajib:

* mengikuti business rules,
* tidak membuat shortcut logic,
* tidak duplicate workflow,
* tidak membuat hidden operational behavior.

---

# Forbidden AI Behavior

AI agents dilarang:

* hardcode permission,
* hardcode branch logic,
* bypass validation,
* membuat orphan systems,
* atau membuat duplicate operational flow.

---

# Final Business Rule Statement

Semua implementation harus:

* mendukung operational stability,
* meningkatkan trust,
* mengurangi chaos,
* menjaga scalability,
* dan mempertahankan premium experience di seluruh academy ecosystem.
