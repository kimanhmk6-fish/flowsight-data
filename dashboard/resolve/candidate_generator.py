import pandas as pd


def generate_lot_candidates(staged_data: dict) -> pd.DataFrame:
    """Sinh candidates cho LOT resolution."""
    candidates = []

    for source_id, df in staged_data.items():
        if "lot_ref_norm" not in df.columns:
            continue

        aliases = df["lot_ref_norm"].dropna().unique()

        for alias in aliases:
            candidates.append({
                "source_id": source_id,
                "alias": alias,
                "n_records": int((df["lot_ref_norm"] == alias).sum()),
            })

    return pd.DataFrame(candidates)
