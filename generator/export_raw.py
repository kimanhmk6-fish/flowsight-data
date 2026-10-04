import pandas as pd
from pathlib import Path
from datetime import datetime
from config.constants import GT_DIR, RAW_DIR
from generator.error_injector import ErrorInjector

injector = ErrorInjector()

def to_alias(canonical_id: str, src: str, line_id: str = "A", created_day: str = "D0") -> str:
    """
    Quy tắc sinh Alias chuẩn DENSO:
    SRC_01: A0147 (Lấy chữ 'A' + 4 số cuối)
    SRC_02: L_A_0147 (L_ + line + _ + 4 số cuối)
    SRC_03: QR260929A0147 (QR + YYMMDD + Line + 4 số cuối)
    SRC_04/05: LOT-0147-A (<canonical_id>-<line>)
    SRC_07: ITEM_P1_0147
    """
    if not isinstance(canonical_id, str):
        return ""
    cid = canonical_id.strip()
    suf = cid.replace("LOT-", "").zfill(4)
    line = str(line_id).strip() if line_id else "A"
    
    # Tính ngày tạo để gắn vào QR code
    try:
        d_idx = int(str(created_day).replace("D", ""))
    except Exception:
        d_idx = 0
    date_dt = pd.to_datetime("2026-09-29") + pd.Timedelta(days=d_idx)
    date_str = date_dt.strftime("%y%m%d")

    if src == "SRC_01":
        return f"A{suf}"
    elif src == "SRC_02":
        return f"L_{line}_{suf}"
    elif src == "SRC_03":
        return f"QR{date_str}{line}{suf}"
    elif src in ["SRC_04", "SRC_05"]:
        return f"{cid}-{line}"
    elif src == "SRC_07":
        return f"ITEM_P1_{suf}"
    return cid

