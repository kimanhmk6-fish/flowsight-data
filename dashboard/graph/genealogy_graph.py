import networkx as nx
import pandas as pd
from .config import CANONICAL_DIR, GRAPH_DIR


def build_genealogy_graph() -> nx.DiGraph:
    """Xây genealogy DAG từ lot.parquet + lot_edge.parquet."""
    print("\n[11C-3a] Building genealogy graph...")

    G = nx.DiGraph()

    # Load tables
    lot_path = CANONICAL_DIR / "lot.parquet"
    edge_path = CANONICAL_DIR / "lot_edge.parquet"

    if not lot_path.exists() or not edge_path.exists():
        print("  ⚠ Missing lot.parquet or lot_edge.parquet")
        return G

    lots = pd.read_parquet(lot_path)
    edges = pd.read_parquet(edge_path)

    # Add nodes
    for _, lot in lots.iterrows():
        G.add_node(
            lot["lot_id"],
            product_id=lot.get("product_id"),
            qty=int(lot["qty"]) if pd.notna(lot.get("qty")) else 0,
            created_ts=str(lot.get("created_ts")),
            line_id=lot.get("line_id"),
            node_type="LOT",
        )

    # Add edges
    for _, edge in edges.iterrows():
        parent = edge["parent_lot_id"]
        child = edge["child_lot_id"]

        # Node cha có thể là BATCH (chưa có trong lots)
        if parent not in G:
            G.add_node(parent, node_type="BATCH")
        if child not in G:
            G.add_node(child, node_type="LOT")

        G.add_edge(
            parent, child,
            edge_id=edge["edge_id"],
            edge_type=edge["edge_type"],
            qty=int(edge["qty"]) if pd.notna(edge["qty"]) else None,
            confidence=float(edge["confidence"]) if pd.notna(edge["confidence"]) else 1.0,
            evidence=edge.get("evidence", ""),
        )

    print(f"  ✓ Nodes: {G.number_of_nodes()}")
    print(f"  ✓ Edges: {G.number_of_edges()}")
    print(f"  ✓ Is DAG: {nx.is_directed_acyclic_graph(G)}")

    return G


def query_upstream(G: nx.DiGraph, lot_id: str, max_depth: int = 10) -> list:
    """Truy ngược: tìm ancestors."""
    if lot_id not in G:
        return []

    ancestors = set()
    queue = [(lot_id, 0)]
    while queue:
        node, depth = queue.pop(0)
        if depth >= max_depth:
            continue
        for pred in G.predecessors(node):
            if pred not in ancestors:
                ancestors.add(pred)
                queue.append((pred, depth + 1))
    return list(ancestors)


def query_downstream(G: nx.DiGraph, lot_id: str, max_depth: int = 10) -> list:
    """Truy xuôi: tìm descendants."""
    if lot_id not in G:
        return []

    descendants = set()
    queue = [(lot_id, 0)]
    while queue:
        node, depth = queue.pop(0)
        if depth >= max_depth:
            continue
        for succ in G.successors(node):
            if succ not in descendants:
                descendants.add(succ)
                queue.append((succ, depth + 1))
    return list(descendants)


def get_full_path(G: nx.DiGraph, from_lot: str, to_lot: str) -> list:
    """Tìm đường đi ngắn nhất."""
    try:
        return nx.shortest_path(G, source=from_lot, target=to_lot)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return []
