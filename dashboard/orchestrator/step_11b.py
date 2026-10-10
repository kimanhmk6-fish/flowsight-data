import time
import pandas as pd
from pathlib import Path

from flowsight.align.anchor_finder import find_anchor_events
from flowsight.align.offset_estimator import estimate_offsets_per_station
from flowsight.align.drift_detector import detect_drift
from flowsight.align.applier import apply_offsets_to_source
from flowsight.align.auditor import save_alignment_audit
from flowsight.align.config import STAGED_DIR, ALIGNED_DIR

from flowsight.resolve.resolver import resolve_all_lots, apply_resolution_to_staged
from flowsight.resolve.auditor import save_resolution_audit
from flowsight.resolve.config import RESOLVED_DIR


def _load_staged_data() -> dict:
    """Load 9 file staged parquet."""
    staged_data = {}
    for src_dir in STAGED_DIR.iterdir():
        if not src_dir.is_dir():
            continue
        for f in src_dir.glob("*.parquet"):
            source_id = src_dir.name
            df = pd.read_parquet(f)
            staged_data[source_id] = df
            print(f"  ✓ {source_id}: {len(df)} rows")
    return staged_data


def run_step_11b():
    """Chạy toàn bộ Bước 11B."""
    t0 = time.time()

    print("=" * 70)
    print("  FLOWSIGHT — BƯỚC 11B")
    print("  Time Alignment + Entity Resolution")
    print("=" * 70)

    # ============================================================
    # LOAD STAGED (từ 11A)
    # ============================================================
    print("\n" + "=" * 70)
    print("  LOADING STAGED DATA (từ 11A)")
    print("=" * 70)

    staged_data = _load_staged_data()
    print(f"\n  Loaded: {len(staged_data)} sources")
# ====
    # TẦNG 11B-1: TIME ALIGNMENT
    # ====
    print("\n" + "=" * 70)
    print(" TẦNG 11B-1: TIME ALIGNMENT")
    print("=" * 70)

    print("\n[Anchor Events] Finding anchors...")
    anchor_pairs = {}

    # Pair 1: QR vs IPC
    if "SRC-03_qr" in staged_data and "SRC-02_ipc" in staged_data:
        anchors = find_anchor_events(
            staged_data["SRC-03_qr"],
            staged_data["SRC-02_ipc"],
            match_on=["lot_ref_norm"],
            ts_col_a="ts_raw",
            ts_col_b="ts_raw",
            max_diff_min=15,
        )
        anchor_pairs["QR_vs_IPC"] = anchors
        print(f" ✓ QR vs IPC: {len(anchors)} anchors")

    # Pair 2: QR vs QC Auto
    if "SRC-03_qr" in staged_data and "SRC-04_qc_auto" in staged_data:
        anchors = find_anchor_events(
            staged_data["SRC-03_qr"],
            staged_data["SRC-04_qc_auto"],
            match_on=["lot_ref_norm"],
            ts_col_a="ts_raw",
            ts_col_b="ts_raw",
            max_diff_min=60,
        )
        anchor_pairs["QR_vs_QC_AUTO"] = anchors
        print(f" ✓ QR vs QC Auto: {len(anchors)} anchors")

    # Offset estimation per station
    print("\n[Offset Estimation] Estimating per station...")
    offset_estimates = {}
    ipc_anchors = anchor_pairs.get("QR_vs_IPC", pd.DataFrame())

    if len(ipc_anchors) > 0 and "station_ref_norm" in ipc_anchors.columns:
        offset_estimates = estimate_offsets_per_station(
            ipc_anchors,
            station_col="station_ref_norm",
            diff_col="raw_diff_sec",
            min_anchors=5,
        )
        for sid, est in offset_estimates.items():
            print(
                f" ✓ {sid}: offset={est.offset_sec:+.1f}s, "
                f"MAD={est.mad_sec:.1f}s, n={est.n_anchors}, "
                f"conf={est.confidence:.2f}"
            )

    # Drift detection
    print("\n[Drift Detection] Detecting linear drift...")
    drift_estimates = {}
    if len(ipc_anchors) > 0 and "station_ref_norm" in ipc_anchors.columns:
        for station_id, group in ipc_anchors.groupby("station_ref_norm"):
            drift = detect_drift(group, str(station_id))
            if drift is not None:
                drift_estimates[str(station_id)] = drift
                sig = "SIG " if drift.is_significant else ""
                print(
                    f" {sig}{station_id}: base={drift.base_offset_sec:+.1f}s, "
                    f"drift={drift.drift_per_day_sec:+.3f}s/day, R2={drift.r_squared:.2f}"
                )

    # Apply offsets
    print("\n[Apply Offsets] Applying to all sources...")
    aligned_data = {}
    for source_id, df in staged_data.items():
        if "station_ref_norm" in df.columns and "ts_raw" in df.columns:
            aligned = apply_offsets_to_source(
                df,
                station_col="station_ref_norm",
                ts_col="ts_raw",
                offsets=offset_estimates,
                output_col="ts_aligned",
            )
        elif "ts_raw" in df.columns:
            aligned = df.copy()
            aligned["ts_aligned"] = pd.to_datetime(aligned["ts_raw"], errors="coerce", dayfirst=True, utc=True)
            aligned["ts_aligned_offset_sec"] = 0.0
            aligned["ts_aligned_station"] = None
        else:
            aligned = df.copy()

        aligned_data[source_id] = aligned
        print(f" ✓ {source_id}: {len(aligned)} rows")
    # ============================================================
    # TẦNG 11B-2: ENTITY RESOLUTION
    # ============================================================
    print("\n" + "=" * 70)
    print("  TẦNG 11B-2: ENTITY RESOLUTION")
    print("=" * 70)

    mapping_df, unresolved = resolve_all_lots(aligned_data)

    # Apply resolution
    print("\n[Apply Resolution] Applying to aligned data...")
    resolved_data = apply_resolution_to_staged(aligned_data, mapping_df)

    # Save resolved
    for source_id, df in resolved_data.items():
        out_dir = RESOLVED_DIR / source_id
        out_dir.mkdir(parents=True, exist_ok=True)
        df.to_parquet(out_dir / f"resolved_{source_id}.parquet", index=False)
        print(f"  ✓ Saved: resolved_{source_id}.parquet")

    # Save resolution audit
    save_resolution_audit(mapping_df, unresolved)

    # ============================================================
    # SUMMARY
    # ============================================================
    elapsed = time.time() - t0

    print("\n" + "=" * 70)
    print(f"  BƯỚC 11B HOÀN TẤT trong {elapsed:.2f}s")
    print(f"  Stations aligned: {len(offset_estimates)}")
    print(f"  Aliases resolved: {mapping_df['canonical_id'].notna().sum()} / {len(mapping_df)}")
    print(f"  Needs review:     {len(unresolved)}")
    print("=" * 70)

    return {
        "aligned_data": aligned_data,
        "mapping_df": mapping_df,
        "unresolved": unresolved,
        "offset_estimates": offset_estimates,
        "drift_estimates": drift_estimates,
    }


if __name__ == "__main__":
    run_step_11b()
