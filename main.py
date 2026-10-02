"""
main.py
Fake News Intelligence — Main Application Entry Point

College DSA Project — Unit IV: Graph and Hashing Concepts
Author: Aryan
Demonstrates: TF-IDF ML classification, SHA-256 Hashing, Custom Hash Table,
              NetworkX Graph, BFS, DFS, Connected Components

Run: python main.py
"""

import sys
import os
import tkinter as tk
import customtkinter as ctk
import threading

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ─────────────────────────────────────────────
# STARTUP: Initialize backend systems
# ─────────────────────────────────────────────
print("=" * 60)
print("  Fake News Intelligence")
print("  News Detection & Relationship Analysis System")
print("  DSA Project — Graph and Hashing (Unit IV)")
print("=" * 60)

print("\n[STARTUP] Initializing database...")
from backend.database import init_database, get_all_articles, get_all_relationships
init_database()

print("[STARTUP] Loading graph from database...")
from backend.graph_manager import get_graph_manager, reset_graph_manager
graph_manager = reset_graph_manager()
articles = get_all_articles()
relationships = get_all_relationships()
graph_manager.load_from_database(articles, relationships)
print(f"[STARTUP] Graph loaded: {graph_manager.node_count()} nodes, {graph_manager.edge_count()} edges")

print("[STARTUP] Loading keyword index...")
from backend.keyword_manager import rebuild_from_articles
rebuild_from_articles(articles)
print(f"[STARTUP] Keyword index loaded: {len(articles)} articles indexed")

print("[STARTUP] Loading ML model...")
from backend.fake_news_model import ensure_model_trained
model_result = ensure_model_trained()
if model_result.get("success"):
    accuracy = model_result.get("accuracy", 0)
    print(f"[STARTUP] ML Model ready. Accuracy: {accuracy:.1f}%")
else:
    print(f"[STARTUP] ML Model warning: {model_result.get('error', 'Unknown')}")

print("[STARTUP] All systems ready.\n")

# ─────────────────────────────────────────────
# CONFIGURE CTK THEME
# ─────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

from frontend.components import COLORS, FONTS, configure_ctk_theme
configure_ctk_theme()


