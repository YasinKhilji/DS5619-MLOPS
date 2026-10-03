# NOTES.md — Week 8: Drift and Observability Monitoring

**Student ID used with `generate_for_student.py`:**
<!-- paste the --student-id value you used -->
142301017


## Drift level vs. expectation

<!-- What drift level did the report show, and does that match what you'd
     expect given the two cameras were built with deliberately different
     visual statistics? -->

The report shows **moderate drift**, with a PSI of **0.1217**.
This makes sense because the reference camera (`camera_A_daylight`) and the live camera (`camera_B_lowlight`) were created under different lighting conditions. So, the difference in their visual statistics is expected to cause some drift.

## What confidence-score-only monitoring misses

<!-- What would you monitor IN ADDITION to confidence score if you had
     access to ground-truth labels a day later? (Tie this to the kinds of
     drift from the lecture — which one does confidence-score-only
     monitoring miss?) -->

Confidence-score monitoring only looks at how confident the model is in its predictions. If we get the actual labels later, I would also check how well the model is performing by looking at things like accuracy and prediction errors.

This would help detect **concept drift**, where the relationship between the input data and the correct output changes, even if the confidence scores still look similar.