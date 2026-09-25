# CI verification

Fill this in after you push and watch the workflow run on GitHub (Actions
tab of your repo). This is how we confirm your CI actually ran green in a
real GitHub Actions runner, not just locally.

## Workflow run

Paste the URL of a successful run of all three jobs (Actions tab -> click
the run -> copy the URL):



https://github.com/YasinKhilji/DS5619-MLOPS/actions/runs/36101287212

## Job summary

For each job, note pass/fail and how long it took:

- `lint`: PASS — 8 seconds
- `unit-test`: PASS — 10 seconds
- `integration-test`: PASS — 18 seconds

## What broke on the way there (optional but useful)

If any job failed before you got it working, briefly note what the failure
was and what fixed it. (Not required, but if `integration-test` gave you
trouble, this is worth 2 sentences for your own future reference — Week 9's
lab also builds on debugging CI-style failures.)

The first CI run failed because the workflow was running from the repository root while the Week 7 project files are under `Week7/week07-cicd/`. The workflow was fixed by setting the working directory to `Week7/week07-cicd` for the jobs. The next run passed all three jobs.