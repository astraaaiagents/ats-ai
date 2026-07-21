# Product Requirements Document (PRD)
## AI-Native Applicant Tracking System for Staffing Agencies

### Executive Summary
The AI-Native Agency ATS is a cloud-based, multi-tenant B2B platform engineered specifically for external recruitment and staffing agencies serving the USA, UK, and EU markets. It centralizes candidate intake, simplifies pipeline management, and introduces CRM-style sourcing and outreach. By natively embedding Large Language Models (LLMs) via secure APIs, the platform automates administrative tasks—such as resume parsing, candidate summarization, and outreach drafting—drastically reducing time-to-shortlist.

**Crucially, this system treats recruitment AI as High-Risk (EU AI Act Annex III, Point 4).** All AI matching and ranking features act strictly as *decision support systems* and require mandatory human approval. Direct employer self-service is intentionally excluded from Version 1, prioritizing agency recruiter efficiency and secure "Magic Link" client portals for candidate reviews.

### Product Vision
To build the definitive operating system for modern staffing agencies where recruiters can source, engage, and submit candidates at scale with AI assistance, while guaranteeing human oversight, uncompromising data privacy, and global regulatory compliance.

---

### Target Personas

| Persona | Role & Needs | System Interaction |
| :--- | :--- | :--- |
| **Account Manager (Recruiter)** | Handles business development, clients, and jobs. Needs tools to review shortlists and present to clients. | Creates job requisitions, manages client portals, tracks placements and fees. |
| **Sourcer (Recruiter)** | Finds and engages candidates. Needs to eliminate manual data entry and scale outreach. | Daily driver. Uses CRM workflows, AI parsers, and drafts outreach. |
| **Candidate** | Seeks transparency, easy application flows, and fast feedback. | Uses the AI Chatbot for pre-screening/FAQs and views application status via a self-service portal (accommodates general agency onboarding as well as specific jobs). |
| **Organization (Client)** | Needs frictionless access to review submitted candidates, read recruiter summaries, and provide feedback. | Receives secure "Magic Links" (with OTP/secondary verification) to read-only white-labeled submission portals. |
| **Agency Admin** | Manages multi-tenant configurations, user permissions, compliance settings, and audits. | Accesses the Admin Console for RBAC, compliance logs, data residency controls, and retention policies. |

---

### System Architecture: The Unified AI Middleware Gateway
To maintain strict compliance and multi-tenant security, all AI features operate through a centralized **Unified AI Middleware Gateway**:
1. **PII Redaction:** Strips Personally Identifiable Information (names, contact info, protected traits) before sending data to external LLMs. *UX includes side-by-side original vs. parsed resume view to mitigate "Scunthorpe" false-redaction problems.*
2. **Provider Routing:** Securely routes sanitized prompts to foundational LLMs (e.g., OpenAI, Anthropic) under Enterprise Zero-Data-Retention (ZDR) agreements. No self-hosted models are used for NLP tasks.
3. **Audit Logging & GDPR Erasure:** Automatically logs all prompts, AI outputs, and recruiter overrides into a database. Logs are pseudonymized to support GDPR "Right to be Forgotten" (targeted deletion) while satisfying EU AI Act traceability.
4. **Data Sovereignty:** Region-specific data residency ensures EU candidate data remains in the EU or uses valid cross-border transfer mechanisms (Standard Contractual Clauses).
5. **API-First Design:** Core architecture is built RESTful with GraphQL readiness and webhooks for future integrations.

---

### Feature Scope (Version 1)

#### Core Features (Non-AI)
* **Multi-Tenant Foundation:** Logical data separation by agency tenant. Role-Based Access Control (RBAC).
* **Candidate Management:** Profile creation, resume document storage, duplicate detection, and chronological activity timelines. Includes basic inbound channels (hosted career pages/job widgets) to drive volume.
* **Job & Requisition Management:** Client job intake forms, stage tracking, and requirement capture.
* **CRM & Outreach:** Sourcing lists, email sequence templates, and comprehensive communication history tracking, integrated with two-way MS Exchange/Google Workspace sync.
* **Client Submission Workflow:** Shortlist curation and generation of secure "Magic Link" portals (protected by OTP) for clients to review and approve/reject candidates.
* **Placement & Fee Tracking:** Tracking of the final placement stage and basic commission/fee calculations.
* **Reporting:** Dashboards for pipeline health, time-to-submit, and recruiter productivity.

#### Candidate-Facing AI Features
* **AI Chatbot:** Interactive pre-screening and 24/7 candidate FAQ answering.
* **AI-Generated Profile Summaries:** Candidates can view, update, and regenerate an AI-generated summary of their own profile (strengths, key skills).
* **AI-Driven Job Recommendations:** Passive recommendations in the portal where candidates can express interest based on fit signals.
* **AI Disclosure & Consent:** Clear notices explaining when and how AI is used, with a right-to-explanation report.

