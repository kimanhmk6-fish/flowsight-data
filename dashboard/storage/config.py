from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
CANONICAL_DIR = DATA_DIR / "canonical"
AUDIT_DIR = DATA_DIR / "audit"

CANONICAL_DIR.mkdir(parents=True, exist_ok=True)

TABLES = [
    "lot",
    "lot_edge",
    "lot_event",
    "material_consumption",
    "jt_order",
    "jt_allocation",
    "shipment",
    "qc_result",
]
