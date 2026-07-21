# Product Requirements Document: AI-Native Agency ATS

**Document Status:** Draft  
**Target Markets:** United States (US), United Kingdom (UK), European Union (EU)  
**System Classification:** High-Risk AI System (EU AI Act Annex III, Point 4a)  
**Deployment Model:** Cloud-Native, Multi-Tenant B2B SaaS  
**Foundational AI Engine:** External LLM APIs (OpenAI, Anthropic) via PII-Redacted Middleware  
**Timeline:** 6 months to GA  
**File:** deepseek-ats-ai.md (Final PRD)

---

## 1. Executive Summary & Product Vision

### 1.1 Executive Summary

The AI-Native Agency ATS is a cloud-based, multi-tenant applicant tracking system purpose-built for external recruitment and staffing agencies serving the US, UK, and EU markets. The platform centralizes candidate intake from multiple recruiters and sourcing channels, provides a unified workspace for requisitions, submissions, outreach, interviews, and placements, and embeds AI assistance into high-leverage workflows.

AI functions exclusively as decision support — all candidate ranking and shortlist decisions require human approval. Recruitment AI that screens, ranks, or selects candidates is classified as high-risk under the EU AI Act (Annex III, Point 4a), so the product embeds governance, transparency, logging, and human oversight as first-class platform capabilities from day one.

The first release targets a 6-month GA timeline. It excludes direct employer self-service and external integrations (job boards, HRIS, calendar sync) but includes candidate-facing AI features, CRM-style sourcing and outreach, and full EU AI Act compliance readiness for US/UK/EU launch.

### 1.2 Product Vision

Create the operating system for modern staffing agencies: one platform where recruiters can source, manage, engage, and submit candidates at scale with AI assistance, while keeping humans in control of hiring decisions. The system should make recruiters faster, candidate management cleaner, and compliance evidence easier to produce.

### 1.3 Core Value Propositions

- **Recruiter Efficiency:** Reduce candidate preparation and submission time from ~45 minutes per submission to under 5 minutes.
- **Speed to Submittal:** Accelerate time-to-first-submittal for new client job requisitions by 50% using semantic matching and AI summarization.
- **Candidate Transparency:** Provide candidates with AI-generated profile summaries, AI-driven job recommendations, and clear disclosure about how AI processes their data.
- **Turnkey Compliance:** Deliver EU AI Act high-risk compliance controls out of the box for EU operations, with CCPA/CPRA and UK GDPR alignment.

---

## 2. Product Principles

- **Human approval is mandatory** for any AI-supported ranking or shortlist export.
- **Tenant data must be isolated** by design — no cross-tenant data leakage.
- **Candidate experience must be transparent** when AI is used.
- **Compliance and auditability are product requirements**, not post-launch add-ons.
- **Recruiter speed and usability** outweigh feature breadth in the first release.
- **AI recommendations must be visually distinguishable** from final decisions.
- **Override reasons must be captured** when a recruiter changes an AI ranking.
- **No automated rejection** — AI cannot reject or auto-select candidates.

---

## 3. Target Personas

| Persona | Description | Primary Goals |
|---------|-------------|---------------|
| **Account Manager (Recruiter)** | Handles business development, clients, and jobs. Reviews shortlists and presents to clients. | Creates job requisitions, manages client portals, tracks placements and fees. |
| **Sourcer (Recruiter)** | Finds and engages candidates. Eliminates manual data entry and scales outreach. | Daily driver of CRM workflows, AI parsers, and outreach drafting. |
| **Candidate** | Job seeker who creates a profile, uploads a resume, receives communications, and tracks application status | Transparent application tracking, control over personal data, respectful AI disclosure, relevant job recommendations |
| **Organization (Client)** | Client company that posts job requirements, reviews submitted candidates, and provides feedback | Frictionless candidate evaluation, access to candidate summaries, feedback on submitted candidates |
| **Agency Admin** | Configures tenants, users, permissions, compliance settings, templates, and reporting | Multi-tenant user management, RBAC, LLM token cost control, compliance audit logs |

---

## 4. Feature Matrix: Core vs. AI-Native Features

### 4.1 Core Features (System Foundation)

