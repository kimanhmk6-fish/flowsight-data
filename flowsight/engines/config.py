"""
config.py — Config cho Intelligence Engines (Bước 12).
"""
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
CANONICAL_DIR = DATA_DIR / "canonical"
MASTER_DIR = DATA_DIR / "master"
GRAPH_DIR = DATA_DIR / "graph"
PREDICTIONS_DIR = DATA_DIR / "predictions"
REPORTS_DIR = ROOT_DIR / "reports"

for d in [PREDICTIONS_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ============================================================
# MONTE CARLO
# ============================================================
MC_N_SIMULATIONS = 20000
MC_RANDOM_SEED = 42

# ============================================================
# THRESHOLDS
# ============================================================
SHORTFALL_THRESHOLD = 10          # < 10 sp coi như không trễ
P_LATE_DEFAULT_THRESHOLD = 0.05   # 5%

# ============================================================
# DEMO CASES (F01-F12)
# ============================================================
CASES_F = [
    {"case_id": "F01", "incident_id": "INC-0001", "station_id": "STN-M2",
     "duration_h": 8.0, "start_ts": "2026-09-29T08:00:00",
     "expected": {"jt_late": ["JT-0231"], "shortfall_qty": 100}},
    {"case_id": "F02", "incident_id": "INC-0002", "station_id": "STN-M2",
     "duration_h": 4.0, "start_ts": "2026-09-30T08:00:00",
     "expected": {"jt_late": [], "shortfall_qty": 0}},
    {"case_id": "F03", "incident_id": "INC-0003", "station_id": "STN-M2",
     "duration_h": 12.0, "start_ts": "2026-10-01T08:00:00",
     "expected": {"jt_late": ["JT-0231", "JT-0235"], "shortfall_qty": 350}},
    {"case_id": "F04", "incident_id": "INC-0004", "station_id": "STN-M1",
     "duration_h": 8.0, "start_ts": "2026-10-02T08:00:00",
     "expected": {"jt_late": [], "shortfall_qty": 0}},
    {"case_id": "F05", "incident_id": "INC-0005", "station_id": "STN-HT",
     "duration_h": 8.0, "start_ts": "2026-10-03T08:00:00",
     "expected": {"jt_late": ["JT-0231"], "shortfall_qty": 100}},
    {"case_id": "F06", "incident_id": "INC-0006", "station_id": "STN-AS2",
     "duration_h": 8.0, "start_ts": "2026-10-04T08:00:00",
     "expected": {"jt_late": [], "shortfall_qty": 0}},
    {"case_id": "F07", "incident_id": "INC-0007", "station_id": "STN-T1",
     "duration_h": 8.0, "start_ts": "2026-10-05T08:00:00",
     "expected": {"jt_late": [], "shortfall_qty": 0}},
    {"case_id": "F08", "incident_id": "INC-0008", "station_id": "STN-M2",
     "duration_h": 8.0, "start_ts": "2026-10-05T16:00:00",
     "expected": {"jt_late": ["JT-0232"], "shortfall_qty": 150}},
    {"case_id": "F09", "incident_id": "INC-0009", "station_id": "STN-M2",
     "duration_h": 8.0, "start_ts": "2026-10-06T08:00:00",
     "expected": {"jt_late": ["JT-0231", "JT-0232"], "shortfall_qty": 180}},
    {"case_id": "F10", "incident_id": "INC-0010", "station_id": "STN-M2",
     "duration_h": 8.0, "start_ts": "2026-10-07T08:00:00",
     "expected": {"jt_late": ["JT-0231"], "shortfall_qty": 120}},
    {"case_id": "F11", "incident_id": "INC-0011", "station_id": "STN-M2",
     "duration_h": 4.0, "start_ts": "2026-10-08T08:00:00",
     "expected": {"jt_late": ["JT-0231"], "shortfall_qty": 60}},
    {"case_id": "F12", "incident_id": "INC-0012", "station_id": "STN-M2",
     "duration_h": 8.0, "start_ts": "2026-10-09T08:00:00",
     "expected": {"jt_late": ["JT-0231", "JT-0235"], "shortfall_qty": 220}},
]
