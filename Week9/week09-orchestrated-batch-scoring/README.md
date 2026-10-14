# Lab 9 — Orchestrated Batch Scoring

**Track B (BMD-45 vehicle detection) · Week 9 · DS5619 Machine Learning Systems Operations**

## Setup

```bash
python -m venv .venv && source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
python generate_for_student.py --student-id <your roll number or institute email>
```

Record your `--student-id` value in `NOTES.md`.

## Files

- `src/mini_orchestrator.py` — implementation of the mini DAG orchestrator (topological ordering, task retries, DAG execution).
- `src/mock_detector.py` — dependency-light stand-in detector (provided).
- `src/run_pipeline.py` — complete driver script defining and running the batch-scoring DAG.
- `data/fixtures/` — personalized sample images to batch-score, generated deterministically from student ID.
- `batch_report.json` — output artifact produced by `load` task in the DAG run.
- `dag_run_summary.json` — execution summary produced by the orchestrator.
- `NOTES.md` — answers regarding retry counts, branch independence, and FinOps retry cost analysis.

## Background

The batch-scoring DAG has this shape ("anatomy of a DAG" applied):

```text
extract --> score --> load
                  \-> notify
```

- **extract**: List every image under `data/fixtures/`.
- **score**: Run the detector over each image, accumulate detection counts.
- **load**: Write `batch_report.json` — depends only on `score`.
- **notify**: A deliberately flaky task (fails twice, then succeeds on the 3rd attempt) simulating an external webhook call — depends only on `score`.

## Implementation

`src/mini_orchestrator.py` implements:
1. `topological_order(tasks)`: Orders tasks so every task runs after its dependencies (using Kahn's algorithm), detecting dependency cycles and missing dependencies.
2. `run_task_with_retry(task, context)`: Retries a single task up to `max_retries` additional times with delay before raising the final exception.
3. `run_dag(tasks, context)`: Executes tasks in topological order, sharing context across tasks, and halts immediately if an unrecoverable failure occurs.

## Running the Pipeline

```bash
python src/run_pipeline.py
```

This runs the 4-task DAG, producing `batch_report.json` and `dag_run_summary.json`.

## Self-Check & Testing

```bash
pytest tests/ -q
```

All smoke tests verify:
- Topological sort for linear chains, branching DAGs, cycles, and missing dependencies.
- Retry behavior on immediate success, transient failures, and permanent exhaustion.
- Context sharing and failure isolation across DAG tasks.
- End-to-end execution of `run_pipeline.py`.
