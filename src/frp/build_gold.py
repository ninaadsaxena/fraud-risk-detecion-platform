"""Step 2: curated Parquet -> gold star schema (Parquet). Account IDs are salted+hashed."""
import hashlib

import pandas as pd

from . import config

PART_OF_DAY = ["night", "morning", "afternoon", "evening"]


def _hash_series(s: pd.Series) -> pd.Series:
    uniq = s.unique()
    mapping = {
        v: hashlib.sha256((config.HASH_SALT + v).encode()).hexdigest()[:16] for v in uniq
    }
    return s.map(mapping)


def run() -> None:
    df = pd.read_parquet(config.CURATED_DIR / "transactions.parquet")
    print(f"[gold] building star schema from {len(df):,} rows")

    dim_type = pd.DataFrame({"type_name": sorted(df["type"].unique())})
    dim_type.insert(0, "type_id", range(1, len(dim_type) + 1))
    type_map = dict(zip(dim_type["type_name"], dim_type["type_id"]))

    steps = pd.DataFrame({"step": sorted(df["step"].unique())})
    steps["day"] = (steps["step"] - 1) // 24 + 1
    steps["hour"] = (steps["step"] - 1) % 24
    steps["part_of_day"] = steps["hour"].map(lambda h: PART_OF_DAY[h // 6])
    dim_time = steps

    orig_key = _hash_series(df["nameOrig"])
    dest_key = _hash_series(df["nameDest"])
    dest_is_merchant = df["nameDest"].str.startswith("M")

    accounts = pd.concat(
        [
            pd.DataFrame({"account_key": orig_key, "account_kind": "customer"}),
            pd.DataFrame(
                {"account_key": dest_key,
                 "account_kind": dest_is_merchant.map({True: "merchant", False: "customer"})}
            ),
        ]
    ).drop_duplicates("account_key")

    fact = pd.DataFrame(
        {
            "txn_id": df["txn_id"].values,
            "step": df["step"].values,
            "type_id": df["type"].map(type_map).astype("int16").values,
            "amount": df["amount"].values,
            "orig_key": orig_key.values,
            "dest_key": dest_key.values,
            "dest_is_merchant": dest_is_merchant.astype("int8").values,
            "oldbalance_orig": df["oldbalanceOrg"].values,
            "newbalance_orig": df["newbalanceOrig"].values,
            "oldbalance_dest": df["oldbalanceDest"].values,
            "newbalance_dest": df["newbalanceDest"].values,
            "is_fraud": df["isFraud"].astype("int8").values,
        }
    )

    out = config.GOLD_DIR
    dim_type.to_parquet(out / "dim_type.parquet", index=False)
    dim_time.to_parquet(out / "dim_time.parquet", index=False)
    accounts.to_parquet(out / "dim_account.parquet", index=False)
    fact.to_parquet(out / "fact_transactions.parquet", index=False)
    print("[gold] wrote dim_type, dim_time, dim_account, fact_transactions")


if __name__ == "__main__":
    run()
