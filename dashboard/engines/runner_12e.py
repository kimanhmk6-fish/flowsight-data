"""
runner_12e.py — BƯỚC 12E: Validation & Benchmark tổng hợp.

Đọc predictions của 12A (forward) + 12B (backward), tính metrics kiểm chứng
so với ground truth, xuất báo cáo gộp 24 case.

Metrics (định nghĩa trong docstring từng hàm):
- Forward: jt_set_accuracy, f1_micro (JT late), mape_shortfall, brier_p_late
- Backward: top1_accuracy, top3_accuracy
- So sánh với target trên slide (F1≥0.85, MAPE≤10%, Brier≤0.15, Top-3≥6/8).

Chạy: python -m flowsight.engines.runner_12e
"""
import json
import glob
from pathlib import Path
from datetime import datetime

import numpy as np

PRED_DIR = Path("data/predictions")
REPORTS_DIR = Path("reports")

# Target trên slide (để đối chiếu, không phải để ép số)
SLIDE_TARGETS = {
    "f1_forward": 0.85,
    "mape_shortfall": 0.10,
    "brier_p_late": 0.15,
    "top3_backward": 6 / 8,
}


def load_predictions(pattern: str) -> list:
    out = []
    for fp in sorted(glob.glob(str(PRED_DIR / pattern))):
        with open(fp, encoding="utf-8") as f:
            out.append(json.load(f))
    return out


def forward_metrics(preds: list) -> dict:
    """Metrics cho forward engine (F01–F12)."""
    tp = fp = fn = 0
    exact_match = 0
    hit = 0
    brier_terms = []
    ape_terms = []  # absolute percentage errors (shortfall)

    per_case = []
    for r in preds:
        case = r.get("case_id", "?")
        exp = r.get("expected", {})
        pred_set = set(j["jt_id"] for j in r.get("summary", {}).get("jts_late", []))
        exp_set = set(exp.get("jt_late", []))

        tp += len(pred_set & exp_set)
        fp += len(pred_set - exp_set)
        fn += len(exp_set - pred_set)

        exact = (pred_set == exp_set)
        if exact:
            exact_match += 1
        hit_case = bool(pred_set & exp_set) or (not pred_set and not exp_set)
        if hit_case:
            hit += 1

        # Brier: p_pred vs outcome (1 nếu truth có JT late)
        jts = r.get("summary", {}).get("jts_late", [])
        p_pred = max([j.get("p_late", 0) for j in jts], default=0.0)
        y = 1.0 if exp_set else 0.0
        brier_terms.append((p_pred - y) ** 2)

        # MAPE shortfall (chỉ khi expected > 0)
        s_pred = r.get("summary", {}).get("total_shortage", 0)
        s_exp = exp.get("shortfall_qty", 0) or 0
        ape = None
        if s_exp > 0:
            ape = abs(s_pred - s_exp) / s_exp
            ape_terms.append(ape)

        per_case.append({
            "case_id": case,
            "pred_jt_late": sorted(pred_set),
            "exp_jt_late": sorted(exp_set),
            "exact_match": exact,
            "hit": hit_case,
            "shortfall_pred": s_pred,
            "shortfall_exp": s_exp,
            "ape_shortfall": round(ape, 3) if ape is not None else None,
            "p_late_pred": round(p_pred, 4),
            "brier": round((p_pred - y) ** 2, 4),
        })

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    n = len(preds)

    return {
        "n_cases": n,
        "jt_set_accuracy": round(exact_match / n, 3) if n else 0,
        "jt_hit_rate": round(hit / n, 3) if n else 0,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1_micro": round(f1, 3),
        "mape_shortfall": round(float(np.mean(ape_terms)), 3) if ape_terms else None,
        "brier_p_late": round(float(np.mean(brier_terms)), 4) if brier_terms else None,
        "per_case": per_case,
    }


