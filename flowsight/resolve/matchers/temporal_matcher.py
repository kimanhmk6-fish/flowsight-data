import pandas as pd
from typing import Optional


def match_temporal(
    alias_a: str,
    source_a: str,
    ts_a: Optional[pd.Timestamp],
    product_a: Optional[str],
    staged_data: dict,
    candidate_pool: set,
    window_min: int = 5,
) -> tuple:
    """
    Match entity bằng temporal proximity.
    Returns: (canonical_id, confidence, method)
    """
    if ts_a is None or pd.isna(ts_a):
        return None, 0.0, None

    ts_a = pd.Timestamp(ts_a)
    window = pd.Timedelta(minutes=window_min)

    matches = []

    for source_id, df in staged_data.items():
        if source_id == source_a:
            continue
        if "ts_aligned" not in df.columns and "ts_raw" not in df.columns:
            continue
        if "lot_ref_norm" not in df.columns:
            continue

        ts_col = "ts_aligned" if "ts_aligned" in df.columns else "ts_raw"
        df_ts = pd.to_datetime(df[ts_col], errors="coerce")
        close = df[(df_ts >= ts_a - window) & (df_ts <= ts_a + window)]

        if len(close) == 0:
            continue

        for cand in close["lot_ref_norm"].dropna().unique():
            if cand in candidate_pool and cand != alias_a:
                matches.append({
                    "canonical_id": cand,
                    "source": source_id,
                    "time_diff_sec": abs((df_ts[close["lot_ref_norm"] == cand].iloc[0] - ts_a).total_seconds()),
                })

    if not matches:
        return None, 0.0, None

    matches_df = pd.DataFrame(matches).sort_values("time_diff_sec")
    best = matches_df.iloc[0]

    confidence = 0.85 * (1 - best["time_diff_sec"] / (window_min * 60))
    confidence = max(0.5, min(0.95, confidence))

    return best["canonical_id"], round(confidence, 3), "temporal"
