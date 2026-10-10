"""
utils.py — Helper functions cho Ingestion Layer.
"""
import json
import hashlib
from pathlib import Path
from datetime import datetime
import pandas as pd


def hash_row(row: pd.Series) -> str:
    """MD5 12 ký tự của 1 dòng — để detect duplicate."""
    return hashlib.md5(str(tuple(row)).encode()).hexdigest()[:12]


def save_audit_log(data: dict, path: Path):
    """Ghi audit log ra JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    print(f"  ✓ Audit saved: {path.name}")


def now_iso() -> str:
    """ISO8601 UTC."""
    return datetime.utcnow().isoformat() + "Z"
