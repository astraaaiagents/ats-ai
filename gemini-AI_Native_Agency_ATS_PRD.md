# Product Requirements Document (PRD)
## Multi-Tenant AI-Native Cloud ATS for Recruitment & Staffing Agencies

**Document Status:** Approved for Engineering & Product Architecture  
**Target Markets:** United States (US), United Kingdom (UK), European Union (EU)  
**System Classification:** High-Risk AI System (EU AI Act Annex III, Point 4a)  
**Deployment Model:** Cloud-Native, Multi-Tenant B2B SaaS  
**Foundational AI Engine:** External LLM APIs (OpenAI, Anthropic) via PII-Redacted Middleware  

---

## 1. Executive Summary & Product Vision

### 1.1 Executive Summary
The Next-Gen Agency Applicant Tracking System (ATS) is an AI-native B2B SaaS platform engineered specifically for external recruitment, staffing, and executive search agencies. Traditional legacy ATS platforms rely on rigid keyword searches, manual resume reformatting, and fragmented communication tools that impose severe administrative overhead on agency recruiters.

This platform integrates foundational Large Language Model (LLM) APIs (OpenAI GPT-4o, Anthropic Claude 3.5 Sonnet) directly into high-leverage agency workflows. By wrapping all external model requests in a strict **PII Redaction Privacy Shield**, the software automates candidate reformatting, executive pitch generation, job intake parsing, and semantic matching while maintaining compliance with the **EU AI Act (Annex III)**, **GDPR**, and **US privacy standards**.

### 1.2 Core Value Proposition & Objectives
* **Agency Efficiency:** Reduce candidate preparation and client submission time by over 70% (from 45 minutes per submission to under 5 minutes).
* **Speed to Submittal:** Accelerate time-to-first-submittal for new client job requisitions by 50% using semantic retrieval-augmented generation (RAG).
* **White-Labeled Client Experience:** Provide staffing clients with an interactive, high-touch portal that accelerates candidate feedback and interview scheduling.
* **Turnkey Regulatory Compliance:** Deliver full compliance out of the box for high-risk HR AI regulations across the US, UK, and EU markets.

---

## 2. Key Personas & System Users

| Persona | Primary Needs & Goals | Core System Interaction |
| :--- | :--- | :--- |
| **Agency Recruiter & Account Manager** | Fast candidate sourcing, instant CV reformatting to agency branding, automated client pitching, candidate ownership tracking. | Daily management of Kanban pipelines, candidate intake, automated outreach, and client submission packages. |
| **Agency Client (Hiring Manager)** | Frictionless candidate evaluation, instant access to candidate summaries, 1-click interview request/approval. | Interactive White-Labeled Client Portal (no complex password requirements, secure magic link access). |
| **Candidate** | Transparent application tracking, control over personal data, easy self-scheduling, and respectful AI disclosure. | Candidate Self-Service Portal (GDPR data rights, interview calendar selection, status updates). |
| **Agency Administrator** | Multi-tenant user management, billing/placement metrics, LLM token cost control, compliance audit logging. | Admin Console (Role-Based Access Control [RBAC], tenant customization, LLM usage caps, bias audit reports). |

---

## 3. System Architecture & Regulatory Guardrails

### 3.1 Multi-Tenant Data Isolation Strategy
* **Logical Data Separation:** Implemented via Row-Level Security (RLS) on PostgreSQL database clusters. Every query enforces `tenant_id` context.
* **Asset Isolation:** Candidate resumes, branded PDFs, and client attachments are stored in tenant-isolated S3 buckets with dedicated KMS encryption keys per enterprise tenant.
* **Candidate Ownership Protection:** Strict database rules prevent candidate contact information leakage across agency clients and safeguard recruiter candidate ownership periods.

### 3.2 Privacy-First LLM Middleware (The PII Privacy Shield)
All external LLM requests pass through a local, non-logging microservice before reaching third-party APIs (OpenAI / Anthropic):
1. **Named Entity Recognition (NER) & Regex Filter:** Automatically redacts names, email addresses, phone numbers, physical addresses, dates of birth, and demographic identifiers.
2. **Payload Anonymization:** Replaces PII with contextual tokens (e.g., `[CANDIDATE_NAME_1]`, `[PHONE_NUMBER_1]`).
3. **LLM Execution:** Sends anonymized prompt context to foundational LLM APIs with zero data retention enabled (Zero Data Retention [ZDR] enterprise agreements).
4. **Token Re-hydration:** Re-injects candidate data locally into generated outputs where necessary (e.g., generating final client-ready PDFs).

