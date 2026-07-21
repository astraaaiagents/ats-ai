<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# direct employer self-service is not in first version.

first release to include candidate-facing AI features.
For matching and ranking, the system should provide only decision support with human approval.
product  should include CRM-style sourcing and outreach features.
integrations are in roadmapΩsnd not for launch scope.
For compliance,  I treat the EU AI Act checklist as high-risk recruitment AI.
create a single PRD markdown document with milestones

I’ve drafted the PRD content and structured it around your scope: agency-first, multi-tenant, AI decision support only, CRM-style sourcing/outreach, and EU AI Act high-risk controls. I also incorporated the launch constraint that direct employer self-service and external integrations are out of scope for version 1, while candidate-facing AI is included.[^1][^2][^3][^4][^5]

## PRD content

# Product Requirements Document (PRD)

## Product Summary

**Product name:** AI-native ATS for recruitment and staffing agencies

**Target customers:** External recruitment agencies, staffing firms, and multi-client talent teams serving USA, UK, and EU markets.

**Release intent:** A cloud-based, multi-tenant applicant tracking system that centralizes candidate intake from multiple sources, supports recruiter-led submission workflows, and uses AI as decision support with human approval. Recruitment AI for screening, ranking, or selection falls within the EU AI Act high-risk recruitment scope, so the product must be designed for governance, transparency, logging, and human oversight from the start.[^3][^5][^1]

## Goals

- Consolidate candidate records from multiple recruiter and sourcing channels into one system.
- Help recruiters manage requisitions, submissions, outreach, interviews, and placements at scale.
- Use AI to accelerate sourcing, parsing, matching, summarization, and candidate communication while keeping a human in the loop.
- Support client-by-client data segregation, configurable workflows, and auditability for agency operations.
- Launch compliant in USA, UK, and EU markets with high-risk recruitment AI controls for the EU.


## Non-goals

- Direct employer self-service in version 1.
- End-to-end autonomous hiring decisions.
- Production integrations with external ATS, job boards, calendars, or HRIS in launch scope.
- Any use of AI to make final hiring decisions without human review.


## Personas

### Recruiter

Agency user who sources candidates, manages pipelines, communicates with candidates, and submits shortlists to organizations.

### Candidate

Job seeker who creates a profile, uploads a resume, applies or is sourced, and tracks status and communication.

### Organization

Client company with job requirements, interview feedback, shortlist approval, and hiring outcome ownership.

### Agency Admin

Configures tenants, users, permissions, compliance settings, templates, and reporting.

## Product Principles

- Human approval for all AI-assisted candidate ranking and recommendations.
- Tenant isolation by default.
- Candidate experience must be transparent about AI usage.
- Compliance-by-design for regulated recruitment AI workflows.
- Fast recruiter workflow beats feature breadth in the first version.


## Core Features

### 1. Multi-tenant foundation

- Tenant-level separation for agency clients, teams, and permissions.
- Role-based access control for recruiter, manager, admin, and read-only client roles.
- Data partitioning for candidate pools, requisitions, notes, templates, and reports.
- Audit logs for all access, edits, submissions, approvals, and exports.


### 2. Candidate management

- Candidate profile creation and enrichment from resume uploads.
- Deduplication across resumes, emails, phone numbers, and linked candidate records.
- Structured timeline for applications, submissions, interviews, feedback, and placements.
- Document store for resumes, cover letters, certifications, and work history.


### 3. Job and requisition management

- Organization job intake forms.
- Requirement capture for role, skills, location, compensation, visa, urgency, and deal terms.
- Requisition lifecycle from open to filled or closed.
- Client-specific approval and submission stages.


### 4. Recruiter CRM and outreach

- Candidate and prospect sourcing lists.
- Outreach sequences using email templates and recruiter notes.
- Activity tracking for calls, emails, follow-ups, and placements.
- Relationship history for candidates, clients, and hiring managers.


### 5. Submission and workflow management

- Shortlist creation and candidate submission packages.
- Interview stage tracking and feedback collection.
- Offer, placement, and closure workflow.
- Rejection and recycle workflows for future opportunities.


