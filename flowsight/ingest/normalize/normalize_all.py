"""
normalize_all.py — Áp dụng ID normalization cho tất cả 9 nguồn (Tầng 11A-3a).
"""
import json
import pandas as pd
from datetime import datetime
from .id_normalizer import (
    normalize_lot_id, normalize_jt_id, normalize_station_id,
    normalize_product_id, normalize_component_id,
)
from ..config import AUDIT_DIR


# Mapping: source → {raw_column: (normalized_column, normalizer_fn)}
NORMALIZATION_RULES = {
    "SRC-01_output": {
        "lot_ref_raw": ("lot_ref_norm", normalize_lot_id),
        "product_ref_raw": ("product_ref_norm", normalize_product_id),
    },
    "SRC-02_ipc": {
        "lot_ref_raw": ("lot_ref_norm", normalize_lot_id),
        "station_ref_raw": ("station_ref_norm", normalize_station_id),
    },
    "SRC-03_qr": {
        "qr_code_raw": ("lot_ref_norm", normalize_lot_id),
        "parent_qr_code_raw": ("parent_lot_ref_norm", normalize_lot_id),
        "station_ref_raw": ("station_ref_norm", normalize_station_id),
    },
    "SRC-04_qc_auto": {
        "lot_ref_raw": ("lot_ref_norm", normalize_lot_id),
        "product_ref_raw": ("product_ref_norm", normalize_product_id),
        "station_ref_raw": ("station_ref_norm", normalize_station_id),
    },
    "SRC-05_qc_sampling": {
        "lot_ref_raw": ("lot_ref_norm", normalize_lot_id),
        "station_ref_raw": ("station_ref_norm", normalize_station_id),
    },
    "SRC-06_jt": {
        "jt_ref_raw": ("jt_ref_norm", normalize_jt_id),
        "product_ref_raw": ("product_ref_norm", normalize_product_id),
    },
    "SRC-07_inventory": {
        "item_ref_raw": ("item_ref_norm", None),
    },
    "SRC-08_shipping": {
        "jt_ref_raw": ("jt_ref_norm", normalize_jt_id),
        "product_ref_raw": ("product_ref_norm", normalize_product_id),
    },
    "SRC-09_incident": {
        "station_ref_raw": ("station_ref_norm", normalize_station_id),
        "incident_ref_raw": ("incident_ref_norm", None),
    },
}


def apply_id_normalization(mapped_data: dict) -> dict:
    """
    Áp dụng ID normalization cho tất cả 9 nguồn.
    """
    print("\n" + "=" * 70)
    print("  TẦNG 11A-3: ID NORMALIZATION")
    print("=" * 70)

    normalized_data = {}
    audit = {}

    for source_id, df in mapped_data.items():
        print(f"\n[{source_id}] Normalizing IDs...")

        if source_id not in NORMALIZATION_RULES:
            print(f"  ⚠ No rules, skipping")
            normalized_data[source_id] = df
            continue

        rules = NORMALIZATION_RULES[source_id]
        normalized_cols = []

        for raw_col, (norm_col, fn) in rules.items():
            if raw_col not in df.columns:
                print(f"  ⚠ Column not found: {raw_col}")
                continue

            if fn is None:
                df[norm_col] = df[raw_col]
            else:
                df[norm_col] = df[raw_col].apply(fn)

            normalized_cols.append(norm_col)
            print(f"  ✓ {raw_col} → {norm_col}")

        normalized_data[source_id] = df
        audit[source_id] = {
            "normalized_columns": normalized_cols,
            "total_rows": len(df),
            "null_norm_count": {
                col: int(df[col].isna().sum())
                for col in normalized_cols
            },
        }

    # Ghi audit
    with open(AUDIT_DIR / "id_normalization_log.json", "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2, ensure_ascii=False, default=str)

    print("\n" + "=" * 70)
    print("  ID NORMALIZATION COMPLETED")
    print("=" * 70)

    return normalized_data


if __name__ == "__main__":
    from ..readers.raw_loader import load_all_raw_sources
    from ..schema.schema_mapper import apply_schema_mapping

    raw = load_all_raw_sources()
    mapped = apply_schema_mapping(raw)
    normalized = apply_id_normalization(mapped)

    for src, df in normalized.items():
        print(f"{src}: {df.shape}")
