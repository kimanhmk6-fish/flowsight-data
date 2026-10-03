# ============================================================
# SEED & REPRODUCIBILITY
# ============================================================
SEED = 42
NUM_DAYS = 14
SHIFTS_PER_DAY = 2
HOURS_PER_SHIFT = 8

# ============================================================
# VOLUME TARGETS (Bước 1 spec)
# ============================================================
TARGET_LOTS = 410
TARGET_EVENTS = 5000
TARGET_QC = 900
TARGET_INCIDENTS = 20
TARGET_QC_SAMPLING = 120
TARGET_JT_ORDERS = 45
TARGET_SHIPMENTS = 30
TARGET_MATERIAL_LOTS = 10   # MVP

# ============================================================
# CLOCK OFFSETS (giây) — D01
# ============================================================
CLOCK_OFFSET = {
    "STN_M2":  -4 * 60,   # -4 phút (M2 chậm)
    "STN_AS2": +6 * 60,   # +6 phút (AS2 nhanh)
}
DRIFT_PER_DAY_SEC = {
    "STN_M2":   +2.0,     # +2s/ngày
    "STN_AS2":  -1.5,     # -1.5s/ngày
}

# ============================================================
# ERROR INJECTION RATES — D01-D10
# ============================================================
MISSING_SCAN_RATE = 0.02         # D02: 2%
DUPLICATE_LOT_RATE = 0.01        # D03: 1%
DECIMAL_COMMA_DAYS = [2, 5, 10]  # D05: 3 ngày dùng dấu phẩy
SCHEMA_DRIFT_DAY = 8             # D04: ngày thứ 9 (0-indexed)
MANUAL_INVENTORY_NOISE_RATE = 0.5  # D06: 50% MANUAL bị làm tròn

# ============================================================
# CANONICAL ID FORMATS
# ============================================================
LOT_PREFIX   = "LOT"
BATCH_PREFIX = "BATCH-HT"
PROD_PREFIX  = "PROD-P"
COMP_PREFIX  = "COMP-C"
MAT_PREFIX   = "MAT"
STN_PREFIX   = "STN"
JT_PREFIX    = "JT"
SHP_PREFIX   = "SHP"
INC_PREFIX   = "INC"

# ============================================================
# TIMELINE
# ============================================================
START_DATE_STR = "2026-09-29"    # D0

# ============================================================
# PATHS
# ============================================================
DATA_DIR   = "data"
MASTER_DIR = f"{DATA_DIR}/master"
GT_DIR     = f"{DATA_DIR}/ground_truth"
RAW_DIR    = f"{DATA_DIR}/raw"

# ============================================================
# STATIONS / PRODUCTS / COMPONENTS (hard-coded)
# ============================================================
STATION_IDS = [
    "STN_INB", "STN_M1", "STN_M2", "STN_HT",
    "STN_AS1", "STN_AS2", "STN_T1", "STN_LAB",
    "STN_PK",  "STN_SHP",
]

PRODUCT_IDS   = [f"PROD_P{i}" for i in range(1, 5)]
COMPONENT_IDS = [f"COMP_C{i}" for i in range(1, 7)]

# ============================================================
# 24 TEST CASES (khóa cứng)
# ============================================================
TEST_CASES = {
    "FORWARD":  [f"F{i:02d}" for i in range(1, 13)],  # F01-F12
    "BACKWARD": [f"R{i:02d}" for i in range(1, 9)],   # R01-R08
    "DATA":     [f"D{i:02d}" for i in range(1, 5)],   # D01-D04
}
