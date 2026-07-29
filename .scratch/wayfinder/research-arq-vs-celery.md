# Question: Is ARQ the right task queue?

The PRD chose ARQ (Async Redis Queue) over Celery for the proactive monitor. Key considerations:

- **ARQ:** Lightweight, works with existing Redis infrastructure, async-native, fewer dependencies
- **Celery:** More mature, better monitoring (Flower), larger ecosystem, but heavier, sync-leaning

Questions to investigate:
1. ARQ feature completeness — cron jobs, retries, distributed workers
2. Celery comparison — does the proactive monitor need Celery's features?
3. Existing Redis infrastructure — is it already set up for task queues?
4. Monitoring — how do we monitor ARQ jobs? Celery has Flower; ARQ has what?
5. Scaling — ARQ vs Celery for the expected load (every 30 min per recruiter, 100+ recruiters)

Resolve by comparing ARQ and Celery for the proactive monitor's specific needs (cron scheduling, retries, monitoring).
