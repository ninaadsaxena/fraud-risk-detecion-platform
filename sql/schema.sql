-- Optional strict schema for Azure SQL Database (T-SQL).
-- Use it if you prefer explicit types/keys: run this first, then set LOAD_MODE=append in .env.
-- Otherwise leave LOAD_MODE=replace and pandas will create the tables for you.

CREATE TABLE dim_type (type_id INT NOT NULL PRIMARY KEY, type_name VARCHAR(20) NOT NULL);
CREATE TABLE dim_time (step INT NOT NULL PRIMARY KEY, day INT NOT NULL, hour INT NOT NULL, part_of_day VARCHAR(10) NOT NULL);
CREATE TABLE dim_account (account_key CHAR(16) NOT NULL PRIMARY KEY, account_kind VARCHAR(10) NOT NULL);

CREATE TABLE fact_transactions (
    txn_id BIGINT NOT NULL PRIMARY KEY,
    step INT NOT NULL REFERENCES dim_time(step),
    type_id INT NOT NULL REFERENCES dim_type(type_id),
    amount FLOAT NOT NULL,
    orig_key CHAR(16) NOT NULL,
    dest_key CHAR(16) NOT NULL,
    dest_is_merchant TINYINT NOT NULL,
    oldbalance_orig FLOAT, newbalance_orig FLOAT,
    oldbalance_dest FLOAT, newbalance_dest FLOAT,
    is_fraud TINYINT NOT NULL
);
CREATE INDEX ix_fact_step ON fact_transactions(step);

CREATE TABLE fact_alerts (
    txn_id BIGINT NOT NULL PRIMARY KEY,
    step INT NOT NULL, type_name VARCHAR(20), amount FLOAT, fraud_score FLOAT, is_fraud TINYINT,
    reason_1 VARCHAR(200), reason_2 VARCHAR(200), reason_3 VARCHAR(200)
);

CREATE TABLE threshold_metrics (
    threshold FLOAT, alerts INT, tp INT, fp INT, fn INT,
    missed_fraud_amount FLOAT, caught_fraud_amount FLOAT, review_cost FLOAT, total_cost FLOAT,
    precision_val FLOAT, recall_val FLOAT, is_chosen TINYINT
);
CREATE TABLE segment_metrics (
    segment_type VARCHAR(30), segment VARCHAR(30), n INT, fraud_count INT, alerts INT, tp INT,
    precision_val FLOAT, recall_val FLOAT
);
CREATE TABLE model_metrics (
    feature_set VARCHAR(20), test_rows INT, test_fraud INT, pr_auc FLOAT, roc_auc FLOAT,
    threshold FLOAT, precision_val FLOAT, recall_val FLOAT, total_cost FLOAT, cost_no_model FLOAT,
    test_start_step FLOAT, trained_at VARCHAR(40)
);
CREATE TABLE data_quality (
    rule VARCHAR(40), severity VARCHAR(10), rows_flagged INT, share FLOAT, rows_in INT
);
