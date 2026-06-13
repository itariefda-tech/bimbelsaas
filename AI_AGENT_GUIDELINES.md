# Premium Multi-Branch Academic Operations Platform

---

# Purpose

Dokumen ini mendefinisikan:

* aturan kerja AI agents,
* workflow development,
* implementation boundaries,
* anti-chaos engineering rules,
* dan operational coding discipline.

Dokumen ini WAJIB diikuti oleh:

* AI coding agents,
* Codex,
* ChatGPT,
* developer contributors,
* dan automated implementation systems.

---

# Core AI Philosophy

---

# 1. AI Is Assistant, Not Architect

AI membantu:

* implementasi,
* refactor,
* audit,
* dan optimisasi.

AI bukan:

* penentu business rules,
* penentu architecture,
* atau penentu operational workflow.

---

# Rule

Jika:

* architecture sudah ada,
* business rules sudah ada,
* role matrix sudah ada,

maka AI wajib mengikuti dokumen tersebut.

---

# Forbidden AI Behavior

AI dilarang:

* mengubah core business logic tanpa approval,
* mengubah permission flow diam-diam,
* membuat workflow baru tanpa dokumentasi,
* atau membuat hidden behavior.

---

# Required Reference Documents

Sebelum implementasi,
AI wajib memahami:

```text
README.md
PROJECT_VISION.md
CORE_FOUNDATION.md
BUSINESS_RULES.md
ROLE_MATRIX.md
MULTI_BRANCH_ARCHITECTURE.md
CLASS_SCHEDULING_SYSTEM.md
PARENT_EXPERIENCE.md
TEACHER_WORKFLOW.md
SUBSCRIPTION_TIER_SYSTEM.md
DATABASE_ARCHITECTURE.md
SYSTEM_ARCHITECTURE.md
UI_UX_GUIDELINES.md
```

---

# Development Philosophy

---

# 1. Stability Over Speed

AI wajib memprioritaskan:

* maintainability,
* readability,
* operational stability.

---

# Forbidden Shortcut

Tidak boleh:

* quick hack,
* temporary dirty patch,
* duplicated workaround,
* atau “asal jalan”.

---

# 2. Modular Development

Semua implementation wajib:

* modular,
* domain-based,
* reusable,
* dan responsibility-scoped.

---

# Rule

Satu module:

* satu tanggung jawab utama.

---

# Forbidden Structure

Tidak boleh:

* giant utility chaos,
* god file,
* atau mixed operational domains.

---

# 3. Anti-Orphan Principle

AI wajib menghindari:

* orphan routes,
* orphan components,
* orphan services,
* orphan styles,
* orphan API endpoints.

---

# Required Cleanup Rule

Jika:

* feature dihapus,
* workflow diganti,
* module dipindahkan,

maka AI wajib:

* membersihkan dependency lama,
* membersihkan imports,
* membersihkan dead code.

---

# 4. No Duplicate Logic

AI wajib:

* reuse logic,
* reuse services,
* reuse validation flow.

---

# Forbidden Behavior

Tidak boleh:

* duplicate validation,
* duplicate schedule logic,
* duplicate permission checks,
* duplicate notification flow.

---

# Example Bad Practice

```text
attendance_validation_v2()
attendance_validation_new()
attendance_validation_fixed()
```

---

# Required Practice

Gunakan:

* centralized service,
* reusable validation,
* shared workflow engine.

---

# Architecture Rules

---

# 1. Respect Layer Boundaries

Frontend:

* UI only.

Backend:

* business logic authority.

Database:

* persistence layer.

---

# Forbidden Architecture Behavior

Tidak boleh:

* business logic di frontend,
* permission validation di UI saja,
* atau hidden logic di component.

---

# 2. Service Layer Mandatory

Business logic wajib:

* centralized di service layer.

---

# Rule

Controllers/API handlers tidak boleh:

* menjadi tempat logic kompleks.

---

# Required Flow

```text
Route/API
→ Service Layer
→ Repository/Data Access
→ Database
```

---

# 3. Permission Validation Must Be Backend-Enforced

Frontend visibility:

* bukan security.

---

# Rule

Semua:

* permissions,
* subscriptions,
* branch scope,
* academy scope

WAJIB divalidasi backend.

---

# Multi-Tenant Rules

---

# 1. Academy Isolation Is Sacred

AI wajib memastikan:

* tidak ada cross academy leakage.

---

# Required Scope Validation

Semua query wajib mempertimbangkan:

```text
academy_id
branch_id
```

---

# Forbidden Query Behavior

Tidak boleh:

* global unsafe query,
* unrestricted joins,
* atau hidden bypass scope.

---

# 2. Branch Scope Must Be Explicit

Branch-level operations wajib:

* branch-aware,
* permission-aware.

---

# Rule

Jangan menggunakan:

* implicit default branch,
* hidden fallback branch,
* atau global operational assumptions.

---

# Scheduling Rules

---

# 1. Scheduling Engine Is Sensitive

Scheduling adalah:

* critical operational system.

---

# Rule

Semua perubahan scheduling wajib:

* conflict-aware,
* auditable,
* realtime-aware.

---

# Forbidden Scheduling Behavior

Tidak boleh:

* silent overwrite,
* direct schedule mutation,
* bypass validation,
* atau hidden reschedule.

---

# Required Validation

Selalu cek:

