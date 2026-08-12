# NOTES.md — Week 2: Config-Driven Data Pipelines

**Student ID used with `generate_for_student.py`:**
142301017

## What was hardcoded, and what would switching it have required?
Originally, the pipeline had the input file path, file format, and high-value transaction threshold hardcoded directly into the Python code. This meant that changing the threshold required modifying and rerunning the code. Similarly, switching from CSV to JSON meant changing the file-reading logic.

The refactored pipeline moves these settings into a YAML configuration file. This makes the pipeline more flexible and easier to maintain, as the same Python code can now process both CSV and JSON files with different transaction thresholds simply by updating the configuration.
