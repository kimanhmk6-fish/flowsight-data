"""
validator.py — Kiểm chứng dữ liệu sinh ra.
Mỗi rule được đếm thật qua helper rule(); không hardcode tổng số.
"""
import pandas as pd
from pathlib import Path
from config.constants import (
    RAW_DIR, GT_DIR, MASTER_DIR,
    TARGET_LOTS, TARGET_EVENTS, TARGET_QC, TARGET_INCIDENTS
)

COUNTS = {"passed": 0, "total": 0}
FAILURES = []


def rule(name: str, cond: bool, msg: str = ""):
    COUNTS["total"] += 1
    if cond:
        COUNTS["passed"] += 1
        print(f"  ✓ {name}")
    else:
        FAILURES.append(f"{name}: {msg}")
        print(f"  ✗ {name} — {msg}")


def check_schema():
    print("\n[1/6] KIỂM TRA SCHEMA ĐỦ 9 NGUỒN RAW...")
    schemas = {
        "SRC-01_output": ["record_id", "local_lot_label", "model_code", "line_code", "qty_ok", "qty_ng", "actual_rate_per_h", "event_ts", "ts_format"],
        "SRC-02_ipc": ["ipc_event_id", "machine_code", "local_lot_ref", "event_type", "event_code", "param_temp", "param_force", "param_vibration", "ts_raw", "ts_format", "export_ts"],
        "SRC-03_qr": ["scan_id", "qr_code", "parent_qr_code", "scan_type", "station_code", "scan_ts_raw", "ts_format", "operator_code"],
        "SRC-04_qc_auto": ["qc_record_id", "local_lot_ref", "model_code", "station_code", "characteristic", "value_raw", "lsl", "usl", "result", "ng_code", "measured_ts_raw", "ts_format"],
        "SRC-06_jt": ["source_order_no", "model_code", "source_line_code", "qty", "due_date_raw", "ts_format", "priority", "customer_code", "status"],
        "SRC-07_inventory": ["snapshot_id", "capture_ts_raw", "ts_format", "item_code", "item_type", "location_code", "qty_raw", "capture_method"],
        "SRC-08_shipping": ["shipment_ref", "order_ref", "truck_ts_raw", "cutoff_ts_raw", "ts_format", "product_code", "qty_planned", "status"],
        "SRC-09_incident": ["incident_ref", "machine_or_station", "start_ts_raw", "end_ts_raw", "ts_format", "incident_code", "note", "reported_by"]
    }
    for folder, cols in schemas.items():
        csv_files = list((Path(RAW_DIR) / folder).glob("*.csv"))
        if not csv_files:
            rule(f"{folder} tồn tại file CSV", False, "thiếu file")
            continue
        sep = ";" if folder == "SRC-06_jt" else ","
        df = pd.read_csv(csv_files[0], sep=sep, nrows=5)
        missing = set(cols) - set(df.columns)
        rule(f"{folder} đủ {len(cols)} cột chuẩn", len(missing) == 0, f"thiếu: {missing}")

    excel_files = list((Path(RAW_DIR) / "SRC-05_qc_sampling").glob("*.xlsx"))
    rule("SRC-05_qc_sampling tồn tại file Excel", len(excel_files) > 0, "thiếu file")
    if excel_files:
        xl = pd.ExcelFile(excel_files[0])
        rule("SRC-05 có sheet 'Data'", "Data" in xl.sheet_names, "thiếu sheet Data")
        df_excel = xl.parse("Data", nrows=5)
        cols_05 = ["local_lot_ref", "characteristic", "value_raw", "measured_date", "station_code", "inspector", "ts_format"]
        missing_05 = set(cols_05) - set(df_excel.columns)
        rule("SRC-05 sheet Data đủ cột", len(missing_05) == 0, f"thiếu: {missing_05}")


