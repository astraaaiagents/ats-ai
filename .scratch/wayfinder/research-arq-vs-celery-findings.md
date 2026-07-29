# Research: Is ARQ the Right Task Queue?

**Date:** 2026-07-26
**Context:** Agent-First AI-Native Recruiter Client Portal
**Decision:** PRD chose ARQ (Async Redis Queue) over Celery

---

## Executive Summary

**Recommendation: CHALLENGE the PRD's choice. Use ARQ for MVP but plan for migration if scale grows.**

ARQ is adequate for the MVP's proactive monitor (every 30 min per recruiter, 100+ recruiters = ~200 tasks/day). However, ARQ is in **maintenance-only mode** with no active development. For a production system that needs to survive beyond MVP, this is a risk. Celery is heavier but actively maintained. For the MVP's scale, ARQ is acceptable with the understanding that it may need replacement.

---

## 1. ARQ Feature Completeness

**Verdict: Adequate for MVP, limited for production scale.**

ARQ provides:
- **Job queues with asyncio and Redis** — lightweight, async-native
- **Retry logic** — configurable retry with backoff
- **Cron jobs** — ARQ supports scheduled tasks via `arq.cron`
- **Distributed workers** — multiple workers can consume from the same queue

However, ARQ is in **maintenance-only mode**. No new features are being developed. This means:
- No new feature requests will be addressed
- Bug fixes may be slow
- No long-term roadmap

For the MVP's scale (200 tasks/day), ARQ's feature set is sufficient.

---

## 2. Celery Comparison

**Verdict: Celery is heavier but more mature and actively maintained.**

| Feature | ARQ | Celery |
|---------|-----|--------|
| **Async-native** | Yes (asyncio) | No (sync-leaning, async support via eventlet/gevent) |
| **Cron jobs** | Built-in (`arq.cron`) | Via Celery Beat |
| **Retry logic** | Built-in | Built-in (more configurable) |
| **Monitoring** | Limited (no Flower equivalent) | Flower (production-grade dashboard) |
| **Active development** | Maintenance-only | Actively maintained |
| **Ecosystem** | Small | Large (tasks, signals, extensions) |
| **Redis dependency** | Required | Required (or RabbitMQ) |
| **Learning curve** | Easy | Steep |
| **Dependencies** | Minimal | Heavy (billions, kombu, pytz, etc.) |

For the proactive monitor's specific needs (cron scheduling, retries, monitoring):
- ARQ handles cron and retries natively
- Celery Beat handles cron; Flower handles monitoring
- ARQ's monitoring is limited — no built-in dashboard

---

## 3. Existing Redis Infrastructure

**Verdict: Both work with existing Redis. ARQ is simpler to set up.**

Both ARQ and Celery require Redis as a broker. The existing ATS already uses Redis for rate limiting, so the infrastructure is in place. ARQ requires fewer dependencies and is simpler to configure — a single Python file sets up workers and cron jobs. Celery requires a more complex configuration (Celery app, worker startup, Beat scheduler).

---

## 4. Monitoring

**Verdict: Celery wins decisively. ARQ has no built-in monitoring dashboard.**

- **Celery + Flower:** Production-grade monitoring dashboard. Shows task success/failure rates, execution times, worker health, queue depths.
- **ARQ:** No built-in monitoring. You'd need to build custom monitoring against Redis keys, or use a third-party tool.

For a production system where you need to know if the sourcing pulse is failing, Celery + Flower is significantly better.

---

## 5. Scaling

**Verdict: Both handle the expected load. ARQ is simpler; Celery is more robust under failure.**

Expected load: 100+ recruiters × 1 sourcing pulse per 30 min = ~200 tasks/day. This is trivial for both systems.

Where Celery has an advantage under load:
- **Better failure handling:** Celery has more robust retry logic, dead letter queues, and task routing
- **Worker management:** Celery can dynamically scale workers; ARQ requires manual worker management
- **Task routing:** Celery supports task routing to specific queues/workers; ARQ is simpler

---

## Recommendation

**Use ARQ for MVP, but document the migration path to Celery.**

For the MVP:
1. **Use ARQ** — it's lightweight, async-native, and sufficient for 200 tasks/day
2. **Build custom monitoring** — watch Redis keys for task status; set up basic alerts
3. **Document the migration path** — if the system grows beyond MVP, migrating to Celery is straightforward (same Redis broker, similar task definitions)

**Migration triggers to Celery:**
- Task volume exceeds 10,000/day
- Need production-grade monitoring (Flower dashboard)
- Need complex task routing or dynamic worker scaling
- ARQ bugs block critical functionality

---

## Sources

- ARQ PyPI page — "Job queues in python with asyncio and redis", maintenance-only mode
- ARQ documentation — cron support, retry logic, worker configuration
- Celery documentation — Beat, Flower, task routing
- Comparison analysis — feature matrix, scaling characteristics