#### Recruiter-Facing AI Features
* **Resume Parsing & Normalization:** Ingests raw CVs and automatically structures work history, skills, and education.
* **AI Match Support (Decision Support):** Compares candidate profiles to requisitions. Generates fit signals and gap analyses. **Requires human approval for ranking.**
* **AI Candidate Summarization:** Auto-generates recruiter-friendly candidate briefs and client-ready submission notes.
* **AI Outreach Assistance:** Drafts highly personalized, job-specific email and message templates for candidate engagement.

#### Out of Scope for Version 1
* Direct employer/organization self-service platform logins.
* Autonomous AI candidate rejection/selection (Zero auto-rejections).
* Production integrations with external ATS systems, HRIS, or background check providers.

---

### Key Performance Indicators (KPIs)
| Metric Category | Target KPI | Business Impact |
|-----------------|------------|-----------------|
| **Operational Efficiency** | <5 min per client submission package (from 45 min) | 88% reduction in administrative candidate prep time |
| **Pipeline Velocity** | 50% decrease in time-to-first-submittal | Faster client response, higher placement win rate |
| **AI Accuracy** | >92% accuracy on CV parsing and PII redaction | Reduced human correction effort, zero data leaks |
| **AI Adoption** | >60% AI recommendation acceptance or edit rate | High recruiter trust and workflow integration |
| **Compliance** | 100% audit log completeness, 0 non-compliance flags | Full operational safety across US/UK/EU markets |

---

### Product Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| **Over-automation (Automation Bias)** | Human approval gate on every shortlist export; override logging; visual distinction of AI outputs; UX friction enforcing manual edit or confirmation of low-confidence AI assertions. |
| **Sourced Candidate Consent** | For passively sourced candidates (e.g., manual LinkedIn PDF uploads), the system holds data locally and blocks LLM routing until an initial outreach email establishes legal basis/consent. |
| **Bias Measurement Paradox** | Since PII is redacted during LLM matching, statistical bias monitoring is conducted offline on aggregated pseudonymized datasets, separate from the live AI processing pipeline. |
| **Prompt Injection** | Input sanitization; output validation; rate limiting; anomaly detection on candidate CV text. |
| **LLM Provider Outage** | Safe fallback behavior; graceful degradation of AI features; output caching where safe. |
| **Model Quality Drift** | Periodic bias and quality monitoring; model drift detection; retrain/fallback procedures. |

---

### Compliance Checklist (EU AI Act Annex III - High-Risk AI) & GDPR
* [x] **Human Oversight Guarantee (Art 14):** AI serves only as decision support. No automated ranking or rejection. UX friction prevents automation bias.
* [x] **Audit Logging (Art 12) & GDPR Erasure:** Pseudonymized logging of all LLM inputs, outputs, and overrides.
* [x] **Transparency & Disclosure (Art 13):** Candidates are explicitly notified of AI usage and the legal basis (Consent vs. Legitimate Interest).
* [x] **PII & Bias Mitigation (Art 10):** PII redaction gateway and offline statistical bias monitoring.
* [x] **Cybersecurity & Robustness (Art 15):** Prompt injection safeguards. ZDR API agreements.
* [x] **Conformity Assessment & CE Marking (Art 43, 48, 49):** Mandatory system assessment and CE marking prior to EU launch.
* [x] **EU Database Registration (Art 60):** Registration of the AI system in the official EU database.
* [x] **Risk & Quality Management Systems (Art 9, 17):** Establishing continuous risk frameworks and technical documentation.
* [x] **Post-Market Monitoring (Art 61):** Active reporting for incidents or AI malfunctions.

---

### Non-Functional Requirements
| Category | Requirement |
|----------|-------------|
| **Availability** | 99.9% uptime SLA for production |
| **Latency** | Page load <200ms, CRUD ops <100ms, semantic search <500ms |
| **AI Inference** | Resume parsing <2s, matching/ranking <1s, summary generation <3s |
| **Scalability** | Auto-scaling for high-volume staffing ingestion |

---

### Development Milestones

#### Phase 1: Core Foundation & Agency CRM
* **Deliverables:** Multi-tenant DB schema, RBAC, Authentication, Email/Calendar Sync.
* **Features:** Candidate database, hosted career pages, job requisitions, basic CRM sourcing, Placement & Fee tracking.

#### Phase 2: AI Middleware Gateway & Candidate Features
* **Deliverables:** Unified AI Middleware Gateway (with PII Redaction, Pseudonymized Audit Logging, and Data Sovereignty routing).
* **Features:** AI Resume Parsing, Candidate-facing AI Chatbot, AI-Generated Profile Summaries, AI Outreach Drafting.

#### Phase 3: AI Match & Submission Workflows
* **Deliverables:** Client interaction layer and AI Decision Support.
* **Features:** AI Match Support, AI-Driven Job Recommendations, AI Candidate Summarization, Shortlist creation, secure "Magic Link" portals (OTP protected) for client review. 

#### Phase 4: Compliance Hardening & Launch Readiness
* **Deliverables:** EU AI Act compliance validation, security pentesting, final legal sign-offs.
* **Features:** Reporting dashboards, CE Marking, EU database registration, QA of prompt injection defenses, implementation of Post-Market Monitoring plan. Final market launch (US, UK, EU).