#### 4.1.1 Multi-Tenant Platform
- Tenant-level isolation via Row-Level Security (RLS) on PostgreSQL
- Role-Based Access Control (RBAC) for Recruiter, Admin, and Read-Only Client roles
- Tenant-isolated S3 storage buckets with dedicated encryption keys
- Full audit logs for all access, edits, submissions, approvals, and exports
- Single-branded UI at launch (no tenant-level white-labeling in v1)

#### 4.1.2 Candidate Management
- Candidate profile creation and enrichment from resume uploads (PDF, DOCX, TXT)
- Hosted career pages and job widgets for basic inbound candidate intake
- Deduplication across resumes, emails, phone numbers, and linked candidate records
- Structured timeline for applications, submissions, interviews, feedback, and placements
- Document store for resumes, cover letters, certifications, and work history
- Candidate self-service portal: profile management, status tracking, consent management

#### 4.1.3 Job & Requisition Management
- Client job intake forms with structured requirement fields
- Requirement capture: role, skills, location, compensation, visa status, urgency, deal terms
- Requisition lifecycle tracking (Open → In Progress → Submitted → Filled → Closed)
- Client-specific submission and approval stage configuration

#### 4.1.4 Submission & Workflow Management
- Shortlist creation with candidate submission packages
- Interview stage tracking and feedback collection
- Offer, placement, and closure workflow
- Placement & fee tracking: commission calculations, fee percentages, guarantee period tracking
- Rejection and recycle workflows for future opportunities

#### 4.1.5 Recruiter CRM & Outreach
- Candidate and prospect sourcing lists
- Outreach templates and sequence management
- Activity tracking for calls, emails, follow-ups, and placements
- Relationship history for candidates, clients, and hiring managers

#### 4.1.6 Client Portal (Read-Only)
- View submitted candidate packages with AI-generated summaries
- Review candidate availability, match context, and summaries
- Provide feedback on submitted candidates
- Track requisition progress and shortlist status
- Secure magic-link authentication with OTP/secondary verification

#### 4.1.7 Search & Reporting
- Search by skill, location, compensation, availability, visa, seniority, and source
- Standard dashboards: pipeline health, submissions, response rates, time-to-submit, time-to-fill
- Recruiter productivity dashboards
- Exportable reports for agency and client review

### 4.2 AI-Native Features (LLM API-Powered)

#### 4.2.1 Resume Parsing & Profile Normalization
- Extract structured data from resumes, CVs, and candidate forms
- Normalize titles, skills, employers, tenure, and education
- Identify missing fields and prompt candidates or recruiters for completion
- Candidate contact details redacted for agency compliance

#### 4.2.2 AI-Generated Candidate Profile Summaries
- Generate recruiter-friendly summaries of candidate history, strengths, and fit
- Create job-specific candidate briefs for submission to organizations
- Candidate-facing summaries visible in the candidate portal
- Summarize interview feedback and candidate communications

#### 4.2.3 AI-Driven Job Recommendations
- **Passive recommendations:** Surface relevant open requisitions to passive candidates in the candidate portal
- **Active matching:** Compare candidate profiles against job requirements to produce explainable fit signals and gap summaries
- Recommendations are suggestions only — final matching decisions remain with the recruiter

#### 4.2.4 AI Match Support & Ranking
- Semantic comparison of candidate profiles against job requirements
- Generate explainable fit scores with contributing factor breakdowns
- Rank candidates for recruiter review only — never auto-select or auto-reject
- Gap analysis highlighting missing skills or experience relative to the role
- **Human approval gate:** Per-shortlist approval required before export/submission to client
- **Override logging:** Recruiter changes to AI rankings must be captured with reason

#### 4.2.5 AI Outreach Assistance
- Draft personalized candidate outreach messages
- Suggest follow-up timing and response-aware next steps
- Generate job-specific outreach variants for different talent pools
- Suggest next actions and pipeline refinements

#### 4.2.6 AI Assistant for Recruiters
- Natural-language query over candidates and jobs
- Suggested search refinements and pipeline actions
- Draft notes, submission blurbs, and interview questions

#### 4.2.7 PII Privacy Shield Middleware
All external LLM requests pass through a local, non-logging microservice:

