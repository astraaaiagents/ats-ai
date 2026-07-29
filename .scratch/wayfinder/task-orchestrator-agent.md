# Question: How is the Orchestrator agent designed?

The Orchestrator is the central coordinator. It parses intent, delegates to specialists, and synthesizes responses. Key decisions:

**Architecture decisions:**
1. **StateGraph design** — What is the LangGraph StateGraph schema? What fields are in the state?
2. **Intent classification** — How does the Orchestrator determine which specialist(s) to call? LLM function calling? Rule-based? Hybrid?
3. **Tool registration** — How are specialist agents registered as tools? What's the tool interface?
4. **Response synthesis** — How does the Orchestrator combine specialist outputs into natural language + structured cards?
5. **Error handling** — What happens when a specialist fails? Retry? Fallback?
6. **Confidence scoring** — How does the Orchestrator compute a confidence score for each response?
7. **Proactive trigger** — How does the Orchestrator support the "sourcing pulse" trigger from the background monitor?
8. **Memory integration** — How does the Orchestrator access session memory (InMemoryStore) and long-term memory (PostgreSQL)?

**Specialist agent interfaces:**
- SourcingAgent: `search_candidates_db()`, `search_job_boards()`, `search_sub_vendors()`, `get_job_details()`
- RankingAgent: `compute_fit_score()`, `identify_gaps()`, `get_recruiter_preferences()`, `compare_candidates()`
- OutreachAgent: `get_candidate_contact()`, `get_job_context()`, `generate_outreach()`, `get_email_templates()`

Resolve by designing the LangGraph StateGraph, defining the state schema, implementing the intent routing logic, and wiring up specialist tool calls.

---

## Resolution

**Date:** 2026-07-26

**Files created:**
- `services/agent_orchestrator/__init__.py` — Entry point: `run_orchestrator()` called by Agent Gateway
- `services/agent_orchestrator/state.py` — `OrchestratorState` TypedDict (16 fields)
- `services/agent_orchestrator/graph.py` — LangGraph `StateGraph` with 7 nodes, conditional routing
- `services/agent_orchestrator/intent_classifier.py` — Rule-based intent classification (6 intents)
- `services/agent_orchestrator/sourcing_agent.py` — SourcingAgent (placeholder)
- `services/agent_orchestrator/ranking_agent.py` — RankingAgent (placeholder)
- `services/agent_orchestrator/outreach_agent.py` — OutreachAgent (placeholder)

**Architecture decisions:**

1. **StateGraph design:** 7-node graph with `OrchestratorState` TypedDict. Nodes: `classify_intent` → conditional routing → specialist node → `synthesize_response` → END. State flows through all nodes via TypedDict.

2. **Intent classification:** Hybrid approach — rule-based keyword matching for fast, deterministic classification (6 intents: source_candidates, check_pipeline, update_preferences, schedule_interview, draft_outreach, general_conversation). LLM-based fallback can be added later.

3. **Tool registration:** Specialist agents are Python async functions, not LangChain tools. Each specialist is a node in the graph that reads state and writes outputs. This avoids LangChain tool-calling overhead and keeps the graph simple.

4. **Response synthesis:** Template-based for MVP (intent-specific response templates). LLM-based synthesis can be added in Phase 3+ when the Orchestrator needs to generate more nuanced responses.

5. **Error handling:** Try/catch in `run_orchestrator()` returns a graceful error message. Specialist nodes log warnings for placeholder implementations. No retry logic at MVP stage — errors surface to the user.

6. **Confidence scoring:** Computed per-intent in the synthesis node. For sourcing: `min(0.9, 0.5 + len(ranked) * 0.1)` — higher when more candidates found. For unimplemented features: low confidence (0.2-0.4) to flag for human review.

7. **Proactive trigger:** The `run_orchestrator()` function accepts optional `job_id` and `preferences` params. The proactive monitor can call it with a "sourcing pulse" message like "Check for new matches against open jobs". The intent classifier will route to `source_candidates`.

8. **Memory integration:** MVP uses in-memory state only (no LangChain InMemoryStore). Long-term memory (PostgreSQL conversation history) is handled by the Agent Gateway service layer. LangChain InMemoryStore can be added when LLM-based synthesis is implemented.

**Graph structure:**
```
START → classify_intent → [conditional: intent] → {specialist_node} → synthesize_response → END
```

**Specialist interfaces:**
- SourcingAgent: `search_candidates(db, org_id, recruiter_id, query, job_id, limit)` → list[dict]
- RankingAgent: `compute_fit_scores(db, candidates, recruiter_id, job_id)` → list[dict]
- OutreachAgent: `generate_outreach(candidates, job_context, recruiter_id)` → list[dict]

**Pattern consistency:** Follows existing conventions — async functions, SQLAlchemy session injection, logging with `logger.warning` for placeholders, type hints with `TypedDict`, docstrings for all public functions.
