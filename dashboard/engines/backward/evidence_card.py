"""
evidence_card.py — Evidence Card cho Backward.
"""
from datetime import datetime


def build_backward_evidence_card(result: dict) -> dict:
    """Tạo Evidence Card cho 1 diagnosis."""

    if result["status"] == "INSUFFICIENT_EVIDENCE":
        return {
            "claim_id": f"CLAIM-{result['case_id']}",
            "item": f"Root cause of {result['lot_id_ng']}",
            "formula_used": [
                "Reverse BFS on genealogy",
                "Fisher Exact Test",
                "Risk Lift = P(NG|F) / P(NG)",
                "Score = w1·norm(-log p) + w2·norm(lift) + w3·signal",
            ],
            "conclusion": {
                "text": result.get("message", "Chưa đủ bằng chứng"),
                "top_causes": [],
            },
            "confidence": 0.0,
            "grade": "N/A",
            "status": "INSUFFICIENT_EVIDENCE",
            "generated_at": datetime.utcnow().isoformat() + "Z",
        }

    top1 = result["top_causes"][0] if result["top_causes"] else None

    if top1:
        conclusion_text = (
            f"Nguyên nhân hàng đầu: {top1['candidate_id']} "
            f"({top1['candidate_type']}) với lift={top1['lift']:.2f}, "
            f"p={top1['p_value']:.4f}. "
            f"Cần cách ly {len(result.get('isolate_lots', []))} lots "
            f"(giảm {result.get('containment_reduction', 0)*100:.0f}% so với baseline)."
        )
    else:
        conclusion_text = "Không có candidate"

    return {
        "claim_id": f"CLAIM-{result['case_id']}",
        "item": f"Root cause of {result['lot_id_ng']}",
        "formula_used": [
            "Reverse BFS on genealogy",
            "Fisher Exact Test (2×2 contingency)",
            "Risk Lift = P(NG|F) / P(NG)",
            "Score = w1·norm(-log p) + w2·norm(lift) + w3·signal",
        ],
        "inputs": {
            "lot_id_ng": result["lot_id_ng"],
            "qc_station": result.get("qc_station"),
            "qc_characteristic": result.get("qc_characteristic"),
            "n_candidates": result.get("n_candidates", 0),
        },
        "conclusion": {
            "text": conclusion_text,
            "top_causes": result["top_causes"],
            "isolate_count": len(result.get("isolate_lots", [])),
            "reduction_pct": result.get("containment_reduction", 0),
        },
        "confidence": result.get("confidence", 0.0),
        "grade": "B",
        "evidence_chain": result.get("evidence_chain", []),
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }
