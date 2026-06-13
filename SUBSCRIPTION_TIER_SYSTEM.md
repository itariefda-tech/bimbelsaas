# Premium Multi-Branch Academic Operations Platform

---

# Purpose

Dokumen ini mendefinisikan:

* SaaS subscription architecture,
* academy billing structure,
* feature gating system,
* premium addon system,
* subscription lifecycle,
* dan monetization rules platform.

Platform adalah:

* multi-tenant SaaS,
* multi-branch academic platform,
* dan subscription-based operational ecosystem.

---

# Core Subscription Philosophy

---

# 1. Subscription Must Feel Premium

Subscription bukan sekadar:

* pembayaran akses aplikasi.

Subscription adalah:

* hubungan jangka panjang,
* operational partnership,
* dan premium service experience.

---

# Rule

Billing experience harus:

* jelas,
* profesional,
* predictable,
* dan trustworthy.

---

# Forbidden Subscription Experience

Tidak boleh:

* confusing pricing,
* hidden feature restrictions,
* surprise limitations,
* atau unclear upgrade behavior.

---

# 2. Multi-Branch Is Default

Semua subscription plan:

* sudah support multi-branch.

---

# Rule

Single branch academy:

* dianggap implementasi sederhana dari multi-branch architecture.

---

# Forbidden Pricing Structure

Tidak boleh:

* biaya tambahan hanya karena multi-branch enabled.

---

# 3. Feature Gating Must Be Predictable

Semua feature limitation wajib:

* jelas,
* transparan,
* dan mudah dipahami.

---

# Rule

Feature gating tidak boleh:

* random,
* hidden,
* atau inconsistent.

---

# SaaS Subscription Structure

---

# Platform Hierarchy

```text id="g8eqov"
Platform Owner
└── Academy Subscription
    ├── Branch Operations
    ├── Teacher Operations
    ├── Student Access
    └── Parent Experience
```

---

# Subscription Types

Platform memiliki 2 level monetization:

---

# 1. Academy Subscription

Academy membayar:

* akses platform utama.

---

# 2. Premium Addon Subscription

Student/parent dapat membeli:

* fitur tambahan tertentu.

---

# Academy Subscription Philosophy

Academy subscription mencakup:

* operasional academy,
* branch management,
* scheduling,
* invoicing,
* parent monitoring,
* dan teacher workflow.

---

# Academy Subscription Goals

Academy harus merasa:

* platform membantu operasional,
* bukan membebani operasional.

---

# Suggested Academy Plans

---

# Starter

Cocok untuk:

* academy kecil,
* operational sederhana.

---

# Suggested Features

* multi branch enabled
* basic scheduling
* attendance system
* parent dashboard
* invoicing
* basic reports

---

# Professional

Cocok untuk:

* growing academy,
* banyak teacher,
* banyak branch.

---

# Suggested Features

* advanced scheduling
* advanced analytics
* realtime operations
* advanced parent experience
* branch comparison
* operational alerts

---

# Enterprise

Cocok untuk:

* large academy,
* franchise education network,
* operationally complex institution.

---

# Suggested Features

* advanced analytics
* AI assistant
* operational automation
* custom branding
* advanced reporting
* dedicated operational tools

---

# Subscription Scope Rules

Academy subscription berlaku untuk:

* seluruh branch academy.

---

# Rule

Subscription tidak dihitung:

* per branch.

---

# Branch Independence Rule

Walaupun:

* billing academy centralized,

operasional branch tetap:

* independen,
* isolated,
* dan branch-scoped.

---

# Premium Addon System

---

# Philosophy

Addon adalah:

* optional enhancement,
* bukan mandatory access.

---

# Example Premium Addons

* cross branch student access
* advanced parent analytics
* premium reports
* AI academic assistant
* enhanced notifications
* advanced scheduling features

---

# Cross Branch Student Addon

---

# Core Rule

Default student:

* hanya memiliki home branch access.

---

# Premium Upgrade

Student dapat membeli:

* cross branch access addon.

---

# Cross Branch Addon Includes

* class enrollment lintas branch
* cross branch schedules
* premium teacher access
* advanced academy flexibility

---

# Billing Responsibility

Cross branch addon:

* dibayar oleh parent/student.

---

# Feature Gating System

---

# Core Rule

Feature access wajib:

* tier-aware,
* permission-aware,
* dan academy-aware.

---

# Required Feature Validation

Semua premium feature wajib:

* tervalidasi backend,
* tidak hanya frontend hidden UI.

---

# Forbidden Feature Behavior

Tidak boleh:

* hidden premium activation,
* accidental access leak,
* frontend-only restriction.

---

# Suggested Feature Categories

