"""
step5_monte_carlo.py — Bước 5: Monte Carlo (uncertainty quantification).
"""
import numpy as np
from flowsight.engines.config import MC_N_SIMULATIONS, MC_RANDOM_SEED


def simulate_shortfall(
    base_shortfall_qty: float,
    n_sim: int = MC_N_SIMULATIONS,
    seed: int = MC_RANDOM_SEED,
    distribution: str = "triangular",
    dist_params: tuple = (0.75, 1.0, 1.5),
) -> dict:
    """
    Monte Carlo: downtime không chắc chắn → shortfall có phân phối.

    Distribution: Triangular(a, mode, b) × base_shortfall_qty
    """
    rng = np.random.default_rng(seed)

    if distribution == "triangular":
        samples = rng.triangular(dist_params[0], dist_params[1], dist_params[2], size=n_sim)
    elif distribution == "normal":
        samples = rng.normal(dist_params[0], dist_params[1], size=n_sim)
        samples = np.maximum(samples, 0)
    else:
        samples = np.ones(n_sim)

    actual_shortfalls = np.maximum(0, base_shortfall_qty * samples)

    threshold = 10

    return {
        "n_simulations": n_sim,
        "base_shortfall": base_shortfall_qty,
        "expected_shortage": round(float(np.mean(actual_shortfalls)), 1),
        "std_shortage": round(float(np.std(actual_shortfalls)), 1),
        "p50_shortage": round(float(np.percentile(actual_shortfalls, 50)), 1),
        "p90_shortage": round(float(np.percentile(actual_shortfalls, 90)), 1),
        "p_late": round(float(np.mean(actual_shortfalls > threshold)), 4),
        "distribution": distribution,
        "dist_params": list(dist_params),
    }
