"""
backend/text_processor.py
Text preprocessing, keyword extraction, and similarity calculation.
Uses TF-IDF concepts to extract important terms.
"""

import re
import math
from collections import Counter
from typing import List, Tuple, Dict

# ─────────────────────────────────────────────
# STOP WORDS — common words to ignore
# ─────────────────────────────────────────────
STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "was", "are", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can", "that", "this",
    "these", "those", "it", "its", "they", "them", "their", "we", "our",
    "you", "your", "he", "she", "his", "her", "i", "my", "me", "us",
    "as", "if", "not", "no", "so", "than", "then", "when", "where",
    "which", "who", "whom", "what", "how", "all", "any", "both", "each",
    "few", "more", "most", "other", "some", "such", "into", "through",
    "during", "before", "after", "above", "below", "up", "down", "out",
    "about", "also", "new", "said", "says", "say", "according", "over",
    "just", "only", "because", "while", "there", "here", "now", "still",
    "between", "among", "against", "without", "within", "since", "until",
    "across", "behind", "beyond", "around", "off", "per", "same"
}


def normalize_text(text: str, remove_stopwords: bool = True) -> str:
    """
    DSA CONCEPT: Text Normalization Pipeline
    Converts text to a canonical form for hashing and comparison.
    Steps:
    1. Lowercase
    2. Remove special characters
    3. Remove extra whitespace
    4. Optionally remove stop words
    """
    if not text:
        return ""

    # Step 1: Convert to lowercase
    text = text.lower()

    # Step 2: Remove URLs
    text = re.sub(r'http\S+|www\S+', '', text)

    # Step 3: Remove special characters, keep only letters and spaces
    text = re.sub(r'[^a-z\s]', ' ', text)

    # Step 4: Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # Step 5: Remove stop words if requested
    if remove_stopwords:
        words = text.split()
        words = [w for w in words if w not in STOP_WORDS and len(w) > 2]
        text = ' '.join(words)

    return text


def tokenize(text: str) -> List[str]:
    """Split normalized text into tokens (words)."""
    normalized = normalize_text(text, remove_stopwords=True)
    return normalized.split() if normalized else []


def compute_tf(tokens: List[str]) -> Dict[str, float]:
    """
    Term Frequency: TF(t) = count(t) / total_tokens
    Higher frequency = more important in this document.
    """
    if not tokens:
        return {}
    total = len(tokens)
    counts = Counter(tokens)
    return {word: count / total for word, count in counts.items()}


def extract_keywords(text: str, top_n: int = 10) -> List[str]:
    """
    Extract top-N keywords from text using TF + word frequency ranking.
    Returns a list of the most significant words.
    """
    tokens = tokenize(text)
    if not tokens:
        return []

    tf_scores = compute_tf(tokens)

    # Boost words that are longer (tend to be more meaningful)
    boosted = {}
    for word, score in tf_scores.items():
        length_boost = min(len(word) / 10.0, 0.5)
        boosted[word] = score + length_boost

    # Sort by score descending
    sorted_keywords = sorted(boosted.items(), key=lambda x: x[1], reverse=True)
    return [word for word, _ in sorted_keywords[:top_n]]


def compute_cosine_similarity(text1: str, text2: str) -> float:
    """
    DSA CONCEPT: Cosine Similarity using TF vectors.
    Measures how similar two texts are regardless of length.
    Returns a float between 0.0 (completely different) and 1.0 (identical).

    Formula: cos(θ) = (A · B) / (|A| × |B|)
    """
    tokens1 = tokenize(text1)
    tokens2 = tokenize(text2)

    if not tokens1 or not tokens2:
        return 0.0

    # Build TF vectors
    tf1 = compute_tf(tokens1)
    tf2 = compute_tf(tokens2)

    # Find common vocabulary
    vocab = set(tf1.keys()) | set(tf2.keys())

    # Compute dot product
    dot_product = sum(tf1.get(word, 0) * tf2.get(word, 0) for word in vocab)

    # Compute magnitudes
    mag1 = math.sqrt(sum(v ** 2 for v in tf1.values()))
    mag2 = math.sqrt(sum(v ** 2 for v in tf2.values()))

    if mag1 == 0 or mag2 == 0:
        return 0.0

    return dot_product / (mag1 * mag2)


def compute_jaccard_similarity(text1: str, text2: str) -> float:
    """
    Jaccard Similarity: |A ∩ B| / |A ∪ B|
    Alternative similarity measure based on word sets.
    """
    set1 = set(tokenize(text1))
    set2 = set(tokenize(text2))
    if not set1 and not set2:
        return 0.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0


def detect_topic(text: str, headline: str) -> str:
    """
    Simple rule-based topic detection.
    Assigns a topic category based on keyword presence.
    """
    combined = (text + " " + headline).lower()

    topic_keywords = {
        "Politics": ["government", "election", "parliament", "president", "minister",
                     "senate", "congress", "policy", "vote", "political", "law", "bill",
                     "democrat", "republican", "party", "legislature"],
        "Technology": ["technology", "tech", "software", "computer", "internet", "ai",
                       "artificial intelligence", "digital", "cyber", "app", "startup",
                       "innovation", "data", "algorithm", "robot", "5g"],
        "Health": ["health", "medical", "hospital", "vaccine", "disease", "virus",
                   "doctor", "medicine", "treatment", "patient", "cancer", "diabetes",
                   "mental health", "fda", "clinical", "drug"],
        "Science": ["science", "research", "study", "scientist", "discovery", "experiment",
                    "laboratory", "physics", "chemistry", "biology", "space", "nasa",
                    "climate", "environment", "energy"],
        "Economy": ["economy", "economic", "market", "stock", "bank", "finance",
                    "investment", "trade", "inflation", "gdp", "unemployment", "recession",
                    "budget", "fiscal", "monetary", "tax", "revenue"],
        "Sports": ["sports", "game", "team", "player", "championship", "league",
                   "tournament", "match", "score", "athlete", "football", "cricket",
                   "basketball", "tennis", "olympic"],
        "Entertainment": ["entertainment", "movie", "film", "music", "celebrity",
                          "artist", "actor", "actress", "show", "award", "oscar",
                          "grammy", "television", "streaming"],
        "World": ["international", "global", "world", "country", "nation", "foreign",
                  "diplomat", "treaty", "united nations", "war", "conflict", "peace"],
    }

    best_topic = "General"
    best_count = 0

    for topic, keywords in topic_keywords.items():
        count = sum(1 for kw in keywords if kw in combined)
        if count > best_count:
            best_count = count
            best_topic = topic

    return best_topic


def get_text_statistics(text: str) -> Dict:
    """Return basic text statistics for display."""
    words = text.split()
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    chars = len(text)
    unique_words = len(set(w.lower() for w in words))
    avg_word_length = sum(len(w) for w in words) / len(words) if words else 0

    return {
        "word_count": len(words),
        "sentence_count": len(sentences),
        "char_count": chars,
        "unique_words": unique_words,
        "avg_word_length": round(avg_word_length, 2),
        "avg_words_per_sentence": round(len(words) / len(sentences), 2) if sentences else 0
    }


def compute_credibility_score(
    confidence: float,
    is_duplicate: bool,
    similar_count: int,
    source_fake_ratio: float = 0.0,
    keyword_overlap: float = 0.0
) -> float:
    """
    Compute an explainable credibility score from multiple factors.
    Returns a value between 0.0 and 100.0.

    Factors:
    - Model confidence (primary signal)
    - Duplicate status (penalizes duplicates slightly)
    - Related articles with different predictions (penalizes)
    - Source history (mild signal)
    """
    score = confidence * 100.0  # Start with model confidence

    if is_duplicate:
        score -= 5.0  # Slight penalty for being duplicate

    if similar_count > 5:
        score -= 3.0  # Many similar articles might indicate viral misinformation

    # Source penalty if source has high fake ratio
    score -= source_fake_ratio * 20.0

    return max(0.0, min(100.0, round(score, 1)))
