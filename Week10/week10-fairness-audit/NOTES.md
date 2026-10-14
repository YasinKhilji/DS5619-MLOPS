# NOTES.md — Week 10: Fairness and Robustness Audit

**Student ID used with `generate_for_student.py`:**
142301017


## Which classes got flagged?

The flagged classes in my run were Bicycle (73.7%), Two-wheeler (78.6%), and Hatchback (88.9%).

Bicycle and Two-wheeler are expected to have lower recall because their smaller bounding boxes make them harder to detect with the detector's 20-pixel connected-component rule. Hatchback was also slightly below the 90% threshold. With only 18 ground-truth boxes, missing two instances gives a recall of 88.9%. This could be sampling noise, but more examples would be needed to confirm that.

## If the grouping variable were a protected attribute

If the groups represented protected demographic attributes instead of vehicle classes, the audit would have greater social and ethical importance. Poor performance for one group could lead to unfair treatment of people in real-world decisions like hiring, loan approvals, or policing. As an engineer, I would have a legal and ethical obligation to investigate the cause, report the disparity clearly, and work to reduce it before deploying the system (for example through re-sampling, adversarial debiasing, or adjusted classification thresholds). I would also need to consider privacy, monitor for fairness drift in production, and ensure the evaluation data represents the groups fairly instead of dismissing gaps as noise.


## Which attack could corrupt this audit?

Data poisoning during data collection could corrupt the audit if someone deliberately changed the images or their annotations. For example, changing ground-truth bounding boxes or labels could make the reported recall inaccurate and hide real detection failures. A useful control would be to validate the dataset using file hashes, keep a trusted version of the evaluation data, and restrict who can modify it.


## Would SHAP or LIME explain a missed detection?

SHAP and LIME explain model outputs by studying how input features affect a prediction. They would not directly explain a missed vehicle in this detector without some adaptation. For example, the missed bicycle in camera_A_daylight/006.jpg, with bounding box [13, 75, 7, 6], has no corresponding predicted box to explain. LIME's usual superpixel-based approach may also be unsuitable because this detector relies on connected pixels and a colour rule. I would first inspect the missed object's colour, size, and connectivity, especially the 20-pixel threshold, to understand why it was missed.


## What did your attack show?

Looking at `fairness_report.json["adversarial"]`:
- Bicycle recall drops from 73.7% at eps=0 down to 63.2% at eps=10 and eps=20, then falls further to 47.4% at eps=30 and 31.6% at eps=40.
- Two-wheeler drops steadily at each step: from 78.6% (eps=0) to 64.3% (eps=10), 42.9% (eps=20), 28.6% (eps=30), and collapses to 14.3% at eps=40.
- Hatchback drops from 88.9% (eps=0) to 83.3% at eps=20 and 61.1% at eps=40.

At eps=20, the most fragile class based on recall drop is Van (-40.0%), followed by Two-wheeler (-35.7%) and Bus (-28.0%). This is not the same class as the clean audit flagged; Van started with 100% recall, so losing 40% gave it the biggest drop.

Comparing the drop ranking (`most_fragile`) with `lowest_recall_under_attack` (Two-wheeler at 42.9%, Van at 60.0%, and Bicycle at 63.2%), they do not completely agree. The lowest recall under attack is the better measure of who is actually hurt, because road users who are missed most often face the real danger, regardless of their starting point. This shows that groups with smaller bounding boxes bear the heaviest cost of an attack or unmonitored failure.

One possible defence is input validation to check image colour channels for unusual shifts and normalize them with white-balancing before running detection. Adversarial training could also test the detector on perturbed images or broaden its colour thresholds. Since this detector depends on a simple, fixed colour rule, an attacker who knows the rule can easily shift pixel values across the threshold. A CNN learns richer spatial features and textures so simple uniform colour shifts affect it less, though CNNs can still be vulnerable to other adversarial noise.
