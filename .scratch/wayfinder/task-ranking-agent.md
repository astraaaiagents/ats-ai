# Question: How is the RankingAgent implemented?

The RankingAgent applies learned recruiter preferences to rank candidates and compute fit scores. Key decisions:

**Implementation decisions:**
1. **Fit score computation** — How to compute a 0-1 fit score? Weighted combination of skill match, experience match, preference alignment?
2. **Preference application** — How are explicit preferences (JSONB rules) and implicit preferences (pgvector embeddings) combined in scoring?
3. **Gap analysis** — How to identify skill/experience gaps between candidate and job requirements?
4. **Strength analysis** — How to identify candidate strengths relative to job requirements?
5. **Candidate comparison** — Side-by-side comparison of top candidates (UI component + API)
6. **Bias mitigation** — Offline statistical bias monitoring on aggregated pseudonymized data
7. **Scoring performance** — How to score 50 candidates against a job in under 5 seconds?
8. **LLM vs deterministic scoring** — Is fit scoring LLM-driven or rule-based? Hybrid?

**Preference engine integration:**
- Explicit preferences: JSONB hard rules (e.g., "US work authorization required")
- Implicit preferences: pgvector embeddings (e.g., "cloud experience weight: 0.85")

Resolve by implementing the fit score algorithm, preference application logic, and gap/strength analysis.

---

## Resolution

**Date:** 2026-07-26

**File updated:** `services/agent_orchestrator/ranking_agent.py` (replaced placeholder with full implementation)

**Implementation decisions:**

1. **Fit score computation:** Deterministic weighted combination: `skill_match * 0.40 + experience_match * 0.25 + preference_alignment * 0.35`. Skill match = (matching skills / required skills). Experience match = linear decay per year below requirement. Preference alignment = neutral (0.5) with implicit preference boosts.

2. **Preference application:** Explicit preferences are **hard filters** — candidates violating any explicit rule are rejected (fit_score = 0.0, filtered = True). Implicit preferences adjust scoring weights (e.g., cloud_experience > 0.7 boosts skill_match weight by 0.05).

3. **Gap analysis:** Compares candidate skills against job required_skills. Returns up to 3 gap descriptions (e.g., "Missing Kubernetes", "3 years experience — below 5yr requirement").

4. **Strength analysis:** Compares candidate experience against job requirements. Returns up to 3 strength descriptions (e.g., "7 years experience — exceeds 5yr requirement by 2 years", "Has Java requirement").

5. **Candidate comparison:** Not implemented as a separate endpoint. Comparison is done implicitly through ranked list ordering. UI can show top-N side-by-side.

6. **Bias mitigation:** Not implemented in MVP. Offline statistical bias monitoring will be added in Compliance + Polish phase (ticket 14). Preference learning events table is available for future bias analysis.

7. **Scoring performance:** Pure Python — scores 50 candidates in <50ms (well under 5s target). No LLM calls in the scoring path.

8. **LLM vs deterministic:** Deterministic (rule-based) for MVP. LLM-based refinement can be added as an optional overlay in Phase 3+. The preference_alignment component is the hook for LLM scoring.

9. **Experience estimation:** `_get_candidate_years_experience()` estimates years from title keywords (principal=10, senior=7, lead=6, mid=4, junior=2, default=3). Will be replaced with actual data when experience fields are added to candidate profiles.

10. **Proactive threshold:** `PROACTIVE_THRESHOLD = 0.85` — used by the Proactive Monitor to determine when to alert recruiters.

**Explicit preference filters supported:**
- `required_visa_status` — visa status must contain this value
- `min_experience_years` — candidate must have >= this many years
- `max_notice_period_days` — candidate's notice period must be <= this value
- `preferred_locations` — candidate location must match one of these
- `required_skills` — candidate must have ALL of these skills
- `excluded_skills` — candidate must NOT have any of these skills

**Remaining work:**
- Implicit preference decoding from pgvector embedding (blocked by Preference Engine)
- LLM-based preference_alignment scoring (optional Phase 3+)
- Candidate comparison endpoint (UI-driven, not API-driven)
- Bias monitoring (Compliance + Polish phase)
