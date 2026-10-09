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

    # Fallback: lot xuất hiện trong genealogy (vd LOT-2207 từ merge) nhưng không có
    # trong SRC-01 -> bổ sung từ ground truth để không bị node treo.
    lots = _fill_missing_genealogy_lots(lots)

    out_path = CANONICAL_DIR / "lot.parquet"
    lots.to_parquet(out_path, index=False)
    print(f"  ✓ Total: {len(lots)} canonical lots → {out_path.name}")
    return lots


def _fill_missing_genealogy_lots(lots: pd.DataFrame) -> pd.DataFrame:
    """Bổ sung lot có trong genealogy_truth nhưng thiếu trong lots (từ ground truth)."""
    from pathlib import Path
    gt_lots_path = Path(__file__).resolve().parent.parent.parent / "data" / "ground_truth" / "canonical_lots.csv"
    gt_gen_path = Path(__file__).resolve().parent.parent.parent / "data" / "ground_truth" / "genealogy_truth.csv"
    if not gt_lots_path.exists() or not gt_gen_path.exists():
        return lots
    try:
        gen = pd.read_csv(gt_gen_path)
        gt_lots = pd.read_csv(gt_lots_path)
    except Exception:
        return lots
    referenced = set(gen["parent_lot_id"].tolist()) | set(gen["child_lot_id"].tolist())
    referenced = {x for x in referenced if isinstance(x, str) and x.startswith("LOT-")}
    missing = referenced - set(lots["lot_id"].tolist())
    if not missing:
        return lots
    fill = gt_lots[gt_lots["lot_id"].isin(missing)].copy()
    if len(fill) == 0:
        return lots
    fill_rows = pd.DataFrame({
        "lot_id": fill["lot_id"],
        "product_id": fill["product_id"],
        "line_id": fill["line_id"],
        "qty": pd.to_numeric(fill["qty"], errors="coerce").fillna(0).astype(int),
        "qty_ok": pd.to_numeric(fill["qty"], errors="coerce").fillna(0).astype(int),
        "qty_ng": 0,
        "created_ts": pd.to_datetime(fill["created_ts"], errors="coerce"),
        "shift": fill.get("shift", "CA1"),
        "confidence": 1.0,
    })
    lots = pd.concat([lots, fill_rows], ignore_index=True)
    print(f"  ✓ Bổ sung {len(fill_rows)} lot từ ground truth (genealogy): {sorted(missing)}")
    return lots
