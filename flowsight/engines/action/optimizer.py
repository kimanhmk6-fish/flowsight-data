"""
optimizer.py — Chọn phương án tối ưu.
Objective:
    Minimize Total_Cost
    Subject to: P(late) ≤ Threshold
"""
from dataclasses import dataclass
from .cost_model import CostModel




@dataclass
class ScoredOption:
    option_id: str
    option_name: str
    p_late: float
    expected_shortfall: float
    expected_delay_hours: float
    total_cost: float
    cost_breakdown: dict
    satisfies_constraint: bool
    is_recommended: bool
    rationale: str




def score_options(
    options: list,
    simulation_results: list,
    cost_model: CostModel,
    p_late_max: float = 0.05,
    use_expedite_penalty: bool = True,
) -> list:
    """Chấm điểm từng phương án."""
    scored = []


    for opt, sim in zip(options, simulation_results):
        cost = cost_model.compute_total(
            ot_hours=opt["ot_hours"],
            n_changeovers=opt["n_changeovers"],
            n_expedite_shipments=(1 if opt["expedite"] and sim.p_late > 0 else 0),
            n_late_jts=(1 if sim.p_late >= 0.5 else 0),
            avg_delay_hours=sim.expected_delay_hours,
            use_expedite=opt["expedite"],
        )


        satisfies = sim.p_late <= p_late_max


        scored.append(ScoredOption(
            option_id=opt["option_id"],
            option_name=opt["name"],
            p_late=sim.p_late,
            expected_shortfall=sim.expected_shortfall,
            expected_delay_hours=sim.expected_delay_hours,
            total_cost=cost.total_cost,
            cost_breakdown={
                "overtime": cost.overtime_cost,
                "changeover": cost.changeover_cost,
                "shipping": cost.shipping_cost,
                "penalty": cost.penalty_cost,
            },
            satisfies_constraint=satisfies,
            is_recommended=False,
            rationale="",
        ))


    return scored




def select_optimal(scored_options: list, p_late_max: float = 0.05) -> ScoredOption:
    """Chọn phương án tối ưu."""
    satisfying = [s for s in scored_options if s.satisfies_constraint]


    if satisfying:
        optimal = min(satisfying, key=lambda s: s.total_cost)
        optimal.rationale = (
            f"Thỏa constraint P(late) ≤ {p_late_max*100:.0f}% "
            f"với chi phí thấp nhất ({optimal.total_cost:,.0f} VND)"
        )
    else:
        optimal = min(scored_options, key=lambda s: s.p_late)
        optimal.rationale = (
            f"Không có phương án nào thỏa P(late) ≤ {p_late_max*100:.0f}%. "
            f"Chọn phương án có P(late) thấp nhất ({optimal.p_late*100:.1f}%)"
        )


    optimal.is_recommended = True
    return optimal




def rank_options_by_cost(scored_options: list) -> list:
    return sorted(scored_options, key=lambda s: s.total_cost)




def rank_options_by_risk(scored_options: list) -> list:
    return sorted(scored_options, key=lambda s: s.p_late)
