from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
STAGED_DIR = DATA_DIR / "staged"
ALIGNED_DIR = DATA_DIR / "aligned"
AUDIT_DIR = DATA_DIR / "audit"

for d in [ALIGNED_DIR, AUDIT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ============================================================
# ANCHOR EVENT DEFINITIONS
# ============================================================
# Anchor = sự kiện xuất hiện ở 2 nguồn với timestamp có thể so sánh.
ANCHOR_PAIRS = [
    {
        "name": "QR_vs_IPC",
        "reference": {"source": "SRC-03_qr", "ts_col": "ts_raw", "id_col": "lot_ref_norm"},
        "target":    {"source": "SRC-02_ipc", "ts_col": "ts_raw", "id_col": "lot_ref_norm"},
        "match_on":  ["lot_ref_norm"],
        "max_diff_min": 15,
    },
    {
        "name": "QR_vs_QC_AUTO",
        "reference": {"source": "SRC-03_qr", "ts_col": "ts_raw", "id_col": "lot_ref_norm"},
        "target":    {"source": "SRC-04_qc_auto", "ts_col": "ts_raw", "id_col": "lot_ref_norm"},
        "match_on":  ["lot_ref_norm"],
        "max_diff_min": 60,
    },
]

# ============================================================
# ALIGNMENT PARAMETERS
# ============================================================
MIN_ANCHOR_EVENTS = 5          # Cần tối thiểu 5 anchor để estimate offset
MAD_THRESHOLD_SEC = 30         # MAD > 30s → flag warning
OUTLIER_THRESHOLD_MAD = 3.5    # Loại bỏ anchor nằm ngoài 3.5×MAD
SYSTEMATIC_OFFSET_THRESHOLD_SEC = 30  # > 30s → coi là systematic offset

# ============================================================
# DRIFT DETECTION
# ============================================================
MIN_ANCHORS_PER_WINDOW = 3
DRIFT_LINEARITY_THRESHOLD = 0.7
