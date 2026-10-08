"""
step5_scoring.py — Bước 5: Composite Score.
Score(f) = w1·norm(-log10(p)) + w2·norm(lift) + w3·signal_strength
"""
import numpy as np
import pandas as pd
from dataclasses import dataclass


W1_PVALUE = 0.5
W2_LIFT = 0.3
W3_SIGNAL = 0.2

MIN_P_VALUE = 0.05
MIN_LIFT = 1.5
INSUFFICIENT_EVIDENCE_THRESHOLD = 0.3


def _get_field(obj, key, default=None):
    """Hỗ trợ cả dataclass object và dict."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)



@dataclass
class ScoredCandidate:
    candidate_id: str
    candidate_type: str
    score: float
    p_value: float
    lift: float
    signal_strength: float
    n_related_lots: int
    n_ng_lots: int
    is_significant: bool
    evidence_chain: list


def normalize_minmax(values: np.ndarray) -> np.ndarray:
    """Normalize về [0, 1]."""
    if len(values) == 0:
        return values
    vmin = values.min()
    vmax = values.max()
    if vmax - vmin < 1e-9:
        return np.ones_like(values) * 0.5
    return (values - vmin) / (vmax - vmin)


def score_candidates(candidates, fisher_results, lift_results, spc_signals):
    fisher_by_id = {r.candidate_id: r for r in fisher_results}
    lift_by_id = {r.candidate_id: r for r in lift_results}

    spc_by_id = {}
    for s in spc_signals:
        base_id = s.candidate_id.split("::")[0]
        spc_by_id.setdefault(base_id, []).append(s)

    p_values = np.array([
        fisher_by_id[_get_field(c, "candidate_id")].p_value
        if _get_field(c, "candidate_id") in fisher_by_id else 1.0
        for c in candidates
    ])
    lifts = np.array([
        lift_by_id[_get_field(c, "candidate_id")].lift
        if _get_field(c, "candidate_id") in lift_by_id else 0.0
        for c in candidates
    ])
    signals = np.array([
        max([s.strength for s in spc_by_id.get(_get_field(c, "candidate_id"), [])], default=0.0)
        for c in candidates
    ])

    neg_log_p = -np.log10(np.maximum(p_values, 1e-10))
    neg_log_p_norm = normalize_minmax(neg_log_p)
    lift_norm = normalize_minmax(lifts)
    signal_norm = normalize_minmax(signals)

    scores = W1_PVALUE * neg_log_p_norm + W2_LIFT * lift_norm + W3_SIGNAL * signal_norm

    results = []
    for i, c in enumerate(candidates):
        cand_id = _get_field(c, "candidate_id")
        cand_type = _get_field(c, "candidate_type", "UNKNOWN")
        fr = fisher_by_id.get(cand_id)
        lr = lift_by_id.get(cand_id)
        spcs = spc_by_id.get(cand_id, [])

        p_val = fr.p_value if fr else 1.0
        lift_val = lr.lift if lr else 0.0
        sig = float(signals[i])

        is_sig = (p_val < MIN_P_VALUE) and (lift_val >= MIN_LIFT)

        evidence = []
        if fr:
            evidence.append({"type": "fisher_exact", "p_value": round(p_val, 4),
                             "contingency": fr.contingency_table})
        if lr:
            evidence.append({"type": "risk_lift", "lift": lift_val,
                             "p_ng_given_f": lr.p_ng_given_f, "p_ng": lr.p_ng})
        for s in spcs:
            evidence.append({"type": "spc_signal", "signal_type": s.signal_type,
                             "n_violations": s.n_violations, "rules": s.rules_triggered})

        results.append(ScoredCandidate(
            candidate_id=cand_id,
            candidate_type=cand_type,
            score=round(float(scores[i]), 4),
            p_value=round(p_val, 4),
            lift=round(lift_val, 3),
            signal_strength=round(sig, 3),
            n_related_lots=_get_field(c, "n_related_lots", 0),
            n_ng_lots=_get_field(c, "n_ng_lots", 0),
            is_significant=is_sig,
            evidence_chain=evidence,
        ))

    results.sort(key=lambda x: x.score, reverse=True)
    return results


def get_top_k(results: list, k: int = 3) -> list:
    return results[:k]


def is_insufficient_evidence(results: list) -> bool:
    """Kiểm tra có đủ evidence không."""
    if not results:
        return True
    top = results[0]
    if not top.is_significant and top.score < INSUFFICIENT_EVIDENCE_THRESHOLD:
        return True
    return False
