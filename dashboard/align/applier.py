import pandas as pd
from typing import Optional


def apply_offset(
    df: pd.DataFrame,
    ts_col: str,
    offset_sec: float,
    drift_per_day_sec: float = 0.0,
    base_date: Optional[pd.Timestamp] = None,
    station_id: Optional[str] = None,
    output_col: str = "ts_aligned",
) -> pd.DataFrame:
    """
    ts_aligned = ts_raw - offset - drift × day_index
    """
    df = df.copy()
    df[ts_col] = pd.to_datetime(df[ts_col], errors="coerce", dayfirst=True)
    if base_date is None:
        base_date = df[ts_col].min().normalize()

    day_index = (df[ts_col].dt.normalize() - base_date).dt.days

    total_offset_sec = offset_sec + drift_per_day_sec * day_index

    df[output_col] = df[ts_col] - pd.to_timedelta(total_offset_sec, unit="s")
    df[f"{output_col}_offset_sec"] = total_offset_sec
    df[f"{output_col}_station"] = station_id

    return df


def apply_offsets_to_source(
    source_df: pd.DataFrame,
    station_col: str,
    ts_col: str,
    offsets: dict,
    output_col: str = "ts_aligned",
) -> pd.DataFrame:
    """Áp dụng offset cho 1 source, xử lý nhiều stations."""
    df = source_df.copy()
    df[output_col] = pd.NaT
    df[f"{output_col}_offset_sec"] = None
    df[f"{output_col}_station"] = None

    for station_id, est in offsets.items():
        mask = df[station_col] == station_id
        if mask.sum() == 0:
            continue

        df_sub = df[mask].copy()
        df_sub_aligned = apply_offset(
            df_sub,
            ts_col=ts_col,
            offset_sec=est.offset_sec,
            drift_per_day_sec=0.0,
            station_id=station_id,
            output_col=output_col,
        )

        df.loc[mask, output_col] = df_sub_aligned[output_col].values
        df.loc[mask, f"{output_col}_offset_sec"] = df_sub_aligned[f"{output_col}_offset_sec"].values
        df.loc[mask, f"{output_col}_station"] = station_id

    # Station không có offset → dùng raw
    df[output_col] = df[output_col].fillna(df[ts_col])

    return df