### 6. Search and reporting

- Search by skill, location, compensation, availability, visa, seniority, and source.
- Standard operational dashboards for pipeline health, submissions, response rates, time-to-submit, time-to-fill, and recruiter productivity.
- Exportable reports for agency and client review.


## AI Features

### 1. Resume parsing and profile normalization

- Extract structured data from resumes, CVs, and candidate forms.
- Normalize titles, skills, employers, tenure, and education.
- Identify missing fields and prompt candidates or recruiters for completion.


### 2. AI match support

- Compare candidate profiles against job requirements.
- Produce explainable fit signals and gap summaries.
- Surface top candidates for recruiter review only; never auto-select or auto-reject.


### 3. AI candidate summarization

- Generate recruiter-friendly summaries of candidate history and strengths.
- Create job-specific candidate briefs for submission to organizations.
- Summarize interview feedback and candidate communications.


### 4. AI outreach assistance

- Draft personalized candidate outreach messages.
- Suggest follow-up timing and response-aware next steps.
- Generate job-specific outreach variants for different talent pools.


### 5. AI assistant for recruiters

- Natural-language query over candidates and jobs.
- Suggested search refinements and pipeline actions.
- Draft notes, submission blurbs, and interview questions.


### 6. AI governance layer

- AI disclosure prompts in candidate portal and recruiter workflows.
- Human approval checkpoints for recommendations and rankings.
- Immutable logs of prompts, outputs, edits, approval decisions, and timestamps.
- Model/provider abstraction for OpenAI, Anthropic, and future providers via secure APIs.


## Candidate Experience

- Create profile manually or from resume upload.
- See status of applications and recruiter communications.
- Consent and disclosure for AI-assisted processing where required.
- Edit profile, upload documents, and manage availability.
- Receive interview and submission notifications.


## Organization Experience

- View submitted candidate packages.
- Review summaries, availability, and match context.
- Give feedback on submitted candidates.
- Track requisition progress and shortlist status.


## Functional Requirements

- Support batch and single candidate ingestion.
- Support duplicate detection and merge workflow.
- Support configurable requisition stages by client or tenant.
- Support candidate submissions with attachment bundles and notes.
- Support recruiter team collaboration on shared roles.
- Support configurable retention and deletion policies.
- Support multi-region deployment readiness for USA, UK, and EU data handling.


## Non-functional Requirements

- Availability target: 99.9% or higher for production.
- Encryption in transit and at rest.
- Tenant-isolated storage and access controls.
- Scalable ingestion for high-volume staffing use cases.
- API-first architecture for future integrations.
- Observability with logs, metrics, and traceability across AI and non-AI workflows.


## AI System Requirements

- Use foundation models only through secure API integrations.
- No training or fine-tuning on customer data without explicit contractual and technical controls.
- Prompt and response logging for auditability.
- Output confidence indicators and explanation snippets.
- Safe fallback when AI output is unavailable.
- Bias and quality monitoring on model-assisted match and ranking workflows.


## EU AI Act High-Risk Compliance Checklist

Recruitment AI used for screening, ranking, or selecting candidates is high-risk under the EU AI Act Annex III point 4, so the product must implement the following controls.[^5][^1][^3]

### Governance and documentation

- Maintain a written AI risk management process.
- Keep technical documentation for AI-assisted features.
- Define intended use, limitations, performance metrics, and residual risks.
- Maintain an approved model inventory and provider register.


### Data governance

- Use representative, relevant, and quality-controlled data.
- Check for duplicates, outliers, and obvious label errors.
- Document data sources and preprocessing steps.
- Establish periodic bias and quality testing.


### Logging and traceability

- Log model inputs, outputs, user actions, approvals, and overrides.
- Retain decision records for audit and dispute handling.
- Make logs searchable by tenant, requisition, user, and candidate.


### Human oversight

- Require human approval before shortlist submission or candidate ranking export.
- Provide clear override and escalation paths.
- Make AI recommendations clearly distinguishable from final decisions.
- Allow recruiters to ignore or modify AI suggestions without penalty.