```
[ Raw Candidate CV / Notes ]
            │
            ▼
┌───────────────────────────────┐
│ Local PII Redaction Layer     │  <-- Strips names, phone, email, addresses
└───────────┬───────────────────┘
            │ (Anonymized Tokens)
            ▼
┌───────────────────────────────┐
│ External Foundational LLM API │  <-- OpenAI / Anthropic (Enterprise ZDR API)
└───────────┬───────────────────┘
            │ (Generated Text)
            ▼
┌───────────────────────────────┐
│ Local Re-hydration & Rendering│  <-- Re-applies agency templates & branding
└───────────────────────────────┘
```

---

## 4. Feature Matrix: Core vs. Agency AI-Native Features

### 4.1 Core Agency Features (System Foundation)
* **Candidate & Client CRM:** Centralized database for managing client companies, client contacts, job requisitions, and candidate records.
* **Customizable Kanban Pipelines:** Visual stage tracking per job requisition (e.g., Sourced -> Screened -> Client Submitted -> Interviewing -> Offer Extended -> Placed).
* **Agency PDF Engine:** Manual and template-driven generation of agency-branded resumes with header/footer customization and watermark enforcement.
* **Email & Calendar Integrations:** Native bi-directional sync with Microsoft Outlook / Office 365 and Google Workspace.
* **Placement & Commission Tracking:** Financial ledger recording fee percentages, candidate start dates, split recruiter commissions, and guarantee period tracking.

### 4.2 AI-Native Features (LLM API Powered)

#### A. Automated Agency Reformatting Engine
* **Functionality:** Ingests candidate CVs in any format (PDF, DOCX, TXT) and parses raw unstructured text into structured JSON.
* **LLM Capability:** Automatically restructures work history, standardizes job titles, cleans formatting inconsistencies, corrects grammar, and formats skills matrices.
* **Agency Scrubbing:** Automatically redacts candidate contact details to prevent client "backdoor hiring" and formats the document into the agency's custom layout in under 10 seconds.

#### B. AI Executive Pitch Generator
* **Functionality:** Generates a concise, high-impact 3-bullet executive synthesis for client submissions.
* **LLM Capability:** Compares candidate CV experience against the specific client job requisition. Highlights key achievements, match percentage, and specific reasons why the candidate fits the client's culture and technical requirements.

#### C. Call-to-Req Intake Engine
* **Functionality:** Converts raw client intake notes or recorded call transcripts into structured job requisitions.
* **LLM Capability:** Extracts required hard/soft skills, salary range, seniority level, core responsibilities, and interview process steps to draft a complete job posting.

#### D. Semantic RAG Search & Candidate Rediscovery
* **Functionality:** Natural language querying across the internal agency database to surface passive talent and "silver medalists" (previous strong candidates).
* **LLM Capability:** Utilizes vector embeddings (pgvector / Pinecone) combined with hybrid keyword search. Allows queries such as: *"Find me Senior Full-Stack Engineers with Fintech experience who were interviewed in the last 6 months."*

#### E. Blind Submission & Anonymization Engine
* **Functionality:** Supports diversity and inclusion initiatives by stripping bias indicators from client presentation packages.
* **LLM Capability:** Removes names, gender pronouns, graduation years, location indicators, and ethnic markers while retaining core technical competencies and impact metrics.

---

## 5. EU AI Act Annex III Compliance Architecture

Because the platform is classified as a **High-Risk AI System** under Annex III, Point 4(a) of the EU AI Act (Regulation 2024/1689), the platform implements the following compliance framework:

```
                          EU AI ACT COMPLIANCE FRAMEWORK
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                      Phase 1: Prohibited AI Safeguards                      │
 │  • Emotion Detection Banned  • Biometric Profiling Disabled                 │
 ├─────────────────────────────────────────────────────────────────────────────┤
 │                  Phase 2: Provider Technical Requirements                   │
 │  • Article 9: Risk Management System & Matrix                               │
 │  • Article 10: Data Governance & Bias Testing (4/5ths Rule Audits)          │
 │  • Article 11 & 12: Technical Documentation & 6-Month System Audit Logs     │
 │  • Article 13 & 14: Human-in-the-Loop UI & Mandatory Overrides              │
 │  • Article 15: Prompt Injection Defenses & Robustness Validation            │
 ├─────────────────────────────────────────────────────────────────────────────┤
 │                   Phase 3: Deployer (Agency) Enablement                     │
 │  • Candidate AI Disclosure Templates  • Article 86 Right-to-Explanation     │
 └─────────────────────────────────────────────────────────────────────────────┘
```

