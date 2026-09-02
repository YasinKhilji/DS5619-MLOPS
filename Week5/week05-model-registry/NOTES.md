# NOTES.md — Week 5: Model Registry Governance

**Student ID used with `generate_for_student.py`:**
142301017

## Which candidate reached Production, and why?

Candidate B was promoted to Production as version v2 because it had an F1 score of 0.828, which was above the required threshold of 0.70, and its model card was complete. Candidate A, registered as v1, was not promoted because its F1 score was only 0.537.




## Gating stale feature data


I would include the feature data timestamp in the model metadata and prevent the model from being promoted if the data is more than 30 days old.




## Scaling the gate to 40 candidates

No major changes would be needed in the registry. Each candidate can still be registered as a separate version, and the same Production checks can be applied to all of them. The main difference is that the pipeline would simply need to evaluate and register a larger number of candidates.

