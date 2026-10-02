"""
backend/keyword_manager.py
Keyword-to-article mapping using the custom HashTable.

DSA CONCEPT: Hash Table Application
Maps keyword strings to lists of article IDs.
Supports fast keyword search across all analyzed articles.
"""

from backend.hash_table import HashTable
from backend.text_processor import extract_keywords, normalize_text
from typing import List, Dict, Optional

# Global keyword hash table instance
_keyword_table: Optional[HashTable] = None


def get_keyword_table() -> HashTable:
    """Get the global keyword hash table (singleton)."""
    global _keyword_table
    if _keyword_table is None:
        _keyword_table = HashTable(size=512)
    return _keyword_table


def reset_keyword_table() -> HashTable:
    """Reset the keyword hash table."""
    global _keyword_table
    _keyword_table = HashTable(size=512)
    return _keyword_table


def index_article(article_id: str, keywords: List[str], topic: str = "") -> None:
    """
    Index an article's keywords in the hash table.
    Also indexes the topic as a keyword.

    After this, you can search for any keyword to find this article.

    Example:
        index_article("A01", ["technology", "startup", "funding"])
        lookup_keyword("technology") → ["A01", ...]
    """
    table = get_keyword_table()

    # Index each keyword
    for keyword in keywords:
        if keyword and len(keyword) > 2:
            normalized_kw = normalize_text(keyword, remove_stopwords=False).lower()
            if normalized_kw:
                table.insert(normalized_kw, article_id)

    # Also index by topic
    if topic:
        table.insert(topic.lower(), article_id)


def lookup_keyword(keyword: str) -> List[str]:
    """
    Search for articles by keyword.
    Returns a list of article IDs.

    Time Complexity: O(1) average case — power of hash tables!
    """
    table = get_keyword_table()
    normalized_kw = normalize_text(keyword, remove_stopwords=False).lower()

    result = table.lookup(normalized_kw)
    if result is None:
        return []
    if isinstance(result, list):
        return result
    return [result]


def get_all_keywords() -> List[str]:
    """Return all indexed keywords."""
    table = get_keyword_table()
    return sorted(table.get_all_keys())


def get_keyword_article_mapping() -> List[Dict]:
    """
    Return all keyword → article ID mappings for display.

    Returns a list of dicts: [{"keyword": "...", "articles": [...], "count": N}]
    Sorted by article count descending.
    """
    table = get_keyword_table()
    items = table.get_all_items()

    result = []
    for keyword, articles in items:
        if isinstance(articles, list):
            count = len(articles)
        else:
            articles = [articles]
            count = 1
        result.append({
            "keyword": keyword,
            "articles": articles,
            "count": count
        })

    # Sort by count descending
    result.sort(key=lambda x: x["count"], reverse=True)
    return result


def get_table_stats() -> Dict:
    """Return hash table statistics for the DSA page."""
    table = get_keyword_table()
    return table.get_bucket_info()


def rebuild_from_articles(articles: List[Dict]) -> None:
    """
    Rebuild the keyword index from all articles in the database.
    Called on application startup.
    """
    reset_keyword_table()
    for article in articles:
        article_id = article.get("article_id", "")
        keywords = article.get("keywords", [])
        topic = article.get("topic", "")
        if article_id:
            index_article(article_id, keywords, topic)
