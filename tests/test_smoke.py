"""End-to-end smoke test on synthetic data with a local SQLite database."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, inspect

ROOT = Path(__file__).resolve().parents[1]


def test_pipeline_end_to_end(tmp_path):
    env = {
        **os.environ,
        "DATA_DIR": str(tmp_path / "data"),
        "MODELS_DIR": str(tmp_path / "models"),
        "FIGURES_DIR": str(tmp_path / "figs"),
        "PYTHONPATH": str(ROOT / "src"),
        "RAW_CSV": "", "DATABASE_URL": "", "AZURE_SQL_SERVER": "", "MAX_STEP": "",
    }
    r = subprocess.run(
        [sys.executable, "-m", "frp.run_all", "--synthetic", "--rows", "30000"],
        env=env, capture_output=True, text=True, cwd=ROOT,
    )
    assert r.returncode == 0, r.stdout + r.stderr

    q = json.loads((tmp_path / "data/curated/quality_report.json").read_text())
    assert q["rows_rejected"] > 0 and q["rows_clean"] > 0

    m = json.loads((tmp_path / "models/test_metrics.json").read_text())
    assert m["pr_auc"] > 0.5

    eng = create_engine(f"sqlite:///{tmp_path / 'data' / 'frp_local.db'}")
    tables = set(inspect(eng).get_table_names())
    assert {"fact_transactions", "fact_alerts", "threshold_metrics",
            "segment_metrics", "model_metrics", "data_quality"} <= tables
    alerts = pd.read_sql("select * from fact_alerts", eng)
    assert len(alerts) > 0 and alerts["reason_1"].str.len().min() > 0
    assert (tmp_path / "figs" / "shap_global_importance.png").exists()
