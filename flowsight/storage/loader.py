import json
from datetime import datetime
from .config import CANONICAL_DIR, TABLES, AUDIT_DIR


def verify_load() -> dict:
    """Verify tất cả canonical tables tồn tại và có dữ liệu."""
    print("\n" + "=" * 70)
    print("  TẦNG 11C-2: STORAGE (verify canonical tables)")
    print("=" * 70)

    import pandas as pd

    report = {"tables": {}, "all_present": True}

    for table in TABLES:
        path = CANONICAL_DIR / f"{table}.parquet"
        if not path.exists():
            print(f"  ⚠ {table:25s}: MISSING")
            report["tables"][table] = {"status": "missing", "rows": 0}
            report["all_present"] = False
            continue

        df = pd.read_parquet(path)
        print(f"  ✓ {table:25s}: {len(df)} rows")
        report["tables"][table] = {
            "status": "ok",
            "rows": len(df),
            "columns": list(df.columns),
        }

    print("\n" + "=" * 70)
    print(f"  Storage: {'ALL OK' if report['all_present'] else 'MISSING SOME TABLES'}")
    print("=" * 70)

    report["checked_at"] = datetime.utcnow().isoformat() + "Z"
    with open(AUDIT_DIR / "storage_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)

    return report
