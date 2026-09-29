"""Feature engineering and the time-based split shared by train/evaluate."""
import numpy as np
import pandas as pd

from . import config

TYPES = ["PAYMENT", "TRANSFER", "CASH_OUT", "DEBIT", "CASH_IN"]
# These two features exploit simulator bookkeeping artefacts and are known to make PaySim
# look easier than reality. "conservative" drops them so you can report both honestly.
BALANCE_ERROR_FEATURES = ["orig_balance_error", "dest_balance_error"]


def load_model_frame() -> pd.DataFrame:
    fact = pd.read_parquet(config.GOLD_DIR / "fact_transactions.parquet")
    dim_type = pd.read_parquet(config.GOLD_DIR / "dim_type.parquet")
    return fact.merge(dim_type, on="type_id", how="left")


def build_features(df: pd.DataFrame, feature_set: str = "full") -> pd.DataFrame:
    X = pd.DataFrame(index=df.index)
    X["amount"] = df["amount"]
    X["log_amount"] = np.log1p(df["amount"])
    X["hour_of_day"] = (df["step"] - 1) % 24
    X["orig_balance_before"] = df["oldbalance_orig"]
    X["dest_balance_before"] = df["oldbalance_dest"]
    X["dest_is_merchant"] = df["dest_is_merchant"]
    X["orig_emptied"] = ((df["oldbalance_orig"] > 0) & (df["newbalance_orig"] == 0)).astype(int)
    X["orig_balance_error"] = df["oldbalance_orig"] - df["amount"] - df["newbalance_orig"]
    X["dest_balance_error"] = df["oldbalance_dest"] + df["amount"] - df["newbalance_dest"]
    for t in TYPES:
        X[f"type_{t}"] = (df["type_name"] == t).astype(int)
    if feature_set == "conservative":
        X = X.drop(columns=BALANCE_ERROR_FEATURES)
    elif feature_set != "full":
        raise ValueError("feature_set must be 'full' or 'conservative'")
    return X


def time_split(df: pd.DataFrame, train_q: float = 0.70, val_q: float = 0.85):
    """Chronological split on `step`: train | validation | test."""
    c1 = df["step"].quantile(train_q)
    c2 = df["step"].quantile(val_q)
    train = df["step"] <= c1
    val = (df["step"] > c1) & (df["step"] <= c2)
    test = df["step"] > c2
    return train, val, test, {"train_max_step": float(c1), "val_max_step": float(c2)}


def alert_cost(y_true, amount, alerted, review_cost: float) -> dict:
    """Missed fraud costs its amount; every alert costs `review_cost` to investigate."""
    y_true = np.asarray(y_true).astype(bool)
    alerted = np.asarray(alerted).astype(bool)
    amount = np.asarray(amount, dtype=float)
    missed = y_true & ~alerted
    caught = y_true & alerted
    missed_amt = float(amount[missed].sum())
    n_alerts = int(alerted.sum())
    return {
        "alerts": n_alerts,
        "tp": int(caught.sum()),
        "fp": int((alerted & ~y_true).sum()),
        "fn": int(missed.sum()),
        "missed_fraud_amount": missed_amt,
        "caught_fraud_amount": float(amount[caught].sum()),
        "review_cost": review_cost * n_alerts,
        "total_cost": missed_amt + review_cost * n_alerts,
    }
