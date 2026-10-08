"""
evidence_card.py — Evidence Card cho Forward predictions.
"""
from datetime import datetime


def build_forward_evidence_card(prediction: dict) -> dict:
    """Tạo Evidence Card cho Forward prediction."""
    steps = prediction.get("steps", {})
    s1 = steps.get("step1_qty_loss", {})
    s3 = steps.get("step3_netting", {})
    s5 = steps.get("step5_monte_carlo", [{}])
    s5 = s5[0] if s5 else {}

    jts_late = prediction.get("summary", {}).get("jts_late", [])

    conclusion_text = (
        f"Incident {prediction.get('incident_id')} tại {prediction.get('station_id')} "
        f"dừng {prediction.get('duration_h')}h → mất {s1.get('qty_lost', 0):.0f} sp. "
        f"Netting cho thấy tổng thiếu hụt {s3.get('total_shortage', 0):.0f} sp. "
        f"Monte Carlo: P(late) = {s5.get('p_late', 0)*100:.1f}%."
    )

    return {
        "claim_id": f"CLAIM-{prediction.get('case_id')}",
        "item": f"Impact of {prediction.get('incident_id', prediction.get('case_id'))}",
        "formula_used": [
            "ΔQ = downtime_h × r_eff",
            "T_starve = WIP / throughput",
            "I(t) = I(t-1) + P(t) - S(t)",
            "Shortfall ~ Triangular(a, m, b) × base",
        ],
        "inputs": [
            {"name": "downtime_h", "value": prediction.get("duration_h"), "unit": "hours"},
            {"name": "rate_effective", "value": s1.get("rate_effective"), "unit": "sp/h",
             "source": s1.get("rate_source")},
            {"name": "qty_lost", "value": s1.get("qty_lost"), "unit": "sp"},
            {"name": "opening_inventory", "value": s3.get("opening_inventory"), "unit": "sp"},
        ],
        "conclusion": {
            "text": conclusion_text,
            "jts_late": jts_late,
            "total_shortage": int(s3.get("total_shortage", 0)),
            "p_late": s5.get("p_late", 0),
        },
        "confidence": 0.86,
        "grade": "B",
        "evidence_chain": [
            {"type": "step1_qty_loss", "value": s1.get("qty_lost")},
            {"type": "step3_netting", "first_shortage_day": s3.get("first_shortage_day")},
            {"type": "step5_monte_carlo", "p_late": s5.get("p_late")},
        ],
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }
