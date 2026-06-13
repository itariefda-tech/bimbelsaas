# Premium Multi-Branch Academic Operations Platform

---

# Purpose

Dokumen ini mendefinisikan:

* arsitektur multi-branch,
* branch isolation,
* cross-branch operations,
* visibility scope,
* dan hubungan operasional antar branch.

Dokumen ini menjadi fondasi:

* database structure,
* permission system,
* scheduling engine,
* reporting,
* invoicing,
* dan realtime operational workflow.

---

# Core Principle

Platform dibangun dengan filosofi:

## Multi-Branch By Default

Semua academy diasumsikan:

* memiliki banyak branch,
* walaupun implementasi awal hanya memakai satu branch.

Single branch hanyalah:

* bentuk sederhana dari multi-branch architecture.

---

# Branch Philosophy

---

# 1. Equal Branch Architecture

Tidak ada:

* branch pusat,
* branch utama,
* branch superior,
* branch anak.

Semua branch:

* setara,
* independen,
* memiliki operasional sendiri.

---

# Rule

Setiap branch memiliki:

* branch manager,
* branch admin,
* invoice sendiri,
* schedule sendiri,
* operational workflow sendiri.

---

# Academy Director Role

Academy Director:

* tidak menjadi branch utama,
* tidak menjadi operator pusat.

Academy Director hanya:

* memiliki global visibility,
* academy-wide monitoring,
* dan strategic oversight.

---

# Academy Structure

```text id="2eh9e6"
Academy
├── Branch Meruya
├── Branch Puri
├── Branch Karawaci
├── Branch Tangerang
└── Branch Online
```

---

# Branch Identity Rules

Setiap branch wajib memiliki:

* branch_id
* academy_id
* branch_name
* branch_code
* timezone
* operational_status

---

# Branch Status

Available statuses:

```text id="v6yk8k"
active
inactive
maintenance
suspended
archived
```

---

# Operational Isolation Principle

Semua operational data wajib:

* branch-aware,
* branch-isolated,
* dan permission-scoped.

---

# Required Branch Isolation

Semua data berikut wajib memiliki:

```sql id="2hr2fq"
academy_id
branch_id
```

---

# Required Entities

* students
* teachers
* schedules
* invoices
* attendance
* classes
* notifications
* payments
* operational_logs
* communication_channels

---

# Forbidden Architecture

Platform dilarang:

* menggunakan global branchless operational data,
* menggunakan hidden default branch,
* atau membuat cross-branch visibility tanpa permission.

---

# Branch Visibility Rules

---

# 1. Branch Admin Visibility

Branch Admin hanya dapat melihat:

* branch miliknya sendiri.

---

# 2. Branch Manager Visibility

Branch Manager hanya dapat melihat:

* branch miliknya sendiri.

---

# 3. Academy Director Visibility

Academy Director dapat melihat:

* seluruh branch dalam academy.

---

# 4. Platform Owner Visibility

Platform Owner dapat melihat:

* seluruh academy,
* seluruh branch global.

---

# Cross Branch Architecture

---

# Purpose

Cross branch system memungkinkan:

* teacher multi-branch assignment,
* student lintas branch,
* dan academy-wide learning flexibility.

---

# Core Rule

Cross branch access:

* bukan default behavior,
* tetapi controlled premium feature.

---

# Teacher Multi-Branch System

Teacher dapat:

* mengajar di lebih dari satu branch.

---

# Example

```text id="sfy7jw"
Teacher:
Sarah

Assigned Branches:
- Meruya
- Puri
- Karawaci
```

---

# Required Teacher Validation

Sistem wajib mencegah:

* overlapping class,
* impossible travel schedule,
* branch conflict,
* duplicate assignment.

---

# Teacher Branch Assignment Rules

Teacher assignment wajib:

* explicit,
* branch-scoped,
* dan time-aware.

---

# Required Database Structure

```text id="b5h5c9"
teacher_branches
```

---

# Suggested Fields

```sql id="61owg9"
teacher_id
branch_id
assignment_status
assigned_at
```

---

# Student Cross Branch System

---

# Default Rule

Student default:

* hanya memiliki access ke home branch.

---

# Premium Upgrade Rule

Cross branch student:

* adalah premium feature,
* membutuhkan addon subscription.

---

# Cross Branch Benefits

Student dapat:

* mengikuti class branch lain,
* melihat schedule lintas branch,
* mengikuti special teacher,
* mengakses premium classes.

---

# Required Validation

Cross branch enrollment wajib:

* conflict-aware,
* schedule-aware,
* dan tier-aware.

---

# Required Database Structure

```text id="r2m8lp"
student_branch_access
```

---

