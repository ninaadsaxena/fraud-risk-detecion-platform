"""Step 1: raw CSV -> validated curated Parquet + rejected rows + data-quality report."""
import json

import numpy as np
import pandas as pd

from . import config

REQUIRED = [
    "step", "type", "amount", "nameOrig", "oldbalanceOrg", "newbalanceOrig",
    "nameDest", "oldbalanceDest", "newbalanceDest", "isFraud",
]
VALID_TYPES = {"PAYMENT", "TRANSFER", "CASH_OUT", "DEBIT", "CASH_IN"}
BALANCE_COLS = ["oldbalanceOrg", "newbalanceOrig", "oldbalanceDest", "newbalanceDest"]


def run() -> dict:
    path = config.raw_csv()
    print(f"[ingest] reading {path}")
    df = pd.read_csv(path)

    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"Raw file is missing required columns: {missing}")

    df.insert(0, "txn_id", np.arange(len(df), dtype="int64"))
    ms = config.max_step()
    if ms is not None:
        df = df[df["step"] <= ms].copy()
        print(f"[ingest] MAX_STEP={ms}: kept {len(df):,} rows")

    n_in = len(df)
    fraud_rate_in = float(df["isFraud"].mean()) if n_in else 0.0

    # (rule name, severity, boolean mask of offending rows)
    rules = [
        ("null_required_field", "reject", df[REQUIRED].isna().any(axis=1)),
        ("unknown_type", "reject", ~df["type"].isin(VALID_TYPES)),
        ("invalid_step", "reject", ~(df["step"] >= 1)),
        ("negative_amount", "reject", df["amount"] < 0),
        ("negative_balance", "reject", (df[BALANCE_COLS] < 0).any(axis=1)),
        ("invalid_label", "reject", ~df["isFraud"].isin([0, 1])),
        ("zero_amount", "warn", df["amount"] == 0),
    ]

    reject_mask = pd.Series(False, index=df.index)
    reason = pd.Series("", index=df.index, dtype="object")
    report_rules = []
    for name, severity, mask in rules:
        mask = mask.fillna(False)
        report_rules.append(
            {"rule": name, "severity": severity, "rows_flagged": int(mask.sum()),
             "share": float(mask.mean()) if n_in else 0.0}
        )
        if severity == "reject":
            newly = mask & ~reject_mask
            reason[newly] = name
            reject_mask |= mask

    rejected = df[reject_mask].assign(reject_reason=reason[reject_mask])
    clean = df[~reject_mask].copy()
    clean["isFraud"] = clean["isFraud"].astype("int8")
    clean["step"] = clean["step"].astype("int32")

    clean.to_parquet(config.CURATED_DIR / "transactions.parquet", index=False)
    rejected.to_csv(config.CURATED_DIR / "rejected_rows.csv", index=False)

    report = {
        "source_file": str(path.name),
        "rows_in": n_in,
        "rows_clean": int(len(clean)),
        "rows_rejected": int(len(rejected)),
        "fraud_rate_in": fraud_rate_in,
        "fraud_rate_clean": float(clean["isFraud"].mean()) if len(clean) else 0.0,
        "rules": report_rules,
    }
    (config.CURATED_DIR / "quality_report.json").write_text(json.dumps(report, indent=2))
    print(f"[ingest] clean={len(clean):,} rejected={len(rejected):,}")
    return report


if __name__ == "__main__":
    run()
