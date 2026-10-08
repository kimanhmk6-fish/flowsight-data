import pandas as pd
from .config import CANONICAL_DIR


def build_jt_allocation(
    canonical_lots: pd.DataFrame,
    resolved_jt: pd.DataFrame,
) -> pd.DataFrame:
    """
    Tái dựng quan hệ lot → JT bằng FIFO.
    - Group lots by product, sort by created_ts.
    - Sort JTs by due_ts.
    - Gán lot cho JT theo thứ tự.
    """
    print("\n[11C-1c] Building JT allocation...")

    # Build jt_order canonical
    jt_order = pd.DataFrame({
        "jt_id": resolved_jt["jt_ref_norm"],
        "product_id": resolved_jt["product_ref_norm"],
        "line_id": resolved_jt.get("line_ref_raw"),
        "qty": pd.to_numeric(
    resolved_jt.get("qty_norm", resolved_jt.get("qty_raw", resolved_jt.get("qty", 0))), 
    errors="coerce"
).fillna(0).astype(int),
        "due_ts": pd.to_datetime(
    resolved_jt.get("due_date_norm", resolved_jt.get("due_date_raw", resolved_jt.get("due_date"))), 
    errors="coerce",
    dayfirst=True
),
        "priority": resolved_jt.get("priority_raw"),
        "customer": resolved_jt.get("customer_raw"),
        "status": resolved_jt.get("status_raw"),
    })
    jt_order = jt_order.dropna(subset=["jt_id"]).drop_duplicates(subset=["jt_id"])

    jt_order.to_parquet(CANONICAL_DIR / "jt_order.parquet", index=False)
    print(f"  ✓ Saved jt_order: {len(jt_order)} rows")

    # FIFO allocation
    allocations = []
    alloc_idx = 1

    # Group lots by product
    lots_by_product = {}
    for _, lot in canonical_lots.iterrows():
        prod = lot["product_id"]
        if pd.isna(prod):
            continue
        lots_by_product.setdefault(prod, []).append(lot)

    for prod in lots_by_product:
        lots_by_product[prod].sort(key=lambda x: x.get("created_ts") or pd.Timestamp.min)

    jts = jt_order.sort_values("due_ts")
    lot_pool = {prod: list(lst) for prod, lst in lots_by_product.items()}

    for _, jt in jts.iterrows():
        prod = jt["product_id"]
        remaining = jt["qty"]

        if prod not in lot_pool:
            continue

        while remaining > 0 and len(lot_pool[prod]) > 0:
            lot = lot_pool[prod][0]
            take = min(int(lot["qty"]), remaining)

            allocations.append({
                "allocation_id": f"ALLOC-{alloc_idx:05d}",
                "jt_id": jt["jt_id"],
                "lot_id": lot["lot_id"],
                "qty_allocated": take,
                "allocation_time": jt["due_ts"],
                "confidence": 0.85,
                "evidence": "fifo_based",
            })

            remaining -= take
            alloc_idx += 1

            if take >= lot["qty"]:
                lot_pool[prod].pop(0)
            else:
                # Partial allocation
                new_lot = dict(lot)
                new_lot["qty"] = lot["qty"] - take
                lot_pool[prod][0] = new_lot

    df = pd.DataFrame(allocations)

    out_path = CANONICAL_DIR / "jt_allocation.parquet"
    df.to_parquet(out_path, index=False)
    print(f"  ✓ Total: {len(df)} allocations → {out_path.name}")

    # Validate
    if len(df) > 0:
        jt_totals = df.groupby("jt_id")["qty_allocated"].sum().reset_index()
        jt_totals = jt_totals.merge(jt_order[["jt_id", "qty"]], on="jt_id", how="left")
        jt_totals["diff"] = (jt_totals["qty_allocated"] - jt_totals["qty"]).abs()
        invalid = jt_totals[jt_totals["diff"] > 5]
        if len(invalid) == 0:
            print(f"  ✓ Allocation validated ({len(jt_totals)} JTs)")
        else:
            print(f"  ⚠ {len(invalid)} JTs với allocation không khớp")

    return df
