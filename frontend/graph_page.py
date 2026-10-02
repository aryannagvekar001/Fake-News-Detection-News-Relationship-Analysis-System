"""
frontend/graph_page.py
News Graph visualization page — simplified and beginner-friendly.

Redesigned to be instantly understandable:
- Big legend with plain-English explanations
- Node cards listed below the graph for easy reading
- Simple stats in plain language
- "How it works" explainer panel
"""

import tkinter as tk
import customtkinter as ctk
from frontend.components import COLORS, FONTS, show_toast
from backend.graph_manager import get_graph_manager
from backend.graph_algorithms import (
    bfs, dfs, find_connected_components, get_most_connected_articles
)
from backend import database
from utils.helpers import truncate_text, prediction_color


class GraphPage(ctk.CTkFrame):
    """
    News article relationship graph page — redesigned for clarity.

    Layout:
    - Top: plain-English "How it works" banner
    - Left: graph canvas with big clear legend
    - Right: easy-to-read stats, article list, cluster summary
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_primary"], **kwargs)
        self._selected_node = None
        self._build_ui()

    def _build_ui(self):
        # ── Top toolbar ───────────────────────────────────────────
        toolbar = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], height=56)
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)

        ctk.CTkLabel(toolbar, text="🕸️  News Relationship Graph",
                     font=FONTS["heading"],
                     text_color=COLORS["text_primary"]).pack(side="left", padx=20, pady=14)

        ctk.CTkButton(toolbar, text="🔄 Refresh",
                      font=FONTS["small"],
                      fg_color=COLORS["accent_purple"],
                      hover_color="#6d28d9",
                      height=32,
                      width=110,
                      command=self.refresh).pack(side="right", padx=16, pady=12)

        # ── "How it works" banner ─────────────────────────────────
        how_frame = ctk.CTkFrame(self, fg_color="#0f2d40", corner_radius=0)
        how_frame.pack(fill="x", padx=0, pady=0)

        how_inner = ctk.CTkFrame(how_frame, fg_color="transparent")
        how_inner.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(how_inner,
                     text="💡 What is this graph?  Each circle (●) = one news article.  "
                          "Lines between circles = articles that are related.  "
                          "Green = Likely Real  ·  Red = Likely Fake  ·  Yellow = Suspicious",
                     font=FONTS["small"],
                     text_color="#7dd3fc",
                     wraplength=1200,
                     justify="left").pack(anchor="w")

        # ── Main split: canvas + sidebar ─────────────────────────
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=3)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)

        # ── Left: Graph canvas ────────────────────────────────────
        self._canvas_frame = ctk.CTkFrame(main, fg_color=COLORS["bg_card"],
                                          corner_radius=0)
        self._canvas_frame.grid(row=0, column=0, sticky="nsew",
                                padx=(12, 6), pady=12)

        self._empty_label = ctk.CTkLabel(
            self._canvas_frame,
            text="🕸️\n\nNo articles analyzed yet.\n\nGo to 'Analyze News', analyze a few articles,\nthen come back and click Refresh.",
            font=FONTS["body"],
            text_color=COLORS["text_muted"],
            justify="center"
        )
        self._empty_label.pack(expand=True)

        # ── Right: Sidebar ─────────────────────────────────────────
        sidebar = ctk.CTkScrollableFrame(main, fg_color=COLORS["bg_secondary"],
                                         width=290)
        sidebar.grid(row=0, column=1, sticky="nsew", padx=(6, 12), pady=12)

        # ── SECTION 1: Simple stats ───────────────────────────────
        stats_card = ctk.CTkFrame(sidebar, fg_color=COLORS["bg_card"], corner_radius=10)
        stats_card.pack(fill="x", padx=8, pady=(12, 8))

        ctk.CTkLabel(stats_card, text="📊 Graph at a Glance",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", padx=14, pady=(12, 6))

        self._stat_labels = {}
        stat_defs = [
            ("articles", "Total Articles", "0", COLORS["accent_cyan"]),
            ("connections", "Total Connections", "0", COLORS["accent_purple"]),
            ("clusters", "News Clusters", "0", COLORS["warning"]),
        ]
        for key, label, val, color in stat_defs:
            row = ctk.CTkFrame(stats_card, fg_color=COLORS["bg_secondary"], corner_radius=6)
            row.pack(fill="x", padx=10, pady=3)
            ctk.CTkLabel(row, text=label,
                         font=FONTS["small"],
                         text_color=COLORS["text_muted"],
                         anchor="w").pack(side="left", padx=10, pady=8)
            lbl = ctk.CTkLabel(row, text=val,
                               font=FONTS["subheading"],
                               text_color=color)
            lbl.pack(side="right", padx=10)
            self._stat_labels[key] = lbl

        # ── SECTION 2: Legend ─────────────────────────────────────
        legend_card = ctk.CTkFrame(sidebar, fg_color=COLORS["bg_card"], corner_radius=10)
        legend_card.pack(fill="x", padx=8, pady=(0, 8))

        ctk.CTkLabel(legend_card, text="🎨 What the Colors Mean",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", padx=14, pady=(12, 6))

        node_legend = [
            (COLORS["real"],       "●", "REAL article",       "Model thinks it's genuine news"),
            (COLORS["fake"],       "●", "FAKE article",       "Model thinks it's misinformation"),
            (COLORS["suspicious"], "●", "SUSPICIOUS article", "Model is not sure either way"),
        ]
        for color, icon, title, desc in node_legend:
            row = ctk.CTkFrame(legend_card, fg_color=COLORS["bg_secondary"], corner_radius=6)
            row.pack(fill="x", padx=10, pady=3)
            ctk.CTkLabel(row, text=icon, font=("Segoe UI", 16),
                         text_color=color, width=28).pack(side="left", padx=(10, 4), pady=6)
            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(side="left", fill="x", expand=True, pady=6)
            ctk.CTkLabel(inner, text=title, font=FONTS["small"],
                         text_color=COLORS["text_primary"], anchor="w").pack(anchor="w")
            ctk.CTkLabel(inner, text=desc, font=FONTS["tiny"],
                         text_color=COLORS["text_muted"], anchor="w").pack(anchor="w")

        # Line/edge legend
        ctk.CTkLabel(legend_card, text="Line (connection) types:",
                     font=FONTS["small"],
                     text_color=COLORS["text_muted"]).pack(anchor="w", padx=14, pady=(8, 4))

        edge_legend = [
            ("#ef4444", "— DUPLICATE",      "Nearly identical article"),
            ("#f59e0b", "— SIMILAR",        "Similar content"),
            ("#06b6d4", "— SAME TOPIC",     "Same news topic"),
            ("#8b5cf6", "— SAME SOURCE",    "Same publisher"),
        ]
        for color, line, desc in edge_legend:
            row = ctk.CTkFrame(legend_card, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=1)
            ctk.CTkLabel(row, text=line, font=FONTS["small"],
                         text_color=color, width=90, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=desc, font=FONTS["tiny"],
                         text_color=COLORS["text_muted"], anchor="w").pack(side="left")

        ctk.CTkFrame(legend_card, fg_color="transparent", height=8).pack()

        # ── SECTION 3: Article List (easy to read) ────────────────
        ctk.CTkLabel(sidebar, text="📰 Articles in Graph",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", padx=12, pady=(4, 6))

        self._articles_frame = ctk.CTkFrame(sidebar, fg_color=COLORS["bg_card"],
                                            corner_radius=10)
        self._articles_frame.pack(fill="x", padx=8, pady=(0, 8))
        ctk.CTkLabel(self._articles_frame, text="No articles yet.",
                     font=FONTS["tiny"],
                     text_color=COLORS["text_muted"]).pack(padx=12, pady=12)

        # ── SECTION 4: News Clusters ──────────────────────────────
        ctk.CTkLabel(sidebar, text="🗂️ News Clusters (Groups)",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", padx=12, pady=(4, 6))

        ctk.CTkLabel(sidebar,
                     text="Articles that are connected to each other form a cluster. "
                          "A large cluster of fake articles could indicate a coordinated misinformation campaign.",
                     font=FONTS["tiny"],
                     text_color=COLORS["text_muted"],
                     wraplength=270,
                     justify="left").pack(anchor="w", padx=12, pady=(0, 6))

        self._clusters_frame = ctk.CTkFrame(sidebar, fg_color=COLORS["bg_card"],
                                            corner_radius=10)
        self._clusters_frame.pack(fill="x", padx=8, pady=(0, 12))
        ctk.CTkLabel(self._clusters_frame, text="No clusters yet.",
                     font=FONTS["tiny"],
                     text_color=COLORS["text_muted"]).pack(padx=12, pady=12)

    def refresh(self):
        """Refresh the graph from the database and redraw."""
        graph_manager = get_graph_manager()
        graph = graph_manager.get_nx_graph()
        graph_stats = graph_manager.get_graph_stats()

        # Update quick stats
        self._stat_labels["articles"].configure(text=str(graph_stats.get("nodes", 0)))
        self._stat_labels["connections"].configure(text=str(graph_stats.get("edges", 0)))
        self._stat_labels["clusters"].configure(text=str(graph_stats.get("components", 0)))

        # Draw graph
        self._draw_graph(graph)

        # Update article list
        self._update_article_list()

        # Update clusters
        self._update_clusters(graph)

    def _draw_graph(self, graph):
        """Draw the NetworkX graph with a beginner-friendly visual style."""
        for widget in self._canvas_frame.winfo_children():
            widget.destroy()

        if graph.number_of_nodes() == 0:
            ctk.CTkLabel(self._canvas_frame,
                         text="🕸️\n\nNo articles analyzed yet.\n\nGo to 'Analyze News', analyze a few articles,\nthen click 🔄 Refresh.",
                         font=FONTS["body"],
                         text_color=COLORS["text_muted"],
                         justify="center").pack(expand=True)
            return

        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import matplotlib.patches as mpatches
            import matplotlib.patheffects as pe
            import networkx as nx
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

            fig, ax = plt.subplots(figsize=(9, 6.5))
            fig.patch.set_facecolor("#0d1117")
            ax.set_facecolor("#0d1117")

            n = graph.number_of_nodes()

            # Layout — spring layout with good spacing
            if n <= 3:
                pos = nx.circular_layout(graph)
            elif n <= 15:
                pos = nx.spring_layout(graph, k=3.0, iterations=80, seed=42)
            else:
                pos = nx.spring_layout(graph, k=2.0, iterations=40, seed=42)

            # Node colors and sizes
            node_colors = []
            node_sizes = []
            for node in graph.nodes():
                pred = graph.nodes[node].get("prediction", "UNKNOWN")
                color_map = {
                    "REAL": "#22c55e",
                    "FAKE": "#ef4444",
                    "SUSPICIOUS": "#f59e0b",
                }
                node_colors.append(color_map.get(pred, "#6b7280"))
                degree = graph.degree(node)
                node_sizes.append(max(400, 200 + degree * 120))

            # Edge colors by relationship type
            edge_color_map = {
                "DUPLICATE":        "#ef4444",
                "SIMILAR_CONTENT":  "#f59e0b",
                "SAME_TOPIC":       "#06b6d4",
                "SAME_SOURCE":      "#8b5cf6",
                "RELATED_KEYWORDS": "#22c55e",
            }
            edge_colors = []
            edge_widths = []
            for u, v in graph.edges():
                rel = graph[u][v].get("relationship_type", "")
                edge_colors.append(edge_color_map.get(rel, "#4b5563"))
                edge_widths.append(2.5 if rel == "DUPLICATE" else 1.5)

            # Draw edges first (behind nodes)
            nx.draw_networkx_edges(
                graph, pos, ax=ax,
                edge_color=edge_colors,
                width=edge_widths,
                alpha=0.7,
                arrows=True,
                arrowsize=14,
                connectionstyle="arc3,rad=0.1",
                min_source_margin=20,
                min_target_margin=20,
            )

            # Draw nodes
            nx.draw_networkx_nodes(
                graph, pos, ax=ax,
                node_color=node_colors,
                node_size=node_sizes,
                alpha=0.95,
                linewidths=2,
                edgecolors="#1e293b",
            )

            # Smart labels: show short article ID parts
            labels = {}
            for node in graph.nodes():
                parts = node.split("-")
                labels[node] = parts[1][:6] if len(parts) > 1 else node[:6]

            nx.draw_networkx_labels(
                graph, pos, labels, ax=ax,
                font_size=7,
                font_color="white",
                font_weight="bold",
            )

            # ── Clean title ────────────────────────────────────────
            ax.set_title(
                f"News Article Graph  ·  {graph.number_of_nodes()} Articles  ·  "
                f"{graph.number_of_edges()} Connections",
                color="#e2e8f0", fontsize=11, pad=10, fontweight="bold"
            )
            ax.axis("off")

            # ── Legend inside chart ────────────────────────────────
            legend_patches = [
                mpatches.Patch(color="#22c55e", label="● REAL article"),
                mpatches.Patch(color="#ef4444", label="● FAKE article"),
                mpatches.Patch(color="#f59e0b", label="● SUSPICIOUS"),
                mpatches.Patch(color="#ef4444", label="— Duplicate"),
                mpatches.Patch(color="#f59e0b", label="— Similar content"),
                mpatches.Patch(color="#06b6d4", label="— Same topic"),
                mpatches.Patch(color="#8b5cf6", label="— Same source"),
            ]
            leg = ax.legend(
                handles=legend_patches,
                loc="lower left",
                facecolor="#1a1f2e",
                edgecolor="#334155",
                labelcolor="#cbd5e1",
                fontsize=8,
                framealpha=0.9,
                title="Legend",
                title_fontsize=8,
            )
            leg.get_title().set_color("#94a3b8")

            plt.tight_layout(pad=0.5)
            canvas = FigureCanvasTkAgg(fig, master=self._canvas_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            plt.close(fig)

        except ImportError:
            ctk.CTkLabel(self._canvas_frame,
                         text="Install matplotlib to see graph visualization.\n\npip install matplotlib",
                         font=FONTS["body"],
                         text_color=COLORS["text_muted"],
                         justify="center").pack(expand=True)
        except Exception as e:
            ctk.CTkLabel(self._canvas_frame,
                         text=f"Graph display error:\n{str(e)[:120]}",
                         font=FONTS["tiny"],
                         text_color=COLORS["text_muted"],
                         justify="center").pack(expand=True)

    def _update_article_list(self):
        """Show a simple, readable list of all articles in the graph."""
        for widget in self._articles_frame.winfo_children():
            widget.destroy()

        articles = database.get_all_articles()
        if not articles:
            ctk.CTkLabel(self._articles_frame, text="No articles yet.",
                         font=FONTS["tiny"],
                         text_color=COLORS["text_muted"]).pack(padx=12, pady=12)
            return

        graph_manager = get_graph_manager()

        for article in articles[:20]:  # Show up to 20
            pred = article.get("prediction", "UNKNOWN")
            color = prediction_color(pred)
            connections = len(graph_manager.get_neighbors(article.get("article_id", "")))

            row = ctk.CTkFrame(self._articles_frame,
                               fg_color=COLORS["bg_secondary"], corner_radius=6)
            row.pack(fill="x", padx=8, pady=3)

            # Color stripe
            stripe = ctk.CTkFrame(row, fg_color=color, width=4, corner_radius=2)
            stripe.pack(side="left", fill="y")

            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, padx=8, pady=6)

            ctk.CTkLabel(info,
                         text=truncate_text(article.get("headline", "No headline"), 38),
                         font=FONTS["tiny"],
                         text_color=COLORS["text_primary"],
                         anchor="w").pack(anchor="w")
            ctk.CTkLabel(info,
                         text=f"{connections} connection{'s' if connections != 1 else ''}  ·  {article.get('source', 'Unknown')}",
                         font=FONTS["tiny"],
                         text_color=COLORS["text_muted"],
                         anchor="w").pack(anchor="w")

            # Prediction badge
            icons = {"REAL": "✅", "FAKE": "❌", "SUSPICIOUS": "⚠️"}
            ctk.CTkLabel(row,
                         text=icons.get(pred, "❓"),
                         font=("Segoe UI Emoji", 13)).pack(side="right", padx=8)

        if len(articles) > 20:
            ctk.CTkLabel(self._articles_frame,
                         text=f"... and {len(articles) - 20} more",
                         font=FONTS["tiny"],
                         text_color=COLORS["text_muted"]).pack(padx=12, pady=4)

    def _update_clusters(self, graph):
        """Update the news clusters panel with plain-English descriptions."""
        for widget in self._clusters_frame.winfo_children():
            widget.destroy()

        result = find_connected_components(graph)
        components = result.get("components", [])

        if not components:
            ctk.CTkLabel(self._clusters_frame, text="No clusters yet.",
                         font=FONTS["tiny"],
                         text_color=COLORS["text_muted"]).pack(padx=12, pady=12)
            return

        for comp in components[:6]:
            size = comp["size"]
            real = comp["real_count"]
            fake = comp["fake_count"]
            susp = comp["suspicious_count"]

            # Determine cluster character
            if fake > real and fake > susp:
                char_icon = "🚨"
                char_text = "Mostly fake"
                char_color = COLORS["fake"]
            elif real > fake and real > susp:
                char_icon = "✅"
                char_text = "Mostly real"
                char_color = COLORS["real"]
            else:
                char_icon = "⚠️"
                char_text = "Mixed"
                char_color = COLORS["suspicious"]

            card = ctk.CTkFrame(self._clusters_frame,
                                fg_color=COLORS["bg_secondary"], corner_radius=8)
            card.pack(fill="x", padx=8, pady=4)

            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=10, pady=(8, 2))

            ctk.CTkLabel(top_row,
                         text=f"{char_icon} Cluster {comp['id']}  ·  {size} article{'s' if size != 1 else ''}",
                         font=FONTS["small"],
                         text_color=COLORS["text_primary"]).pack(side="left")
            ctk.CTkLabel(top_row,
                         text=char_text,
                         font=FONTS["tiny"],
                         text_color=char_color).pack(side="right")

            ctk.CTkLabel(card,
                         text=f"  ✅ {real} Real   ❌ {fake} Fake   ⚠️ {susp} Suspicious",
                         font=FONTS["tiny"],
                         text_color=COLORS["text_muted"]).pack(anchor="w", padx=10, pady=(0, 8))
