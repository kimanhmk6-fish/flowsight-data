"""
runner_12b.py — Chạy Backward Engine cho 8 case R01-R08.
"""
import json
import time
from datetime import datetime

from flowsight.engines.config import PREDICTIONS_DIR, REPORTS_DIR
from flowsight.engines.shared.graph_loader import load_canonical_tables, load_genealogy_graph
from flowsight.engines.backward.cause_engine import BackwardCauseEngine
from flowsight.engines.backward.evidence_card import build_backward_evidence_card


CASES_R = [
    {
        "case_id": "R01", "incident_id": "INC-0013", "lot_id_ng": "LOT-0403",
        "qc_station": "STN-LAB", "qc_characteristic": "Lực ép",
        "expected_cause": "BATCH-HT-B07", "expected_type": "BATCH",
    },
    {
        "case_id": "R02", "incident_id": "INC-0014", "lot_id_ng": "LOT-0002",
        "qc_station": "STN-T1", "qc_characteristic": "Đường kính trục",
        "expected_cause": "STN-M1", "expected_type": "MACHINE",
    },
    {
        "case_id": "R03", "incident_id": "INC-0015", "lot_id_ng": "LOT-0401",
        "qc_station": "STN-LAB", "qc_characteristic": "Độ cứng",
        "expected_cause": "STN-HT", "expected_type": "PROCESS",
    },
    {
        "case_id": "R04", "incident_id": "INC-0016", "lot_id_ng": "LOT-0240",
        "qc_station": "STN-AS2", "qc_characteristic": "Lực ép",
        "expected_cause": "STN-AS2", "expected_type": "HUMAN",
    },
    {
        "case_id": "R05", "incident_id": "INC-0017", "lot_id_ng": "LOT-0403",
        "qc_station": "STN-LAB", "qc_characteristic": "Lực ép",
        "expected_cause": "LABEL_DUPLICATION", "expected_type": "DATA_QUALITY",
    },
    {
        "case_id": "R06", "incident_id": "INC-0018", "lot_id_ng": "LOT-0232",
        "qc_station": "STN-AS2", "qc_characteristic": "Lực ép",
        "expected_cause": "COMBINED", "expected_type": "COMBINED",
    },
    {
        "case_id": "R07", "incident_id": "INC-0019", "lot_id_ng": "LOT-0300",
        "qc_station": "STN-LAB", "qc_characteristic": "Lực ép",
        "expected_cause": "INSUFFICIENT_EVIDENCE", "expected_type": "UNKNOWN",
    },
    {
        "case_id": "R08", "incident_id": "INC-0020", "lot_id_ng": "LOT-0235",
        "qc_station": "STN-SHP", "qc_characteristic": "Lực ép",
        "expected_cause": "SUPPLIER_MAT", "expected_type": "MATERIAL",
    },
]


def run_backward_engine():
    t0 = time.time()

    print("=" * 70)
    print("  BƯỚC 12B: BACKWARD CAUSE RANKING ENGINE")
    print("=" * 70)

    # Load data
    print("\n[Load] Loading canonical tables + graph...")
    tables = load_canonical_tables()
    G = load_genealogy_graph()

    print(f"  ✓ Tables: {list(tables.keys())}")
    print(f"  ✓ Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    # Init engine
    engine = BackwardCauseEngine(tables, G)

    # Run cases
    print("\n[Diagnose] Running Backward Cause Ranking for 8 cases...")
    results = []
    evidence_cards = []

    for case in CASES_R:
        print(f"\n  [{case['case_id']}] Lô NG: {case['lot_id_ng']}")

        result = engine.diagnose(case)
        result["expected_cause"] = case["expected_cause"]
        result["expected_type"] = case["expected_type"]
        result["case_id"] = case["case_id"]
        results.append(result)

        card = build_backward_evidence_card(result)
        evidence_cards.append(card)

        # Save
        out_path = PREDICTIONS_DIR / "backward" / f"{case['case_id']}_prediction.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)

        # Print summary
        if result["status"] == "INSUFFICIENT_EVIDENCE":
            print(f"    → Status: INSUFFICIENT_EVIDENCE")
            print(f"    → Expected: {case['expected_cause']}")
        else:
            top1 = result["top_causes"][0]
            print(f"    → Top-1: {top1['candidate_id']} "
                  f"({top1['candidate_type']}, score={top1['score']:.3f}, "
                  f"p={top1['p_value']:.4f}, lift={top1['lift']:.2f})")
            print(f"    → Isolate: {len(result.get('isolate_lots', []))} lots "
                  f"(reduction {result.get('containment_reduction', 0)*100:.1f}%)")

    # Summary
    elapsed = time.time() - t0

    # Compute accuracy
    top1_correct = 0
    top3_correct = 0

    for r in results:
        exp = r["expected_cause"]
        if r["status"] == "INSUFFICIENT_EVIDENCE":
            if exp == "INSUFFICIENT_EVIDENCE":
                top1_correct += 1
                top3_correct += 1
        else:
            top1_id = r["top_causes"][0]["candidate_id"] if r["top_causes"] else ""
            top3_ids = [tc["candidate_id"] for tc in r["top_causes"][:3]]

            if exp == top1_id or exp in top1_id:
                top1_correct += 1
            if any(exp in tcid or exp == tcid for tcid in top3_ids):
                top3_correct += 1

    top1_acc = top1_correct / len(results) if results else 0
    top3_acc = top3_correct / len(results) if results else 0

    report = {
        "step": "12B_backward_engine",
        "run_at": datetime.utcnow().isoformat() + "Z",
        "elapsed_sec": round(elapsed, 2),
        "n_cases": len(results),
        "top1_accuracy": round(top1_acc, 3),
        "top3_accuracy": round(top3_acc, 3),
        "results": results,
        "evidence_cards": evidence_cards,
    }

    with open(REPORTS_DIR / "backward_engine_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)

    print("\n" + "=" * 70)
    print(f"  BƯỚC 12B HOÀN TẤT trong {elapsed:.2f}s")
    print(f"  Cases: {len(results)}")
    print(f"  Top-1 Accuracy: {top1_acc:.1%}")
    print(f"  Top-3 Accuracy: {top3_acc:.1%}")
    print(f"  Report: reports/backward_engine_report.json")
    print("=" * 70)

    return report


if __name__ == "__main__":
    run_backward_engine()
