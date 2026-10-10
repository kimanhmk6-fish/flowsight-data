import pandas as pd
from .config import CANONICAL_DIR


def build_shipment(resolved_shipping: pd.DataFrame) -> pd.DataFrame:
    """Tái dựng quan hệ JT → shipment từ SRC-08."""
    print("\n[11C-1e] Building shipment relationships...")

    df = resolved_shipping.copy()

    shipments = pd.DataFrame({
        "shipment_id": df["shipment_ref_raw"],
        "jt_id": df["jt_ref_norm"],
        "truck_time": pd.to_datetime(df["truck_ts_norm"], errors="coerce"),
        "cutoff_time": pd.to_datetime(df["cutoff_ts_norm"], errors="coerce"),
        "qty_planned": pd.to_numeric(df["qty_planned_norm"], errors="coerce").fillna(0).astype(int),
        "status": df["status_raw"],
        "confidence": 0.95,
        "evidence": "direct_shipping_plan",
    })

    shipments = shipments.dropna(subset=["shipment_id", "jt_id"])

    out_path = CANONICAL_DIR / "shipment.parquet"
    shipments.to_parquet(out_path, index=False)
    print(f"  ✓ Total: {len(shipments)} shipment records → {out_path.name}")
    return shipments
