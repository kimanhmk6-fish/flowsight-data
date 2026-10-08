def match_exact(alias: str, canonical_pool: set) -> tuple:
    """
    Match exact: alias == canonical_id sau khi normalize.
    Returns: (canonical_id, confidence, method)
    """
    if alias in canonical_pool:
        return alias, 1.0, "exact"
    return None, 0.0, None