### 5.1 Prohibited Practices Controls (Article 5)
* **Zero Emotion Recognition:** Strict architectural exclusion of video/facial emotion detection or voice stress analysis tools.
* **No Biometric Categorization:** Prevention of automated categorization based on protected characteristics (race, gender, religion, political affiliation).

### 5.2 Technical & Operational Obligations
* **Human-in-the-Loop (HITL) Guarantee (Article 14):** AI serves exclusively as a decision-support system. **Automated auto-rejections are strictly blocked.** Rejection actions require explicit, recorded human confirmation.
* **Prompt Injection Defenses (Article 15):** Input sanitation blocks candidate CV prompt injection exploits (e.g., hidden text designed to manipulate AI matching scores).
* **Audit Logging & Traceability (Article 12):** All AI interactions (prompts, raw outputs, match scores, recruiter overrides) are stored in immutable audit logs for a mandatory minimum of **6 months**.
* **Candidate Disclosure & Right to Explanation (Articles 26 & 86):** Candidate-facing portals include automated notifications disclosing AI usage, alongside one-click automated report generation explaining candidate evaluation criteria.

---

## 6. Detailed Development Roadmap & Milestones

```
   Phase 1 (M1-3)            Phase 2 (M4-6)            Phase 3 (M7-9)           Phase 4 (M10-12)
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│ Multi-Tenant     │ ────>│ Privacy Shield   │ ────>│ White-Labeled    │ ────>│ EU AI Act &      │
│ Base & Core ATS  │      │ & AI Sourcing    │      │ Client Portal    │      │ Global Compliance│
└──────────────────┘      └──────────────────┘      └──────────────────┘      └──────────────────┘
```

### Phase 1: Multi-Tenant Architecture & Core Agency Engine (Months 1–3)
* **Deliverables:**
  * Multi-tenant infrastructure setup with PostgreSQL Row-Level Security (RLS).
  * Role-Based Access Control (RBAC) for Recruiter, Account Manager, and Admin roles.
  * Core CRM, Candidate Database, and Kanban Pipeline Management.
  * Agency PDF Template Engine for manual resume reformatting.
  * Basic job posting distribution and manual candidate application intake.

### Phase 2: Privacy Shield & AI Sourcing Engine (Months 4–6)
* **Deliverables:**
  * Deployment of local PII Redaction Middleware and foundational LLM API gateway (OpenAI / Anthropic).
  * Automated AI Candidate Resume Reformatting & Scrubbing engine.
  * AI Executive Pitch Generator for client submissions.
  * Vector Database implementation (pgvector) for natural language semantic search across candidate databases.
  * Call-to-Req Intake Engine for automated job description creation.

### Phase 3: White-Labeled Client Portal & Automated Scheduling (Months 7–9)
* **Deliverables:**
  * Interactive, white-labeled client presentation portal with magic-link authentication.
  * 1-click candidate review, feedback collection, and video snippet presentation.
  * Automated candidate self-scheduling engine integrated with Outlook and Google calendars.
  * Anonymized Blind Submission toggle for agency client presentations.

### Phase 4: Compliance Framework, Analytics & Enterprise Features (Months 10–12)
* **Deliverables:**
  * Implementation of full EU AI Act compliance suite (audit logs, prompt injection safeguards, bias reporting).
  * Candidate AI disclosure notifications and Article 86 Right-to-Explanation tool.
  * Advanced agency business intelligence: Recruiter activity metrics, time-to-submittal analytics, fee forecasting, and LLM token usage controls.
  * Final pre-market CE Marking, conformity assessment, and EU AI Database registration.

---

## 7. Key Performance Indicators (KPIs) & Success Metrics

| Metric Category | Target KPI | Business Impact |
| :--- | :--- | :--- |
| **Operational Efficiency** | < 5 minutes per client submission package (from 45 mins) | 88% reduction in administrative candidate prep time. |
| **Pipeline Velocity** | 50% decrease in Time-to-First-Submittal | Faster client response time, increasing agency placement win rate. |
| **Client Engagement** | > 75% client portal review rate within 24 hours | Faster feedback loops from client hiring managers. |
| **Platform Precision** | > 92% accuracy on CV parsing and PII redaction | Reduced human correction effort and zero data leak incidents. |
| **Regulatory Compliance** | 100% audit log completeness & 0 non-compliance flags | Full operational safety across US, UK, and EU markets. |