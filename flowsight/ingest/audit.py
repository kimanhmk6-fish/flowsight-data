"""
audit.py — Audit trail tổng hợp cho 11A.
"""
import json
from .config import AUDIT_DIR


def generate_11a_audit_report() -> dict:
    """Tổng hợp audit từ các log files."""
    report = {
        "step": "11A",
        "artifacts": {},
        "summary": {},
    }

    for name, fname in [
        ("ingestion", "ingestion_log.json"),
        ("schema_mapping", "schema_mapping_log.json"),
        ("id_normalization", "id_normalization_log.json"),
        ("value_normalization", "value_normalization_log.json"),
    ]:
        path = AUDIT_DIR / fname
        if path.exists():
            with open(path, encoding="utf-8") as f:
                report["artifacts"][name] = json.load(f)

    ingestion = report["artifacts"].get("ingestion", {})
    schema_map = report["artifacts"].get("schema_mapping", [])
    id_norm = report["artifacts"].get("id_normalization", {})

    report["summary"] = {
        "sources_ingested": len(ingestion.get("sources", {})),
        "sources_success": sum(
            1 for s in ingestion.get("sources", {}).values()
            if s.get("status") == "success"
        ),
        "total_rows": sum(
            s.get("rows", 0) for s in ingestion.get("sources", {}).values()
        ),
        "columns_renamed": sum(
            len(m.get("renamed_columns", {})) for m in schema_map
        ) if isinstance(schema_map, list) else 0,
        "id_cols_normalized": sum(
            len(v.get("normalized_columns", [])) for v in id_norm.values()
        ) if isinstance(id_norm, dict) else 0,
    }

    # Lưu report
    with open(AUDIT_DIR / "step_11a_audit.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)

    return report


if __name__ == "__main__":
    report = generate_11a_audit_report()
    print(json.dumps(report["summary"], indent=2, ensure_ascii=False))
