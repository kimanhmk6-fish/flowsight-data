"""
what_if_engine.py
"""
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from .cost_model import CostModel
from .options_generator import generate_standard_options
from .recovery_simulator import simulate_all_options
from .optimizer import score_options, select_optimal
from .sensitivity import sensitivity_to_threshold, sensitivity_to_cost


class WhatIfEngine:
    def __init__(self, cost_config_path: Optional[Path] = None):
        self.cost_model = CostModel(cost_config_path)

    def simulate(self, prediction, p_late_max=0.05, has_alternative_line=True):
        incident_duration_h = prediction.get("duration_h", 8.0)
        summary = prediction.get("summary", {})
        jts_late = summary.get("jts_late", [])

        if jts_late:
            base_shortfall = jts_late[0].get("shortfall_qty", 0)
            base_p_late = jts_late[0].get("p_late", 0)
        else:
            base_shortfall = summary.get("total_shortage", 0) or 0
            base_p_late = 0.5 if base_shortfall > 100 else 0.1

        # BƯỚC 1: Generate options (list of ActionOption dataclass)
        options_obj = generate_standard_options(incident_duration_h, has_alternative_line)

        # BƯỚC 2: Convert sang list of dict NGAY TỪ ĐẦU
        # -> để simulator + optimizer + sensitivity dùng kiểu dict[]
        options = [asdict(o) for o in options_obj]

        # BƯỚC 3: Simulate (dùng dict)
        sim_results = simulate_all_options(options, base_shortfall, base_p_late, incident_duration_h)

        # BƯỚC 4: Score (dùng dict)
        scored = score_options(options, sim_results, self.cost_model, p_late_max=p_late_max)

        # BƯỚC 5: Select optimal
        optimal = select_optimal(scored, p_late_max=p_late_max)

        # BƯỚC 6: Sensitivity (dùng dict)
        try:
            sens_thr = sensitivity_to_threshold(options, sim_results, self.cost_model)
            sens_cost = sensitivity_to_cost(options, sim_results, self.cost_model, parameter="overtime")
        except Exception as e:
            print(f"    WARN Sensitivity failed: {e}")
            sens_thr = None
            sens_cost = None

        # BƯỚC 7: Build result
        return {
            "case_id": prediction.get("case_id"),
            "incident_id": prediction.get("incident_id"),
            "p_late_max": p_late_max,
            "base_context": {
                "incident_duration_h": incident_duration_h,
                "base_shortfall_qty": base_shortfall,
                "base_p_late": base_p_late,
            },
            "options": options,  # đã là list of dict
            "simulations": [asdict(s) for s in sim_results],
            "scored": [asdict(s) for s in scored],
            "optimal": asdict(optimal),
            "sensitivity": {
                "threshold": asdict(sens_thr) if sens_thr else {},
                "cost": asdict(sens_cost) if sens_cost else {},
            },
        }
