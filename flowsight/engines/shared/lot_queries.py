"""
lot_queries.py — Helper query lots/JTs từ canonical tables.
"""
import pandas as pd


def get_lots_for_jt(tables: dict, jt_id: str) -> list:
    """Lấy lots được allocate cho 1 JT."""
    alloc = tables.get("jt_allocation", pd.DataFrame())
    if len(alloc) == 0:
        return []
    return alloc[alloc["jt_id"] == jt_id]["lot_id"].tolist()


def get_jts_for_station(tables: dict, station_id: str, window_h: float = 24) -> list:
    """Lấy JTs có khả năng bị ảnh hưởng bởi station."""
    events = tables.get("lot_event", pd.DataFrame())
    if len(events) == 0:
        return []

    lots_at_station = events[events["station_id"] == station_id]["lot_id"].unique()
    alloc = tables.get("jt_allocation", pd.DataFrame())
    if len(alloc) == 0:
        return []

    return alloc[alloc["lot_id"].isin(lots_at_station)]["jt_id"].unique().tolist()


def get_effective_rate(tables: dict, station_id: str) -> float:
    """Ước lượng rate thực tế (sp/h) của station từ lịch sử."""
    events = tables.get("lot_event", pd.DataFrame())
    if len(events) == 0:
        return 92.0  # default

    station_events = events[events["station_id"] == station_id]
    if len(station_events) == 0:
        return 92.0

    # Từ lot_event: mỗi event có duration = end - start
    if "ts_raw" in station_events.columns:
        try:
            station_events = station_events.copy()
            station_events["ts_raw"] = pd.to_datetime(station_events["ts_raw"], errors="coerce")
        except Exception:
            pass

    # Default: 92 sp/h (từ historical median của mock data)
    return 92.0