def export_all():
    print("=" * 60)
    print("XUẤT 9 NGUỒN DỮ LIỆU RAW (CHUẨN HÓA ENCODING & DELIMITER)")
    print("=" * 60)

    # Đọc dữ liệu sự thật khách quan từ Người 1
    df_lots = pd.read_csv(Path(GT_DIR) / "canonical_lots.csv")
    df_prod = pd.read_csv(Path(GT_DIR) / "production_truth.csv")
    lot_meta = df_lots.set_index("lot_id").to_dict(orient="index")

    # 1. SRC-01: Production Output (Bắt buộc UTF-8 BOM, dấu phẩy)
    print("\n[RAW] Xuất SRC-01 Production Output...")
    df_end = df_prod[df_prod["station_id"] == "STN-PK"].copy()
    src01_rows = []
    for idx, r in df_end.iterrows():
        meta = lot_meta.get(r["lot_id"], {"line_id": "A", "created_day": "D0"})
        dt = pd.to_datetime(r["end_time"])
        src01_rows.append({
            "record_id": f"REC_{len(src01_rows)+1:06d}",
            "local_lot_label": to_alias(r["lot_id"], "SRC_01", meta["line_id"], meta["created_day"]),
            "model_code": "P1",
            "line_code": meta["line_id"],
            "qty_ok": r["qty_out"],
            "qty_ng": r["qty_ng"],
            "actual_rate_per_h": round(float(r["qty_out"]) / 0.5, 2),
            "event_ts": dt.strftime("%d/%m/%Y %H:%M"),
            "ts_format": "DD/MM/YYYY HH:MM"
        })
    df_src01 = pd.DataFrame(src01_rows)
    out_path_01 = Path(RAW_DIR) / "SRC-01_output" / "output_perf_LineA_20260929.csv"
    df_src01.to_csv(out_path_01, index=False, encoding="utf-8-sig")
    print(f"  ✓ Đã ghi: {out_path_01.name} ({len(df_src01)} dòng, encoding=utf-8-sig)")

    # 2. SRC-02: IPC Log (Bắt buộc UTF-8 no BOM, ISO8601, có D01 Clock Offset)
    print("\n[RAW] Xuất SRC-02 IPC Log...")
    src02_rows = []
    for idx, r in df_prod.iterrows():
        meta = lot_meta.get(r["lot_id"], {"line_id": "A", "created_day": "D0"})
        stn_code = r["station_id"].replace("STN-", "")
        src02_rows.append({
            "ipc_event_id": f"IPC_{stn_code}_{len(src02_rows)+1:06d}",
            "machine_code": stn_code,
            "local_lot_ref": to_alias(r["lot_id"], "SRC_02", meta["line_id"], meta["created_day"]),
            "event_type": r["event_type"],
            "event_code": r["fmea_code"] if pd.notna(r["fmea_code"]) else "",
            "param_temp": r["param_temp"],
            "param_force": r["param_force"],
            "param_vibration": r["param_vibration"],
            "ts_raw": r["start_time"],
            "ts_format": "ISO8601",
            "export_ts": r["end_time"]
        })
    df_src02 = pd.DataFrame(src02_rows)
    df_src02 = injector.apply_clock_offset(df_src02, station_col="machine_code", ts_col="ts_raw")
    out_path_02 = Path(RAW_DIR) / "SRC-02_ipc" / "ipc_M2_20260929.csv"
    df_src02.to_csv(out_path_02, index=False, encoding="utf-8")
    print(f"  ✓ Đã ghi: {out_path_02.name} ({len(df_src02)} dòng, D01 Offset applied)")

    # 3. SRC-03: QR Scan (CSV UTF-8, có D02 Missing Scan + D03 Duplicate)
    print("\n[RAW] Xuất SRC-03 QR Scan...")
    src03_rows = []
    for idx, r in df_prod.iterrows():
        meta = lot_meta.get(r["lot_id"], {"line_id": "A", "created_day": "D0"})
        stn_code = r["station_id"].replace("STN-", "")
        dt = pd.to_datetime(r["start_time"])
        src03_rows.append({
            "scan_id": f"SCAN_{len(src03_rows)+1:06d}",
            "qr_code": to_alias(r["lot_id"], "SRC_03", meta["line_id"], meta["created_day"]),
            "parent_qr_code": "QR260930B07" if "0401" <= r["lot_id"].replace("LOT-","") <= "0405" else "",
            "scan_type": "MOVE" if stn_code != "INB" else "RECEIVE",
            "station_code": stn_code,
            "scan_ts_raw": dt.strftime("%Y-%m-%d %H:%M:%S"),
            "ts_format": "YYYY-MM-DD HH:MM:SS",
            "operator_code": "OP_001"
        })
    df_src03 = pd.DataFrame(src03_rows)
    df_src03 = injector.remove_missing_scans(df_src03)
    df_src03 = injector.inject_duplicate_lot(df_src03)
    out_path_03 = Path(RAW_DIR) / "SRC-03_qr" / "lot_scans.csv"
    df_src03.to_csv(out_path_03, index=False, encoding="utf-8")
    print(f"  ✓ Đã ghi: {out_path_03.name} ({len(df_src03)} dòng, D02 & D03 applied)")

    # 4. SRC-04: QC Auto (CSV UTF-8, có D05 Decimal Comma)
    print("\n[RAW] Xuất SRC-04 QC Auto...")
    df_qc = pd.read_csv(Path(GT_DIR) / "qc_truth.csv")
    df_qc_auto = df_qc[df_qc["test_type"] == "AUTO"].copy()
    src04_rows = []
    for idx, r in df_qc_auto.iterrows():
        meta = lot_meta.get(r["lot_id"], {"line_id": "A", "created_day": "D0"})
        dt = pd.to_datetime(r["measured_time"])
        src04_rows.append({
            "qc_record_id": f"QC_AUTO_{len(src04_rows)+1:06d}",
            "local_lot_ref": to_alias(r["lot_id"], "SRC_04", meta["line_id"], meta["created_day"]),
            "model_code": "P1",
            "station_code": "T1",
            "characteristic": r["characteristic"],
            "value_raw": str(r["value"]),
            "lsl": str(r["lsl"]),
            "usl": str(r["usl"]),
            "result": r["result"],
            "ng_code": r["ng_code"] if pd.notna(r["ng_code"]) else "",
            "measured_ts_raw": dt.strftime("%d/%m/%Y %H:%M:%S"),
            "ts_format": "DD/MM/YYYY HH:MM:SS"
        })
    df_src04 = pd.DataFrame(src04_rows)
    df_src04 = injector.apply_decimal_comma(df_src04)
    out_path_04 = Path(RAW_DIR) / "SRC-04_qc_auto" / "qc_autotest_LineA_20260929.csv"
    df_src04.to_csv(out_path_04, index=False, encoding="utf-8")
    print(f"  ✓ Đã ghi: {out_path_04.name} ({len(df_src04)} dòng, D05 Decimal comma applied)")

    # 5. SRC-05: QC Sampling (Excel Multi-sheet, có D04 Schema Drift)
    print("\n[RAW] Xuất SRC-05 QC Sampling Excel...")
    df_qc_sample = df_qc[df_qc["test_type"] == "SAMPLE"].copy()
    excel_path_05 = Path(RAW_DIR) / "SRC-05_qc_sampling" / "qc_sampling_W39.xlsx"
    src05_rows = []
    for idx, r in df_qc_sample.iterrows():
        meta = lot_meta.get(r["lot_id"], {"line_id": "A", "created_day": "D0"})
        dt = pd.to_datetime(r["measured_time"])
        src05_rows.append({
            "local_lot_ref": to_alias(r["lot_id"], "SRC_05", meta["line_id"], meta["created_day"]),
            "characteristic": r["characteristic"],
            "value_raw": str(r["value"]),
            "measured_date": dt.strftime("%d/%m/%Y %H:%M"),
            "station_code": "LAB",
            "inspector": "INS_001",
            "ts_format": "DD/MM/YYYY HH:MM"
        })
    df_src05 = pd.DataFrame(src05_rows)
    with pd.ExcelWriter(excel_path_05, engine="openpyxl") as writer:
        df_src05.to_excel(writer, sheet_name="Data", index=False)
        # Sheet drift ngày thứ 9
        df_drift = injector.apply_schema_drift_day9(df_src05.copy())
        df_drift.to_excel(writer, sheet_name="Day_9", index=False)
    print(f"  ✓ Đã ghi: {excel_path_05.name} (Multi-sheet: Data & Day_9 Schema Drift)")

    # 6. SRC-06: Planning / JT Orders (Bắt buộc Delimiter ';')
    print("\n[RAW] Xuất SRC-06 Planning JT Orders...")
    df_jt = pd.read_csv(Path(GT_DIR) / "jt_order_truth.csv")
    src06_rows = []
    for idx, r in df_jt.iterrows():
        dt = pd.to_datetime(r["due_ts"])
        src06_rows.append({
            "source_order_no": r["jt_id"],
            "model_code": r["product_id"].replace("PROD-", ""),
            "source_line_code": r["line_id"],
            "qty": r["qty"],
            "due_date_raw": dt.strftime("%d/%m/%Y"),
            "ts_format": "DD/MM/YYYY",
            "priority": r["priority"],
            "customer_code": r["customer"],
            "status": r["status"]
        })
    df_src06 = pd.DataFrame(src06_rows)
    out_path_06 = Path(RAW_DIR) / "SRC-06_jt" / "plan_jt_orders.csv"
    df_src06.to_csv(out_path_06, sep=";", index=False, encoding="utf-8")
    print(f"  ✓ Đã ghi: {out_path_06.name} ({len(df_src06)} dòng, sep=';')")

    # 7. SRC-07: Inventory Snapshot (CSV, có D06 Manual Noise)
    print("\n[RAW] Xuất SRC-07 Inventory Snapshot...")
    df_inv = pd.read_csv(Path(GT_DIR) / "inventory_truth.csv")
    src07_rows = []
    for idx, r in df_inv.iterrows():
        dt = pd.to_datetime(r["snapshot_time"])
        src07_rows.append({
            "snapshot_id": r["snapshot_id"],
            "capture_ts_raw": dt.strftime("%d/%m/%Y %H:%M"),
            "ts_format": "DD/MM/YYYY HH:MM",
            "item_code": r["item_id"],
            "item_type": r["item_type"],
            "location_code": r["location"].replace(" ", "_"),
            "qty_raw": str(r["qty"]),
            "capture_method": r["capture_method"]
        })
    df_src07 = pd.DataFrame(src07_rows)
    df_src07 = injector.round_manual_inventory(df_src07)
    out_path_07 = Path(RAW_DIR) / "SRC-07_inventory" / "inventory_snapshot.csv"
    df_src07.to_csv(out_path_07, index=False, encoding="utf-8")
    print(f"  ✓ Đã ghi: {out_path_07.name} ({len(df_src07)} dòng, D06 Manual noise applied)")

    # 8. SRC-08: Shipping Plan (CSV)
    print("\n[RAW] Xuất SRC-08 Shipping Plan...")
    df_ship = pd.read_csv(Path(GT_DIR) / "shipment_truth.csv")
    src08_rows = []
    for idx, r in df_ship.iterrows():
        t_dt = pd.to_datetime(r["truck_time"])
        c_dt = pd.to_datetime(r["cutoff_time"])
        src08_rows.append({
            "shipment_ref": r["shipment_id"],
            "order_ref": r["jt_id"],
            "truck_ts_raw": t_dt.strftime("%d/%m/%Y %H:%M"),
            "cutoff_ts_raw": c_dt.strftime("%d/%m/%Y %H:%M"),
            "ts_format": "DD/MM/YYYY HH:MM",
            "product_code": "P1",
            "qty_planned": r["qty_planned"],
            "status": r["status"]
        })
    df_src08 = pd.DataFrame(src08_rows)
    out_path_08 = Path(RAW_DIR) / "SRC-08_shipping" / "shipping_plan.csv"
    df_src08.to_csv(out_path_08, index=False, encoding="utf-8")
    print(f"  ✓ Đã ghi: {out_path_08.name} ({len(df_src08)} dòng)")

    # 9. SRC-09: Incident Log (CSV + Excel)
    print("\n[RAW] Xuất SRC-09 Incident Log...")
    df_inc = pd.read_csv(Path(GT_DIR) / "incident_truth.csv")
    src09_rows = []
    for idx, r in df_inc.iterrows():
        s_dt = pd.to_datetime(r["start_time"])
        e_dt = pd.to_datetime(r["end_time"])
        src09_rows.append({
            "incident_ref": r["incident_id"],
            "machine_or_station": r["station_id"].replace("STN-", ""),
            "start_ts_raw": s_dt.strftime("%d/%m/%Y %H:%M"),
            "end_ts_raw": e_dt.strftime("%d/%m/%Y %H:%M"),
            "ts_format": "DD/MM/YYYY HH:MM",
            "incident_code": r["fmea_code"],
            "note": f"RPN={r['rpn']}, Severity={r['severity_level']}",
            "reported_by": "Van"
        })
    df_src09 = pd.DataFrame(src09_rows)
    out_path_09_csv = Path(RAW_DIR) / "SRC-09_incident" / "andon_scans.csv"
    out_path_09_xlsx = Path(RAW_DIR) / "SRC-09_incident" / "incident_log.xlsx"
    df_src09.to_csv(out_path_09_csv, index=False, encoding="utf-8")
    with pd.ExcelWriter(out_path_09_xlsx, engine="openpyxl") as writer:
        df_src09.to_excel(writer, sheet_name="Incidents_2026", index=False)
    print(f"  ✓ Đã ghi: {out_path_09_csv.name} & {out_path_09_xlsx.name}")

    print("\n✓ ĐÃ HOÀN THÀNH XUẤT 9 NGUỒN DỮ LIỆU RAW ĐẠT CHUẨN 100%.")

if __name__ == "__main__":
    export_all()
