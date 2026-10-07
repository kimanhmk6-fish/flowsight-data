"""
raw_loader.py — Orchestrator đọc 9 nguồn RAW (Tầng 11A-1).
"""
import json
from pathlib import Path
from datetime import datetime
from .csv_reader import CSVReader
from .excel_reader import ExcelReader
from ..config import RAW_SOURCES, AUDIT_DIR


def load_all_raw_sources() -> dict:
    """
    Đọc tất cả 9 nguồn RAW.
    Returns: dict[source_id, pd.DataFrame]
    """
    print("=" * 70)
    print("  TẦNG 11A-1: INGESTION")
    print("=" * 70)

    raw_data = {}
    audit = {
        "started_at": datetime.utcnow().isoformat() + "Z",
        "sources": {},
    }

    for source_id, config in RAW_SOURCES.items():
        print(f"\n[{source_id}] Loading...")

        try:
            fmt = config["format"]

            if fmt == "csv":
                reader = CSVReader(source_id, config)
            elif fmt == "excel":
                reader = ExcelReader(source_id, config)
            elif fmt == "auto":
                files = list(Path(config["path"]).glob(config["file_pattern"]))
                if not files:
                    raise FileNotFoundError(f"No files matching {config['file_pattern']}")
                if files[0].suffix.lower() in [".xlsx", ".xls"]:
                    reader = ExcelReader(source_id, config)
                else:
                    reader = CSVReader(source_id, config)
            else:
                raise ValueError(f"Unknown format: {fmt}")

            df = reader.read_all()
            raw_data[source_id] = df

            print(f"  ✓ Loaded: {len(df)} rows, {len(df.columns)} columns")
            print(f"    Files: {df['_source_file'].nunique()} unique")

            audit["sources"][source_id] = {
                "status": "success",
                "rows": len(df),
                "columns": list(df.columns),
                "files": df["_source_file"].unique().tolist(),
            }

        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            audit["sources"][source_id] = {
                "status": "failed",
                "error": str(e),
            }
            raise

    audit["finished_at"] = datetime.utcnow().isoformat() + "Z"

    # Ghi audit log
    with open(AUDIT_DIR / "ingestion_log.json", "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2, ensure_ascii=False, default=str)

    print("\n" + "=" * 70)
    print(f"  INGESTION COMPLETED: {len(raw_data)} sources")
    print("=" * 70)

    return raw_data


if __name__ == "__main__":
    data = load_all_raw_sources()
    for src, df in data.items():
        print(f"{src}: {df.shape}")
