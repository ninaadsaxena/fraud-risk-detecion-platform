"""Step 4: test-set metrics, threshold grid, segment metrics, SHAP (global + per-alert reasons)."""
import json

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from sklearn.metrics import average_precision_score, roc_auc_score

from . import config
from .features import alert_cost, build_features, load_model_frame, time_split

MAX_ALERTS_EXPLAINED = 50_000
AMOUNT_BINS = [0, 1e3, 1e4, 1e5, 1e6, np.inf]
AMOUNT_LABELS = ["<1k", "1k-10k", "10k-100k", "100k-1M", ">1M"]


def _shap_matrix(explainer, X):
    sv = explainer.shap_values(X)
    if isinstance(sv, list):  # older shap: [class0, class1]
        sv = sv[1]
    sv = np.asarray(sv)
    if sv.ndim == 3:  # newer shap: (n, features, classes)
        sv = sv[:, :, 1]
    return sv


def _reasons(sv_row, x_row, cols, k=3):
    idx = np.argsort(-np.abs(sv_row))[:k]
    out = [f"{cols[i]}={x_row[i]:.4g} ({'+' if sv_row[i] >= 0 else '-'}{abs(sv_row[i]):.2f})" for i in idx]
    return out + [""] * (k - len(out))


def _seg_row(kind, name, y, alerted):
    y = np.asarray(y).astype(bool)
    a = np.asarray(alerted).astype(bool)
    tp = int((y & a).sum())
    return {
        "segment_type": kind, "segment": str(name), "n": int(len(y)),
        "fraud_count": int(y.sum()), "alerts": int(a.sum()), "tp": tp,
        "precision_val": tp / a.sum() if a.sum() else np.nan,
        "recall_val": tp / y.sum() if y.sum() else np.nan,
    }


def run() -> dict:
    meta = json.loads((config.MODELS_DIR / "train_meta.json").read_text())
    model = joblib.load(config.MODELS_DIR / "model.joblib")
    df = load_model_frame()
    _, _, te, _ = time_split(df)
    X_all = build_features(df, meta["feature_set"])
    d, X = df[te].copy(), X_all[te]
    y = d["is_fraud"].values
    p = model.predict_proba(X)[:, 1]
    thr = meta["threshold"]
    rc = meta["review_cost"]

    # ---- headline metrics
    at = alert_cost(y, d["amount"].values, p >= thr, rc)
    base = alert_cost(y, d["amount"].values, np.zeros_like(y), rc)
    metrics = {
        "feature_set": meta["feature_set"],
        "test_rows": int(len(d)),
        "test_fraud": int(y.sum()),
        "pr_auc": float(average_precision_score(y, p)) if y.sum() else np.nan,
        "roc_auc": float(roc_auc_score(y, p)) if 0 < y.sum() < len(y) else np.nan,
        "threshold": thr,
        "precision_val": at["tp"] / at["alerts"] if at["alerts"] else np.nan,
        "recall_val": at["tp"] / y.sum() if y.sum() else np.nan,
        "total_cost": at["total_cost"],
        "cost_no_model": base["total_cost"],
        "test_start_step": meta["test_start_step"],
        "trained_at": meta["trained_at"],
    }

    # ---- threshold grid (for the Power BI "model performance" page)
    rows = []
    for t in np.round(np.linspace(0.02, 0.98, 49), 3):
        c = alert_cost(y, d["amount"].values, p >= t, rc)
        rows.append({
            "threshold": float(t), **c,
            "precision_val": c["tp"] / c["alerts"] if c["alerts"] else np.nan,
            "recall_val": c["tp"] / y.sum() if y.sum() else np.nan,
            "is_chosen": int(abs(t - round(thr, 3)) < 0.0105),
        })
    threshold_metrics = pd.DataFrame(rows)

    # ---- segment metrics (NOT a protected-attribute fairness test; the data has none)
    alerted = p >= thr
    segs = []
    for name, m in d.groupby("type_name").indices.items():
        segs.append(_seg_row("transaction_type", name, y[m], alerted[m]))
    amt_bin = pd.cut(d["amount"], AMOUNT_BINS, labels=AMOUNT_LABELS, right=False)
    for name in AMOUNT_LABELS:
        m = (amt_bin == name).values
        if m.any():
            segs.append(_seg_row("amount_band", name, y[m], alerted[m]))
    hour = ((d["step"] - 1) % 24).values
    for name, lo, hi in [("night 00-05", 0, 5), ("morning 06-11", 6, 11),
                         ("afternoon 12-17", 12, 17), ("evening 18-23", 18, 23)]:
        m = (hour >= lo) & (hour <= hi)
        if m.any():
            segs.append(_seg_row("time_of_day", name, y[m], alerted[m]))
    segment_metrics = pd.DataFrame(segs)

    # ---- SHAP: global plot + per-alert reasons
    explainer = shap.TreeExplainer(model)
    cols = list(X.columns)
    rng = np.random.default_rng(config.RANDOM_STATE)
    samp = X.iloc[rng.choice(len(X), size=min(5000, len(X)), replace=False)]
    sv_samp = _shap_matrix(explainer, samp)
    plt.figure()
    shap.summary_plot(sv_samp, samp, show=False, plot_type="bar", max_display=12)
    plt.tight_layout()
    plt.savefig(config.FIGURES_DIR / "shap_global_importance.png", dpi=150)
    plt.close()

    alert_idx = np.where(alerted)[0]
    if len(alert_idx) > MAX_ALERTS_EXPLAINED:  # keep the highest-scoring alerts
        alert_idx = alert_idx[np.argsort(-p[alert_idx])[:MAX_ALERTS_EXPLAINED]]
    Xa = X.iloc[alert_idx]
    if len(Xa):
        sva = _shap_matrix(explainer, Xa)
        reasons = [_reasons(sva[i], Xa.values[i], cols) for i in range(len(Xa))]
    else:
        reasons = []
    alerts = pd.DataFrame({
        "txn_id": d["txn_id"].values[alert_idx],
        "step": d["step"].values[alert_idx],
        "type_name": d["type_name"].values[alert_idx],
        "amount": d["amount"].values[alert_idx],
        "fraud_score": p[alert_idx],
        "is_fraud": y[alert_idx],
        "reason_1": [r[0] for r in reasons],
        "reason_2": [r[1] for r in reasons],
        "reason_3": [r[2] for r in reasons],
    })

    out = config.GOLD_DIR
    alerts.to_parquet(out / "fact_alerts.parquet", index=False)
    threshold_metrics.to_parquet(out / "threshold_metrics.parquet", index=False)
    segment_metrics.to_parquet(out / "segment_metrics.parquet", index=False)
    pd.DataFrame([metrics]).to_parquet(out / "model_metrics.parquet", index=False)
    (config.MODELS_DIR / "test_metrics.json").write_text(json.dumps(metrics, indent=2, default=float))
    print(f"[evaluate] PR-AUC={metrics['pr_auc']:.3f} precision={metrics['precision_val']:.3f} "
          f"recall={metrics['recall_val']:.3f} alerts={len(alerts):,}")
    return metrics


if __name__ == "__main__":
    run()
