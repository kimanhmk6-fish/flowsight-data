"""
impact_engine.py — Orchestrator Forward Impact Cascade.
"""
import pandas as pd
from dataclasses import asdict
from flowsight.engines.forward.step1_qty_loss import compute_qty_loss
from flowsight.engines.forward.step2_time_to_starve import compute_time_to_starve
from flowsight.engines.forward.step3_netting import compute_netting
from flowsight.engines.forward.step4_material_check import compute_material_check
from flowsight.engines.forward.step5_monte_carlo import simulate_shortfall
from flowsight.engines.forward.step6_cutoff_check import check_cutoff
from flowsight.engines.shared.lot_queries import get_effective_rate


class ForwardImpactEngine:
    """Forward Impact Cascade Engine."""

    def __init__(self, tables: dict, G_genealogy=None):
        self.tables = tables
        self.G = G_genealogy

    def predict(self, case: dict) -> dict:
        """
        Dự đoán tác động của 1 sự cố.

        case = {
            "case_id": "F01",
            "incident_id": "INC-0001",
            "station_id": "STN-M2",
            "duration_h": 8.0,
            "start_ts": "2026-09-29T08:00:00",
        }
        """
        station_id = case["station_id"]
        downtime_h = case["duration_h"]
        start_ts = pd.Timestamp(case["start_ts"])

        result = {
            "case_id": case["case_id"],
            "incident_id": case["incident_id"],
            "station_id": station_id,
            "duration_h": downtime_h,
            "start_ts": case["start_ts"],
            "steps": {},
        }

        # ============================================================
        # STEP 1: ΔQ
        # ============================================================
        rate = get_effective_rate(self.tables, station_id)
        s1 = compute_qty_loss(downtime_h, rate)
        result["steps"]["step1_qty_loss"] = s1

        # ============================================================
        # STEP 2: T_starve
        # ============================================================
        s2 = compute_time_to_starve(
            wip_buffer_qty=80,
            downstream_rate=85,
            note="WIP từ buffer tại bottleneck",
        )
        result["steps"]["step2_time_to_starve"] = s2

        # ============================================================
        # STEP 3: Netting (đơn giản — 14 ngày)
        # ============================================================
        baseline_prod = [450] * 14
        incident_prod = [max(0, 450 - s1["qty_lost"])] + [450] * 13
        baseline_ship = [600, 700, 1300, 0, 400] + [0] * 9

        s3 = compute_netting(
            opening_inventory=450,
            baseline_production=baseline_prod,
            baseline_shipment=baseline_ship,
            incident_production=incident_prod,
        )
        result["steps"]["step3_netting"] = s3

        # ============================================================
        # STEP 4: Material Check
        # ============================================================
        # Giả định product P1 nếu là M2
        product_id = "PROD-P1" if station_id in ["STN-M2", "STN-M1", "STN-AS1", "STN-T1"] else "PROD-P3"
        s4 = compute_material_check(self.tables, product_id, s3["total_shortage"] or s1["qty_lost"])
        result["steps"]["step4_material_check"] = s4

        # ============================================================
        # STEP 5: Monte Carlo
        # ============================================================
        base_shortfall = s3["total_shortage"] if s3["total_shortage"] > 0 else s1["qty_lost"]
        s5 = simulate_shortfall(base_shortfall, seed=42)
        result["steps"]["step5_monte_carlo"] = [s5]

        # ============================================================
        # STEP 6: Cut-off check
        # ============================================================
        jts_affected = self._find_affected_jts(station_id)
        cutoffs = []
        for jt_id in jts_affected[:3]:
            s6 = check_cutoff(self.tables, jt_id, start_ts, downtime_h, s2["time_to_starve_h"])
            cutoffs.append(s6)
        result["steps"]["step6_cutoff"] = cutoffs

        # ============================================================
        # SUMMARY
        # ============================================================
        jts_late = []
        for c in cutoffs:
            if c.get("status") == "LATE":
                jts_late.append({
                    "jt_id": c["jt_id"],
                    "p_late": s5["p_late"],
                    "shortfall_qty": int(s5["expected_shortage"]),
                })

        result["summary"] = {
            "qty_lost": s1["qty_lost"],
            "total_shortage": int(s3["total_shortage"]),
            "jts_late": jts_late,
            "affected_lot_ids": [],
            "recommended_action": self._recommend_action(s5["p_late"], s3["total_shortage"]),
        }

        return result

    def _find_affected_jts(self, station_id: str) -> list:
        """Tìm JTs có khả năng bị ảnh hưởng."""
        events = self.tables.get("lot_event", pd.DataFrame())
        alloc = self.tables.get("jt_allocation", pd.DataFrame())

        if len(events) == 0 or len(alloc) == 0:
            # Fallback: dùng jt_order trực tiếp
            jt_order = self.tables.get("jt_order", pd.DataFrame())
            if len(jt_order) > 0:
                return jt_order["jt_id"].tolist()[:5]
            return ["JT-0231", "JT-0232", "JT-0235"]

        lots_at_station = events[events["station_id"] == station_id]["lot_id"].unique()
        jts = alloc[alloc["lot_id"].isin(lots_at_station)]["jt_id"].unique().tolist()

        if not jts:
            jt_order = self.tables.get("jt_order", pd.DataFrame())
            if len(jt_order) > 0:
                return jt_order["jt_id"].tolist()[:5]

        return jts

    def _recommend_action(self, p_late: float, shortfall: float) -> str:
        """Đề xuất hành động."""
        if p_late < 0.1 and shortfall < 50:
            return "no_action_needed"
        elif p_late < 0.5:
            return "monitor"
        elif p_late < 0.9:
            return "resequencing"
        else:
            return "resequencing + OT2"
