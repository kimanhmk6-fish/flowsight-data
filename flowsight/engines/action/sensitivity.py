"""
sensitivity.py — Phân tích độ nhạy.
"""
from dataclasses import dataclass




@dataclass
class SensitivityResult:
    parameter: str
    variations: list
    is_robust: bool
    note: str




def sensitivity_to_threshold(
    options: list,
    simulation_results: list,
    cost_model,
    thresholds: list = None,
) -> SensitivityResult:
    """Test các ngưỡng P(late) khác nhau."""
    if thresholds is None:
        thresholds = [0.01, 0.05, 0.10, 0.20]


    from .optimizer import score_options, select_optimal


    variations = []
    for thr in thresholds:
        scored = score_options(
            options, simulation_results, cost_model, p_late_max=thr,
        )
        optimal = select_optimal(scored, p_late_max=thr)
        variations.append({
            "threshold": thr,
            "optimal_option_id": optimal.option_id,
            "optimal_option_name": optimal.option_name,
            "cost": optimal.total_cost,
            "p_late": optimal.p_late,
        })


    opt_ids = set(v["optimal_option_id"] for v in variations)
    is_robust = len(opt_ids) == 1


    note = ""
    if is_robust:
        note = f"Recommendation ổn định: option {list(opt_ids)[0]}"
    else:
        note = f"Recommendation thay đổi theo threshold: {opt_ids}"


    return SensitivityResult(
        parameter="p_late_threshold",
        variations=variations,
        is_robust=is_robust,
        note=note,
    )




def sensitivity_to_cost(
    options: list,
    simulation_results: list,
    cost_model,
    parameter: str = "overtime",
    variations_pct: list = None,
) -> SensitivityResult:
    """Test độ nhạy của cost parameter."""
    if variations_pct is None:
        variations_pct = [-0.20, -0.10, 0, 0.10, 0.20]


    from .optimizer import score_options, select_optimal


    variations = []
    original_config = {k: dict(v) for k, v in cost_model.config.items() if isinstance(v, dict)}


    for pct in variations_pct:
        multiplier = 1 + pct


        if parameter == "overtime":
            base = original_config["labor"]["operator_hourly_rate"]
            cost_model.config["labor"]["operator_hourly_rate"] = base * multiplier
        elif parameter == "changeover":
            base = original_config["changeover"]["fixed_cost"]
            cost_model.config["changeover"]["fixed_cost"] = base * multiplier


        scored = score_options(options, simulation_results, cost_model)
        optimal = select_optimal(scored)


        variations.append({
            "pct_change": pct,
            "optimal_option_id": optimal.option_id,
            "cost": optimal.total_cost,
        })


        # Reset
        cost_model.config = {k: dict(v) if isinstance(v, dict) else v
                              for k, v in original_config.items()}


    opt_ids = set(v["optimal_option_id"] for v in variations)
    is_robust = len(opt_ids) == 1


    return SensitivityResult(
        parameter=parameter,
        variations=variations,
        is_robust=is_robust,
        note=f"Robust: {is_robust}" if is_robust else f"Changes: {opt_ids}",
    )
