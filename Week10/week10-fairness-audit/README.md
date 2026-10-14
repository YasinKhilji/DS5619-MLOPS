# Lab 10 — Fairness and Robustness Audit

**Course:** DS5619 Machine Learning Systems Operations  
**Track:** Track B (BMD-45 vehicle detection)  
**Deliverable:** Week 10 Lab Submission

---

## Overview

This lab operationalizes the **Bias Detection and Fairness Monitoring** content from the Week 10 lecture. Using synthetic CCTV images based on the BMD-45 dataset (*Sharma et al., "BMD-45: A Large-Scale CCTV Vehicle Detection Dataset for Urban Traffic," CVPR 2026*), this project conducts:
1. **Class-Based Performance Disparity Audit**: Evaluating equal-opportunity recall across 14 vehicle classes to detect whether smaller-vehicle classes (Bicycles, Two-wheelers) suffer from systematic underperformance.
2. **Adversarial Robustness Evaluation**: Implementing an FGSM-style white-box channel perturbation attack ($L_\infty$ budget $\epsilon \in \{0, 10, 20, 30, 40\}$) to measure the fragility of each vehicle class under adversarial shift.

---

## Project Structure

```
week10-fairness-audit/
├── _shared/
│   └── student_seed.py           # Deterministic student seed generator
├── data/
│   └── fixtures/                 # Student-personalized CCTV images & COCO annotations
│       ├── camera_A_daylight/
│       ├── camera_B_lowlight/
│       └── _annotations.coco.json
├── src/
│   ├── fairness_audit.py         # IoU computation, ground-truth matching, per-class recall audit
│   ├── adversarial.py            # FGSM channel perturbation, audit under attack, fragility ranking
│   ├── mock_detector.py          # Fast stand-in detector for rapid verification
│   └── run_pipeline.py           # Driver script writing fairness_report.json
├── tests/
│   └── test_smoke.py             # Test suite validating audit and adversarial implementations
├── fairness_report.json          # Complete report of clean and attacked evaluations
├── generate_for_student.py       # Fixture generator seeded with student ID
├── NOTES.md                      # Audit observations, ethics analysis, and security evaluation
├── README.pdf                    # Lab instructions
├── README.md                     # Project documentation
└── requirements.txt              # Project dependencies (pillow, pytest)
```

---

## Setup & Reproduction

### 1. Environment Setup
```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Generate Personalized Student Fixtures
Deterministic seed generation from student ID:
```bash
python generate_for_student.py --student-id 142301017
```
This generates 60 synthetic CCTV images (30 daylight, 30 lowlight) and `_annotations.coco.json` in `data/fixtures/`.

### 3. Run Pipeline
To execute both the clean fairness audit and the adversarial attack suite:
```bash
python src/run_pipeline.py
```
This writes `fairness_report.json` with per-category recall, underperforming categories, and robustness statistics under attack.

### 4. Run Self-Check Tests
```bash
pytest tests/ -q
```

---

## Key Findings

### Clean Performance Disparity Audit (Threshold = 90% Recall)
- **Flagged Categories**:
  - `Bicycle`: 14 / 19 = **73.7%** recall
  - `Two-wheeler`: 11 / 14 = **78.6%** recall
  - `Hatchback`: 16 / 18 = **88.9%** recall (sampling noise due to small sample size)
- **Top Performers**: Bus, Tempo-traveller, MUV, Van, Other at 100.0% recall.
- **Root Cause**: Bicycles and two-wheelers have small bounding box footprints ($7\times 6$ to $15\times 6$ pixels). Sensor noise and border outlines frequently fragment connected components below the 20-pixel detector threshold.

### Adversarial Robustness Analysis
- **White-Box Attack**: Under an $L_\infty$ perturbation lowering red and raising green/blue by $\epsilon \in [0, 40]$:
  - **Most Fragile by Drop ($\epsilon = 20$)**: `Van` (-40.0%), `Two-wheeler` (-35.7%), `Bus` (-28.0%).
  - **Lowest Absolute Recall ($\epsilon = 20$)**: `Two-wheeler` (42.9%), `Van` (60.0%), `Bicycle` (63.2%).
  - **Catastrophic Collapse ($\epsilon = 40$)**: Two-wheeler recall collapses to 14.3% and Bicycle to 31.6%.
- Detailed analysis of ethics, SHAP/LIME limitations on object detection, attack vectors, and defenses is documented in [NOTES.md](file:///c:/Users/yasin/OneDrive/Documents/ML_OPS/DS5619-MLOPS/Week10/week10-fairness-audit/NOTES.md).
