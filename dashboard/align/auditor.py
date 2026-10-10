import json
from datetime import datetime
from .config import AUDIT_DIR


def save_alignment_audit(
    anchor_pairs: dict,
    offset_estimates: dict,
    drift_estimates: dict,
) -> dict:
    audit = {
        "step": "11B-1_time_alignment",
        "run_at": datetime.utcnow().isoformat() + "Z",
        "anchor_pairs": {},
        "offsets": {},
        "drifts": {},
    }

    for pair_name, anchors_df in anchor_pairs.items():
        audit["anchor_pairs"][pair_name] = {
            "n_anchors": len(anchors_df),
            "median_diff_sec": float(anchors_df["raw_diff_sec"].median()) if len(anchors_df) > 0 else None,
            "std_diff_sec": float(anchors_df["raw_diff_sec"].std()) if len(anchors_df) > 0 else None,
        }

    for station_id, est in offset_estimates.items():
        audit["offsets"][station_id] = {
            "offset_sec": est.offset_sec,
            "mad_sec": est.mad_sec,
            "n_anchors": est.n_anchors,
            "n_outliers_removed": est.n_outliers_removed,
            "confidence": est.confidence,
            "method": est.method,
        }

    for station_id, drift in drift_estimates.items():
        audit["drifts"][station_id] = {
            "base_offset_sec": drift.base_offset_sec,
            "drift_per_day_sec": drift.drift_per_day_sec,
            "r_squared": drift.r_squared,
            "n_days": drift.n_days,
            "is_significant": drift.is_significant,
        }

    with open(AUDIT_DIR / "time_alignment_audit.json", "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2, ensure_ascii=False, default=str)

    return audit
