"""
config.py — Config cho Ingestion Layer (Bước 11A).
"""
import os
from pathlib import Path

# ============================================================
# SEED & REPRODUCIBILITY
# ============================================================
SEED = 42
os.environ["PYTHONHASHSEED"] = str(SEED)

# ============================================================
# PATHS
# ============================================================
# flowsight/ingest/config.py → parent.parent = flowsight/ → parent = repo root
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
STAGED_DIR = DATA_DIR / "staged"
AUDIT_DIR = DATA_DIR / "audit"

for d in [STAGED_DIR, AUDIT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ============================================================
# 9 NGUỒN RAW — FILE FLAT (khớp với data/raw hiện tại)
# ============================================================
RAW_SOURCES = {
    "SRC-01_output": {
        "path": RAW_DIR / "SRC-01_output",
        "file_pattern": "output_perf_*.csv",
        "format": "csv",
        "encoding": "utf-8-sig",     # CÓ BOM
        "delimiter": ",",
        "sheet": None,
    },
    "SRC-02_ipc": {
        "path": RAW_DIR / "SRC-02_ipc",
        "file_pattern": "ipc_*.csv",
        "format": "csv",
        "encoding": "utf-8",         # KHÔNG BOM
        "delimiter": ",",
        "sheet": None,
    },
    "SRC-03_qr": {
        "path": RAW_DIR / "SRC-03_qr",
        "file_pattern": "lot_scans.csv",
        "format": "csv",
        "encoding": "utf-8",
        "delimiter": ",",
        "sheet": None,
    },
    "SRC-04_qc_auto": {
        "path": RAW_DIR / "SRC-04_qc_auto",
        "file_pattern": "qc_autotest_*.csv",
        "format": "csv",
        "encoding": "utf-8",
        "delimiter": ",",
        "sheet": None,
    },
    "SRC-05_qc_sampling": {
        "path": RAW_DIR / "SRC-05_qc_sampling",
        "file_pattern": "qc_sampling_*.xlsx",
        "format": "excel",
        "encoding": None,
        "delimiter": None,
        "sheet": None,               # Multi-sheet, auto-detect
    },
    "SRC-06_jt": {
        "path": RAW_DIR / "SRC-06_jt",
        "file_pattern": "plan_jt_orders.csv",
        "format": "csv",
        "encoding": "utf-8",
        "delimiter": ";",            # DẤU CHẤM PHẨY
        "sheet": None,
    },
    "SRC-07_inventory": {
        "path": RAW_DIR / "SRC-07_inventory",
        "file_pattern": "inventory_snapshot.csv",
        "format": "csv",
        "encoding": "utf-8",
        "delimiter": ",",
        "sheet": None,
    },
    "SRC-08_shipping": {
        "path": RAW_DIR / "SRC-08_shipping",
        "file_pattern": "shipping_plan.csv",
        "format": "csv",
        "encoding": "utf-8",
        "delimiter": ",",
        "sheet": None,
    },
    "SRC-09_incident": {
        "path": RAW_DIR / "SRC-09_incident",
        "file_pattern": "incident_log.*",
        "format": "auto",            # CSV hoặc Excel
        "encoding": "utf-8",
        "delimiter": ",",
        "sheet": None,
    },
}
