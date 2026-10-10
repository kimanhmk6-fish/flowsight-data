import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Optional


@dataclass
class OffsetEstimate:
    station_id: str
    offset_sec: float
    mad_sec: float
    n_anchors: int
    n_outliers_removed: int
    confidence: float
    method: str = "median_mad"


def estimate_offset(
    diffs_sec: np.ndarray,
    station_id: str,
    mad_threshold: float = 3.5,
    min_anchors: int = 5,
) -> Optional[OffsetEstimate]:
    """Ước lượng offset từ mảng diff bằng robust statistics."""
    if len(diffs_sec) < min_anchors:
        return None

    median_offset = float(np.median(diffs_sec))
    abs_dev = np.abs(diffs_sec - median_offset)
    mad = float(np.median(abs_dev))

    if mad < 1e-6:
        mad = 1.0

    mask = abs_dev <= mad_threshold * mad
    clean_diffs = diffs_sec[mask]
    n_outliers = int((~mask).sum())

    if len(clean_diffs) < min_anchors:
        clean_diffs = diffs_sec

    final_offset = float(np.median(clean_diffs))
    final_mad = float(np.median(np.abs(clean_diffs - final_offset)))

    n_factor = min(1.0, len(clean_diffs) / 50)
    mad_factor = 1.0 / (1.0 + final_mad / 10.0)
    confidence = round(n_factor * mad_factor, 3)

    return OffsetEstimate(
        station_id=station_id,
        offset_sec=round(final_offset, 2),
        mad_sec=round(final_mad, 2),
        n_anchors=len(clean_diffs),
        n_outliers_removed=n_outliers,
        confidence=confidence,
    )


def estimate_offsets_per_station(
    anchors: pd.DataFrame,
    station_col: str = "station_ref_norm",
    diff_col: str = "raw_diff_sec",
    min_anchors: int = 5,
) -> dict:
    """Ước lượng offset cho từng station."""
    result = {}
    if station_col not in anchors.columns:
        return result

    for station_id, group in anchors.groupby(station_col):
        diffs = group[diff_col].values
        est = estimate_offset(diffs, str(station_id), min_anchors=min_anchors)
        if est is not None:
            result[str(station_id)] = est
    return result
