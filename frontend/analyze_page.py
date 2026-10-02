"""
frontend/analyze_page.py
Analyze News page — the core user-facing feature.
Allows users to submit an article for full analysis.
"""

import tkinter as tk
import customtkinter as ctk
import threading
from frontend.components import (
    COLORS, FONTS, PredictionBadge, ConfidenceBar,
    LoadingSpinner, show_toast, KeywordTag
)
from backend.news_analyzer import analyze_article
from utils.helpers import format_timestamp, truncate_text, prediction_color, relationship_color


class AnalyzePage(ctk.CTkFrame):
    """
    News analysis submission and results page.

    Features:
    - Article input form (headline, content, source, date)
    - Real-time analysis on submit
    - Results panel with prediction, confidence, keywords, related articles
    - Explainability section
    """

    def __init__(self, parent, on_analysis_complete=None, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_primary"], **kwargs)
        self._on_analysis_complete = on_analysis_complete
        self._last_result = None
        self._build_ui()

    def _build_ui(self):
        # Main horizontal split
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # ── LEFT PANEL: Input Form ────────────────────────────────
        left_scroll = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg_primary"],
                                              width=500)
        left_scroll.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=20)

        # Header
        header = ctk.CTkFrame(left_scroll, fg_color=COLORS["bg_secondary"], corner_radius=12)
        header.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(header, text="🔍 Analyze News Article",
                     font=FONTS["heading"],
                     text_color=COLORS["text_primary"]).pack(anchor="w", padx=16, pady=(12, 4))
        ctk.CTkLabel(header, text="Enter a news article below and click Analyze to get an assessment.",
                     font=FONTS["small"],
                     text_color=COLORS["text_muted"]).pack(anchor="w", padx=16, pady=(0, 12))

        # Headline field
        ctk.CTkLabel(left_scroll, text="📰 Headline *",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(0, 4))
        self._headline_var = tk.StringVar()
        self._headline_entry = ctk.CTkEntry(
            left_scroll,
            textvariable=self._headline_var,
            placeholder_text="Enter the news headline...",
            font=FONTS["body"],
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            height=40
        )
        self._headline_entry.pack(fill="x", pady=(0, 12))

        # Content field
        ctk.CTkLabel(left_scroll, text="📄 Article Content *",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(0, 4))
        self._content_text = ctk.CTkTextbox(
            left_scroll,
            font=FONTS["body"],
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            height=200,
            wrap="word"
        )
        self._content_text.pack(fill="x", pady=(0, 12))
        self._content_text.insert("1.0", "")

        # Source and Date row
        meta_frame = ctk.CTkFrame(left_scroll, fg_color="transparent")
        meta_frame.pack(fill="x", pady=(0, 12))
        meta_frame.columnconfigure([0, 1], weight=1)

        ctk.CTkLabel(meta_frame, text="📡 Source / Publisher",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(meta_frame, text="📅 Publication Date (optional)",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).grid(row=0, column=1, sticky="w", padx=(12, 0))

        self._source_var = tk.StringVar()
        ctk.CTkEntry(meta_frame, textvariable=self._source_var,
                     placeholder_text="e.g., BBC News",
                     font=FONTS["body"],
                     fg_color=COLORS["bg_input"],
                     border_color=COLORS["border"],
                     text_color=COLORS["text_primary"],
                     height=36).grid(row=1, column=0, sticky="ew", pady=(4, 0))

        self._date_var = tk.StringVar()
        ctk.CTkEntry(meta_frame, textvariable=self._date_var,
                     placeholder_text="e.g., 2024-01-15",
                     font=FONTS["body"],
                     fg_color=COLORS["bg_input"],
                     border_color=COLORS["border"],
                     text_color=COLORS["text_primary"],
                     height=36).grid(row=1, column=1, sticky="ew", padx=(12, 0), pady=(4, 0))

        # Quick Demo Buttons
        demo_frame = ctk.CTkFrame(left_scroll, fg_color=COLORS["bg_card"], corner_radius=8)
        demo_frame.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(demo_frame, text="💡 Load Demo Article:",
                     font=FONTS["small"],
                     text_color=COLORS["text_muted"]).pack(side="left", padx=12, pady=8)
        ctk.CTkButton(demo_frame, text="📰 Real News",
                      font=FONTS["tiny"],
                      fg_color=COLORS["real"],
                      hover_color="#16a34a",
                      height=28,
                      command=lambda: self._load_demo("real")).pack(side="left", padx=4, pady=8)
        ctk.CTkButton(demo_frame, text="🚫 Fake News",
                      font=FONTS["tiny"],
                      fg_color=COLORS["fake"],
                      hover_color="#dc2626",
                      height=28,
                      command=lambda: self._load_demo("fake")).pack(side="left", padx=4, pady=8)
        ctk.CTkButton(demo_frame, text="🔗 Duplicate",
                      font=FONTS["tiny"],
                      fg_color="#8b5cf6",
                      hover_color="#7c3aed",
                      height=28,
                      command=lambda: self._load_demo("duplicate")).pack(side="left", padx=4, pady=8)

        # Action buttons
        btn_frame = ctk.CTkFrame(left_scroll, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(4, 0))

        self._analyze_btn = ctk.CTkButton(
            btn_frame,
            text="🔍  Analyze News Article",
            font=("Segoe UI", 13, "bold"),
            fg_color=COLORS["accent_purple"],
            hover_color="#6d28d9",
            height=44,
            corner_radius=10,
            command=self._start_analysis
        )
        self._analyze_btn.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            btn_frame,
            text="🗑 Clear",
            font=FONTS["small"],
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["bg_secondary"],
            height=44,
            width=80,
            corner_radius=10,
            command=self._clear_form
        ).pack(side="left", padx=(8, 0))

        # Status / spinner
        self._status_frame = ctk.CTkFrame(left_scroll, fg_color="transparent")
        self._status_frame.pack(fill="x", pady=(8, 0))
        self._spinner = LoadingSpinner(self._status_frame)
        self._spinner.pack(side="left")
        self._status_label = ctk.CTkLabel(self._status_frame, text="",
                                           font=FONTS["small"],
                                           text_color=COLORS["text_muted"])
        self._status_label.pack(side="left", padx=(8, 0))

        # Error label
        self._error_label = ctk.CTkLabel(left_scroll, text="",
                                          font=FONTS["small"],
                                          text_color=COLORS["fake"])
        self._error_label.pack(anchor="w", pady=(4, 0))

        # ── RIGHT PANEL: Results ──────────────────────────────────
        right_scroll = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg_primary"])
        right_scroll.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=20)

        # Empty state
        self._empty_state = ctk.CTkFrame(right_scroll, fg_color=COLORS["bg_card"],
                                          corner_radius=16)
        self._empty_state.pack(fill="both", expand=True, pady=40)
        ctk.CTkLabel(self._empty_state, text="🔍",
                     font=("Segoe UI Emoji", 48)).pack(pady=(40, 8))
        ctk.CTkLabel(self._empty_state,
                     text="Submit an article to see the analysis results here.",
                     font=FONTS["body"],
                     text_color=COLORS["text_muted"],
                     wraplength=300).pack()

        # Results panel (hidden until analysis)
        self._results_frame = ctk.CTkFrame(right_scroll, fg_color="transparent")
        self._right_scroll = right_scroll

    def _load_demo(self, demo_type: str):
        """Load a demo article into the form fields."""
        demos = {
            "real": {
                "headline": "Scientists confirm climate change accelerating faster than predicted",
                "content": "A comprehensive new study published in Nature Climate Journal has found that global temperatures are rising at a rate significantly faster than models predicted just five years ago. Researchers from 15 countries analyzed over 50 years of temperature data. The study found that ocean temperatures have increased by 0.4 degrees Celsius over the past decade, contributing to more frequent extreme weather events. The lead researcher Dr. Sarah Chen emphasized that immediate action on carbon emissions is critical to preventing irreversible damage to ecosystems.",
                "source": "Science Daily",
                "date": "2024-01-15"
            },
            "fake": {
                "headline": "SHOCKING: Government secretly adding mind control chemicals to tap water",
                "content": "EXCLUSIVE REPORT: Multiple insider sources have confirmed that the government has been secretly adding mind control chemicals to the public water supply for the past 20 years. The chemicals, developed by a shadowy organization of billionaires, are designed to make citizens more obedient and less likely to question authority. A brave whistleblower has come forward with documents proving this conspiracy. The mainstream media is trying to suppress this information. Share this article before it gets deleted! The deep state cannot hide the truth much longer. Wake up people!",
                "source": "TruthBombs247",
                "date": "2024-01-15"
            },
            "duplicate": {
                "headline": "Scientists confirm climate change accelerating faster than predicted",
                "content": "A comprehensive new study published in Nature Climate Journal has found that global temperatures are rising at a rate significantly faster than models predicted just five years ago. Researchers from 15 countries analyzed over 50 years of temperature data. The study found that ocean temperatures have increased by 0.4 degrees Celsius over the past decade, contributing to more frequent extreme weather events. The lead researcher Dr. Sarah Chen emphasized that immediate action on carbon emissions is critical to preventing irreversible damage to ecosystems.",
                "source": "News Mirror",
                "date": "2024-01-16"
            }
        }

        demo = demos.get(demo_type, {})
        self._headline_var.set(demo.get("headline", ""))
        self._content_text.delete("1.0", "end")
        self._content_text.insert("1.0", demo.get("content", ""))
        self._source_var.set(demo.get("source", ""))
        self._date_var.set(demo.get("date", ""))
        self._error_label.configure(text="")

    def _clear_form(self):
        """Clear all form fields."""
        self._headline_var.set("")
        self._content_text.delete("1.0", "end")
        self._source_var.set("")
        self._date_var.set("")
        self._error_label.configure(text="")
        self._status_label.configure(text="")

    def _start_analysis(self):
        """Validate inputs and start analysis in a background thread."""
        headline = self._headline_var.get().strip()
        content = self._content_text.get("1.0", "end").strip()
        source = self._source_var.get().strip() or "Unknown"
        pub_date = self._date_var.get().strip()

        # Validation
        if not headline:
            self._error_label.configure(text="⚠️ Please enter a headline.")
            return
        if not content:
            self._error_label.configure(text="⚠️ Please enter article content.")
            return
        if len(content) < 20:
            self._error_label.configure(text="⚠️ Article content is too short (minimum 20 characters).")
            return

        self._error_label.configure(text="")
        self._analyze_btn.configure(state="disabled", text="Analyzing...")
        self._spinner.start()
        self._status_label.configure(text="Running analysis pipeline...")

        # Run in background thread to keep UI responsive
        def run():
            result = analyze_article(headline, content, source, pub_date)
            self.after(0, lambda: self._on_analysis_done(result))

        threading.Thread(target=run, daemon=True).start()

    def _on_analysis_done(self, result: dict):
        """Called on the main thread after analysis completes."""
        self._spinner.stop()
        self._analyze_btn.configure(state="normal", text="🔍  Analyze News Article")
        self._status_label.configure(text="")

        if not result.get("success"):
            self._error_label.configure(text=f"⚠️ {result.get('error', 'Analysis failed.')}")
            return

        self._last_result = result
        self._show_results(result)

        if self._on_analysis_complete:
            self._on_analysis_complete(result)

        show_toast(self.winfo_toplevel(),
                   f"✅ Analysis complete: {result.get('prediction')} ({result.get('confidence')}% confidence)",
                   color=COLORS["accent_purple"])

    def _show_results(self, result: dict):
        """Render the analysis results in the right panel."""
        # Clear previous results
        for widget in self._results_frame.winfo_children():
            widget.destroy()

        # Hide empty state
        self._empty_state.pack_forget()
        self._results_frame.pack(fill="both", expand=True)

        # ── Prediction Banner ─────────────────────────────────────
        pred = result.get("prediction", "UNKNOWN")
        pred_color = prediction_color(pred)
        conf = result.get("confidence", 0.0)

        banner = ctk.CTkFrame(self._results_frame, fg_color=pred_color,
                               corner_radius=12)
        banner.pack(fill="x", pady=(0, 12))

        pred_icons = {"REAL": "✅", "FAKE": "❌", "SUSPICIOUS": "⚠️", "UNKNOWN": "❓"}
        icon = pred_icons.get(pred, "❓")

        banner_inner = ctk.CTkFrame(banner, fg_color="transparent")
        banner_inner.pack(padx=20, pady=16)

        ctk.CTkLabel(banner_inner, text=f"{icon}  System Assessment: {pred}",
                     font=("Segoe UI", 18, "bold"),
                     text_color="white").pack(anchor="w")
        ctk.CTkLabel(banner_inner, text=f"Confidence: {conf:.1f}%  |  Credibility Score: {result.get('credibility_score', 0):.1f}/100",
                     font=FONTS["small"],
                     text_color="#e2e8f0").pack(anchor="w", pady=(4, 0))
        ctk.CTkLabel(banner_inner,
                     text="⚠️ System assessment only. Not a verified truth indicator.",
                     font=FONTS["tiny"],
                     text_color="white").pack(anchor="w", pady=(4, 0))

        # ── Confidence Bars ───────────────────────────────────────
        conf_frame = ctk.CTkFrame(self._results_frame, fg_color=COLORS["bg_card"],
                                   corner_radius=10)
        conf_frame.pack(fill="x", pady=(0, 12))
        conf_inner = ctk.CTkFrame(conf_frame, fg_color="transparent")
        conf_inner.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(conf_inner, text="Model Confidence Breakdown",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(0, 8))

        ConfidenceBar(conf_inner, value=result.get("real_probability", 0),
                      label="Real Probability", color=COLORS["real"]).pack(fill="x", pady=3)
        ConfidenceBar(conf_inner, value=result.get("fake_probability", 0),
                      label="Fake Probability", color=COLORS["fake"]).pack(fill="x", pady=3)
        ConfidenceBar(conf_inner, value=result.get("credibility_score", 0),
                      label="Credibility Score", color=COLORS["accent_cyan"]).pack(fill="x", pady=3)

        # ── Article Info ──────────────────────────────────────────
        info_frame = ctk.CTkFrame(self._results_frame, fg_color=COLORS["bg_card"],
                                   corner_radius=10)
        info_frame.pack(fill="x", pady=(0, 12))
        info_inner = ctk.CTkFrame(info_frame, fg_color="transparent")
        info_inner.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(info_inner, text="📋 Article Information",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(0, 8))

        from frontend.components import InfoRow
        from utils.helpers import format_timestamp
        InfoRow(info_inner, "Article ID", result.get("article_id", "")).pack(fill="x", pady=2)
        InfoRow(info_inner, "Source", result.get("source", "Unknown")).pack(fill="x", pady=2)
        InfoRow(info_inner, "Topic", result.get("topic", "General")).pack(fill="x", pady=2)
        InfoRow(info_inner, "Word Count", str(result.get("word_count", 0))).pack(fill="x", pady=2)
        InfoRow(info_inner, "Analyzed At", format_timestamp(result.get("timestamp"))).pack(fill="x", pady=2)

        # ── Duplicate Status ──────────────────────────────────────
        dup_color = COLORS["fake"] if result.get("is_duplicate") else COLORS["real"]
        dup_text = f"YES — Similar to {result.get('duplicate_of', '')} ({result.get('similarity_score', 0):.1f}% similar)" \
            if result.get("is_duplicate") else "NO"
        InfoRow(info_inner, "Duplicate", dup_text, value_color=dup_color).pack(fill="x", pady=2)

        # ── Keywords ──────────────────────────────────────────────
        kw_frame = ctk.CTkFrame(self._results_frame, fg_color=COLORS["bg_card"],
                                 corner_radius=10)
        kw_frame.pack(fill="x", pady=(0, 12))
        kw_inner = ctk.CTkFrame(kw_frame, fg_color="transparent")
        kw_inner.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(kw_inner, text="🏷️ Extracted Keywords",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(0, 8))

        kw_tags_frame = ctk.CTkFrame(kw_inner, fg_color="transparent")
        kw_tags_frame.pack(anchor="w")
        keywords = result.get("keywords", [])
        for kw in keywords[:12]:
            KeywordTag(kw_tags_frame, kw).pack(side="left", padx=3, pady=3)

        # ── Explainability ────────────────────────────────────────
        exp_frame = ctk.CTkFrame(self._results_frame, fg_color=COLORS["bg_card"],
                                  corner_radius=10)
        exp_frame.pack(fill="x", pady=(0, 12))
        exp_inner = ctk.CTkFrame(exp_frame, fg_color="transparent")
        exp_inner.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(exp_inner, text="💡 Why This Assessment?",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(0, 8))

        for factor in result.get("explanation", []):
            frow = ctk.CTkFrame(exp_inner, fg_color=COLORS["bg_secondary"],
                                corner_radius=6)
            frow.pack(fill="x", pady=3)
            level = factor.get("level", "info")
            level_colors = {
                "High": COLORS["real"], "Medium": COLORS["warning"],
                "Low": COLORS["fake"], "Very High": COLORS["real"],
                "positive": COLORS["real"], "negative": COLORS["fake"],
                "warning": COLORS["warning"], "info": COLORS["info"]
            }
            fc = level_colors.get(level, COLORS["text_muted"])

            fr = ctk.CTkFrame(frow, fg_color="transparent")
            fr.pack(fill="x", padx=12, pady=8)

            ctk.CTkLabel(fr, text=factor.get("factor", ""),
                         font=FONTS["small"],
                         text_color=COLORS["text_secondary"],
                         width=160, anchor="w").pack(side="left")
            ctk.CTkLabel(fr, text=factor.get("value", ""),
                         font=("Segoe UI", 12, "bold"),
                         text_color=fc).pack(side="left", padx=(8, 8))
            ctk.CTkLabel(fr, text=factor.get("description", ""),
                         font=FONTS["tiny"],
                         text_color=COLORS["text_muted"],
                         anchor="w", wraplength=300).pack(side="left")

        # ── Related Articles ──────────────────────────────────────
        related = result.get("related_articles", [])
        if related:
            rel_frame = ctk.CTkFrame(self._results_frame, fg_color=COLORS["bg_card"],
                                      corner_radius=10)
            rel_frame.pack(fill="x", pady=(0, 12))
            rel_inner = ctk.CTkFrame(rel_frame, fg_color="transparent")
            rel_inner.pack(fill="x", padx=16, pady=12)

            ctk.CTkLabel(rel_inner, text=f"🔗 Related Articles ({len(related)} found)",
                         font=FONTS["subheading"],
                         text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(0, 8))

            for rel in related:
                rrow = ctk.CTkFrame(rel_inner, fg_color=COLORS["bg_secondary"],
                                    corner_radius=6)
                rrow.pack(fill="x", pady=3)

                rel_color = relationship_color(rel.get("relationship", ""))
                ind = ctk.CTkFrame(rrow, fg_color=rel_color, width=4, corner_radius=2)
                ind.pack(side="left", fill="y")

                info = ctk.CTkFrame(rrow, fg_color="transparent")
                info.pack(side="left", fill="x", expand=True, padx=10, pady=8)

                ctk.CTkLabel(info, text=truncate_text(rel.get("headline", ""), 70),
                             font=FONTS["small"],
                             text_color=COLORS["text_primary"],
                             anchor="w").pack(anchor="w")
                ctk.CTkLabel(info,
                             text=f"{rel.get('source', 'Unknown')} · {rel.get('relationship', '').replace('_', ' ')} · {rel.get('similarity', 0):.1f}% similar",
                             font=FONTS["tiny"],
                             text_color=COLORS["text_muted"],
                             anchor="w").pack(anchor="w")

                pred_badge = rel.get("prediction", "UNKNOWN")
                ctk.CTkLabel(rrow, text=f"  {pred_badge}  ",
                             font=FONTS["tiny"],
                             text_color="white",
                             fg_color=prediction_color(pred_badge),
                             corner_radius=4).pack(side="right", padx=10)

        # ── Graph DSA Info ────────────────────────────────────────
        dsa_frame = ctk.CTkFrame(self._results_frame, fg_color=COLORS["bg_card"],
                                  corner_radius=10)
        dsa_frame.pack(fill="x", pady=(0, 12))
        dsa_inner = ctk.CTkFrame(dsa_frame, fg_color="transparent")
        dsa_inner.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(dsa_inner, text="🏗️ DSA Information",
                     font=FONTS["subheading"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(0, 8))

        hash_info = result.get("hash_info", {})
        from frontend.components import InfoRow
        InfoRow(dsa_inner, "Graph Node ID", result.get("graph_node_id", "")).pack(fill="x", pady=2)
        InfoRow(dsa_inner, "Graph Connections", str(result.get("graph_connections", 0))).pack(fill="x", pady=2)
        InfoRow(dsa_inner, "Short Hash (SHA-256)",
                hash_info.get("short_hash", "N/A")).pack(fill="x", pady=2)

        # Show normalized hash
        nh = hash_info.get("normalized_hash", "")
        ctk.CTkLabel(dsa_inner, text="Full SHA-256 Hash:",
                     font=FONTS["small"],
                     text_color=COLORS["text_muted"]).pack(anchor="w", pady=(8, 2))
        hash_box = ctk.CTkTextbox(dsa_inner, height=50, font=FONTS["mono_small"],
                                   fg_color=COLORS["bg_input"],
                                   text_color=COLORS["accent_cyan"])
        hash_box.pack(fill="x")
        hash_box.insert("1.0", nh)
        hash_box.configure(state="disabled")
