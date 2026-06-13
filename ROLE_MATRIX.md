# Premium Multi-Branch Academic Operations Platform

---

# Purpose

Dokumen ini mendefinisikan:

* role system,
* permission hierarchy,
* visibility scope,
* operational authority,
* dan access limitation.

Semua:

* backend authorization,
* frontend visibility,
* navigation rendering,
* API protection,
* dan AI-generated implementation

WAJIB mengikuti role matrix ini.

---

# Core Permission Principles

---

# 1. Least Privilege Principle

Setiap role hanya boleh:

* melihat,
* mengakses,
* dan mengubah

data yang memang dibutuhkan.

---

# Rule

Role tidak boleh memiliki:

* access berlebihan,
* hidden admin capability,
* atau unrestricted visibility.

---

# 2. Visibility ≠ Edit Authority

Melihat data:

* bukan berarti boleh mengubah data.

---

# Example

Parent:

* boleh melihat attendance,
* tetapi tidak boleh mengubah attendance.

---

# 3. Branch Isolation Principle

Semua operational role:

* dibatasi berdasarkan branch scope.

---

# Rule

Role branch-level:

* tidak boleh mengakses branch lain,
* kecuali memang memiliki explicit multi-branch authority.

---

# 4. Multi-Role System

Satu user dapat memiliki:

* lebih dari satu role.

---

# Example

```text id="n0sxvc"
User:
Arief

Roles:
- academy_director
- branch_manager
```

---

# Rule

Permission:

* merupakan gabungan seluruh role aktif user.

---

# Forbidden

Role gabungan statis.

```text id="n9w3sx"
DirectorAndAdmin
```

---

# Official Role Hierarchy

```text id="33wojk"
Platform Owner
└── Academy Director
    ├── Branch Manager
    ├── Branch Admin
    ├── Teacher
    ├── Student
    └── Parent
```

---

# ROLE DEFINITIONS

---

# 1. Platform Owner

## Description

Pemilik platform SaaS global.

Mengontrol:

* seluruh academy,
* seluruh subscription,
* seluruh infrastructure,
* dan global platform health.

---

# Visibility Scope

* all academies
* all branches
* all platform analytics
* all subscription data

---

# Permissions

Can:

* manage academies
* manage subscriptions
* manage plans
* manage global settings
* view global analytics
* manage platform infrastructure

---

# Restrictions

Should NOT:

* operate branch schedules
* manage attendance manually
* interfere with daily branch workflow

---

# 2. Academy Director

## Description

Pemilik atau kepala academy.

Memiliki global visibility terhadap seluruh branch dalam academy.

---

# Visibility Scope

* all academy branches
* all academy reports
* all academy teachers
* all academy students
* all academy invoices

---

# Permissions

Can:

* monitor all branches
* view academy analytics
* view revenue reports
* view teacher performance
* manage academy-level settings
* approve high-level operational changes

---

# Restrictions

Should NOT:

* become operational attendance operator
* manually handle daily branch workflow

---

# 3. Branch Manager

## Description

Operational controller untuk satu branch.

---

# Visibility Scope

* assigned branch only

---

# Permissions

Can:

* monitor branch performance
* approve schedule changes
* view branch reports
* monitor teacher workload
* manage branch operations

---

# Restrictions

Cannot:

* access other branches
* access academy-wide settings
* access platform billing

---

# 4. Branch Admin

## Description

Operational executor untuk branch.

---

# Visibility Scope

* assigned branch only

---

# Permissions

Can:

* create schedules
* manage classes
* manage attendance
* create invoices
* manage student administration
* manage branch communication

---

# Restrictions

Cannot:

* access academy-wide settings
* access other branches
* manage SaaS subscriptions

---

# 5. Teacher

## Description

Teaching operational role.

---

# Visibility Scope

* assigned classes
* assigned students
* assigned schedules
* assigned branch access

---

# Permissions

Can:

* input attendance
* create lesson summaries
* upload materials
* assign homework
* communicate with assigned classes
* view assigned student progress

---

# Cross Branch Rules

Teacher MAY:

* teach across multiple branches.

---

# Required Conditions

Teacher assignments must:

* prevent schedule overlap,
* prevent branch conflict,
* and follow operational validation.

---

# Restrictions

Cannot:

