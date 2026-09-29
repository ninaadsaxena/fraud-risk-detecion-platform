# Power BI dashboard guide

Power BI Desktop is a free app but, as far as I know, Windows-only. On a Mac, use a Windows PC/VM or a university lab machine.
A free Power BI licence cannot share reports with other people, so deliver the `.pbix` file, screenshots and a short
screen recording (put them in this folder and link them from the main README).

## 1. Connect
Get data > **Azure SQL Database** > server + database > **Import** mode. Load: `fact_transactions`, `fact_alerts`,
`dim_time`, `dim_type`, `threshold_metrics`, `segment_metrics`, `model_metrics`, `data_quality`.
(If your `fact_transactions` is huge, run with `LOAD_SCOPE=test_period` first.)

## 2. Model (Model view)
- `fact_transactions[step]` -> `dim_time[step]` (many-to-one)
- `fact_transactions[type_id]` -> `dim_type[type_id]` (many-to-one)
- `fact_alerts[txn_id]` -> `fact_transactions[txn_id]` (many-to-one)
- `threshold_metrics`, `segment_metrics`, `model_metrics`, `data_quality`: no relationships

## 3. Measures (paste into a `_Measures` table)
```DAX
Total Transactions = COUNTROWS(fact_transactions)
Fraud Transactions = CALCULATE(COUNTROWS(fact_transactions), fact_transactions[is_fraud] = 1)
Fraud Rate = DIVIDE([Fraud Transactions], [Total Transactions])
Fraud Amount = CALCULATE(SUM(fact_transactions[amount]), fact_transactions[is_fraud] = 1)

Alerts = COUNTROWS(fact_alerts)
True Alerts = CALCULATE(COUNTROWS(fact_alerts), fact_alerts[is_fraud] = 1)
Alert Precision = DIVIDE([True Alerts], [Alerts])
Caught Fraud Amount = CALCULATE(SUM(fact_alerts[amount]), fact_alerts[is_fraud] = 1)

Test Recall = MAX(model_metrics[recall_val])
Cost With Model = MAX(model_metrics[total_cost])
Cost Without Model = MAX(model_metrics[cost_no_model])
Cost Saving = [Cost Without Model] - [Cost With Model]
```
Note: alert measures cover the **test period** only; label those visuals accordingly.

## 4. Pages
1. **Executive overview:** cards (Total Transactions, Fraud Rate, Fraud Amount, Alerts, Cost Saving); fraud amount by `dim_time[day]`; fraud count by `dim_type[type_name]`.
2. **Model performance:** line chart of `threshold_metrics` (precision_val, recall_val vs threshold); `total_cost` vs threshold with the chosen point (`is_chosen = 1`) highlighted; cards for PR-AUC, ROC-AUC, threshold.
3. **Alert investigation:** table from `fact_alerts` sorted by `fraud_score` desc with `reason_1..3`; add a **drill-through** page for one `txn_id`.
4. **Segment analysis:** clustered bars of `recall_val` and `precision_val` from `segment_metrics` by `segment_type` (slicer) and `segment`. State clearly this is not a protected-attribute fairness test.
5. **Data quality:** `data_quality` table/bar (rule, rows_flagged) so reviewers see what was rejected and why.

## 5. Storytelling checklist
- One insight per page in the title (e.g. "The model cuts expected cost by X% at the chosen threshold").
- Consistent colours; no more than ~6 visuals per page; label the test-period scope.
- Add tooltips explaining precision, recall and the cost assumption (REVIEW_COST).

## 6. Deliverables to commit here
`fraud_risk.pbix` (or a note if too large), page screenshots (`01_overview.png` ...), and a 1-2 minute screen recording (MP4 or GIF).
