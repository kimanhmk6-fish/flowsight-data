import networkx as nx
from typing import Optional


def reverse_bfs(
    G: nx.DiGraph,
    start_node: str,
    max_depth: int = 10,
    filter_fn: Optional[callable] = None,
) -> list:
    """Reverse BFS — truy ngược genealogy (Backward Cause)."""
    if start_node not in G:
        return []

    visited = set()
    result = []
    queue = [(start_node, 0)]

    while queue:
        node, depth = queue.pop(0)
        if depth > max_depth:
            continue
        for pred in G.predecessors(node):
            if pred in visited:
                continue
            if filter_fn and not filter_fn(pred, G):
                continue
            visited.add(pred)
            result.append({"node": pred, "depth": depth + 1})
            queue.append((pred, depth + 1))

    return result


def forward_bfs(
    G: nx.DiGraph,
    start_node: str,
    max_depth: int = 10,
    filter_fn: Optional[callable] = None,
) -> list:
    """Forward BFS — lan truyền xuôi (Forward Impact)."""
    if start_node not in G:
        return []

    visited = set()
    result = []
    queue = [(start_node, 0)]

    while queue:
        node, depth = queue.pop(0)
        if depth > max_depth:
            continue
        for succ in G.successors(node):
            if succ in visited:
                continue
            if filter_fn and not filter_fn(succ, G):
                continue
            visited.add(succ)
            result.append({"node": succ, "depth": depth + 1})
            queue.append((succ, depth + 1))

    return result


def find_common_ancestors(G: nx.DiGraph, nodes: list) -> set:
    """Tìm tổ tiên chung (Containment)."""
    if not nodes:
        return set()

    ancestors_per_node = []
    for n in nodes:
        if n not in G:
            continue
        anc = {n}
        for pred in nx.ancestors(G, n):
            anc.add(pred)
        ancestors_per_node.append(anc)

    if not ancestors_per_node:
        return set()

    return set.intersection(*ancestors_per_node)