---

# Basic Features

Always included:

* schedules
* attendance
* class management
* invoicing
* parent dashboard

---

# Premium Features

Require:

* higher tier,
* addon,
* atau enterprise access.

---

# Example Premium Features

* advanced analytics
* AI insights
* branch comparison dashboard
* smart notifications
* advanced reports

---

# Subscription Lifecycle

---

# Academy Subscription Lifecycle

```text id="lznnzt"
Trial
→ Active
→ Grace Period
→ Suspended
→ Archived
```

---

# Status Definitions

## Trial

Limited trial access.

---

## Active

Normal operational access.

---

## Grace Period

Temporary operational continuation after unpaid subscription.

---

## Suspended

Restricted operational access.

---

## Archived

Academy inactive and archived.

---

# Grace Period Rules

Grace period bertujuan:

* menghindari operational disruption mendadak.

---

# Recommended Grace Period

```text id="8w7k1z"
7 - 14 days
```

---

# During Grace Period

Academy masih dapat:

* melihat data,
* menjalankan operasional terbatas,
* menyelesaikan payment.

---

# Suspension Rules

Saat suspended:

* operational editing dibatasi,
* tetapi critical data masih readable.

---

# Rule

Platform tidak boleh:

* langsung menghapus data academy.

---

# Subscription Expiration Rules

Jika subscription expired:

* academy masuk suspended mode.

---

# Suspended Mode Behavior

Allowed:

* limited visibility
* payment actions
* subscription renewal

---

# Blocked Actions

Blocked:

* new schedules
* new invoice generation
* operational modification

---

# Billing Architecture

---

# Core Billing Separation

Platform wajib memisahkan:

---

# 1. SaaS Billing

```text id="m8o5sx"
Academy
↔ Platform
```

Untuk:

* subscription platform,
* addons,
* premium access.

---

# 2. Academic Billing

```text id="b4vjlwm"
Parent
↔ Academy
```

Untuk:

* tuition,
* modules,
* class fees,
* operational education payment.

---

# Rule

SaaS billing dan academic billing:

* wajib terisolasi.

---

# Payment Methods

Suggested support:

* bank transfer
* virtual account
* e-wallet
* payment gateway

---

# Invoice Philosophy

Invoice harus:

* professional,
* premium,
* dan easy to understand.

---

# Required Invoice Data

* invoice number
* academy identity
* student identity
* branch
* due date
* payment status
* payment history

---

# Branding Rules

---

# Academy Branding

Academy dapat:

* upload logo
* set theme colors
* customize academy identity

---

# Rule

Branding tidak boleh:

* merusak UI consistency,
* merusak readability,
* atau membuat chaotic interface.

---

# White Label Philosophy

Enterprise tier dapat support:

* custom branding,
* domain customization,
* premium identity.

---

# Suggested White Label Features

* custom domain
* academy logo
* academy theme
* academy welcome page

---

# Operational Limitation Philosophy

Platform tidak boleh terasa:

* restrictive,
* hostile,
* atau manipulative.

---

# Rule

Limitations harus:

* operationally reasonable,
* transparan,
* dan fair.

---

# Subscription Notification Rules

---

# Required Subscription Notifications

* upcoming renewal
* payment success
* payment failure
* grace period warning
* expiration warning

---

# Notification Priority

## High Priority

* suspension warning
* expiration warning

---

## Medium Priority

* renewal reminder

---

## Low Priority

* promotional information

---

# Analytics Rules

---

# Platform Analytics

Platform Owner dapat melihat:

* MRR
* active academies
* churn rate
* addon usage
* feature adoption

---

# Academy Analytics

Academy Director dapat melihat:

* branch performance
* parent engagement
* operational consistency
* teacher workload

---

# Subscription Security Rules

Subscription validation wajib:

* backend validated,
* realtime-aware,
* audit-logged.

---

# Forbidden Security Behavior

Tidak boleh:

* bypass subscription validation,
* hidden feature unlock,
* or frontend-only gating.

---

# AI Agent Rules

AI-generated implementation wajib:

* mengikuti feature gating,
* mengikuti subscription lifecycle,
* tidak bypass billing validation,
* dan tidak membuat hidden premium logic.

---

# Forbidden AI Behaviors

AI agents dilarang:

* hardcode premium access,
* bypass addon validation,
* membuat inconsistent gating,
* atau mengabaikan subscription state.

---

# Final Subscription Foundation Statement

Subscription system adalah:

* fondasi sustainability platform,
* fondasi monetization,
* dan fondasi long-term scalability.

Semua implementation wajib:

* transparan,
* predictable,
* secure,
* scalable,
* dan premium dalam experience.