class FakeNewsApp(ctk.CTk):
    """
    Main application window.

    Navigation sidebar with tabs:
    - Dashboard
    - Analyze News
    - News Graph
    - History
    - Sources
    - DSA Analysis
    - Timeline
    - About
    """

    # Navigation items: (icon, label, page_key)
    NAV_ITEMS = [
        ("📊", "Dashboard", "dashboard"),
        ("🔍", "Analyze News", "analyze"),
        ("🕸️", "News Graph", "graph"),
        ("📚", "History", "history"),
        ("📡", "Sources", "sources"),
        ("⏱️", "Timeline", "timeline"),
        ("ℹ️", "About", "about"),
    ]

    def __init__(self):
        super().__init__()

        self.title("Fake News Intelligence — News Detection & Relationship Analysis System")
        self.geometry("1400x820")
        self.minsize(1100, 700)
        self.configure(fg_color=COLORS["bg_primary"])

        # Try to set icon
        try:
            self.iconbitmap(default="")
        except Exception:
            pass

        self._current_page = None
        self._pages = {}
        self._nav_buttons = {}
        self._article_page_visible = False

        self._build_ui()
        self._navigate("dashboard")

        # Bind keyboard shortcut for quick navigation
        self.bind("<Control-1>", lambda e: self._navigate("dashboard"))
        self.bind("<Control-2>", lambda e: self._navigate("analyze"))
        self.bind("<Control-3>", lambda e: self._navigate("graph"))
        self.bind("<Control-4>", lambda e: self._navigate("history"))

    def _build_ui(self):
        """Build the main application layout."""
        # ── Main layout: sidebar + content ────────────────────────
        self.columnconfigure(0, weight=0)  # Sidebar (fixed width)
        self.columnconfigure(1, weight=1)  # Content area
        self.rowconfigure(0, weight=1)

        # ── Sidebar ───────────────────────────────────────────────
        sidebar = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"],
                               width=200, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        # App logo / title
        logo_frame = ctk.CTkFrame(sidebar, fg_color=COLORS["accent_purple"],
                                   corner_radius=0, height=80)
        logo_frame.pack(fill="x")
        logo_frame.pack_propagate(False)

        logo_inner = ctk.CTkFrame(logo_frame, fg_color="transparent")
        logo_inner.pack(fill="both", expand=True, padx=16, pady=12)

        ctk.CTkLabel(logo_inner, text="🔍",
                     font=("Segoe UI Emoji", 22)).pack(anchor="w")
        ctk.CTkLabel(logo_inner, text="Fake News",
                     font=("Segoe UI", 13, "bold"),
                     text_color="white").pack(anchor="w")
        ctk.CTkLabel(logo_inner, text="Intelligence",
                     font=("Segoe UI", 11),
                     text_color="#c4b5fd").pack(anchor="w")

        # Separator
        ctk.CTkFrame(sidebar, fg_color=COLORS["border"], height=1).pack(fill="x")

        # Navigation buttons
        nav_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        nav_frame.pack(fill="both", expand=True, padx=8, pady=12)

        for icon, label, page_key in self.NAV_ITEMS:
            btn = ctk.CTkButton(
                nav_frame,
                text=f"{icon}  {label}",
                font=FONTS["body"],
                fg_color="transparent",
                hover_color=COLORS["bg_card"],
                text_color=COLORS["text_secondary"],
                anchor="w",
                height=40,
                corner_radius=8,
                command=lambda k=page_key: self._navigate(k)
            )
            btn.pack(fill="x", pady=2)
            self._nav_buttons[page_key] = btn

        # Bottom: version info
        ctk.CTkFrame(sidebar, fg_color=COLORS["border"], height=1).pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(sidebar, text="Fake News Intelligence\nv1.0",
                     font=FONTS["tiny"],
                     text_color=COLORS["text_muted"],
                     justify="center").pack(pady=8)

        # ── Content Area ──────────────────────────────────────────
        self._content_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_primary"],
                                            corner_radius=0)
        self._content_frame.grid(row=0, column=1, sticky="nsew")

        # Initialize pages
        self._init_pages()

    def _init_pages(self):
        """Initialize all page frames (lazy — only shown when navigated to)."""
        from frontend.dashboard import DashboardPage
        from frontend.analyze_page import AnalyzePage
        from frontend.graph_page import GraphPage
        from frontend.history_page import HistoryPage
        from frontend.article_page import ArticlePage
        from frontend.sources_page import SourcesPage
        from frontend.dsa_page import DSAPage
        from frontend.timeline_page import TimelinePage

        self._pages["dashboard"] = DashboardPage(self._content_frame)
        self._pages["analyze"] = AnalyzePage(
            self._content_frame,
            on_analysis_complete=self._on_analysis_complete
        )
        self._pages["graph"] = GraphPage(self._content_frame)
        self._pages["history"] = HistoryPage(
            self._content_frame,
            on_view_article=self._show_article_detail
        )
        self._pages["article"] = ArticlePage(
            self._content_frame,
            on_back=self._hide_article_detail
        )
        self._pages["sources"] = SourcesPage(self._content_frame)
        self._pages["dsa"] = DSAPage(self._content_frame)
        self._pages["timeline"] = TimelinePage(self._content_frame)
        self._pages["about"] = self._build_about_page()

    def _build_about_page(self):
        """Build the About page with project info and viva Q&A."""
        page = ctk.CTkScrollableFrame(self._content_frame, fg_color=COLORS["bg_primary"])

        # Header
        header = ctk.CTkFrame(page, fg_color=COLORS["bg_secondary"], corner_radius=16)
        header.pack(fill="x", padx=20, pady=(20, 16))

        inner = ctk.CTkFrame(header, fg_color="transparent")
        inner.pack(padx=24, pady=20)

        ctk.CTkLabel(inner, text="🔍 Fake News Intelligence",
                     font=("Segoe UI", 22, "bold"),
                     text_color=COLORS["text_primary"]).pack(anchor="w")
        ctk.CTkLabel(inner, text="News Detection & Relationship Analysis System",
                     font=FONTS["subtitle"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(4, 0))
        ctk.CTkLabel(inner, text="College DSA Project  ·  Unit IV: Graph and Hashing Concepts",
                     font=FONTS["small"],
                     text_color=COLORS["text_muted"]).pack(anchor="w", pady=(4, 0))

        # Disclaimer
        disc = ctk.CTkFrame(page, fg_color="#1c1008", corner_radius=8)
        disc.pack(fill="x", padx=20, pady=(0, 16))
        ctk.CTkLabel(disc,
                     text="⚠️ IMPORTANT DISCLAIMER: This application is a college DSA project using DEMO data "
                          "and a simple ML model trained on SAMPLE articles. ALL analysis results are SYSTEM "
                          "ASSESSMENTS ONLY and must NOT be used to determine the truth or falsehood of any "
                          "real-world news article.",
                     font=FONTS["small"],
                     text_color="#f59e0b",
                     wraplength=900).pack(padx=16, pady=12)

        # DSA Concepts
        self._about_section(page, "🏗️ DSA Concepts Implemented",
                            [
                                ("Hashing (SHA-256)", "Used for exact duplicate detection. Same normalized text → same hash. O(1) lookup."),
                                ("SimHash", "Locality Sensitive Hashing for near-duplicate detection. Hamming distance measures similarity."),
                                ("Custom Hash Table", "Separate chaining collision resolution. Polynomial rolling hash function. Used for keyword index."),
                                ("Graph (DiGraph)", "NetworkX directed graph. Articles = nodes, relationships = edges."),
                                ("BFS", "Breadth-First Search using Queue (FIFO). Finds articles within N relationship levels."),
                                ("DFS", "Depth-First Search using Stack (LIFO). Explores all articles in a connected cluster."),
                                ("Connected Components", "Identifies clusters of related news articles. Applied to undirected view of the graph."),
                                ("TF-IDF", "Term Frequency-Inverse Document Frequency. Converts text to numerical vectors for ML."),
                                ("Logistic Regression", "Binary classifier trained on real/fake labelled examples."),
                                ("Cosine Similarity", "Measures text similarity using TF vectors. Used for near-duplicate detection."),
                            ])

        # Viva Q&A
        self._about_section(page, "🎓 Viva Q&A Reference",
                            [
                                ("Q: What is hashing?",
                                 "A: A hash function maps input of any size to a fixed-size output (the hash). "
                                 "It's deterministic, fast, and collision-resistant. We use SHA-256."),
                                ("Q: How does duplicate detection work?",
                                 "A: We normalize text (lowercase, remove stopwords), then compute SHA-256. "
                                 "Two articles with the same normalized hash are exact duplicates (O(1) check)."),
                                ("Q: What is a hash collision?",
                                 "A: When two different inputs produce the same hash. Our custom hash table "
                                 "resolves collisions using Separate Chaining (linked list per bucket)."),
                                ("Q: Why represent news as a graph?",
                                 "A: A graph captures relationships between articles — same topic, similar content, "
                                 "same source, duplicates. This lets us find clusters of related misinformation."),
                                ("Q: What is BFS and when do we use it?",
                                 "A: BFS (Breadth-First Search) uses a Queue. It explores articles layer by layer. "
                                 "We use it to find all articles within N relationship levels of a given article."),
                                ("Q: What is DFS and when do we use it?",
                                 "A: DFS (Depth-First Search) uses a Stack. It goes as deep as possible before backtracking. "
                                 "We use it to explore all articles in a connected cluster."),
                                ("Q: What are connected components?",
                                 "A: A maximal set of nodes where every node is reachable from every other. "
                                 "Each component is a 'news cluster'. We find them using BFS from unvisited nodes."),
                                ("Q: What is TF-IDF?",
                                 "A: TF = Term Frequency (how often a word appears in a document). "
                                 "IDF = Inverse Document Frequency (penalizes common words across all documents). "
                                 "TF-IDF captures words that are important to a specific article but not in general."),
                                ("Q: What is Logistic Regression?",
                                 "A: A linear classifier that outputs a probability. We train it on labelled "
                                 "real/fake articles. It learns which words/patterns are associated with fake news."),
                                ("Q: What are the limitations of your ML model?",
                                 "A: Trained on a small DEMO dataset, not real verified news. Cannot detect "
                                 "context-dependent falsehoods. High confidence does NOT mean ground truth. "
                                 "Language and domain shift can degrade performance significantly."),
                            ])

        # Technologies
        self._about_section(page, "⚙️ Technologies Used",
                            [
                                ("Python 3.x", "Core programming language"),
                                ("CustomTkinter", "Modern dark-themed desktop GUI framework"),
                                ("SQLite", "Local database for persistent storage"),
                                ("NetworkX", "Graph data structure and algorithms library"),
                                ("scikit-learn", "TF-IDF vectorizer and Logistic Regression classifier"),
                                ("Matplotlib", "Graph visualization and dashboard charts"),
                                ("hashlib", "SHA-256 and MD5 hashing (Python standard library)"),
                                ("pandas", "CSV dataset loading and processing"),
                                ("joblib", "Model serialization/deserialization"),
                            ])

        return page

    def _about_section(self, parent, title: str, items: list):
        """Create an about section with a header and Q&A items."""
        section = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=12)
        section.pack(fill="x", padx=20, pady=(0, 16))

        inner = ctk.CTkFrame(section, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=16)

        ctk.CTkLabel(inner, text=title,
                     font=FONTS["heading"],
                     text_color=COLORS["accent_cyan"]).pack(anchor="w", pady=(0, 12))

        line = ctk.CTkFrame(inner, fg_color=COLORS["accent_cyan"], height=2, corner_radius=1)
        line.pack(fill="x", pady=(0, 12))

        for q, a in items:
            item_frame = ctk.CTkFrame(inner, fg_color=COLORS["bg_secondary"], corner_radius=8)
            item_frame.pack(fill="x", pady=4)

            item_inner = ctk.CTkFrame(item_frame, fg_color="transparent")
            item_inner.pack(fill="x", padx=16, pady=10)

            ctk.CTkLabel(item_inner, text=q,
                         font=FONTS["subheading"],
                         text_color=COLORS["accent_purple"],
                         anchor="w").pack(anchor="w")
            ctk.CTkLabel(item_inner, text=a,
                         font=FONTS["small"],
                         text_color=COLORS["text_secondary"],
                         anchor="w",
                         wraplength=800).pack(anchor="w", pady=(4, 0))

    def _navigate(self, page_key: str):
        """Navigate to a specific page."""
        # Hide all pages
        for key, page in self._pages.items():
            page.place_forget()

        # Show target page
        target = self._pages.get(page_key)
        if target is None:
            return

        target.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._current_page = page_key

        # Refresh page data when navigated to
        refresh_map = {
            "dashboard": lambda: self._pages["dashboard"].refresh(),
            "graph": lambda: self._pages["graph"].refresh(),
            "history": lambda: self._pages["history"].refresh(),
            "sources": lambda: self._pages["sources"].refresh(),
            "timeline": lambda: self._pages["timeline"].refresh(),
        }
        if page_key in refresh_map:
            refresh_map[page_key]()

        # Update nav button styles
        for key, btn in self._nav_buttons.items():
            if key == page_key:
                btn.configure(fg_color=COLORS["accent_purple"],
                              text_color="white")
            else:
                btn.configure(fg_color="transparent",
                              text_color=COLORS["text_secondary"])

    def _on_analysis_complete(self, result: dict):
        """Called when an article analysis completes."""
        # Reload graph with new data
        from backend.graph_manager import get_graph_manager
        gm = get_graph_manager()
        # The graph was already updated by news_analyzer, just ensure consistency
        print(f"[APP] Analysis complete. Graph now has {gm.node_count()} nodes.")

    def _show_article_detail(self, article: dict):
        """Show the article detail page (from history)."""
        self._pages["article"].load_article(article)
        self._navigate("article")
        # Remove "article" from nav highlight
        for key, btn in self._nav_buttons.items():
            btn.configure(fg_color="transparent", text_color=COLORS["text_secondary"])

    def _hide_article_detail(self):
        """Go back from article detail to history."""
        self._navigate("history")

    def on_closing(self):
        """Handle window close."""
        print("[APP] Shutting down...")
        self.destroy()


def main():
    """Main entry point."""
    app = FakeNewsApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    print("[APP] Application started. Window displayed.")
    app.mainloop()


if __name__ == "__main__":
    main()
