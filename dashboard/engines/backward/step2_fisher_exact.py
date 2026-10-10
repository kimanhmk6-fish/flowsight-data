"""
step2_fisher_exact.py — Bước 2: Fisher Exact Test.
Bảng tương quan 2×2:
                NG      OK
    Có F        a       b
    Không có F  c       d
"""
import numpy as np
import pandas as pd
from scipy.stats import fisher_exact
from dataclasses import dataclass


@dataclass
class FisherResult:
    candidate_id: str
    candidate_type: str
    contingency_table: dict
    odds_ratio: float
    p_value: float
    n_total: int
    n_sufficient: bool


def _get_field(obj, key):
    """Hỗ trợ cả dataclass object và dict."""
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)


def _get_candidate_type(candidate):
    """Hỗ trợ cả dataclass object và dict."""
    if isinstance(candidate, dict):
        return candidate.get("candidate_type", "UNKNOWN")
    return getattr(candidate, "candidate_type", "UNKNOWN")


def fisher_test_candidate(candidate, lots, universe_lot_ids=None):
    candidate_id = _get_field(candidate, "candidate_id")
    related_ids = set(_get_field(candidate, "related_lot_ids") or [])


    # Universe
    if universe_lot_ids is None:
        universe = lots.copy()
    else:
        universe = lots[lots["lot_id"].isin(universe_lot_ids)]

    if "is_ng" not in universe.columns:
        universe = universe.copy()
        if "qty_ng" in universe.columns:
            universe["is_ng"] = (universe["qty_ng"] > 0).astype(int)
        else:
            universe["is_ng"] = 0

    in_F = universe["lot_id"].isin(related_ids)

    a = int(((universe["is_ng"] == 1) & in_F).sum())
    b = int(((universe["is_ng"] == 0) & in_F).sum())
    c = int(((universe["is_ng"] == 1) & ~in_F).sum())
    d = int(((universe["is_ng"] == 0) & ~in_F).sum())

    # Edge case
    if a + b == 0 or c + d == 0 or a + c == 0 or b + d == 0:
        return FisherResult(
            candidate_id=candidate_id,
            candidate_type=_get_candidate_type(candidate),
            contingency_table={"a": a, "b": b, "c": c, "d": d},
            odds_ratio=0.0,
            p_value=1.0,
            n_total=a + b + c + d,
            n_sufficient=False,
        )

    try:
        odds_ratio, p_value = fisher_exact([[a, b], [c, d]], alternative="two-sided")
    except Exception:
        odds_ratio, p_value = 0.0, 1.0

    n_sufficient = (min(a, b, c, d) >= 2) or ((a + b + c + d) >= 20)

    return FisherResult(
        candidate_id=candidate_id,
        candidate_type=_get_candidate_type(candidate),
        contingency_table={"a": a, "b": b, "c": c, "d": d},
        odds_ratio=float(odds_ratio) if not np.isnan(odds_ratio) else 0.0,
        p_value=float(p_value),
        n_total=a + b + c + d,
        n_sufficient=n_sufficient,
    )


def fisher_test_batch(candidates, lots):
    results = []
    for cand in candidates:
        try:
            res = fisher_test_candidate(cand, lots)
            results.append(res)
        except Exception as e:
            cid = _get_field(cand, "candidate_id") or "UNKNOWN"
            print(f"  ⚠ Fisher test failed for {cid}: {e}")
    return results

