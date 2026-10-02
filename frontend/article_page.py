"""
frontend/article_page.py
Detailed Article View page.
Shows comprehensive analysis for a selected article.
"""

import tkinter as tk
import customtkinter as ctk
from frontend.components import (
    COLORS, FONTS, PredictionBadge, ConfidenceBar, InfoRow,
    KeywordTag, RelationshipTag
)
from utils.helpers import format_timestamp, truncate_text, prediction_color, relationship_color
from backend.graph_manager import get_graph_manager
from backend.graph_algorithms import bfs, dfs


class ArticlePage(ctk.CTkFrame):
    """
    Detailed view for a single analyzed article.
    Includes:
    - Full article information
    - Prediction & confidence
    - Text analysis (keywords, statistics)
    - Relationship analysis
    - DSA information (hash, graph, BFS/DFS)
    """

    def __init__(self, parent, on_back=None, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_primary"], **kwargs)
        self._on_back = on_back
        self._article = None
        self._build_ui()

    def _build_ui(self):
        # Back button header
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], height=56)
        header.pack(fill="x")
        header.pack_propagate(False)

        header_inner = ctk.CTkFrame(header, fg_color="transparent")
        header_inner.pack(fill="both", expand=True, padx=16)

        ctk.CTkButton(header_inner, text="← Back",
                      font=FONTS["body"],
                      fg_color="transparent",
                      hover_color=COLORS["bg_card"],
                      text_color=COLORS["accent_cyan"],
                      height=36,
                      width=80,
                      command=self._go_back).pack(side="left", pady=10)

        self._title_label = ctk.CTkLabel(header_inner, text="Article Details",
                                          font=FONTS["heading"],
                                          text_color=COLORS["text_primary"])
        self._title_label.pack(side="left", padx=(16, 0), pady=10)

        # Scrollable content
        self._scroll = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg_primary"])
        self._scroll.pack(fill="both", expand=True, padx=20, pady=16)

        # Placeholder
        self._placeholder = ctk.CTkLabel(self._scroll,
                                          text="Select an article from History to view details.",
                                          font=FONTS["body"],
                                          text_color=COLORS["text_muted"])
        self._placeholder.pack(pady=80)

    def load_article(self, article: dict):
        """Load and display an article's full analysis."""
        self._article = article

        # Clear previous content
        for widget in self._scroll.winfo_children():
            widget.destroy()

        pred = article.get("prediction", "UNKNOWN")
        pred_color = prediction_color(pred)
        conf = article.get("confidence", 0)
        if conf <= 1.0:
            conf *= 100

        # ── Banner ────────────────────────────────────────────────
        banner = ctk.CTkFrame(self._scroll, fg_color=pred_color, corner_radius=12)
        banner.pack(fill="x", pady=(0, 16))

        banner_inner = ctk.CTkFrame(banner, fg_color="transparent")
        banner_inner.pack(padx=20, pady=16)

        icons = {"REAL": "✅", "FAKE": "❌", "SUSPICIOUS": "⚠️"}
        ctk.CTkLabel(banner_inner,
                     text=f"{icons.get(pred, '❓')}  {pred}  —  System Assessment",
                     font=("Segoe UI", 18, "bold"),
                     text_color="white").pack(anchor="w")

        ctk.CTkLabel(banner_inner,
                     text=truncate_text(article.get("headline", ""), 120),
                     font=FONTS["body"],
                     text_color="white",
                     wraplength=800).pack(anchor="w", pady=(6, 0))

        ctk.CTkLabel(banner_inner,
                     text="⚠️  System assessment only — based on DEMO model and SAMPLE data.",
                     font=FONTS["tiny"],
                     text_color="white").pack(anchor="w", pady=(6, 0))

        # ── Two column layout ─────────────────────────────────────
        two_col = ctk.CTkFrame(self._scroll, fg_color="transparent")
        two_col.pack(fill="x", pady=(0, 16))
        two_col.columnconfigure([0, 1], weight=1)

        # LEFT: Article Info
        left_card = ctk.CTkFrame(two_col, fg_color=COLORS["bg_card"], corner_radius=10)
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left_inner = ctk.CTkFrame(left_card, fg_color="transparent")
        left_inner.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(left_inner, text="📋 Article Information",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(0, 8))

        InfoRow(left_inner, "Article ID", article.get("article_id", "N/A")).pack(fill="x", pady=2)
        InfoRow(left_inner, "Source", article.get("source", "Unknown")).pack(fill="x", pady=2)
        InfoRow(left_inner, "Topic", article.get("topic", "General")).pack(fill="x", pady=2)
        InfoRow(left_inner, "Publication Date", article.get("pub_date") or "Not specified").pack(fill="x", pady=2)
        InfoRow(left_inner, "Analyzed At", format_timestamp(article.get("timestamp"))).pack(fill="x", pady=2)
        InfoRow(left_inner, "Word Count", str(article.get("word_count", 0))).pack(fill="x", pady=2)

        dup_color = COLORS["fake"] if article.get("is_duplicate") else COLORS["real"]
        dup_text = "YES" if article.get("is_duplicate") else "NO"
        InfoRow(left_inner, "Duplicate", dup_text, value_color=dup_color).pack(fill="x", pady=2)
        if article.get("duplicate_of"):
            InfoRow(left_inner, "Duplicate Of", str(article.get("duplicate_of", ""))[:40]).pack(fill="x", pady=2)
            InfoRow(left_inner, "Similarity",
                    f"{article.get('similarity_score', 0) * 100:.1f}%").pack(fill="x", pady=2)

        # RIGHT: Confidence
        right_card = ctk.CTkFrame(two_col, fg_color=COLORS["bg_card"], corner_radius=10)
        right_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        right_inner = ctk.CTkFrame(right_card, fg_color="transparent")
        right_inner.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(right_inner, text="📊 Confidence Scores",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(0, 8))

        ConfidenceBar(right_inner, value=conf,
                      label="Overall Confidence",
                      color=pred_color).pack(fill="x", pady=4)
        ConfidenceBar(right_inner,
                      value=article.get("credibility_score", 0),
                      label="Credibility Score",
                      color=COLORS["accent_cyan"]).pack(fill="x", pady=4)

        # ── Keywords ──────────────────────────────────────────────
        kw_card = ctk.CTkFrame(self._scroll, fg_color=COLORS["bg_card"], corner_radius=10)
        kw_card.pack(fill="x", pady=(0, 12))
        kw_inner = ctk.CTkFrame(kw_card, fg_color="transparent")
        kw_inner.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(kw_inner, text="🏷️ Keyword Analysis",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(0, 8))

        keywords = article.get("keywords", [])
        if keywords:
            kw_tags = ctk.CTkFrame(kw_inner, fg_color="transparent")
            kw_tags.pack(anchor="w", fill="x")
            for kw in keywords:
                KeywordTag(kw_tags, kw).pack(side="left", padx=3, pady=3)
        else:
            ctk.CTkLabel(kw_inner, text="No keywords extracted.",
                         font=FONTS["small"],
                         text_color=COLORS["text_muted"]).pack(anchor="w")

        # ── Full Article Content ───────────────────────────────────
        content_card = ctk.CTkFrame(self._scroll, fg_color=COLORS["bg_card"], corner_radius=10)
        content_card.pack(fill="x", pady=(0, 12))
        content_inner = ctk.CTkFrame(content_card, fg_color="transparent")
        content_inner.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(content_inner, text="📄 Article Content",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(0, 8))

        content_box = ctk.CTkTextbox(content_inner,
                                      font=FONTS["body"],
                                      fg_color=COLORS["bg_input"],
                                      text_color=COLORS["text_primary"],
                                      height=150,
                                      wrap="word",
                                      state="normal")
        content_box.pack(fill="x")
        content_box.insert("1.0", article.get("content", "Content not available."))
        content_box.configure(state="disabled")

        # ── Related Articles ──────────────────────────────────────
        related = article.get("related_articles", [])
        rel_card = ctk.CTkFrame(self._scroll, fg_color=COLORS["bg_card"], corner_radius=10)
        rel_card.pack(fill="x", pady=(0, 12))
        rel_inner = ctk.CTkFrame(rel_card, fg_color="transparent")
        rel_inner.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(rel_inner, text=f"🔗 Relationship Analysis ({len(related)} relationships)",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(0, 8))

        if not related:
            ctk.CTkLabel(rel_inner,
                         text="No relationships found yet. As you analyze more articles, relationships will appear here.",
                         font=FONTS["small"],
                         text_color=COLORS["text_muted"]).pack(anchor="w")
        else:
            for rel in related:
                rrow = ctk.CTkFrame(rel_inner, fg_color=COLORS["bg_secondary"], corner_radius=6)
                rrow.pack(fill="x", pady=3)
                rc = relationship_color(rel.get("relationship", ""))
                ind = ctk.CTkFrame(rrow, fg_color=rc, width=4, corner_radius=2)
                ind.pack(side="left", fill="y")

                rinfo = ctk.CTkFrame(rrow, fg_color="transparent")
                rinfo.pack(side="left", fill="x", expand=True, padx=10, pady=8)
                ctk.CTkLabel(rinfo,
                             text=truncate_text(rel.get("headline", ""), 70),
                             font=FONTS["small"],
                             text_color=COLORS["text_primary"],
                             anchor="w").pack(anchor="w")
                ctk.CTkLabel(rinfo,
                             text=f"{rel.get('source', 'Unknown')} · {rel.get('relationship', '').replace('_', ' ')} · {rel.get('similarity', 0):.1f}% similar",
                             font=FONTS["tiny"],
                             text_color=COLORS["text_muted"],
                             anchor="w").pack(anchor="w")

                ctk.CTkLabel(rrow, text=f"  {rel.get('prediction', 'UNKNOWN')}  ",
                             font=FONTS["tiny"],
                             text_color="white",
                             fg_color=prediction_color(rel.get("prediction", "UNKNOWN")),
                             corner_radius=4).pack(side="right", padx=10)

        # ── DSA Information ───────────────────────────────────────
        dsa_card = ctk.CTkFrame(self._scroll, fg_color=COLORS["bg_card"], corner_radius=10)
        dsa_card.pack(fill="x", pady=(0, 12))
        dsa_inner = ctk.CTkFrame(dsa_card, fg_color="transparent")
        dsa_inner.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(dsa_inner, text="🏗️ DSA Information",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(0, 8))

        hash_info = article.get("hash_info", {})
        article_id = article.get("article_id", "")

        graph_manager = get_graph_manager()
        connections = len(graph_manager.get_neighbors(article_id)) if article_id else 0

        dsa_grid = ctk.CTkFrame(dsa_inner, fg_color="transparent")
        dsa_grid.pack(fill="x")
        dsa_grid.columnconfigure([0, 1], weight=1)

        # Left DSA info
        left_dsa = ctk.CTkFrame(dsa_grid, fg_color=COLORS["bg_secondary"], corner_radius=8)
        left_dsa.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=4)
        left_dsa_inner = ctk.CTkFrame(left_dsa, fg_color="transparent")
        left_dsa_inner.pack(fill="x", padx=12, pady=12)

        ctk.CTkLabel(left_dsa_inner, text="Hashing",
                     font=FONTS["subheading"],
                     text_color=COLORS["accent_cyan"]).pack(anchor="w", pady=(0, 6))
        InfoRow(left_dsa_inner, "Short Hash", hash_info.get("short_hash", "N/A")).pack(fill="x", pady=2)
        InfoRow(left_dsa_inner, "SimHash", str(hash_info.get("simhash", "N/A"))[:20]).pack(fill="x", pady=2)
        InfoRow(left_dsa_inner, "Algorithm", "SHA-256").pack(fill="x", pady=2)
        InfoRow(left_dsa_inner, "Hash Length", "256 bits / 64 chars").pack(fill="x", pady=2)

        # Right DSA info
        right_dsa = ctk.CTkFrame(dsa_grid, fg_color=COLORS["bg_secondary"], corner_radius=8)
        right_dsa.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=4)
        right_dsa_inner = ctk.CTkFrame(right_dsa, fg_color="transparent")
        right_dsa_inner.pack(fill="x", padx=12, pady=12)

        ctk.CTkLabel(right_dsa_inner, text="Graph",
                     font=FONTS["subheading"],
                     text_color=COLORS["accent_purple"]).pack(anchor="w", pady=(0, 6))
        InfoRow(right_dsa_inner, "Node ID", article_id[:30]).pack(fill="x", pady=2)
        InfoRow(right_dsa_inner, "Connections", str(connections)).pack(fill="x", pady=2)
        InfoRow(right_dsa_inner, "Graph Type", "Directed Graph").pack(fill="x", pady=2)
        InfoRow(right_dsa_inner, "Representation", "Adjacency List").pack(fill="x", pady=2)

        # BFS/DFS from this node
        ctk.CTkLabel(dsa_inner, text="Run Traversal from this Article:",
                     font=FONTS["small"],
                     text_color=COLORS["text_muted"]).pack(anchor="w", pady=(12, 4))

        trav_btns = ctk.CTkFrame(dsa_inner, fg_color="transparent")
        trav_btns.pack(anchor="w")

        ctk.CTkButton(trav_btns, text="▶ Run BFS",
                      font=FONTS["small"],
                      fg_color=COLORS["accent_cyan"],
                      hover_color="#0891b2",
                      height=32,
                      command=lambda: self._run_traversal("bfs", article_id)).pack(side="left", padx=(0, 8))

        ctk.CTkButton(trav_btns, text="▶ Run DFS",
                      font=FONTS["small"],
                      fg_color="#8b5cf6",
                      hover_color="#7c3aed",
                      height=32,
                      command=lambda: self._run_traversal("dfs", article_id)).pack(side="left")

        self._traversal_output = ctk.CTkTextbox(
            dsa_inner,
            font=FONTS["mono"],
            fg_color=COLORS["bg_input"],
            text_color=COLORS["accent_cyan"],
            height=100,
            state="disabled"
        )
        self._traversal_output.pack(fill="x", pady=(8, 0))

        # Full hash display
        ctk.CTkLabel(dsa_inner, text="Full SHA-256 Normalized Hash:",
                     font=FONTS["small"],
                     text_color=COLORS["text_muted"]).pack(anchor="w", pady=(12, 4))
        hash_box = ctk.CTkTextbox(dsa_inner,
                                   font=FONTS["mono_small"],
                                   fg_color=COLORS["bg_input"],
                                   text_color=COLORS["accent_cyan"],
                                   height=50)
        hash_box.pack(fill="x")
        hash_box.insert("1.0", hash_info.get("normalized_hash", "Not available"))
        hash_box.configure(state="disabled")

    def _run_traversal(self, algo: str, article_id: str):
        """Run BFS or DFS from this article and display result."""
        if not article_id:
            return

        graph = get_graph_manager().get_nx_graph()

        if algo == "bfs":
            result = bfs(graph, article_id, max_depth=3)
        else:
            result = dfs(graph, article_id, max_nodes=20)

        self._traversal_output.configure(state="normal")
        self._traversal_output.delete("1.0", "end")

        if result.get("error"):
            self._traversal_output.insert("end", f"Error: {result['error']}")
        else:
            order = result.get("traversal_order", [])
            algo_name = "BFS (Breadth-First Search)" if algo == "bfs" else "DFS (Depth-First Search)"
            ds_name = "Queue (FIFO)" if algo == "bfs" else "Stack (LIFO)"

            self._traversal_output.insert("end", f"Algorithm: {algo_name}\n")
            self._traversal_output.insert("end", f"Data Structure: {ds_name}\n")
            self._traversal_output.insert("end", f"Nodes Visited: {result.get('visited_count', 0)}\n\n")
            self._traversal_output.insert("end", "Traversal Order:\n")

            traversal_str = " → ".join(
                (n.split("-")[1][:8] if "-" in n else n[:8]) for n in order
            )
            self._traversal_output.insert("end", traversal_str if traversal_str else "(No connections)")

        self._traversal_output.configure(state="disabled")

    def _go_back(self):
        if self._on_back:
            self._on_back()
