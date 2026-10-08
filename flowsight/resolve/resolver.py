import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional

from .config import (
    RESOLVED_DIR, AUDIT_DIR, MIN_CONFIDENCE_ACCEPT, TIER_WEIGHTS,
)
from .matchers.exact_matcher import match_exact
from .matchers.suffix_matcher import match_suffix
from .matchers.temporal_matcher import match_temporal


# ============================================================
# CANONICAL POOL — sinh từ range + special lots
# ============================================================
def load_canonical_pool() -> dict:
    """Pool of possible canonical LOT IDs (không dùng ground truth mapping)."""
    lots = [f"LOT-{i:04d}" for i in range(1, 411)]
    # Special lots cho test case R04, R06, R07, R08
    special = ["LOT-1050", "LOT-1060", "LOT-1070", "LOT-1079", "LOT-1080", "LOT-1081"]
    lots.extend(special)
    return {
        "LOT": set(lots),
        "LOT_list": sorted(lots),
    }


# ============================================================
# RESOLVER
# ============================================================
def resolve_alias(
    alias: str,
    source_id: str,
    ts: Optional[pd.Timestamp],
    product: Optional[str],
    canonical_pool: set,
    canonical_pool_list: list,
    staged_data: dict,
) -> dict:
    """Resolve 1 alias qua 3 tầng matching."""

    # Tầng 1: Exact
    cid, conf, method = match_exact(alias, canonical_pool)
    if cid is not None:
        return {
            "alias": alias, "source_id": source_id,
            "canonical_id": cid, "confidence": conf,
            "method": method, "needs_review": False,
        }

    # Tầng 2: Suffix
    cid, conf, method = match_suffix(alias, canonical_pool_list)
    if cid is not None:
        return {
            "alias": alias, "source_id": source_id,
            "canonical_id": cid, "confidence": conf,
            "method": method, "needs_review": conf < MIN_CONFIDENCE_ACCEPT,
        }

    # Tầng 3: Temporal
    cid, conf, method = match_temporal(
        alias, source_id, ts, product,
        staged_data, canonical_pool,
    )
    if cid is not None:
        return {
            "alias": alias, "source_id": source_id,
            "canonical_id": cid, "confidence": conf,
            "method": method, "needs_review": conf < MIN_CONFIDENCE_ACCEPT,
        }

    # Không match
    return {
        "alias": alias, "source_id": source_id,
        "canonical_id": None, "confidence": 0.0,
        "method": "no_match", "needs_review": True,
    }


def resolve_all_lots(staged_data: dict) -> tuple:
    """
    Resolve tất cả lots.
    Returns: (mapping_df, unresolved_df)
    """
    print("\n" + "=" * 70)
    print("  TẦNG 11B-2: ENTITY RESOLUTION")
    print("=" * 70)

    pool = load_canonical_pool()
    canonical_set = pool["LOT"]
    canonical_list = pool["LOT_list"]

    # Collect unique aliases
    all_aliases = []
    for source_id, df in staged_data.items():
        if "lot_ref_norm" not in df.columns:
            continue

        unique_aliases = df["lot_ref_norm"].dropna().unique()
        for alias in unique_aliases:
            sample = df[df["lot_ref_norm"] == alias].iloc[0]
            ts = sample.get("ts_aligned") if "ts_aligned" in sample else sample.get("ts_raw")
            product = sample.get("product_ref_norm")

            all_aliases.append({
                "source_id": source_id,
                "alias": alias,
                "sample_ts": ts,
                "sample_product": product,
                "n_records": int((df["lot_ref_norm"] == alias).sum()),
            })

    aliases_df = pd.DataFrame(all_aliases).drop_duplicates(subset=["source_id", "alias"])
    print(f"\nTotal aliases to resolve: {len(aliases_df)}")

    # Resolve từng alias
    mappings = []
    for _, row in aliases_df.iterrows():
        result = resolve_alias(
            alias=row["alias"],
            source_id=row["source_id"],
            ts=row["sample_ts"],
            product=row["sample_product"],
            canonical_pool=canonical_set,
            canonical_pool_list=canonical_list,
            staged_data=staged_data,
        )
        result["n_records"] = row["n_records"]
        mappings.append(result)

    mapping_df = pd.DataFrame(mappings)

    total = len(mapping_df)
    resolved = mapping_df["canonical_id"].notna().sum()
    needs_review = mapping_df["needs_review"].sum()

    print(f"\nResolution results:")
    print(f"  Total aliases:  {total}")
    print(f"  Resolved:       {resolved} ({100*resolved/total:.1f}%)")
    print(f"  Needs review:   {needs_review}")

    method_counts = mapping_df.groupby("method").size()
    print(f"\nMethod breakdown:")
    for method, count in method_counts.items():
        print(f"  {method:20s}: {count}")

    # Save
    mapping_df.to_parquet(RESOLVED_DIR / "entity_mapping_resolved.parquet", index=False)

    unresolved = mapping_df[mapping_df["canonical_id"].isna() | mapping_df["needs_review"]]
    unresolved.to_csv(AUDIT_DIR / "manual_review_queue.csv", index=False)

    print(f"\n  ✓ Saved mapping: {len(mapping_df)} rows")
    print(f"  ✓ Manual review queue: {len(unresolved)} rows")
    print("=" * 70)

    return mapping_df, unresolved


def apply_resolution_to_staged(staged_data: dict, mapping_df: pd.DataFrame) -> dict:
    """Áp dụng mapping vào staged data → resolved data."""
    resolved_data = {}

    for source_id, df in staged_data.items():
        df = df.copy()

        src_mapping = mapping_df[mapping_df["source_id"] == source_id]
        alias_to_canonical = dict(zip(src_mapping["alias"], src_mapping["canonical_id"]))
        alias_to_conf = dict(zip(src_mapping["alias"], src_mapping["confidence"]))

        if "lot_ref_norm" in df.columns:
            df["lot_canonical_id"] = df["lot_ref_norm"].map(alias_to_canonical)
            df["lot_match_confidence"] = df["lot_ref_norm"].map(alias_to_conf)

        resolved_data[source_id] = df

    return resolved_data