def check_volume():
    print("\n[2/6] KIỂM TRA KHỐI LƯỢNG (VOLUME ±10%)...")
    lots = len(pd.read_csv(Path(GT_DIR) / "canonical_lots.csv"))
    events = len(pd.read_csv(Path(GT_DIR) / "production_truth.csv"))
    qc = len(pd.read_csv(Path(GT_DIR) / "qc_truth.csv"))
    inc = len(pd.read_csv(Path(GT_DIR) / "incident_truth.csv"))
    rule(f"Lots ≈ {TARGET_LOTS} (thực {lots})", abs(lots - TARGET_LOTS) / TARGET_LOTS <= 0.10, f"sai lệch {lots}")
    rule(f"Events ≈ {TARGET_EVENTS} (thực {events})", abs(events - TARGET_EVENTS) / TARGET_EVENTS <= 0.15, f"sai lệch {events}")
    rule(f"QC ≈ {TARGET_QC} (thực {qc})", abs(qc - TARGET_QC) / TARGET_QC <= 0.10, f"sai lệch {qc}")
    rule(f"Incidents ≈ {TARGET_INCIDENTS} (thực {inc})", abs(inc - TARGET_INCIDENTS) <= 2, f"sai lệch {inc}")


def check_business_rules():
    print("\n[3/6] KIỂM TRA BẢO TOÀN VẬT CHẤT & GENEALOGY...")
    df_prod = pd.read_csv(Path(GT_DIR) / "production_truth.csv")
    invalid_qty = df_prod[df_prod["qty_in"] != df_prod["qty_out"] + df_prod["qty_ng"]]
    rule("Bảo toàn vật chất (qty_in = qty_out + qty_ng)", len(invalid_qty) == 0, f"{len(invalid_qty)} dòng vi phạm")

    df_genealogy = pd.read_csv(Path(GT_DIR) / "genealogy_truth.csv")
    lots = set(pd.read_csv(Path(GT_DIR) / "canonical_lots.csv")["lot_id"])
    # parent có thể là BATCH (mẻ lò) — chỉ lot parent mới phải tồn tại
    dangling_parent = df_genealogy[(~df_genealogy["parent_lot_id"].isin(lots))
                                   & (~df_genealogy["parent_lot_id"].str.startswith("BATCH-"))]
    dangling_child = df_genealogy[~df_genealogy["child_lot_id"].isin(lots)]
    rule("Genealogy không có cạnh treo (parent)", len(dangling_parent) == 0,
         f"{len(dangling_parent)} cạnh treo: {dangling_parent['parent_lot_id'].unique()[:3]}")
    rule("Genealogy không có cạnh treo (child)", len(dangling_child) == 0,
         f"{len(dangling_child)} cạnh treo: {dangling_child['child_lot_id'].unique()[:3]}")
    splits = df_genealogy[df_genealogy["edge_type"] == "SPLIT"]
    rule("Đủ liên kết SPLIT cho 2 mẻ B07/B08", len(splits) == 10, f"thực {len(splits)}")


def check_temporal_consistency():
    print("\n[4/6] KIỂM TRA TÍNH NHÂN QUẢ THỜI GIAN...")
    df_prod = pd.read_csv(Path(GT_DIR) / "production_truth.csv")
    df_cons = pd.read_csv(Path(GT_DIR) / "material_consumption_truth.csv")
    df_qc = pd.read_csv(Path(GT_DIR) / "qc_truth.csv")

    prod_start = df_prod.groupby("lot_id")["start_time"].min().reset_index()
    merged_cons = df_cons.merge(prod_start, on="lot_id")
    inv_cons = merged_cons[pd.to_datetime(merged_cons["consumption_time"]) > pd.to_datetime(merged_cons["start_time"])]
    rule("Vật tư tiêu hao trước khi SX bắt đầu", len(inv_cons) == 0, f"{len(inv_cons)} vi phạm")

    prod_end = df_prod.groupby("lot_id")["end_time"].max().reset_index()
    merged_qc = df_qc.merge(prod_end, on="lot_id")
    inv_qc = merged_qc[pd.to_datetime(merged_qc["measured_time"]) < pd.to_datetime(merged_qc["end_time"])]
    rule("QC đo sau khi SX kết thúc", len(inv_qc) == 0, f"{len(inv_qc)} vi phạm")


