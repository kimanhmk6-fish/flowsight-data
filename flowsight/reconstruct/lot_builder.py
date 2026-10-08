import pandas as pd
from .config import CANONICAL_DIR


def build_canonical_lots(resolved_output: pd.DataFrame) -> pd.DataFrame:
    """Tạo bảng lot canonical."""
    print("\n[11C-1a] Building canonical lots...")

    df = resolved_output.copy()

    # Xử lý các cột số
    qty_ok = pd.to_numeric(df["qty_ok_norm"], errors="coerce").fillna(0).astype(int)
    qty_ng = pd.to_numeric(df["qty_ng_norm"], errors="coerce").fillna(0).astype(int)

    lots = pd.DataFrame({
        "lot_id": df["lot_canonical_id"],
        "product_id": df["product_ref_norm"],
        "line_id": df["line_ref_raw"],
        "qty": qty_ok + qty_ng,
        "qty_ok": qty_ok,
        "qty_ng": qty_ng,
        "created_ts": pd.to_datetime(df["event_ts_norm"], errors="coerce"),
        "shift": df["shift_raw"],
        "confidence": df.get("lot_match_confidence", 1.0),
    })

    lots = lots.dropna(subset=["lot_id"]).drop_duplicates(subset=["lot_id"])
    lots["qty"] = lots["qty"].astype(int)

    out_path = CANONICAL_DIR / "lot.parquet"
    lots.to_parquet(out_path, index=False)
    print(f"  ✓ Total: {len(lots)} canonical lots → {out_path.name}")
    return lots
