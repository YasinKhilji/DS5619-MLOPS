# NOTES.md — Week 3: ETL and Data Validation

**Student ID used with `generate_for_student.py`:**
142301017


## Quarantine count vs. the 7 known injected problems

The dataset had 600 rows. After running the ETL, 6 rows were quarantined and 594 rows were kept as clean.
There were 7 injected problems, but the number of quarantined rows was 6 because some rows had more than one problem. In particular, rows 71 and 180 had a missing amount, which failed both the not-null and positive amount checks.
So there were 8 validation violations across 6 rows.
The pipeline passed all 5 tests.