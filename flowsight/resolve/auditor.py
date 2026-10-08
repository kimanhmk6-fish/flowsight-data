import json
from datetime import datetime
from .config import AUDIT_DIR


def save_resolution_audit(mapping_df, unresolved_df) -> dict:
    audit = {
        "step": "11B-2_entity_resolution",
        "run_at": datetime.utcnow().isoformat() + "Z",
        "total_aliases": len(mapping_df),
        "resolved": int(mapping_df["canonical_id"].notna().sum()),
        "needs_review": int(mapping_df["needs_review"].sum()),
        "method_breakdown": mapping_df.groupby("method").size().to_dict(),
        "confidence_distribution": {
            "0.9-1.0": int(((mapping_df["confidence"] >= 0.9) & (mapping_df["confidence"] <= 1.0)).sum()),
            "0.75-0.9": int(((mapping_df["confidence"] >= 0.75) & (mapping_df["confidence"] < 0.9)).sum()),
            "0.5-0.75": int(((mapping_df["confidence"] >= 0.5) & (mapping_df["confidence"] < 0.75)).sum()),
            "<0.5": int((mapping_df["confidence"] < 0.5).sum()),
        },
        "unresolved_count": len(unresolved_df),
    }

    with open(AUDIT_DIR / "entity_resolution_audit.json", "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2, ensure_ascii=False, default=str)
    return audit
