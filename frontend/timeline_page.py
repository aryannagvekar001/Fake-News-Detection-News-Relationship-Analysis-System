"""
frontend/timeline_page.py
Timeline Analysis page — shows related articles in chronological order.
"""

import tkinter as tk
import customtkinter as ctk
from frontend.components import COLORS, FONTS
from backend import database
from utils.helpers import format_timestamp, prediction_color, truncate_text


class TimelinePage(ctk.CTkFrame):
    """
    Timeline view showing articles sorted by timestamp.
    Highlights related article clusters chronologically.
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
        ctk.CTkLabel(header_inner, text="⏱️  Timeline Analysis",
                     font=FONTS["heading"],
                     text_color=COLORS["text_primary"]).pack(side="left", pady=15)

        ctk.CTkButton(header, text="🔄 Refresh",
                      font=FONTS["small"],
                      fg_color=COLORS["accent_purple"],
                      hover_color="#6d28d9",
                      height=32, width=100,
                      command=self.refresh).pack(side="right", padx=16, pady=14)

        # Main layout
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=20, pady=16)
        main.columnconfigure(0, weight=3)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)

        # Timeline canvas
        self._timeline_scroll = ctk.CTkScrollableFrame(main, fg_color=COLORS["bg_primary"])
        self._timeline_scroll.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        # Right panel: topic filter
        right = ctk.CTkFrame(main, fg_color=COLORS["bg_card"], corner_radius=12)
        right.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(right, text="📊 Timeline Stats",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", padx=16, pady=(16, 8))

        self._stats_label = ctk.CTkLabel(right, text="No data yet.",
                                          font=FONTS["small"],
                                          text_color=COLORS["text_muted"])
        self._stats_label.pack(anchor="w", padx=16)

        ctk.CTkLabel(right, text="🏷️ Filter by Topic",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", padx=16, pady=(16, 8))

        self._topic_var = tk.StringVar(value="All Topics")
        self._topic_menu = ctk.CTkOptionMenu(
            right,
            variable=self._topic_var,
            values=["All Topics"],
            font=FONTS["small"],
            fg_color=COLORS["bg_input"],
            button_color=COLORS["accent_purple"],
            button_hover_color="#6d28d9",
            command=lambda _: self._filter_timeline()
        )
        self._topic_menu.pack(padx=16, fill="x")

        ctk.CTkLabel(right, text="🎯 Filter by Prediction",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", padx=16, pady=(16, 8))

        self._pred_var = tk.StringVar(value="All")
        for label, val in [("All", "All"), ("Real", "REAL"), ("Fake", "FAKE"), ("Suspicious", "SUSPICIOUS")]:
            ctk.CTkButton(right, text=label,
                          font=FONTS["small"],
                          fg_color=COLORS["bg_secondary"],
                          hover_color=COLORS["bg_input"],
                          height=30,
                          command=lambda v=val: self._set_pred_filter(v)).pack(fill="x", padx=16, pady=2)

        self._all_articles = []

    def refresh(self):
        """Reload timeline from database."""
        self._all_articles = database.get_all_articles()
        self._all_articles.sort(key=lambda a: a.get("timestamp", ""), reverse=False)

        # Update topic menu
        topics = list(set(a.get("topic", "General") for a in self._all_articles))
        topics.sort()
        self._topic_menu.configure(values=["All Topics"] + topics)

        # Update stats
        total = len(self._all_articles)
        self._stats_label.configure(
            text=f"Total: {total} articles\nTime span: " +
                 (f"\n{format_timestamp(self._all_articles[0].get('timestamp'))}\n→\n{format_timestamp(self._all_articles[-1].get('timestamp'))}"
                  if self._all_articles else "N/A")
        )

        self._filter_timeline()

    def _set_pred_filter(self, val: str):
        self._pred_var.set(val)
        self._filter_timeline()

    def _filter_timeline(self):
        """Apply filters and render timeline."""
        topic = self._topic_var.get()
        pred = self._pred_var.get()

        filtered = self._all_articles
        if topic != "All Topics":
            filtered = [a for a in filtered if a.get("topic") == topic]
        if pred != "All":
            filtered = [a for a in filtered if a.get("prediction") == pred]

        self._render_timeline(filtered)

    def _render_timeline(self, articles: list):
        """Render the timeline view."""
        for widget in self._timeline_scroll.winfo_children():
            widget.destroy()

        if not articles:
            ctk.CTkLabel(self._timeline_scroll,
                         text="No articles match the current filter.\nAnalyze articles to build the timeline.",
                         font=FONTS["body"],
                         text_color=COLORS["text_muted"],
                         justify="center").pack(pady=60)
            return

        ctk.CTkLabel(self._timeline_scroll,
                     text=f"Showing {len(articles)} articles chronologically:",
                     font=FONTS["small"],
                     text_color=COLORS["text_muted"]).pack(anchor="w", pady=(0, 12))

        for i, article in enumerate(articles):
            pred = article.get("prediction", "UNKNOWN")
            color = prediction_color(pred)

            # Timeline item
            item_frame = ctk.CTkFrame(self._timeline_scroll, fg_color="transparent")
            item_frame.pack(fill="x", pady=4)

            # Left: time + line
            time_frame = ctk.CTkFrame(item_frame, fg_color="transparent", width=100)
            time_frame.pack(side="left", fill="y")
            time_frame.pack_propagate(False)

            from datetime import datetime
            ts = article.get("timestamp", "")
            try:
                dt = datetime.fromisoformat(ts)
                time_str = dt.strftime("%I:%M %p")
                date_str = dt.strftime("%d %b")
            except Exception:
                time_str = "N/A"
                date_str = ""

            ctk.CTkLabel(time_frame, text=time_str,
                         font=("Segoe UI", 11, "bold"),
                         text_color=COLORS["text_secondary"]).pack(anchor="e", padx=(0, 12))
            ctk.CTkLabel(time_frame, text=date_str,
                         font=FONTS["tiny"],
                         text_color=COLORS["text_muted"]).pack(anchor="e", padx=(0, 12))

            # Center: colored dot
            dot_frame = ctk.CTkFrame(item_frame, fg_color="transparent", width=24)
            dot_frame.pack(side="left", fill="y")
            dot_frame.pack_propagate(False)

            # Dot
            dot = ctk.CTkFrame(dot_frame, fg_color=color, width=16, height=16,
                                corner_radius=8)
            dot.pack(pady=12)

            # Vertical line (except last item)
            if i < len(articles) - 1:
                line = ctk.CTkFrame(dot_frame, fg_color=COLORS["border"],
                                    width=2, height=30, corner_radius=1)
                line.pack()

            # Right: article card
            card = ctk.CTkFrame(item_frame, fg_color=COLORS["bg_card"],
                                corner_radius=8)
            card.pack(side="left", fill="x", expand=True, padx=(8, 0))

            card_inner = ctk.CTkFrame(card, fg_color="transparent")
            card_inner.pack(fill="x", padx=12, pady=10)

            # Top row: headline + badge
            top_row = ctk.CTkFrame(card_inner, fg_color="transparent")
            top_row.pack(fill="x")

            ctk.CTkLabel(top_row,
                         text=truncate_text(article.get("headline", ""), 70),
                         font=FONTS["body"],
                         text_color=COLORS["text_primary"],
                         anchor="w").pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(top_row, text=f"  {pred}  ",
                         font=FONTS["tiny"],
                         text_color="white",
                         fg_color=color,
                         corner_radius=4).pack(side="right", padx=(8, 0))

            # Meta
            conf = article.get("confidence", 0)
            if conf <= 1.0:
                conf *= 100

            meta_text = f"📰 {article.get('source', 'Unknown')}  ·  📊 {article.get('topic', 'General')}  ·  {conf:.0f}% confidence"
            if article.get("is_duplicate"):
                meta_text += "  ·  🔗 DUPLICATE"

            ctk.CTkLabel(card_inner, text=meta_text,
                         font=FONTS["tiny"],
                         text_color=COLORS["text_muted"],
                         anchor="w").pack(anchor="w", pady=(3, 0))
