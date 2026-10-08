"""
runner_12c.py — Chạy What-if Engine cho các case F01-F12.
"""
import json
import time
from pathlib import Path
from datetime import datetime


from flowsight.engines.config import PREDICTIONS_DIR, REPORTS_DIR
from flowsight.engines.action.what_if_engine import WhatIfEngine
from flowsight.engines.action.evidence_card import build_action_evidence_card




def run_what_if_engine():
    t0 = time.time()


    print("=" * 70)
    print("  BƯỚC 12C: ACTION SIMULATOR + WHAT-IF")
    print("=" * 70)


    # Init engine
    engine = WhatIfEngine()


    # Load forward predictions
    print("\n[Load] Loading forward predictions...")
    forward_dir = PREDICTIONS_DIR / "forward"
    predictions = {}


    if forward_dir.exists():
        for f in forward_dir.glob("F*_prediction.json"):
            case_id = f.stem.replace("_prediction", "")
            with open(f, encoding="utf-8") as fp:
                predictions[case_id] = json.load(fp)


    print(f"  ✓ Loaded {len(predictions)} forward predictions")


    if not predictions:
        print("\n  ⚠ Không có forward predictions. Chạy 12A trước:")
        print("    python -m flowsight.engines.runner_12a")
        return {}


    # Simulate cho mỗi case
    print("\n[Simulate] Running What-if for each case...")
    results = []
    evidence_cards = []


    for case_id, pred in sorted(predictions.items()):
        print(f"\n  [{case_id}] Simulating...")


        try:
            sim = engine.simulate(pred, p_late_max=0.05)
            sim["case_id"] = case_id
            results.append(sim)


            card = build_action_evidence_card(sim)
            evidence_cards.append(card)


            # Save
            out_path = PREDICTIONS_DIR / "what_if" / f"{case_id}_what_if.json"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(sim, f, indent=2, ensure_ascii=False, default=str)


            # Print summary
            opt = sim["optimal"]
            print(f"    → Recommended: {opt['option_id']} ({opt['option_name']})")
            print(f"    → P(late): {opt['p_late']*100:.2f}%")
            print(f"    → Cost: {opt['total_cost']:,.0f} VND")


        except Exception as e:
            print(f"    ✗ FAILED: {e}")
            continue


    # Save report
    elapsed = time.time() - t0


    report = {
        "step": "12C_what_if",
        "run_at": datetime.utcnow().isoformat() + "Z",
        "elapsed_sec": round(elapsed, 2),
        "n_cases": len(results),
        "results": results,
        "evidence_cards": evidence_cards,
    }


    with open(REPORTS_DIR / "action_engine_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)


    print("\n" + "=" * 70)
    print(f"  BƯỚC 12C HOÀN TẤT trong {elapsed:.2f}s")
    print(f"  Cases simulated: {len(results)}")
    print(f"  Report: reports/action_engine_report.json")
    print("=" * 70)


    return report




if __name__ == "__main__":
    run_what_if_engine()
