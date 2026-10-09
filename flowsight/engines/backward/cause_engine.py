"""
cause_engine.py — Orchestrator Backward Cause Ranking.
"""
import pandas as pd
from dataclasses import asdict

from flowsight.engines.backward.step1_reverse_bfs import generate_candidates
from flowsight.engines.backward.step2_fisher_exact import fisher_test_batch
from flowsight.engines.backward.step3_risk_lift import compute_risk_lift
from flowsight.engines.backward.step4_spc_signal import detect_spc_signals_batch
from flowsight.engines.backward.step5_scoring import (
    score_candidates, get_top_k, is_insufficient_evidence,
)
from flowsight.engines.backward.step6_containment import compute_containment


class BackwardCauseEngine:
    """Backward Cause Ranking Engine."""

    def __init__(self, tables: dict, G_genealogy):
        self.lots = tables.get("lot", pd.DataFrame())
        self.events = tables.get("lot_event", pd.DataFrame())
        self.consumption = tables.get("material_consumption", pd.DataFrame())
        self.allocations = tables.get("jt_allocation", pd.DataFrame())
        self.qc_result = tables.get("qc_result", pd.DataFrame())
        self.G = G_genealogy

        # Ensure is_ng: lấy từ kết quả QC (NG/FAIL), không phải qty_ng sản xuất
        # (qty_ng là anomaly vật lý ngẫu nhiên, khác với NG do lỗi hệ thống)
        self.lots = self.lots.copy()
        ng_lots = set()
        if len(self.qc_result) > 0 and "result" in self.qc_result.columns:
            ng_mask = self.qc_result["result"].astype(str).str.upper().isin(["NG", "FAIL", "NOT OK"])
            ng_lots = set(self.qc_result[ng_mask]["lot_id"].unique().tolist())
        self.lots["is_ng"] = self.lots["lot_id"].isin(ng_lots).astype(int)

    def diagnose(self, case: dict) -> dict:
        """
        case = {
            "case_id": "R01",
            "incident_id": "INC-0013",
            "lot_id_ng": "LOT-0403",
            "qc_station": "STN-LAB",
            "qc_characteristic": "Lực ép",
        }
        """
        lot_id = case["lot_id_ng"]

        result = {
            "case_id": case.get("case_id"),
            "incident_id": case.get("incident_id"),
            "lot_id_ng": lot_id,
            "qc_station": case.get("qc_station"),
            "qc_characteristic": case.get("qc_characteristic"),
            "steps": {},
            "status": "PENDING",
        }

        # ============================================================
        # STEP 1: Reverse BFS
        # ============================================================
        candidates = generate_candidates(
            lot_id=lot_id,
            lots=self.lots,
            events=self.events,
            consumption=self.consumption,
            G=self.G,
            max_depth=5,
        )
        result["steps"]["step1_candidates"] = [asdict(c) for c in candidates]
        result["n_candidates"] = len(candidates)

        if len(candidates) == 0:
            result["status"] = "INSUFFICIENT_EVIDENCE"
            result["message"] = "Không tìm thấy candidate nào"
            return result

        # ============================================================
        # STEP 2: Fisher Exact
        # ============================================================
        fisher_results = fisher_test_batch(candidates, self.lots)
        result["steps"]["step2_fisher"] = [asdict(r) for r in fisher_results]

        # ============================================================
        # STEP 3: Risk Lift
        # ============================================================
        lift_results = []
        for fr in fisher_results:
            try:
                lr = compute_risk_lift(fr)
                lift_results.append(lr)
            except Exception:
                pass
        result["steps"]["step3_lift"] = [asdict(r) for r in lift_results]

        # ============================================================
        # STEP 4: SPC Signal
        # ============================================================
        spc_signals = detect_spc_signals_batch(
            candidates, self.events, self.qc_result,
        )
        result["steps"]["step4_spc"] = [asdict(s) for s in spc_signals]

        # ============================================================
        # STEP 5: Scoring
        # ============================================================
        scored = score_candidates(
            candidates, fisher_results, lift_results, spc_signals,
        )
        result["steps"]["step5_scored"] = [asdict(c) for c in scored]

        # Check insufficient evidence (case R07)
        if is_insufficient_evidence(scored):
            result["status"] = "INSUFFICIENT_EVIDENCE"
            result["message"] = "Chưa đủ bằng chứng để kết luận nguyên nhân"
            result["top_causes"] = []
            return result

        # ============================================================
        # STEP 6: Containment
        # ============================================================
        top1 = scored[0]
        top1_candidate = next(
            (c for c in candidates if c.candidate_id == top1.candidate_id),
            None,
        )

        if top1_candidate is not None:
            containment = compute_containment(
                candidate={
                    "candidate_type": top1.candidate_type,
                    "candidate_id": top1.candidate_id,
                    "related_lot_ids": top1_candidate.related_lot_ids,
                },
                lot_id_ng=lot_id,
                lots=self.lots,
                events=self.events,
                consumption=self.consumption,
                G=self.G,
            )
            result["steps"]["step6_containment"] = asdict(containment)
        else:
            containment = None
            result["steps"]["step6_containment"] = {}

        # ============================================================
        # SUMMARY
        # ============================================================
        top3 = get_top_k(scored, k=3)

        result["status"] = "RESOLVED"
        result["top_causes"] = [
            {
                "rank": i + 1,
                "candidate_id": c.candidate_id,
                "candidate_type": c.candidate_type,
                "score": c.score,
                "p_value": c.p_value,
                "lift": c.lift,
                "is_significant": c.is_significant,
            }
            for i, c in enumerate(top3)
        ]
        result["top_cause"] = top3[0].candidate_id
        result["top_cause_type"] = top3[0].candidate_type
        result["confidence"] = round(min(0.99, top3[0].score * 1.1), 3)

        if containment is not None:
            result["isolate_lots"] = containment.isolate_lot_ids
            result["containment_reduction"] = containment.reduction_pct
        else:
            result["isolate_lots"] = [lot_id]
            result["containment_reduction"] = 0.0

        result["evidence_chain"] = top3[0].evidence_chain

        return result
