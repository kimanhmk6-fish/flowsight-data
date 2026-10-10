import json
from datetime import datetime
from .config import AUDIT_DIR


def save_reconstruction_audit(report: dict) -> dict:
    audit = {
        "step": "11C-1_relationship_reconstruction",
        "run_at": datetime.utcnow().isoformat() + "Z",
        **report,
    }
    with open(AUDIT_DIR / "reconstruction_audit.json", "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2, ensure_ascii=False, default=str)
    return audit