* teacher conflict
* room conflict
* student overlap
* branch collision

---

# UI/UX Rules

---

# 1. Respect Role Identity

Setiap dashboard wajib:

* mengikuti karakter role.

---

# Forbidden UI Behavior

Tidak boleh:

* semua dashboard terlihat sama,
* copy-paste dashboard antar role,
* atau admin-style overload untuk parent.

---

# 2. Mobile-First Mandatory

AI wajib memprioritaskan:

* mobile usability.

---

# Required Mobile Priorities

* teacher attendance
* parent monitoring
* notifications
* schedule access

---

# 3. Anti-Chaos UI

AI wajib menghindari:

* popup berlebihan,
* nested modal,
* noisy UI,
* visual clutter,
* inconsistent spacing.

---

# Forbidden UI Pattern

Tidak boleh:

* dashboard penuh tabel,
* action button random,
* inconsistent status color,
* atau hidden operational flow.

---

# Naming Convention Rules

---

# 1. Naming Must Be Predictable

Gunakan:

* descriptive naming,
* consistent naming,
* dan domain-aware naming.

---

# Examples

Good:

```text
schedule_conflict_service
teacher_workload_validator
attendance_summary_card
```

Bad:

```text
helper2
utils_new
finalFixComponent
temporaryHandler
```

---

# 2. Avoid Version Chaos

Tidak boleh:

* v2
* final
* final_fix
* latest_new

---

# Required Refactor Behavior

Refactor:

* replace old system,
* jangan menumpuk system baru di samping lama.

---

# File Structure Rules

---

# Rule

Semua file wajib:

* domain-grouped,
* readable,
* maintainable.

---

# Forbidden Structure

Tidak boleh:

* giant folder dumping,
* mixed unrelated files,
* component chaos.

---

# Required Structure

```text
modules/
  scheduling/
  attendance/
  invoices/
  notifications/
```

---

# Realtime Rules

---

# 1. Realtime Must Be Scoped

Realtime updates wajib:

* permission-aware,
* branch-aware,
* academy-aware.

---

# Forbidden Behavior

Tidak boleh:

* unrestricted broadcast,
* global socket leak,
* duplicate realtime events.

---

# Audit Rules

---

# 1. Critical Actions Must Be Auditable

Semua perubahan penting wajib:

* memiliki actor,
* timestamp,
* previous state,
* new state.

---

# Required Audit Areas

* schedule changes
* attendance edits
* invoice changes
* role changes
* subscription changes

---

# Performance Rules

---

# 1. Avoid Heavy Rendering

AI wajib menghindari:

* giant page rendering,
* unnecessary rerender,
* duplicated fetch.

---

# Required Optimization Areas

* schedules
* notifications
* dashboards
* analytics

---

# 2. Avoid Massive Payloads

API responses wajib:

* scoped,
* paginated,
* efficient.

---

# Forbidden API Behavior

Tidak boleh:

* giant payload default,
* full dashboard preload tanpa kebutuhan,
* atau nested overfetch.

---

# Database Rules

---

# 1. Respect Database Architecture

AI wajib mengikuti:

* naming conventions,
* relational structure,
* audit fields,
* indexing philosophy.

---

# Forbidden Database Behavior

Tidak boleh:

* duplicate tables,
* inconsistent naming,
* unsafe joins,
* hardcoded IDs.

---

# Documentation Rules

---

# 1. Significant Changes Must Update Docs

Jika AI:

* mengubah workflow,
* menambah module,
* mengubah architecture,

maka documentation wajib diperbarui.

---

# Required Documentation Updates

* README
* architecture docs
* role docs
* workflow docs
* API docs

---

# Refactor Rules

---

# 1. Refactor Must Reduce Chaos

Refactor harus:

* memperjelas system,
* mengurangi duplication,
* meningkatkan maintainability.

---

# Forbidden Refactor

Tidak boleh:

* refactor kosmetik,
* rename chaos,
* atau menambah abstraction tanpa manfaat jelas.

---

# Error Handling Rules

---

# Rule

Error handling wajib:

* human-readable,
* operationally useful,
* dan traceable.

---

# Forbidden Error Behavior

Tidak boleh:

* silent failure,
* raw exception exposure,
* atau hidden operational crash.

---

# Testing Rules

---

# Required Testing Areas

* scheduling
* permissions
* attendance
* subscriptions
* notifications
* branch isolation

---

# AI Validation Checklist

Sebelum finalize implementation,
AI wajib mengecek:

```text
[ ] No duplicate logic
[ ] No orphan files
[ ] Mobile-first respected
[ ] Branch scope validated
[ ] Academy scope validated
[ ] Permissions backend-enforced
[ ] Scheduling validation intact
[ ] Notification flow safe
[ ] Audit logging preserved
[ ] UI consistency maintained
```

---

# Forbidden AI Emergency Behavior

AI dilarang:

* membuat quick dirty patch,
* bypass architecture,
* hardcode permissions,
* menambah hidden dependency,
* atau mengorbankan maintainability demi speed.

---

# Final AI Agent Statement

AI agents adalah:

* implementation assistants,
* bukan architecture authority.

Semua implementation wajib:

* mengikuti dokumen pondasi,
* menjaga operational stability,
* menjaga maintainability,
* menjaga scalability,
* dan mengurangi chaos jangka panjang.
