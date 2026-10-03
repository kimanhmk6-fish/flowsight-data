import pandas as pd
from pathlib import Path
from config.constants import MASTER_DIR

Path(MASTER_DIR).mkdir(parents=True, exist_ok=True)


def build_dim_station() -> pd.DataFrame:
    """10 trạm: STN_INB, STN_M1, STN_M2, STN_HT, STN_AS1, STN_AS2, STN_T1, STN_LAB, STN_PK, STN_SHP."""
    # TODO: hard-code 10 trạm với các cột:
    #   station_id, station_name, line_id, stage, station_type,
    #   rated_rate_per_h, cycle_time_s, is_shared, is_bottleneck,
    #   spare_capacity_h_per_day, changeover_time_s, fmea_code_primary, spc_characteristics
    # Gợi ý: STN_M2 = bottleneck, changeover_time_s = 1800
    pass


def build_dim_product() -> pd.DataFrame:
    """4 sản phẩm PROD_P1..P4."""
    # TODO: cột product_id, product_name, product_family, uom,
    #       target_daily_qty, customer_code, active_flag, assembly_line_primary,
    #       changeover_group
    pass


def build_dim_component() -> pd.DataFrame:
    """6 linh kiện COMP_C1..C6."""
    # TODO: cột component_id, component_name, supplier_code,
    #       lead_time_days, safety_stock_qty, fmea_code_supplier
    pass


def build_bom() -> pd.DataFrame:
    """BOM cho 4 sản phẩm (~16 dòng)."""
    # TODO: cột bom_id, product_id, component_id, qty_per_unit,
    #       unit_consumption, scrap_factor
    pass


def build_routing() -> pd.DataFrame:
    """Routing cho 4 sản phẩm (~35 dòng)."""
    # TODO: cột routing_id, product_id, seq_no, station_id,
    #       std_cycle_time_s, yield_rate, scrap_rate, is_bottleneck, is_optional
    # QUAN TRỌNG: yield_rate + scrap_rate = 1.0
    pass


def build_fmea_registry() -> pd.DataFrame:
    """16 FMEA codes chuẩn DENSO."""
    # TODO: cột fmea_code, fmea_category, fmea_description, station_id,
    #       severity, occurrence, detection, rpn, rpn_threshold, recommended_action
    pass


def build_all_master() -> dict:
    """Orchestrator: sinh tất cả master data."""
    print("=" * 60)
    print("  BUILDING MASTER DATA")
    print("=" * 60)
    result = {
        "dim_station":   build_dim_station(),
        "dim_product":   build_dim_product(),
        "dim_component": build_dim_component(),
        "bom":           build_bom(),
        "routing":       build_routing(),
        "fmea_registry": build_fmea_registry(),
    }
    print("✓ Master data built.")
    return result


if __name__ == "__main__":
    build_all_master()
