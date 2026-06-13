# Premium Multi-Branch Academic Operations Platform

---

# Purpose

Dokumen ini mendefinisikan:

* scheduling architecture,
* class lifecycle,
* conflict detection,
* reschedule workflow,
* realtime synchronization,
* dan operational scheduling rules.

Scheduling adalah:

* core operational engine platform.

Jika scheduling gagal:

* operasional academy akan chaos,
* teacher overload,
* parent trust turun,
* dan branch stability terganggu.

---

# Core Scheduling Philosophy

---

# 1. Scheduling Stability Is Sacred

Scheduling adalah:

* jantung operasional academy.

Semua scheduling workflow wajib:

* realtime,
* predictable,
* auditable,
* dan conflict-aware.

---

# Rule

Tidak boleh ada:

* hidden reschedule,
* duplicate schedule,
* silent override,
* atau schedule ambiguity.

---

# 2. Human-Centered Scheduling

Scheduling harus memahami:

* manusia lelah,
* guru berpindah branch,
* kelas berubah,
* dan operasional tidak selalu sempurna.

---

# Rule

Sistem harus:

* membantu operasional,
* bukan memperumit operasional.

---

# 3. Branch-Aware Scheduling

Semua scheduling wajib:

* branch-scoped,
* academy-aware,
* dan permission-scoped.

---

# Core Scheduling Entities

---

# 1. Academic Schedule

Representasi:

* kelas,
* waktu,
* teacher,
* room,
* branch,
* dan operational state.

---

# Required Schedule Data

```sql id="vj8k2u"
academy_id
branch_id
class_id
teacher_id
room_id
schedule_date
start_time
end_time
timezone
schedule_status
```

---

# 2. Class Session

Setiap pertemuan adalah:

* session individual.

---

# Example

```text id="2m0gk4"
English Intermediate
Every Monday & Wednesday
19:00 - 21:00
```

akan menghasilkan:

* banyak class sessions.

---

# 3. Schedule Lifecycle

```text id="x4rqzx"
Draft
→ Scheduled
→ Confirmed
→ Active
→ Completed
```

---

# Additional States

```text id="h5w3j5"
Rescheduled
Cancelled
Pending Approval
Suspended
```

---

# Scheduling Scope Rules

---

# Branch Scope

Default scheduling hanya berlaku:

* di branch terkait.

---

# Cross Branch Scheduling

Cross branch scheduling hanya berlaku jika:

* teacher memiliki multi-branch assignment,
* student memiliki premium cross-branch access.

---

# Forbidden Behavior

Tidak boleh:

* assign teacher ke branch tanpa authorization,
* assign student lintas branch tanpa valid subscription.

---

# Scheduling Engine Rules

---

# Core Scheduling Validation

Semua scheduling wajib memeriksa:

* teacher availability
* room availability
* branch availability
* student conflict
* operational overlap

---

# Required Scheduling Validation Order

```text id="i0mt2s"
1. Branch Validation
2. Teacher Validation
3. Room Validation
4. Student Validation
5. Time Conflict Validation
6. Cross Branch Validation
7. Realtime Lock Validation
```

---

# Teacher Scheduling Rules

---

# Teacher Assignment Rules

Teacher dapat:

* mengajar banyak class,
* mengajar lintas branch.

---

# Required Teacher Validation

Platform wajib mendeteksi:

* overlapping teaching time,
* impossible transition time,
* overload schedule,
* branch collision.

---

# Example Conflict

```text id="1jlwm0"
Teacher:
Sarah

Branch Meruya:
09:00 - 11:00

Branch Karawaci:
09:30 - 11:30
```

MUST BE BLOCKED.

---

# Teacher Workload Protection

Platform wajib:

* memonitor workload teacher,
* dan memberikan operational warning.

---

# Suggested Workload Warning

```text id="2swr3e"
High Teaching Load
Potential Burnout Risk
```

---

# Student Scheduling Rules

---

# Student Schedule Validation

Student tidak boleh:

* memiliki overlapping class,
* duplicate session,
* impossible cross-branch timing.

---

# Premium Cross Branch Rule

Student lintas branch:

* wajib memiliki premium access.

---

# Required Validation

Cross branch student scheduling wajib:

* subscription-aware,
* branch-aware,
* schedule-aware.

---

# Room Scheduling Rules

---

# Room Conflict Detection

Room tidak boleh:

* digunakan dua class bersamaan.

---

# Required Room Data

```sql id="xt4n4j"
room_id
branch_id
capacity
room_type
operational_status
```

---

# Room Status

```text id="4jbf4u"
available
maintenance
inactive
reserved
```

---

# Realtime Scheduling System

---

# Core Principle

Scheduling wajib:

