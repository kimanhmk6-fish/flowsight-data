import pandas as pd
from pathlib import Path
from config.constants import MASTER_DIR

Path(MASTER_DIR).mkdir(parents=True, exist_ok=True)

def build_dim_station() -> pd.DataFrame:
    stations = [
        ("STN-INB", "Trạm nhập kho linh kiện", "SHARED", "INBOUND", "MANUAL", None, 60.0, True, False, 4.0, 0.0, "FMEA-INB-001", "material_receipt_rate"),
        ("STN-M1", "Máy phay CNC M1", "A", "MACHINING", "MACHINE", 128.57, 28.0, False, False, 1.5, 600.0, "FMEA-M1-001", "Đường kính trục"),
        ("STN-M2", "Máy ép thủy lực M2", "A", "MACHINING", "MACHINE", 100.00, 36.0, False, True, 2.5, 1800.0, "FMEA-M2-001", "Lực ép"),
        ("STN-HT", "Lò nhiệt luyện HT (dùng chung)", "SHARED", "MACHINING", "BATCH", 20.00, 7200.0, True, False, 1.0, 3600.0, "FMEA-HT-001", "Độ cứng"),
        ("STN-AS1", "Lắp ráp robot AS1", "A", "ASSEMBLY", "MACHINE", 85.71, 42.0, False, False, 1.0, 900.0, "FMEA-AS1-001", "Mô-men xoắn"),
        ("STN-AS2", "Lắp ráp thủ công AS2", "B", "ASSEMBLY", "MANUAL", 65.45, 55.0, False, False, 0.5, 1200.0, "FMEA-AS2-001", "Mô-men xoắn"),
        ("STN-T1", "Máy test tự động T1", "A", "QC", "TEST", 240.00, 15.0, False, False, 2.0, 300.0, "FMEA-T1-001", "Kích thước tổng thể"),
        ("STN-LAB", "Phòng đo LAB", "SHARED", "QC", "TEST", None, 900.0, True, False, 3.0, 0.0, "FMEA-LAB-001", "Độ cứng"),
        ("STN-PK", "Đóng gói PK", "SHARED", "PACKING", "MANUAL", None, 45.0, True, False, 2.0, 120.0, "FMEA-PK-001", ""),
        ("STN-SHP", "Bến xuất hàng SHP", "SHARED", "SHIPPING", "TRANSPORT", None, 120.0, True, False, 0.5, 0.0, "FMEA-SHP-001", "")
    ]
    cols = ["station_id", "station_name", "line_id", "stage", "station_type", "rated_rate_per_h", "cycle_time_s", "is_shared", "is_bottleneck", "spare_capacity_h_per_day", "changeover_time_s", "fmea_code_primary", "spc_characteristics"]
    df = pd.DataFrame(stations, columns=cols)
    df.to_csv(Path(MASTER_DIR) / "dim_station.csv", index=False)
    return df

def build_dim_product() -> pd.DataFrame:
    products = [
        ("PROD-P1", "Sản phẩm truyền động A", "Drivetrain", "pcs", 900, "KHACH_X", True, "A", "GROUP_12"),
        ("PROD-P2", "Sản phẩm truyền động B", "Drivetrain", "pcs", 572, "KHACH_Y", True, "A", "GROUP_12"),
        ("PROD-P3", "Sản phẩm phụ trợ C", "Auxiliary", "pcs", 400, "KHACH_Z", True, "B", "GROUP_34"),
        ("PROD-P4", "Sản phẩm phụ trợ D", "Auxiliary", "pcs", 300, "KHACH_W", True, "B", "GROUP_34")
    ]
    cols = ["product_id", "product_name", "product_family", "uom", "target_daily_qty", "customer_code", "active_flag", "assembly_line_primary", "changeover_group"]
    df = pd.DataFrame(products, columns=cols)
    df.to_csv(Path(MASTER_DIR) / "dim_product.csv", index=False)
    return df