1. **NER & Regex Filter:** Automatically redacts names, email addresses, phone numbers, physical addresses, dates of birth, and demographic identifiers
2. **Payload Anonymization:** Replaces PII with contextual tokens (`[CANDIDATE_NAME_1]`, `[PHONE_NUMBER_1]`)
3. **LLM Execution:** Sends anonymized prompt context to foundational LLM APIs with Zero Data Retention (ZDR) enterprise agreements
4. **Token Re-hydration:** Re-injects candidate data locally into generated outputs where necessary
5. **Side-by-side verification UI:** Recruiters can view original CV alongside redacted version to catch and correct false positives (Scunthorpe problem mitigation)

```
[ Raw Candidate CV / Notes ]
            │
            ▼
┌───────────────────────────────┐
│ Local PII Redaction Layer     │  ← Strips names, phone, email, addresses
└───────────┬───────────────────┘
            │ (Anonymized Tokens)
            ▼
┌───────────────────────────────┐
│ External Foundational LLM API │  ← OpenAI / Anthropic (Enterprise ZDR API)
└───────────┬───────────────────┘
            │ (Generated Text)
            ▼
┌───────────────────────────────┐
│ Local Re-hydration & Rendering│  ← Re-applies agency templates & branding
└───────────────────────────────┘
```

---

## 5. Candidate-Facing AI Features (v1)

Three candidate-facing AI features are in scope for the first release, accessible through the Candidate Self-Service Portal:

### 5.1 AI-Generated Profile Summaries
- Candidates see an AI-generated summary of their own profile (strengths, key skills, experience highlights)
- Summary updates automatically when resume or profile data changes
- Candidates can request regeneration or flag inaccuracies
- Clear disclosure that the summary was AI-generated

### 5.2 AI-Driven Job Recommendations
- Candidates see recommended open requisitions based on their profile
- Recommendations are passive suggestions — candidates express interest, recruiters manage the matching process
- Candidates see fit signals (e.g., "Your skills match 8 of 12 requirements")
- Recruiters see which candidates expressed interest in which roles

### 5.3 AI Disclosure & Consent
- Clear notices explaining when and how AI is used in profile processing and matching
- Consent workflows for AI-assisted processing where required (GDPR/UK GDPR)
- Right-to-explanation: one-click reports explaining AI evaluation criteria
- No automated rejection — human decision always required

---

## 6. EU AI Act Annex III Compliance Architecture

The platform is classified as a **High-Risk AI System** under Annex III, Point 4(a) of the EU AI Act (Regulation 2024/1689). The following framework is implemented:

```
                      EU AI ACT COMPLIANCE FRAMEWORK
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                  Phase 1: Prohibited AI Safeguards (Art. 5)                 │
 │  • Emotion Detection Banned  • Biometric Profiling Disabled                 │
 │  • No Automated Rejection or Auto-Selection                                 │
 ├─────────────────────────────────────────────────────────────────────────────┤
 │               Phase 2: Provider Technical Requirements                      │
 │  • Article 9: Risk Management System & Matrix                               │
 │  • Article 10: Data Governance & Bias Testing (4/5ths Rule Audits)          │
 │  • Article 11 & 12: Technical Documentation & Audit Logs (6-month min)     │
 │  • Article 13 & 14: Human-in-the-Loop UI & Mandatory Overrides             │
 │  • Article 15: Prompt Injection Defenses & Robustness Validation            │
 ├─────────────────────────────────────────────────────────────────────────────┤
 │                   Phase 3: Deployer (Agency) Enablement                     │
 │  • Candidate AI Disclosure Templates  • Article 86 Right-to-Explanation    │
 │  • Candidate Rights Workflows (Access, Correction, Deletion, Portability)  │
 └─────────────────────────────────────────────────────────────────────────────┘
```

### 6.1 Comprehensive Compliance Checklist

#### 6.1.1 Governance & Documentation
- [ ] Maintain a written AI risk management process
- [ ] Keep technical documentation for each AI-assisted feature
- [ ] Define intended use, limitations, performance metrics, and residual risks per feature
- [ ] Maintain an approved model inventory and provider register
- [ ] Conduct conformity assessment before EU market deployment
- [ ] Register high-risk AI system in EU AI database

