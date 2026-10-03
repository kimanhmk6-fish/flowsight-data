import simpy
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from config.constants import (
    SEED, NUM_DAYS, TARGET_LOTS, START_DATE_STR
)

np.random.seed(SEED)

class FactorySim:
    def __init__(self, env: simpy.Environment):
        self.env = env
        self.lots = []
        self.events = []
        self.genealogy = []
        self.consumption = []
        self.current_day = 0
        self.lot_counter = 0
        self.edge_counter = 0
        self.start_date = datetime.strptime(START_DATE_STR, "%Y-%m-%d")

    def run_day(self, day: int):
        self.current_day = day
        # 14 ngày x ~28-29 lots/ngày = 400 lots chính
        lots_today = 29 if day < 8 else 28
        for i in range(lots_today):
            if self.lot_counter >= 400:
                break
            prod_idx = (self.lot_counter % 4) + 1
            prod_id = f"PROD-P{prod_idx}"
            shift = "CA1" if (i % 2 == 0) else "CA2"
            base_hour = 6 if shift == "CA1" else 14
            created_ts = self.start_date + timedelta(days=day, hours=base_hour + (i % 8) * 0.8)
            lot = self.create_lot(prod_id, qty=200, day_idx=day, created_ts=created_ts, shift=shift)
            self.route_lot(lot)

        # Xử lý tách mẻ HT
        if day == 1:
            self.split_batch("BATCH-HT-B07", num_children=5, day_idx=1, prod_id="PROD-P1")
        elif day == 3:
            self.split_batch("BATCH-HT-B08", num_children=5, day_idx=3, prod_id="PROD-P2")

    def create_lot(self, product_id: str, qty: int = 200, parent_batch: str = None, 
                   day_idx: int = 0, created_ts: datetime = None, shift: str = "CA1",
                   custom_lot_id: str = None) -> dict:
        if custom_lot_id:
            lot_id = custom_lot_id
        else:
            self.lot_counter += 1
            lot_id = f"LOT-{self.lot_counter:04d}"

        line_id = "A" if product_id in ["PROD-P1", "PROD-P2"] else "B"
        if created_ts is None:
            created_ts = self.start_date + timedelta(days=day_idx, hours=8)

        lot_dict = {
            "lot_id": lot_id,
            "product_id": product_id,
            "qty": qty,
            "parent_kind": "BATCH" if parent_batch else "RAW",
            "parent_batch": parent_batch,
            "line_id": line_id,
            "created_day": f"D{day_idx}",
            "created_ts": created_ts.strftime("%Y-%m-%dT%H:%M:%S"),
            "shift": shift,
            "status": "DONE"
        }
        self.lots.append(lot_dict)
        self.consume_materials(lot_dict)
        return lot_dict

    def split_batch(self, batch_id: str, num_children: int = 5, day_idx: int = 1, prod_id: str = "PROD-P1"):
        batch_ts = self.start_date + timedelta(days=day_idx, hours=10)
        start_idx = 401 if "B07" in batch_id else 406
        for i in range(num_children):
            c_id = f"LOT-{start_idx + i:04d}"
            child_lot = self.create_lot(
                product_id=prod_id, qty=200, parent_batch=batch_id,
                day_idx=day_idx, created_ts=batch_ts + timedelta(minutes=i * 5),
                custom_lot_id=c_id
            )
            self.edge_counter += 1
            self.genealogy.append({
                "edge_id": f"EDGE-{self.edge_counter:05d}",
                "parent_lot_id": batch_id,
                "child_lot_id": c_id,
                "edge_type": "SPLIT",
                "qty": 200,
                "true_time": batch_ts.strftime("%Y-%m-%dT%H:%M:%S")
            })
            self.route_lot(child_lot)

        # Merge mẫu R01
        if "B07" in batch_id:
            for p in ["LOT-0403", "LOT-0404"]:
                self.edge_counter += 1
                self.genealogy.append({
                    "edge_id": f"EDGE-{self.edge_counter:05d}",
                    "parent_lot_id": p,
                    "child_lot_id": "LOT-2207",
                    "edge_type": "MERGE",
                    "qty": 200,
                    "true_time": (batch_ts + timedelta(hours=4)).strftime("%Y-%m-%dT%H:%M:%S")
                })

    def consume_materials(self, lot: dict):
        bom_map = {
            "PROD-P1": [("COMP-C1", 400), ("COMP-C3", 200)],
            "PROD-P2": [("COMP-C1", 300), ("COMP-C4", 400)],
            "PROD-P3": [("COMP-C2", 200), ("COMP-C6", 800)],
            "PROD-P4": [("COMP-C2", 400), ("COMP-C4", 200)],
        }
        comps = bom_map.get(lot["product_id"], [("COMP-C1", 200)])
        for comp_id, qty_need in comps:
            mat_lot = f"MAT-{comp_id.replace('COMP-', '')}-0917-01"
            if lot["lot_id"] in ["LOT-0403", "LOT-0404"]:
                mat_lot = "MAT-C3-0917-02"
            self.consumption.append({
                "consumption_id": f"CONS-{len(self.consumption)+1:05d}",
                "lot_id": lot["lot_id"],
                "mat_lot_id": mat_lot,
                "component_id": comp_id,
                "qty_consumed": qty_need,
                "consumption_time": lot["created_ts"]
            })

    def route_lot(self, lot: dict):
        stations = ["STN-INB", "STN-M1", "STN-M2", "STN-HT", "STN-AS1", "STN-T1", "STN-PK", "STN-SHP"] if lot["line_id"] == "A" else ["STN-INB", "STN-M1", "STN-HT", "STN-AS2", "STN-T1", "STN-PK", "STN-SHP"]
        curr_time = datetime.strptime(lot["created_ts"], "%Y-%m-%dT%H:%M:%S")
        for stn in stations:
            dur = 600 if stn in ["STN-HT", "STN-LAB"] else 120
            is_ano = bool(np.random.rand() < 0.04)
            ano_type = np.random.choice(["TEMP_SPIKE", "TOOL_VIBRATION", "FORCE_DROP"]) if is_ano else None
            p_temp = round(float(np.random.normal(178, 3) + (15 if ano_type == "TEMP_SPIKE" else 0)), 1) if stn in ["STN-M2", "STN-HT"] else None
            p_force = round(float(np.random.normal(45, 2)), 1) if stn == "STN-M2" else None
            p_vib = round(float(np.random.normal(3.5, 1)), 1) if stn == "STN-M1" else None

            qty_ng = 2 if is_ano else 0
            qty_out = lot["qty"] - qty_ng

            self.events.append({
                "event_id": f"EVT-{len(self.events)+1:06d}",
                "lot_id": lot["lot_id"],
                "station_id": stn,
                "event_type": "START",
                "start_time": curr_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "end_time": (curr_time + timedelta(seconds=dur)).strftime("%Y-%m-%dT%H:%M:%S"),
                "shift": lot["shift"],
                "param_temp": p_temp,
                "param_force": p_force,
                "param_vibration": p_vib,
                "qty_in": lot["qty"],
                "qty_out": qty_out,
                "qty_ng": qty_ng,
                "is_physical_anomaly": is_ano,
                "anomaly_type": ano_type,
                "fmea_code": "FMEA-M2-001" if is_ano else None
            })
            curr_time += timedelta(seconds=dur + 30)

def run_simulation() -> FactorySim:
    env = simpy.Environment()
    factory = FactorySim(env)
    for day in range(NUM_DAYS):
        factory.run_day(day)
    return factory

if __name__ == "__main__":
    f = run_simulation()
    print(f"\n✓ Đã tạo {len(f.lots)} lots")
    print(f"✓ Đã tạo {len(f.events)} events")
    print(f"✓ Đã tạo {len(f.genealogy)} genealogy edges")
