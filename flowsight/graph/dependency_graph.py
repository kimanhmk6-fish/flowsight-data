import networkx as nx
import pandas as pd
from .config import MASTER_DIR


def build_dependency_graph() -> nx.DiGraph:
    """Xây dependency graph giữa các stations từ routing."""
    print("\n[11C-3b] Building dependency graph...")

    G = nx.DiGraph()

    stations_path = MASTER_DIR / "dim_station.csv"
    routing_path = MASTER_DIR / "routing.csv"

    if not stations_path.exists() or not routing_path.exists():
        print("  ⚠ Missing dim_station.csv or routing.csv")
        return G

    stations = pd.read_csv(stations_path)
    routing = pd.read_csv(routing_path)

    for _, st in stations.iterrows():
        G.add_node(
            st["station_id"],
            station_name=st.get("station_name"),
            line_id=st.get("line_id"),
            stage=st.get("stage"),
            station_type=st.get("station_type"),
            cycle_time_s=st.get("cycle_time_s"),
        )

    for product, group in routing.groupby("product_id"):
        group = group.sort_values("seq_no")
        stations_seq = group["station_id"].tolist()

        for i in range(len(stations_seq) - 1):
            src = stations_seq[i]
            dst = stations_seq[i + 1]

            if G.has_edge(src, dst):
                G[src][dst]["product_count"] += 1
                G[src][dst]["products"].append(product)
            else:
                G.add_edge(
                    src, dst,
                    dependency_type="process_sequence",
                    product_count=1,
                    products=[product],
                )

    print(f"  ✓ Nodes: {G.number_of_nodes()}")
    print(f"  ✓ Edges: {G.number_of_edges()}")

    return G
