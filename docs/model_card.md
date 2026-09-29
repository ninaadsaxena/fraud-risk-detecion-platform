# Model card: Fraud risk model (LightGBM)

> Template. Replace every `[ ]` with results from your real run. Delete this line.

## Intended use
Rank transactions for analyst review in a demonstration setting. **Not** for production decisions or any use on real customers.

## Data
- Source: PaySim synthetic mobile-money transactions (Kaggle). Rows used: [ ] (MAX_STEP = [ ]).
- Fraud prevalence: [ ]%. Label: `isFraud`. `isFlaggedFraud` is not used.
- Personal data: none (synthetic). Account IDs are salted-hashed in the gold layer anyway.

## Model
- LightGBM, `scale_pos_weight` from the training split, early stopping on validation PR-AUC.
- Chronological split: train <= [ ], validation <= [ ], test > [ ] (steps).
- Two feature sets: `conservative` (no balance-error features) and `full`. See README.
- Alert threshold: minimises validation cost = missed-fraud amount + `REVIEW_COST` x alerts. REVIEW_COST = [ ].

## Performance (test period only)
| Feature set | PR-AUC | ROC-AUC | Precision | Recall | Cost with model | Cost without model |
|---|---|---|---|---|---|---|
| conservative | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| full | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |

Accuracy is not reported: with extreme class imbalance it is uninformative.

## Explainability
Global SHAP importance: `docs/figures/shap_global_importance.png`. Each alert stores its top 3 SHAP reasons in `fact_alerts`.
SHAP shows what drove the score, not why fraud happened.

## Segment analysis
See `segment_metrics` (type, amount band, time of day): [summarise weak spots here].
This is **not** a protected-attribute fairness test because the dataset has no such fields.

## Limitations and risks
- Synthetic data; simulator artefacts (balance-error features) inflate the `full` results.
- Threshold depends on the assumed cost ratio, which is invented here.
- No drift monitoring, no human-in-the-loop measurement.

## Monitoring plan (proposed, not implemented)
Track alert volume, precision on reviewed alerts, score distribution drift, and cost per period; retrain on a schedule
and whenever drift or precision degrades beyond agreed limits.
