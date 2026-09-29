-- Optional convenience views (T-SQL). Power BI can also compute all of this with DAX.
CREATE OR ALTER VIEW vw_daily_kpis AS
SELECT t.day,
       COUNT(*)                                   AS txns,
       SUM(CAST(f.is_fraud AS INT))               AS fraud_txns,
       SUM(f.amount)                              AS total_amount,
       SUM(CASE WHEN f.is_fraud = 1 THEN f.amount ELSE 0 END) AS fraud_amount
FROM fact_transactions f
JOIN dim_time t ON t.step = f.step
GROUP BY t.day;
GO

CREATE OR ALTER VIEW vw_alert_queue AS
SELECT a.txn_id, a.step, a.type_name, a.amount, a.fraud_score,
       a.reason_1, a.reason_2, a.reason_3
FROM fact_alerts a;
GO