def backward_metrics(preds: list) -> dict:
    """Metrics cho backward engine (R01–R08)."""
    top1 = top3 = 0
    per_case = []
    for r in preds:
        case = r.get("case_id", "?")
        exp = r.get("expected_cause", "?")
        top1_id = r.get("top_cause")
        tops = [t.get("candidate_id") for t in r.get("top_causes", [])[:3]]
        m1 = (top1_id == exp)
        m3 = (exp in tops)
        if m1:
            top1 += 1
        if m3:
            top3 += 1
        per_case.append({
            "case_id": case,
            "top1_pred": top1_id,
            "expected": exp,
            "top1_match": m1,
            "top3_match": m3,
            "top3_list": tops,
        })
    n = len(preds)
    return {
        "n_cases": n,
        "top1_accuracy": round(top1 / n, 3) if n else 0,
        "top1_count": f"{top1}/{n}",
        "top3_accuracy": round(top3 / n, 3) if n else 0,
        "top3_count": f"{top3}/{n}",
        "per_case": per_case,
    }


def main():
    print("=" * 70)
    print("BƯỚC 12E: VALIDATION & BENCHMARK TỔNG HỢP")
    print("=" * 70)

    fwd = load_predictions("forward/F*_prediction.json")
    bwd = load_predictions("backward/R*_prediction.json")
    print(f"  Forward cases: {len(fwd)}, Backward cases: {len(bwd)}")

    fm = forward_metrics(fwd)
    bm = backward_metrics(bwd)

    # Đối chiếu target slide
    targets_check = {
        "f1_forward": {
            "target": SLIDE_TARGETS["f1_forward"],
            "actual": fm["f1_micro"],
            "meets": fm["f1_micro"] >= SLIDE_TARGETS["f1_forward"],
        },
        "mape_shortfall": {
            "target": SLIDE_TARGETS["mape_shortfall"],
            "actual": fm["mape_shortfall"],
            "meets": (fm["mape_shortfall"] is not None
                      and fm["mape_shortfall"] <= SLIDE_TARGETS["mape_shortfall"]),
        },
        "brier_p_late": {
            "target": SLIDE_TARGETS["brier_p_late"],
            "actual": fm["brier_p_late"],
            "meets": (fm["brier_p_late"] is not None
                      and fm["brier_p_late"] <= SLIDE_TARGETS["brier_p_late"]),
        },
        "top3_backward": {
            "target": round(SLIDE_TARGETS["top3_backward"], 3),
            "actual": bm["top3_accuracy"],
            "meets": bm["top3_accuracy"] >= SLIDE_TARGETS["top3_backward"],
        },
    }

    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "coverage_note": (
            "20 engine cases (12 forward + 8 backward). "
            "4 DQ checks (D01–D04) nằm ở pipeline 11 (validator), "
            "cộng lại thành 24 case trên slide."
        ),
        "slide_targets": SLIDE_TARGETS,
        "targets_check": targets_check,
        "forward": fm,
        "backward": bm,
    }

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS_DIR / "validation_24cases.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # CSV benchmark gọn
    import csv
    csv_path = REPORTS_DIR / "benchmark_report.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["metric", "target", "actual", "meets_target"])
        for k, v in targets_check.items():
            w.writerow([k, v["target"], v["actual"],
                        "YES" if v["meets"] else "NO"])
        w.writerow(["jt_set_accuracy", "", fm["jt_set_accuracy"], ""])
        w.writerow(["jt_hit_rate", "", fm["jt_hit_rate"], ""])
        w.writerow(["top1_backward", "", bm["top1_accuracy"], ""])

    print("\n  --- KẾT QUẢ vs TARGET SLIDE ---")
    for k, v in targets_check.items():
        status = "✓ ĐẠT" if v["meets"] else "✗ CHƯA ĐẠT"
        print(f"  {k}: target={v['target']}, actual={v['actual']} → {status}")
    print(f"\n  Forward F1-micro: {fm['f1_micro']} | hit_rate: {fm['jt_hit_rate']}")
    print(f"  Backward Top-1: {bm['top1_count']} | Top-3: {bm['top3_count']}")
    print(f"\n  Report: {out_path}")
    print(f"  CSV: {csv_path}")
    print("=" * 70)
    print("  BƯỚC 12E HOÀN TẤT")
    print("=" * 70)


if __name__ == "__main__":
    main()
