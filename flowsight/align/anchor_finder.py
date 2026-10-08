import re
import pandas as pd
import numpy as np

def _extract_number_key(val):
    """Lấy 4 chữ số cuối từ bất kỳ dạng mã nào (VD: L_A_0001 -> 0001, LOT-0401 -> 0401)"""
    if pd.isna(val) or val is None:
        return None
    s = str(val).strip()
    m = re.search(r"(\d{3,4})", s)
    if m:
        return m.group(1).zfill(4)
    return s

def find_anchor_events(
    source_a: pd.DataFrame,
    source_b: pd.DataFrame,
    match_on: list,
    ts_col_a: str = "ts_raw",
    ts_col_b: str = "ts_raw",
    max_diff_min: float = 60,  # Tăng lên 60 phút để tránh lệch time zone/clock
) -> pd.DataFrame:
    a = source_a.copy()
    b = source_b.copy()

    # Parse datetime hỗ trợ cả UTC và naive
    a["ts_a"] = pd.to_datetime(a[ts_col_a], errors="coerce", dayfirst=True, utc=True)
    b["ts_b"] = pd.to_datetime(b[ts_col_b], errors="coerce", dayfirst=True, utc=True)

    a = a.dropna(subset=["ts_a"])
    b = b.dropna(subset=["ts_b"])

    # Tạo key chuẩn hóa theo 4 số
    a["match_key"] = a["lot_ref_norm"].apply(_extract_number_key)
    b["match_key"] = b["lot_ref_norm"].apply(_extract_number_key)

    cols_b = ["match_key", "ts_b"]
    if "station_ref_norm" in b.columns:
        cols_b.append("station_ref_norm")

    a_keys = a[["match_key", "ts_a"]].dropna()
    b_keys = b[cols_b].dropna(subset=["match_key", "ts_b"])

    merged = a_keys.merge(b_keys, on="match_key", how="inner")

    if len(merged) == 0:
        return pd.DataFrame(columns=match_on + ["ts_a", "ts_b", "raw_diff_sec"])

    # Tính khoảng chênh lệch thời gian (giây)
    merged["raw_diff_sec"] = (merged["ts_a"] - merged["ts_b"]).dt.total_seconds()
    
    # Lọc sự kiện trong khoảng chênh lệch thời gian cho phép
    merged = merged[merged["raw_diff_sec"].abs() <= max_diff_min * 60]
    merged["abs_diff"] = merged["raw_diff_sec"].abs()

    # Lấy bản ghi chênh lệch thời gian nhỏ nhất
    merged = merged.sort_values("abs_diff").groupby(["match_key", "ts_a"]).first().reset_index()

    merged["lot_ref_norm"] = "LOT-" + merged["match_key"]

    out_cols = match_on + ["ts_a", "ts_b", "raw_diff_sec"]
    if "station_ref_norm" in merged.columns:
        out_cols.append("station_ref_norm")

    return merged[out_cols]