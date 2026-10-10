from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
RESOLVED_DIR = DATA_DIR / "resolved"
CANONICAL_DIR = DATA_DIR / "canonical"
MASTER_DIR = DATA_DIR / "master"
GT_DIR = DATA_DIR / "ground_truth"
AUDIT_DIR = DATA_DIR / "audit"

for d in [CANONICAL_DIR, AUDIT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Reconstruction rules
MIN_EDGE_CONFIDENCE = 0.75
QTY_CONSERVATION_TOLERANCE = 5

EVIDENCE_CONFIDENCE = {
    "direct_scan": 1.00,
    "inferred_time": 0.85,
    "inferred_qty": 0.80,
    "inferred_batch": 0.75,
}

