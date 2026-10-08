"""
step2_time_to_starve.py — Bước 2: T_starve = WIP / throughput (Little's Law).
"""


def compute_time_to_starve(
    wip_buffer_qty: float,
    downstream_rate: float,
    note: str = "",
) -> dict:
    """
    Tính thời gian downstream chạy được trước khi hết WIP.
    """
    if downstream_rate <= 0:
        return {
            "wip_buffer_qty": wip_buffer_qty,
            "downstream_rate": downstream_rate,
            "time_to_starve_h": float("inf"),
            "note": "Downstream rate = 0",
        }

    t_starve = wip_buffer_qty / downstream_rate

    return {
        "wip_buffer_qty": wip_buffer_qty,
        "downstream_rate": downstream_rate,
        "time_to_starve_h": round(t_starve, 2),
        "note": note,
        "formula": "T_starve = WIP / throughput (Little's Law)",
    }
