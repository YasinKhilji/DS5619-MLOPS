"""
Feature drift monitoring for the vehicle detector — this week's lecture
content (univariate drift, PSI) applied to the detector's own confidence
scores as the monitored feature.

BMD-45's paper reports a real domain-shift finding: the SAME detector
architecture scores ~33.6% mAP when trained on a different dataset and
evaluated on BMD-45's real-world CCTV footage, versus ~83.8% mAP when
trained in-domain on BMD-45 itself. `data/fixtures/camera_A_daylight/` and
`data/fixtures/camera_B_lowlight/` are a synthetic, illustrative stand-in
for that same idea — same detector, two different visual conditions.
Confidence score
is the feature we monitor here because it's the one thing a production
system has at inference time without ground truth labels (which is exactly
why feature/prediction drift monitoring exists — you often don't get labels
in real time).

Fill in the four functions marked # TODO. Constants above them are given.
"""
import glob
import math
import os
import statistics
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mock_detector as det

PSI_MODERATE_THRESHOLD = 0.10
PSI_SIGNIFICANT_THRESHOLD = 0.25
N_BINS = 10


# ---------------------------------------------------------------------------
# Part 1 — Extract the monitored feature (confidence scores) from a camera
# ---------------------------------------------------------------------------

def extract_confidence_scores(camera_dir):
    """Run the detector over every *.jpg image in `camera_dir` (use
    glob.glob(os.path.join(camera_dir, "*.jpg")), sorted for determinism)
    and return a flat list of every detection's confidence score (float)
    across all images in that directory.

    Use Image.open(path).convert("RGB") to load each image, then
    det.detect(image) to get its detections, and collect d.score from each.
    """
    scores = []

    for path in sorted(glob.glob(os.path.join(camera_dir, "*.jpg"))):
        image = Image.open(path).convert("RGB")
        detections = det.detect(image)

        for d in detections:
            scores.append(float(d.score))

    return scores


# ---------------------------------------------------------------------------
# Part 2 — Population Stability Index between a reference and live distribution
# ---------------------------------------------------------------------------

def compute_psi(reference_scores, live_scores, n_bins=N_BINS):
    """Compute the Population Stability Index between two lists of scores,
    both assumed to lie in [0.0, 1.0] (confidence scores).

    Steps:
      1. Split [0.0, 1.0] into `n_bins` equal-width bins.
      2. For each bin, compute the PROPORTION (count / total) of
         reference_scores and of live_scores that fall in it. A score of
         exactly 1.0 belongs in the last bin.
      3. To avoid division by zero / log(0) for empty bins, clamp every
         proportion to a minimum of 1e-4 before using it in the ratio/log
         below.
      4. PSI = sum over bins of (live_pct - ref_pct) * ln(live_pct / ref_pct)
      5. Return the PSI value (float). Larger values mean more drift; PSI
         is 0 when the two distributions are identical.
    """
    bin_width = 1.0 / n_bins

    ref_counts = [0] * n_bins
    live_counts = [0] * n_bins

    for score in reference_scores:
        index = min(int(score / bin_width), n_bins - 1)
        ref_counts[index] += 1

    for score in live_scores:
        index = min(int(score / bin_width), n_bins - 1)
        live_counts[index] += 1

    ref_total = len(reference_scores)
    live_total = len(live_scores)

    psi = 0.0

    for i in range(n_bins):
        ref_pct = max(ref_counts[i] / ref_total, 1e-4)
        live_pct = max(live_counts[i] / live_total, 1e-4)

        psi += (live_pct - ref_pct) * math.log(live_pct / ref_pct)

    return float(psi)


# ---------------------------------------------------------------------------
# Part 3 — Turn a PSI value into an actionable label
# ---------------------------------------------------------------------------

def classify_drift(psi):
    """Standard PSI interpretation bands:
      psi < PSI_MODERATE_THRESHOLD           -> "none"
      PSI_MODERATE_THRESHOLD <= psi < PSI_SIGNIFICANT_THRESHOLD -> "moderate"
      psi >= PSI_SIGNIFICANT_THRESHOLD       -> "significant"

    Return one of those three strings.
    """
    if psi < PSI_MODERATE_THRESHOLD:
        return "none"
    elif psi < PSI_SIGNIFICANT_THRESHOLD:
        return "moderate"
    else:
        return "significant"


# ---------------------------------------------------------------------------
# Part 4 — Summary statistics for a score distribution (for the report)
# ---------------------------------------------------------------------------

def summarize_scores(scores):
    """Return a dict: {"count": int, "mean": float, "std": float,
    "min": float, "max": float}, all rounded to 4 decimal places except
    count. Use the `statistics` module (mean, stdev — if len(scores) < 2,
    std should be 0.0 rather than raising).
    """
    count = len(scores)

    if count == 0:
        return {
            "count": 0,
            "mean": 0.0,
            "std": 0.0,
            "min": 0.0,
            "max": 0.0,
        }

    mean = statistics.mean(scores)
    std = statistics.stdev(scores) if count >= 2 else 0.0

    return {
        "count": count,
        "mean": round(mean, 4),
        "std": round(std, 4),
        "min": round(min(scores), 4),
        "max": round(max(scores), 4),
    }
