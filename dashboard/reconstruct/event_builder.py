import pandas as pd
from .config import CANONICAL_DIR


def build_lot_events(resolved_ipc: pd.DataFrame) -> pd.DataFrame:
    """Tái dựng lot_event từ SRC-02 IPC."""
    print("\n[11C-1f] Building lot events from IPC...")

    df = resolved_ipc.copy()

    events = pd.DataFrame({
        "event_id": df["ipc_event_id_raw"],
        "lot_id": df["lot_canonical_id"],
        "station_id": df["station_ref_norm"],
        "event_type": df["event_type_raw"],
        "event_code": df["event_code_raw"],
        "ts_raw": pd.to_datetime(df["ts_raw"], errors="coerce"),
        "ts_aligned": pd.to_datetime(df.get("ts_aligned"), errors="coerce"),
        "source": "SRC-02_ipc",
        "confidence": 1.0,
    })

    events = events.dropna(subset=["lot_id"])

    out_path = CANONICAL_DIR / "lot_event.parquet"
    events.to_parquet(out_path, index=False)
    print(f"  ✓ Total: {len(events)} events → {out_path.name}")
    return events