#### 6.1.2 Prohibited Practices Controls (Article 5)
- [ ] Zero emotion recognition: architectural exclusion of video/facial emotion detection or voice stress analysis
- [ ] No biometric categorization: prevention of automated categorization based on protected characteristics (race, gender, religion, political affiliation)
- [ ] No automated rejection or auto-selection: rejection actions require explicit, recorded human confirmation

#### 6.1.3 Data Governance (Article 10)
- [ ] Use representative, relevant, and quality-controlled training/operational data
- [ ] Check for duplicates, outliers, and obvious label errors
- [ ] Document data sources, preprocessing steps, and data lineage
- [ ] Establish periodic bias testing (4/5ths rule disparate impact analysis)
- [ ] No training or fine-tuning on customer candidate data without explicit contractual and technical controls

#### 6.1.4 Logging & Traceability (Article 12)
- [ ] Immutable pseudonymized logging of all AI interactions: prompts, raw outputs, match scores, recruiter overrides
- [ ] Logs pseudonymized using contextual tokens to support GDPR targeted deletion (Right to be Forgotten) while maintaining EU AI Act traceability requirements
- [ ] Logs retained for mandatory minimum of 6 months
- [ ] Logs searchable by tenant, requisition, user, and candidate
- [ ] Timestamped records of all human approval/rejection decisions
- [ ] Audit trail for every AI recommendation → human decision flow

#### 6.1.5 Human Oversight (Article 14)
- [ ] Human approval required before any shortlist submission or candidate ranking export
- [ ] AI recommendations visually distinct from final decisions
- [ ] Recruiters can override, ignore, or modify AI suggestions without penalty
- [ ] Override reasons captured and logged when recruiter changes an AI ranking
- [ ] Clear override and escalation paths for contested recommendations
- [ ] Recruiters trained on AI system limitations and proper use

#### 6.1.6 Transparency & Candidate Rights (Articles 13, 26, 86)
- [ ] Disclose to candidates when AI assists with profile processing or matching
- [ ] Explain purpose and type of AI support used in candidate-facing notices
- [ ] Provide understandable AI disclosure in candidate portal and email templates
- [ ] Right to explanation: one-click automated report explaining candidate evaluation criteria
- [ ] Candidate access, correction, objection, deletion, and portability workflows
- [ ] Complaint intake and case tracking for AI-related concerns

#### 6.1.7 Accuracy, Robustness & Cybersecurity (Article 15)
- [ ] Input sanitization to block candidate CV prompt injection exploits
- [ ] Rate-limit and secure all AI API calls to external providers
- [ ] Output validation before downstream workflow use
- [ ] Confidence indicators on AI-generated outputs
- [ ] Safe fallback when AI provider is unavailable
- [ ] Model drift monitoring and periodic accuracy evaluation
- [ ] Zero Data Retention (ZDR) agreements with all foundation model providers

#### 6.1.8 Post-Market Monitoring
- [ ] Track incidents, escalations, adverse outputs, and model regressions
- [ ] Review AI system performance by tenant and workflow
- [ ] Maintain rollback procedures for problematic model versions
- [ ] Periodic bias and fairness monitoring
- [ ] Regular vendor review for all AI API providers
- [ ] Incident response plan for AI system failures

---

## 7. Privacy & Security Requirements

### 7.1 Data Protection
- **GDPR** ready: consent workflows, lawful basis processing, data subject access requests
- **UK GDPR** alignment for UK launch
- **CCPA/CPRA** aware data handling for US customers
- Data retention controls by tenant, geography, and record type
- Automated deletion workflows per retention policy
- Right to be forgotten: full data erasure within 24 hours of verified request

### 7.2 Infrastructure Security
- TLS 1.2+ encryption in transit, AES-256 encryption at rest
- Tenant-isolated S3 buckets with dedicated KMS encryption keys per enterprise tenant
- Postgres Row-Level Security (RLS) enforcing tenant_id on every query
- Secrets management for all API keys and credentials
- Incident response and breach notification procedures