* access branch financial reports
* modify invoices
* manage academy settings
* edit unauthorized schedules

---

# 6. Student

## Description

Learning participant.

---

# Visibility Scope

* enrolled classes
* own schedules
* own assignments
* own progress

---

# Permissions

Can:

* access learning materials
* view schedules
* submit assignments
* join class communication
* view own progress

---

# Restrictions

Cannot:

* edit attendance
* edit academic records
* manage schedules
* access parent billing
* access operational reports

---

# Cross Branch Access

Default:

* single branch access only.

Premium:

* cross branch access available through upgrade.

---

# 7. Parent

## Description

Primary payer and monitoring authority.

---

# Visibility Scope

* linked children only

---

# Permissions

Can:

* view attendance
* view lesson summaries
* view invoices
* upload payment proof
* receive operational notifications
* monitor child progress
* view schedules

---

# Restrictions

Cannot:

* edit attendance
* edit lesson reports
* modify academic records
* modify schedules
* manage operational workflows

---

# Permission Categories

---

# A. View Permissions

```text id="djw9sl"
VIEW:
- dashboard
- attendance
- invoices
- schedules
- analytics
- reports
- communication
```

---

# B. Create Permissions

```text id="2jlwm1"
CREATE:
- schedules
- invoices
- materials
- announcements
- assignments
```

---

# C. Edit Permissions

```text id="q6a0ns"
EDIT:
- schedules
- attendance
- lesson reports
- student records
```

---

# D. Approval Permissions

```text id="1jkn7i"
APPROVE:
- reschedule requests
- operational changes
- branch actions
```

---

# E. Financial Permissions

```text id="jiz6i2"
FINANCIAL:
- invoice generation
- payment confirmation
- financial reports
```

---

# Branch Scope Matrix

| Role             | Branch Scope          |
| ---------------- | --------------------- |
| Platform Owner   | All Academies         |
| Academy Director | All Academy Branches  |
| Branch Manager   | Assigned Branch       |
| Branch Admin     | Assigned Branch       |
| Teacher          | Assigned Branch/Class |
| Student          | Own Branch/Class      |
| Parent           | Linked Student Only   |

---

# Operational Authority Matrix

| Action              | Director | Branch Manager | Branch Admin | Teacher | Parent | Student |
| ------------------- | -------- | -------------- | ------------ | ------- | ------ | ------- |
| View Reports        | YES      | LIMITED        | LIMITED      | NO      | NO     | NO      |
| Create Schedule     | OPTIONAL | YES            | YES          | NO      | NO     | NO      |
| Edit Attendance     | NO       | OPTIONAL       | YES          | YES     | NO     | NO      |
| Generate Invoice    | NO       | OPTIONAL       | YES          | NO      | NO     | NO      |
| Upload Materials    | OPTIONAL | OPTIONAL       | OPTIONAL     | YES     | NO     | NO      |
| View Parent Billing | YES      | LIMITED        | YES          | NO      | YES    | NO      |

---

# Notification Visibility Rules

---

# Parent Receives

* attendance alerts
* schedule changes
* invoice notifications
* class cancellations
* progress updates

---

# Teacher Receives

* teaching schedule
* class updates
* assignment notifications
* operational alerts

---

# Branch Admin Receives

* operational alerts
* scheduling conflicts
* payment alerts
* print queue alerts

---

# Audit Log Rules

Semua permission-sensitive actions wajib:

* memiliki actor identity,
* timestamp,
* affected entity,
* dan change detail.

---

# Forbidden Role Behaviors

Platform MUST prevent:

* hidden admin access
* unauthorized branch access
* cross-role privilege leak
* direct database privilege assumptions
* frontend-only permission validation

---

# Required Authorization Rules

Authorization wajib:

* backend validated,
* API validated,
* dan frontend-aware.

Frontend visibility saja tidak cukup.

---

# AI Agent Rules

AI-generated implementation wajib:

* mengikuti role matrix,
* tidak membuat hidden permissions,
* tidak bypass branch isolation,
* tidak hardcode role logic,
* dan tidak membuat duplicate permission flow.

---

# Final Role Matrix Statement

Role system platform harus:

* scalable,
* auditable,
* branch-aware,
* maintainable,
* dan stabil dalam operational complexity tinggi.
