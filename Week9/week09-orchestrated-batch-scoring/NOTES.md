# NOTES.md — Week 9: Orchestrated Batch Scoring

**Student ID used with `generate_for_student.py`:**
142301017

## notify retry count

<!-- How many attempts did notify take in your run? (Check
     dag_run_summary.json.) -->

In `dag_run_summary.json`, `notify` took **3 attempts** to succeed.
It failed on the first two attempts because of the simulated transient errors in `src/run_pipeline.py`, and then succeeded on the third attempt after being retried.

## Branch independence

<!-- Why does load still succeed even though notify — its "sibling" in the
     DAG — failed on its first two attempts? What does that tell you about
     how failures in one branch of a DAG should (or shouldn't) affect an
     unrelated branch? -->

Both `load` and `notify` depend only on `score`, not on each other. Once `score` completes and writes its results into the shared context, `load` already has everything it needs to execute. In our pipeline run, `load` ran before `notify`, but even if they ran concurrently, `load` doesn't depend on `notify` at all.

This shows that in a DAG, tasks on independent branches should have isolated failure domains. A temporary failure or retry in an auxiliary task like `notify` shouldn't block or fail unrelated tasks like `load`, allowing the core data pipeline to succeed even if a side effect fails.

## Retry cost under FinOps

<!-- Tying back to this week's FinOps content: if notify were a metered API
     call you paid for per attempt, what would you change about the retry
     strategy, and why is "retry every failed task the same way" a risky
     default once cost enters the picture? -->

If `notify` were a metered API where each call costs money, I'd change the retry strategy to be cost-aware:
- Only retry transient errors (like 429 rate limits or timeouts), and never retry deterministic client errors (like 400 Bad Request or 401/403 Auth errors) where retrying just burns budget with zero chance of succeeding.
- Add exponential backoff with jitter instead of immediate retries, keep max retries low (1–2 max), and drop failed alerts into a dead-letter queue or fallback log.
- Pass idempotency keys to ensure we don't get billed twice for duplicate calls.

"Retry every failed task the same way" is a risky default because tasks have very different cost profiles. Retrying a local file write or CPU script costs virtually nothing, but retrying paid external APIs or heavy GPU workloads incurs direct financial costs every attempt. If there's a permanent bug or bad input, blanket retries just multiply failure costs for nothing.
