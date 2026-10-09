"""
impact_engine.py — Orchestrator Forward Impact Cascade.

Step 3 (netting) đọc đầu vào từ bảng canonical + config, không hardcode.
Một JT được đánh dấu LATE khi rớt kiểm tra thời gian (step 6) HOẶC
netting cho thấy thiếu hàng vào ngày đáo hạn của JT đó.
"""
import pandas as pd
from flowsight.engines.config import (
    OPENING_INVENTORY, FALLBACK_DAILY_PRODUCTION, NETTING_HORIZON_DAYS,
)
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

    # ------------------------------------------------------------------
    # Helpers đọc dữ liệu từ bảng
    # ------------------------------------------------------------------
    def _product_for_station(self, station_id: str, affected_lots: list = None) -> str:
        # Giả định mô hình (ghi nhận): tổn thất của incident được quy về product
        # chính của line để cho biên bảo thủ (worst-case). HT phục vụ 2 line nên
        # dùng product chiếm đa số trong các lot bị ảnh hưởng.
        # TODO: multi-product ATP (phân bổ tổn thất theo tỷ trọng từng product).
        if station_id == "STN-HT" and affected_lots:
            lots = self.tables.get("lot", pd.DataFrame())
            if len(lots):
                prods = lots[lots["lot_id"].isin(affected_lots)]["product_id"].tolist()
                if prods:
                    return pd.Series(prods).mode().iloc[0]
        if station_id in ["STN-M2", "STN-M1", "STN-AS1", "STN-T1"]:
            return "PROD-P1"
        if station_id in ["STN-AS2"]:
            return "PROD-P3"
        return "PROD-P1" if station_id == "STN-HT" else "PROD-P3"

    def _daily_production(self, product_id: str, ref_date: pd.Timestamp) -> float:
        """Sản lượng/ngày của product: trung bình ngày từ bảng lot (toàn horizon)."""
        lots = self.tables.get("lot", pd.DataFrame())
        if len(lots) == 0 or "created_ts" not in lots.columns:
            return FALLBACK_DAILY_PRODUCTION.get(product_id, 900.0)
        lots = lots.copy()
        lots["created_dt"] = pd.to_datetime(lots["created_ts"], errors="coerce")
        sel = lots[lots["product_id"] == product_id]
        if len(sel) == 0:
            return FALLBACK_DAILY_PRODUCTION.get(product_id, 900.0)
        daily = sel.groupby(sel["created_dt"].dt.date)["qty"].sum()
        return round(float(daily.mean()), 1) if len(daily) else FALLBACK_DAILY_PRODUCTION.get(product_id, 900.0)

    def _shipment_schedule(self, product_id: str, start_date: pd.Timestamp, days: int) -> list:
        """Lịch giao hàng/ngày của product từ bảng jt_order (theo due_ts)."""
        jt_order = self.tables.get("jt_order", pd.DataFrame())
        sched = [0.0] * days
        if len(jt_order) == 0:
            return sched
        jo = jt_order.copy()
        jo["due_dt"] = pd.to_datetime(jo["due_ts"], errors="coerce")
        jo = jo[(jo["product_id"] == product_id) & jo["due_dt"].notna()]
        for _, r in jo.iterrows():
            idx = (r["due_dt"].normalize() - start_date.normalize()).days
            if 0 <= idx < days:
                sched[idx] += float(r.get("qty", 0) or 0)
        return sched

    # ------------------------------------------------------------------
    def predict(self, case: dict) -> dict:
        station_id = case["station_id"]
        downtime_h = case["duration_h"]
        start_ts = pd.Timestamp(case["start_ts"])
        start_date = start_ts.normalize()

        result = {
            "case_id": case["case_id"],
            "incident_id": case["incident_id"],
            "station_id": station_id,
            "duration_h": downtime_h,
            "start_ts": case["start_ts"],
            "steps": {},
        }

        # STEP 1: ΔQ
        rate = get_effective_rate(self.tables, station_id)
        s1 = compute_qty_loss(downtime_h, rate)
        result["steps"]["step1_qty_loss"] = s1

        # STEP 2: T_starve
        s2 = compute_time_to_starve(
            wip_buffer_qty=80, downstream_rate=85,
            note="WIP từ buffer tại bottleneck",
        )
        result["steps"]["step2_time_to_starve"] = s2

        # Lot bị ảnh hưởng (dùng để xác định product)
        affected_lots = self._affected_lots(station_id, start_ts, downtime_h)

        # STEP 3: Netting — đọc từ bảng
        product_id = self._product_for_station(station_id, affected_lots)
        days = NETTING_HORIZON_DAYS
        opening = OPENING_INVENTORY.get(product_id, 450.0)
        daily_prod = self._daily_production(product_id, start_date)
        baseline_prod = [daily_prod] * days
        baseline_ship = self._shipment_schedule(product_id, start_date, days)
        incident_prod = [max(0.0, daily_prod - s1["qty_lost"])] + [daily_prod] * (days - 1)

        s3 = compute_netting(
            opening_inventory=opening,
            baseline_production=baseline_prod,
            baseline_shipment=baseline_ship,
            incident_production=incident_prod,
            days=days,
        )
        s3["inputs"] = {
            "product_id": product_id,
            "opening_inventory": opening,
            "daily_production": daily_prod,
            "shipment_schedule": baseline_ship,
        }
        result["steps"]["step3_netting"] = s3

        # STEP 4: Material Check
        s4 = compute_material_check(self.tables, product_id, s3["total_shortage"] or s1["qty_lost"])
        result["steps"]["step4_material_check"] = s4

        # STEP 5: Monte Carlo
        base_shortfall = s3["total_shortage"] if s3["total_shortage"] > 0 else s1["qty_lost"]
        s5 = simulate_shortfall(base_shortfall, seed=42)
        result["steps"]["step5_monte_carlo"] = [s5]

        # STEP 6: Cut-off check
        jts_affected = self._find_affected_jts(station_id, product_id)
        cutoffs = []
        for jt_id in jts_affected[:5]:
            s6 = check_cutoff(self.tables, jt_id, start_ts, downtime_h, s2["time_to_starve_h"])
            cutoffs.append(s6)
        result["steps"]["step6_cutoff"] = cutoffs

        # SUMMARY: Per-JT ATP — cấp phát supply theo thứ tự đáo hạn.
        # JT đã DEPARTED đủ số lượng được coi là hoàn thành, không xét trễ.
        jt_order = self.tables.get("jt_order", pd.DataFrame())
        shipment = self.tables.get("shipment", pd.DataFrame())
        fulfilled = set()
        if len(shipment):
            for _, sh in shipment.iterrows():
                if str(sh.get("status", "")).upper() == "DEPARTED":
                    fulfilled.add(sh.get("jt_id"))

        jts_late = []
        total_shortage_atp = 0.0
        if len(jt_order):
            jo = jt_order[jt_order["product_id"] == product_id].copy()
            jo["due_dt"] = pd.to_datetime(jo["due_ts"], errors="coerce")
            jo = jo.sort_values(["due_dt", "jt_id"])
            # Supply khả dụng trước mỗi ngày đáo hạn: opening + SX các ngày trước đó
            # (SX trong ngày đáo hạn chưa kịp hoàn tất để giao).
            cum_prod = [0.0]
            for d in range(days):
                cum_prod.append(cum_prod[-1] + (incident_prod[d] if d < len(incident_prod) else 0.0))
            remaining = opening
            last_due_idx = -1
            for _, jr in jo.iterrows():
                jt_id = jr["jt_id"]
                due = jr["due_dt"]
                if pd.isna(due):
                    continue
                due_idx = (due.normalize() - start_date).days
                if due_idx < 0 or due_idx > days:
                    continue
                # Cộng dồn SX từ sau lần cấp phát trước đến trước ngày đáo hạn
                for d in range(last_due_idx + 1, due_idx):
                    remaining += incident_prod[d] if d < len(incident_prod) else 0.0
                last_due_idx = max(last_due_idx, due_idx - 1)
                need = float(jr.get("qty", 0) or 0)
                if jt_id in fulfilled:
                    # Đã giao đủ: trừ supply nhưng không xét trễ
                    remaining -= need
                    continue
                if remaining >= need:
                    remaining -= need
                else:
                    short = need - remaining
                    remaining = 0.0
                    total_shortage_atp += short
                    # Kiểm tra time-check tương ứng
                    c = next((x for x in cutoffs if x.get("jt_id") == jt_id), {})
                    jts_late.append({
                        "jt_id": jt_id,
                        "p_late": s5["p_late"],
                        "shortfall_qty": int(round(short)),
                        "late_by": "qty" + ("+time" if c.get("status") == "LATE" else ""),
                        "due_ts": str(jr.get("due_ts")),
                    })
            # Cộng time-based LATE chưa nằm trong danh sách
            for c in cutoffs:
                if c.get("status") == "LATE" and not any(j["jt_id"] == c.get("jt_id") for j in jts_late):
                    jts_late.append({
                        "jt_id": c.get("jt_id"),
                        "p_late": s5["p_late"],
                        "shortfall_qty": int(s5["expected_shortage"]),
                        "late_by": "time",
                    })

        # Monte Carlo trên shortfall ATP thực tế
        base_atp = total_shortage_atp if total_shortage_atp > 0 else (s3["total_shortage"] if s3["total_shortage"] > 0 else s1["qty_lost"])
        s5_atp = simulate_shortfall(base_atp, seed=42)
        result["steps"]["step5_monte_carlo"] = [s5_atp]
        for j in jts_late:
            if j["late_by"].startswith("qty"):
                j["p_late"] = s5_atp["p_late"]
                j["shortfall_qty"] = int(s5_atp["expected_shortage"])

        result["summary"] = {
            "qty_lost": s1["qty_lost"],
            "total_shortage": int(round(total_shortage_atp)),
            "jts_late": jts_late,
            "affected_lot_ids": affected_lots,
            "recommended_action": self._recommend_action(s5_atp["p_late"], total_shortage_atp),
        }
        return result

    def _affected_lots_for_case(self, incident_id: str) -> list:
        return []  # điền bên dưới trong predict (cần station_id + start_ts)

    def _affected_lots(self, station_id: str, start_ts: pd.Timestamp, duration_h: float) -> list:
        """Lot có event tại trạm trong cửa sổ incident."""
        events = self.tables.get("lot_event", pd.DataFrame())
        if len(events) == 0:
            return []
        ev = events.copy()
        # dùng ts_aligned nếu có, fallback ts_raw
        ts_col = "ts_aligned" if "ts_aligned" in ev.columns else "ts_raw"
        ev["ts"] = pd.to_datetime(ev[ts_col], errors="coerce")
        end_ts = start_ts + pd.Timedelta(hours=duration_h)
        mask = (ev["station_id"] == station_id) & (ev["ts"] >= start_ts) & (ev["ts"] <= end_ts)
        return sorted(ev[mask]["lot_id"].unique().tolist())

    def _find_affected_jts(self, station_id: str, product_id: str = None) -> list:
        """JT bị ảnh hưởng: lot qua trạm -> allocation -> JT (lọc theo product)."""
        events = self.tables.get("lot_event", pd.DataFrame())
        alloc = self.tables.get("jt_allocation", pd.DataFrame())
        jt_order = self.tables.get("jt_order", pd.DataFrame())

        jts = []
        if len(events) and len(alloc):
            lots_at_station = events[events["station_id"] == station_id]["lot_id"].unique()
            jts = alloc[alloc["lot_id"].isin(lots_at_station)]["jt_id"].unique().tolist()

        if product_id and len(jt_order):
            prod_jts = set(jt_order[jt_order["product_id"] == product_id]["jt_id"].tolist())
            jts = [j for j in jts if j in prod_jts] or jts

        if not jts and len(jt_order):
            jts = jt_order["jt_id"].tolist()[:5]
        if not jts:
            jts = ["JT-0231", "JT-0235"]
        # Sắp xếp theo due_ts để JT đáo hạn sớm lên trước
        if len(jt_order):
            due_map = dict(zip(jt_order["jt_id"], pd.to_datetime(jt_order["due_ts"], errors="coerce")))
            jts = sorted(set(jts), key=lambda j: (pd.isna(due_map.get(j)), due_map.get(j)))
        return jts

    def _recommend_action(self, p_late: float, shortfall: float) -> str:
        if p_late < 0.1 and shortfall < 50:
            return "no_action_needed"
        elif p_late < 0.5:
            return "monitor"
        elif p_late < 0.9:
            return "resequencing"
        return "resequencing + OT2"
