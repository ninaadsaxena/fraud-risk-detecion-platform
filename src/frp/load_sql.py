"""Step 5: load gold tables + quality report into Azure SQL (or SQLite locally)."""
import json
import os

import pandas as pd

from . import config

TABLES = [
    "dim_type", "dim_time", "dim_account", "fact_transactions",
    "fact_alerts", "threshold_metrics", "segment_metrics", "model_metrics",
]


def run() -> None:
    mode = os.getenv("LOAD_MODE", "replace")  # "append" if you created tables with sql/schema.sql
    scope = os.getenv("LOAD_SCOPE", "all")
    engine = config.get_engine()
    print(f"[load] target dialect: {engine.dialect.name}, mode={mode}, scope={scope}")

    test_start = None
    if scope == "test_period":
        meta = json.loads((config.MODELS_DIR / "train_meta.json").read_text())
        test_start = meta["test_start_step"]

    for t in TABLES:
        df = pd.read_parquet(config.GOLD_DIR / f"{t}.parquet")
        if t == "fact_transactions" and test_start is not None:
            df = df[df["step"] > test_start]
        df.to_sql(t, engine, if_exists=mode, index=False, chunksize=10_000)
        print(f"[load] {t}: {len(df):,} rows")

    q = json.loads((config.CURATED_DIR / "quality_report.json").read_text())
    dq = pd.DataFrame(q["rules"])
    dq["rows_in"] = q["rows_in"]
    dq.to_sql("data_quality", engine, if_exists=mode, index=False)
    print("[load] data_quality loaded")


if __name__ == "__main__":
    run()
