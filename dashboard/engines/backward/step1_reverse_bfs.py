"""
step1_reverse_bfs.py — Bước 1: Sinh candidate set F.
Từ lô NG, duyệt ngược genealogy + temporal để tìm mọi "nghi phạm".
"""
import pandas as pd
import networkx as nx
from dataclasses import dataclass


@dataclass
class Candidate:
    candidate_type: str    # "MACHINE", "MATERIAL", "BATCH", "SHIFT"
    candidate_id: str
    n_related_lots: int
    n_ng_lots: int
    related_lot_ids: list
    evidence_source: str


def _count_ng_lots(lot_ids: list, lots: pd.DataFrame) -> int:
    """Đếm số lots bị NG trong tập."""
    if "is_ng" not in lots.columns or len(lots) == 0:
        return 0
    subset = lots[lots["lot_id"].isin(lot_ids)]
    return int(subset["is_ng"].sum())


def _ensure_is_ng(lots: pd.DataFrame) -> pd.DataFrame:
    """Đảm bảo lots có cột is_ng."""
    lots = lots.copy()
    if "is_ng" not in lots.columns:
        if "qty_ng" in lots.columns:
            lots["is_ng"] = (lots["qty_ng"] > 0).astype(int)
        else:
            lots["is_ng"] = 0
    return lots


def generate_candidates(
    lot_id: str,
    lots: pd.DataFrame,
    events: pd.DataFrame,
    consumption: pd.DataFrame,
    G: nx.DiGraph,
    max_depth: int = 5,
) -> list:
    """
    Sinh tập nghi phạm F cho lô NG.
    Chiến lược:
        1. Reverse BFS trên genealogy → ancestors
        2. Từ ancestors, extract machines, materials, batches, shifts
        3. Cho mỗi candidate, đếm số lots liên quan + số NG
    """
    lots = _ensure_is_ng(lots)
    candidates = {}

    # ============================================================
    # 1a. Reverse BFS — tìm ancestor lots
    # ============================================================
    ancestor_lots = {lot_id}
    if lot_id in G:
        for anc in nx.ancestors(G, lot_id):
            ancestor_lots.add(anc)

    # ============================================================
    # 1b. Tìm machines từ events của ancestors
    # ============================================================
    if len(events) > 0 and "station_id" in events.columns:
        ancestor_events = events[events["lot_id"].isin(ancestor_lots)]

        for station_id, group in ancestor_events.groupby("station_id"):
            lot_ids = group["lot_id"].unique().tolist()
            ng_lots = _count_ng_lots(lot_ids, lots)

            key = ("MACHINE", station_id)
            candidates[key] = Candidate(
                candidate_type="MACHINE",
                candidate_id=str(station_id),
                n_related_lots=len(lot_ids),
                n_ng_lots=ng_lots,
                related_lot_ids=lot_ids,
                evidence_source="lot_event",
            )

    # ============================================================
    # 1c. Tìm materials từ consumption
    # ============================================================
    if len(consumption) > 0 and "mat_lot_id" in consumption.columns:
        ancestor_cons = consumption[consumption["lot_id"].isin(ancestor_lots)]

        for mat_lot_id, group in ancestor_cons.groupby("mat_lot_id"):
            lot_ids = group["lot_id"].unique().tolist()
            ng_lots = _count_ng_lots(lot_ids, lots)

            key = ("MATERIAL", mat_lot_id)
            candidates[key] = Candidate(
                candidate_type="MATERIAL",
                candidate_id=str(mat_lot_id),
                n_related_lots=len(lot_ids),
                n_ng_lots=ng_lots,
                related_lot_ids=lot_ids,
                evidence_source="material_consumption",
            )

    # ============================================================
    # 1d. Tìm batches từ genealogy
    # ============================================================
    for anc_lot in ancestor_lots:
        if str(anc_lot).startswith("BATCH-HT"):
            if anc_lot in G:
                children = list(G.successors(anc_lot))
                ng_lots = _count_ng_lots(children, lots)

                key = ("BATCH", anc_lot)
                candidates[key] = Candidate(
                    candidate_type="BATCH",
                    candidate_id=str(anc_lot),
                    n_related_lots=len(children),
                    n_ng_lots=ng_lots,
                    related_lot_ids=children,
                    evidence_source="genealogy",
                )

    # ============================================================
    # 1e. Tìm shifts
    # ============================================================
    if len(events) > 0 and "shift" in events.columns:
        ancestor_events = events[events["lot_id"].isin(ancestor_lots)]

        for shift, group in ancestor_events.groupby("shift"):
            if pd.isna(shift):
                continue
            lot_ids = group["lot_id"].unique().tolist()
            ng_lots = _count_ng_lots(lot_ids, lots)

            key = ("SHIFT", str(shift))
            candidates[key] = Candidate(
                candidate_type="SHIFT",
                candidate_id=str(shift),
                n_related_lots=len(lot_ids),
                n_ng_lots=ng_lots,
                related_lot_ids=lot_ids,
                evidence_source="lot_event",
            )

    return list(candidates.values())
