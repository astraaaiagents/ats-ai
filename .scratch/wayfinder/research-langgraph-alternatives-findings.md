# Research: Is LangGraph the Right Agent Framework?

**Date:** 2026-07-26
**Context:** Agent-First AI-Native Recruiter Client Portal
**Decision:** PRD chose LangGraph (StateGraph) over AutoGen, CrewAI, and custom frameworks

---

## Executive Summary

**Recommendation: CONFIRM the PRD's choice of LangGraph.**

LangGraph is the right choice for this project. It provides durable execution, human-in-the-loop support, and a TypeScript SDK (LangGraph.js) that enables full-stack consistency. The PRD's decision is sound.

---

## 1. LangGraph Production Readiness

**Verdict: Production-ready.**

LangGraph is described as a "low-level orchestration framework for building stateful agents." Key production features:
- **Durable execution:** Workflows persist through failures and can run for extended periods, automatically resuming from exactly where they left off. This is critical for agent workflows that may span multiple LLM calls.
- **Human-in-the-loop oversight:** Developers can inspect and modify agent state at any point during execution. This directly supports the EU AI Act requirement for human approval gates.
- **LangSmith debugging:** Built-in observability and debugging tooling. Critical for debugging agent behavior in production.
- **Production-ready deployment:** Designed for production deployment with state persistence and recovery.

LangChain has been actively maintaining LangGraph since late 2023. The API is stable and the documentation is comprehensive.

---

## 2. TypeScript SDK Maturity

**Verdict: Good parity with Python SDK.**

LangGraph provides an "equivalent JS/TS library" called LangGraph.js. This is a significant advantage for this project because:
- The frontend is Next.js (TypeScript)
- The backend is FastAPI (Python)
- Having the same agent framework on both sides enables code sharing and consistency

The TypeScript SDK supports the core StateGraph pattern, persistence, and human-in-the-loop workflows. Feature parity with Python is good for the patterns this project needs.

---

## 3. State Management

**Verdict: Excellent fit for session + long-term memory requirements.**

LangGraph's state management model:
- **Short-term working memory:** For ongoing reasoning within a single conversation
- **Long-term persistent memory:** Across sessions via durable execution
- **State inspection/modification:** At any point during execution (supports human oversight)

This maps directly to the PRD's two-tier memory model:
- Session Memory (InMemoryStore) → LangGraph's short-term working memory
- Conversation Memory (PostgreSQL) → LangGraph's durable execution persistence

---

## 4. MCP Support

**Verdict: Not yet in the core README, but LangChain's broader ecosystem supports MCP.**

The LangGraph README does not explicitly mention MCP (Model Context Protocol) support. However, LangChain as a whole has been investing in MCP integration. For this project, MCP is a "nice-to-have" rather than a requirement — the Orchestrator + Specialist pattern works fine without it.

---

## 5. Comparison with Alternatives

| Factor | LangGraph | AutoGen | CrewAI | Custom |
|--------|-----------|---------|--------|--------|
| **Production readiness** | Production-ready | Production-ready (Microsoft) | Emerging | N/A |
| **TypeScript SDK** | Yes (LangGraph.js) | No (Python-only) | Python-focused | Your choice |
| **State management** | Excellent (durable execution) | Good | Basic | Your responsibility |
| **Human-in-the-loop** | Built-in | Built-in | Limited | Your responsibility |
| **Weight** | Lightweight | Heavy | Medium | N/A |
| **Learning curve** | Medium | Steep | Easy | Steep |
| **Debugging** | LangSmith | Limited | Limited | Your tooling |

---

## Recommendation

**Confirm the PRD's choice of LangGraph.**

For an agent-first recruiter portal with:
- Multi-agent orchestration (Orchestrator + Specialists)
- Human approval gates (EU AI Act compliance)
- Full-stack TypeScript consistency (Next.js frontend + LangGraph.js)
- Durable execution (agent workflows spanning multiple LLM calls)

LangGraph is the best fit. AutoGen is heavier and Python-only. CrewAI lacks the state management depth. A custom framework would be a significant development cost with no clear advantage.

---

## Sources

- LangGraph GitHub README — feature summary, durable execution, human-in-the-loop
- LangGraph.js documentation — TypeScript SDK parity
- LangSmith documentation — debugging and observability
