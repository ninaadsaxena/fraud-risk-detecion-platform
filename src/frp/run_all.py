"""Run the whole pipeline: python -m frp.run_all [--synthetic] [--feature-set conservative] [--upload] [--no-sql]"""
import argparse

from . import build_gold, config, evaluate, ingest, load_sql, train, upload_adls


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--synthetic", action="store_true", help="generate a small synthetic CSV first (demo/CI)")
    ap.add_argument("--rows", type=int, default=50_000, help="synthetic rows")
    ap.add_argument("--feature-set", choices=["full", "conservative"], default="full")
    ap.add_argument("--upload", action="store_true", help="upload curated+gold files to Azure Storage")
    ap.add_argument("--no-sql", action="store_true", help="skip the database load")
    a = ap.parse_args()

    if a.synthetic:
        from .synthetic import write_csv

        p = write_csv(config.RAW_DIR / "synthetic_paysim.csv", n_rows=a.rows)
        import os
        os.environ["RAW_CSV"] = str(p)

    ingest.run()
    build_gold.run()
    train.run(a.feature_set)
    evaluate.run()
    if a.upload:
        upload_adls.run()
    if not a.no_sql:
        load_sql.run()
    print("[done] pipeline complete")


if __name__ == "__main__":
    main()
