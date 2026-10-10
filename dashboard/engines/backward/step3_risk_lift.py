"""
step3_risk_lift.py — Bước 3: Risk Lift.
Công thức:
    P(NG|F) = a / (a + b)
    P(NG)   = (a + c) / n
    Lift    = P(NG|F) / P(NG)
"""
from dataclasses import dataclass


@dataclass
class LiftResult:
    candidate_id: str
    p_ng_given_f: float
    p_ng: float
    lift: float
    is_significant: bool
    interpretation: str


def compute_risk_lift(fisher_result, min_lift: float = 2.0) -> LiftResult:
    """Tính Lift từ FisherResult."""
    t = fisher_result.contingency_table
    a, b, c, d = t["a"], t["b"], t["c"], t["d"]

    n_with_f = a + b
    p_ng_given_f = a / n_with_f if n_with_f > 0 else 0.0

    n_total = a + b + c + d
    p_ng = (a + c) / n_total if n_total > 0 else 0.0

    if p_ng == 0:
        lift = 0.0
    else:
        lift = p_ng_given_f / p_ng

    is_significant = (lift >= min_lift) and (fisher_result.p_value < 0.05)

    if lift >= 5:
        interp = f"Rất mạnh (lift={lift:.2f})"
    elif lift >= 2:
        interp = f"Mạnh (lift={lift:.2f})"
    elif lift >= 1.5:
        interp = f"Trung bình (lift={lift:.2f})"
    elif lift >= 1.0:
        interp = f"Yếu (lift={lift:.2f})"
    else:
        interp = f"Không có tác dụng bảo vệ (lift={lift:.2f})"

    return LiftResult(
        candidate_id=fisher_result.candidate_id,
        p_ng_given_f=round(p_ng_given_f, 4),
        p_ng=round(p_ng, 4),
        lift=round(lift, 3),
        is_significant=is_significant,
        interpretation=interp,
    )
