import pandas as pd
import json
from pathlib import Path
from datetime import timedelta
from config.constants import GT_DIR, SEED, START_DATE_STR

Path(GT_DIR).mkdir(parents=True, exist_ok=True)


# ============================================================
# 1. GENEALOGY
# ============================================================
def build_genealogy_truth(factory) -> pd.DataFrame:
    """Xuất genealogy_truth.csv — quan hệ SPLIT/MERGE."""
    print("\n[GT] Building genealogy_truth.csv...")
    # TODO: convert factory.genealogy → DataFrame
    # Cột: edge_id, parent_lot_id, child_lot_id, edge_type, qty,
    #      true_time, confidence, evidence
    pass


# ============================================================
# 2. CANONICAL LOTS
# ============================================================
def build_canonical_lots(factory) -> pd.DataFrame:
    """Xuất canonical_lots.csv — 410 lots."""
    print("\n[GT] Building canonical_lots.csv...")
    # TODO: convert factory.lots → DataFrame
    # Cột: lot_id, product_id, qty, parent_kind, parent_batch,
    #      line_id, created_day, created_ts, shift, status
    pass


# ============================================================
# 3. PRODUCTION EVENTS
# ============================================================
def build_production_truth(factory) -> pd.DataFrame:
    """Xuất production_truth.csv (~5000 events)."""
    print("\n[GT] Building production_truth.csv...")
    # TODO: convert factory.events → DataFrame
    # Cột: event_id, lot_id, station_id, event_type, start_time, end_time,
    #      shift, param_temp, param_force, param_vibration,
    #      qty_in, qty_out, qty_ng, is_physical_anomaly, anomaly_type
    pass


# ============================================================
# 4. MATERIAL CONSUMPTION
# ============================================================
def build_material_consumption(factory) -> pd.DataFrame:
    """Xuất material_consumption_truth.csv (~1000 dòng)."""
    print("\n[GT] Building material_consumption_truth.csv...")
    # TODO: convert factory.consumption → DataFrame
    # Cột: consumption_id, lot_id, mat_lot_id, component_id,
    #      qty_consumed, consumption_time
    pass


def build_material_lots() -> pd.DataFrame:
    """Xuất material_lot_truth.csv."""
    # TODO: hard-code danh sách material lots
    # VD: MAT_C3_0917_02, qty=5000, received D0
    pass


# ============================================================
# 5. QC
# ============================================================
def build_qc_truth(factory) -> pd.DataFrame:
    """Xuất qc_truth.csv (~950 records)."""
    print("\n[GT] Building qc_truth.csv...")
    # TODO: AUTO: 2 đặc tính/lot, SAMPLE: 10% lots × 3 đặc tính
    # TODO: gán spc_nelson_rule và cpk_trend
    # Case R03: LOT_0401..LOT_0405 có QC NG ở LAB
    pass


def build_qc_capability(factory) -> pd.DataFrame:
    """Xuất qc_capability_truth.csv (~75 dòng)."""
    print("\n[GT] Building qc_capability_truth.csv...")
    # TODO: 14 ngày × 5 đặc tính = ~70 dòng
    # Case R02: Cpk STN_M1 DECLINING 1.48 → 0.68
    pass


# ============================================================
# 6. JT ALLOCATION
# ============================================================
def build_jt_orders() -> pd.DataFrame:
    """Xuất jt_order_truth.csv (45 JT orders)."""
    # TODO
    pass


def build_jt_allocation() -> pd.DataFrame:
    """Xuất jt_allocation_truth.csv (~180 dòng)."""
    # TODO: mỗi JT cần 2-5 lots
    pass


# ============================================================
# 7. INVENTORY / SHIPMENT
# ============================================================
def build_inventory_truth(factory) -> pd.DataFrame:
    """Xuất inventory_truth.csv (~400 dòng)."""
    # TODO: 2 snapshots/ngày × 14 ngày × ~14 items
    pass


def build_shipment_truth(factory) -> pd.DataFrame:
    """Xuất shipment_truth.csv (~45 dòng)."""
    # TODO
    pass


# ============================================================
# 8. INCIDENTS
# ============================================================
def build_incident_truth(factory) -> pd.DataFrame:
    """Xuất incident_truth.csv (20 dòng) + gắn test_case_link."""
    print("\n[GT] Building incident_truth.csv...")
    # TODO: 12 cho F01-F12, 8 cho R01-R08
    # Cột: incident_id, station_id, start_time, end_time, duration_h,
    #      fmea_code, rpn, severity_level, root_cause_type,
    #      affected_lots, test_case_link
    pass


# ============================================================
# 9. ENTITY MAPPING
# ============================================================
def build_entity_mapping(factory) -> pd.DataFrame:
    """Xuất entity_mapping_truth.csv (canonical ↔ 9 aliases)."""
    print("\n[GT] Building entity_mapping_truth.csv...")
    # TODO: với mỗi canonical lot, sinh 5 aliases:
    #   SRC_01_OUTPUT:  A0147
    #   SRC_02_IPC:     L_A_0147
    #   SRC_03_QR:      QR260929A147
    #   SRC_04_QC_AUTO: LOT_0147_A
    #   SRC_05_QC_SAMP: LOT_0147_A
    pass


# ============================================================
# 10. 24 TEST CASE ANSWERS
# ============================================================
def build_24_test_case_answers(factory):
    """Sinh impact_truth_Fxx.json và cause_truth_Rxx.json."""
    print("\n[GT] Building 24 test case answers...")
    # TODO: chạy lại logic netting / cause trên Ground Truth
    # → lấy đáp án cho từng case
    pass


# ============================================================
# MAIN ORCHESTRATOR
# ============================================================
def main(factory):
    print("=" * 60)
    print("  BUILDING GROUND TRUTH")
    print("=" * 60)

    build_canonical_lots(factory)
    build_genealogy_truth(factory)
    build_material_lots()
    build_material_consumption(factory)
    build_production_truth(factory)
    build_qc_truth(factory)
    build_qc_capability(factory)
    build_jt_orders()
    build_jt_allocation()
    build_inventory_truth(factory)
    build_shipment_truth(factory)
    build_incident_truth(factory)
    build_entity_mapping(factory)
    build_24_test_case_answers(factory)

    print("\n✓ Ground Truth exported successfully.")


if __name__ == "__main__":
    from factory_sim import run_simulation
    factory = run_simulation()
    main(factory)
