"""
frontend/graph_page.py
News Graph visualization page.
Shows the NetworkX graph of article relationships using matplotlib.
"""

import tkinter as tk
import customtkinter as ctk
import threading
from frontend.components import COLORS, FONTS, show_toast
from backend.graph_manager import get_graph_manager
from backend.graph_algorithms import (
    bfs, dfs, find_connected_components, get_most_connected_articles
)
from backend import database
from utils.helpers import truncate_text, prediction_color


class GraphPage(ctk.CTkFrame):
    """
    Interactive news relationship graph page.

    Features:
    - Matplotlib-based graph visualization
    - Node color coding by prediction (green=real, red=fake, yellow=suspicious)
    - BFS/DFS traversal controls
    - Connected components display
    - Article search within graph
    - Selected node details
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_primary"], **kwargs)
        self._selected_node = None
        self._build_ui()

    def _build_ui(self):
        # Top toolbar
        toolbar = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], height=60)
        toolbar.pack(fill="x", padx=0, pady=(0, 0))
        toolbar.pack_propagate(False)

        toolbar_inner = ctk.CTkFrame(toolbar, fg_color="transparent")
        toolbar_inner.pack(side="left", padx=20, pady=10, fill="x", expand=True)

        ctk.CTkLabel(toolbar_inner, text="🕸️  News Relationship Graph",
                     font=FONTS["heading"],
                     text_color=COLORS["text_primary"]).pack(side="left")

        ctk.CTkButton(toolbar, text="🔄 Refresh Graph",
                      font=FONTS["small"],
                      fg_color=COLORS["accent_purple"],
                      hover_color="#6d28d9",
                      height=32,
                      width=140,
                      command=self.refresh).pack(side="right", padx=16, pady=14)

        # Main content: graph canvas + right sidebar
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=3)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)

        # ── Graph Canvas ──────────────────────────────────────────
        self._canvas_frame = ctk.CTkFrame(main, fg_color=COLORS["bg_card"],
                                           corner_radius=0)
        self._canvas_frame.grid(row=0, column=0, sticky="nsew", padx=(12, 6),
                                 pady=12)

        self._empty_label = ctk.CTkLabel(
            self._canvas_frame,
            text="🕸️\n\nNo graph data yet.\n\nAnalyze some articles first,\nthen refresh this page.",
            font=FONTS["body"],
            text_color=COLORS["text_muted"],
            justify="center"
        )
        self._empty_label.pack(expand=True)

        # ── Right Sidebar ─────────────────────────────────────────
        sidebar = ctk.CTkScrollableFrame(main, fg_color=COLORS["bg_secondary"],
                                          width=280)
        sidebar.grid(row=0, column=1, sticky="nsew", padx=(6, 12), pady=12)

        # Graph stats
        ctk.CTkLabel(sidebar, text="📊 Graph Statistics",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", padx=12, pady=(12, 8))

        self._stats_frame = ctk.CTkFrame(sidebar, fg_color=COLORS["bg_card"],
                                          corner_radius=8)
        self._stats_frame.pack(fill="x", padx=8, pady=(0, 12))
        self._stats_labels = {}
        stat_keys = [("nodes", "Nodes"), ("edges", "Edges"),
                     ("components", "Clusters"), ("density", "Density")]
        for key, label in stat_keys:
            row = ctk.CTkFrame(self._stats_frame, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=4)
            ctk.CTkLabel(row, text=label + ":", font=FONTS["small"],
                         text_color=COLORS["text_muted"], width=80, anchor="w").pack(side="left")
            lbl = ctk.CTkLabel(row, text="0", font=FONTS["small"],
                               text_color=COLORS["accent_cyan"])
            lbl.pack(side="right")
            self._stats_labels[key] = lbl

        # Legend
        ctk.CTkLabel(sidebar, text="🎨 Legend",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", padx=12, pady=(0, 8))
        legend_frame = ctk.CTkFrame(sidebar, fg_color=COLORS["bg_card"], corner_radius=8)
        legend_frame.pack(fill="x", padx=8, pady=(0, 12))
        for pred, color, icon in [("REAL", COLORS["real"], "●"),
                                   ("FAKE", COLORS["fake"], "●"),
                                   ("SUSPICIOUS", COLORS["suspicious"], "●")]:
            lr = ctk.CTkFrame(legend_frame, fg_color="transparent")
            lr.pack(fill="x", padx=12, pady=3)
            ctk.CTkLabel(lr, text=icon, font=FONTS["body"],
                         text_color=color).pack(side="left")
            ctk.CTkLabel(lr, text=f" {pred}", font=FONTS["small"],
                         text_color=COLORS["text_secondary"]).pack(side="left")

        # BFS/DFS Controls
        ctk.CTkLabel(sidebar, text="🔁 Graph Traversal",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", padx=12, pady=(0, 8))

        traversal_frame = ctk.CTkFrame(sidebar, fg_color=COLORS["bg_card"], corner_radius=8)
        traversal_frame.pack(fill="x", padx=8, pady=(0, 12))

        ctk.CTkLabel(traversal_frame, text="Select Start Article:",
                     font=FONTS["small"],
                     text_color=COLORS["text_muted"]).pack(anchor="w", padx=12, pady=(10, 4))

        self._article_var = tk.StringVar(value="Select an article...")
        self._article_dropdown = ctk.CTkOptionMenu(
            traversal_frame,
            variable=self._article_var,
            values=["No articles yet"],
            font=FONTS["tiny"],
            fg_color=COLORS["bg_input"],
            button_color=COLORS["accent_purple"],
            button_hover_color="#6d28d9",
            width=240
        )
        self._article_dropdown.pack(padx=12, pady=(0, 8), fill="x")

        btn_row = ctk.CTkFrame(traversal_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=12, pady=(0, 12))

        ctk.CTkButton(btn_row, text="BFS",
                      font=FONTS["small"],
                      fg_color=COLORS["accent_cyan"],
                      hover_color="#0891b2",
                      height=32,
                      command=lambda: self._run_traversal("bfs")).pack(side="left", expand=True, padx=(0, 4))
        ctk.CTkButton(btn_row, text="DFS",
                      font=FONTS["small"],
                      fg_color="#8b5cf6",
                      hover_color="#7c3aed",
                      height=32,
                      command=lambda: self._run_traversal("dfs")).pack(side="left", expand=True, padx=(4, 0))

        # Traversal output
        self._traversal_output = ctk.CTkTextbox(
            traversal_frame,
            font=FONTS["mono_small"],
            fg_color=COLORS["bg_input"],
            text_color=COLORS["accent_cyan"],
            height=120,
            state="disabled"
        )
        self._traversal_output.pack(fill="x", padx=12, pady=(0, 12))

        # Connected Components
        ctk.CTkLabel(sidebar, text="🗂️ News Clusters",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", padx=12, pady=(0, 8))

        self._clusters_frame = ctk.CTkFrame(sidebar, fg_color=COLORS["bg_card"],
                                             corner_radius=8)
        self._clusters_frame.pack(fill="x", padx=8, pady=(0, 12))
        ctk.CTkLabel(self._clusters_frame, text="No clusters yet.",
                     font=FONTS["tiny"],
                     text_color=COLORS["text_muted"]).pack(padx=12, pady=12)

        # Most Connected
        ctk.CTkLabel(sidebar, text="⭐ Most Connected",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", padx=12, pady=(0, 8))

        self._top_nodes_frame = ctk.CTkFrame(sidebar, fg_color=COLORS["bg_card"],
                                              corner_radius=8)
        self._top_nodes_frame.pack(fill="x", padx=8, pady=(0, 12))

    def refresh(self):
        """Refresh the graph from the database and redraw."""
        graph_manager = get_graph_manager()
        graph_stats = graph_manager.get_graph_stats()

        # Update stats
        self._stats_labels["nodes"].configure(text=str(graph_stats.get("nodes", 0)))
        self._stats_labels["edges"].configure(text=str(graph_stats.get("edges", 0)))
        self._stats_labels["components"].configure(text=str(graph_stats.get("components", 0)))
        self._stats_labels["density"].configure(text=str(graph_stats.get("density", 0.0)))

        # Update article dropdown
        articles = database.get_all_articles()
        if articles:
            options = [f"{a['article_id']} — {truncate_text(a['headline'], 40)}" for a in articles]
            self._article_dropdown.configure(values=options)
            self._article_var.set(options[0])
        else:
            self._article_dropdown.configure(values=["No articles yet"])

        # Draw graph
        self._draw_graph(graph_manager.get_nx_graph())

        # Update clusters
        self._update_clusters(graph_manager.get_nx_graph())

        # Update top nodes
        self._update_top_nodes(graph_manager.get_nx_graph())

    def _draw_graph(self, graph):
        """Draw the NetworkX graph in the canvas frame."""
        # Clear canvas
        for widget in self._canvas_frame.winfo_children():
            widget.destroy()

        if graph.number_of_nodes() == 0:
            ctk.CTkLabel(self._canvas_frame,
                         text="🕸️\n\nNo graph data yet.\nAnalyze articles first.",
                         font=FONTS["body"],
                         text_color=COLORS["text_muted"],
                         justify="center").pack(expand=True)
            return

        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import matplotlib.patches as mpatches
            import networkx as nx
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

            fig, ax = plt.subplots(figsize=(9, 6))
            fig.patch.set_facecolor("#0f0f1a")
            ax.set_facecolor("#0f0f1a")

            # Layout
            if graph.number_of_nodes() <= 20:
                pos = nx.spring_layout(graph, k=2.5, iterations=60, seed=42)
            else:
                pos = nx.spring_layout(graph, k=1.5, iterations=30, seed=42)

            # Node colors
            node_colors = [graph.nodes[n].get("color", "#6b7280") for n in graph.nodes()]

            # Edge colors by type
            edge_colors_map = {
                "DUPLICATE": "#ef4444",
                "SIMILAR_CONTENT": "#f59e0b",
                "SAME_TOPIC": "#06b6d4",
                "SAME_SOURCE": "#8b5cf6",
                "RELATED_KEYWORDS": "#22c55e"
            }
            edge_colors = [
                edge_colors_map.get(graph[u][v].get("relationship_type", ""), "#4b5563")
                for u, v in graph.edges()
            ]

            # Draw edges
            nx.draw_networkx_edges(graph, pos, ax=ax, edge_color=edge_colors,
                                   alpha=0.6, arrows=True, arrowsize=12,
                                   connectionstyle="arc3,rad=0.1",
                                   width=1.5)

            # Draw nodes
            nx.draw_networkx_nodes(graph, pos, ax=ax,
                                   node_color=node_colors,
                                   node_size=400, alpha=0.9)

            # Node labels (short IDs)
            labels = {}
            for node in graph.nodes():
                labels[node] = node.split("-")[1][:6] if "-" in node else node[:6]
            nx.draw_networkx_labels(graph, pos, labels, ax=ax,
                                    font_size=7, font_color="#f1f5f9",
                                    font_weight="bold")

            ax.set_title("News Article Relationship Graph",
                         color="#f1f5f9", fontsize=11, pad=12)
            ax.axis("off")

            # Legend
            legend_patches = [
                mpatches.Patch(color=COLORS["real"], label="REAL"),
                mpatches.Patch(color=COLORS["fake"], label="FAKE"),
                mpatches.Patch(color=COLORS["suspicious"], label="SUSPICIOUS"),
                mpatches.Patch(color="#ef4444", label="DUPLICATE edge"),
                mpatches.Patch(color="#f59e0b", label="SIMILAR edge"),
                mpatches.Patch(color="#06b6d4", label="SAME TOPIC edge"),
            ]
            ax.legend(handles=legend_patches, loc="upper left",
                      facecolor="#1a1a2e", edgecolor="#1e293b",
                      labelcolor="#94a3b8", fontsize=7)

            plt.tight_layout()
            canvas = FigureCanvasTkAgg(fig, master=self._canvas_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            plt.close(fig)

        except ImportError:
            ctk.CTkLabel(self._canvas_frame,
                         text="Install matplotlib to see graph visualization.",
                         font=FONTS["body"],
                         text_color=COLORS["text_muted"]).pack(expand=True)
        except Exception as e:
            ctk.CTkLabel(self._canvas_frame,
                         text=f"Graph error: {str(e)[:100]}",
                         font=FONTS["tiny"],
                         text_color=COLORS["text_muted"]).pack(expand=True)

    def _run_traversal(self, algo: str):
        """Run BFS or DFS from the selected article."""
        selected = self._article_var.get()
        if not selected or selected in ("Select an article...", "No articles yet"):
            show_toast(self.winfo_toplevel(), "Please select an article first.",
                       color=COLORS["warning"])
            return

        article_id = selected.split(" — ")[0].strip()
        graph = get_graph_manager().get_nx_graph()

        if algo == "bfs":
            result = bfs(graph, article_id, max_depth=3)
        else:
            result = dfs(graph, article_id, max_nodes=30)

        # Display result
        self._traversal_output.configure(state="normal")
        self._traversal_output.delete("1.0", "end")

        if result.get("error"):
            self._traversal_output.insert("end", f"Error: {result['error']}")
        else:
            order = result.get("traversal_order", [])
            algo_name = "BFS" if algo == "bfs" else "DFS"
            self._traversal_output.insert("end", f"Algorithm: {algo_name}\n")
            self._traversal_output.insert("end", f"Start: {article_id}\n")
            self._traversal_output.insert("end", f"Visited: {result.get('visited_count', 0)} nodes\n\n")
            self._traversal_output.insert("end", "Traversal Order:\n")

            for i, node in enumerate(order):
                short_id = node.split("-")[1][:8] if "-" in node else node[:8]
                arrow = " → " if i < len(order) - 1 else ""
                if algo == "bfs" and "levels" in result:
                    level = result["levels"].get(node, 0)
                    self._traversal_output.insert("end", f"[L{level}] {short_id}{arrow}")
                else:
                    self._traversal_output.insert("end", f"{short_id}{arrow}")
                if (i + 1) % 4 == 0:
                    self._traversal_output.insert("end", "\n")

        self._traversal_output.configure(state="disabled")

    def _update_clusters(self, graph):
        """Update the connected components / clusters display."""
        for widget in self._clusters_frame.winfo_children():
            widget.destroy()

        result = find_connected_components(graph)
        components = result.get("components", [])

        if not components:
            ctk.CTkLabel(self._clusters_frame, text="No clusters yet.",
                         font=FONTS["tiny"],
                         text_color=COLORS["text_muted"]).pack(padx=12, pady=12)
            return

        for comp in components[:5]:  # Show top 5 clusters
            row = ctk.CTkFrame(self._clusters_frame, fg_color=COLORS["bg_secondary"],
                               corner_radius=6)
            row.pack(fill="x", padx=8, pady=4)

            ctk.CTkLabel(row,
                         text=f"Cluster {comp['id']}: {comp['size']} articles",
                         font=FONTS["small"],
                         text_color=COLORS["text_primary"]).pack(anchor="w", padx=10, pady=(6, 2))
            ctk.CTkLabel(row,
                         text=f"✅ {comp['real_count']} Real  ❌ {comp['fake_count']} Fake  ⚠️ {comp['suspicious_count']} Suspicious",
                         font=FONTS["tiny"],
                         text_color=COLORS["text_muted"]).pack(anchor="w", padx=10, pady=(0, 6))

    def _update_top_nodes(self, graph):
        """Update the most connected articles list."""
        for widget in self._top_nodes_frame.winfo_children():
            widget.destroy()

        top = get_most_connected_articles(graph, top_n=5)
        if not top:
            ctk.CTkLabel(self._top_nodes_frame, text="No data yet.",
                         font=FONTS["tiny"],
                         text_color=COLORS["text_muted"]).pack(padx=12, pady=12)
            return

        for item in top:
            row = ctk.CTkFrame(self._top_nodes_frame, fg_color=COLORS["bg_secondary"],
                               corner_radius=6)
            row.pack(fill="x", padx=8, pady=3)
            ctk.CTkLabel(row,
                         text=truncate_text(item.get("headline", ""), 35),
                         font=FONTS["tiny"],
                         text_color=COLORS["text_primary"]).pack(anchor="w", padx=10, pady=(6, 2))
            ctk.CTkLabel(row,
                         text=f"{item.get('degree', 0)} connections · {item.get('prediction', 'UNKNOWN')}",
                         font=FONTS["tiny"],
                         text_color=COLORS["text_muted"]).pack(anchor="w", padx=10, pady=(0, 6))
