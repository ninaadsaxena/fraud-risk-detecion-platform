"""Small PaySim-shaped synthetic dataset for demos, tests and CI. NOT real data."""
from pathlib import Path

import numpy as np
import pandas as pd


def generate(n_rows=50_000, n_steps=240, fraud_rate=0.006, seed=42, inject_bad=True) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    types = np.array(["PAYMENT", "TRANSFER", "CASH_OUT", "DEBIT", "CASH_IN"])
    t = rng.choice(types, size=n_rows, p=[0.34, 0.08, 0.35, 0.01, 0.22])
    step = np.sort(rng.integers(1, n_steps + 1, size=n_rows))

    amount = np.round(rng.lognormal(9.0, 1.4, n_rows), 2)
    old_org = np.round(rng.lognormal(10.0, 1.8, n_rows), 2)

    can_fraud = np.isin(t, ["TRANSFER", "CASH_OUT"])
    is_fraud = (rng.random(n_rows) < fraud_rate / can_fraud.mean()) & can_fraud

    drain_all = rng.random(n_rows) < 0.8
    fraud_amt = np.where(drain_all, old_org, np.round(old_org * rng.uniform(0.6, 1.0, n_rows), 2))
    debit = np.isin(t, ["PAYMENT", "TRANSFER", "CASH_OUT", "DEBIT"])
    amount = np.where(is_fraud, fraud_amt, np.where(debit, np.minimum(amount, old_org), amount))

    new_org = np.where(t == "CASH_IN", old_org + amount, old_org - amount)
    new_org = np.round(np.maximum(new_org, 0), 2)

    merchant = t == "PAYMENT"
    old_dest = np.where(merchant, 0.0, np.round(rng.lognormal(9.5, 1.8, n_rows), 2))
    new_dest = np.where(merchant, 0.0, old_dest + amount)
    # simulator-style artefact: fraudulent flows often leave the destination balance unchanged
    new_dest = np.where(is_fraud, old_dest, new_dest)

    df = pd.DataFrame(
        {
            "step": step,
            "type": t,
            "amount": amount,
            "nameOrig": ["C" + str(x) for x in rng.integers(10**8, 10**9, n_rows)],
            "oldbalanceOrg": old_org,
            "newbalanceOrig": new_org,
            "nameDest": [("M" if m else "C") + str(x) for m, x in zip(merchant, rng.integers(10**8, 10**9, n_rows))],
            "oldbalanceDest": old_dest,
            "newbalanceDest": np.round(new_dest, 2),
            "isFraud": is_fraud.astype(int),
            "isFlaggedFraud": 0,
        }
    )

    if inject_bad:  # a few bad rows so the data-quality report has something to show
        k = max(3, n_rows // 2000)
        bad = rng.choice(n_rows, size=3 * k, replace=False)
        df.loc[bad[:k], "amount"] = -abs(df.loc[bad[:k], "amount"])
        df.loc[bad[k : 2 * k], "type"] = "UNKNOWN"
        df.loc[bad[2 * k :], "oldbalanceOrg"] = np.nan
    return df


def write_csv(path: Path, **kwargs) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    generate(**kwargs).to_csv(path, index=False)
    return path
