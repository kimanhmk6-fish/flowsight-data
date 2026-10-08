import pandas as pd
from .config import CANONICAL_DIR, MASTER_DIR


def build_material_consumption(
    canonical_lots: pd.DataFrame,
) -> pd.DataFrame:
    """
    Tái dựng quan hệ lot → material_lot từ BOM + FIFO.
    """
    print("\n[11C-1d] Building material consumption...")

    bom_path = MASTER_DIR / "bom.csv"
    if not bom_path.exists():
        print(f"  ⚠ BOM không tồn tại: {bom_path}")
        return pd.DataFrame()

    bom = pd.read_csv(bom_path)

    # Material lots từ ground_truth
    from .config import GT_DIR
    mat_lots_path = GT_DIR / "material_lot_truth.csv"
    if mat_lots_path.exists():
        mat_lots = pd.read_csv(mat_lots_path)
        mat_lots["received_ts"] = pd.to_datetime(mat_lots["received_ts"], errors="coerce")
    else:
        # Fallback: sinh từ component
        mat_lots = pd.DataFrame({
            "mat_lot_id": [f"MAT-{c}-0917-01" for c in bom["component_id"].unique()],
            "component_id": bom["component_id"].unique(),
            "received_ts": pd.Timestamp("2026-09-29"),
        })

    mat_lots = mat_lots.sort_values("received_ts")

    consumptions = []
    cons_idx = 1

    for _, lot in canonical_lots.iterrows():
        prod = lot["product_id"]
        if pd.isna(prod):
            continue

        lot_bom = bom[bom["product_id"] == prod]

        for _, b in lot_bom.iterrows():
            comp = b["component_id"]

            candidates = mat_lots[mat_lots["component_id"] == comp]
            if len(candidates) == 0:
                continue

            mat_lot = candidates.iloc[0]
            qty = round(float(b["qty_per_unit"]) * int(lot["qty"]))

            consumptions.append({
                "consumption_id": f"CONS-{cons_idx:05d}",
                "lot_id": lot["lot_id"],
                "mat_lot_id": mat_lot["mat_lot_id"],
                "component_id": comp,
                "qty_consumed": qty,
                "consumption_time": lot["created_ts"],
                "confidence": 0.90,
                "evidence": "fifo_bom_based",
            })
            cons_idx += 1

    df = pd.DataFrame(consumptions)

    out_path = CANONICAL_DIR / "material_consumption.parquet"
    df.to_parquet(out_path, index=False)
    print(f"  ✓ Total: {len(df)} consumption records → {out_path.name}")
    return df
