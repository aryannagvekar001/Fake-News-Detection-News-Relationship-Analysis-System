"""
frontend/history_page.py
Analysis History page — browse all previously analyzed articles.
"""

import tkinter as tk
import customtkinter as ctk
from frontend.components import COLORS, FONTS, ScrollableArticleList, show_toast
from backend import database
from backend.news_analyzer import get_article_analysis
from utils.helpers import format_timestamp, prediction_color, truncate_text


class HistoryPage(ctk.CTkFrame):
    """
    History page with:
    - Scrollable list of all analyzed articles
    - Search bar
    - Filter by prediction (All / Real / Fake / Suspicious)
    - Delete article
    - View detailed article analysis
    """

    def __init__(self, parent, on_view_article=None, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_primary"], **kwargs)
        self._on_view_article = on_view_article
        self._all_articles = []
        self._build_ui()

    def _build_ui(self):
        # ── Header ────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], height=60)
        header.pack(fill="x")
        header.pack_propagate(False)

        header_inner = ctk.CTkFrame(header, fg_color="transparent")
        header_inner.pack(side="left", fill="y", padx=20)

        ctk.CTkLabel(header_inner, text="📚  Analysis History",
                     font=FONTS["heading"],
                     text_color=COLORS["text_primary"]).pack(side="left", pady=15)

        # Refresh button
        ctk.CTkButton(header, text="🔄 Refresh",
                      font=FONTS["small"],
                      fg_color=COLORS["accent_purple"],
                      hover_color="#6d28d9",
                      height=32,
                      width=100,
                      command=self.refresh).pack(side="right", padx=16, pady=14)

        # ── Search & Filter Bar ───────────────────────────────────
        filter_bar = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], height=56)
        filter_bar.pack(fill="x", padx=12, pady=(12, 0))
        filter_bar.pack_propagate(False)

        filter_inner = ctk.CTkFrame(filter_bar, fg_color="transparent")
        filter_inner.pack(fill="both", expand=True, padx=16, pady=10)

        # Search
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", self._on_search_changed)
        ctk.CTkEntry(filter_inner,
                     textvariable=self._search_var,
                     placeholder_text="🔍  Search articles by headline, source, or content...",
                     font=FONTS["body"],
                     fg_color=COLORS["bg_input"],
                     border_color=COLORS["border"],
                     text_color=COLORS["text_primary"],
                     height=36).pack(side="left", fill="x", expand=True)

        # Filter buttons
        self._filter_var = tk.StringVar(value="ALL")
        filter_btns = ctk.CTkFrame(filter_inner, fg_color="transparent")
        filter_btns.pack(side="right", padx=(12, 0))

        filters = [("All", "ALL", COLORS["text_secondary"]),
                   ("Real", "REAL", COLORS["real"]),
                   ("Fake", "FAKE", COLORS["fake"]),
                   ("Suspicious", "SUSPICIOUS", COLORS["suspicious"])]

        for label, val, color in filters:
            ctk.CTkButton(filter_btns,
                          text=label,
                          font=FONTS["tiny"],
                          fg_color=COLORS["bg_secondary"],
                          hover_color=COLORS["bg_input"],
                          text_color=color,
                          height=30,
                          width=80,
                          command=lambda v=val: self._set_filter(v)).pack(side="left", padx=2)

        # ── Article Count Label ───────────────────────────────────
        self._count_label = ctk.CTkLabel(self, text="Loading...",
                                          font=FONTS["small"],
                                          text_color=COLORS["text_muted"])
        self._count_label.pack(anchor="w", padx=20, pady=(8, 4))

        # ── Article List ──────────────────────────────────────────
        self._article_list = ScrollableArticleList(
            self,
            on_select=self._on_article_selected
        )
        self._article_list.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def refresh(self):
        """Load all articles from the database."""
        self._all_articles = database.get_all_articles()
        self._apply_filter()

    def _set_filter(self, prediction: str):
        """Set the current filter and refresh the list."""
        self._filter_var.set(prediction)
        self._apply_filter()

    def _on_search_changed(self, *args):
        """Called when search text changes."""
        self._apply_filter()

    def _apply_filter(self):
        """Filter and display articles based on current search + prediction filter."""
        query = self._search_var.get().strip().lower()
        pred_filter = self._filter_var.get()

        filtered = self._all_articles

        # Apply prediction filter
        if pred_filter != "ALL":
            filtered = [a for a in filtered if a.get("prediction") == pred_filter]

        # Apply search filter
        if query:
            filtered = [
                a for a in filtered
                if query in a.get("headline", "").lower()
                or query in a.get("source", "").lower()
                or query in a.get("content", "").lower()
                or query in a.get("article_id", "").lower()
            ]

        count = len(filtered)
        self._count_label.configure(text=f"Showing {count} article{'s' if count != 1 else ''}")

        # Render
        self._render_articles(filtered)

    def _render_articles(self, articles: list):
        """Render the article list."""
        # Clear existing
        for widget in self._article_list.winfo_children():
            widget.destroy()

        if not articles:
            ctk.CTkLabel(self._article_list,
                         text="No articles found. Try a different search or filter.",
                         font=FONTS["body"],
                         text_color=COLORS["text_muted"]).pack(pady=40)
            return

        for article in articles:
            self._create_article_row(article)

    def _create_article_row(self, article: dict):
        """Create a single article row with details and action buttons."""
        pred = article.get("prediction", "UNKNOWN")
        color = prediction_color(pred)

        row = ctk.CTkFrame(self._article_list, fg_color=COLORS["bg_card"],
                           corner_radius=8)
        row.pack(fill="x", pady=3, padx=4)

        # Left indicator
        indicator = ctk.CTkFrame(row, fg_color=color, width=4, corner_radius=2)
        indicator.pack(side="left", fill="y")

        # Main content
        content = ctk.CTkFrame(row, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=12, pady=10)

        # Headline
        ctk.CTkLabel(content,
                     text=truncate_text(article.get("headline", "Unknown"), 85),
                     font=FONTS["body"],
                     text_color=COLORS["text_primary"],
                     anchor="w").pack(anchor="w")

        # Meta row
        meta = ctk.CTkFrame(content, fg_color="transparent")
        meta.pack(anchor="w", fill="x", pady=(3, 0))

        meta_items = [
            f"📰 {article.get('source', 'Unknown')}",
            f"🕐 {format_timestamp(article.get('timestamp'))}",
            f"📊 {article.get('topic', 'General')}",
        ]
        if article.get("is_duplicate"):
            meta_items.append("🔗 DUPLICATE")
        if article.get("word_count"):
            meta_items.append(f"📝 {article.get('word_count')} words")

        for item in meta_items:
            ctk.CTkLabel(meta, text=item + "  ", font=FONTS["tiny"],
                         text_color=COLORS["text_muted"]).pack(side="left")

        # Right area: badge + confidence + buttons
        right = ctk.CTkFrame(row, fg_color="transparent")
        right.pack(side="right", padx=10)

        # Prediction badge
        ctk.CTkLabel(right, text=f"  {pred}  ",
                     font=FONTS["tiny"],
                     text_color="white",
                     fg_color=color,
                     corner_radius=4).pack(pady=(10, 2))

        # Confidence
        conf = article.get("confidence", 0)
        if conf <= 1.0:
            conf *= 100
        ctk.CTkLabel(right, text=f"{conf:.0f}% conf.",
                     font=FONTS["tiny"],
                     text_color=COLORS["text_muted"]).pack()

        # Buttons
        btn_frame = ctk.CTkFrame(right, fg_color="transparent")
        btn_frame.pack(pady=(4, 10))

        ctk.CTkButton(btn_frame, text="👁 View",
                      font=FONTS["tiny"],
                      fg_color=COLORS["accent_purple"],
                      hover_color="#6d28d9",
                      height=26,
                      width=55,
                      command=lambda a=article: self._on_article_selected(a)).pack(side="left", padx=2)

        ctk.CTkButton(btn_frame, text="🗑",
                      font=FONTS["tiny"],
                      fg_color=COLORS["bg_secondary"],
                      hover_color=COLORS["fake"],
                      height=26,
                      width=30,
                      command=lambda a=article: self._delete_article(a)).pack(side="left")

    def _on_article_selected(self, article: dict):
        """Handle article selection — open detailed view."""
        if self._on_view_article:
            # Get full analysis data
            full_data = get_article_analysis(article.get("article_id", ""))
            if full_data:
                self._on_view_article(full_data)
            else:
                self._on_view_article(article)

    def _delete_article(self, article: dict):
        """Delete an article from the database."""
        article_id = article.get("article_id", "")
        if not article_id:
            return

        success = database.delete_article(article_id)
        if success:
            show_toast(self.winfo_toplevel(), "Article deleted successfully.",
                       color=COLORS["success"])
            self.refresh()
        else:
            show_toast(self.winfo_toplevel(), "Failed to delete article.",
                       color=COLORS["error"])
