"""
runner_12a.py — Chạy Forward Engine cho 12 case F01-F12.
"""
import json
import time
from datetime import datetime
from pathlib import Path

from flowsight.engines.config import CASES_F, PREDICTIONS_DIR, REPORTS_DIR
from flowsight.engines.shared.graph_loader import load_canonical_tables, load_genealogy_graph
from flowsight.engines.forward.impact_engine import ForwardImpactEngine
from flowsight.engines.forward.evidence_card import build_forward_evidence_card


def run_forward_engine():
    t0 = time.time()

    print("=" * 70)
    print("  BƯỚC 12A: FORWARD IMPACT CASCADE ENGINE")
    print("=" * 70)

    # Load data
    print("\n[Load] Loading canonical tables + graph...")
    tables = load_canonical_tables()
    G = load_genealogy_graph()

    print(f"  ✓ Tables: {list(tables.keys())}")
    print(f"  ✓ Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    # Init engine
    engine = ForwardImpactEngine(tables, G)

    # Run cases
    print("\n[Predict] Running Forward Impact Cascade for 12 cases...")
    results = []
    evidence_cards = []

    for case in CASES_F:
        print(f"\n  [{case['case_id']}] Incident {case['incident_id']} "
              f"@ {case['station_id']} · {case['duration_h']}h")

        result = engine.predict(case)
        result["expected"] = case["expected"]
        results.append(result)

        # Evidence card
        card = build_forward_evidence_card(result)
        evidence_cards.append(card)

        # Save
        out_path = PREDICTIONS_DIR / "forward" / f"{case['case_id']}_prediction.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)

        # Print summary
        s = result["summary"]
        print(f"    → Qty lost: {s['qty_lost']:.0f} sp")
        print(f"    → Total shortage: {s['total_shortage']} sp")
        print(f"    → JT late: {len(s['jts_late'])}")
        print(f"    → Recommended: {s['recommended_action']}")

    # Summary report
    elapsed = time.time() - t0

    # Metrics
    n_total = len(results)
    n_with_late = sum(1 for r in results if r["summary"]["jts_late"])

    report = {
        "step": "12A_forward_engine",
        "run_at": datetime.utcnow().isoformat() + "Z",
        "elapsed_sec": round(elapsed, 2),
        "n_cases": n_total,
        "n_with_jt_late": n_with_late,
        "results": results,
        "evidence_cards": evidence_cards,
    }

    with open(REPORTS_DIR / "forward_engine_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)

    print("\n" + "=" * 70)
    print(f"  BƯỚC 12A HOÀN TẤT trong {elapsed:.2f}s")
    print(f"  Cases: {n_total}")
    print(f"  Cases with JT late: {n_with_late}")
    print(f"  Report: reports/forward_engine_report.json")
    print("=" * 70)

    return report


if __name__ == "__main__":
    run_forward_engine()