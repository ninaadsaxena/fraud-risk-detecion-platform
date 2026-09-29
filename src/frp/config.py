"""Central configuration. Everything is driven by environment variables (see .env.example)."""
import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

DATA_DIR = Path(os.getenv("DATA_DIR", ROOT / "data"))
RAW_DIR = DATA_DIR / "raw"
CURATED_DIR = DATA_DIR / "curated"
GOLD_DIR = DATA_DIR / "gold"
MODELS_DIR = Path(os.getenv("MODELS_DIR", ROOT / "models"))
FIGURES_DIR = Path(os.getenv("FIGURES_DIR", ROOT / "docs" / "figures"))

for _d in (RAW_DIR, CURATED_DIR, GOLD_DIR, MODELS_DIR, FIGURES_DIR):
    _d.mkdir(parents=True, exist_ok=True)

HASH_SALT = os.getenv("HASH_SALT", "change-me")
REVIEW_COST = float(os.getenv("REVIEW_COST", "10"))
RANDOM_STATE = 42


def max_step():
    v = os.getenv("MAX_STEP", "").strip()
    return int(v) if v else None


def raw_csv() -> Path:
    v = os.getenv("RAW_CSV", "").strip()
    if v:
        return Path(v)
    candidates = sorted(RAW_DIR.glob("*.csv"))
    if not candidates:
        raise FileNotFoundError(
            f"No CSV found in {RAW_DIR}. Download PaySim from Kaggle into data/raw/ "
            "or run with --synthetic for a small demo."
        )
    return candidates[0]


def get_engine():
    """Return a SQLAlchemy engine: DATABASE_URL > Azure SQL > local SQLite."""
    from sqlalchemy import create_engine

    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        return create_engine(url)

    server = os.getenv("AZURE_SQL_SERVER", "").strip()
    if server:
        odbc = (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            f"SERVER=tcp:{server},1433;"
            f"DATABASE={os.getenv('AZURE_SQL_DATABASE', '')};"
            f"UID={os.getenv('AZURE_SQL_USER', '')};"
            f"PWD={os.getenv('AZURE_SQL_PASSWORD', '')};"
            "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
        )
        return create_engine(
            "mssql+pyodbc:///?odbc_connect=" + quote_plus(odbc), fast_executemany=True
        )

    return create_engine(f"sqlite:///{DATA_DIR / 'frp_local.db'}")