def build_dim_component() -> pd.DataFrame:
    components = [
        ("COMP-C1", "Trục thép chính", "NCC-X", 3.0, 3000, "pcs", True, ""),
        ("COMP-C2", "Vòng bi loại A", "NCC-X", 3.0, 2000, "pcs", True, ""),
        ("COMP-C3", "Phớt cao su đặc biệt", "NCC-X", 5.0, 1500, "pcs", True, "FMEA-SUP-001"),
        ("COMP-C4", "Keo công nghiệp loại B", "NCC-Y", 4.0, 800, "kg", False, ""),
        ("COMP-C5", "Đai ốc inox M8", "NCC-Y", 4.0, 5000, "pcs", False, ""),
        ("COMP-C6", "Vật liệu đệm chống rung", "NCC-Z", 7.0, 600, "pcs", True, "")
    ]
    cols = ["component_id", "component_name", "supplier_code", "lead_time_days", "safety_stock_qty", "uom", "inspection_required", "fmea_code_supplier"]
    df = pd.DataFrame(components, columns=cols)
    df.to_csv(Path(MASTER_DIR) / "dim_component.csv", index=False)
    return df

def build_bom() -> pd.DataFrame:
    bom = [
        ("BOM-001", "PROD-P1", "COMP-C1", 2.000, "pcs", 1.002),
        ("BOM-002", "PROD-P1", "COMP-C3", 1.000, "pcs", 1.005),
        ("BOM-003", "PROD-P1", "COMP-C5", 4.000, "pcs", 1.001),
        ("BOM-004", "PROD-P1", "COMP-C6", 0.500, "pcs", 1.002),
        ("BOM-005", "PROD-P1", "COMP-C2", 1.000, "pcs", 1.002),
        ("BOM-006", "PROD-P2", "COMP-C1", 1.500, "pcs", 1.002),
        ("BOM-007", "PROD-P2", "COMP-C2", 2.000, "pcs", 1.002),
        ("BOM-008", "PROD-P2", "COMP-C3", 0.500, "pcs", 1.005),
        ("BOM-009", "PROD-P2", "COMP-C5", 3.000, "pcs", 1.001),
        ("BOM-010", "PROD-P3", "COMP-C2", 1.000, "pcs", 1.002),
        ("BOM-011", "PROD-P3", "COMP-C4", 0.200, "kg", 1.010),
        ("BOM-012", "PROD-P3", "COMP-C5", 2.000, "pcs", 1.001),
        ("BOM-013", "PROD-P4", "COMP-C2", 2.000, "pcs", 1.002),
        ("BOM-014", "PROD-P4", "COMP-C4", 0.150, "kg", 1.010),
        ("BOM-015", "PROD-P4", "COMP-C6", 1.000, "pcs", 1.002),
        ("BOM-016", "PROD-P4", "COMP-C5", 2.000, "pcs", 1.001)
    ]
    cols = ["bom_id", "product_id", "component_id", "qty_per_unit", "unit_consumption", "scrap_factor"]
    df = pd.DataFrame(bom, columns=cols)
    df.to_csv(Path(MASTER_DIR) / "bom.csv", index=False)
    return df

