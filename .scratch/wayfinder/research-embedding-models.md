# Question: What embedding model should we use?

The PRD chose OpenAI text-embedding-3-small (1536-dim) via the AI Middleware Gateway. Key considerations:

- **OpenAI text-embedding-3-small:** Consistent with LLM provider (GPT-4o), 1536-dim sufficient for skill matching, via AI Middleware Gateway
- **OpenAI text-embedding-3-large:** Better accuracy, higher cost, 3072-dim
- **Cohere embed-english-v3:** Competitive accuracy, different dimensionality
- **Sentence Transformers (local):** Free, no API calls, but requires hosting

Questions to investigate:
1. Accuracy comparison — OpenAI vs Cohere vs Sentence Transformers for IT skill matching
2. Cost — embedding costs at scale (50K candidates, daily re-embedding?)
3. Dimensionality — 1536-dim vs alternatives, impact on pgvector performance
4. Update frequency — how often are embeddings recomputed? (on candidate update? periodic?)
5. Local vs API — can we run embeddings locally to reduce cost and latency?

Resolve by comparing embedding models for the specific use case (IT skill matching in staffing), considering accuracy, cost, and operational complexity.
