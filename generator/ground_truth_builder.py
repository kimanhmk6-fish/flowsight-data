import pandas as pd
import json
from pathlib import Path
from datetime import datetime, timedelta
from config.constants import GT_DIR, START_DATE_STR

Path(GT_DIR).mkdir(parents=True, exist_ok=True)

def build_canonical_lots(factory) -> pd.DataFrame:
    df = pd.DataFrame(factory.lots)
    df.to_csv(Path(GT_DIR) / "canonical_lots.csv", index=False)
    return df

def build_genealogy_truth(factory) -> pd.DataFrame:
    df = pd.DataFrame(factory.genealogy)
    df.to_csv(Path(GT_DIR) / "genealogy_truth.csv", index=False)
    return df

def build_production_truth(factory) -> pd.DataFrame:
    df = pd.DataFrame(factory.events)
    df.to_csv(Path(GT_DIR) / "production_truth.csv", index=False)
    return df

def build_material_consumption(factory) -> pd.DataFrame:
    df = pd.DataFrame(factory.consumption)
    df.to_csv(Path(GT_DIR) / "material_consumption_truth.csv", index=False)
    return df

def build_material_lots() -> pd.DataFrame:
    mats = [
        ("MAT-C1-0917-01", "COMP-C1", "NCC-X", 5000, "D0", "2026-09-29T07:00:00"),
        ("MAT-C3-0917-02", "COMP-C3", "NCC-X", 5000, "D0", "2026-09-29T07:00:00"),
        ("MAT-C4-0917-01", "COMP-C4", "NCC-Y", 3000, "D0", "2026-09-29T07:00:00")
    ]
    df = pd.DataFrame(mats, columns=["mat_lot_id", "component_id", "supplier_code", "qty_received", "received_day", "received_ts"])
    df.to_csv(Path(GT_DIR) / "material_lot_truth.csv", index=False)
    return df

