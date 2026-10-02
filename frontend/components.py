"""
frontend/components.py
Reusable UI components for the Fake News Intelligence application.
Built with CustomTkinter for a modern dark-themed interface.
"""

import tkinter as tk
import customtkinter as ctk
from utils.helpers import prediction_color, relationship_color, truncate_text

# ─────────────────────────────────────────────
# THEME / COLOR CONSTANTS
# ─────────────────────────────────────────────
COLORS = {
    "bg_primary": "#0f0f1a",
    "bg_secondary": "#1a1a2e",
    "bg_card": "#16213e",
    "bg_input": "#0d1117",
    "accent_purple": "#7c3aed",
    "accent_cyan": "#06b6d4",
    "accent_purple_light": "#a78bfa",
    "text_primary": "#f1f5f9",
    "text_secondary": "#94a3b8",
    "text_muted": "#64748b",
    "border": "#1e293b",
    "real": "#22c55e",
    "fake": "#ef4444",
    "suspicious": "#f59e0b",
    "unknown": "#6b7280",
    "success": "#10b981",
    "warning": "#f59e0b",
    "error": "#ef4444",
    "info": "#06b6d4",
}

FONTS = {
    "title": ("Segoe UI", 22, "bold"),
    "subtitle": ("Segoe UI", 14),
    "heading": ("Segoe UI", 16, "bold"),
    "subheading": ("Segoe UI", 13, "bold"),
    "body": ("Segoe UI", 12),
    "small": ("Segoe UI", 11),
    "tiny": ("Segoe UI", 10),
    "mono": ("Courier New", 11),
    "mono_small": ("Courier New", 10),
}


def configure_ctk_theme():
    """Apply the dark theme to CustomTkinter."""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")


# ─────────────────────────────────────────────
# STAT CARD
# ─────────────────────────────────────────────
class StatCard(ctk.CTkFrame):
    """
    A card widget that displays a single statistic with icon, label, and value.
    Used on the Dashboard page.
    """
    def __init__(self, parent, title: str, value: str, icon: str = "📊",
                 color: str = None, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_card"],
                        corner_radius=12, **kwargs)
        self._color = color or COLORS["accent_cyan"]
        self._value_var = tk.StringVar(value=value)

        # Colored top border indicator
        indicator = ctk.CTkFrame(self, fg_color=self._color, height=4, corner_radius=2)
        indicator.pack(fill="x", padx=0, pady=(0, 0))

        # Content frame
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=16, pady=12)

        # Icon + Title row
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x")
        ctk.CTkLabel(header, text=icon, font=("Segoe UI Emoji", 20)).pack(side="left")
        ctk.CTkLabel(header, text=title, font=FONTS["small"],
                     text_color=COLORS["text_secondary"]).pack(side="left", padx=(8, 0))

        # Value
        ctk.CTkLabel(content, textvariable=self._value_var,
                     font=("Segoe UI", 28, "bold"),
                     text_color=self._color).pack(anchor="w", pady=(4, 0))

    def update_value(self, new_value: str):
        """Update the displayed value."""
        self._value_var.set(new_value)


# ─────────────────────────────────────────────
# PREDICTION BADGE
# ─────────────────────────────────────────────
class PredictionBadge(ctk.CTkLabel):
    """
    A colored label badge showing REAL / FAKE / SUSPICIOUS.
    """
    def __init__(self, parent, prediction: str = "UNKNOWN", **kwargs):
        color = prediction_color(prediction)
        super().__init__(
            parent,
            text=f"  {prediction}  ",
            font=("Segoe UI", 13, "bold"),
            text_color="white",
            fg_color=color,
            corner_radius=8,
            **kwargs
        )

    def update_prediction(self, prediction: str):
        color = prediction_color(prediction)
        self.configure(text=f"  {prediction}  ", fg_color=color)


