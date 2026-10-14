# NOTES.md — Week 10: Fairness and Robustness Audit

**Student ID used with `generate_for_student.py`:**
`142301017`
(Deterministically generated seed: `3926553592`)


## Which classes got flagged?

Running the clean audit on our personalized fixtures (`data/fixtures/`) under the 90% recall threshold (`recall_threshold = 0.90`) flagged three categories:
- **Bicycle**: 14 / 19 = **73.68%** (flagged)
- **Two-wheeler**: 11 / 14 = **78.57%** (flagged)
- **Hatchback**: 16 / 18 = **88.89%** (flagged)

All other classes remained strictly above the threshold: Truck (90.9%), Three-wheeler (93.3%), Sedan (93.8%), Mini-bus (94.4%), LCV (94.4%), SUV (95.5%), and Other, Van, MUV, Tempo-traveller, and Bus all at 100.0%.

This outcome directly matches what is expected from how `generate_for_student.py` constructs the fixtures:
1. **Structural Disparity in Small Vehicles**: `generate_for_student.py` assigns per-class size multipliers where small classes are scaled down dramatically (`Bicycle: 0.35`, `Two-wheeler: 0.45`), whereas large classes receive multipliers of 1.8 to 2.2 (`Bus: 2.2`, `Truck: 2.0`). In `mock_detector.py`, detection requires a connected component of at least 20 contiguous reddish pixels (`len(pts) >= 20`). For bicycles and two-wheelers, bounding boxes are often as small as $7 \times 6$ or $15 \times 6$ pixels; once outlines and camera noise are factored in, connected reddish components frequently fall below 20 pixels or fail IoU overlap. `generate_for_student.py` intentionally tests and retries sub-seeds to ensure that `Bicycle` and `Two-wheeler` both land below 90% while no large class does.
2. **Sampling Noise vs. Real Disparity**: `Hatchback` (88.89%) has a baseline size multiplier of 1.0, but with only 18 ground-truth instances, missing merely 2 boxes drops recall from 100% to 88.89%. As highlighted in `README.pdf`, with small sample sizes (~5–30 boxes per class), an 88.9% vs 94.4% recall difference is finite-sample sampling noise rather than a structural algorithmic deficit like the one affecting bicycles and two-wheelers.


## If the grouping variable were a protected attribute

If the grouping variable were a protected demographic attribute (e.g., race, ethnicity, sex/gender, age, or disability status) under frameworks such as Title VII of the Civil Rights Act, the Equal Credit Opportunity Act (ECOA), or the EU AI Act, the stakes and engineering obligations would fundamentally change:

1. **Ethical Stakes & Harm Severity**:
   - In vehicle detection, missing a bicycle or hatchback results in traffic management inaccuracies or degraded toll/parking automation.
   - Across protected human groups, performance disparities translate directly into **allocative harms** (e.g., systemic denial of mortgages, employment opportunities, or healthcare resources) and **representational / physical harms** (e.g., facial recognition misidentifications leading to wrongful arrests, or medical diagnosis models underdiagnosing underserved groups).

