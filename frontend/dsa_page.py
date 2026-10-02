"""
frontend/dsa_page.py
DSA Analysis Page — explicitly demonstrates the Data Structures used.

This page is specifically designed for college viva demonstrations.
It shows hashing, graph algorithms, and hash table operations interactively.
"""

import tkinter as tk
import customtkinter as ctk
from frontend.components import COLORS, FONTS, InfoRow
from backend.hashing import get_all_hash_info, compute_simhash, hamming_distance
from backend.hash_table import HashTable
from backend.keyword_manager import get_keyword_table, get_keyword_article_mapping, lookup_keyword
from backend.graph_manager import get_graph_manager
from backend.graph_algorithms import bfs, dfs, find_connected_components, get_most_connected_articles
from backend import database
from utils.helpers import truncate_text


class DSAPage(ctk.CTkFrame):
    """
    Interactive DSA demonstration page for college viva.
    
    Sections:
    1. Hashing Demo — real-time hash computation and normalization
    2. Hash Table Demo — keyword lookup and statistics
    3. Graph Demo — BFS/DFS traversal with step-by-step output
    4. Connected Components — cluster analysis
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_primary"], **kwargs)
        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        header_inner = ctk.CTkFrame(header, fg_color="transparent")
        header_inner.pack(side="left", fill="y", padx=20)
        ctk.CTkLabel(header_inner, text="🏗️  DSA Analysis — Data Structures Demonstration",
                     font=FONTS["heading"],
                     text_color=COLORS["text_primary"]).pack(side="left", pady=15)

        # Scrollable main content
        scroll = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg_primary"])
        scroll.pack(fill="both", expand=True, padx=20, pady=16)

        # ════════════════════════════════════════════════════════
        # SECTION 1: HASHING DEMO
        # ════════════════════════════════════════════════════════
        self._build_hashing_section(scroll)

        # ════════════════════════════════════════════════════════
        # SECTION 2: HASH TABLE DEMO
        # ════════════════════════════════════════════════════════
        self._build_hash_table_section(scroll)

        # ════════════════════════════════════════════════════════
        # SECTION 3: GRAPH ALGORITHMS DEMO
        # ════════════════════════════════════════════════════════
        self._build_graph_section(scroll)

        # ════════════════════════════════════════════════════════
        # SECTION 4: CONNECTED COMPONENTS
        # ════════════════════════════════════════════════════════
        self._build_components_section(scroll)

    def _section_header(self, parent, number: str, title: str, subtitle: str, color: str):
        """Create a styled section header."""
        frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=12)
        frame.pack(fill="x", pady=(0, 12))
        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=16)

        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(anchor="w")

        ctk.CTkLabel(row, text=number,
                     font=("Segoe UI", 24, "bold"),
                     text_color=color,
                     fg_color=COLORS["bg_secondary"],
                     corner_radius=8,
                     width=40).pack(side="left", padx=(0, 12))
        ctk.CTkLabel(row, text=title,
                     font=FONTS["heading"],
                     text_color=COLORS["text_primary"]).pack(side="left")
        ctk.CTkLabel(inner, text=subtitle,
                     font=FONTS["small"],
                     text_color=COLORS["text_muted"]).pack(anchor="w", pady=(4, 0))

        line = ctk.CTkFrame(inner, fg_color=color, height=2, corner_radius=1)
        line.pack(fill="x", pady=(8, 0))
        return frame

    # ────────────────────────────────────────────────────────────
    # SECTION 1: HASHING
    # ────────────────────────────────────────────────────────────
    def _build_hashing_section(self, parent):
        self._section_header(parent, "01", "Hashing",
                             "Compute SHA-256 hashes and see normalization in action.",
                             COLORS["accent_cyan"])

        hash_demo = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=12)
        hash_demo.pack(fill="x", pady=(0, 20))
        hash_inner = ctk.CTkFrame(hash_demo, fg_color="transparent")
        hash_inner.pack(fill="x", padx=20, pady=16)

        # Explanation
        explanation = (
            "A hash function maps input text to a fixed-size output (the 'hash' or 'digest').\n"
            "Properties: Deterministic | Fast | Collision-resistant | One-way\n"
            "SHA-256 produces a 256-bit (64 hex character) output for ANY input length."
        )
        exp_box = ctk.CTkTextbox(hash_inner, font=FONTS["small"],
                                  fg_color=COLORS["bg_secondary"],
                                  text_color=COLORS["text_muted"],
                                  height=60, state="normal")
        exp_box.pack(fill="x", pady=(0, 12))
        exp_box.insert("1.0", explanation)
        exp_box.configure(state="disabled")

        # Input
        ctk.CTkLabel(hash_inner, text="Enter text to hash:",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(0, 4))

        input_row = ctk.CTkFrame(hash_inner, fg_color="transparent")
        input_row.pack(fill="x", pady=(0, 12))

        self._hash_input = ctk.CTkEntry(input_row,
                                         placeholder_text="Type any text here...",
                                         font=FONTS["body"],
                                         fg_color=COLORS["bg_input"],
                                         border_color=COLORS["border"],
                                         text_color=COLORS["text_primary"],
                                         height=40)
        self._hash_input.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._hash_input.insert(0, "Government announces new education policy!")

        ctk.CTkButton(input_row, text="Compute Hash",
                      font=FONTS["small"],
                      fg_color=COLORS["accent_cyan"],
                      hover_color="#0891b2",
                      height=40,
                      width=130,
                      command=self._compute_hash).pack(side="left")

        # Output area
        output_frame = ctk.CTkFrame(hash_inner, fg_color=COLORS["bg_secondary"],
                                     corner_radius=8)
        output_frame.pack(fill="x", pady=(0, 12))
        output_inner = ctk.CTkFrame(output_frame, fg_color="transparent")
        output_inner.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(output_inner, text="Hashing Pipeline Output:",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(0, 8))

        self._hash_output = ctk.CTkTextbox(output_inner,
                                            font=FONTS["mono"],
                                            fg_color=COLORS["bg_input"],
                                            text_color=COLORS["accent_cyan"],
                                            height=200,
                                            state="disabled")
        self._hash_output.pack(fill="x")

        # SimHash demo
        ctk.CTkLabel(hash_inner, text="Near-Duplicate Detection (SimHash Comparison):",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(12, 4))

        simhash_frame = ctk.CTkFrame(hash_inner, fg_color="transparent")
        simhash_frame.pack(fill="x")
        simhash_frame.columnconfigure([0, 1], weight=1)

        self._sim_text1 = ctk.CTkEntry(simhash_frame,
                                        placeholder_text="Text A...",
                                        font=FONTS["body"],
                                        fg_color=COLORS["bg_input"],
                                        border_color=COLORS["border"],
                                        text_color=COLORS["text_primary"])
        self._sim_text1.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self._sim_text1.insert(0, "Government announces education policy")

        self._sim_text2 = ctk.CTkEntry(simhash_frame,
                                        placeholder_text="Text B...",
                                        font=FONTS["body"],
                                        fg_color=COLORS["bg_input"],
                                        border_color=COLORS["border"],
                                        text_color=COLORS["text_primary"])
        self._sim_text2.grid(row=0, column=1, sticky="ew", padx=(4, 0))
        self._sim_text2.insert(0, "Government announces new education policy")

        ctk.CTkButton(hash_inner, text="Compare SimHash",
                      font=FONTS["small"],
                      fg_color="#8b5cf6",
                      hover_color="#7c3aed",
                      height=36,
                      command=self._compare_simhash).pack(anchor="w", pady=(8, 0))

        self._simhash_result = ctk.CTkLabel(hash_inner, text="",
                                             font=FONTS["body"],
                                             text_color=COLORS["accent_cyan"])
        self._simhash_result.pack(anchor="w", pady=(4, 0))

    def _compute_hash(self):
        """Compute and display SHA-256 hash pipeline."""
        text = self._hash_input.get().strip()
        if not text:
            return

        from backend.hashing import (normalize_text, compute_sha256,
                                      compute_md5, get_short_hash)
        from backend.text_processor import normalize_text as norm

        normalized = norm(text, remove_stopwords=False)
        normalized_no_stop = norm(text, remove_stopwords=True)
        sha256 = compute_sha256(normalized)
        sha256_no_stop = compute_sha256(normalized_no_stop)
        md5 = compute_md5(text)
        short = get_short_hash(text)

        output = (
            f"INPUT TEXT:\n{text}\n\n"
            f"STEP 1 — Normalize (lowercase + clean):\n{normalized}\n\n"
            f"STEP 2 — Normalize (remove stop words):\n{normalized_no_stop}\n\n"
            f"STEP 3 — SHA-256 Hash (with stop words):\n{sha256}\n\n"
            f"STEP 4 — SHA-256 Hash (without stop words):\n{sha256_no_stop}\n\n"
            f"MD5 Hash (32 chars):\n{md5}\n\n"
            f"Short Hash (8 chars, for display):\n{short}\n\n"
            f"Hash Length: {len(sha256)} characters = 256 bits\n"
            f"Same input always produces the same hash (DETERMINISTIC)."
        )

        self._hash_output.configure(state="normal")
        self._hash_output.delete("1.0", "end")
        self._hash_output.insert("1.0", output)
        self._hash_output.configure(state="disabled")

    def _compare_simhash(self):
        """Compare two texts using SimHash."""
        t1 = self._sim_text1.get().strip()
        t2 = self._sim_text2.get().strip()

        if not t1 or not t2:
            self._simhash_result.configure(text="Please enter both texts.")
            return

        from backend.hashing import simhash_similarity, compute_simhash, hamming_distance

        h1 = compute_simhash(t1)
        h2 = compute_simhash(t2)
        dist = hamming_distance(h1, h2)
        sim = simhash_similarity(t1, t2)

        result = (
            f"SimHash A: {h1}\n"
            f"SimHash B: {h2}\n"
            f"Hamming Distance: {dist} bits differ out of 64\n"
            f"Similarity Score: {sim*100:.1f}%  →  "
            f"{'NEAR DUPLICATE (≥85%)' if sim >= 0.85 else ('SIMILAR (≥60%)' if sim >= 0.60 else 'DIFFERENT')}"
        )
        self._simhash_result.configure(text=result)

    # ────────────────────────────────────────────────────────────
    # SECTION 2: HASH TABLE
    # ────────────────────────────────────────────────────────────
    def _build_hash_table_section(self, parent):
        self._section_header(parent, "02", "Hash Table",
                             "Keyword → Article index using Custom Hash Table with Separate Chaining.",
                             COLORS["accent_purple"])

        ht_frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=12)
        ht_frame.pack(fill="x", pady=(0, 20))
        ht_inner = ctk.CTkFrame(ht_frame, fg_color="transparent")
        ht_inner.pack(fill="x", padx=20, pady=16)

        # Explanation
        exp = (
            "Our custom HashTable uses SEPARATE CHAINING for collision resolution.\n"
            "Each bucket is a linked list of (key, value) pairs.\n"
            "Hash Function: Polynomial Rolling Hash  |  Time: O(1) average  |  Space: O(n)"
        )
        exp_box = ctk.CTkTextbox(ht_inner, font=FONTS["small"],
                                  fg_color=COLORS["bg_secondary"],
                                  text_color=COLORS["text_muted"],
                                  height=55, state="normal")
        exp_box.pack(fill="x", pady=(0, 12))
        exp_box.insert("1.0", exp)
        exp_box.configure(state="disabled")

        # Table stats
        ctk.CTkLabel(ht_inner, text="Current Hash Table Statistics:",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(0, 8))

        self._ht_stats_frame = ctk.CTkFrame(ht_inner, fg_color=COLORS["bg_secondary"],
                                             corner_radius=8)
        self._ht_stats_frame.pack(fill="x", pady=(0, 12))

        ctk.CTkButton(ht_inner, text="📊 Load Table Stats",
                      font=FONTS["small"],
                      fg_color=COLORS["accent_purple"],
                      hover_color="#6d28d9",
                      height=36,
                      command=self._load_ht_stats).pack(anchor="w", pady=(0, 12))

        # Keyword lookup
        ctk.CTkLabel(ht_inner, text="Keyword Lookup (O(1) average time):",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(0, 8))

        lookup_row = ctk.CTkFrame(ht_inner, fg_color="transparent")
        lookup_row.pack(fill="x", pady=(0, 8))

        self._kw_search = ctk.CTkEntry(lookup_row,
                                        placeholder_text="Enter keyword to search...",
                                        font=FONTS["body"],
                                        fg_color=COLORS["bg_input"],
                                        border_color=COLORS["border"],
                                        text_color=COLORS["text_primary"],
                                        height=36)
        self._kw_search.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(lookup_row, text="🔍 Lookup",
                      font=FONTS["small"],
                      fg_color=COLORS["accent_cyan"],
                      hover_color="#0891b2",
                      height=36,
                      width=90,
                      command=self._do_keyword_lookup).pack(side="left")

        self._kw_result = ctk.CTkTextbox(ht_inner,
                                          font=FONTS["mono"],
                                          fg_color=COLORS["bg_input"],
                                          text_color=COLORS["accent_cyan"],
                                          height=120,
                                          state="disabled")
        self._kw_result.pack(fill="x")

        # Keyword index preview
        ctk.CTkLabel(ht_inner, text="Keyword Index (top 10 keywords):",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(12, 8))

        ctk.CTkButton(ht_inner, text="Load Keyword Index",
                      font=FONTS["small"],
                      fg_color=COLORS["bg_secondary"],
                      hover_color=COLORS["bg_input"],
                      height=32,
                      command=self._load_keyword_index).pack(anchor="w", pady=(0, 8))

        self._kw_index_frame = ctk.CTkFrame(ht_inner, fg_color=COLORS["bg_secondary"],
                                             corner_radius=8)
        self._kw_index_frame.pack(fill="x")

    def _load_ht_stats(self):
        """Load and display hash table statistics."""
        from backend.keyword_manager import get_table_stats
        stats = get_table_stats()

        for widget in self._ht_stats_frame.winfo_children():
            widget.destroy()

        inner = ctk.CTkFrame(self._ht_stats_frame, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)
        inner.columnconfigure([0, 1, 2, 3], weight=1)

        stat_items = [
            ("Total Buckets", stats.get("total_buckets", 0), COLORS["accent_cyan"]),
            ("Used Buckets", stats.get("used_buckets", 0), COLORS["real"]),
            ("Total Keywords", stats.get("total_entries", 0), COLORS["accent_purple"]),
            ("Collisions", stats.get("collisions", 0), COLORS["suspicious"]),
            ("Load Factor", f"{stats.get('load_factor', 0):.3f}", COLORS["info"]),
            ("Max Chain Length", stats.get("max_chain_length", 0), COLORS["warning"]),
        ]

        for i, (label, value, color) in enumerate(stat_items):
            col = i % 4
            row = i // 4
            card = ctk.CTkFrame(inner, fg_color=COLORS["bg_card"], corner_radius=6)
            card.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
            ctk.CTkLabel(card, text=str(value),
                         font=("Segoe UI", 20, "bold"),
                         text_color=color).pack(pady=(8, 2))
            ctk.CTkLabel(card, text=label,
                         font=FONTS["tiny"],
                         text_color=COLORS["text_muted"]).pack(pady=(0, 8))

    def _do_keyword_lookup(self):
        """Perform keyword lookup in the hash table."""
        keyword = self._kw_search.get().strip()
        if not keyword:
            return

        from backend.keyword_manager import lookup_keyword
        from backend.hash_table import HashTable

        table = get_keyword_table()
        idx = table._hash(keyword.lower())
        articles = lookup_keyword(keyword)

        output = f"KEYWORD LOOKUP: '{keyword}'\n"
        output += f"Hash Function Result: bucket index = {idx}\n"
        output += f"Time Complexity: O(1) average case\n\n"

        if articles:
            output += f"Found {len(articles)} article(s):\n"
            for art_id in articles:
                article = database.get_article_by_id(art_id)
                if article:
                    output += f"  → {art_id}: {truncate_text(article.get('headline', ''), 60)}\n"
                else:
                    output += f"  → {art_id}\n"
        else:
            output += "No articles found for this keyword.\n"
            output += "Tip: Analyze more articles to build the keyword index."

        self._kw_result.configure(state="normal")
        self._kw_result.delete("1.0", "end")
        self._kw_result.insert("1.0", output)
        self._kw_result.configure(state="disabled")

    def _load_keyword_index(self):
        """Show top keywords from the hash table."""
        from backend.keyword_manager import get_keyword_article_mapping

        for widget in self._kw_index_frame.winfo_children():
            widget.destroy()

        mapping = get_keyword_article_mapping()[:10]

        if not mapping:
            ctk.CTkLabel(self._kw_index_frame,
                         text="No keywords indexed yet. Analyze articles first.",
                         font=FONTS["small"],
                         text_color=COLORS["text_muted"]).pack(padx=12, pady=12)
            return

        inner = ctk.CTkFrame(self._kw_index_frame, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=12)

        # Header
        hrow = ctk.CTkFrame(inner, fg_color="transparent")
        hrow.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(hrow, text="Keyword", font=FONTS["small"],
                     text_color=COLORS["text_muted"], width=120, anchor="w").pack(side="left")
        ctk.CTkLabel(hrow, text="Articles", font=FONTS["small"],
                     text_color=COLORS["text_muted"], width=60).pack(side="left")
        ctk.CTkLabel(hrow, text="Article IDs", font=FONTS["small"],
                     text_color=COLORS["text_muted"]).pack(side="left")

        for item in mapping:
            row = ctk.CTkFrame(inner, fg_color=COLORS["bg_secondary"], corner_radius=4)
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(row, text=item["keyword"],
                         font=FONTS["mono_small"],
                         text_color=COLORS["accent_cyan"],
                         width=120, anchor="w").pack(side="left", padx=8, pady=6)
            ctk.CTkLabel(row, text=str(item["count"]),
                         font=FONTS["small"],
                         text_color=COLORS["accent_purple"],
                         width=60).pack(side="left")
            ids_str = ", ".join(str(a)[:12] for a in item["articles"][:4])
            if len(item["articles"]) > 4:
                ids_str += "..."
            ctk.CTkLabel(row, text=ids_str,
                         font=FONTS["mono_small"],
                         text_color=COLORS["text_muted"],
                         anchor="w").pack(side="left", padx=4)

    # ────────────────────────────────────────────────────────────
    # SECTION 3: GRAPH ALGORITHMS
    # ────────────────────────────────────────────────────────────
    def _build_graph_section(self, parent):
        self._section_header(parent, "03", "Graph Algorithms",
                             "Run BFS and DFS on the news article graph interactively.",
                             COLORS["real"])

        graph_frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=12)
        graph_frame.pack(fill="x", pady=(0, 20))
        graph_inner = ctk.CTkFrame(graph_frame, fg_color="transparent")
        graph_inner.pack(fill="x", padx=20, pady=16)

        # Graph info
        ctk.CTkLabel(graph_inner, text="Current Graph Statistics:",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(0, 8))

        self._graph_stats_frame = ctk.CTkFrame(graph_inner, fg_color=COLORS["bg_secondary"],
                                                corner_radius=8)
        self._graph_stats_frame.pack(fill="x", pady=(0, 12))

        ctk.CTkButton(graph_inner, text="📊 Load Graph Stats",
                      font=FONTS["small"],
                      fg_color=COLORS["real"],
                      hover_color="#16a34a",
                      height=36,
                      command=self._load_graph_stats).pack(anchor="w", pady=(0, 16))

        # Traversal demo
        ctk.CTkLabel(graph_inner, text="Interactive BFS / DFS Traversal:",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(0, 8))

        algo_row = ctk.CTkFrame(graph_inner, fg_color="transparent")
        algo_row.pack(fill="x", pady=(0, 8))

        # Article selector
        articles = database.get_all_articles()
        options = [f"{a['article_id']} — {truncate_text(a['headline'], 40)}" for a in articles] if articles else ["No articles yet"]

        self._dsa_article_var = tk.StringVar(value=options[0] if options else "")
        self._dsa_dropdown = ctk.CTkOptionMenu(
            algo_row,
            variable=self._dsa_article_var,
            values=options,
            font=FONTS["tiny"],
            fg_color=COLORS["bg_input"],
            button_color=COLORS["accent_purple"],
            button_hover_color="#6d28d9",
            width=350
        )
        self._dsa_dropdown.pack(side="left", padx=(0, 8))

        ctk.CTkButton(algo_row, text="▶ BFS",
                      font=FONTS["small"],
                      fg_color=COLORS["accent_cyan"],
                      hover_color="#0891b2",
                      height=36,
                      command=lambda: self._run_dsa_traversal("bfs")).pack(side="left", padx=(0, 4))
        ctk.CTkButton(algo_row, text="▶ DFS",
                      font=FONTS["small"],
                      fg_color="#8b5cf6",
                      hover_color="#7c3aed",
                      height=36,
                      command=lambda: self._run_dsa_traversal("dfs")).pack(side="left")

        # Refresh dropdown
        ctk.CTkButton(graph_inner, text="↺ Refresh Article List",
                      font=FONTS["tiny"],
                      fg_color=COLORS["bg_secondary"],
                      height=28,
                      command=self._refresh_dsa_dropdown).pack(anchor="w", pady=(4, 12))

        # Output
        ctk.CTkLabel(graph_inner, text="Algorithm Output:",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(0, 8))

        self._dsa_algo_output = ctk.CTkTextbox(
            graph_inner,
            font=FONTS["mono"],
            fg_color=COLORS["bg_input"],
            text_color=COLORS["accent_cyan"],
            height=220,
            state="disabled"
        )
        self._dsa_algo_output.pack(fill="x")

    def _load_graph_stats(self):
        """Load and display graph statistics."""
        graph_manager = get_graph_manager()
        stats = graph_manager.get_graph_stats()

        for widget in self._graph_stats_frame.winfo_children():
            widget.destroy()

        inner = ctk.CTkFrame(self._graph_stats_frame, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)
        inner.columnconfigure([0, 1, 2, 3, 4], weight=1)

        stat_items = [
            ("Nodes (V)", stats.get("nodes", 0), COLORS["accent_cyan"]),
            ("Edges (E)", stats.get("edges", 0), COLORS["accent_purple"]),
            ("Density", stats.get("density", 0.0), COLORS["info"]),
            ("Components", stats.get("components", 0), COLORS["warning"]),
            ("Avg Degree", stats.get("avg_degree", 0.0), COLORS["real"]),
        ]

        for i, (label, value, color) in enumerate(stat_items):
            card = ctk.CTkFrame(inner, fg_color=COLORS["bg_card"], corner_radius=6)
            card.grid(row=0, column=i, padx=4, pady=4, sticky="nsew")
            ctk.CTkLabel(card, text=str(value),
                         font=("Segoe UI", 20, "bold"),
                         text_color=color).pack(pady=(8, 2))
            ctk.CTkLabel(card, text=label,
                         font=FONTS["tiny"],
                         text_color=COLORS["text_muted"]).pack(pady=(0, 8))

        # Relationship types breakdown
        edges = graph_manager.get_all_edges()
        rel_types = {}
        for edge in edges:
            rt = edge.get("relationship_type", "UNKNOWN")
            rel_types[rt] = rel_types.get(rt, 0) + 1

        if rel_types:
            ctk.CTkLabel(self._graph_stats_frame, text="Edge Types:",
                         font=FONTS["small"],
                         text_color=COLORS["text_muted"]).pack(anchor="w", padx=16, pady=(4, 4))
            rt_row = ctk.CTkFrame(self._graph_stats_frame, fg_color="transparent")
            rt_row.pack(fill="x", padx=16, pady=(0, 12))
            for rt, count in rel_types.items():
                from utils.helpers import relationship_color
                ctk.CTkLabel(rt_row,
                             text=f" {rt.replace('_', ' ')}: {count} ",
                             font=FONTS["tiny"],
                             text_color="white",
                             fg_color=relationship_color(rt),
                             corner_radius=4).pack(side="left", padx=4)

    def _refresh_dsa_dropdown(self):
        """Refresh the article dropdown."""
        articles = database.get_all_articles()
        options = [f"{a['article_id']} — {truncate_text(a['headline'], 40)}" for a in articles] if articles else ["No articles yet"]
        self._dsa_dropdown.configure(values=options)
        if options:
            self._dsa_article_var.set(options[0])

    def _run_dsa_traversal(self, algo: str):
        """Run BFS or DFS and display detailed output."""
        selected = self._dsa_article_var.get()
        if not selected or selected == "No articles yet":
            return

        article_id = selected.split(" — ")[0].strip()
        graph = get_graph_manager().get_nx_graph()

        if algo == "bfs":
            result = bfs(graph, article_id, max_depth=4)
            algo_full = "Breadth-First Search (BFS)"
            ds_used = "QUEUE (FIFO) — collections.deque"
            exploration = "Explores layer by layer (level by level)"
        else:
            result = dfs(graph, article_id, max_nodes=30)
            algo_full = "Depth-First Search (DFS)"
            ds_used = "STACK (LIFO) — Python list"
            exploration = "Explores as deep as possible before backtracking"

        self._dsa_algo_output.configure(state="normal")
        self._dsa_algo_output.delete("1.0", "end")

        if result.get("error"):
            self._dsa_algo_output.insert("end", f"Error: {result['error']}\n")
            self._dsa_algo_output.insert("end", "The selected article may not have any connections yet.\n")
            self._dsa_algo_output.insert("end", "Analyze more articles to build the graph.")
        else:
            order = result.get("traversal_order", [])

            output = f"══════════════════════════════════════════\n"
            output += f"  ALGORITHM: {algo_full}\n"
            output += f"══════════════════════════════════════════\n\n"
            output += f"Data Structure Used: {ds_used}\n"
            output += f"Strategy: {exploration}\n"
            output += f"Start Node: {article_id}\n"
            output += f"Nodes Visited: {result.get('visited_count', 0)}\n\n"

            output += f"TRAVERSAL ORDER:\n{'─'*40}\n"
            for i, node in enumerate(order):
                short = node.split("-")[1][:8] if "-" in node else node[:8]
                article = database.get_article_by_id(node)
                headline = truncate_text(article.get("headline", ""), 45) if article else "Unknown"
                pred = article.get("prediction", "?") if article else "?"
                output += f"Step {i+1:>2}: {short} | {pred:<12} | {headline}\n"

                if algo == "bfs" and "levels" in result:
                    level = result["levels"].get(node, 0)
                    if i == 0 or level != result["levels"].get(order[i-1], -1):
                        pass  # Level already shown in order

            output += f"\n{'─'*40}\n"
            output += f"Total nodes reachable: {len(order)}\n"

            if algo == "bfs" and "level_groups" in result:
                output += "\nBy Level (BFS layers):\n"
                for level, nodes in sorted(result["level_groups"].items()):
                    output += f"  Level {level}: {len(nodes)} node(s)\n"

            self._dsa_algo_output.insert("1.0", output)

        self._dsa_algo_output.configure(state="disabled")

    # ────────────────────────────────────────────────────────────
    # SECTION 4: CONNECTED COMPONENTS
    # ────────────────────────────────────────────────────────────
    def _build_components_section(self, parent):
        self._section_header(parent, "04", "Connected Components",
                             "Identify clusters of related news articles.",
                             COLORS["warning"])

        comp_frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=12)
        comp_frame.pack(fill="x", pady=(0, 20))
        comp_inner = ctk.CTkFrame(comp_frame, fg_color="transparent")
        comp_inner.pack(fill="x", padx=20, pady=16)

        exp = (
            "A Connected Component is a maximal set of nodes where every node can reach every other node.\n"
            "Algorithm: Apply BFS/DFS from each unvisited node. Each call discovers a new component.\n"
            "Time Complexity: O(V + E) where V = nodes, E = edges."
        )
        exp_box = ctk.CTkTextbox(comp_inner, font=FONTS["small"],
                                  fg_color=COLORS["bg_secondary"],
                                  text_color=COLORS["text_muted"],
                                  height=55, state="normal")
        exp_box.pack(fill="x", pady=(0, 12))
        exp_box.insert("1.0", exp)
        exp_box.configure(state="disabled")

        ctk.CTkButton(comp_inner, text="🔍 Find Connected Components",
                      font=FONTS["small"],
                      fg_color=COLORS["warning"],
                      hover_color="#d97706",
                      text_color="black",
                      height=40,
                      command=self._find_components).pack(anchor="w", pady=(0, 12))

        self._components_output = ctk.CTkTextbox(
            comp_inner,
            font=FONTS["mono"],
            fg_color=COLORS["bg_input"],
            text_color=COLORS["accent_cyan"],
            height=200,
            state="disabled"
        )
        self._components_output.pack(fill="x")

    def _find_components(self):
        """Find and display connected components."""
        graph = get_graph_manager().get_nx_graph()
        result = find_connected_components(graph)

        self._components_output.configure(state="normal")
        self._components_output.delete("1.0", "end")

        components = result.get("components", [])

        if not components:
            self._components_output.insert("1.0",
                "No components found.\nAnalyze more articles to build the graph.")
        else:
            output = f"Found {result['count']} Connected Component(s)\n"
            output += f"Total Nodes: {result['total_nodes']}, Total Edges: {result['total_edges']}\n"
            output += f"{'═'*50}\n\n"

            for comp in components:
                output += f"📦 News Cluster {comp['id']}: {comp['size']} articles\n"
                output += f"   Dominant: {comp['dominant']}\n"
                output += f"   ✅ Real: {comp['real_count']}  ❌ Fake: {comp['fake_count']}  ⚠️ Suspicious: {comp['suspicious_count']}\n"
                output += f"   Internal Edges: {comp['internal_edges']}\n"
                short_nodes = [n.split("-")[1][:8] if "-" in n else n[:6] for n in comp['nodes'][:5]]
                output += f"   Nodes (first 5): {', '.join(short_nodes)}{'...' if len(comp['nodes']) > 5 else ''}\n\n"

            self._components_output.insert("1.0", output)

        self._components_output.configure(state="disabled")

    def refresh(self):
        """Refresh the DSA page (update dropdown if needed)."""
        self._refresh_dsa_dropdown()
