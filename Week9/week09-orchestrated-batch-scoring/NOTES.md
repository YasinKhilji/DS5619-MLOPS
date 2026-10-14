# NOTES.md — Week 9: Orchestrated Batch Scoring

**Student ID used with `generate_for_student.py`:**
142301017

## notify retry count

<!-- How many attempts did notify take in your run? (Check
     dag_run_summary.json.) -->

In dag_run_summary.json, notify took 3 attempts to succeed. It failed twice because of the simulated errors and succeeded on the third attempt after retries.

## Branch independence

<!-- Why does load still succeed even though notify — its "sibling" in the
     DAG — failed on its first two attempts? What does that tell you about
     how failures in one branch of a DAG should (or shouldn't) affect an
     unrelated branch? -->

Both load and notify depend on score, but neither depends on the other. Once score finishes, both tasks can run independently. In our run, load succeeded even though notify failed on its first two attempts.

This shows that a failure in one branch should not stop another branch that does not depend on it. This helps the main pipeline continue even when a separate task, such as sending a notification, has temporary problems.

## Retry cost under FinOps

<!-- Tying back to this week's FinOps content: if notify were a metered API
     call you paid for per attempt, what would you change about the retry
     strategy, and why is "retry every failed task the same way" a risky
     default once cost enters the picture? -->

If notify used a paid API, I would retry only temporary errors, such as timeouts or rate limits. I would avoid retrying errors like invalid requests because they are unlikely to succeed without fixing the problem. I would also use a short delay between retries and limit the number of attempts.

Retrying every task in the same way can waste money. For example, retrying a local script may cost very little, while retrying a paid API or a GPU job can add extra costs. So, the retry strategy should depend on the type of task and the cost of each attempt.