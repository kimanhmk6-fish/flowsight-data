"""
step4_spc_signal.py — Bước 4: SPC Signal (Nelson Rules).
"""
import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Optional
from flowsight.engines.shared.spc_utils import check_all_nelson_rules, compute_cpk_trend


@dataclass
class SPCSignalResult:
    candidate_id: str
    signal_type: str
    n_violations: int
    rules_triggered: list
    strength: float
    details: dict


def detect_spc_signals_for_machine(
    station_id: str,
    events: pd.DataFrame,
    param_cols: list = ["param_temp", "param_force", "param_vibration"],
) -> list:
    """Phát hiện SPC signal cho 1 machine."""
    results = []

    if len(events) == 0:
        return results

    station_events = events[events["station_id"] == station_id].copy()
    if len(station_events) < 5:
        return results

    if "ts_aligned" in station_events.columns:
        station_events = station_events.sort_values("ts_aligned")
    elif "ts_raw" in station_events.columns:
        station_events = station_events.sort_values("ts_raw")

    for col in param_cols:
        if col not in station_events.columns:
            continue

        # Cột *_raw (từ IPC)
        if col not in station_events.columns:
            continue

        values = pd.to_numeric(station_events[col], errors="coerce").dropna().values
        if len(values) < 5:
            continue

        spc = check_all_nelson_rules(values)
        if spc["n_violations"] > 0:
            strength = min(1.0, spc["n_violations"] / 20.0)
            results.append(SPCSignalResult(
                candidate_id=station_id,
                signal_type=f"PARAM_ANOMALY_{col}",
                n_violations=spc["n_violations"],
                rules_triggered=spc["rules_triggered"],
                strength=round(strength, 3),
                details={
                    "param": col, "mean": spc["mean"], "std": spc["std"],
                    "sample_size": len(values),
                },
            ))

    return results


def detect_cpk_decline(
    station_id: str,
    characteristic: str,
    qc_result: pd.DataFrame,
    min_samples: int = 10,
) -> Optional[SPCSignalResult]:
    """Phát hiện Cpk decline cho (station, characteristic)."""
    if len(qc_result) == 0:
        return None

    qc = qc_result[
        (qc_result["station_id"] == station_id)
        & (qc_result["characteristic"] == characteristic)
        & (qc_result["value"].notna())
    ].copy()

    if len(qc) < min_samples:
        return None

    if "measured_ts" in qc.columns:
        qc = qc.sort_values("measured_ts")

    lsl = qc["lsl"].dropna().iloc[0] if qc["lsl"].notna().any() else None
    usl = qc["usl"].dropna().iloc[0] if qc["usl"].notna().any() else None

    if lsl is None or usl is None:
        return None

    values = qc["value"].astype(float).values
    cpk_result = compute_cpk_trend(values, lsl, usl)

    if cpk_result.get("trend") == "DECLINING" and (cpk_result.get("cpk") or 2.0) < 1.33:
        return SPCSignalResult(
            candidate_id=f"{station_id}::{characteristic}",
            signal_type="CPK_DECLINE",
            n_violations=1,
            rules_triggered=["CPK_TREND"],
            strength=min(1.0, (1.33 - (cpk_result.get("cpk") or 0)) / 0.5),
            details={
                "station_id": station_id,
                "characteristic": characteristic,
                "cpk": cpk_result.get("cpk"),
                "trend": cpk_result.get("trend"),
                "delta": cpk_result.get("delta"),
            },
        )
    return None


def detect_spc_signals_batch(candidates, events, qc_result):
    all_signals = []

    for cand in candidates:
        # Hỗ trợ cả dataclass object và dict
        if isinstance(cand, dict):
            cand_type = cand.get("candidate_type", "UNKNOWN")
            cand_id = cand.get("candidate_id", "UNKNOWN")
        else:
            cand_type = getattr(cand, "candidate_type", "UNKNOWN")
            cand_id = getattr(cand, "candidate_id", "UNKNOWN")

        if cand_type == "MACHINE":
            signals = detect_spc_signals_for_machine(cand_id, events)
            all_signals.extend(signals)

            if len(qc_result) > 0 and "characteristic" in qc_result.columns:
                for char in qc_result["characteristic"].dropna().unique()[:3]:
                    s = detect_cpk_decline(cand_id, char, qc_result)
                    if s:
                        all_signals.append(s)

    return all_signals


