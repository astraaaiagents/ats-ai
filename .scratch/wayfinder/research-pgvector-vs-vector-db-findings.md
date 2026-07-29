# pgvector vs Dedicated Vector Database — Research Findings

**Date:** 2026-07-26
**Context:** Agent-First AI-Native Recruiter Client Portal
**Scale:** ~50K candidates today, scaling to 500K+
**Embedding Model:** OpenAI text-embedding-ada-002 (1536 dimensions)

---

## Executive Summary

**Recommendation: CONFIRM the PRD's choice of pgvector.**

For your scale (50K to 500K candidates), pgvector is the right choice. It delivers sub-10ms latency, eliminates the operational overhead of a separate vector database, and provides native hybrid search via pgvector + pg_trgm/tsvector. A dedicated vector database (Pinecone, Weaviate, Qdrant) only becomes justified at 10M+ vectors, high-write-throughput scenarios (thousands of writes/sec), or when you need horizontal sharding across multiple nodes.

Your use case does not hit any of those thresholds.

---

## 1. pgvector Performance for 50K–500K Candidates

### Verdict: Excellent. No concerns at this scale.

**50K vectors (current):**
- Trivially handled. Even a brute-force cosine similarity scan completes in <5ms on a modest instance.
- HNSW index is optional at this scale but recommended for consistency as data grows.
- RAM requirement: ~300MB for raw vectors + ~1–2GB for HNSW index. Fits in any standard RDS instance.

**500K vectors (target):**
- HNSW index with 1536 dimensions: ~3–6GB RAM for the index alone.
- Expected query latency: <10ms with proper HNSW tuning (`m=16`, `ef_construction=256`, `ef_search=64`).
- A 4 vCPU / 16GB RAM RDS instance handles this comfortably.
- Throughput: hundreds of queries per second (QPS) on a single node.

**Hardware sizing for 500K vectors:**
| Component | Size |
|---|---|
| Raw vectors (500K x 1536 x 4 bytes) | ~3 GB |
| HNSW index (2–4x vector size) | ~6–12 GB |
| pg_catalog + TOAST + WAL | ~2–4 GB |
| **Recommended RAM** | **16–32 GB** |
| **Recommended vCPU** | **4–8** |

At 500K, you are well within pgvector's comfort zone. The index fits in RAM, queries are fast, and there is no need for sharding or a separate vector store.

---

## 2. Hybrid Search Capability

### Verdict: Good enough for your use case. Not as polished as dedicated hybrid search, but functional.

pgvector does not have a native "hybrid search" operator like Weaviate's `bm25 + vector` fusion. Instead, you achieve hybrid search by combining:

1. **Vector similarity** (pgvector HNSW index on cosine distance)
2. **Full-text search** (PostgreSQL `tsvector` + GIN index via `pg_trgm` or `ts_rank`)
3. **Metadata filtering** (standard B-tree/BRIN indexes on candidate attributes)

**Implementation pattern:**
```sql
-- Two-pass approach:
-- 1. Vector search returns top-N candidates with similarity scores
-- 2. Full-text search scores keywords independently
-- 3. RRF (Reciprocal Rank Fusion) combines the two scores in application code
```

**Performance:**
- For 500K rows, a combined vector + full-text query with RRF fusion completes in ~15–30ms.
- This is acceptable for recruiter-facing search (sub-second response is the UX target).
- PostgreSQL's GIN index on `tsvector` is battle-tested and handles this workload easily.

**Limitations vs. dedicated hybrid search:**
- No single-query native hybrid operator (requires application-level RRF or weighted scoring).
- No built-in BM25 scoring (you use `ts_rank` or implement BM25 manually).
- Slightly more application complexity, but not a dealbreaker.

**Bottom line:** For a recruiter portal searching candidate profiles, the hybrid search quality from pgvector + tsvector is sufficient. The UX target is sub-second response, and you are well within that budget.

---

## 3. Infrastructure Cost Comparison

### Verdict: pgvector wins decisively for your scale.

**pgvector (single PostgreSQL instance):**
| Cost Component | Monthly Estimate |
|---|---|
| RDS PostgreSQL (4 vCPU, 16GB RAM) | ~$300–500 |
| Storage (100GB SSD) | ~$10–15 |
| Backups | Included |
| **Total** | **~$310–515/mo** |

**Dedicated vector database (e.g., Pinecone, Weaviate Cloud):**
| Cost Component | Monthly Estimate |
|---|---|
| RDS PostgreSQL (relational data) | ~$300–500 |
| Pinecone (500K vectors, small index) | ~$100–200 |
| Weaviate Cloud (basic) | ~$150–300 |
| Qdrant Cloud (basic) | ~$50–150 |
| **Total** | **~$450–1,150/mo** |

**Operational overhead of a separate vector DB:**
- Separate deployment, monitoring, backup, and scaling strategy
- Network latency between app and vector DB (additional 5–20ms per query)
- Data synchronization: candidate records live in PostgreSQL; embeddings must be kept in sync
- Additional failure surface: two systems to monitor, debug, and maintain
- Team must learn a new API, query language, and operational model