def build_routing() -> pd.DataFrame:
    routings = [
        ("RT-P1-01", "PROD-P1", 1, "STN-INB", 60.0, 1.0000, 0.0000, False, False, "Nhập kho"),
        ("RT-P1-02", "PROD-P1", 2, "STN-M1", 28.0, 0.9990, 0.0010, False, False, "CNC"),
        ("RT-P1-03", "PROD-P1", 3, "STN-M2", 36.0, 0.9985, 0.0015, True, False, "Ép - Bottleneck"),
        ("RT-P1-04", "PROD-P1", 4, "STN-HT", 7200.0, 0.9975, 0.0025, False, False, "Nhiệt luyện"),
        ("RT-P1-05", "PROD-P1", 5, "STN-AS1", 42.0, 0.9980, 0.0020, False, False, "Robot AS1"),
        ("RT-P1-06", "PROD-P1", 6, "STN-T1", 15.0, 0.9995, 0.0005, False, False, "Test tự động"),
        ("RT-P1-07", "PROD-P1", 7, "STN-PK", 45.0, 0.9995, 0.0005, False, False, "Đóng gói"),
        ("RT-P1-08", "PROD-P1", 8, "STN-SHP", 120.0, 1.0000, 0.0000, False, False, "Xuất hàng"),

        ("RT-P2-01", "PROD-P2", 1, "STN-INB", 60.0, 1.0000, 0.0000, False, False, ""),
        ("RT-P2-02", "PROD-P2", 2, "STN-M1", 32.0, 0.9990, 0.0010, False, False, ""),
        ("RT-P2-03", "PROD-P2", 3, "STN-M2", 36.0, 0.9985, 0.0015, True, False, "Bottleneck"),
        ("RT-P2-04", "PROD-P2", 4, "STN-HT", 7200.0, 0.9975, 0.0025, False, False, ""),
        ("RT-P2-05", "PROD-P2", 5, "STN-AS1", 45.0, 0.9980, 0.0020, False, False, ""),
        ("RT-P2-06", "PROD-P2", 6, "STN-T1", 15.0, 0.9995, 0.0005, False, False, ""),
        ("RT-P2-07", "PROD-P2", 7, "STN-LAB", 900.0, 0.9990, 0.0010, False, True, "Mẫu 10%"),
        ("RT-P2-08", "PROD-P2", 8, "STN-PK", 45.0, 0.9995, 0.0005, False, False, ""),
        ("RT-P2-09", "PROD-P2", 9, "STN-SHP", 120.0, 1.0000, 0.0000, False, False, ""),

        ("RT-P3-01", "PROD-P3", 1, "STN-INB", 60.0, 1.0000, 0.0000, False, False, ""),
        ("RT-P3-02", "PROD-P3", 2, "STN-M1", 30.0, 0.9990, 0.0010, False, False, ""),
        ("RT-P3-03", "PROD-P3", 3, "STN-HT", 7200.0, 0.9975, 0.0025, False, False, ""),
        ("RT-P3-04", "PROD-P3", 4, "STN-AS2", 55.0, 0.9965, 0.0035, False, False, "Thủ công Line B"),
        ("RT-P3-05", "PROD-P3", 5, "STN-T1", 15.0, 0.9995, 0.0005, False, False, ""),
        ("RT-P3-06", "PROD-P3", 6, "STN-PK", 45.0, 0.9995, 0.0005, False, False, ""),
        ("RT-P3-07", "PROD-P3", 7, "STN-SHP", 120.0, 1.0000, 0.0000, False, False, ""),

        ("RT-P4-01", "PROD-P4", 1, "STN-INB", 60.0, 1.0000, 0.0000, False, False, ""),
        ("RT-P4-02", "PROD-P4", 2, "STN-M1", 32.0, 0.9990, 0.0010, False, False, ""),
        ("RT-P4-03", "PROD-P4", 3, "STN-HT", 7200.0, 0.9975, 0.0025, False, False, ""),
        ("RT-P4-04", "PROD-P4", 4, "STN-AS2", 58.0, 0.9965, 0.0035, False, False, ""),
        ("RT-P4-05", "PROD-P4", 5, "STN-LAB", 900.0, 0.9990, 0.0010, False, False, ""),
        ("RT-P4-06", "PROD-P4", 6, "STN-PK", 45.0, 0.9995, 0.0005, False, False, ""),
        ("RT-P4-07", "PROD-P4", 7, "STN-SHP", 120.0, 1.0000, 0.0000, False, False, "")
    ]
    cols = ["routing_id", "product_id", "seq_no", "station_id", "std_cycle_time_s", "yield_rate", "scrap_rate", "is_bottleneck", "is_optional", "notes"]
    df = pd.DataFrame(routings, columns=cols)
    df.to_csv(Path(MASTER_DIR) / "routing.csv", index=False)
    return df

