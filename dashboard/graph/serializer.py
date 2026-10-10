import pickle
import networkx as nx
from .config import GRAPH_DIR


def save_graph(G: nx.DiGraph, name: str):
    """Save graph dạng pickle."""
    path = GRAPH_DIR / f"{name}.pkl"
    with open(path, "wb") as f:
        pickle.dump(G, f)
    print(f"  ✓ Saved: {path.name}")


def load_graph(name: str) -> nx.DiGraph:
    """Load graph từ pickle."""
    path = GRAPH_DIR / f"{name}.pkl"
    if not path.exists():
        return nx.DiGraph()
    with open(path, "rb") as f:
        return pickle.load(f)


def export_graphml(G: nx.DiGraph, name: str):
    """Export graph dạng GraphML (visualize với Gephi/yEd)."""
    path = GRAPH_DIR / f"{name}.graphml"

    for u, v, data in G.edges(data=True):
        for key, val in list(data.items()):
            if isinstance(val, list):
                G[u][v][key] = str(val)
            elif val is None:
                G[u][v][key] = ""

    for n, data in G.nodes(data=True):
        for key, val in list(data.items()):
            if isinstance(val, list):
                G.nodes[n][key] = str(val)
            elif val is None:
                G.nodes[n][key] = ""

    try:
        nx.write_graphml(G, path)
        print(f"  ✓ Exported: {path.name}")
    except Exception as e:
        print(f"  ⚠ Export GraphML failed: {e}")