**pgvector advantage:** One database, one operational surface, one billing line item. The embeddings live alongside the candidate data with zero sync overhead.

---

## 4. pgvector vs OpenAI Embeddings Compatibility

### Verdict: Full compatibility. This is a non-issue.

pgvector is designed to work seamlessly with OpenAI embeddings:

- **Dimension support:** pgvector's `vector` type supports up to 16,000 dimensions. OpenAI Ada-002 uses 1536 dimensions — well within limits.
- **Distance functions:** pgvector supports cosine distance (`<=>`), L2 distance (`<+>`), and inner product (`<#>`). OpenAI embeddings are normalized, so cosine distance is the natural choice.
- **Data type:** OpenAI returns a JSON array of floats. pgvector accepts this directly via `ARRAY[]::vector`.
- **Example:**
  ```sql
  INSERT INTO candidates (id, embedding, profile)
  VALUES (1, '[0.1, 0.2, ..., 0.9]'::vector, 'Full text profile...');
  ```

- **Re-embedding:** When you upgrade embedding models, you simply update the vector column. pgvector handles any dimension change without schema migration.

No compatibility concerns whatsoever.

---

## 5. Future Scaling — When Would pgvector Become a Bottleneck?

### Verdict: You would need to reach 10M+ vectors before pgvector becomes a concern.

**Scaling thresholds:**

| Vector Count | pgvector Status | Action Required |
|---|---|---|
| **< 100K** | Trivial | None |
| **100K – 500K** | Excellent | Standard HNSW tuning |
| **500K – 1M** | Good | Monitor RAM; ensure index fits in cache |
| **1M – 5M** | Manageable | 32–64GB RAM instance; monitor WAL growth |
| **5M – 10M** | Pushing limits | Consider `halfvec` (quantization) to reduce RAM; aggressive vacuuming |
| **10M – 50M** | Difficult | Evaluate dedicated vector DB; consider Citus for sharding |
| **50M+** | Not recommended | Dedicated vector DB (Milvus, Qdrant, Pinecone) |

**Your trajectory:** At 500K candidates, you are at the lower end of the "good" range. Even aggressive growth (10x to 5M) would still be manageable on a well-provisioned PostgreSQL instance.

**Signals that it is time to migrate to a dedicated vector DB:**
1. Query latency consistently exceeds 50ms despite hardware scaling
2. You need horizontal sharding (cannot scale vertically further)
3. Write throughput exceeds 1,000 writes/sec (MVCC bloat becomes unmanageable)
4. Vector count exceeds 10M on a single node
5. You need real-time vector updates (insert/delete) at high frequency

**For a recruiter portal:** Candidate records are updated infrequently (perhaps daily or weekly). Write throughput is negligible. The bottleneck is query latency, and at 500K vectors, pgvector delivers sub-10ms queries.

---

## Trade-Offs Summary

| Factor | pgvector | Dedicated Vector DB |
|---|---|---|
| **Infrastructure complexity** | Low (one DB) | High (two systems) |
| **Monthly cost (500K vectors)** | $310–515 | $450–1,150 |
| **Query latency (500K)** | <10ms | <5ms (marginal gain) |
| **Hybrid search** | Application-level RRF | Native (Weaviate, Qdrant) |
| **Write throughput** | Moderate (hundreds/sec) | High (thousands/sec) |
| **Scaling beyond 10M** | Difficult (vertical only) | Easy (horizontal sharding) |
| **Data sync** | None needed | Required (embedding sync) |
| **Operational surface** | 1 system | 2+ systems |
| **OpenAI compatibility** | Full | Full |

---

## Recommendation

**Confirm the PRD's choice of pgvector.**

For a recruiter client portal with 50K–500K candidates:

1. **Use pgvector with HNSW indexing** (`m=16`, `ef_construction=256`, `ef_search=64`).
2. **Use PostgreSQL `tsvector` + GIN index** for full-text search on candidate profiles.
3. **Implement RRF (Reciprocal Rank Fusion)** in application code to combine vector and keyword scores.
4. **Size the RDS instance at 4 vCPU / 16GB RAM** for 500K vectors. Upgrade to 32GB RAM if you approach 1M.
5. **Use PgBouncer** for connection pooling under load.
6. **Run regular VACUUM** to manage index bloat from updates.

**Re-evaluate at 5M+ vectors.** By then, you will have real usage data to inform whether a dedicated vector DB is justified. At that point, Qdrant or Weaviate would be the likely candidates if migration becomes necessary.

---

## Sources

- pgvector GitHub README — scalability guidance, dimension limits, indexing strategies
- Production experience reports — pgvector at 1M+ vectors, HNSW tuning, vacuuming requirements
- Hardware sizing calculations — HNSW index size formula (N x M x d x 4 bytes)
- Cost comparisons — RDS pricing, Pinecone/Weaviate/Qdrant cloud tiers
- Hybrid search patterns — pgvector + tsvector + RRF fusion
