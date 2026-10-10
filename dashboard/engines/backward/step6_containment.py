"""
step6_containment.py — Bước 6: Containment Scope (minimal).
"""
import pandas as pd
import networkx as nx
from dataclasses import dataclass
from typing import Optional


@dataclass
class ContainmentResult:
    candidate_id: str
    candidate_type: str
    isolate_lot_ids: list
    n_isolated: int
    n_baseline: int
    reduction_pct: float
    baseline_method: str
    rationale: list


def compute_containment(
    candidate: dict,
    lot_id_ng: str,
    lots: pd.DataFrame,
    events: pd.DataFrame,
    consumption: pd.DataFrame,
    G: nx.DiGraph,
    baseline_scope: list = None,
) -> ContainmentResult:
    """Tính containment scope tối thiểu."""
    cand_type = candidate["candidate_type"]
    cand_id = candidate["candidate_id"]

    isolate = set()
    rationale = []

    # Nguyên tắc 1: luôn cách ly lô NG gốc
    isolate.add(lot_id_ng)
    rationale.append(f"Lô NG gốc: {lot_id_ng}")

    # Nguyên tắc 2: cách ly dựa trên loại candidate
    if cand_type == "MACHINE":
        if len(events) > 0 and "station_id" in events.columns:
            machine_events = events[
                (events["station_id"] == cand_id) & (events["lot_id"] != lot_id_ng)
            ]
            ng_events = events[events["lot_id"] == lot_id_ng]

            if len(ng_events) > 0:
                ts_col = "ts_aligned" if "ts_aligned" in ng_events.columns else "ts_raw"
                ng_ts = pd.to_datetime(ng_events[ts_col], errors="coerce").min()

                if pd.notna(ng_ts) and ts_col in machine_events.columns:
                    machine_events = machine_events.copy()
                    machine_events[ts_col] = pd.to_datetime(machine_events[ts_col], errors="coerce")
                    window = machine_events[
                        (machine_events[ts_col] >= ng_ts - pd.Timedelta(hours=12))
                        & (machine_events[ts_col] <= ng_ts + pd.Timedelta(hours=12))
                    ]
                    same_machine_lots = window["lot_id"].unique().tolist()
                    isolate.update(same_machine_lots)
                    rationale.append(
                        f"Lots cùng machine {cand_id} trong ±12h: {len(same_machine_lots)}"
                    )

    elif cand_type == "MATERIAL":
        if len(consumption) > 0 and "mat_lot_id" in consumption.columns:
            mat_cons = consumption[consumption["mat_lot_id"] == cand_id]
            same_mat_lots = mat_cons["lot_id"].unique().tolist()
            isolate.update(same_mat_lots)
            rationale.append(f"Lots dùng chung material {cand_id}: {len(same_mat_lots)}")

    elif cand_type == "BATCH":
        if cand_id in G:
            children = list(G.successors(cand_id))
            isolate.update(children)
            rationale.append(f"Lots con của batch {cand_id}: {len(children)}")

    elif cand_type == "SHIFT":
        if len(events) > 0 and "shift" in events.columns:
            ng_events = events[events["lot_id"] == lot_id_ng]
            if len(ng_events) > 0:
                ts_col = "ts_aligned" if "ts_aligned" in ng_events.columns else "ts_raw"
                ng_ts = pd.to_datetime(ng_events[ts_col], errors="coerce").min()
                if pd.notna(ng_ts):
                    ng_date = ng_ts.normalize()
                    events_copy = events.copy()
                    events_copy[ts_col] = pd.to_datetime(events_copy[ts_col], errors="coerce")
                    same_shift = events_copy[
                        (events_copy["shift"] == cand_id)
                        & (events_copy[ts_col].dt.normalize() == ng_date)
                    ]["lot_id"].unique().tolist()
                    isolate.update(same_shift)
                    rationale.append(
                        f"Lots cùng shift {cand_id} ngày {ng_date.date()}: {len(same_shift)}"
                    )

    # Baseline: cách ly tất cả lots trong ngày
    if baseline_scope is None:
        if len(events) > 0:
            ng_events = events[events["lot_id"] == lot_id_ng]
            if len(ng_events) > 0:
                ts_col = "ts_aligned" if "ts_aligned" in ng_events.columns else "ts_raw"
                ng_date = pd.to_datetime(ng_events[ts_col], errors="coerce").min().normalize()
                events_copy = events.copy()
                events_copy[ts_col] = pd.to_datetime(events_copy[ts_col], errors="coerce")
                baseline = events_copy[
                    events_copy[ts_col].dt.normalize() == ng_date
                ]["lot_id"].unique().tolist()
            else:
                baseline = []
        else:
            baseline = []
    else:
        baseline = baseline_scope

    n_isolated = len(isolate)
    n_baseline = len(baseline)

    if n_baseline > 0:
        reduction_pct = 1 - (n_isolated / n_baseline)
    else:
        reduction_pct = 0.0

    return ContainmentResult(
        candidate_id=cand_id,
        candidate_type=cand_type,
        isolate_lot_ids=sorted(list(isolate)),
        n_isolated=n_isolated,
        n_baseline=n_baseline,
        reduction_pct=round(reduction_pct, 4),
        baseline_method="all_lots_in_day",
        rationale=rationale,
    )
