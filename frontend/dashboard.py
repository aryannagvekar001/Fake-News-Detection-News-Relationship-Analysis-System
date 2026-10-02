"""
frontend/dashboard.py
Dashboard page showing system-wide statistics and charts.
"""

import tkinter as tk
import customtkinter as ctk
from frontend.components import COLORS, FONTS, StatCard, SectionHeader
from backend import database
from backend.graph_manager import get_graph_manager
from backend.graph_algorithms import find_connected_components


class DashboardPage(ctk.CTkFrame):
    """
    Dashboard showing:
    - Total articles, real, fake, suspicious, duplicates
    - Graph nodes, edges, clusters
    - Bar chart of prediction distribution
    - Recent articles list
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_primary"], **kwargs)
        self._build_ui()

    def _build_ui(self):
        # Scrollable content
        scroll = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg_primary"])
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        # ── Header ────────────────────────────────────────────────
        header = ctk.CTkFrame(scroll, fg_color=COLORS["bg_secondary"], corner_radius=16)
        header.pack(fill="x", pady=(0, 20))

        inner = ctk.CTkFrame(header, fg_color="transparent")
        inner.pack(padx=24, pady=20)

        ctk.CTkLabel(inner, text="📊 Dashboard",
                     font=FONTS["title"],
                     text_color=COLORS["text_primary"]).pack(anchor="w")
        ctk.CTkLabel(inner, text="Real-time statistics from your analyzed articles database.",
                     font=FONTS["small"],
                     text_color=COLORS["text_muted"]).pack(anchor="w")

        # ── Stats Cards ───────────────────────────────────────────
        ctk.CTkLabel(scroll, text="📈 Article Statistics",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(0, 8))

        stats_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, 20))
        stats_frame.columnconfigure([0, 1, 2, 3, 4], weight=1)

        self._stat_cards = {}
        card_defs = [
            ("total", "Total Analyzed", "0", "📰", COLORS["accent_cyan"]),
            ("real", "Real Articles", "0", "✅", COLORS["real"]),
            ("fake", "Fake Articles", "0", "❌", COLORS["fake"]),
            ("suspicious", "Suspicious", "0", "⚠️", COLORS["suspicious"]),
            ("duplicates", "Duplicates", "0", "🔗", "#8b5cf6"),
        ]

        for col, (key, title, val, icon, color) in enumerate(card_defs):
            card = StatCard(stats_frame, title=title, value=val, icon=icon, color=color)
            card.grid(row=0, column=col, padx=6, pady=4, sticky="nsew")
            self._stat_cards[key] = card

        # ── Graph Stats ───────────────────────────────────────────
        ctk.CTkLabel(scroll, text="🕸️ Graph Statistics",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(0, 8))

        graph_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        graph_frame.pack(fill="x", pady=(0, 20))
        graph_frame.columnconfigure([0, 1, 2, 3], weight=1)

        graph_card_defs = [
            ("nodes", "Graph Nodes", "0", "⬡", COLORS["accent_purple"]),
            ("edges", "Graph Edges", "0", "↔", COLORS["accent_cyan"]),
            ("relationships", "Relationships", "0", "🔀", COLORS["info"]),
            ("clusters", "News Clusters", "0", "🗂️", COLORS["warning"]),
        ]

        for col, (key, title, val, icon, color) in enumerate(graph_card_defs):
            card = StatCard(graph_frame, title=title, value=val, icon=icon, color=color)
            card.grid(row=0, column=col, padx=6, pady=4, sticky="nsew")
            self._stat_cards[key] = card

        # ── Chart ─────────────────────────────────────────────────
        ctk.CTkLabel(scroll, text="📉 Prediction Distribution",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(0, 8))

        self._chart_frame = ctk.CTkFrame(scroll, fg_color=COLORS["bg_card"],
                                          corner_radius=12, height=260)
        self._chart_frame.pack(fill="x", pady=(0, 20))
        self._chart_frame.pack_propagate(False)

        # Placeholder label until chart is drawn
        self._chart_placeholder = ctk.CTkLabel(
            self._chart_frame,
            text="Analyze some articles to see the distribution chart.",
            font=FONTS["body"],
            text_color=COLORS["text_muted"]
        )
        self._chart_placeholder.pack(expand=True)

        # ── Recent Articles ────────────────────────────────────────
        ctk.CTkLabel(scroll, text="🕐 Recent Articles",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(0, 8))

        self._recent_frame = ctk.CTkFrame(scroll, fg_color=COLORS["bg_card"], corner_radius=12)
        self._recent_frame.pack(fill="x", pady=(0, 20))

        # Disclaimer
        disclaimer_frame = ctk.CTkFrame(scroll, fg_color="#1c1008", corner_radius=8)
        disclaimer_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(disclaimer_frame,
                     text="⚠️  All statistics are based on articles analyzed using the DEMO dataset model. "
                          "Results are system assessments only and not verified ground truth.",
                     font=FONTS["tiny"],
                     text_color="#f59e0b",
                     wraplength=900).pack(padx=16, pady=10)

    def refresh(self):
        """Refresh all dashboard data from the database."""
        # Get stats
        stats = database.get_dashboard_stats()
        graph_manager = get_graph_manager()
        graph_stats = graph_manager.get_graph_stats()

        # Update article stat cards
        self._stat_cards["total"].update_value(str(stats.get("total", 0)))
        self._stat_cards["real"].update_value(str(stats.get("real", 0)))
        self._stat_cards["fake"].update_value(str(stats.get("fake", 0)))
        self._stat_cards["suspicious"].update_value(str(stats.get("suspicious", 0)))
        self._stat_cards["duplicates"].update_value(str(stats.get("duplicates", 0)))

        # Update graph stat cards
        self._stat_cards["nodes"].update_value(str(graph_stats.get("nodes", 0)))
        self._stat_cards["edges"].update_value(str(graph_stats.get("edges", 0)))
        self._stat_cards["relationships"].update_value(str(stats.get("relationships", 0)))
        self._stat_cards["clusters"].update_value(str(graph_stats.get("components", 0)))

        # Update chart
        self._draw_chart(stats)

        # Update recent articles
        self._show_recent_articles()

    def _draw_chart(self, stats: dict):
        """Draw a bar chart using matplotlib embedded in the frame."""
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

            # Clear existing chart
            for widget in self._chart_frame.winfo_children():
                widget.destroy()

            real = stats.get("real", 0)
            fake = stats.get("fake", 0)
            suspicious = stats.get("suspicious", 0)
            total = real + fake + suspicious

            if total == 0:
                ctk.CTkLabel(self._chart_frame,
                             text="No data yet. Analyze articles to see the chart.",
                             font=FONTS["body"],
                             text_color=COLORS["text_muted"]).pack(expand=True)
                return

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 2.5))
            fig.patch.set_facecolor("#16213e")

            # Bar chart
            categories = ["Real", "Fake", "Suspicious"]
            values = [real, fake, suspicious]
            colors_bar = [COLORS["real"], COLORS["fake"], COLORS["suspicious"]]

            bars = ax1.bar(categories, values, color=colors_bar, edgecolor="none",
                           width=0.5)
            ax1.set_facecolor("#16213e")
            ax1.tick_params(colors="#94a3b8")
            ax1.spines[:].set_color("#1e293b")
            ax1.set_title("Prediction Distribution", color="#f1f5f9", fontsize=10)
            ax1.set_ylabel("Count", color="#94a3b8", fontsize=9)

            for bar, val in zip(bars, values):
                if val > 0:
                    ax1.text(bar.get_x() + bar.get_width() / 2.0, bar.get_height() + 0.1,
                             str(val), ha='center', va='bottom', color="#f1f5f9", fontsize=9)

            # Pie chart
            if total > 0:
                pie_data = [(v, c, l) for v, c, l in
                            zip(values, colors_bar, categories) if v > 0]
                pie_vals = [x[0] for x in pie_data]
                pie_cols = [x[1] for x in pie_data]
                pie_labels = [x[2] for x in pie_data]

                wedges, texts, autotexts = ax2.pie(
                    pie_vals, labels=pie_labels, colors=pie_cols,
                    autopct='%1.0f%%', startangle=90,
                    textprops={'color': '#94a3b8', 'fontsize': 9}
                )
                for at in autotexts:
                    at.set_color('#f1f5f9')
                    at.set_fontsize(8)
                ax2.set_facecolor("#16213e")
                ax2.set_title("Article Breakdown", color="#f1f5f9", fontsize=10)

            plt.tight_layout(pad=1.2)
            canvas = FigureCanvasTkAgg(fig, master=self._chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)
            plt.close(fig)

        except ImportError:
            ctk.CTkLabel(self._chart_frame,
                         text="Install matplotlib to see charts.",
                         font=FONTS["body"],
                         text_color=COLORS["text_muted"]).pack(expand=True)
        except Exception as e:
            ctk.CTkLabel(self._chart_frame,
                         text=f"Chart error: {str(e)[:80]}",
                         font=FONTS["tiny"],
                         text_color=COLORS["text_muted"]).pack(expand=True)

    def _show_recent_articles(self):
        """Show the 5 most recently analyzed articles."""
        for widget in self._recent_frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self._recent_frame, text="Recent Articles",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", padx=16, pady=(12, 8))

        articles = database.get_all_articles()[:5]  # Only last 5

        if not articles:
            ctk.CTkLabel(self._recent_frame,
                         text="No articles analyzed yet. Go to 'Analyze News' to get started.",
                         font=FONTS["body"],
                         text_color=COLORS["text_muted"]).pack(pady=20)
            return

        from utils.helpers import format_timestamp, prediction_color
        for article in articles:
            row = ctk.CTkFrame(self._recent_frame, fg_color=COLORS["bg_secondary"],
                               corner_radius=6)
            row.pack(fill="x", padx=12, pady=3)

            pred = article.get("prediction", "UNKNOWN")
            color = prediction_color(pred)

            left = ctk.CTkFrame(row, fg_color=color, width=4, corner_radius=2)
            left.pack(side="left", fill="y")

            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="both", expand=True, padx=10, pady=8)

            from utils.helpers import truncate_text
            ctk.CTkLabel(info,
                         text=truncate_text(article.get("headline", ""), 80),
                         font=FONTS["small"],
                         text_color=COLORS["text_primary"],
                         anchor="w").pack(anchor="w")
            ctk.CTkLabel(info,
                         text=f"{article.get('source', 'Unknown')} · {format_timestamp(article.get('timestamp'))}",
                         font=FONTS["tiny"],
                         text_color=COLORS["text_muted"],
                         anchor="w").pack(anchor="w")

            # Badge
            ctk.CTkLabel(row, text=f"  {pred}  ",
                         font=FONTS["tiny"],
                         text_color="white",
                         fg_color=color,
                         corner_radius=4).pack(side="right", padx=10)