# Suggested Fields

```sql id="pnjduh"
student_id
branch_id
access_type
subscription_tier
expired_at
```

---

# Branch Scheduling Architecture

Scheduling wajib:

* branch-aware,
* realtime-aware,
* dan conflict-aware.

---

# Required Scheduling Validation

Sistem wajib mendeteksi:

* teacher overlap
* room overlap
* duplicate student class
* branch collision
* operational conflict

---

# Forbidden Scheduling Behavior

Tidak boleh ada:

* silent schedule override,
* hidden reschedule,
* duplicate teaching session.

---

# Branch Communication Rules

Communication wajib:

* branch-scoped,
* structured,
* dan traceable.

---

# Allowed Communication Scope

## Branch Communication

* teacher ↔ branch admin
* branch announcements
* operational notices

---

## Class Communication

* teacher ↔ student
* teacher ↔ parent
* assignment discussion

---

## Academy Communication

* academy-wide announcements
* policy updates
* operational alerts

---

# Forbidden Communication

Tidak boleh:

* unrestricted branch chat,
* cross branch spam,
* unmoderated public communication.

---

# Branch Financial Architecture

---

# Core Rule

Financial operations bersifat:

* branch-isolated,
* branch-reportable,
* dan academy-visible.

---

# Branch Financial Ownership

Branch memiliki:

* invoice sendiri,
* payment tracking sendiri,
* financial report sendiri.

---

# Academy Director Financial Visibility

Academy Director dapat:

* melihat seluruh branch revenue,
* melihat branch performance,
* melihat overdue analytics.

---

# Forbidden Financial Behavior

Branch tidak boleh:

* mengakses branch financial lain,
* mengubah academy subscription,
* atau melihat platform billing.

---

# Branch Analytics System

---

# Branch-Level Analytics

Setiap branch wajib memiliki:

* student count
* revenue
* attendance rate
* teacher load
* operational alerts
* overdue invoice rate

---

# Academy-Wide Analytics

Academy Director dapat melihat:

* branch comparison
* global academy performance
* best performing branch
* overloaded branch
* operational health

---

# Branch Comparison Example

| Branch   | Students | Revenue | Attendance |
| -------- | -------- | ------- | ---------- |
| Meruya   | 220      | 120jt   | 95%        |
| Puri     | 180      | 90jt    | 91%        |
| Karawaci | 140      | 70jt    | 88%        |

---

# Branch Operational Independence

Setiap branch wajib dapat:

* tetap beroperasi,
* walaupun branch lain mengalami masalah.

---

# Example

Jika:

* Branch Puri maintenance,
* maka Branch Meruya tetap berjalan normal.

---

# Branch Notification Architecture

Notification wajib:

* branch-aware,
* permission-aware,
* operationally relevant.

---

# Required Notification Scope

## Branch Scope

* operational alerts
* attendance issues
* scheduling conflict

---

## Parent Scope

* class updates
* attendance alerts
* payment notifications

---

## Teacher Scope

* teaching schedule
* operational changes
* assignment updates

---

# Realtime Multi-Branch Rules

Realtime system wajib:

* scoped by branch,
* scoped by academy,
* dan scoped by permission.

---

# Forbidden Realtime Behavior

Tidak boleh:

* broadcast seluruh academy tanpa kebutuhan,
* expose branch lain,
* atau leak operational data.

---

# Branch Audit Architecture

Semua branch actions wajib:

* memiliki audit log,
* actor identity,
* branch scope,
* timestamp,
* dan change history.

---

# Required Audit Areas

* schedule changes
* invoice changes
* payment confirmation
* attendance edits
* teacher reassignment
* branch operational changes

---

# Multi-Branch Scalability Principle

Architecture wajib scalable untuk:

* banyak branch,
* ribuan student,
* banyak teachers,
* dan high operational traffic.

---

# Required Scalability Areas

* scheduling
* communication
* notification
* invoicing
* realtime updates
* analytics

---

# AI Agent Rules

AI-generated implementation wajib:

* mengikuti branch isolation,
* tidak bypass branch validation,
* tidak hardcode branch logic,
* tidak membuat global unsafe query,
* dan tidak membuat hidden cross-branch access.

---

# Forbidden AI Behaviors

AI agents dilarang:

* membuat global branchless access,
* membuat unrestricted visibility,
* membuat duplicated branch workflow,
* atau mengabaikan branch isolation.

---

# Final Multi-Branch Foundation Statement

Multi-branch architecture adalah:

* fondasi scalability,
* fondasi operational stability,
* dan fondasi premium academy ecosystem.

Semua implementation wajib:

* branch-aware,
* scalable,
* auditable,
* dan operationally stable.
