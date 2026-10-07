"""
id_normalizer.py — Chuẩn hóa alias ID về canonical format (Tầng 11A-3).
"""
import re
from typing import Optional


# ============================================================
# REGEX PATTERNS
# ============================================================

# LOT aliases:
#   "LOT-0147"       → canonical
#   "L-A-0147"       → IPC
#   "QR260929A147"   → QR scan
#   "A147"           → Output
#   "LOT-0147-A"     → QC Auto/Sampling
LOT_PATTERNS = [
    (re.compile(r"^QR(\d{6})([A-Z])(\d{3,4})$"), "qr"),
    (re.compile(r"^L-([A-Z])-(\d{3,4})$"), "ipc"),
    (re.compile(r"^([A-Z])(\d{3,4})$"), "output"),
    (re.compile(r"^LOT-(\d{3,4})-([A-Z])$"), "qc"),
    (re.compile(r"^LOT-(\d{3,4})$"), "canonical"),
    (re.compile(r"^QR-(.+)$"), "qr_special"),
]

# JT patterns
JT_PATTERNS = [
    (re.compile(r"^JT-(\d{3,4})$"), "canonical"),
    (re.compile(r"^JT[-_]?(\d+)$"), "loose"),
]

# Station patterns
STATION_PATTERNS = [
    (re.compile(r"^STN-([A-Z0-9]+)$"), "canonical"),
    (re.compile(r"^([A-Z0-9]+)$"), "loose"),   # M2 → STN-M2
]

# Product patterns
PRODUCT_PATTERNS = [
    (re.compile(r"^PROD-P(\d+)$"), "canonical"),
    (re.compile(r"^P0?(\d+)$"), "short"),
]

# Component patterns
COMPONENT_PATTERNS = [
    (re.compile(r"^COMP-C(\d+)$"), "canonical"),
    (re.compile(r"^ITEM_COMP-C(\d+)$"), "inventory"),
    (re.compile(r"^C(\d+)$"), "short"),
]


# ============================================================
# NORMALIZERS
# ============================================================

def normalize_lot_id(raw: Optional[str]) -> Optional[str]:
    """
    Chuẩn hóa mọi alias LOT về "LOT-NNNN".

    Examples:
        "L-A-0147"       → "LOT-0147"
        "QR260929A147"   → "LOT-0147"
        "A147"           → "LOT-0147"
        "LOT-0147-A"     → "LOT-0147"
        "LOT-0147"       → "LOT-0147"
        None             → None
    """
    if raw is None or (isinstance(raw, str) and raw.strip() == ""):
        return None

    raw = str(raw).strip()

    for pattern, kind in LOT_PATTERNS:
        m = pattern.match(raw)
        if m:
            if kind == "canonical":
                return f"LOT-{int(m.group(1)):04d}"
            elif kind == "ipc":
                return f"LOT-{int(m.group(2)):04d}"
            elif kind == "qr":
                return f"LOT-{int(m.group(3)):04d}"
            elif kind == "output":
                return f"LOT-{int(m.group(2)):04d}"
            elif kind == "qc":
                return f"LOT-{int(m.group(1)):04d}"
            elif kind == "qr_special":
                inner = m.group(1)
                num = re.search(r"(\d+)", inner)
                if num:
                    return f"LOT-{int(num.group(1)):04d}"
                return raw

    return raw   # Không match → giữ nguyên


def normalize_jt_id(raw: Optional[str]) -> Optional[str]:
    """Chuẩn hóa JT alias về "JT-NNNN"."""
    if raw is None or (isinstance(raw, str) and raw.strip() == ""):
        return None

    raw = str(raw).strip()

    for pattern, kind in JT_PATTERNS:
        m = pattern.match(raw)
        if m:
            return f"JT-{int(m.group(1)):04d}"

    return raw


def normalize_station_id(raw: Optional[str]) -> Optional[str]:
    """Chuẩn hóa station alias về "STN-XXX"."""
    if raw is None or (isinstance(raw, str) and raw.strip() == ""):
        return None

    raw = str(raw).strip()

    if raw.startswith("STN-"):
        return raw

    if re.match(r"^[A-Z0-9]+$", raw):
        return f"STN-{raw}"

    return raw


def normalize_product_id(raw: Optional[str]) -> Optional[str]:
    """Chuẩn hóa product alias về "PROD-PN"."""
    if raw is None or (isinstance(raw, str) and raw.strip() == ""):
        return None

    raw = str(raw).strip()

    for pattern, kind in PRODUCT_PATTERNS:
        m = pattern.match(raw)
        if m:
            return f"PROD-P{int(m.group(1))}"

    return raw


def normalize_component_id(raw: Optional[str]) -> Optional[str]:
    """Chuẩn hóa component alias về "COMP-CN"."""
    if raw is None or (isinstance(raw, str) and raw.strip() == ""):
        return None

    raw = str(raw).strip()

    for pattern, kind in COMPONENT_PATTERNS:
        m = pattern.match(raw)
        if m:
            return f"COMP-C{int(m.group(1))}"

    return raw


def normalize_batch_id(raw: Optional[str]) -> Optional[str]:
    """Chuẩn hóa batch alias về "BATCH-HT-XXX"."""
    if raw is None:
        return None
    raw = str(raw).strip()
    if raw.startswith("BATCH-HT-"):
        return raw
    if re.match(r"^B\d{2}$", raw):
        return f"BATCH-HT-{raw}"
    return raw
