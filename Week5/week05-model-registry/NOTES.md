# NOTES.md — Week 5: Model Registry Governance

**Student ID used with `generate_for_student.py`:**
142301017

## Which candidate reached Production, and why?

Candidate B was registered as version v2 and successfully promoted to Production. It passed the required production checks because its F1 score was above the minimum threshold of 0.70 and its model card was complete. On the other hand, Candidate A was registered as version v1, but its F1 score was only 0.537, so its promotion to Production was correctly blocked.



## Gating stale feature data


To prevent models trained on outdated feature data from being promoted, I would add a feature-data freshness check to promote_model. The model’s manifest or training metadata would include the timestamp of the feature data used during training. Before promoting the model, the Production gate would check how old that data is and reject the model if it is more than 30 days old. In that case, it could raise a GovernanceError to prevent the promotion.



## Scaling the gate to 40 candidates

The registry design would not need any major changes if a hyperparameter search generated 40 candidates instead of just 2. The existing register_model() function already assigns a new version to each model without overwriting earlier versions, while promote_model() applies the same governance checks to any candidate being considered for Production.

The main change would be in the surrounding pipeline or model selection process. It would need to evaluate all 40 candidates, register the relevant ones, and determine which candidates are worth considering for promotion. The Production governance checks can stay the same, ensuring that every candidate still meets the required criteria before being promoted.
