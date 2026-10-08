"""
spc_utils.py — SPC Nelson Rules + Cpk trend.
"""
import numpy as np
import pandas as pd


# ============================================================
# NELSON RULES (1, 2, 3, 5)
# ============================================================
def check_nelson_rule_1(values: np.ndarray, mean: float, std: float) -> list:
    """Rule 1: 1 điểm ngoài 3σ."""
    if std == 0:
        return []
    return [{"index": i, "value": float(v), "rule": "NELSON_1"}
            for i, v in enumerate(values) if abs(v - mean) > 3 * std]


def check_nelson_rule_2(values: np.ndarray, mean: float, window: int = 9) -> list:
    """Rule 2: 9 điểm liên tiếp cùng phía mean."""
    violations = []
    if len(values) < window:
        return violations
    for i in range(len(values) - window + 1):
        w = values[i:i + window]
        if all(v > mean for v in w) or all(v < mean for v in w):
            violations.append({
                "index": i, "window_end": i + window - 1,
                "rule": "NELSON_2",
                "direction": "above" if w[0] > mean else "below",
            })
    return violations


def check_nelson_rule_3(values: np.ndarray, window: int = 6) -> list:
    """Rule 3: 6 điểm tăng/giảm liên tiếp."""
    violations = []
    if len(values) < window:
        return violations
    for i in range(len(values) - window + 1):
        w = values[i:i + window]
        diffs = np.diff(w)
        if all(d > 0 for d in diffs) or all(d < 0 for d in diffs):
            violations.append({
                "index": i, "window_end": i + window - 1,
                "rule": "NELSON_3",
                "direction": "increasing" if diffs[0] > 0 else "decreasing",
            })
    return violations


def check_nelson_rule_5(values: np.ndarray, mean: float, std: float) -> list:
    """Rule 5: 2/3 điểm ngoài 2σ cùng phía."""
    if std == 0:
        return []
    violations = []
    threshold = 2 * std
    for i in range(len(values) - 2):
        w = values[i:i + 3]
        above = sum(1 for v in w if v - mean > threshold)
        below = sum(1 for v in w if mean - v > threshold)
        if above >= 2 or below >= 2:
            violations.append({
                "index": i, "window_end": i + 2,
                "rule": "NELSON_5",
                "direction": "above" if above >= 2 else "below",
            })
    return violations


def check_all_nelson_rules(values: np.ndarray) -> dict:
    """Chạy tất cả rules."""
    if len(values) == 0:
        return {"violations": [], "n_violations": 0, "rules_triggered": []}

    values = np.array(values, dtype=float)
    values = values[~np.isnan(values)]

    if len(values) < 3:
        return {"violations": [], "n_violations": 0, "rules_triggered": []}

    mean = float(np.mean(values))
    std = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0

    all_violations = []
    all_violations.extend(check_nelson_rule_1(values, mean, std))
    all_violations.extend(check_nelson_rule_2(values, mean))
    all_violations.extend(check_nelson_rule_3(values))
    all_violations.extend(check_nelson_rule_5(values, mean, std))

    rules_triggered = sorted(set(v["rule"] for v in all_violations))

    return {
        "violations": all_violations,
        "n_violations": len(all_violations),
        "rules_triggered": rules_triggered,
        "mean": round(mean, 4),
        "std": round(std, 4),
    }


def compute_cpk_trend(values: np.ndarray, lsl: float, usl: float) -> dict:
    """Tính Cp, Cpk và trend signal."""
    if len(values) < 5:
        return {"cpk": None, "trend": "INSUFFICIENT_DATA"}

    values = np.array(values, dtype=float)
    mean = float(np.mean(values))
    std = float(np.std(values, ddof=1))

    if std == 0:
        return {"cpk": None, "trend": "ZERO_VARIANCE"}

    cp = (usl - lsl) / (6 * std)
    cpu = (usl - mean) / (3 * std)
    cpl = (mean - lsl) / (3 * std)
    cpk = min(cpu, cpl)

    half = len(values) // 2
    if half < 2:
        return {"cpk": round(cpk, 3), "trend": "STABLE"}

    mean_first = float(np.mean(values[:half]))
    mean_second = float(np.mean(values[half:]))
    delta = (min((usl - mean_second) / (3 * std), (mean_second - lsl) / (3 * std))
             - min((usl - mean_first) / (3 * std), (mean_first - lsl) / (3 * std)))

    if delta < -0.1:
        trend = "DECLINING"
    elif delta > 0.1:
        trend = "IMPROVING"
    else:
        trend = "STABLE"

    return {
        "cp": round(cp, 3), "cpk": round(cpk, 3),
        "cpu": round(cpu, 3), "cpl": round(cpl, 3),
        "mean": round(mean, 4), "std": round(std, 4),
        "trend": trend, "delta": round(delta, 3),
    }