### Transparency

- Disclose to candidates when AI assists with profile processing or matching.
- Explain the purpose and type of AI support used.
- Provide understandable candidate notices in the portal and email templates.


### Accuracy, robustness, and cybersecurity

- Monitor AI quality, drift, and failure modes.
- Rate-limit and secure all AI calls to external providers.
- Protect against prompt injection and data exfiltration.
- Validate outputs before downstream workflow use.


### User and candidate rights support

- Support access, correction, objection, deletion, and portability workflows.
- Support complaint intake and case tracking.
- Support records needed for regulatory response.


### Post-market monitoring

- Track incidents, escalations, adverse outputs, and model regressions.
- Review performance by tenant and workflow.
- Maintain rollback procedures for problematic models.


## Privacy and Security Checklist

- GDPR-ready consent and lawful basis workflows for EU operations.
- UK GDPR alignment for UK launch.
- CCPA/CPRA-aware data handling for USA customers.
- Data retention controls by tenant and record type.
- Security review for secrets management, access logging, and incident response.
- Vendor review for all AI API providers.


## Milestones

### Phase 0: Discovery and design

- Finalize workflows, permission model, tenant model, and data schema.
- Define compliance architecture and AI usage boundaries.
- Validate candidate, recruiter, and organization journeys.


### Phase 1: Core platform

- Build authentication, tenant isolation, RBAC, audit logs, and admin setup.
- Launch candidate profiles, resume ingestion, job requisitions, and pipeline management.
- Deliver basic search, tagging, notes, and document storage.


### Phase 2: AI-assisted workflows

- Add resume parsing, candidate summaries, and requirement extraction.
- Add AI match support with human review.
- Add AI drafting for outreach and submission notes.
- Add AI logging, disclosure, and approval gates.


### Phase 3: CRM and agency operations

- Add outreach sequences, activity tracking, and client collaboration features.
- Add shortlist management and submission pack generation.
- Add reporting dashboards for agency operations.


### Phase 4: Compliance hardening and scale

- Complete EU AI Act control implementation and validation.
- Add monitoring, drift checks, and post-market review workflows.
- Harden security, performance, and multi-region readiness.
- Prepare for roadmap integrations with job boards, calendars, email, and external ATS systems.


## Success Metrics

- Time to shortlist reduced for recruiters.
- Increased recruiter throughput per week.
- Improved response rate on outreach.
- Reduced manual parsing and data entry time.
- AI-assisted recommendations accepted or edited by recruiters at a high rate.
- Zero critical compliance findings in launch audits.


## Open Questions

- Which candidate data sources are mandatory for version 1 beyond resume upload and recruiter entry.
- Which countries need localization in the first launch wave beyond USA, UK, and EU.
- What level of client visibility should organizations receive in version 1.
- Which AI providers will be approved at launch and what regional routing is required.
- What retention defaults should apply per tenant and geography.

If you want, I can now convert this into a cleaner “ship-ready” PRD format with a one-page executive summary, detailed MVP scope, and a release plan by quarter.
<span style="display:none">[^10][^6][^7][^8][^9]</span>

<div align="center">⁂</div>

[^1]: https://artificialintelligenceact.eu/what-the-act-means-for-staffing-businesses/

[^2]: https://www.leonar.app/for-agencies/

[^3]: https://www.hunton.com/insights/legal/the-impact-of-the-eu-ai-act-on-human-resources-activities

[^4]: https://www.leonar.app/features/ats-for-agencies/

[^5]: https://www.deepinspect.ai/blog/eu-ai-act-for-hr

[^6]: https://treegarden.io/blog/eu-ai-act-recruitment-compliance-guide/

[^7]: https://ariahr.ai/blog/eu-ai-act-hiring-compliance

[^8]: http://ada-journal.org/index.php/ada/article/download/24/25

[^9]: https://blindstairs.com/resources/eu-ai-act-guide/

[^10]: https://www.cooperhire.io/blog/recruiting-under-the-eu-ai-act

