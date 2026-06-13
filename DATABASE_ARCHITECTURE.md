# Premium Multi-Branch Academic Operations Platform

---

# Purpose

Dokumen ini mendefinisikan:

* database philosophy,
* data isolation strategy,
* relational architecture,
* audit strategy,
* realtime-friendly design,
* dan scalability foundation platform.

Database adalah:

* fondasi operasional platform,
* sumber kebenaran utama,
* dan backbone seluruh workflow academy.

Jika database architecture salah:

* scheduling akan chaos,
* permission akan bocor,
* reporting akan lambat,
* dan scalability akan runtuh.

---

# Core Database Philosophy

---

# 1. Multi-Tenant By Design

Platform adalah:

* SaaS multi academy.

---

# Rule

Semua data wajib:

* academy-aware,
* tenant-isolated,
* dan permission-scoped.

---

# Required Core Scope

Semua operational entities wajib memiliki:

```sql id="ykympk"
academy_id
```

---

# Forbidden Architecture

Tidak boleh:

* shared unsafe data,
* global academy leakage,
* atau tenant ambiguity.

---

# 2. Multi-Branch By Default

Semua operational entities wajib:

* branch-aware.

---

# Required Branch Scope

Semua operational entities wajib memiliki:

```sql id="0l0b28"
branch_id
```

---

# Required Entities

* schedules
* students
* attendance
* invoices
* classes
* teacher assignments
* communication
* payments

---

# 3. Operational Clarity Over Cleverness

Database harus:

* jelas,
* mudah dipahami,
* mudah di-maintain,
* dan scalable.

---

# Rule

Avoid:

* over abstraction,
* hidden logic,
* magic relationships,
* dan polymorphic chaos.

---

# 4. Auditability Is Mandatory

Semua perubahan penting wajib:

* dapat ditelusuri,
* dapat diaudit,
* dan memiliki actor identity.

---

# Required Audit Metadata

```sql id="j7e0y4"
created_at
updated_at
created_by
updated_by
```

---

# Additional Audit Areas

* schedule changes
* invoice updates
* payment confirmation
* attendance edits
* permission changes

---

# 5. Realtime-Friendly Architecture

Platform menggunakan:

* realtime updates,
* notifications,
* scheduling synchronization.

---

# Rule

Database wajib:

* optimized for realtime reads,
* indexing-aware,
* dan scalable under operational traffic.

---

# Core Database Structure

---

# Platform Layer

---

# academies

Representasi:

* tenant utama platform.

---

# Suggested Fields

```sql id="1m3pk7"
id
name
slug
logo
subscription_plan
subscription_status
created_at
updated_at
```

---

# academy_settings

Pengaturan academy.

---

# Suggested Fields

```sql id="80ltwy"
academy_id
theme
timezone
currency
branding
notification_preferences
```

---

# Branch Layer

---

# branches

Representasi:

* cabang academy.

---

# Suggested Fields

```sql id="d65l6f"
id
academy_id
name
code
timezone
status
address
created_at
```

---

# Branch Status

```text id="1drjlwm"
active
inactive
maintenance
archived
```

---

# User Layer

---

# users

Tabel identitas global user.

---

# Suggested Fields

```sql id="bh6jgm"
id
academy_id
email
password_hash
full_name
phone
avatar
status
last_login_at
created_at
```

---

# Core User Principle

User adalah:

* identity layer,
* bukan role layer.

---

# user_roles

Support:

* multi-role system.

---

# Suggested Fields

```sql id="9b4tqt"
id
user_id
role
branch_id
assigned_at
```

---

# Forbidden Architecture

Tidak boleh:

* single rigid role column,
* hardcoded role hierarchy.

---

# Parent & Student Architecture

---

# students

Representasi student utama.

---

# Suggested Fields

```sql id="4t4u0n"
id
academy_id
home_branch_id
full_name
birth_date
student_code
status
created_at
```

---

# parents

Representasi parent/wali murid.

---

# Suggested Fields

```sql id="kzjlwm"
id
academy_id
user_id
relationship_type
primary_contact
```

---

# parent_students

Support:

* multi child parent.

---

# Suggested Fields

```sql id="8y8vqk"
parent_id
student_id
relationship_status
```

---

# Rule

Satu parent dapat:

* memiliki banyak student.

Satu student dapat:

* memiliki lebih dari satu guardian.

---

# Teacher Architecture

---

# teachers

Representasi teacher profile.

---

# Suggested Fields

```sql id="2k95x4"
id
academy_id
user_id
teacher_code
employment_status
specialization
```

---

# teacher_branches

Support:

* multi branch teacher assignment.

---

# Suggested Fields

```sql id="mb4nzz"
teacher_id
branch_id
assignment_status
assigned_at
```

---

# Scheduling Architecture

---

# classes

Representasi class utama.

---

# Suggested Fields

```sql id="1djlwm"
id
academy_id
branch_id
program_id
class_name
level_id
capacity
status
```

---

# class_students

Enrollment relation.

---

# Suggested Fields

```sql id="9xdycb"
class_id
student_id
enrollment_status
joined_at
```

---

# schedules

Representasi jadwal class.

---

# Suggested Fields

```sql id="6o1kkh"
id
academy_id
branch_id
class_id
teacher_id
room_id
schedule_date
start_time
end_time
timezone
status
```

---

# schedule_changes

Audit schedule modifications.

---

# Suggested Fields

