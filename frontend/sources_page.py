"""
frontend/sources_page.py
Source Analysis page — statistics per publisher/source.
Uses neutral wording as required (observed results, not absolute truth).
"""

import tkinter as tk
import customtkinter as ctk
from frontend.components import COLORS, FONTS
from backend import database
from utils.helpers import safe_divide


class SourcesPage(ctk.CTkFrame):
    """
    Source Analysis page displaying per-publisher statistics.
    
    IMPORTANT: All wording is neutral. The application does NOT
    declare any source as "trustworthy" or "untrustworthy" based
    on limited demo data.
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
        ctk.CTkLabel(header_inner, text="📡  Source Analysis",
                     font=FONTS["heading"],
                     text_color=COLORS["text_primary"]).pack(side="left", pady=15)

        ctk.CTkButton(header, text="🔄 Refresh",
                      font=FONTS["small"],
                      fg_color=COLORS["accent_purple"],
                      hover_color="#6d28d9",
                      height=32, width=100,
                      command=self.refresh).pack(side="right", padx=16, pady=14)

        # Disclaimer
        disclaimer = ctk.CTkFrame(self, fg_color="#1c1008", corner_radius=0)
        disclaimer.pack(fill="x")
        ctk.CTkLabel(disclaimer,
                     text="ℹ️  The data shown below reflects OBSERVED RESULTS within the analyzed dataset only. "
                          "It does NOT indicate whether a source is reliable or unreliable in general. "
                          "All assessments are made by a DEMO model on SAMPLE data.",
                     font=FONTS["tiny"],
                     text_color="#f59e0b",
                     wraplength=1000).pack(padx=20, pady=10)

        # Search
        search_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], height=52)
        search_frame.pack(fill="x", padx=12, pady=(12, 0))
        search_frame.pack_propagate(False)

        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *a: self._filter_sources())
        ctk.CTkEntry(search_frame,
                     textvariable=self._search_var,
                     placeholder_text="🔍  Search sources...",
                     font=FONTS["body"],
                     fg_color=COLORS["bg_input"],
                     border_color=COLORS["border"],
                     text_color=COLORS["text_primary"],
                     height=36).pack(side="left", fill="x", expand=True, padx=16, pady=8)

        # Content: table header + scrollable rows
        self._table_header = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], height=40)
        self._table_header.pack(fill="x", padx=12, pady=(8, 0))
        self._table_header.pack_propagate(False)

        cols = [("Source Name", 3), ("Total", 1), ("Real", 1), ("Fake", 1),
                ("Suspicious", 1), ("Duplicates", 1), ("Last Seen", 2)]
        for col_name, weight in cols:
            ctk.CTkLabel(self._table_header, text=col_name,
                         font=FONTS["small"],
                         text_color=COLORS["text_muted"]).pack(side="left",
                                                                padx=12, pady=10,
                                                                expand=(weight > 1))

        self._scroll = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg_primary"])
        self._scroll.pack(fill="both", expand=True, padx=12, pady=(4, 12))

        self._all_sources = []

    def refresh(self):
        """Refresh source data from the database."""
        self._all_sources = database.get_all_sources()
        self._filter_sources()

    def _filter_sources(self):
        """Filter sources by search query."""
        query = self._search_var.get().strip().lower()
        filtered = self._all_sources
        if query:
            filtered = [s for s in filtered if query in s.get("source_name", "").lower()]

        self._render_sources(filtered)

    def _render_sources(self, sources: list):
        """Render the source table."""
        for widget in self._scroll.winfo_children():
            widget.destroy()

        if not sources:
            ctk.CTkLabel(self._scroll,
                         text="No sources found. Analyze articles from various sources first.",
                         font=FONTS["body"],
                         text_color=COLORS["text_muted"]).pack(pady=40)
            return

        for i, source in enumerate(sources):
            bg = COLORS["bg_card"] if i % 2 == 0 else COLORS["bg_secondary"]
            row = ctk.CTkFrame(self._scroll, fg_color=bg, corner_radius=6)
            row.pack(fill="x", pady=2)

            total = source.get("total_articles", 0)
            real = source.get("real_count", 0)
            fake = source.get("fake_count", 0)
            suspicious = source.get("suspicious_count", 0)
            duplicates = source.get("duplicate_count", 0)

            # Source name
            name_frame = ctk.CTkFrame(row, fg_color="transparent")
            name_frame.pack(side="left", padx=12, pady=10, fill="x", expand=True)
            ctk.CTkLabel(name_frame, text=source.get("source_name", "Unknown"),
                         font=FONTS["body"],
                         text_color=COLORS["text_primary"],
                         anchor="w").pack(anchor="w")

            from utils.helpers import format_timestamp
            ctk.CTkLabel(name_frame,
                         text=f"First seen: {format_timestamp(source.get('first_seen'))}",
                         font=FONTS["tiny"],
                         text_color=COLORS["text_muted"],
                         anchor="w").pack(anchor="w")

            # Stats
            def stat_label(parent, value, color=None):
                ctk.CTkLabel(parent, text=str(value),
                             font=FONTS["body"],
                             text_color=color or COLORS["text_primary"],
                             width=50).pack(side="left", padx=8)

            stat_label(row, total, COLORS["accent_cyan"])
            stat_label(row, real, COLORS["real"])
            stat_label(row, fake, COLORS["fake"])
            stat_label(row, suspicious, COLORS["suspicious"])
            stat_label(row, duplicates, "#8b5cf6")

            # Last seen
            from utils.helpers import format_timestamp
            ctk.CTkLabel(row,
                         text=format_timestamp(source.get("last_seen")),
                         font=FONTS["tiny"],
                         text_color=COLORS["text_muted"],
                         width=120).pack(side="right", padx=12)

            # Mini bar showing fake ratio
            if total > 0:
                fake_ratio = safe_divide(fake, total)
                bar_frame = ctk.CTkFrame(row, fg_color="transparent", width=80)
                bar_frame.pack(side="right", padx=4)
                bar_frame.pack_propagate(False)
                bar = ctk.CTkProgressBar(bar_frame, height=6,
                                          fg_color=COLORS["bg_input"],
                                          progress_color=COLORS["fake"],
                                          width=70)
                bar.pack(pady=16)
                bar.set(fake_ratio)
