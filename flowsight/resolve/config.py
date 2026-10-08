from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
ALIGNED_DIR = DATA_DIR / "aligned"
RESOLVED_DIR = DATA_DIR / "resolved"
AUDIT_DIR = DATA_DIR / "audit"

for d in [RESOLVED_DIR, AUDIT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Thresholds
MIN_CONFIDENCE_ACCEPT = 0.75
MIN_CONFIDENCE_MANUAL = 0.50

TIER_WEIGHTS = {
    "exact": 1.00,
    "suffix": 0.95,
    "temporal": 0.85,
    "fuzzy": 0.70,
    "historical": 0.90,
}

TEMPORAL_WINDOW_MIN = 5
TEMPORAL_PRODUCT_BONUS = 0.05

MANUAL_REVIEW_THRESHOLD = 0.75
