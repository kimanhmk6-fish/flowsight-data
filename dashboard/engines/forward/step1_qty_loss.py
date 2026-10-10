"""
step1_qty_loss.py — Bước 1: ΔQ = downtime_h × r_eff.
"""


def compute_qty_loss(
    downtime_h: float,
    rate_effective: float,
    rate_source: str = "historical_median",
) -> dict:
    """
    Tính sản lượng thiếu khi máy dừng.

    Công thức: ΔQ = downtime_h × r_eff
    """
    qty_lost = downtime_h * rate_effective

    return {
        "downtime_h": downtime_h,
        "rate_effective": rate_effective,
        "rate_source": rate_source,
        "qty_lost": round(qty_lost, 1),
        "formula": "ΔQ = downtime_h × r_eff",
    }
