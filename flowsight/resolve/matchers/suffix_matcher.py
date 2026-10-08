import re


def extract_suffix(alias: str) -> str:
    """Extract 4-digit suffix từ alias."""
    m = re.search(r"(\d{3,4})", str(alias))
    if m:
        return m.group(1).zfill(4)
    return ""


def match_suffix(alias: str, canonical_pool: list) -> tuple:
    """
    Match bằng 4-digit suffix.
    Returns: (canonical_id, confidence, method)
    """
    alias_suffix = extract_suffix(alias)
    if not alias_suffix:
        return None, 0.0, None

    matches = [c for c in canonical_pool if extract_suffix(c) == alias_suffix]

    if len(matches) == 1:
        return matches[0], 0.95, "suffix"
    elif len(matches) > 1:
        return None, 0.0, "ambiguous_suffix"

    return None, 0.0, None
