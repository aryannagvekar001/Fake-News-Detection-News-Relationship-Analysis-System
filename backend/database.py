"""
backend/database.py
SQLite database layer for the Fake News Intelligence system.
Handles all CRUD operations for articles, relationships, and sources.
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

# Database file location
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "news_database.db")


def get_connection():
    """Create and return a database connection."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enables column access by name
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_database():
    """Initialize the database schema. Creates tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # Articles table — main entity
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id TEXT UNIQUE NOT NULL,
            headline TEXT NOT NULL,
            content TEXT NOT NULL,
            source TEXT DEFAULT 'Unknown',
            pub_date TEXT,
            prediction TEXT,
            confidence REAL DEFAULT 0.0,
            credibility_score REAL DEFAULT 0.0,
            keywords TEXT,
            hash_headline TEXT,
            hash_content TEXT,
            hash_normalized TEXT,
            graph_node_id TEXT,
            is_duplicate INTEGER DEFAULT 0,
            duplicate_of TEXT,
            similarity_score REAL DEFAULT 0.0,
            topic TEXT DEFAULT 'General',
            timestamp TEXT,
            word_count INTEGER DEFAULT 0
        )
    """)

    # Relationships table — graph edges
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id_a TEXT NOT NULL,
            article_id_b TEXT NOT NULL,
            relationship_type TEXT NOT NULL,
            similarity_score REAL DEFAULT 0.0,
            created_at TEXT,
            FOREIGN KEY (article_id_a) REFERENCES articles(article_id),
            FOREIGN KEY (article_id_b) REFERENCES articles(article_id),
            UNIQUE(article_id_a, article_id_b, relationship_type)
        )
    """)

    # Sources table — publisher statistics
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_name TEXT UNIQUE NOT NULL,
            total_articles INTEGER DEFAULT 0,
            real_count INTEGER DEFAULT 0,
            fake_count INTEGER DEFAULT 0,
            suspicious_count INTEGER DEFAULT 0,
            duplicate_count INTEGER DEFAULT 0,
            first_seen TEXT,
            last_seen TEXT
        )
    """)

    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
# ARTICLE OPERATIONS
# ─────────────────────────────────────────────

def save_article(article_data: Dict[str, Any]) -> bool:
    """Save an analyzed article to the database."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO articles
            (article_id, headline, content, source, pub_date, prediction, confidence,
             credibility_score, keywords, hash_headline, hash_content, hash_normalized,
             graph_node_id, is_duplicate, duplicate_of, similarity_score, topic, timestamp, word_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            article_data.get("article_id"),
            article_data.get("headline"),
            article_data.get("content"),
            article_data.get("source", "Unknown"),
            article_data.get("pub_date"),
            article_data.get("prediction"),
            article_data.get("confidence", 0.0),
            article_data.get("credibility_score", 0.0),
            json.dumps(article_data.get("keywords", [])),
            article_data.get("hash_headline"),
            article_data.get("hash_content"),
            article_data.get("hash_normalized"),
            article_data.get("graph_node_id"),
            int(article_data.get("is_duplicate", False)),
            article_data.get("duplicate_of"),
            article_data.get("similarity_score", 0.0),
            article_data.get("topic", "General"),
            article_data.get("timestamp", datetime.now().isoformat()),
            article_data.get("word_count", 0)
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[DB ERROR] save_article: {e}")
        return False


def get_all_articles() -> List[Dict]:
    """Retrieve all articles from the database."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM articles ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        conn.close()
        result = []
        for row in rows:
            d = dict(row)
            d["keywords"] = json.loads(d.get("keywords") or "[]")
            result.append(d)
        return result
    except Exception as e:
        print(f"[DB ERROR] get_all_articles: {e}")
        return []


def get_article_by_id(article_id: str) -> Optional[Dict]:
    """Get a single article by its ID."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM articles WHERE article_id = ?", (article_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            d = dict(row)
            d["keywords"] = json.loads(d.get("keywords") or "[]")
            return d
        return None
    except Exception as e:
        print(f"[DB ERROR] get_article_by_id: {e}")
        return None


def get_article_by_hash(hash_normalized: str) -> Optional[Dict]:
    """Find an article with a matching normalized hash (duplicate detection)."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM articles WHERE hash_normalized = ?", (hash_normalized,))
        row = cursor.fetchone()
        conn.close()
        if row:
            d = dict(row)
            d["keywords"] = json.loads(d.get("keywords") or "[]")
            return d
        return None
    except Exception as e:
        print(f"[DB ERROR] get_article_by_hash: {e}")
        return None


