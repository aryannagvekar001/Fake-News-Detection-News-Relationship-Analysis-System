"""
backend/graph_algorithms.py
BFS, DFS, and Connected Components algorithms for the news graph.

DSA CONCEPT: Graph Traversal
- BFS (Breadth-First Search): Explore layer by layer using a QUEUE.
- DFS (Depth-First Search): Explore as deep as possible using a STACK (or recursion).

These algorithms answer questions like:
- "Which articles are within 2 relationships of Article A?" (BFS)
- "Can I reach Article C from Article A through any path?" (DFS)
- "Which group of articles form a cluster?" (Connected Components)
"""

from collections import deque  # DSA: Queue implementation for BFS
from typing import List, Dict, Set, Tuple, Optional
import networkx as nx


def bfs(graph: nx.DiGraph, start_node: str, max_depth: int = 3) -> Dict:
    """
    DSA CONCEPT: Breadth-First Search (BFS)

    Uses a QUEUE (FIFO) data structure.
    Explores all neighbors at depth d before moving to depth d+1.

    Algorithm:
    1. Enqueue start node
    2. Mark start as visited
    3. While queue is not empty:
       a. Dequeue a node
       b. If depth < max_depth, enqueue its unvisited neighbors
       c. Mark neighbors as visited
    4. Return traversal order

    Time Complexity: O(V + E) where V = nodes, E = edges
    Space Complexity: O(V) for the visited set and queue

    Used for: Finding articles within N relationship levels of a given article.
    """
    if not graph.has_node(start_node):
        return {
            "traversal_order": [],
            "levels": {},
            "visited_count": 0,
            "error": f"Node '{start_node}' not found in graph"
        }

    # ── Initialize ──────────────────────────────────────────────
    visited: Set[str] = set()
    queue: deque = deque()  # FIFO Queue
    traversal_order: List[str] = []
    levels: Dict[str, int] = {}  # node → depth level

    # Start BFS from the given node
    queue.append((start_node, 0))  # (node, depth)
    visited.add(start_node)
    levels[start_node] = 0

    # ── BFS Loop ─────────────────────────────────────────────────
    while queue:
        current_node, depth = queue.popleft()  # Dequeue (FIFO)
        traversal_order.append(current_node)

        if depth >= max_depth:
            continue

        # Get all neighbors (both directions for undirected traversal)
        neighbors = set(graph.successors(current_node)) | set(graph.predecessors(current_node))

        for neighbor in sorted(neighbors):  # Sort for deterministic output
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, depth + 1))  # Enqueue
                levels[neighbor] = depth + 1

    # Build result by depth levels
    level_groups: Dict[int, List[str]] = {}
    for node, level in levels.items():
        if level not in level_groups:
            level_groups[level] = []
        level_groups[level].append(node)

    return {
        "traversal_order": traversal_order,
        "levels": levels,
        "level_groups": level_groups,
        "visited_count": len(visited),
        "start_node": start_node,
        "max_depth": max_depth,
        "algorithm": "BFS (Breadth-First Search)",
        "data_structure": "Queue (FIFO) — deque"
    }


def dfs(graph: nx.DiGraph, start_node: str, max_nodes: int = 50) -> Dict:
    """
    DSA CONCEPT: Depth-First Search (DFS)

    Uses a STACK (LIFO) data structure (implemented via Python call stack / explicit stack).
    Explores as deep as possible before backtracking.

    Algorithm:
    1. Push start node to stack
    2. While stack is not empty:
       a. Pop a node
       b. If not visited, mark as visited and record
       c. Push all unvisited neighbors to stack
    3. Return traversal order

    Time Complexity: O(V + E)
    Space Complexity: O(V)

    Used for: Exploring all articles in a connected cluster.
    """
    if not graph.has_node(start_node):
        return {
            "traversal_order": [],
            "visited_count": 0,
            "error": f"Node '{start_node}' not found in graph"
        }

    # ── Initialize ──────────────────────────────────────────────
    visited: Set[str] = set()
    stack: List[str] = []  # LIFO Stack
    traversal_order: List[str] = []
    parent: Dict[str, Optional[str]] = {start_node: None}

    # ── DFS using explicit stack ──────────────────────────────────
    stack.append(start_node)

    while stack and len(traversal_order) < max_nodes:
        current_node = stack.pop()  # Pop from stack (LIFO)

        if current_node in visited:
            continue

        visited.add(current_node)
        traversal_order.append(current_node)

        # Get neighbors (both directions)
        neighbors = set(graph.successors(current_node)) | set(graph.predecessors(current_node))

        for neighbor in sorted(neighbors, reverse=True):  # Reverse sort for consistent order
            if neighbor not in visited:
                stack.append(neighbor)
                if neighbor not in parent:
                    parent[neighbor] = current_node

    return {
        "traversal_order": traversal_order,
        "visited_count": len(visited),
        "parent_map": parent,
        "start_node": start_node,
        "algorithm": "DFS (Depth-First Search)",
        "data_structure": "Stack (LIFO) — list"
    }


