"""
step6_cutoff_check.py — Bước 6: Cut-off check.
"""
import pandas as pd


def check_cutoff(
    tables: dict,
    jt_id: str,
    incident_start_ts: pd.Timestamp,
    incident_duration_h: float,
    recovery_time_h: float,
) -> dict:
    """
    Kiểm tra JT có kịp ship không.
    """
    shipment = tables.get("shipment", pd.DataFrame())

    if len(shipment) == 0:
        return {"jt_id": jt_id, "status": "no_shipment"}

    jt_ship = shipment[shipment["jt_id"] == jt_id]
    if len(jt_ship) == 0:
        return {"jt_id": jt_id, "status": "no_shipment_for_jt"}

    row = jt_ship.iloc[0]
    truck_time = pd.to_datetime(row["truck_time"])
    cutoff_time = pd.to_datetime(row["cutoff_time"])

    incident_start = pd.Timestamp(incident_start_ts)
    # Incident xảy ra sau khi xe đã chạy -> không thể ảnh hưởng chuyến này
    if incident_start > truck_time:
        return {
            "jt_id": jt_id,
            "incident_start": str(incident_start),
            "incident_duration_h": incident_duration_h,
            "recovery_time_h": round(recovery_time_h, 2),
            "completion_time": str(incident_start),
            "cutoff_time": str(cutoff_time),
            "truck_time": str(truck_time),
            "kips": True,
            "status": "PASS",
            "note": "incident_after_truck",
        }
    completion_time = incident_start + pd.Timedelta(hours=incident_duration_h + recovery_time_h)

    kips = completion_time <= truck_time

    return {
        "jt_id": jt_id,
        "incident_start": str(incident_start),
        "incident_duration_h": incident_duration_h,
        "recovery_time_h": round(recovery_time_h, 2),
        "completion_time": str(completion_time),
        "cutoff_time": str(cutoff_time),
        "truck_time": str(truck_time),
        "kips": kips,
        "status": "PASS" if kips else "LATE",
    }
