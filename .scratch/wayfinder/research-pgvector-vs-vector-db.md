# Question: Is pgvector the right vector search solution?

The PRD chose pgvector (PostgreSQL extension) over separate vector DBs (Weaviate, Pinecone, Qdrant). Key considerations:

- **pgvector:** Co-located with existing PostgreSQL, no new infrastructure, hybrid search (vector + structured), billion-scale with IVF index
- **Separate vector DB:** Better performance at scale, more features (hybrid search, metadata filtering), but adds infrastructure complexity

Questions to investigate:
1. pgvector performance for 50K-500K candidates — can it handle the query load?
2. Hybrid search capability — pgvector supports vector + keyword, but how well?
3. Infrastructure cost — does adding a separate vector DB justify the operational overhead?
4. pgvector vs OpenAI embeddings compatibility — embedding model choice affects vector dimension
5. Future scaling — at what point would pgvector become a bottleneck?

Resolve by benchmarking pgvector (or reading published benchmarks), comparing with 1-2 alternatives, and recommending a choice.