def find_connected_components(graph: nx.DiGraph) -> Dict:
    """
    DSA CONCEPT: Connected Components

    A connected component is a maximal set of nodes where every node
    is reachable from every other node (ignoring edge direction).

    Algorithm:
    - Use BFS/DFS from each unvisited node to find all nodes in its component.
    - Each call to BFS/DFS from a new unvisited node discovers a new component.

    Time Complexity: O(V + E)

    Used for: Identifying clusters of related news articles.
    """
    if graph.number_of_nodes() == 0:
        return {"components": [], "count": 0, "largest": 0}

    # Convert to undirected for component analysis
    undirected = graph.to_undirected()
    components_raw = list(nx.connected_components(undirected))

    # Sort by size descending
    components_raw.sort(key=len, reverse=True)

    components = []
    for i, component in enumerate(components_raw, 1):
        nodes = list(component)
        # Get prediction stats for this cluster
        predictions = []
        for node_id in nodes:
            if graph.has_node(node_id):
                pred = graph.nodes[node_id].get("prediction", "UNKNOWN")
                predictions.append(pred)

        fake_count = predictions.count("FAKE")
        real_count = predictions.count("REAL")
        suspicious_count = predictions.count("SUSPICIOUS")

        # Internal edges (relationships within this component)
        internal_edges = 0
        for a, b in graph.edges():
            if a in component and b in component:
                internal_edges += 1

        components.append({
            "id": i,
            "nodes": nodes,
            "size": len(nodes),
            "real_count": real_count,
            "fake_count": fake_count,
            "suspicious_count": suspicious_count,
            "internal_edges": internal_edges,
            "dominant": "FAKE" if fake_count > real_count else ("REAL" if real_count > fake_count else "MIXED")
        })

    return {
        "components": components,
        "count": len(components),
        "largest": len(components_raw[0]) if components_raw else 0,
        "total_nodes": graph.number_of_nodes(),
        "total_edges": graph.number_of_edges()
    }


def find_shortest_path(graph: nx.DiGraph, source: str, target: str) -> Dict:
    """
    Find the shortest path between two articles using BFS.
    Returns the path as a list of article IDs.
    """
    if not graph.has_node(source) or not graph.has_node(target):
        return {"path": [], "length": -1, "found": False}

    try:
        undirected = graph.to_undirected()
        path = nx.shortest_path(undirected, source=source, target=target)
        return {
            "path": path,
            "length": len(path) - 1,
            "found": True
        }
    except nx.NetworkXNoPath:
        return {"path": [], "length": -1, "found": False}
    except nx.NodeNotFound:
        return {"path": [], "length": -1, "found": False}


def get_most_connected_articles(graph: nx.DiGraph, top_n: int = 5) -> List[Dict]:
    """Return the top N articles with the most connections (highest degree)."""
    if graph.number_of_nodes() == 0:
        return []

    degree_list = [(node, graph.degree(node)) for node in graph.nodes()]
    degree_list.sort(key=lambda x: x[1], reverse=True)

    result = []
    for node_id, degree in degree_list[:top_n]:
        data = dict(graph.nodes[node_id])
        result.append({
            "article_id": node_id,
            "degree": degree,
            "headline": data.get("headline", "")[:60],
            "prediction": data.get("prediction", "UNKNOWN"),
            "source": data.get("source", "Unknown")
        })
    return result
