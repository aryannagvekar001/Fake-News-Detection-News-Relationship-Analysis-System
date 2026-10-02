"""
utils/helpers.py
Utility functions shared across the application.
"""

import os
import sys
from datetime import datetime
from typing import Optional


def resource_path(relative_path: str) -> str:
    """Get the absolute path to a resource (works in dev and packaged mode)."""
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, relative_path)


def format_timestamp(ts: Optional[str]) -> str:
    """Format an ISO timestamp string for display."""
    if not ts:
        return "N/A"
    try:
        dt = datetime.fromisoformat(ts)
        return dt.strftime("%d %b %Y, %I:%M %p")
    except Exception:
        return ts


def format_percentage(value: float) -> str:
    """Format a float as a percentage string."""
    return f"{value:.1f}%"


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to a maximum length with ellipsis."""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def prediction_color(prediction: str) -> str:
    """Return the hex color for a prediction label."""
    colors = {
        "REAL": "#22c55e",
        "FAKE": "#ef4444",
        "SUSPICIOUS": "#f59e0b",
        "UNKNOWN": "#6b7280"
    }
    return colors.get(prediction, "#6b7280")


def relationship_color(rel_type: str) -> str:
    """Return the hex color for a relationship type."""
    colors = {
        "DUPLICATE": "#ef4444",
        "SIMILAR_CONTENT": "#f59e0b",
        "SAME_TOPIC": "#06b6d4",
        "SAME_SOURCE": "#8b5cf6",
        "RELATED_KEYWORDS": "#22c55e"
    }
    return colors.get(rel_type, "#6b7280")


def get_confidence_label(confidence: float) -> str:
    """Return a human-readable label for a confidence value (0-1 scale or 0-100 scale)."""
    if confidence > 1.0:
        confidence /= 100.0
    if confidence >= 0.85:
        return "Very High"
    elif confidence >= 0.70:
        return "High"
    elif confidence >= 0.55:
        return "Medium"
    elif confidence >= 0.40:
        return "Low"
    else:
        return "Very Low"


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division that returns a default value if denominator is zero."""
    if denominator == 0:
        return default
    return numerator / denominator
