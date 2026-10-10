import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Optional


@dataclass
class DriftEstimate:
    station_id: str
    base_offset_sec: float
    drift_per_day_sec: float
    r_squared: float
    n_days: int
    is_significant: bool
    method: str = "linear_regression"


def detect_drift(
    anchors: pd.DataFrame,
    station_id: str,
    ts_col: str = "ts_a",
    diff_col: str = "raw_diff_sec",
    min_anchors_per_day: int = 3,
) -> Optional[DriftEstimate]:
    """Fit linear: diff = a + b × day_index."""
    if len(anchors) < min_anchors_per_day * 3:
        return None

    df = anchors.copy()
    df[ts_col] = pd.to_datetime(df[ts_col])
    df["day_index"] = (df[ts_col].dt.normalize() - df[ts_col].min().normalize()).dt.days

    daily_counts = df.groupby("day_index").size()
    valid_days = daily_counts[daily_counts >= min_anchors_per_day].index

    if len(valid_days) < 3:
        return None

    df = df[df["day_index"].isin(valid_days)]

    x = df["day_index"].values.astype(float)
    y = df[diff_col].values.astype(float)

    try:
        coeffs = np.polyfit(x, y, 1)
    except (np.linalg.LinAlgError, ValueError):
        return None

    drift_per_day = float(coeffs[0])
    base_offset = float(coeffs[1])

    y_pred = np.polyval(coeffs, x)
    ss_res = ((y - y_pred) ** 2).sum()
    ss_tot = ((y - y.mean()) ** 2).sum()
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0

    is_significant = abs(drift_per_day) > 1.0

    return DriftEstimate(
        station_id=str(station_id),
        base_offset_sec=round(base_offset, 2),
        drift_per_day_sec=round(drift_per_day, 3),
        r_squared=round(float(r_squared), 3),
        n_days=len(valid_days),
        is_significant=is_significant,
    )
