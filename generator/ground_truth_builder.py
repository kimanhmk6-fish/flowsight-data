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
        special_jts = [
        ("JT-0231", "PROD-P1", "A", 900, "D1",  "2026-09-30T10:00:00", "URGENT", "KHACH_X", "OPEN"),
        ("JT-0235", "PROD-P2", "A", 600, "D10", "2026-10-09T10:00:00", "NORMAL", "KHACH_Y", "OPEN"),
        ]
        for jt_id, p_id, line, qty, due_day, due_ts, prio, cust, status in special_jts:
            rows.append({
                "jt_id": jt_id, "product_id": p_id, "line_id": line,
                "qty": qty, "due_day": due_day, "due_ts": due_ts,
                "priority": prio, "customer": cust, "status": status
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
        ("INC-0016", "STN-AS2", "2026-10-06T14:00:00", "2026-10-06T14:15:00", 0.25, "FMEA-AS2-001", 30,  "LOW",      "HUMAN",        "LOT-0240", "R04"),
        ("INC-0017", "STN-HT", "2026-09-30T10:00:00", "2026-09-30T10:30:00", 0.5, "FMEA-DATA-001", 42, "MEDIUM", "DATA_QUALITY", "LOT-0403,LOT-0404", "R05"),
        ("INC-0018", "STN-AS2", "2026-10-07T10:00:00", "2026-10-07T10:30:00", 0.5,  "FMEA-COMB-001", 48, "MEDIUM",   "COMBINED",     "LOT-0232", "R06"),
        ("INC-0019", "STN-LAB", "2026-10-08T14:00:00", "2026-10-08T14:30:00", 0.5,  "FMEA-UNKNOWN", 0,   "UNKNOWN",  "UNKNOWN",      "LOT-0300", "R07"),
        ("INC-0020", "STN-SHP", "2026-10-10T10:00:00", "2026-10-10T10:30:00", 0.5,  "FMEA-SUP-002", 108, "CRITICAL", "MATERIAL",     "LOT-0235", "R08"),

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
    
    ###Sinh đủ 24 test case JSON, chỉ dùng lot/JT hợp lệ với ground truth hiện có:
    ###LOT: chỉ LOT-0001..LOT-0410
    ###JT-0231/JT-0235: giữ (đã có trong shipment + allocation — special case F01)
    ###R04-R08: map lot ảo cũ (1050/1060/1070/1080) → lot thật cùng ngữ cảnh
    
    impact_cases = {
        "F01": {
            "jt_late": ["JT-0231"], "shortfall_qty": 100, "P_late": 0.995,
            "affected_lots": ["LOT-0147", "LOT-0148"],
            "fmea_code": "FMEA-M2-001", "rpn": 96,
            "recommended_action": "resequencing + OT2",
            "station_id": "STN-M2", "duration_h": 8.0,
        },
        "F02": {
            "jt_late": ["JT-0231"], "shortfall_qty": 50, "P_late": 0.92,
            "affected_lots": ["LOT-0147"],
            "fmea_code": "FMEA-M2-001", "rpn": 64,
            "recommended_action": "monitor + buffer",
            "station_id": "STN-M2", "duration_h": 4.0,
        },
        "F03": {
            "jt_late": ["JT-0231", "JT-0235"], "shortfall_qty": 200, "P_late": 0.998,
            "affected_lots": ["LOT-0231", "LOT-0235"],
            "fmea_code": "FMEA-M2-001", "rpn": 128,
            "recommended_action": "expedite + OT3",
            "station_id": "STN-M2", "duration_h": 12.0,
        },
        "F04": {
            "jt_late": [], "shortfall_qty": 0, "P_late": 0.15,
            "affected_lots": [],
            "fmea_code": "FMEA-M1-002", "rpn": 54,
            "recommended_action": "routine maintenance",
            "station_id": "STN-M1", "duration_h": 8.0,
        },
        "F05": {
            "jt_late": ["JT-0235"], "shortfall_qty": 150, "P_late": 0.97,
            "affected_lots": ["LOT-0401", "LOT-0402", "LOT-0403", "LOT-0404", "LOT-0405"],
            "fmea_code": "FMEA-HT-001", "rpn": 135,
            "recommended_action": "quarantine batch + review furnace",
            "station_id": "STN-HT", "duration_h": 8.0,
        },
        "F06": {
            "jt_late": [], "shortfall_qty": 0, "P_late": 0.20,
            "affected_lots": ["LOT-0240"],
            "fmea_code": "FMEA-AS2-001", "rpn": 30,
            "recommended_action": "retrain operator",
            "station_id": "STN-AS2", "duration_h": 8.0,
        },
        "F07": {
            "jt_late": [], "shortfall_qty": 0, "P_late": 0.10,
            "affected_lots": [],
            "fmea_code": "FMEA-T1-001", "rpn": 42,
            "recommended_action": "stabilize power supply",
            "station_id": "STN-T1", "duration_h": 8.0,
        },
        "F08": {
            "jt_late": ["JT-0231"], "shortfall_qty": 80, "P_late": 0.88,
            "affected_lots": ["LOT-0232"],
            "fmea_code": "FMEA-M2-001", "rpn": 96,
            "recommended_action": "loadcell calibration",
            "station_id": "STN-M2", "duration_h": 8.0,
        },
        "F09": {
            "jt_late": ["JT-0231"], "shortfall_qty": 180, "P_late": 0.96,
            "affected_lots": ["LOT-0231", "LOT-0232"],
            "fmea_code": "FMEA-M2-001", "rpn": 96,
            "recommended_action": "combined resequencing",
            "station_id": "STN-M2", "duration_h": 8.0,
        },
        "F10": {
            "jt_late": ["JT-0231"], "shortfall_qty": 120, "P_late": 0.94,
            "affected_lots": ["LOT-0231"],
            "fmea_code": "FMEA-M2-001", "rpn": 96,
            "recommended_action": "tool replacement",
            "station_id": "STN-M2", "duration_h": 8.0,
        },
        "F11": {
            "jt_late": ["JT-0231"], "shortfall_qty": 60, "P_late": 0.75,
            "affected_lots": ["LOT-0231"],
            "fmea_code": "FMEA-COMB-001", "rpn": 48,
            "recommended_action": "multivariate analysis",
            "station_id": "STN-M2", "duration_h": 4.0,
        },
        "F12": {
            "jt_late": ["JT-0231", "JT-0235"], "shortfall_qty": 220, "P_late": 0.99,
            "affected_lots": ["LOT-0231", "LOT-0235"],
            "fmea_code": "FMEA-M2-001", "rpn": 96,
            "recommended_action": "emergency maintenance + OT4",
            "station_id": "STN-M2", "duration_h": 8.0,
        },
    }

    cause_cases = {
        "R01": {
            "top_cause": "MAT-C3-0917-02", "cause_type": "MATERIAL",
            "fmea_code": "FMEA-SUP-001", "rpn": 96, "confidence": 0.92,
            "isolate_lots": ["LOT-0403", "LOT-0404"],
            "evidence_chain": ["PK-2207", "STN-AS2", "LOT-0403", "BATCH-HT-B07", "MAT-C3-0917-02"],
        },
        "R02": {
            "top_cause": "STN-M1", "cause_type": "MACHINE",
            "fmea_code": "FMEA-M1-001", "rpn": 54, "confidence": 0.78,
            "isolate_lots": [],
            "evidence_chain": ["STN-M1", "Cpk_drift"],
        },
        "R03": {
            "top_cause": "STN-HT", "cause_type": "PROCESS",
            "fmea_code": "FMEA-HT-001", "rpn": 135, "confidence": 0.95,
            "isolate_lots": ["LOT-0401", "LOT-0402", "LOT-0403", "LOT-0404", "LOT-0405"],
            "evidence_chain": ["STN-LAB", "BATCH-HT-B07", "STN-HT", "temp_deviation"],
        },
        "R04": {
            "top_cause": "STN-AS2", "cause_type": "HUMAN",
            "fmea_code": "FMEA-AS2-001", "rpn": 30, "confidence": 0.65,
            "isolate_lots": ["LOT-0240"],
            "evidence_chain": ["STN-AS2", "shift_change", "LOT-0240"],
        },
        "R05": {
            "top_cause": "LABEL_DUPLICATION", "cause_type": "DATA_QUALITY",
            "fmea_code": "FMEA-DATA-001", "rpn": 42, "confidence": 0.88,
            "isolate_lots": ["LOT-0403", "LOT-0404"],
            "evidence_chain": ["SRC-03", "duplicate_qr", "LOT-0403", "LOT-0404"],
        },
        "R06": {
            "top_cause": "COMBINED", "cause_type": "COMBINED",
            "fmea_code": "FMEA-COMB-001", "rpn": 48, "confidence": 0.72,
            "isolate_lots": ["LOT-0232"],
            "evidence_chain": ["STN-AS2", "STN-M2", "LOT-0232"],
        },
        "R07": {
            "top_cause": "UNKNOWN", "cause_type": "UNKNOWN",
            "fmea_code": "FMEA-UNKNOWN", "rpn": 0, "confidence": 0.30,
            "isolate_lots": ["LOT-0300"],
            "evidence_chain": ["STN-LAB", "LOT-0300"],
        },
        "R08": {
            "top_cause": "SUPPLIER_MAT", "cause_type": "MATERIAL",
            "fmea_code": "FMEA-SUP-002", "rpn": 108, "confidence": 0.93,
            "isolate_lots": ["LOT-0235"],
            "evidence_chain": ["SHP-1010-1", "JT-0235", "LOT-0235", "customer_feedback"],
            "shipment_id": "SHP-1010-1",
            "detected_after_delivery": True,
        },
    }

    data_health_cases = {
        "D01": {
            "description": "Clock offset & drift detection",
            "detected_offset_min": -4.0,
            "tolerance_sec": 15,
            "affected_stations": ["STN-M2", "STN-AS2"],
            "drift_per_day_sec": {"STN-M2": 2.0, "STN-AS2": -1.5},
        },
        "D02": {
            "description": "Missing scan restoration",
            "missing_scans_detected": 100,
            "entity_restoration_rate": 0.95,
            "affected_stations": ["STN-HT", "STN-AS1", "STN-AS2", "STN-T1"],
            "critical_lots_with_gaps": ["LOT-0147", "LOT-0148", "LOT-0403", "LOT-0404"],
        },
        "D03": {
            "description": "Duplicate lot label detection",
            "duplicates_detected": 4,
            "duplicate_rate": 0.01,
            "affected_lots": ["LOT-0403", "LOT-0404"],
        },
        "D04": {
            "description": "Schema drift detection in Excel",
            "schema_drift_detected": True,
            "drift_day": 9,
            "sheet_name": "Day_9",
            "mapped_columns": {
                "Mã lô": "lot_id",
                "Giá trị": "value",
                "Đặc tính": "characteristic",
                "Ngày đo": "measured_date",
                "Mã trạm": "station_id",
                "Người kiểm tra": "inspector",
            },
        },
    }

    for case_id, expected in impact_cases.items():
        payload = {"case_id": case_id, "case_group": "FORWARD", "expected_result": expected}
        with open(Path(GT_DIR) / f"impact_truth_{case_id}.json", "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

    for case_id, expected in cause_cases.items():
        payload = {"case_id": case_id, "case_group": "BACKWARD", "expected_result": expected}
        with open(Path(GT_DIR) / f"cause_truth_{case_id}.json", "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

    for case_id, expected in data_health_cases.items():
        payload = {"case_id": case_id, "case_group": "DATA", "expected_result": expected}
        with open(Path(GT_DIR) / f"data_health_truth_{case_id}.json", "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

    old = Path(GT_DIR) / "data_health_truth.json"
    if old.exists():
        old.unlink()

    print("  ✓ Đã sinh 24 test case JSON: 12 F + 8 R + 4 D")


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
