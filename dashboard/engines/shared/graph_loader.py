"""
graph_loader.py — Load canonical tables + NetworkX graph.
"""
import pandas as pd
from flowsight.engines.config import CANONICAL_DIR, GRAPH_DIR
from flowsight.graph.serializer import load_graph


def load_canonical_tables() -> dict:
    """Load 8 canonical tables từ data/canonical/."""
    tables = {}
    for name in ["lot", "lot_edge", "lot_event", "material_consumption",
                 "jt_order", "jt_allocation", "shipment", "qc_result"]:
        path = CANONICAL_DIR / f"{name}.parquet"
        if path.exists():
            tables[name] = pd.read_parquet(path)
    return tables


def load_genealogy_graph():
    """Load NetworkX genealogy graph."""
    return load_graph("genealogy")


def load_dependency_graph():
    """Load NetworkX dependency graph."""
    return load_graph("dependency")
