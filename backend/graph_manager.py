"""
backend/graph_manager.py
Graph data structure management using NetworkX.

DSA CONCEPT: Graph
- A graph G = (V, E) where V = vertices (nodes) and E = edges.
- Here: Articles are nodes, relationships are edges.
- We use a directed graph (DiGraph) where relationships have direction.

Why represent news as a graph?
- Captures relationships between articles
- Enables traversal algorithms (BFS, DFS)
- Identifies clusters of related misinformation
- Reveals how fake news spreads through sources
"""

import networkx as nx
from typing import Optional, List, Dict, Tuple, Any

# Relationship types (edge labels)
REL_SIMILAR_CONTENT = "SIMILAR_CONTENT"
REL_SAME_TOPIC = "SAME_TOPIC"
REL_SAME_SOURCE = "SAME_SOURCE"
REL_DUPLICATE = "DUPLICATE"
REL_RELATED_KEYWORDS = "RELATED_KEYWORDS"

# Similarity thresholds
SIMILAR_THRESHOLD = 0.4    # Cosine similarity >= 0.4 → SIMILAR_CONTENT
DUPLICATE_THRESHOLD = 0.9  # Cosine similarity >= 0.9 → DUPLICATE

# Node colors by prediction (for visualization)
NODE_COLORS = {
    "REAL": "#22c55e",       # Green
    "FAKE": "#ef4444",       # Red
    "SUSPICIOUS": "#f59e0b", # Amber
    "UNKNOWN": "#6b7280"     # Gray
}


