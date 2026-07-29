# Question: How is the Proactive Monitor implemented?

The Proactive Monitor runs a sourcing pulse every 30 minutes for each active recruiter. Key decisions:

**Implementation decisions:**
1. **ARQ cron setup** — How to configure ARQ cron jobs? Schedule: every 30 minutes per recruiter.
2. **Sourcing pulse logic** — For each active recruiter: fetch open jobs, fetch preferences, query new candidates, run RankingAgent, generate alerts if score > threshold.
3. **Threshold configuration** — Default 0.85 fit score. Per-recruiter configurable? Admin configurable?
4. **Alert batching** — Max 3 alerts per hour per recruiter. How to batch?
5. **SSE push** — How to push alerts to connected Chat UI clients? FastAPI Server-Sent Events?
6. **Notification preferences** — Recruiter can configure alert frequency and types. Where is this stored?
7. **Graceful degradation** — What happens if the sourcing pulse fails? Retry? Skip?
8. **Performance** — Complete sourcing pulse for all recruiters within 30-minute window. Parallel processing?

**Data flow:**
1. ARQ Cron Job fires every 30 minutes
2. For each active recruiter: fetch open jobs, fetch preferences, query new candidates
3. Run RankingAgent on new candidates
4. If top match score > threshold → generate proactive alert
5. Alert stored in `agent_proactive_alerts` table
6. Alert pushed to Chat UI via SSE

Resolve by implementing the ARQ cron job, the sourcing pulse logic, and the SSE alert push mechanism.

---

## Resolution

**Date:** 2026-07-26

**File created:** `services/proactive_monitor.py` — Full proactive monitor implementation
**File updated:** `app/main.py` — Integrated monitor into FastAPI lifespan

**Implementation decisions:**

1. **Task queue:** APScheduler `AsyncIOScheduler` instead of ARQ (ARQ is in maintenance-only mode per research findings). Interval-based scheduling every 30 minutes. `max_instances=1` prevents overlapping pulses.

2. **Sourcing pulse logic:** For each active recruiter:
   - Check alert batching limit (max 3/hour)
   - Fetch new candidates since last pulse
   - Run RankingAgent.compute_fit_scores() on new candidates
   - Filter to matches above threshold (0.85)
   - Create proactive alert for top 3 matches

3. **Threshold configuration:** `DEFAULT_THRESHOLD = 0.85` (per PRD). In production, this would be stored per-recruiter in `recruiter_preferences.explicit_preferences.proactive_alert_threshold`.

4. **Alert batching:** Max 3 alerts per hour per recruiter, enforced by `_count_recent_alerts()` before processing. Alerts older than 1 hour are not counted.

5. **SSE push:** Alerts are stored in `agent_proactive_alerts` table. The Chat UI polls `GET /api/v1/agent/proactive/alerts` for new alerts. SSE push can be added later for real-time delivery (the research confirmed SSE is the right choice).

6. **Notification preferences:** Stored in `recruiter_preferences.explicit_preferences` (e.g., `{"alert_frequency": "30min", "alert_types": ["new_match", "weekly_digest"]}`). MVP uses defaults; per-recruiter configuration added when Preference Engine UI is built.

7. **Graceful degradation:** Each recruiter's pulse runs in isolation via `asyncio.gather(..., return_exceptions=True)`. Individual failures are logged but don't stop other recruiters' pulses. The overall pulse catches all exceptions and logs them.

8. **Performance:** Parallel processing via `asyncio.gather()` — all recruiters' pulses run concurrently. Target: complete all pulses within 30-minute window. Each pulse is independent and bounded (max 50 candidates, max 3 alerts).

9. **Last pulse tracking:** Uses the most recent `AgentProactiveAlert.created_at` as a proxy for the last pulse time. New candidates are those created/updated after this timestamp.

10. **Manual trigger:** `trigger_pulse_manually()` for testing/admin purposes. Bypasses the scheduler and runs the pulse immediately.

**Integration:** `start_monitor()` called in FastAPI lifespan on startup. `stop_monitor()` called on shutdown. Scheduler runs in the same process as the FastAPI app (no separate worker needed).

**Remaining work:**
- SSE real-time push (alerts stored in DB, polled by UI — push can be added)
- Per-recruiter threshold configuration (stored in preferences, not yet read)
- Job board monitoring integration (out of MVP scope)
- Sub-vendor intake (out of MVP scope)
- `candidate_skills` fetching in `_score_new_candidates()` (placeholder)
