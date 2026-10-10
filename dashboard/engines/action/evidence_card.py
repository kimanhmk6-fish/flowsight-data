"""
evidence_card.py — Evidence Card cho Action Simulation.
"""
from datetime import datetime




def build_action_evidence_card(sim_result: dict) -> dict:
    """Tạo Evidence Card cho action simulation."""
    optimal = sim_result["optimal"]
    base = sim_result["base_context"]


    cost_rows = []
    for s in sim_result["scored"]:
        cost_rows.append({
            "option": s["option_id"],
            "name": s["option_name"],
            "p_late": s["p_late"],
            "cost": s["total_cost"],
            "satisfies": s["satisfies_constraint"],
            "recommended": s["is_recommended"],
        })


    conclusion = (
        f"Đề xuất phương án {optimal['option_id']} ({optimal['option_name']}): "
        f"P(late)={optimal['p_late']*100:.1f}% ≤ {sim_result['p_late_max']*100:.0f}%, "
        f"chi phí {optimal['total_cost']:,.0f} VND. "
        f"Lý do: {optimal['rationale']}."
    )


    return {
        "claim_id": f"CLAIM-ACTION-{sim_result.get('case_id')}",
        "item": f"Action recommendation for {sim_result.get('incident_id')}",
        "formula_used": [
            "Objective: min Total_Cost subject to P(late) ≤ threshold",
            "Total_Cost = OT_Cost + Changeover_Cost + Shipping_Cost + Penalty_Cost",
            "P(late) từ Monte Carlo 20,000 simulations",
        ],
        "context": base,
        "options_compared": cost_rows,
        "conclusion": {
            "text": conclusion,
            "recommended_option_id": optimal["option_id"],
            "recommended_option_name": optimal["option_name"],
            "p_late": optimal["p_late"],
            "total_cost": optimal["total_cost"],
            "cost_breakdown": optimal["cost_breakdown"],
        },
        "sensitivity": {
            "threshold_robust": sim_result.get("sensitivity", {}).get("threshold", {}).get("is_robust", False),
            "cost_robust": sim_result.get("sensitivity", {}).get("cost", {}).get("is_robust", False),
        },
        "confidence": 0.88,
        "grade": "B",
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }
