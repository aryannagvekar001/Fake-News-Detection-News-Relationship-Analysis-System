"""
backend/news_analyzer.py
Main orchestrator that ties together all backend modules.

When a user submits an article for analysis, this module:
1. Preprocesses and normalizes the text
2. Extracts keywords
3. Detects exact and near duplicates using hashing
4. Runs the ML model for fake/real prediction
5. Finds related articles
6. Creates graph nodes and edges
7. Calculates credibility score
8. Saves everything to the database
9. Returns a comprehensive analysis result

This is the "brain" of the application.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from backend import database
from backend import keyword_manager
from backend.text_processor import (
    normalize_text, extract_keywords, compute_cosine_similarity,
    compute_jaccard_similarity, detect_topic, get_text_statistics,
    compute_credibility_score
)
from backend.hashing import (
    compute_headline_hash, compute_content_hash, compute_normalized_hash,
    get_short_hash, get_all_hash_info, simhash_similarity
)
from backend.graph_manager import get_graph_manager, REL_SIMILAR_CONTENT, REL_SAME_TOPIC, REL_SAME_SOURCE, REL_DUPLICATE, REL_RELATED_KEYWORDS
from backend.fake_news_model import get_model

# Thresholds for relationship detection
EXACT_DUPLICATE_THRESHOLD = 1.0    # Same hash = exact duplicate
NEAR_DUPLICATE_THRESHOLD = 0.85    # Cosine ≥ 0.85 → DUPLICATE edge
SIMILAR_THRESHOLD = 0.40           # Cosine ≥ 0.40 → SIMILAR_CONTENT edge
KEYWORD_OVERLAP_THRESHOLD = 0.30   # Jaccard ≥ 0.30 → RELATED_KEYWORDS edge


def generate_article_id(headline: str) -> str:
    """
    Generate a unique article ID.
    Format: ART-{short_hash}-{timestamp_suffix}
    Example: ART-A3F9B2C1-1234
    """
    short = get_short_hash(headline)
    suffix = str(uuid.uuid4())[:4].upper()
    return f"ART-{short}-{suffix}"


def analyze_article(
    headline: str,
    content: str,
    source: str = "Unknown",
    pub_date: str = ""
) -> Dict:
    """
    Main analysis function. Analyzes a news article end-to-end.

    Parameters:
        headline: Article title
        content: Full article text
        source: Publisher/source name
        pub_date: Optional publication date string

    Returns:
        A comprehensive result dictionary with all analysis findings.
    """

    # ─────────────────────────────────────────────────────────────
    # VALIDATION
    # ─────────────────────────────────────────────────────────────
    if not headline or not headline.strip():
        return {"success": False, "error": "Headline cannot be empty."}
    if not content or not content.strip():
        return {"success": False, "error": "Article content cannot be empty."}
    if len(content.strip()) < 20:
        return {"success": False, "error": "Article content is too short (minimum 20 characters)."}

    headline = headline.strip()
    content = content.strip()
    source = source.strip() if source else "Unknown"

    # ─────────────────────────────────────────────────────────────
    # STEP 1: TEXT PREPROCESSING & KEYWORD EXTRACTION
    # ─────────────────────────────────────────────────────────────
    print(f"[ANALYZER] Step 1: Preprocessing '{headline[:50]}...'")
    keywords = extract_keywords(content + " " + headline, top_n=12)
    topic = detect_topic(content, headline)
    text_stats = get_text_statistics(content)

    # ─────────────────────────────────────────────────────────────
    # STEP 2: HASHING
    # ─────────────────────────────────────────────────────────────
    print("[ANALYZER] Step 2: Computing hashes...")
    hash_headline = compute_headline_hash(headline)
    hash_content = compute_content_hash(content)
    hash_normalized = compute_normalized_hash(headline, content)
    hash_info = get_all_hash_info(headline, content)

    # ─────────────────────────────────────────────────────────────
    # STEP 3: DUPLICATE DETECTION
    # ─────────────────────────────────────────────────────────────
    print("[ANALYZER] Step 3: Checking for duplicates...")
    is_duplicate = False
    duplicate_of = None
    similarity_score = 0.0
    duplicate_type = None

    # Check exact duplicate by hash
    existing = database.get_article_by_hash(hash_normalized)
    if existing:
        is_duplicate = True
        duplicate_of = existing["article_id"]
        similarity_score = 1.0
        duplicate_type = "EXACT"

    # Check near-duplicates using cosine similarity against all stored articles
    near_duplicate_matches = []
    all_articles = database.get_all_hashes()
    combined_text = headline + " " + content

    for stored in all_articles:
        if stored["article_id"] == duplicate_of:
            continue  # Already found as exact duplicate
        stored_combined = stored.get("headline", "") + " " + stored.get("content", "")

        # Use simhash for fast pre-filter
        sim_sim = simhash_similarity(combined_text, stored_combined)
        if sim_sim > 0.5:
            # Do full cosine similarity for confirmed candidates
            cosine_sim = compute_cosine_similarity(combined_text, stored_combined)
            if cosine_sim >= NEAR_DUPLICATE_THRESHOLD:
                near_duplicate_matches.append({
                    "article_id": stored["article_id"],
                    "similarity": cosine_sim,
                    "type": "NEAR_DUPLICATE"
                })
            elif cosine_sim >= SIMILAR_THRESHOLD:
                near_duplicate_matches.append({
                    "article_id": stored["article_id"],
                    "similarity": cosine_sim,
                    "type": "SIMILAR"
                })

    # Take the closest near-duplicate if no exact match
    if not is_duplicate and near_duplicate_matches:
        near_duplicate_matches.sort(key=lambda x: x["similarity"], reverse=True)
        best = near_duplicate_matches[0]
        if best["type"] == "NEAR_DUPLICATE":
            is_duplicate = True
            duplicate_of = best["article_id"]
            similarity_score = best["similarity"]
            duplicate_type = "NEAR"

    # ─────────────────────────────────────────────────────────────
    # STEP 4: ML PREDICTION
    # ─────────────────────────────────────────────────────────────
    print("[ANALYZER] Step 4: Running ML model...")
    model = get_model()
    prediction_result = model.predict(content, headline)
    prediction = prediction_result.get("prediction", "UNKNOWN")
    confidence = prediction_result.get("confidence", 0.0)
    real_prob = prediction_result.get("real_probability", 0.0)
    fake_prob = prediction_result.get("fake_probability", 0.0)

    # ─────────────────────────────────────────────────────────────
    # STEP 5: SOURCE ANALYSIS
    # ─────────────────────────────────────────────────────────────
    source_fake_ratio = 0.0
    sources = database.get_all_sources()
    for src in sources:
        if src["source_name"].lower() == source.lower():
            total = src["total_articles"]
            if total > 0:
                source_fake_ratio = src["fake_count"] / total
            break

    # ─────────────────────────────────────────────────────────────
    # STEP 6: CREDIBILITY SCORE
    # ─────────────────────────────────────────────────────────────
    credibility_score = compute_credibility_score(
        confidence=real_prob,
        is_duplicate=is_duplicate,
        similar_count=len(near_duplicate_matches),
        source_fake_ratio=source_fake_ratio,
        keyword_overlap=0.0
    )

    # ─────────────────────────────────────────────────────────────
    # STEP 7: ARTICLE ID & GRAPH NODE
    # ─────────────────────────────────────────────────────────────
    article_id = generate_article_id(headline)
    graph_node_id = article_id  # Node ID same as article ID

    # ─────────────────────────────────────────────────────────────
    # STEP 8: BUILD GRAPH EDGES (RELATIONSHIPS)
    # ─────────────────────────────────────────────────────────────
    print("[ANALYZER] Step 8: Building graph relationships...")
    graph_manager = get_graph_manager()
    relationships_found = []

    # Add this article's node
    article_node_data = {
        "headline": headline,
        "source": source,
        "prediction": prediction,
        "topic": topic,
        "pub_date": pub_date,
        "confidence": confidence
    }
    graph_manager.add_article_node(article_id, article_node_data)

    # Add relationships to graph (and database)
    # Exact/near duplicate relationship
    if duplicate_of:
        rel_type = REL_DUPLICATE
        graph_manager.add_relationship(article_id, duplicate_of, rel_type, similarity_score)
        database.save_relationship(article_id, duplicate_of, rel_type, similarity_score)
        relationships_found.append({
            "target": duplicate_of,
            "type": rel_type,
            "score": similarity_score
        })

    # Process all near-duplicate and similar matches
    for match in near_duplicate_matches:
        if match["article_id"] == duplicate_of:
            continue
        sim = match["similarity"]
        if sim >= NEAR_DUPLICATE_THRESHOLD:
            rel_type = REL_DUPLICATE
        elif sim >= SIMILAR_THRESHOLD:
            rel_type = REL_SIMILAR_CONTENT
        else:
            continue

        graph_manager.add_relationship(article_id, match["article_id"], rel_type, sim)
        database.save_relationship(article_id, match["article_id"], rel_type, sim)
        relationships_found.append({
            "target": match["article_id"],
            "type": rel_type,
            "score": sim
        })

    # Topic-based relationships: link to same-topic articles
    all_db_articles = database.get_all_articles()
    for stored_article in all_db_articles:
        stored_id = stored_article["article_id"]
        if stored_id == article_id or stored_id == duplicate_of:
            continue
        stored_combined = stored_article.get("headline", "") + " " + stored_article.get("content", "")

        # Same topic
        if stored_article.get("topic") == topic and topic != "General":
            jaccard = compute_jaccard_similarity(combined_text, stored_combined)
            if jaccard >= KEYWORD_OVERLAP_THRESHOLD:
                graph_manager.add_relationship(article_id, stored_id, REL_SAME_TOPIC, jaccard)
                database.save_relationship(article_id, stored_id, REL_SAME_TOPIC, jaccard)
                if not any(r["target"] == stored_id for r in relationships_found):
                    relationships_found.append({
                        "target": stored_id,
                        "type": REL_SAME_TOPIC,
                        "score": jaccard
                    })

        # Same source
        if (stored_article.get("source", "").lower() == source.lower()
                and source.lower() not in ("unknown", "")):
            if not graph_manager.graph.has_edge(article_id, stored_id):
                graph_manager.add_relationship(article_id, stored_id, REL_SAME_SOURCE, 0.5)
                database.save_relationship(article_id, stored_id, REL_SAME_SOURCE, 0.5)
                if not any(r["target"] == stored_id for r in relationships_found):
                    relationships_found.append({
                        "target": stored_id,
                        "type": REL_SAME_SOURCE,
                        "score": 0.5
                    })

    # ─────────────────────────────────────────────────────────────
    # STEP 9: KEYWORD INDEXING
    # ─────────────────────────────────────────────────────────────
    keyword_manager.index_article(article_id, keywords, topic)

    # ─────────────────────────────────────────────────────────────
    # STEP 10: SAVE TO DATABASE
    # ─────────────────────────────────────────────────────────────
    print("[ANALYZER] Step 10: Saving to database...")
    timestamp = datetime.now().isoformat()

    article_data = {
        "article_id": article_id,
        "headline": headline,
        "content": content,
        "source": source,
        "pub_date": pub_date,
        "prediction": prediction,
        "confidence": confidence,
        "credibility_score": credibility_score,
        "keywords": keywords,
        "hash_headline": hash_headline,
        "hash_content": hash_content,
        "hash_normalized": hash_normalized,
        "graph_node_id": graph_node_id,
        "is_duplicate": is_duplicate,
        "duplicate_of": duplicate_of,
        "similarity_score": similarity_score,
        "topic": topic,
        "timestamp": timestamp,
        "word_count": text_stats.get("word_count", 0)
    }

    database.save_article(article_data)
    database.upsert_source(source, prediction, is_duplicate)

    # ─────────────────────────────────────────────────────────────
    # STEP 11: COMPILE FINAL RESULT
    # ─────────────────────────────────────────────────────────────

    # Get related articles with details
    related_articles = []
    for rel in relationships_found[:8]:  # Top 8 related
        rel_article = database.get_article_by_id(rel["target"])
        if rel_article:
            related_articles.append({
                "article_id": rel["target"],
                "headline": rel_article.get("headline", "")[:80],
                "source": rel_article.get("source", ""),
                "prediction": rel_article.get("prediction", ""),
                "relationship": rel["type"],
                "similarity": round(rel["score"] * 100, 1)
            })

    result = {
        "success": True,
        "article_id": article_id,

        # Prediction
        "prediction": prediction,
        "confidence": round(confidence * 100, 1),
        "real_probability": round(real_prob * 100, 1),
        "fake_probability": round(fake_prob * 100, 1),
        "credibility_score": credibility_score,

        # Article info
        "headline": headline,
        "source": source,
        "topic": topic,
        "pub_date": pub_date,
        "timestamp": timestamp,
        "word_count": text_stats.get("word_count", 0),

        # Text analysis
        "keywords": keywords,
        "text_statistics": text_stats,

        # Duplicate info
        "is_duplicate": is_duplicate,
        "duplicate_of": duplicate_of,
        "duplicate_type": duplicate_type,
        "similarity_score": round(similarity_score * 100, 1),

        # Related articles
        "related_articles": related_articles,
        "related_count": len(relationships_found),

        # Graph info
        "graph_node_id": graph_node_id,
        "graph_connections": len(relationships_found),

        # Hash info (for DSA demonstration)
        "hash_info": hash_info,

        # Explainability
        "explanation": _build_explanation(prediction, confidence, is_duplicate,
                                          len(relationships_found), real_prob, fake_prob),

        "disclaimer": "⚠️ System assessment based on DEMO model and SAMPLE data. Not a reliable truth indicator."
    }

    print(f"[ANALYZER] Analysis complete: {prediction} ({confidence*100:.1f}% confidence)")
    return result


def _build_explanation(
    prediction: str,
    confidence: float,
    is_duplicate: bool,
    related_count: int,
    real_prob: float,
    fake_prob: float
) -> List[Dict]:
    """
    Build a human-readable explanation of the prediction factors.
    This is for the explainability requirement.
    """
    factors = []

    # Model confidence
    conf_level = "High" if confidence > 0.8 else ("Medium" if confidence > 0.6 else "Low")
    factors.append({
        "factor": "Model Confidence",
        "value": f"{confidence * 100:.1f}%",
        "level": conf_level,
        "description": f"The ML model assessed this article with {conf_level.lower()} confidence."
    })

    # Real probability
    factors.append({
        "factor": "Real Probability",
        "value": f"{real_prob * 100:.1f}%",
        "level": "positive" if real_prob > 0.5 else "negative",
        "description": f"Probability assigned to REAL classification."
    })

    # Fake probability
    factors.append({
        "factor": "Fake Probability",
        "value": f"{fake_prob * 100:.1f}%",
        "level": "negative" if fake_prob > 0.5 else "positive",
        "description": f"Probability assigned to FAKE classification."
    })

    # Duplicate status
    if is_duplicate:
        factors.append({
            "factor": "Duplicate Detected",
            "value": "YES",
            "level": "warning",
            "description": "This article appears to be a duplicate or near-duplicate of an existing article."
        })

    # Related articles
    if related_count > 0:
        factors.append({
            "factor": "Related Articles Found",
            "value": str(related_count),
            "level": "info",
            "description": f"Found {related_count} related article(s) in the database."
        })

    return factors


def get_article_analysis(article_id: str) -> Optional[Dict]:
    """
    Retrieve a full analysis for an already-stored article.
    Used when opening an article from history.
    """
    article = database.get_article_by_id(article_id)
    if not article:
        return None

    relationships = database.get_relationships_for_article(article_id)
    related_articles = []

    for rel in relationships:
        other_id = rel["article_id_b"] if rel["article_id_a"] == article_id else rel["article_id_a"]
        other = database.get_article_by_id(other_id)
        if other:
            related_articles.append({
                "article_id": other_id,
                "headline": other.get("headline", "")[:80],
                "source": other.get("source", ""),
                "prediction": other.get("prediction", ""),
                "relationship": rel.get("relationship_type", ""),
                "similarity": round(rel.get("similarity_score", 0) * 100, 1)
            })

    graph_manager = get_graph_manager()
    neighbors = graph_manager.get_neighbors(article_id)

    hash_info = get_all_hash_info(
        article.get("headline", ""),
        article.get("content", "")
    )

    article["related_articles"] = related_articles
    article["related_count"] = len(related_articles)
    article["graph_connections"] = len(neighbors)
    article["hash_info"] = hash_info
    article["confidence_display"] = round(article.get("confidence", 0) * 100, 1)

    return article
