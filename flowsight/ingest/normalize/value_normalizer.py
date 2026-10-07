"""
value_normalizer.py — Chuẩn hóa giá trị: số, dấu phẩy/chấm, OK/NG, timestamp.
"""
import re
import json
import pandas as pd
import numpy as np
from typing import Optional, Any
from ..config import AUDIT_DIR


def normalize_decimal(raw: Any) -> Optional[float]:
    """
    Chuẩn hóa số thập phân: "12,5" → 12.5, "12.5" → 12.5.
    Handle cả nghìn separator.
    """
    if raw is None or raw == "" or (not isinstance(raw, str) and pd.isna(raw)):
        return None

    if isinstance(raw, (int, float, np.number)):
        return float(raw)

    s = str(raw).strip()
    if s == "":
        return None

    s = re.sub(r"[^\d,.\-]", "", s)
    if s == "":
        return None

    # Case 1: có cả dấu chấm và dấu phẩy
    if "," in s and "." in s:
        last_comma = s.rfind(",")
        last_dot = s.rfind(".")
        if last_comma > last_dot:
            s = s.replace(".", "").replace(",", ".")   # 1.234,5 → 1234.5
        else:
            s = s.replace(",", "")                     # 1,234.5 → 1234.5

    # Case 2: chỉ có dấu phẩy
    elif "," in s:
        if s.count(",") == 1 and len(s) - s.rfind(",") == 3:
            s = s.replace(",", "")                     # 1,234 → 1234
        else:
            s = s.replace(",", ".")                    # 12,5 → 12.5

    try:
        return float(s)
    except ValueError:
        return None


def normalize_int(raw: Any) -> Optional[int]:
    """Chuẩn hóa integer."""
    f = normalize_decimal(raw)
    if f is None:
        return None
    return int(round(f))


def normalize_result(raw: Any) -> Optional[str]:
    """Chuẩn hóa kết quả: OK/NG/PASS/FAIL/Đạt/Không đạt."""
    if raw is None or (not isinstance(raw, str) and pd.isna(raw)):
        return None

    s = str(raw).strip().upper()

    if s in ["OK", "PASS", "ĐẠT", "DAT", "TRUE", "1"]:
        return "OK"
    if s in ["NG", "FAIL", "KHÔNG ĐẠT", "KHONG DAT", "FALSE", "0"]:
        return "NG"

    return s


def normalize_timestamp(raw: Any, fmt: str = "auto") -> Optional[pd.Timestamp]:
    """
    Chuẩn hóa timestamp từ nhiều format về pd.Timestamp.
    Hỗ trợ: ISO8601, dd/mm/yyyy HH:MM:SS, dd/mm/yyyy HH:MM, dd/mm/yyyy.
    """
    if raw is None or raw == "" or (not isinstance(raw, str) and pd.isna(raw)):
        return None

    if isinstance(raw, pd.Timestamp):
        return raw

    s = str(raw).strip()

    # Thử ISO 8601
    try:
        return pd.Timestamp(s)
    except (ValueError, TypeError):
        pass

    # Thử dd/mm/yyyy
    for fmt_str in ["%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y"]:
        try:
            return pd.to_datetime(s, format=fmt_str)
        except (ValueError, TypeError):
            continue

    return None


def apply_value_normalization(mapped_data: dict) -> dict:
    """
    Áp dụng value normalization cho các cột số, timestamp, result.
    """
    print("\n" + "=" * 70)
    print("  TẦNG 11A-3b: VALUE NORMALIZATION")
    print("=" * 70)

    VALUE_RULES = {
        "SRC-01_output": {
            "qty_ok_raw": normalize_int,
            "qty_ng_raw": normalize_int,
            "rate_per_h_raw": normalize_decimal,
            "event_ts_raw": normalize_timestamp,
        },
        "SRC-02_ipc": {
            "param_temp_raw": normalize_decimal,
            "param_force_raw": normalize_decimal,
            "param_vib_raw": normalize_decimal,
            "ts_raw": normalize_timestamp,
            "export_ts_raw": normalize_timestamp,
        },
        "SRC-03_qr": {
            "ts_raw": normalize_timestamp,
        },
        "SRC-04_qc_auto": {
            "value_raw": normalize_decimal,
            "lsl_raw": normalize_decimal,
            "usl_raw": normalize_decimal,
            "result_raw": normalize_result,
            "ts_raw": normalize_timestamp,
        },
        "SRC-06_jt": {
            "qty_raw": normalize_int,
        },
        "SRC-07_inventory": {
            "qty_raw": normalize_int,
            "ts_raw": normalize_timestamp,
        },
        "SRC-08_shipping": {
            "truck_ts_raw": normalize_timestamp,
            "cutoff_ts_raw": normalize_timestamp,
            "qty_planned_raw": normalize_int,
        },
        "SRC-09_incident": {
            "start_ts_raw": normalize_timestamp,
            "end_ts_raw": normalize_timestamp,
        },
    }

    normalized_data = {}
    audit = {}

    for source_id, df in mapped_data.items():
        print(f"\n[{source_id}] Normalizing values...")

        if source_id not in VALUE_RULES:
            normalized_data[source_id] = df
            continue

        rules = VALUE_RULES[source_id]
        audit[source_id] = {}

        for col, fn in rules.items():
            if col not in df.columns:
                continue

            norm_col = col.replace("_raw", "_norm")
            if norm_col == col:
                norm_col = f"{col}_norm"

            df[norm_col] = df[col].apply(fn)

            n_input = int(df[col].notna().sum())
            n_output = int(df[norm_col].notna().sum())
            n_failed = n_input - n_output

            audit[source_id][col] = {
                "target": norm_col,
                "n_input": n_input,
                "n_output": n_output,
                "n_failed": n_failed,
            }

            status = "✓" if n_failed == 0 else f"⚠ {n_failed} failed"
            print(f"  {status} {col} → {norm_col}")

        normalized_data[source_id] = df

    # Ghi audit
    with open(AUDIT_DIR / "value_normalization_log.json", "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2, ensure_ascii=False, default=str)

    print("\n" + "=" * 70)
    print("  VALUE NORMALIZATION COMPLETED")
    print("=" * 70)

    return normalized_data
