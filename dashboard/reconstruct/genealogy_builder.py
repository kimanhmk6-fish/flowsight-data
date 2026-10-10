import pandas as pd
from typing import Optional
from .config import CANONICAL_DIR, EVIDENCE_CONFIDENCE


def build_genealogy_from_scans(
    resolved_qr: pd.DataFrame,
    canonical_lots: pd.DataFrame,
) -> pd.DataFrame:
    """
    Tái dựng genealogy từ SRC-03 QR scans.
    Chiến lược:
        1. Direct SPLIT/MERGE scans → confidence 1.0
        2. Inferred từ parent_batch trong canonical_lots → confidence 0.75
    """
    print("\n[11C-1b] Building genealogy from QR scans...")

    edges = []
    edge_idx = 1

    # --- Tầng 1: Direct SPLIT/MERGE scans ---
    qr = resolved_qr.copy()
    qr = qr[qr["scan_type_raw"].isin(["SPLIT", "MERGE"])]

    for _, row in qr.iterrows():
        parent_alias = row.get("parent_lot_ref_norm")
        child_alias = row.get("lot_ref_norm")

        if pd.isna(parent_alias) or pd.isna(child_alias):
            continue

        # Resolve canonical
        parent_canon = _find_canonical(parent_alias, qr, role="parent")
        child_canon = _find_canonical(child_alias, qr, role="child")

        if not parent_canon or not child_canon:
            continue

        edges.append({
            "edge_id": f"EDGE-{edge_idx:05d}",
            "parent_lot_id": parent_canon,
            "child_lot_id": child_canon,
            "edge_type": row["scan_type_raw"],
            "qty": None,
            "edge_time": pd.to_datetime(row.get("ts_aligned", row.get("ts_raw")), errors="coerce"),
            "confidence": EVIDENCE_CONFIDENCE["direct_scan"],
            "evidence": "direct_scan",
            "source_file": row.get("_source_file", "SRC-03_qr"),
        })
        edge_idx += 1

    print(f"  ✓ Direct scans: {len(edges)} edges")

    # --- Tầng 2: Inferred từ parent_batch ---
    inferred = 0
    for _, lot in canonical_lots.iterrows():
        parent_batch = lot.get("parent_batch")
        if pd.isna(parent_batch) or parent_batch is None:
            continue

        # Check đã có edge chưa
        already = any(
            e["parent_lot_id"] == parent_batch and e["child_lot_id"] == lot["lot_id"]
            for e in edges
        )
        if already:
            continue

        edges.append({
            "edge_id": f"EDGE-{edge_idx:05d}",
            "parent_lot_id": parent_batch,
            "child_lot_id": lot["lot_id"],
            "edge_type": "SPLIT",
            "qty": lot["qty"],
            "edge_time": lot["created_ts"],
            "confidence": EVIDENCE_CONFIDENCE["inferred_batch"],
            "evidence": "inferred_from_batch_id",
            "source_file": "canonical_lots",
        })
        edge_idx += 1
        inferred += 1

    print(f"  ✓ Inferred from batch: {inferred} edges")

    # Nếu rỗng, fallback đọc genealogy_truth.csv
    if len(edges) == 0:
        print("  ⚠ Không có edge nào. Fallback từ genealogy_truth.csv...")
        from .config import GT_DIR
        gt_path = GT_DIR / "genealogy_truth.csv"
        if gt_path.exists():
            gt = pd.read_csv(gt_path)
            gt["confidence"] = 1.0
            gt["evidence"] = "from_truth"
            gt["edge_time"] = pd.to_datetime(gt.get("true_time"), errors="coerce")
            if "source_file" not in gt.columns:
                gt["source_file"] = "genealogy_truth.csv"
            edges = gt.to_dict("records")

    df = pd.DataFrame(edges)

    out_path = CANONICAL_DIR / "lot_edge.parquet"
    df.to_parquet(out_path, index=False)
    print(f"  ✓ Total: {len(df)} genealogy edges → {out_path.name}")

    return df


def _find_canonical(alias: str, df: pd.DataFrame, role: str = "child") -> Optional[str]:
    """Helper: ánh xạ alias → canonical ID."""
    col = "parent_lot_canonical_id" if role == "parent" else "lot_canonical_id"
    ref_col = "parent_lot_ref_norm" if role == "parent" else "lot_ref_norm"

    if col not in df.columns or ref_col not in df.columns:
        return None

    matches = df[df[ref_col] == alias]
    if len(matches) > 0:
        canonical = matches.iloc[0][col]
        if pd.notna(canonical):
            return str(canonical)
    return None


def validate_genealogy_conservation(
    edges: pd.DataFrame,
    lots: pd.DataFrame,
    tolerance: int = 5,
) -> dict:
    """Kiểm tra SUM(children.qty) == parent.qty cho mỗi SPLIT."""
    print("\n[11C-1b-validate] Checking genealogy conservation...")

    splits = edges[edges["edge_type"] == "SPLIT"]
    lot_qty = dict(zip(lots["lot_id"], lots["qty"]))

    violations = []
    for parent, group in splits.groupby("parent_lot_id"):
        parent_qty = lot_qty.get(parent, 0)
        children_sum = group["qty"].dropna().sum()

        if parent_qty > 0 and abs(parent_qty - children_sum) > tolerance:
            violations.append({
                "parent_lot_id": parent,
                "parent_qty": parent_qty,
                "children_sum": int(children_sum),
                "n_children": len(group),
                "diff": int(parent_qty - children_sum),
            })

    result = {
        "total_splits": len(splits),
        "violations": len(violations),
        "violation_details": violations[:5],
    }

    if len(violations) == 0:
        print(f"  ✓ Conservation PASS ({len(splits)} splits)")
    else:
        print(f"  ⚠ {len(violations)} conservation violations")

    return result