* realtime synchronized.

---

# Required Realtime Events

* new schedule
* reschedule
* cancellation
* teacher reassignment
* room reassignment
* emergency changes

---

# Realtime Sync Targets

* teacher dashboard
* student dashboard
* parent dashboard
* branch admin dashboard

---

# Reschedule Workflow

---

# Core Rule

Reschedule tidak boleh:

* instant overwrite.

---

# Required Workflow

```text id="qmnlye"
Request
→ Validation
→ Approval
→ Notification
→ Realtime Sync
→ Audit Log
```

---

# Reschedule Authority

| Role             | Authority      |
| ---------------- | -------------- |
| Teacher          | Request Only   |
| Branch Admin     | Approve        |
| Branch Manager   | Approve        |
| Academy Director | Oversight Only |

---

# Required Reschedule Reason

Semua reschedule wajib:

* memiliki reason.

---

# Suggested Reasons

```text id="5c1qza"
Teacher Sick
Operational Issue
Room Unavailable
Holiday Adjustment
Emergency Event
Technical Issue
```

---

# Schedule Cancellation Rules

---

# Cancellation Authority

Schedule cancellation hanya dapat dilakukan oleh:

* Branch Admin
* Branch Manager

---

# Required Cancellation Workflow

```text id="jtfmfe"
Cancel
→ Notify Users
→ Update Schedule
→ Audit Log
```

---

# Required Notification Targets

* teacher
* student
* parent
* related operational users

---

# Schedule Visibility Rules

---

# Teacher Visibility

Teacher hanya dapat melihat:

* assigned schedules.

---

# Student Visibility

Student hanya dapat melihat:

* enrolled schedules.

---

# Parent Visibility

Parent hanya dapat melihat:

* linked student schedules.

---

# Academy Director Visibility

Academy Director dapat melihat:

* seluruh academy schedules.

---

# Schedule Notification Rules

---

# Required Notification Events

* class reminder
* schedule changes
* cancellations
* room changes
* teacher replacement

---

# Notification Priority

## High Priority

* cancellation
* reschedule
* emergency changes

---

## Medium Priority

* reminders
* room updates

---

# Low Priority

* informational updates

---

# Attendance Integration Rules

---

# Attendance Dependency

Attendance hanya dapat:

* dibuat pada active session.

---

# Required Validation

Tidak boleh:

* attendance tanpa session,
* attendance di cancelled class,
* attendance duplicate.

---

# Lesson Summary Integration

Setiap completed session wajib:

* memiliki lesson summary.

---

# Required Summary Fields

```sql id="3mjlwm"
session_id
teacher_id
lesson_topic
teacher_notes
homework
summary_status
```

---

# Parent Monitoring Integration

Parent wajib dapat melihat:

* session history,
* attendance history,
* lesson summary,
* schedule updates.

---

# Scheduling Analytics

---

# Required Analytics

* teacher workload
* branch utilization
* room utilization
* cancellation rate
* reschedule rate
* attendance consistency

---

# Operational Warning System

Platform wajib memberikan warning untuk:

* teacher overload
* excessive reschedule
* schedule collision
* room congestion
* operational instability

---

# Suggested Warning Example

```text id="dgr2s7"
Warning:
Branch Meruya experiencing high schedule collision risk.
```

---

# Timezone Architecture

---

# Core Rule

Semua schedule wajib:

* timezone-aware.

---

# Required Fields

```sql id="mxvhzx"
timezone
utc_timestamp
local_time
```

---

# Scheduling Performance Rules

Scheduling engine wajib:

* fast,
* scalable,
* realtime capable.

---

# Forbidden Performance Behavior

Tidak boleh:

* full-table conflict scan,
* blocking realtime operations,
* synchronous heavy recalculation.

---

# Audit Log Rules

Semua schedule actions wajib tercatat:

* created_by
* updated_by
* approval_actor
* change_reason
* previous_schedule
* new_schedule
* timestamp

---

# AI Agent Rules

AI-generated implementation wajib:

* mengikuti scheduling rules,
* mengikuti validation order,
* tidak bypass conflict detection,
* tidak bypass approval workflow,
* dan tidak membuat hidden scheduling logic.

---

# Forbidden AI Behaviors

AI agents dilarang:

* hardcode schedules,
* bypass realtime sync,
* bypass branch isolation,
* membuat silent reschedule,
* atau membuat duplicate scheduling flow.

---

# Final Scheduling Foundation Statement

Scheduling system adalah:

* jantung operasional platform,
* fondasi trust,
* dan fondasi stabilitas academy.

Semua implementation wajib:

* realtime,
* auditable,
* scalable,
* conflict-aware,
* dan operationally stable.