```sql id="o0n5l9"
schedule_id
old_schedule
new_schedule
change_reason
approved_by
changed_by
created_at
```

---

# Attendance Architecture

---

# attendances

Attendance per session.

---

# Suggested Fields

```sql id="xjlwmz"
id
academy_id
branch_id
schedule_id
student_id
attendance_status
recorded_by
recorded_at
```

---

# Attendance Status

```text id="1x7r5y"
present
late
absent
excused
online
```

---

# Lesson Reporting Architecture

---

# lesson_summaries

Lesson report per session.

---

# Suggested Fields

```sql id="8brjlw"
id
schedule_id
teacher_id
lesson_topic
summary
homework
teacher_notes
created_at
```

---

# Material Management Architecture

---

# materials

Master material repository.

---

# Suggested Fields

```sql id="5jlwmf"
id
academy_id
title
material_type
version
status
uploaded_by
created_at
```

---

# material_distributions

Tracking branch/class usage.

---

# Suggested Fields

```sql id="mjlwm0"
material_id
branch_id
class_id
distribution_status
```

---

# Financial Architecture

---

# invoices

Academic billing.

---

# Suggested Fields

```sql id="gnjlwm"
id
academy_id
branch_id
student_id
invoice_number
amount
due_date
status
created_by
```

---

# payments

Payment records.

---

# Suggested Fields

```sql id="ymjlwm"
id
invoice_id
payment_method
amount_paid
payment_date
confirmed_by
status
```

---

# Subscription Architecture

---

# academy_subscriptions

SaaS subscription records.

---

# Suggested Fields

```sql id="rjlwmz"
academy_id
subscription_plan
status
started_at
expired_at
grace_period_until
```

---

# premium_addons

Addon system.

---

# Suggested Fields

```sql id="5s0d78"
academy_id
addon_type
status
expired_at
```

---

# Cross Branch Architecture

---

# student_branch_access

Premium cross branch access.

---

# Suggested Fields

```sql id="njlwmf"
student_id
branch_id
access_type
expired_at
```

---

# Communication Architecture

---

# communication_channels

Representasi channel komunikasi.

---

# Suggested Fields

```sql id="5g3lna"
id
academy_id
branch_id
channel_type
related_entity_id
status
```

---

# messages

Realtime communication records.

---

# Suggested Fields

```sql id="vjlwm1"
id
channel_id
sender_id
message_type
content
created_at
```

---

# Notification Architecture

---

# notifications

Notification center.

---

# Suggested Fields

```sql id="7jlwmw"
id
academy_id
recipient_user_id
notification_type
priority
payload
read_at
created_at
```

---

# Notification Priorities

```text id="v0bdjlwm"
high
medium
low
```

---

# Audit Architecture

---

# audit_logs

Centralized audit system.

---

# Suggested Fields

```sql id="qjlwm7"
id
academy_id
branch_id
actor_user_id
entity_type
entity_id
action_type
previous_data
new_data
ip_address
created_at
```

---

# Required Audit Coverage

* attendance edits
* schedule changes
* invoice changes
* role changes
* payment confirmation
* material updates

---

# Realtime Architecture Support

Database wajib support:

* websocket updates
* notification queue
* realtime scheduling
* operational sync

---

# Suggested Future Tables

```text id="1jlwm4"
realtime_events
job_queue
notification_queue
websocket_sessions
```

---

# Soft Delete Philosophy

Critical operational data:

* tidak boleh hard delete.

---

# Rule

Gunakan:

* soft delete,
* archived state,
* status lifecycle.

---

# Required Soft Delete Areas

* students
* schedules
* invoices
* payments
* classes
* materials

---

# Indexing Philosophy

Index wajib diprioritaskan untuk:

* academy_id
* branch_id
* schedule_date
* teacher_id
* student_id
* notification recipient
* invoice status

---

# Performance Rules

Database wajib:

* optimized for operational reads,
* scalable,
* dan realtime-friendly.

---

# Forbidden Database Behaviors

Tidak boleh:

* N+1 query chaos
* unindexed realtime queries
* cross academy unsafe joins
* giant transactional locks

---

# Data Privacy Rules

Semua data wajib:

* permission-aware,
* academy-scoped,
* dan branch-scoped.

---

# Forbidden Privacy Behavior

Tidak boleh:

* cross academy leakage
* unauthorized branch visibility
* unrestricted query access

---

# AI Agent Rules

AI-generated implementation wajib:

* mengikuti relational structure,
* mengikuti tenant isolation,
* mengikuti audit requirements,
* dan tidak membuat hidden schema behavior.

---

# Forbidden AI Behaviors

AI agents dilarang:

* membuat duplicate tables
* bypass academy scope
* bypass branch isolation
* membuat unsafe joins
* membuat inconsistent naming

---

# Naming Convention Rules

---

# Table Naming

Gunakan:

* plural snake_case

---

# Examples

```text id="vjlwm9"
students
teacher_branches
lesson_summaries
audit_logs
```

---

# Foreign Key Naming

Gunakan:

* singular_id format

---

# Examples

```text id="7jlwml"
academy_id
branch_id
teacher_id
student_id
```

---

# Final Database Foundation Statement

Database architecture adalah:

* fondasi stabilitas platform,
* fondasi scalability,
* fondasi auditability,
* dan fondasi operational trust.

Semua implementation wajib:

* scalable,
* branch-aware,
* realtime-friendly,
* auditable,
* dan maintainable jangka panjang.