def check_injected_errors():
    print("\n[5/6] KIỂM TRA TOÀN VẸN CÁC LỖI ĐÃ CHÈN (D01-D06)...")
    ipc_files = list((Path(RAW_DIR) / "SRC-02_ipc").glob("*.csv"))
    rule("D01: SRC-02_ipc tồn tại & không rỗng", len(ipc_files) > 0 and (len(pd.read_csv(ipc_files[0])) > 0 if ipc_files else False), "thiếu file")

    qr_files = list((Path(RAW_DIR) / "SRC-03_qr").glob("*.csv"))
    if qr_files:
        df_qr = pd.read_csv(qr_files[0])
        df_prod = pd.read_csv(Path(GT_DIR) / "production_truth.csv")
        drop_rate = 1.0 - (len(df_qr) / len(df_prod))
        rule(f"D02: missing scan ≥ 1.5% (thực {drop_rate:.2%})", drop_rate >= 0.015, f"thấp: {drop_rate:.2%}")
        dup_scans = df_qr[df_qr["qr_code"].str.contains("0403", na=False)]
        rule("D03: duplicate lot labels", len(dup_scans) >= 2, "chưa chèn")
    else:
        rule("D02/D03: SRC-03_qr tồn tại", False, "thiếu file")

    excel_files = list((Path(RAW_DIR) / "SRC-05_qc_sampling").glob("*.xlsx"))
    if excel_files:
        xl = pd.ExcelFile(excel_files[0])
        target_sheet = "Day_9" if "Day_9" in xl.sheet_names else xl.sheet_names[-1]
        df_drift = xl.parse(target_sheet)
        rule("D04: schema drift trên Excel", "Mã lô" in df_drift.columns and "Giá trị" in df_drift.columns, "chưa áp dụng")
    else:
        rule("D04: SRC-05 Excel tồn tại", False, "thiếu file")

    qc_auto_files = list((Path(RAW_DIR) / "SRC-04_qc_auto").glob("*.csv"))
    if qc_auto_files:
        df_qc_auto = pd.read_csv(qc_auto_files[0])
        has_comma = df_qc_auto["value_raw"].astype(str).str.contains(",").any()
        rule("D05: dấu phẩy thập phân trong QC Auto", bool(has_comma), "chưa có")
    else:
        rule("D05: SRC-04_qc_auto tồn tại", False, "thiếu file")

    inv_files = list((Path(RAW_DIR) / "SRC-07_inventory").glob("*.csv"))
    if inv_files:
        df_inv = pd.read_csv(inv_files[0])
        manual_qtys = df_inv[df_inv["capture_method"] == "MANUAL"]["qty_raw"].astype(int)
        rule("D06: tồn kho MANUAL làm tròn", bool((manual_qtys % 10 == 0).all()), "chưa làm tròn")
    else:
        rule("D06: SRC-07_inventory tồn tại", False, "thiếu file")