def build_qc_truth(factory) -> pd.DataFrame:
    qc = []
    idx = 1
    for lot in factory.lots:
        t_base = datetime.strptime(lot["created_ts"], "%Y-%m-%dT%H:%M:%S") + timedelta(hours=3)
        res = "NG" if lot["lot_id"] in ["LOT-0403", "LOT-0404"] else "OK"
        rule = "NELSON_1" if res == "NG" else "IN_CONTROL"
        trend = "DECLINING" if res == "NG" else "STABLE"
        qc.append({
            "qc_id": f"QC-{idx:05d}", "lot_id": lot["lot_id"], "station_id": "STN-T1",
            "test_type": "AUTO", "characteristic": "Đường kính trục",
            "value": 12.61 if res == "NG" else 12.47, "lsl": 12.30, "usl": 12.60,
            "result": res, "ng_code": "NG-01" if res == "NG" else "",
            "measured_time": t_base.strftime("%Y-%m-%dT%H:%M:%S"),
            "spc_nelson_rule": rule, "cpk_trend": trend,
            "dn7_flag": "OUT_OF_SPEC" if res == "NG" else "NORMAL"
        })
        idx += 1
        qc.append({
            "qc_id": f"QC-{idx:05d}", "lot_id": lot["lot_id"], "station_id": "STN-LAB",
            "test_type": "SAMPLE", "characteristic": "Lực ép",
            "value": 187.9, "lsl": 170.0, "usl": 230.0, "result": "OK", "ng_code": "",
            "measured_time": (t_base + timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%S"),
            "spc_nelson_rule": "IN_CONTROL", "cpk_trend": "STABLE", "dn7_flag": "NORMAL"
        })
        idx += 1
    df = pd.DataFrame(qc)
    df.to_csv(Path(GT_DIR) / "qc_truth.csv", index=False)
    return df

def build_qc_capability() -> pd.DataFrame:
    rows = []
    start_d = datetime.strptime(START_DATE_STR, "%Y-%m-%d")
    for d in range(14):
        cpk = max(0.68, 1.48 - (d * 0.08))
        rows.append({
            "cap_id": f"CAP-{d+1:05d}", "station_id": "STN-M1", "characteristic": "Đường kính trục",
            "cap_date": (start_d + timedelta(days=d)).strftime("%Y-%m-%d"), "n_sample": 30,
            "mean": 12.46, "std_dev": 0.031, "cp": 1.50, "cpk": round(cpk, 2),
            "trend_signal": "DECLINING" if d > 5 else "STABLE", "dn7_alert": "WARNING" if d > 5 else "NORMAL"
        })
    df = pd.DataFrame(rows)
    df.to_csv(Path(GT_DIR) / "qc_capability_truth.csv", index=False)
    return df

def build_jt_orders() -> pd.DataFrame:
    rows = []
    start_d = datetime.strptime(START_DATE_STR, "%Y-%m-%d")
    for i in range(1, 46):
        qty = 1300 if i == 1 else (600 if i % 2 == 0 else 900)
        p_id = f"PROD-P{((i-1)%4)+1}"
        d_day = min(13, (i // 3) + 1)
        rows.append({
            "jt_id": f"JT-{i:04d}", "product_id": p_id,
            "line_id": "A" if p_id in ["PROD-P1", "PROD-P2"] else "B",
            "qty": qty, "due_day": f"D{d_day}",
            "due_ts": (start_d + timedelta(days=d_day, hours=10)).strftime("%Y-%m-%dT%H:%M:%S"),
            "priority": "URGENT" if i == 12 else "NORMAL", "customer": "KHACH_X", "status": "OPEN"
        })
    df = pd.DataFrame(rows)
    df.to_csv(Path(GT_DIR) / "jt_order_truth.csv", index=False)
    return df

def build_jt_allocation(factory) -> pd.DataFrame:
    allocs = []
    start_d = datetime.strptime(START_DATE_STR, "%Y-%m-%d")
    allocs.append({"allocation_id": "ALLOC-00001", "jt_id": "JT-0001", "lot_id": "LOT-0001", "qty_allocated": 200, "allocation_time": "2026-09-29T09:00:00"})
    allocs.append({"allocation_id": "ALLOC-00050", "jt_id": "JT-0231", "lot_id": "LOT-0147", "qty_allocated": 200, "allocation_time": "2026-10-01T09:00:00"})
    allocs.append({"allocation_id": "ALLOC-00051", "jt_id": "JT-0231", "lot_id": "LOT-0148", "qty_allocated": 200, "allocation_time": "2026-10-01T09:00:00"})
    df = pd.DataFrame(allocs)
    df.to_csv(Path(GT_DIR) / "jt_allocation_truth.csv", index=False)
    return df

def build_inventory_truth() -> pd.DataFrame:
    rows = []
    start_d = datetime.strptime(START_DATE_STR, "%Y-%m-%d")
    idx = 1
    for day in range(14):
        for s_idx, (shift, h) in enumerate([("CA1", 6), ("CA2", 18)]):
            snap_time = start_d + timedelta(days=day, hours=h)
            for p in range(1, 5):
                rows.append({
                    "snapshot_id": f"INV-{idx:05d}", "snapshot_time": snap_time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "item_type": "FG", "item_id": f"PROD-P{p}",
                    "location": "Kho FG - Line A" if p <= 2 else "Kho FG - Line B",
                    "qty": 450, "capture_method": "AUTO" if s_idx == 0 else "MANUAL"
                })
                idx += 1
            rows.append({
                "snapshot_id": f"INV-{idx:05d}", "snapshot_time": snap_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "item_type": "COMPONENT", "item_id": "COMP-C3", "location": "Kho NVL",
                "qty": 600 if day == 0 and s_idx == 0 else 3000, "capture_method": "AUTO" if s_idx == 0 else "MANUAL"
            })
            idx += 1
    df = pd.DataFrame(rows)
    df.to_csv(Path(GT_DIR) / "inventory_truth.csv", index=False)
    return df

def build_shipment_truth() -> pd.DataFrame:
    ships = [
        ("SHP-1001-1", "2026-10-01T10:00:00", "2026-10-01T09:00:00", "JT-0001", 600, 600, "DEPARTED", ""),
        ("SHP-1002-1", "2026-10-02T10:00:00", "2026-10-02T09:00:00", "JT-0231", 1300, 1200, "PARTIAL", "FMEA-M2-001"),
        ("SHP-1010-1", "2026-10-10T10:00:00", "2026-10-10T09:00:00", "JT-0235", 600, 600, "DEPARTED", "")
    ]
    df = pd.DataFrame(ships, columns=["shipment_id", "truck_time", "cutoff_time", "jt_id", "qty_planned", "qty_actual", "status", "fmea_related_incident"])
    df.to_csv(Path(GT_DIR) / "shipment_truth.csv", index=False)
    return df

def build_incident_truth() -> pd.DataFrame:
    incidents = [
        ("INC-0001", "STN-M2", "2026-09-29T08:00:00", "2026-09-29T16:00:00", 8.0, "FMEA-M2-001", 96, "HIGH", "MACHINE", "LOT-0147,LOT-0148", "F01"),
        ("INC-0002", "STN-M2", "2026-09-30T08:00:00", "2026-09-30T12:00:00", 4.0, "FMEA-M2-001", 64, "MEDIUM", "MACHINE", "LOT-0147", "F02"),
        ("INC-0003", "STN-M2", "2026-10-01T08:00:00", "2026-10-01T20:00:00", 12.0, "FMEA-M2-001", 128, "CRITICAL", "MACHINE", "LOT-0231,LOT-0235", "F03"),
        ("INC-0004", "STN-M1", "2026-10-02T08:00:00", "2026-10-02T16:00:00", 8.0, "FMEA-M1-002", 54, "MEDIUM", "MACHINE", "", "F04"),
        ("INC-0005", "STN-HT", "2026-10-03T08:00:00", "2026-10-03T16:00:00", 8.0, "FMEA-HT-001", 135, "CRITICAL", "PROCESS", "LOT-0401,LOT-0402,LOT-0403,LOT-0404,LOT-0405", "F05"),
        ("INC-0006", "STN-AS2", "2026-10-04T08:00:00", "2026-10-04T16:00:00", 8.0, "FMEA-AS2-001", 30, "LOW", "HUMAN", "LOT-0240", "F06"),
        ("INC-0007", "STN-T1", "2026-10-05T08:00:00", "2026-10-05T16:00:00", 8.0, "FMEA-T1-001", 42, "MEDIUM", "MACHINE", "", "F07"),
        ("INC-0008", "STN-M2", "2026-10-05T16:00:00", "2026-10-06T00:00:00", 8.0, "FMEA-M2-001", 96, "HIGH", "MACHINE", "LOT-0232", "F08"),
        ("INC-0009", "STN-M2", "2026-10-06T08:00:00", "2026-10-06T16:00:00", 8.0, "FMEA-M2-001", 96, "HIGH", "MACHINE", "LOT-0231,LOT-0232", "F09"),
        ("INC-0010", "STN-M2", "2026-10-07T08:00:00", "2026-10-07T16:00:00", 8.0, "FMEA-M2-001", 96, "HIGH", "MACHINE", "LOT-0231", "F10"),
        ("INC-0011", "STN-M2", "2026-10-08T08:00:00", "2026-10-08T12:00:00", 4.0, "FMEA-COMB-001", 48, "MEDIUM", "COMBINED", "LOT-0231", "F11"),
        ("INC-0012", "STN-M2", "2026-10-09T08:00:00", "2026-10-09T16:00:00", 8.0, "FMEA-M2-001", 96, "HIGH", "MACHINE", "LOT-0231,LOT-0235", "F12"),
        ("INC-0013", "STN-AS2", "2026-09-30T16:00:00", "2026-09-30T16:30:00", 0.5, "FMEA-SUP-001", 96, "HIGH", "MATERIAL", "LOT-0403,LOT-0404", "R01"),
        ("INC-0014", "STN-M1", "2026-10-06T14:00:00", "2026-10-06T14:30:00", 0.5, "FMEA-M1-001", 54, "MEDIUM", "MACHINE", "", "R02"),
        ("INC-0015", "STN-HT", "2026-09-30T18:00:00", "2026-09-30T18:30:00", 0.5, "FMEA-HT-001", 135, "CRITICAL", "PROCESS", "LOT-0401,LOT-0402,LOT-0403,LOT-0404,LOT-0405", "R03"),
        ("INC-0016", "STN-AS2", "2026-10-06T14:00:00", "2026-10-06T14:15:00", 0.25, "FMEA-AS2-001", 30, "LOW", "HUMAN", "LOT-1050", "R04"),
        ("INC-0017", "STN-HT", "2026-09-30T10:00:00", "2026-09-30T10:30:00", 0.5, "FMEA-DATA-001", 42, "MEDIUM", "DATA_QUALITY", "LOT-0403,LOT-0404", "R05"),
        ("INC-0018", "STN-AS2", "2026-10-07T10:00:00", "2026-10-07T10:30:00", 0.5, "FMEA-COMB-001", 48, "MEDIUM", "COMBINED", "LOT-1060", "R06"),
        ("INC-0019", "STN-LAB", "2026-10-08T14:00:00", "2026-10-08T14:30:00", 0.5, "FMEA-UNKNOWN", 0, "UNKNOWN", "UNKNOWN", "LOT-1070", "R07"),
        ("INC-0020", "STN-SHP", "2026-10-10T10:00:00", "2026-10-10T10:30:00", 0.5, "FMEA-SUP-002", 108, "CRITICAL", "MATERIAL", "LOT-1080", "R08")
    ]
    cols = ["incident_id", "station_id", "start_time", "end_time", "duration_h", "fmea_code", "rpn", "severity_level", "root_cause_type", "affected_lots", "test_case_link"]
    df = pd.DataFrame(incidents, columns=cols)
    df.to_csv(Path(GT_DIR) / "incident_truth.csv", index=False)
    return df

def build_entity_mapping(factory) -> pd.DataFrame:
    rows = []
    for lot in factory.lots:
        cid = lot["lot_id"]
        suf = cid.replace("LOT-", "")
        line = lot["line_id"]
        rows.append({"canonical_type": "LOT", "canonical_id": cid, "source_system": "SRC-01", "source_id": f"A{suf}", "source_context": "output_perf.csv"})
        rows.append({"canonical_type": "LOT", "canonical_id": cid, "source_system": "SRC-02", "source_id": f"L-{line}-{suf}", "source_context": "ipc.csv"})
        rows.append({"canonical_type": "LOT", "canonical_id": cid, "source_system": "SRC-03", "source_id": f"QR260929A{suf}", "source_context": "lot_scans.csv"})
        rows.append({"canonical_type": "LOT", "canonical_id": cid, "source_system": "SRC-04", "source_id": f"{cid}-{line}", "source_context": "qc_auto.csv"})
    df = pd.DataFrame(rows)
    df.to_csv(Path(GT_DIR) / "entity_mapping_truth.csv", index=False)
    return df

def build_24_test_case_answers():
    f01 = {
        "case_id": "F01",
        "expected_result": {
            "jt_late": ["JT-0231"],
            "shortfall_qty": 100,
            "P_late": 0.995,
            "affected_lots": ["LOT-0147", "LOT-0148"],
            "fmea_code": "FMEA-M2-001",
            "rpn": 96,
            "recommended_action": "resequencing + OT2"
        }
    }
    with open(Path(GT_DIR) / "impact_truth_F01.json", "w", encoding="utf-8") as f:
        json.dump(f01, f, indent=2)

    r01 = {
        "case_id": "R01",
        "expected_result": {
            "top_cause": "MAT-C3-0917-02",
            "cause_type": "MATERIAL",
            "fmea_code": "FMEA-SUP-001",
            "rpn": 96,
            "confidence": 0.92,
            "isolate_lots": ["LOT-0403", "LOT-0404"]
        }
    }
    with open(Path(GT_DIR) / "cause_truth_R01.json", "w", encoding="utf-8") as f:
        json.dump(r01, f, indent=2)

    dh = {
        "D01": {"detected_offset_min": -4.0, "tolerance_sec": 15},
        "D02": {"missing_scans_detected": 100, "entity_restoration_rate": 0.95},
        "D03": {"duplicates_detected": 4, "duplicate_rate": 0.01},
        "D04": {"schema_drift_detected": True, "mapped_columns": {"Mã lô": "lot_id", "Giá trị": "value"}}
    }
    with open(Path(GT_DIR) / "data_health_truth.json", "w", encoding="utf-8") as f:
        json.dump(dh, f, indent=2)

def main(factory):
    print("=" * 60)
    print("XUẤT TOÀN BỘ GROUND TRUTH (BÍ MẬT QUỐC GIA)")
    print("=" * 60)
    build_canonical_lots(factory)
    build_genealogy_truth(factory)
    build_material_lots()
    build_material_consumption(factory)
    build_production_truth(factory)
    build_qc_truth(factory)
    build_qc_capability()
    build_jt_orders()
    build_jt_allocation(factory)
    build_inventory_truth()
    build_shipment_truth()
    build_incident_truth()
    build_entity_mapping(factory)
    build_24_test_case_answers()
    print("✓ Ground Truth exported successfully.")

if __name__ == "__main__":
    from generator.factory_sim import run_simulation
    factory = run_simulation()
    main(factory)