def get_all_hashes() -> List[Dict]:
    """Return all article IDs with their normalized hashes for near-duplicate check."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT article_id, headline, hash_normalized, content FROM articles")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"[DB ERROR] get_all_hashes: {e}")
        return []


def delete_article(article_id: str) -> bool:
    """Delete an article and its relationships from the database."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM relationships WHERE article_id_a = ? OR article_id_b = ?",
                       (article_id, article_id))
        cursor.execute("DELETE FROM articles WHERE article_id = ?", (article_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[DB ERROR] delete_article: {e}")
        return False


def search_articles(query: str) -> List[Dict]:
    """Full-text search across headline, content, and source."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        pattern = f"%{query}%"
        cursor.execute("""
            SELECT * FROM articles
            WHERE headline LIKE ? OR content LIKE ? OR source LIKE ?
            ORDER BY timestamp DESC
        """, (pattern, pattern, pattern))
        rows = cursor.fetchall()
        conn.close()
        result = []
        for row in rows:
            d = dict(row)
            d["keywords"] = json.loads(d.get("keywords") or "[]")
            result.append(d)
        return result
    except Exception as e:
        print(f"[DB ERROR] search_articles: {e}")
        return []


# ─────────────────────────────────────────────
# RELATIONSHIP OPERATIONS
# ─────────────────────────────────────────────

def save_relationship(a_id: str, b_id: str, rel_type: str, score: float) -> bool:
    """Save a relationship (edge) between two articles."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO relationships
            (article_id_a, article_id_b, relationship_type, similarity_score, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (a_id, b_id, rel_type, score, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[DB ERROR] save_relationship: {e}")
        return False


def get_relationships_for_article(article_id: str) -> List[Dict]:
    """Get all relationships involving a specific article."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM relationships
            WHERE article_id_a = ? OR article_id_b = ?
        """, (article_id, article_id))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"[DB ERROR] get_relationships_for_article: {e}")
        return []


def get_all_relationships() -> List[Dict]:
    """Get all relationships in the database."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM relationships")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"[DB ERROR] get_all_relationships: {e}")
        return []


# ─────────────────────────────────────────────
# SOURCE OPERATIONS
# ─────────────────────────────────────────────

def upsert_source(source_name: str, prediction: str, is_duplicate: bool):
    """Update source statistics after an article is analyzed."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        # Insert if not exists
        cursor.execute("""
            INSERT OR IGNORE INTO sources (source_name, first_seen, last_seen)
            VALUES (?, ?, ?)
        """, (source_name, now, now))

        # Update counts
        cursor.execute("""
            UPDATE sources SET
                total_articles = total_articles + 1,
                last_seen = ?
            WHERE source_name = ?
        """, (now, source_name))

        if prediction == "REAL":
            cursor.execute("UPDATE sources SET real_count = real_count + 1 WHERE source_name = ?",
                           (source_name,))
        elif prediction == "FAKE":
            cursor.execute("UPDATE sources SET fake_count = fake_count + 1 WHERE source_name = ?",
                           (source_name,))
        elif prediction == "SUSPICIOUS":
            cursor.execute("UPDATE sources SET suspicious_count = suspicious_count + 1 WHERE source_name = ?",
                           (source_name,))

        if is_duplicate:
            cursor.execute("UPDATE sources SET duplicate_count = duplicate_count + 1 WHERE source_name = ?",
                           (source_name,))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB ERROR] upsert_source: {e}")


def get_all_sources() -> List[Dict]:
    """Get all sources and their statistics."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sources ORDER BY total_articles DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"[DB ERROR] get_all_sources: {e}")
        return []


# ─────────────────────────────────────────────
# DASHBOARD STATISTICS
# ─────────────────────────────────────────────

def get_dashboard_stats() -> Dict:
    """Return aggregate statistics for the dashboard."""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM articles")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM articles WHERE prediction = 'REAL'")
        real = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM articles WHERE prediction = 'FAKE'")
        fake = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM articles WHERE prediction = 'SUSPICIOUS'")
        suspicious = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM articles WHERE is_duplicate = 1")
        duplicates = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM relationships")
        relationships = cursor.fetchone()[0]

        conn.close()
        return {
            "total": total,
            "real": real,
            "fake": fake,
            "suspicious": suspicious,
            "duplicates": duplicates,
            "relationships": relationships
        }
    except Exception as e:
        print(f"[DB ERROR] get_dashboard_stats: {e}")
        return {"total": 0, "real": 0, "fake": 0, "suspicious": 0, "duplicates": 0, "relationships": 0}