def build_fmea_registry() -> pd.DataFrame:
    fmea_items = [
        ("FMEA-M2-001", "TOOL_WEAR", "Mòn khuôn ép", "STN-M2", 8, 3, 4, 96, "MEDIUM", "Đổi khuôn định kỳ"),
        ("FMEA-M2-002", "TOOL_JAM", "Kẹt khuôn", "STN-M2", 7, 2, 3, 42, "LOW", "Vệ sinh khuôn"),
        ("FMEA-M2-003", "FORCE_DEVIATION", "Lệch lực ép", "STN-M2", 7, 2, 4, 56, "MEDIUM", "Hiệu chuẩn loadcell"),
        ("FMEA-M1-001", "TOOL_WEAR", "Mòn dao CNC", "STN-M1", 6, 3, 3, 54, "MEDIUM", "Đổi dao định kỳ"),
        ("FMEA-M1-002", "TOOL_VIBRATION", "Rung dao CNC", "STN-M1", 6, 3, 3, 54, "MEDIUM", "Cân bằng trục"),
        ("FMEA-M1-003", "TOOL_BREAKAGE", "Gãy dao", "STN-M1", 9, 1, 2, 18, "LOW", "Giám sát tải"),
        ("FMEA-HT-001", "TEMP_DEVIATION", "Lệch nhiệt độ lò", "STN-HT", 9, 3, 5, 135, "HIGH", "Hiệu chuẩn thermocouple"),
        ("FMEA-HT-002", "TIME_DEVIATION", "Lệch thời gian mẻ", "STN-HT", 6, 2, 3, 36, "LOW", "Kiểm tra timer"),
        ("FMEA-AS1-001", "TORQUE_DEVIATION", "Lệch mô-men robot", "STN-AS1", 7, 2, 4, 56, "MEDIUM", "Hiệu chuẩn sensor"),
        ("FMEA-AS2-001", "OPERATOR_ERROR", "Lỗi thao tác thủ công", "STN-AS2", 5, 3, 2, 30, "LOW", "Đào tạo lại"),
        ("FMEA-T1-001", "VOLTAGE_DROP", "Sụt áp máy test", "STN-T1", 7, 2, 3, 42, "LOW", "Ổn định nguồn"),
        ("FMEA-LAB-001", "MEASUREMENT_ERROR", "Sai số đo LAB", "STN-LAB", 5, 2, 2, 20, "LOW", "Hiệu chuẩn thiết bị"),
        ("FMEA-SUP-001", "SUPPLIER_QUALITY", "Lỗi vật tư NCC", "", 8, 3, 4, 96, "MEDIUM", "Kiểm tra đầu vào"),
        ("FMEA-SUP-002", "MATERIAL_BATCH", "Lô vật tư lỗi", "", 9, 2, 6, 108, "HIGH", "Truy xuất containment"),
        ("FMEA-DATA-001", "LABEL_DUPLICATION", "Trùng nhãn Lot", "STN-HT", 7, 2, 3, 42, "LOW", "Kiểm tra scan 2 lần"),
        ("FMEA-COMB-001", "COMBINED_CAUSES", "Nguyên nhân kết hợp", "", 6, 2, 4, 48, "LOW", "Phân tích đa biến"),
        ("FMEA-UNKNOWN", "INSUFFICIENT_EVIDENCE", "Chưa đủ bằng chứng", "", 0, 0, 0, 0, "NA", "Kiểm tra thủ công")
    ]
    cols = ["fmea_code", "fmea_category", "fmea_description", "station_id", "severity", "occurrence", "detection", "rpn", "rpn_threshold", "recommended_action"]
    df = pd.DataFrame(fmea_items, columns=cols)
    df.to_csv(Path(MASTER_DIR) / "fmea_registry.csv", index=False)
    return df

def build_all_master() -> dict:
    print("=" * 60)
    print("BUILDING MASTER DATA (ĐỦ 6 FILE CHUẨN DENSO)")
    print("=" * 60)
    res = {
        "dim_station": build_dim_station(),
        "dim_product": build_dim_product(),
        "dim_component": build_dim_component(),
        "bom": build_bom(),
        "routing": build_routing(),
        "fmea_registry": build_fmea_registry()
    }
    print("✓ Đã tạo thành công đủ 6 file Master Data tại data/master/")
    return res

if __name__ == "__main__":
    build_all_master()
