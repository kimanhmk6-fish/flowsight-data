"""
schema_mapper.py — Ánh xạ cột RAW → cột chuẩn (Tầng 11A-2).
"""
import yaml
import json
import pandas as pd
from pathlib import Path
from typing import Optional
from ..config import AUDIT_DIR


class SchemaMapper:
    """Ánh xạ cột từ RAW schema về canonical schema."""

    def __init__(self, mappings_path: Optional[Path] = None):
        if mappings_path is None:
            mappings_path = Path(__file__).parent / "mappings.yaml"

        with open(mappings_path, encoding="utf-8") as f:
            self.mappings = yaml.safe_load(f)

        self.audit_log = []

    def map_columns(self, df: pd.DataFrame, source_id: str) -> pd.DataFrame:
        """
        Ánh xạ cột RAW → cột chuẩn.
        - Cột nào không có trong mapping → giữ nguyên
        - Cột nào cần map nhưng thiếu → tạo cột None + log warning
        """
        if source_id not in self.mappings:
            raise ValueError(f"No mapping defined for source: {source_id}")

        source_mapping = self.mappings[source_id]
        existing_cols = set(df.columns)
        rename_dict = {}
        unmapped_raw_cols = []
        missing_target_cols = []

        # Bước 1: Tìm cột RAW tương ứng cho mỗi target
        for target_col, raw_aliases in source_mapping.items():
            matched_raw = None
            for alias in raw_aliases:
                if alias in existing_cols:
                    matched_raw = alias
                    break

            if matched_raw is not None:
                rename_dict[matched_raw] = target_col
            else:
                missing_target_cols.append(target_col)

        # Bước 2: Cột RAW nào không map → đánh dấu unmapped
        mapped_raw_cols = set(rename_dict.keys())
        for col in existing_cols:
            if col.startswith("_"):
                continue
            if col not in mapped_raw_cols:
                unmapped_raw_cols.append(col)

        # Bước 3: Apply rename
        df_mapped = df.rename(columns=rename_dict)

        # Bước 4: Thêm cột thiếu dưới dạng None
        for col in missing_target_cols:
            df_mapped[col] = None

        # Bước 5: Log audit
        self.audit_log.append({
            "source_id": source_id,
            "renamed_columns": rename_dict,
            "missing_target_cols": missing_target_cols,
            "unmapped_raw_cols": unmapped_raw_cols,
            "total_rows": len(df_mapped),
            "total_columns": len(df_mapped.columns),
        })

        return df_mapped

    def get_audit_log(self) -> list:
        return self.audit_log


def apply_schema_mapping(raw_data: dict) -> dict:
    """
    Áp dụng schema mapping cho tất cả 9 nguồn.
    """
    print("\n" + "=" * 70)
    print("  TẦNG 11A-2: SCHEMA MAPPING")
    print("=" * 70)

    mapper = SchemaMapper()
    mapped_data = {}

    for source_id, df in raw_data.items():
        print(f"\n[{source_id}] Mapping columns...")

        try:
            df_mapped = mapper.map_columns(df, source_id)
            mapped_data[source_id] = df_mapped

            log = mapper.audit_log[-1]
            print(f"  ✓ Renamed {len(log['renamed_columns'])} columns")
            if log["missing_target_cols"]:
                print(f"    ⚠ Missing target cols: {log['missing_target_cols']}")
            if log["unmapped_raw_cols"]:
                print(f"    ⚠ Unmapped RAW cols: {log['unmapped_raw_cols']}")

        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            raise

    # Ghi audit log
    with open(AUDIT_DIR / "schema_mapping_log.json", "w", encoding="utf-8") as f:
        json.dump(mapper.get_audit_log(), f, indent=2, ensure_ascii=False, default=str)

    print("\n" + "=" * 70)
    print("  SCHEMA MAPPING COMPLETED")
    print("=" * 70)

    return mapped_data


if __name__ == "__main__":
    from ..readers.raw_loader import load_all_raw_sources
    raw = load_all_raw_sources()
    mapped = apply_schema_mapping(raw)
    for src, df in mapped.items():
        print(f"{src}: {df.shape}")