### 7.3 Operational Security
- SOC 2 Type II compliance target
- Regular penetration testing and vulnerability scanning
- SSO/SAML readiness (Okta, Azure AD) for roadmap
- Rate limiting and abuse prevention on all API endpoints

---

## 8. Non-Functional Requirements

| Category | Requirement |
|----------|-------------|
| **Availability** | 99.9% uptime SLA for production |
| **Latency** | Page load <200ms, CRUD ops <100ms, semantic search <500ms |
| **AI Inference** | Resume parsing <2s, matching/ranking <1s, summary generation <3s |
| **Scalability** | Auto-scaling for high-volume staffing ingestion |
| **Architecture** | API-first design for future integration roadmap |
| **Observability** | Centralized logging, metrics, and traces across AI and non-AI workflows |
| **Multi-Region** | Deployment readiness for US, UK, and EU data residency |

---

## 9. Out of Scope for v1

- Direct employer self-service (agency administrators manage client relationships)
- Production integrations with external ATS, job boards, calendars, or HRIS
- AI-assisted chatbot/Q&A for candidates
- Tenant-level white-labeling (custom branding per agency)
- Full interview scheduling engine
- Salary prediction
- Interview transcription and summarization
- Automated background checks
- Public job board distribution

These items are planned for the post-launch roadmap.

---

## 10. Milestones & Delivery Plan

### Phase 1: Core Platform (Months 1–3)

**Deliverables:**
- Multi-tenant infrastructure with PostgreSQL RLS and tenant-isolated storage
- Authentication, RBAC (Recruiter, Admin, Read-Only Client roles), admin console
- Candidate profiles with resume upload and ingestion (PDF, DOCX, TXT)
- Job/requisition management with structured requirement capture
- Kanban pipeline management with configurable stages
- Submission workflow with shortlist creation
- Basic search (keyword, skill, location, status)
- Document storage for resumes, notes, and submission packages
- Audit logging for all core actions

**Milestone:** Internal alpha at end of Month 2

### Phase 2: CRM & Candidate-Facing AI (Months 3–4)

**Deliverables:**
- AI resume parsing and profile normalization
- AI candidate profile summaries (recruiter-facing and candidate-facing)
- Sourcing lists and prospect tracking
- Outreach templates and sequence management
- Activity tracking (calls, emails, follow-ups)
- Relationship history across candidates and client contacts
- Recruiter notes and collaboration features
- Client feedback capture workflow

**Milestone:** Beta release at end of Month 4

### Phase 3: AI Matching & Client Portal (Months 4–5)

**Deliverables:**
- AI-driven job recommendations (passive candidate recommendations in portal + active matching)
- AI match support with explainable fit scores and gap analysis
- Candidate ranking with per-shortlist human approval gate
- Override reason capture when recruiter changes AI rankings
- AI outreach drafting assistance
- Read-only client portal with magic-link authentication
- Client candidate review, feedback, and submission tracking
- AI disclosure notices in candidate portal and recruiter workflows

**Milestone:** Client portal + AI matching deployed at end of Month 5

### Phase 4: Compliance Hardening & GA Readiness (Months 5–6)

**Deliverables:**
- Full EU AI Act governance implementation
- Immutable audit logging with 6-month retention
- Bias monitoring and disparate impact analysis (4/5ths rule)
- Prompt injection defenses and output validation
- Candidate rights workflows (access, correction, deletion, portability)
- Right-to-explanation automated report generation
- Post-market monitoring and incident tracking
- Conformity assessment documentation
- Performance optimization and multi-region readiness
- Security hardening and penetration testing

**Milestone:** GA release at end of Month 6

---

## 11. Architectural Principles

### 11.1 Multi-Tenant Data Isolation

- **Logical separation:** Row-Level Security (RLS) on PostgreSQL — every query enforces `tenant_id` context
- **Asset isolation:** Candidate resumes, PDFs, and attachments stored in tenant-isolated S3 buckets with dedicated KMS keys
- **Candidate ownership:** Database rules prevent candidate contact information leakage across agency clients and safeguard recruiter candidate ownership periods

### 11.2 AI Architecture