2. **Legal and Regulatory Obligations**:
   - Disparities across protected classes trigger strict liability under disparate impact doctrines and AI regulatory standards (such as the EU AI Act's mandatory conformity assessments for high-risk systems and FTC enforcement on algorithmic bias).
   - An engineer would be legally prohibited from deploying a model showing statistically significant disparate performance without documented business necessity and exhaustive exploration of less discriminatory alternatives.

3. **Engineering Obligations**:
   - **No Dismissal as "Noise"**: Sampling noise cannot be brushed aside; the engineering team has an affirmative obligation to collect statistically representative datasets across all demographic groups and intersections (e.g., race $\times$ gender).
   - **Active Bias Mitigation**: Engineers must implement formalized mitigation across the ML lifecycle:
     - *Pre-processing*: Re-weighting and re-sampling training splits to balance group representations.
     - *In-processing*: Fairness-constrained loss formulations (e.g., adversarial debiasing or minimax optimization for equal opportunity).
     - *Post-processing*: Calibrated threshold adjustments (Equalized Odds post-processing) ensuring group-level true positive rate parity.
   - **Continuous Fairness Monitoring & Governance**: Deployment requires continuous production monitoring for fairness drift (monitoring true positive and selection rates per group in real time) with automated circuit breakers and human-in-the-loop fallback procedures whenever disparities widen.


## Which attack could corrupt this audit?

- **Lifecycle Stage**: Data Preparation & Evaluation Pipeline.
- **Attack**: **Evaluation Data Poisoning / Integrity Tampering**.
  - An adversary (such as an insider under pressure to meet deployment targets, a compromised third-party data vendor, or an attacker wishing to mask surveillance flaws) could tamper with the evaluation dataset (`data/fixtures/`) or its annotation manifest (`_annotations.coco.json`).
  - By injecting tiny clusters of reddish pixels (satisfying $r > 120, r - g > 40, r - b > 40$) into the ground-truth regions of missed bicycles and two-wheelers, or by altering the bounding box annotations of missed objects, the attacker can artificially inflate detection recall for `Bicycle` and `Two-wheeler` above 90%.
  - Because the pipeline measures per-class recall mechanically, this attack would silently produce a passing audit report (`fairness_report.json`), masking an active, hazardous disparity from auditors and decision-makers without altering model code.
- **Control from the Lecture**:
  - **Cryptographic Provenance & Immutable Data Versioning**: Store evaluation fixtures and ground-truth manifests in an immutable, cryptographically signed data store (e.g., using DVC, LakeFS, or signed Git LFS with SHA-256 integrity verification). The audit pipeline must verify cryptographic checksums before running evaluations. Any unauthorized modification aborts execution immediately.
  - **Sanitization & Anomaly Checks**: Implement pre-audit automated data validation to flag statistical anomalies in fixture distributions (such as unnatural color variance or bounding box anomalies).
  - **Segregated Audit Infrastructure**: Run compliance audits within an isolated, read-only CI/CD environment with strict role-based access control, ensuring model developers and untrusted pipelines cannot modify audit data.


## Would SHAP or LIME explain a missed detection?

- **Specific Missed Box**:
  - In `camera_A_daylight/006.jpg`, a ground-truth `Bicycle` box at `bbox = [13, 75, 7, 6]` (width = 7, height = 6, area = 42 pixels) is completely missed by the detector (`detections = []` overlapping this region).
- **Would SHAP or LIME actually help?**
  - **No.** Neither SHAP nor LIME would provide a meaningful or useful explanation for *why* the detector missed this box.
- **What Breaks Both Tools' Assumptions**:
  1. **Absence of Output Prediction (The False-Negative Challenge)**:
     - Both SHAP (KernelSHAP) and LIME are built to explain an *existing scalar model output* $f(x)$ (such as a class probability or regression score).
     - In object detection, the output is a variable-length list of detected bounding boxes $[(x, y, w, h), \text{category}, \text{score}]$. For a false negative (missed detection), there is **no output detection object** at that spatial location. Because there is no predicted instance or score to attribute feature importance to, standard SHAP/LIME cannot even be instantiated without defining an artificial, ad-hoc surrogate (e.g., maximum IoU detection score over the region), which defeats the purpose of local attribution.
  2. **Non-Local Spatial Connectivity vs. Superpixel Masking**:
     - LIME relies on segmenting the image into superpixels (via SLIC/Quickshift) and toggling them on or off to train an interpretable local linear surrogate.
     - However, object detection in this model operates via **connected component flood filling** (`mock_detector.py:flood`), where pixels must form an unbroken 4-connected cluster of at least 20 qualifying pixels. Superpixel masking introduces artificial geometric boundaries that shatter spatial contiguity, obscuring the true mechanism of the detector.
  3. **Non-Additive Discontinuous Thresholds**:
     - SHAP assumes features contribute additively towards an output expectation (the Shapley efficiency property: $\sum \phi_i = f(x) - \mathbb{E}[f]$).
     - Here, the decision logic is a discontinuous conjunction of sharp thresholds: $r > 120 \land (r - g) > 40 \land (r - b) > 40 \land \text{connected\_pixels} \ge 20$. In our $7 \times 6$ bicycle box (42 pixels total), boundary outlines and daylight noise left fewer than 20 qualifying contiguous pixels. Additive feature attribution across superpixels cannot capture this joint spatial-connectivity constraint.
  4. **Appropriate Explanation Method**:
     - Rather than feature attribution methods, explaining missed detections requires **geometric counterfactual analysis** (e.g., computing the minimum bounding box scale expansion or contrast increase required to cross the 20-pixel threshold) or anchor/rule explanations over bounding box properties.


## What did your attack show?

### 1. Recall Breakdown Under Attack
Under the white-box FGSM-style perturbation (decreasing red by $\epsilon$ and increasing green/blue by $\epsilon$, clamped to $[0, 255]$), recall evolved across budgets $\epsilon \in [0, 10, 20, 30, 40]$ as follows:

| Vehicle Class | $\epsilon = 0$ (Clean) | $\epsilon = 10$ | $\epsilon = 20$ | $\epsilon = 30$ | $\epsilon = 40$ |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Bicycle** | 73.7% | 63.2% | 63.2% | 47.4% | 31.6% |
| **Two-wheeler** | 78.6% | 64.3% | 42.9% | 28.6% | 14.3% |
| **Hatchback** | 88.9% | 94.4% | 83.3% | 77.8% | 61.1% |
| **Van** | 100.0% | 86.7% | 60.0% | 46.7% | 40.0% |
| **Bus** | 100.0% | 84.0% | 72.0% | 68.0% | 44.0% |
| **Other** | 100.0% | 91.7% | 75.0% | 41.7% | 8.3% |
| **Sedan** | 93.8% | 87.5% | 75.0% | 62.5% | 31.3% |
| **Mini-bus** | 94.4% | 94.4% | 77.8% | 61.1% | 55.6% |
| **LCV** | 94.4% | 83.3% | 72.2% | 61.1% | 50.0% |
| **MUV** | 100.0% | 81.8% | 81.8% | 81.8% | 45.5% |
| **Three-wheeler**| 93.3% | 86.7% | 86.7% | 60.0% | 40.0% |
| **Truck** | 90.9% | 90.9% | 90.9% | 90.9% | 90.9% |
| **SUV** | 95.5% | 95.5% | 95.5% | 59.1% | 54.5% |
| **Tempo-traveller**| 100.0% | 100.0% | 100.0% | 78.6% | 71.4% |

- `Bicycle` falls immediately at $\epsilon = 10$ (73.7% $\to$ 63.2%), stabilizes at $\epsilon = 20$, and then plunges at $\epsilon = 30$ (47.4%) and $\epsilon = 40$ (31.6%).
- `Two-wheeler` experiences a steep, continuous drop at every single increment: 78.6% $\to$ 64.3% $\to$ 42.9% $\to$ 28.6% $\to$ 14.3%, suffering near-total blindness by $\epsilon = 40$.
- `Hatchback` fluctuates slightly at $\epsilon = 10$ (94.4%, due to minor pixel shifts altering connected blob boundaries), then drops steadily: 83.3% at $\epsilon = 20$, 77.8% at $\epsilon = 30$, and 61.1% at $\epsilon = 40$.

### 2. Most Fragile Class vs. Clean Audit Flags
At the report budget ($\epsilon = 20$), `most_fragile` ranks the largest drop in recall ($\text{Recall}_0 - \text{Recall}_{20}$):
1. **Van**: drop = **0.4000** (100.0% $\to$ 60.0%, $-40.0\%$)
2. **Two-wheeler**: drop = **0.3571** (78.6% $\to$ 42.9%, $-35.7\%$)
3. **Bus**: drop = **0.2800** (100.0% $\to$ 72.0%, $-28.0\%$)

**Is it the same class the clean audit flagged?**
- No, not completely. The clean audit flagged `Bicycle`, `Two-wheeler`, and `Hatchback`.
- In contrast, the most fragile class by recall drop is **Van** (which had a perfect 100% clean recall). Only `Two-wheeler` appears in both the clean audit flagged categories and the top-3 most fragile categories.

### 3. Drop Ranking (`most_fragile`) vs. Absolute Performance (`lowest_recall_under_attack`)
At $\epsilon = 20$, the categories with the lowest absolute recall under attack are:
1. **Two-wheeler**: **42.86%**
2. **Van**: **60.00%**
3. **Bicycle**: **63.16%**

- **Do they agree?** No. `Bicycle` dropped only 10.5% (from 73.7% to 63.2%), so it did not make the top-3 drop ranking (`most_fragile`). Conversely, `Bus` dropped 28.0% (making it the 3rd most fragile), yet its absolute recall remains 72.0%—well above Bicycle and Two-wheeler.
- **Which is the better measure of who is hurt?** `lowest_recall_under_attack` is the superior measure of real-world harm. A relative drop only measures mathematical sensitivity to perturbation. For vulnerable road users, absolute detection rate dictates physical safety: whether a cyclist is missed 37% of the time (recall = 63%) or a motorcyclist is missed 57% of the time (recall = 43%) represents an immediate safety hazard, regardless of whether their baseline was already deficient.
- **Who bears the cost?** The cost is disproportionately borne by groups that already face baseline disadvantages (small-vehicle users like cyclists and motorcyclists). Because their visual footprint is small, any perturbation or distribution shift pushes them far past the point of operational failure (down to 14% at $\epsilon = 40$), while large vehicles like Trucks and Tempo-travellers remain robustly detected.

### 4. Adversarial Training and Input Validation
- **Input Validation**:
  - Implement real-time channel statistics checking: compute the image-wide chromatic distributions $\mathbb{E}[R - G]$ and $\mathbb{E}[R - B]$ and compare against historical camera profile baselines.
  - Apply automated color constancy / white-balance normalization (e.g., Gray World or Shades of Gray algorithm, histogram equalization) to re-align shifted channel distributions prior to detector inference.
- **Adversarial Training**:
  - In a learned model, adversarial training involves augmenting training batches with multi-step FGSM/PGD perturbed images.
  - For this rule-based detector, adversarial hardening would involve expanding the color rule boundaries to accommodate chromatic shifts (e.g., accepting $(r - g) > 40 - 2\epsilon$ or using a Mahalanobis distance metric in RGB space rather than hard axis-aligned cuts).

### 5. Why Does a Simple Rule Break More Easily Than a CNN (or Does It)?
- **Analytical Brittleness of the Handcrafted Rule**:
  - The mock detector uses a rigid, hardcoded, axis-aligned decision rule: $r > 120 \land r - g > 40 \land r - b > 40$.
  - In a white-box setting, the gradient sign is analytically exact and uniform across all pixels. Shifting red down and green/blue up by $\epsilon$ systematically pushes pixels across the threshold with 100% spatial efficiency. There is zero feature redundancy, spatial hierarchy, or contextual understanding.
- **Comparison to CNNs**:
  - A CNN utilizes hierarchical convolutional features (edges, textures, shapes, spatial context) trained across thousands of parameters. Because CNNs typically undergo data augmentation (such as color jitter and brightness variations), a uniform color shift of $\pm 10$ or $\pm 20$ intensity levels usually does not collapse high-level feature representations.
  - However, CNNs are notorious for being vulnerable to *imperceptible high-frequency adversarial perturbations* ($\epsilon \approx 8/255$ under $L_\infty$), which exploit high-dimensional linearity without causing visible color shifts. Thus, while the simple rule breaks easily under visible macro-level photometric shifts, CNNs are far more susceptible to imperceptible, adversarial noise.
