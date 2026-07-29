# Research: What Embedding Model Should We Use?

**Date:** 2026-07-26
**Context:** Agent-First AI-Native Recruiter Client Portal
**Decision:** PRD chose OpenAI text-embedding-3-small (1536-dim) via AI Middleware Gateway

---

## Executive Summary

**Recommendation: CONFIRM the PRD's choice of OpenAI text-embedding-3-small.**

For IT skill matching in a staffing context, OpenAI text-embedding-3-small provides the best balance of accuracy, cost, and operational simplicity. The 1536 dimensions work well with pgvector. At 50K candidates with weekly re-embedding, the monthly cost is ~$1-2 — negligible compared to the value of accurate skill matching.

---

## 1. Accuracy Comparison

**Verdict: OpenAI text-embedding-3-small is competitive. Cohere embed-english-v3 is comparable. Local models lag for this use case.**

**MTEB (Massive Text Embedding Benchmark) rankings for semantic search:**
- **OpenAI text-embedding-3-small:** ~63-64% on MTEB semantic search aggregate
- **Cohere embed-english-v3:** ~64-65% on MTEB semantic search aggregate (slightly better)
- **Sentence Transformers all-mpnet-base-v2:** ~62% on MTEB semantic search
- **Sentence Transformers all-MiniLM-L6-v2:** ~59% on MTEB (5x faster, good quality tradeoff)

For **IT skill matching specifically**, the differences are marginal because:
- All models capture semantic similarity well for technical terms ("Python", "Kubernetes", "React")
- The bottleneck is not the embedding model — it's the hybrid search strategy (vector + keyword + structured filters)
- Skill names are relatively short and well-defined, which all models handle well

**Bottom line:** Cohere is marginally better on benchmarks, but the difference is negligible for IT skill matching. OpenAI's model is more than good enough.

---

## 2. Cost Comparison

**Verdict: OpenAI text-embedding-3-small is cheap at scale. All options are affordable for MVP.**

| Model | Cost per 1,000 embeddings | Monthly cost (50K candidates, weekly re-embed) |
|-------|--------------------------|------------------------------------------------|
| **OpenAI text-embedding-3-small** | $0.02 | ~$1-2 |
| **OpenAI text-embedding-3-large** | $0.13 | ~$7-13 |
| **Cohere embed-english-v3** | ~$0.025 (similar tier) | ~$1-2 |
| **Sentence Transformers (local)** | $0 (free) | Hosting cost (~$50/mo GPU) |

**At 500K candidates with daily re-embedding:**
- OpenAI 3-small: ~$30/mo
- Cohere v3: ~$30/mo
- Local GPU: ~$200-500/mo (GPU hosting) + engineering time

For the MVP's scale, embedding costs are negligible. The cost advantage of local models only matters at very large scale (millions of embeddings/day).

---

## 3. Dimensionality

**Verdict: 1536-dim is sufficient. Higher dimensions don't meaningfully improve skill matching.**

| Model | Dimensions | pgvector Impact |
|-------|-----------|-----------------|
| **OpenAI text-embedding-3-small** | 1536 | ~300MB for 50K vectors; ~3GB for 500K |
| **OpenAI text-embedding-3-large** | 3072 | ~600MB for 50K vectors; ~6GB for 500K |
| **Cohere embed-english-v3** | 1024 | ~200MB for 50K vectors; ~2GB for 500K |
| **Sentence Transformers all-mpnet-base-v2** | 768 | ~150MB for 50K vectors; ~1.5GB for 500K |

Higher dimensions increase:
- Storage requirements (linearly)
- HNSW index size (linearly)
- Query latency (marginally — more dimensions = slightly more computation)

For skill matching, 1536 dimensions is more than sufficient. The marginal accuracy gain from 3072 dimensions (text-embedding-3-large) does not justify the 2x storage cost.

---

## 4. Update Frequency

**Verdict: Weekly re-embedding is sufficient. Event-driven on candidate update is better.**

**Recommended strategy:**
- **Event-driven:** Re-embed when a candidate's skills/profile is updated (via resume upload, profile edit, or parsing)
- **Periodic batch:** Weekly re-embedding of all candidates to pick up any model updates or profile drift
- **Not real-time:** Candidate profiles change infrequently (daily/weekly at most)

This means:
- 50K candidates × weekly re-embedding = 50K API calls/week = ~12K/day = trivial for OpenAI's rate limits
- Event-driven re-embedding adds ~10-50 API calls/day during active recruiting — negligible

---

## 5. Local vs API

**Verdict: API (OpenAI) is the right choice for MVP. Local only if cost becomes significant.**

**API (OpenAI text-embedding-3-small):**
- Pros: No hosting cost, always up-to-date, zero maintenance, via existing AI Middleware Gateway
- Cons: API dependency, small cost at scale

**Local (Sentence Transformers):**
- Pros: Free, no API dependency, full control
- Cons: GPU hosting cost (~$200-500/mo), engineering time to maintain, model updates are your responsibility

For MVP, API is clearly better. The $1-2/mo cost is negligible. Local only makes sense if:
- You exceed OpenAI's rate limits
- You need to embed millions of documents/day
- Data residency requirements prohibit sending embeddings to external APIs

---

## Recommendation

**Confirm the PRD's choice of OpenAI text-embedding-3-small.**

For the recruiter portal:
1. **Use OpenAI text-embedding-3-small (1536-dim)** via the existing AI Middleware Gateway
2. **Re-embed event-driven** — when a candidate's profile/skills change
3. **Weekly batch re-embedding** — catch any drift or model improvements
4. **Monthly cost at 500K candidates:** ~$30/mo — negligible
5. **Re-evaluate local models** only if costs exceed $100/mo or data residency requires it

Cohere embed-english-v3 is a close second (slightly better on benchmarks, lower dimensions) but offers no meaningful advantage for this use case. Staying with OpenAI keeps the stack simpler (one provider for both LLM and embeddings).

---

## Sources

- MTEB (Massive Text Embedding Benchmark) leaderboard — semantic search rankings
- OpenAI embeddings documentation — model specs, pricing, dimensions
- Cohere embeddings documentation — model specs, pricing
- Sentence Transformers documentation — model quality, speed benchmarks
- Hardware sizing — vector storage calculations for pgvector HNSW index