- **External LLM APIs only:** OpenAI, Anthropic via secure API integration — no self-hosted models
- **No training on customer data:** Explicit contractual and technical controls prevent provider training on candidate data
- **PII privacy shield:** All LLM requests pass through local NER/regex redaction layer before reaching external APIs
- **Provider abstraction:** Common interface for swapping/adding LLM providers
- **Zero Data Retention (ZDR):** Enterprise agreements with all providers

### 11.3 API-First Design

- RESTful API for all core entities (candidates, jobs, applications, users)
- GraphQL readiness for complex query patterns
- Webhook event system for roadmap integration triggers
- Rate limiting, authentication, and monitoring on all endpoints

---

## 12. Key Performance Indicators (KPIs)

| Metric Category | Target KPI | Business Impact |
|----------------|------------|-----------------|
| **Operational Efficiency** | <5 min per client submission package (from 45 min) | 88% reduction in administrative candidate prep time |
| **Pipeline Velocity** | 50% decrease in time-to-first-submittal | Faster client response, higher placement win rate |
| **Client Engagement** | >75% client portal review rate within 24 hours | Faster feedback loops from client hiring managers |
| **AI Accuracy** | >92% accuracy on CV parsing and PII redaction | Reduced human correction effort, zero data leaks |
| **AI Adoption** | >60% AI recommendation acceptance or edit rate | High recruiter trust and workflow integration |
| **Compliance** | 100% audit log completeness, 0 non-compliance flags | Full operational safety across US/UK/EU markets |
| **Recruiter Throughput** | 2x increase in candidates processed per week | Direct productivity ROI for agency customers |

---

## 13. Risk Assessment & Mitigation

| Risk | Mitigation |
|------|------------|
| **Over-automation (Automation Bias)** — AI suggestions treated as decisions | Human approval gate on every shortlist export; override logging; visual distinction of AI outputs; UX friction enforcing manual edit or confirmation of low-confidence AI assertions |
| **Sourced Candidate Consent** — Passively sourced candidates (e.g., manual LinkedIn PDF uploads) processed without consent | System holds data locally; blocks LLM routing until initial outreach email establishes legal basis/consent |
| **Bias Measurement Paradox** — PII redacted during LLM matching, making real-time bias monitoring on individual predictions infeasible | Statistical bias monitoring conducted offline on aggregated pseudonymized datasets, separate from live AI processing pipeline |
| **Compliance gap** — EU AI Act requirements missed | Compliance-by-design from day one; dedicated compliance phase (M5–6); external audit readiness |
| **Data contamination** — Cross-tenant data leakage | RLS on every query; tenant-isolated storage; dedicated KMS keys per enterprise tenant |
| **Model quality drift** — AI accuracy degrades over time | Periodic bias and quality monitoring; model drift detection; retrain/fallback procedures |
| **User adoption** — Recruiters reject AI workflows | AI as decision support only; override without penalty; focus on recruiter speed UX |
| **LLM provider outage** — AI features unavailable | Safe fallback behavior; graceful degradation; output caching where safe |
| **Prompt injection** — Candidate CV manipulation of AI matching | Input sanitization; output validation; rate limiting; anomaly detection on matching patterns |

---

## 14. Open Questions for Next Iteration

- Which candidate data sources beyond resume upload and recruiter entry are mandatory for post-launch roadmap?
- Which countries need localization beyond USA, UK, and EU in subsequent releases?
- What default retention periods should apply per tenant and geography?
- Which LLM providers should be approved at launch beyond OpenAI and Anthropic?
- What integrations (job boards, HRIS, calendar, email) should be prioritized first on the roadmap?

---

## 15. Success Criteria for v1

- Core ATS operational with multi-tenant isolation, RBAC, candidate management, and submission workflows
- Three candidate-facing AI features deployed: profile summaries, job recommendations, and disclosure/consent
- AI match support with human approval gate and override logging operational
- CRM sourcing and outreach features functional
- Read-only client portal deployed
- EU AI Act high-risk compliance controls implemented and auditable
- Zero critical compliance findings in pre-launch audit
- Platform deployable in US, UK, and EU regions with appropriate data handling

---

*This document represents the formally approved product requirements for the 6-month v1 of the AI-Native Agency ATS. All features, compliance controls, and milestones described above are committed scope for the GA release.*
