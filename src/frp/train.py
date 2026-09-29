"""Step 3: train LightGBM on a chronological split; pick the alert threshold by expected cost."""
import argparse
import json
from datetime import datetime, timezone

import joblib
import numpy as np
from lightgbm import LGBMClassifier, early_stopping
from sklearn.metrics import average_precision_score

from . import config
from .features import alert_cost, build_features, load_model_frame, time_split


def run(feature_set: str = "full") -> dict:
    df = load_model_frame()
    tr, va, te, cuts = time_split(df)
    X = build_features(df, feature_set)
    y = df["is_fraud"]
    print(f"[train] rows train/val/test = {tr.sum():,}/{va.sum():,}/{te.sum():,}; "
          f"fraud train={int(y[tr].sum())} val={int(y[va].sum())} test={int(y[te].sum())}")
    if y[tr].sum() == 0 or y[va].sum() == 0:
        raise RuntimeError("No fraud cases in train or validation split; use more data.")

    pos = int(y[tr].sum())
    neg = int((y[tr] == 0).sum())
    model = LGBMClassifier(
        n_estimators=500, learning_rate=0.05, num_leaves=31, subsample=0.8, subsample_freq=1,
        colsample_bytree=0.8, scale_pos_weight=min(neg / max(pos, 1), 100.0),
        random_state=config.RANDOM_STATE, n_jobs=-1, verbose=-1,
    )
    model.fit(
        X[tr], y[tr], eval_set=[(X[va], y[va])], eval_metric="average_precision",
        callbacks=[early_stopping(30, verbose=False)],
    )

    p_val = model.predict_proba(X[va])[:, 1]
    amt_val = df.loc[va, "amount"].values
    y_val = y[va].values

    best = None
    for thr in np.linspace(0.02, 0.98, 97):
        c = alert_cost(y_val, amt_val, p_val >= thr, config.REVIEW_COST)
        if best is None or c["total_cost"] < best[1]["total_cost"]:
            best = (float(thr), c)
    thr, cost = best
    baseline = alert_cost(y_val, amt_val, np.zeros_like(y_val), config.REVIEW_COST)["total_cost"]

    meta = {
        "feature_set": feature_set,
        "features": list(X.columns),
        "threshold": thr,
        "review_cost": config.REVIEW_COST,
        "val_pr_auc": float(average_precision_score(y_val, p_val)),
        "val_cost_at_threshold": cost["total_cost"],
        "val_cost_no_model": baseline,
        "test_start_step": cuts["val_max_step"],
        **cuts,
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    joblib.dump(model, config.MODELS_DIR / "model.joblib")
    (config.MODELS_DIR / "train_meta.json").write_text(json.dumps(meta, indent=2))
    print(f"[train] threshold={thr:.2f} val PR-AUC={meta['val_pr_auc']:.3f}")
    return meta


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--feature-set", choices=["full", "conservative"], default="full")
    run(ap.parse_args().feature_set)