class GraphManager:
    """
    Manages the news article relationship graph.

    Uses NetworkX DiGraph internally, but provides a clean API
    that mirrors what a custom adjacency list would look like.

    Graph Properties:
    - Nodes: Article objects with metadata attributes
    - Edges: Relationship objects with type and similarity score
    - Directed: Edge A→B means A is related to B
    """

    def __init__(self):
        # DSA: Directed Graph (adjacency list representation internally)
        self.graph = nx.DiGraph()

    def add_article_node(self, article_id: str, data: Dict) -> None:
        """
        Add an article as a node in the graph.

        Node attributes:
        - article_id: unique identifier
        - headline: article title
        - source: publisher
        - prediction: REAL/FAKE/SUSPICIOUS
        - topic: detected topic
        - pub_date: publication date
        - confidence: model confidence
        """
        self.graph.add_node(article_id, **{
            "label": article_id,
            "headline": data.get("headline", "")[:50],
            "source": data.get("source", "Unknown"),
            "prediction": data.get("prediction", "UNKNOWN"),
            "topic": data.get("topic", "General"),
            "pub_date": data.get("pub_date", ""),
            "confidence": data.get("confidence", 0.0),
            "color": NODE_COLORS.get(data.get("prediction", "UNKNOWN"), "#6b7280")
        })

    def remove_article_node(self, article_id: str) -> None:
        """Remove an article node and all its edges from the graph."""
        if self.graph.has_node(article_id):
            self.graph.remove_node(article_id)

    def add_relationship(self, a_id: str, b_id: str, rel_type: str, score: float) -> None:
        """
        Add a directed edge between two article nodes.

        Edge attributes:
        - relationship_type: SIMILAR_CONTENT, SAME_TOPIC, etc.
        - similarity_score: float between 0.0 and 1.0
        - weight: used by graph algorithms (= similarity_score)
        """
        if not self.graph.has_node(a_id) or not self.graph.has_node(b_id):
            return
        # Avoid self-loops
        if a_id == b_id:
            return
        # Only add if edge doesn't exist or update with higher score
        if self.graph.has_edge(a_id, b_id):
            existing_score = self.graph[a_id][b_id].get("similarity_score", 0)
            if score > existing_score:
                self.graph[a_id][b_id]["similarity_score"] = score
                self.graph[a_id][b_id]["relationship_type"] = rel_type
        else:
            self.graph.add_edge(a_id, b_id, **{
                "relationship_type": rel_type,
                "similarity_score": score,
                "weight": score,
                "label": f"{rel_type}\n{score:.2f}"
            })

    def has_node(self, article_id: str) -> bool:
        """Check if an article node exists in the graph."""
        return self.graph.has_node(article_id)

    def get_neighbors(self, article_id: str) -> List[str]:
        """
        Get all directly connected articles (both in-neighbors and out-neighbors).
        Returns a list of article IDs.
        """
        if not self.graph.has_node(article_id):
            return []
        # Combine successors and predecessors for undirected view
        neighbors = set(self.graph.successors(article_id))
        neighbors |= set(self.graph.predecessors(article_id))
        neighbors.discard(article_id)
        return list(neighbors)

    def get_node_data(self, article_id: str) -> Optional[Dict]:
        """Return the data dictionary for a specific node."""
        if self.graph.has_node(article_id):
            return dict(self.graph.nodes[article_id])
        return None

    def get_edge_data(self, a_id: str, b_id: str) -> Optional[Dict]:
        """Return edge data between two articles."""
        if self.graph.has_edge(a_id, b_id):
            return dict(self.graph[a_id][b_id])
        return None

    def get_all_nodes(self) -> List[Dict]:
        """Return all nodes with their data."""
        result = []
        for node_id, data in self.graph.nodes(data=True):
            result.append({"id": node_id, **data})
        return result

    def get_all_edges(self) -> List[Dict]:
        """Return all edges with their data."""
        result = []
        for a, b, data in self.graph.edges(data=True):
            result.append({"from": a, "to": b, **data})
        return result

    def get_node_degree(self, article_id: str) -> int:
        """Return the total degree (in + out) of a node."""
        if not self.graph.has_node(article_id):
            return 0
        return self.graph.degree(article_id)

    def node_count(self) -> int:
        """Total number of nodes in the graph."""
        return self.graph.number_of_nodes()

    def edge_count(self) -> int:
        """Total number of edges in the graph."""
        return self.graph.number_of_edges()

    def get_graph_stats(self) -> Dict:
        """Return comprehensive graph statistics."""
        if self.graph.number_of_nodes() == 0:
            return {
                "nodes": 0, "edges": 0, "density": 0.0,
                "components": 0, "largest_component": 0,
                "avg_degree": 0.0, "isolated_nodes": 0
            }

        undirected = self.graph.to_undirected()
        components = list(nx.connected_components(undirected))
        degrees = [d for _, d in self.graph.degree()]

        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "density": round(nx.density(self.graph), 4),
            "components": len(components),
            "largest_component": max(len(c) for c in components) if components else 0,
            "avg_degree": round(sum(degrees) / len(degrees), 2) if degrees else 0.0,
            "isolated_nodes": sum(1 for d in degrees if d == 0)
        }

    def load_from_database(self, articles: List[Dict], relationships: List[Dict]) -> None:
        """
        Rebuild the graph from database records.
        Called on application startup.
        """
        # Add all article nodes
        for article in articles:
            self.add_article_node(article["article_id"], article)

        # Add all relationship edges
        for rel in relationships:
            self.add_relationship(
                rel["article_id_a"],
                rel["article_id_b"],
                rel["relationship_type"],
                rel["similarity_score"]
            )

    def find_related_by_type(self, article_id: str, rel_type: str) -> List[str]:
        """Find all articles connected by a specific relationship type."""
        related = []
        for a, b, data in self.graph.edges(data=True):
            if data.get("relationship_type") == rel_type:
                if a == article_id:
                    related.append(b)
                elif b == article_id:
                    related.append(a)
        return list(set(related))

    def get_nx_graph(self) -> nx.DiGraph:
        """Return the underlying NetworkX graph for algorithms and visualization."""
        return self.graph


# Global singleton — shared across the application
_graph_manager_instance: Optional[GraphManager] = None


def get_graph_manager() -> GraphManager:
    """Get the global GraphManager instance (singleton pattern)."""
    global _graph_manager_instance
    if _graph_manager_instance is None:
        _graph_manager_instance = GraphManager()
    return _graph_manager_instance


def reset_graph_manager() -> GraphManager:
    """Reset and return a new GraphManager instance."""
    global _graph_manager_instance
    _graph_manager_instance = GraphManager()
    return _graph_manager_instance
