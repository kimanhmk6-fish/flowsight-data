"""
step3_netting.py — Bước 3: I(t) = I(t-1) + P(t) - S(t) (MRP/ATP netting).
"""
import pandas as pd


def compute_netting(
    opening_inventory: float,
    baseline_production: list,
    baseline_shipment: list,
    incident_production: list,
    days: int = 14,
) -> dict:
    """
    Time-Phased Netting.

    Args:
        opening_inventory: Tồn kho đầu
        baseline_production: [P(0), P(1), ...] baseline
        baseline_shipment: [S(0), S(1), ...] baseline
        incident_production: [P'(0), P'(1), ...] incident
        days: số ngày horizon
    """
    baseline_trajectory = [opening_inventory]
    incident_trajectory = [opening_inventory]

    for d in range(min(days, len(baseline_production))):
        p_base = baseline_production[d] if d < len(baseline_production) else 0
        s = baseline_shipment[d] if d < len(baseline_shipment) else 0
        baseline_trajectory.append(baseline_trajectory[-1] + p_base - s)

    for d in range(min(days, len(incident_production))):
        p_inc = incident_production[d] if d < len(incident_production) else 0
        s = baseline_shipment[d] if d < len(baseline_shipment) else 0
        incident_trajectory.append(incident_trajectory[-1] + p_inc - s)

    # Ngày đầu tiên thiếu (< 0)
    first_shortage_day = None
    for d, v in enumerate(incident_trajectory):
        if v < 0:
            first_shortage_day = d
            break

    # Tổng thiếu hụt
    total_shortage = sum(abs(v) for v in incident_trajectory if v < 0)

    return {
        "opening_inventory": opening_inventory,
        "baseline_trajectory": baseline_trajectory,
        "incident_trajectory": incident_trajectory,
        "first_shortage_day": first_shortage_day,
        "total_shortage": round(total_shortage, 1),
        "formula": "I(t) = I(t-1) + P(t) - S(t)",
    }
