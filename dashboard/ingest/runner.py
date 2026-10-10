"""
runner.py — Orchestrator cho toàn bộ Bước 11A.
Pipeline: Ingestion → Schema Mapping → ID Normalization → Value Normalization → Save Staged.
"""
import time
from pathlib import Path
from .config import STAGED_DIR
from .readers.raw_loader import load_all_raw_sources
from .schema.schema_mapper import apply_schema_mapping
from .normalize.normalize_all import apply_id_normalization
from .normalize.value_normalizer import apply_value_normalization


def save_staged(df, source_id: str, suffix: str = ""):
    """Lưu DataFrame đã normalize vào staged/."""
    out_dir = STAGED_DIR / source_id
    out_dir.mkdir(parents=True, exist_ok=True)

    filename = f"staged_{source_id}{suffix}.parquet"
    path = out_dir / filename

    df.to_parquet(path, index=False)
    print(f"  ✓ Saved: {path.relative_to(STAGED_DIR.parent)} ({len(df)} rows)")


def run_step_11a() -> dict:
    t0 = time.time()
    print("=" * 70)
    print("  FLOWSIGHT — BUOC 11A")
    print("  Ingestion + Schema Mapping + ID Normalization")
    print("=" * 70)

    raw_data = load_all_raw_sources()
    mapped_data = apply_schema_mapping(raw_data)
    id_normalized = apply_id_normalization(mapped_data)
    fully_normalized = apply_value_normalization(id_normalized)

    # ------------------------------------------------------------------
    # FIX: Xử lý SRC-05 đặc biệt — tách riêng từng sheet để tránh trùng cột
    # ------------------------------------------------------------------
    if "SRC-05_qc_sampling" in fully_normalized:
        df05 = fully_normalized["SRC-05_qc_sampling"].copy()

        # Drop các cột RAW không cần (đã có bản _norm)
        raw_cols_to_drop = [
            "Lot_ID", "LOT_ID", "lot_id", "local_lot_ref", "Mã lô",
            "Characteristic", "characteristic", "Đặc tính",
            "Value", "value", "Giá trị",
            "Measured_Date", "measured_date", "Ngày đo",
            "Station", "station", "station_code", "Mã trạm",
            "Inspector", "inspector", "Người kiểm tra",
        ]
        df05 = df05.drop(columns=[c for c in raw_cols_to_drop if c in df05.columns])

        # Kiểm tra và loại bỏ cột trùng
        df05 = df05.loc[:, ~df05.columns.duplicated()]

        fully_normalized["SRC-05_qc_sampling"] = df05
        print(f"\n[FIX] SRC-05: dropped raw cols, remaining {len(df05.columns)} cols")

    print("\n" + "=" * 70)
    print("  SAVING STAGED DATA")
    print("=" * 70)

    for source_id, df in fully_normalized.items():
        # Loại bỏ cột trùng phòng trường hợp còn sót
        df = df.loc[:, ~df.columns.duplicated()]
        save_staged(df, source_id)

    elapsed = time.time() - t0
    print("\n" + "=" * 70)
    print(f"  BUOC 11A HOAN TAT trong {elapsed:.2f}s")
    print(f"  Sources processed: {len(fully_normalized)}")
    print("=" * 70)
    return fully_normalized

if __name__ == "__main__":
    run_step_11a()
