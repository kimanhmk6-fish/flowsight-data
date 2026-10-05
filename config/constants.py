from pathlib import Path

# ============================================================
# SEED & REPRODUCIBILITY
# ============================================================
SEED = 42
NUM_DAYS = 14
SHIFTS_PER_DAY = 2
HOURS_PER_SHIFT = 8

# ============================================================
# TARGET VOLUMES (±10%)
# ============================================================
TARGET_LOTS = 410
TARGET_EVENTS = 3000
TARGET_QC = 950
TARGET_INCIDENTS = 20
TARGET_JT_ORDERS = 45
TARGET_SHIPMENTS = 30
TARGET_MATERIAL_LOTS = 10

# ============================================================
# CLOCK OFFSETS (giây) — D01
# ============================================================
CLOCK_OFFSET = {
    "STN-M2": -240,   # -4 phút
    "STN-AS2": 360,   # +6 phút
}
DRIFT_PER_DAY_SEC = {
    "STN-M2": +2.0,
    "STN-AS2": -1.5,
}

# ============================================================
# ERROR INJECTION RATES
# ============================================================
MISSING_SCAN_RATE = 0.02
DUPLICATE_LOT_RATE = 0.01
DECIMAL_COMMA_DAYS = [2, 5, 10]
SCHEMA_DRIFT_DAY = 8
MANUAL_INVENTORY_NOISE_RATE = 0.5

# ============================================================
# CANONICAL ID FORMATS (Dùng dấu gạch ngang '-' tuyệt đối)
# ============================================================
LOT_PREFIX = "LOT"
BATCH_PREFIX = "BATCH-HT"
PROD_PREFIX = "PROD-P"
COMP_PREFIX = "COMP-C"
MAT_PREFIX = "MAT"
STN_PREFIX = "STN"
JT_PREFIX = "JT"
SHP_PREFIX = "SHP"
INC_PREFIX = "INC"

START_DATE_STR = "2026-09-29"

# ============================================================
# PATHS
# ============================================================
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
MASTER_DIR = DATA_DIR / "master"
GT_DIR = DATA_DIR / "ground_truth"
RAW_DIR = DATA_DIR / "raw"
REPORTS_DIR = ROOT_DIR / "reports"

for d in [MASTER_DIR, GT_DIR, RAW_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)