# ─────────────────────────────────────────────
# CONFIDENCE BAR
# ─────────────────────────────────────────────
class ConfidenceBar(ctk.CTkFrame):
    """
    A progress bar widget showing confidence percentage.
    """
    def __init__(self, parent, value: float = 0.0, label: str = "Confidence",
                 color: str = None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._color = color or COLORS["accent_cyan"]

        # Label row
        label_frame = ctk.CTkFrame(self, fg_color="transparent")
        label_frame.pack(fill="x")
        ctk.CTkLabel(label_frame, text=label, font=FONTS["small"],
                     text_color=COLORS["text_secondary"]).pack(side="left")
        self._pct_label = ctk.CTkLabel(label_frame, text=f"{value:.1f}%",
                                        font=FONTS["small"],
                                        text_color=self._color)
        self._pct_label.pack(side="right")

        # Progress bar
        self._bar = ctk.CTkProgressBar(self, height=8, corner_radius=4,
                                        fg_color=COLORS["bg_secondary"],
                                        progress_color=self._color)
        self._bar.pack(fill="x", pady=(4, 0))
        self._bar.set(max(0.0, min(1.0, value / 100.0)))

    def update_value(self, value: float, color: str = None):
        if color:
            self._color = color
            self._bar.configure(progress_color=color)
            self._pct_label.configure(text_color=color)
        self._pct_label.configure(text=f"{value:.1f}%")
        self._bar.set(max(0.0, min(1.0, value / 100.0)))


# ─────────────────────────────────────────────
# SECTION HEADER
# ─────────────────────────────────────────────
class SectionHeader(ctk.CTkFrame):
    """A styled section header with optional accent line."""
    def __init__(self, parent, title: str, subtitle: str = "", icon: str = "", **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x")

        if icon:
            ctk.CTkLabel(row, text=icon, font=("Segoe UI Emoji", 18)).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(row, text=title, font=FONTS["heading"],
                     text_color=COLORS["text_primary"]).pack(side="left")

        if subtitle:
            ctk.CTkLabel(self, text=subtitle, font=FONTS["small"],
                         text_color=COLORS["text_muted"]).pack(anchor="w", pady=(2, 0))

        # Accent line
        line = ctk.CTkFrame(self, fg_color=COLORS["accent_purple"], height=2, corner_radius=1)
        line.pack(fill="x", pady=(6, 0))


# ─────────────────────────────────────────────
# ARTICLE LIST ITEM
# ─────────────────────────────────────────────
class ArticleListItem(ctk.CTkFrame):
    """A clickable list item for displaying an article in history/search results."""
    def __init__(self, parent, article: dict, on_click=None, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_card"], corner_radius=8,
                        cursor="hand2", **kwargs)
        self._article = article
        self._on_click = on_click

        # Left colored indicator
        pred = article.get("prediction", "UNKNOWN")
        color = prediction_color(pred)
        indicator = ctk.CTkFrame(self, fg_color=color, width=4, corner_radius=2)
        indicator.pack(side="left", fill="y", padx=(0, 10))

        # Content
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, pady=10, padx=(0, 10))

        # Headline
        headline = truncate_text(article.get("headline", "Unknown"), 90)
        ctk.CTkLabel(content, text=headline, font=FONTS["body"],
                     text_color=COLORS["text_primary"],
                     anchor="w", wraplength=500).pack(anchor="w")

        # Meta row
        meta = ctk.CTkFrame(content, fg_color="transparent")
        meta.pack(anchor="w", fill="x")

        source = article.get("source", "Unknown")
        ctk.CTkLabel(meta, text=f"📰 {source}", font=FONTS["tiny"],
                     text_color=COLORS["text_muted"]).pack(side="left")
        ctk.CTkLabel(meta, text=" · ", font=FONTS["tiny"],
                     text_color=COLORS["text_muted"]).pack(side="left")

        from utils.helpers import format_timestamp
        ts = format_timestamp(article.get("timestamp"))
        ctk.CTkLabel(meta, text=f"🕐 {ts}", font=FONTS["tiny"],
                     text_color=COLORS["text_muted"]).pack(side="left")

        if article.get("is_duplicate"):
            ctk.CTkLabel(meta, text=" · 🔗 DUPLICATE", font=FONTS["tiny"],
                         text_color=COLORS["suspicious"]).pack(side="left")

        # Right badge
        badge_frame = ctk.CTkFrame(self, fg_color="transparent")
        badge_frame.pack(side="right", padx=10)

        ctk.CTkLabel(badge_frame, text=f"  {pred}  ",
                     font=FONTS["tiny"],
                     text_color="white",
                     fg_color=color,
                     corner_radius=6).pack()

        conf = article.get("confidence", 0)
        if conf <= 1.0:
            conf *= 100
        ctk.CTkLabel(badge_frame, text=f"{conf:.0f}%",
                     font=FONTS["tiny"],
                     text_color=COLORS["text_muted"]).pack(pady=(2, 0))

        # Bind click events
        self.bind("<Button-1>", self._click)
        for widget in self.winfo_children():
            self._bind_recursive(widget)

    def _bind_recursive(self, widget):
        widget.bind("<Button-1>", self._click)
        for child in widget.winfo_children():
            self._bind_recursive(child)

    def _click(self, event=None):
        if self._on_click:
            self._on_click(self._article)


# ─────────────────────────────────────────────
# SCROLLABLE ARTICLE LIST
# ─────────────────────────────────────────────
class ScrollableArticleList(ctk.CTkScrollableFrame):
    """A scrollable list of ArticleListItems."""
    def __init__(self, parent, on_select=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._on_select = on_select
        self._items = []

    def load_articles(self, articles: list):
        """Clear and reload the article list."""
        for widget in self.winfo_children():
            widget.destroy()
        self._items = []

        if not articles:
            ctk.CTkLabel(self, text="No articles found.",
                         font=FONTS["body"],
                         text_color=COLORS["text_muted"]).pack(pady=40)
            return

        for article in articles:
            item = ArticleListItem(self, article, on_click=self._on_select)
            item.pack(fill="x", pady=3, padx=4)
            self._items.append(item)


# ─────────────────────────────────────────────
# INFO ROW
# ─────────────────────────────────────────────
class InfoRow(ctk.CTkFrame):
    """A key-value display row for article details."""
    def __init__(self, parent, label: str, value: str, value_color: str = None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        ctk.CTkLabel(self, text=label + ":", font=FONTS["small"],
                     text_color=COLORS["text_muted"], width=140,
                     anchor="w").pack(side="left")
        ctk.CTkLabel(self, text=value, font=FONTS["small"],
                     text_color=value_color or COLORS["text_primary"],
                     anchor="w", wraplength=400).pack(side="left", padx=(8, 0))


# ─────────────────────────────────────────────
# KEYWORD TAG
# ─────────────────────────────────────────────
class KeywordTag(ctk.CTkLabel):
    """A small tag label for displaying keywords."""
    def __init__(self, parent, keyword: str, **kwargs):
        super().__init__(
            parent,
            text=f" {keyword} ",
            font=FONTS["tiny"],
            text_color=COLORS["accent_cyan"],
            fg_color=COLORS["bg_secondary"],
            corner_radius=4,
            **kwargs
        )


# ─────────────────────────────────────────────
# LOADING SPINNER
# ─────────────────────────────────────────────
class LoadingSpinner(ctk.CTkLabel):
    """A simple animated loading indicator."""
    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, parent, **kwargs):
        super().__init__(parent, text="⠋", font=("Segoe UI", 18),
                         text_color=COLORS["accent_purple"], **kwargs)
        self._frame = 0
        self._running = False

    def start(self):
        self._running = True
        self._animate()

    def stop(self):
        self._running = False
        self.configure(text="")

    def _animate(self):
        if self._running:
            self.configure(text=self.FRAMES[self._frame % len(self.FRAMES)])
            self._frame += 1
            self.after(80, self._animate)


# ─────────────────────────────────────────────
# TOAST NOTIFICATION
# ─────────────────────────────────────────────
def show_toast(parent_window, message: str, color: str = None, duration: int = 3000):
    """Show a temporary toast notification at the bottom of the window."""
    color = color or COLORS["accent_cyan"]
    toast = ctk.CTkToplevel(parent_window)
    toast.overrideredirect(True)
    toast.attributes("-topmost", True)
    toast.configure(fg_color=COLORS["bg_card"])

    frame = ctk.CTkFrame(toast, fg_color=color, corner_radius=8)
    frame.pack(fill="both", expand=True, padx=2, pady=2)

    ctk.CTkLabel(frame, text=message, font=FONTS["small"],
                 text_color="white", wraplength=350).pack(padx=16, pady=10)

    # Position near bottom center of parent
    parent_window.update_idletasks()
    px = parent_window.winfo_x() + parent_window.winfo_width() // 2 - 175
    py = parent_window.winfo_y() + parent_window.winfo_height() - 80
    toast.geometry(f"350x50+{px}+{py}")

    toast.after(duration, toast.destroy)


# ─────────────────────────────────────────────
# RELATIONSHIP TAG
# ─────────────────────────────────────────────
class RelationshipTag(ctk.CTkLabel):
    """A colored tag for relationship types."""
    def __init__(self, parent, rel_type: str, **kwargs):
        color = relationship_color(rel_type)
        super().__init__(
            parent,
            text=f" {rel_type.replace('_', ' ')} ",
            font=FONTS["tiny"],
            text_color="white",
            fg_color=color,
            corner_radius=4,
            **kwargs
        )
