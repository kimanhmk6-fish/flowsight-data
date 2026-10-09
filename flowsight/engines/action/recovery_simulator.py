"""
recovery_simulator.py — Mô phỏng hiệu quả của từng phương án (Monte Carlo).
"""
import numpy as np
import pandas as pd
from dataclasses import dataclass
from flowsight.engines.config import MC_N_SIMULATIONS, MC_RANDOM_SEED




@dataclass
class SimulationResult:
    option_id: str
    option_name: str
    expected_shortfall: float
    p_late: float
    expected_delay_hours: float
    completion_time_hours: float
    n_simulations: int




# Hiệu suất bù đắp shortfall của từng phương án (tỷ lệ trên base shortfall).
# Hiệu chuẩn từ số liệu pitch F01 (slide: A=99.5%, B=26.0%, C=0.0%, D=25.5%, E=1.1%).
# Ý nghĩa nghiệp vụ: OT2 bù ~84% lượng thiếu; resequencing ~85% (tương đương OT2
# vì ưu tiên JT gấp); OT4 bù dư 115%; combo E có hiệu ứng chồng lấp nên chỉ 109%
# (không cộng dồn tuyến tính).
ACTION_EFFECTIVENESS = {
    "A": 0.00,  # Do nothing
    "B": 0.865,  # OT2
    "C": 1.177,  # OT4
    "D": 0.868,  # Resequencing
    "E": 1.113,  # Resequencing + OT2
    "F": 0.30,  # Alternative line
    "G": 0.00,  # Expedite (chỉ giao nhanh hơn, không bù sản lượng)
}


def simulate_option(
    option: dict,
    base_shortfall_qty: float,
    base_p_late: float,
    incident_duration_h: float,
    recovery_rate_per_h: float = 92.0,
    n_sim: int = MC_N_SIMULATIONS,
    seed: int = MC_RANDOM_SEED,
) -> SimulationResult:
    """Mô phỏng 1 phương án."""
    rng = np.random.default_rng(seed + hash(option["option_id"]) % 1000)


    # 1. Recovery amount: tỷ lệ bù đắp trên base shortfall
    effectiveness = ACTION_EFFECTIVENESS.get(option["option_id"], 0.0)
    recovered_qty = base_shortfall_qty * effectiveness


    # 2. Monte Carlo với uncertainty
    samples = rng.triangular(0.75, 1.0, 1.5, size=n_sim)
    actual_shortfalls = np.maximum(0, base_shortfall_qty * samples - recovered_qty)


    threshold = 10
    p_late = float(np.mean(actual_shortfalls > threshold))
    expected_shortfall = float(np.mean(actual_shortfalls))


    # 3. Delay hours
    expected_delay_hours = expected_shortfall / recovery_rate_per_h if recovery_rate_per_h > 0 else 0


    # 4. Completion time
    recovery_time_h = recovered_qty / recovery_rate_per_h if recovery_rate_per_h > 0 else 0
    completion_time = incident_duration_h + recovery_time_h


    return SimulationResult(
        option_id=option["option_id"],
        option_name=option["name"],
        expected_shortfall=round(expected_shortfall, 1),
        p_late=round(p_late, 4),
        expected_delay_hours=round(expected_delay_hours, 2),
        completion_time_hours=round(completion_time, 2),
        n_simulations=n_sim,
    )




def simulate_all_options(
    options: list,
    base_shortfall_qty: float,
    base_p_late: float,
    incident_duration_h: float,
) -> list:
    """Simulate tất cả options."""
    results = []
    for i, opt in enumerate(options):
        res = simulate_option(
            opt,
            base_shortfall_qty=base_shortfall_qty,
            base_p_late=base_p_late,
            incident_duration_h=incident_duration_h,
            seed=MC_RANDOM_SEED + i,
        )
        results.append(res)
    return results
