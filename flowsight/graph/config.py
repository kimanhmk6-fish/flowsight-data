from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
CANONICAL_DIR = DATA_DIR / "canonical"
MASTER_DIR = DATA_DIR / "master"
GRAPH_DIR = DATA_DIR / "graph"
AUDIT_DIR = DATA_DIR / "audit"

GRAPH_DIR.mkdir(parents=True, exist_ok=True)