def check_cross_file_consistency():
    print("\n[6/6] KIỂM TRA KHÓA LIÊN KẾT & TÍNH NHẤT QUÁN KỊCH BẢN...")
    lots_df = pd.read_csv(Path(GT_DIR) / "canonical_lots.csv")
    canonical_lots = set(lots_df["lot_id"])
    lot_product = dict(zip(lots_df["lot_id"], lots_df["product_id"]))
    prod_lots = set(pd.read_csv(Path(GT_DIR) / "production_truth.csv")["lot_id"])
    rule("Lot trong production_truth ⊂ canonical_lots", prod_lots.issubset(canonical_lots), "có lot lạ")

    invalid_ids = [lot for lot in canonical_lots if "_" in lot]
    rule("Canonical ID dùng dấu '-' (không '_')", len(invalid_ids) == 0, f"VD: {invalid_ids[:3]}")

    stations = set(pd.read_csv(Path(MASTER_DIR) / "dim_station.csv")["station_id"])
    prod_stations = set(pd.read_csv(Path(GT_DIR) / "production_truth.csv")["station_id"])
    rule("Trạm trong production ⊂ dim_station", prod_stations.issubset(stations), "có trạm lạ")

    # JT: không trùng, allocation/shipment tham chiếu hợp lệ
    jt = pd.read_csv(Path(GT_DIR) / "jt_order_truth.csv")
    rule("jt_order không trùng jt_id", jt["jt_id"].is_unique, f"{jt['jt_id'].duplicated().sum()} trùng")
    jt_ids = set(jt["jt_id"])
    jt_product = dict(zip(jt["jt_id"], jt["product_id"]))
    alloc = pd.read_csv(Path(GT_DIR) / "jt_allocation_truth.csv")
    rule("allocation.jt_id ⊂ jt_order", set(alloc["jt_id"]).issubset(jt_ids), "có JT lạ")
    rule("allocation.lot_id ⊂ canonical_lots", set(alloc["lot_id"]).issubset(canonical_lots), "có lot lạ")
    prod_mismatch = alloc[alloc.apply(lambda r: lot_product.get(r["lot_id"]) != jt_product.get(r["jt_id"]), axis=1)]
    rule("allocation: product của lot khớp product của JT", len(prod_mismatch) == 0,
         f"{len(prod_mismatch)} dòng lệch: {prod_mismatch[['jt_id','lot_id']].head(2).to_dict('records')}")

    ship = pd.read_csv(Path(GT_DIR) / "shipment_truth.csv")
    rule("shipment.jt_id ⊂ jt_order", set(ship["jt_id"]).issubset(jt_ids), "có JT lạ")
    jt_qty = dict(zip(jt["jt_id"], jt["qty"]))
    ship_mismatch = ship[ship.apply(lambda r: r["qty_planned"] != jt_qty.get(r["jt_id"]), axis=1)]
    rule("shipment.qty_planned khớp jt_order.qty", len(ship_mismatch) == 0,
         f"{len(ship_mismatch)} dòng lệch")

    # F01: JT-0231 = 1300, shortfall = 1300 - 1200 = 100
    jt231 = jt[jt["jt_id"] == "JT-0231"]
    rule("JT-0231 tồn tại trong jt_order", len(jt231) == 1, "thiếu JT-0231")
    if len(jt231) == 1:
        rule("JT-0231 qty = 1300", int(jt231.iloc[0]["qty"]) == 1300, f"thực {jt231.iloc[0]['qty']}")
    shp231 = ship[ship["jt_id"] == "JT-0231"]
    if len(shp231):
        rule("F01 shortfall = 100 (1300-1200)", int(shp231.iloc[0]["qty_planned"] - shp231.iloc[0]["qty_actual"]) == 100, "sai")

    # Tồn kho D0: P1 = 450, P2 = 600
    inv = pd.read_csv(Path(GT_DIR) / "inventory_truth.csv")
    d0 = inv[inv["snapshot_time"].str.startswith("2026-09-29T06")]
    p1_qty = set(d0[d0["item_id"] == "PROD-P1"]["qty"].tolist())
    p2_qty = set(d0[d0["item_id"] == "PROD-P2"]["qty"].tolist())
    rule("Tồn D0: P1 = 450", p1_qty == {450}, f"thực {p1_qty}")
    rule("Tồn D0: P2 = 600", p2_qty == {600}, f"thực {p2_qty}")


def run_all():
    print("=" * 60)
    print("BẮT ĐẦU CHẠY VALIDATOR")
    print("=" * 60)
    check_schema()
    check_volume()
    check_business_rules()
    check_temporal_consistency()
    check_injected_errors()
    check_cross_file_consistency()
    print("\n" + "=" * 60)
    if FAILURES:
        print(f"KẾT QUẢ: {COUNTS['passed']}/{COUNTS['total']} RULES PASS — CÓ {len(FAILURES)} LỖI:")
        for f in FAILURES:
            print(f"  ✗ {f}")
    else:
        print(f"KẾT QUẢ: {COUNTS['passed']}/{COUNTS['total']} RULES PASS TUYỆT ĐỐI! SẴN SÀNG CHO BƯỚC 11.")
    print("=" * 60)
    return len(FAILURES) == 0


if __name__ == "__main__":
    import sys
    sys.exit(0 if run_all() else 1)
