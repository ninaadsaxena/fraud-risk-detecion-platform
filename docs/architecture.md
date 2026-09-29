# Architecture

## Layers
| Layer | Location | Contents |
|---|---|---|
| Raw | `data/raw/` (and `raw` container, optional) | Source CSV as downloaded |
| Curated | `data/curated/` / `curated` container | Validated `transactions.parquet`, `rejected_rows.csv`, `quality_report.json` |
| Gold | `data/gold/` / `gold` container | Star schema + model outputs (Parquet) |
| Serving | Azure SQL Database | Same gold tables, queried by Power BI |

## Star schema
- `fact_transactions` (grain: one transaction) -> `dim_time` (step), `dim_type`, hashed account keys (`dim_account`)
- Model outputs: `fact_alerts` (one row per alerted test transaction, with top-3 SHAP reasons),
  `threshold_metrics`, `segment_metrics`, `model_metrics`, `data_quality`

## Data-quality rules (`ingest.py`)
Reject: null required field, unknown type, invalid step, negative amount, negative balance, invalid label.
Warn only: zero amount. Rejected rows are written out with the failing rule, never silently dropped.

## Data lineage (add your own diagram here)
raw CSV -> ingest (rules) -> curated Parquet -> gold star schema -> model -> alerts/metrics -> Azure SQL -> Power BI.
Export the Mermaid diagram from the README as `architecture.png` and commit it here.
