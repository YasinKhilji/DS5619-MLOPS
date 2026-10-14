# NOTES.md — Week 9: Orchestrated Batch Scoring

**Student ID used with `generate_for_student.py`:**
142301017
(Seed: 4153183100)

## notify retry count

The `notify` task took **3 attempts** to succeed in this run (1 initial attempt + 2 retries, succeeding on attempt 3), as recorded in `dag_run_summary.json`:

```json
"notify": {
  "status": "success",
  "attempts": 3
}
```

In `src/run_pipeline.py`, `notify` simulates transient failures while its attempt counter is less than 3 (`_notify_attempt_counter["n"] < 3`), raising a `RuntimeError`. Because `notify` is configured with `max_retries=3`, `run_task_with_retry` catches the transient exceptions, sleeps for the specified `retry_delay_seconds=0.1`, and re-executes. On attempt 3, the condition passes, setting `context["notified"] = True` and recording 3 total attempts.

## Branch independence

- **Why `load` still succeeds:**
  The DAG defined in `src/run_pipeline.py` has the structure:
  ```text
  extract --> score --> load
                    \-> notify
  ```
  Both `load` and `notify` depend strictly on `score`; neither depends on the other. They are independent sibling branches. In our orchestrator's topological execution order (`['extract', 'score', 'load', 'notify']`), `load` was scheduled and executed to completion before `notify` was ever invoked. Even if `notify` had executed first or concurrently (as in an Airflow deployment with a Celery or Kubernetes executor), `load` requires only that its upstream parent `score` has succeeded and populated `context`. Because `score` completed successfully, `load` has all the data and execution prerequisites it needs to succeed.

- **What this tells us about DAG failure handling:**
  A core design principle of DAG-based orchestration is **fault isolation across independent branches**. Failures or retries in one branch must not block or fail unrelated sibling branches unless there is an explicit downstream dependency between them. This decoupling ensures that core operational outcomes (such as writing batch scoring results to `batch_report.json`) remain resilient and unaffected by transient or permanent failures in auxiliary side effects (such as webhooks, Slack alerts, or external telemetry). It prevents unnecessary pipeline-wide failures and saves downstream computation.

## Retry cost under FinOps

- **FinOps-tailored retry strategy for a metered API:**
  If `notify` were a metered API call billed per request attempt (e.g., commercial LLM inference API, paid SMS/Twilio alert, or third-party computer vision API), treating every failure with blind retries directly burns cloud budget. The retry strategy should be adapted as follows:
  1. **Error Classification & Selective Retries:** Distinguish transient, retriable errors (HTTP 429 rate limit, HTTP 503 service unavailable, socket timeout) from deterministic, non-retriable errors (HTTP 400 Bad Request, 401 Unauthorized, 403 Forbidden, 422 Unprocessable Entity). Retrying a deterministic 4xx error guarantees a 100% failure rate while multiplying billing costs on every invocation.
  2. **Exponential Backoff with Full Jitter:** Instead of fixed-interval sleeps, implement exponential backoff with jitter (`delay = base * 2^attempt + jitter`) to avoid hammering rate-limited endpoints during service degradation.
  3. **Strict Retry Budgets & Circuit Breakers:** Lower `max_retries` (e.g. 1 or 2 retries max) and implement a circuit breaker to fail fast if systemic service failures occur, capping financial exposure.
  4. **Dead-Letter Queues (DLQ) & Fallback Channels:** After bounded retries are exhausted, offload the failed event to a dead-letter queue (e.g. AWS SQS DLQ or local audit log) for manual inspection or off-peak replay rather than stalling or repeatedly retrying in-line.
  5. **Idempotency Keys:** Include a unique `Idempotency-Key` header with every request so the API vendor does not double-bill or duplicate operations if a network failure occurs after processing.

- **Why "retry every failed task the same way" is a risky default once cost enters the picture:**
  - **Asymmetric unit economics:** Tasks in an ML/data pipeline have vastly different cost profiles. A local CPU task (such as `extract` listing files or `load` dumping JSON) costs negligible marginal compute and can be retried liberally. In contrast, tasks that invoke metered commercial APIs or spin up GPU spot instances carry direct, marginal dollar costs per attempt.
  - **Runaway cost amplification:** A blanket default (e.g., "retry 3–5 times across the board") acts as a multiplier on failure costs. In automated, scheduled batch pipelines (e.g., hourly or daily runs), a persistent failure (such as an expired API key or invalid payload format) would turn a single failure into 4–6 billable requests per batch, silently wasting thousands of dollars with zero probability of success.
  - **Alignment with FinOps principles:** FinOps demands cost awareness, resource accountability, and optimization of unit economics. Error recovery policies must be cost-aware: inexpensive, idempotent tasks can afford aggressive retry loops, while metered or resource-intensive tasks require conservative retry ceilings, budget-aware error filtering, and graceful fallbacks.
