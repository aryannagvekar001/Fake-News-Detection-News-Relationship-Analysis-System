"""
backend/hashing.py
Hashing implementation using Python's hashlib.

DSA CONCEPT: Hashing
- A hash function maps input data of arbitrary size to a fixed-size value.
- Used here for duplicate detection and fast lookup.
- We use SHA-256 (Secure Hash Algorithm 256-bit).

Applications in this project:
1. Exact duplicate detection: same hash = same article
2. Near-duplicate detection: similar hash after normalization
3. Content fingerprinting: quick comparison without reading full text
"""

import hashlib
from backend.text_processor import normalize_text
from typing import Tuple


def compute_sha256(text: str) -> str:
    """
    Compute SHA-256 hash of a given string.
    SHA-256 produces a 64-character hexadecimal string.

    DSA CONCEPT: Hash Function
    - Deterministic: same input always gives same output
    - Fast computation: O(n) where n = length of input
    - Collision resistant: astronomically unlikely to find two inputs with same hash
    """
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def compute_md5(text: str) -> str:
    """
    Compute MD5 hash (shorter, for display purposes only).
    Note: MD5 is NOT cryptographically secure, but is fine for duplicate detection.
    """
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def compute_headline_hash(headline: str) -> str:
    """
    Compute hash for a news headline.
    Normalizes first, then hashes.

    Example:
        Input:  "Government ANNOUNCES New Education Policy!"
        Normal: "government announce new education policy"
        Hash:   "3a4f7d..." (SHA-256)
    """
    normalized = normalize_text(headline, remove_stopwords=False)
    return compute_sha256(normalized)


def compute_content_hash(content: str) -> str:
    """
    Compute hash for full article content.
    Uses full normalization including stop word removal.
    """
    normalized = normalize_text(content, remove_stopwords=True)
    return compute_sha256(normalized)


def compute_normalized_hash(headline: str, content: str) -> str:
    """
    Compute a combined normalized hash from headline + content.
    Used for EXACT duplicate detection.

    Two articles are exact duplicates if their normalized hashes match.
    """
    combined = normalize_text(headline + " " + content, remove_stopwords=True)
    return compute_sha256(combined)


def get_short_hash(text: str, length: int = 8) -> str:
    """
    Return a shortened hash (first N characters) for display purposes.
    Used in the UI to show article IDs.
    """
    return compute_sha256(text)[:length].upper()


def is_exact_duplicate(hash1: str, hash2: str) -> bool:
    """
    Check if two hashes are identical (exact duplicate).
    O(1) comparison — this is the power of hashing!

    Without hashing: comparing two articles would require O(n) character-by-character comparison.
    With hashing: O(1) hash comparison.
    """
    return hash1 == hash2


def compute_simhash(text: str, bits: int = 64) -> int:
    """
    DSA CONCEPT: SimHash (Locality Sensitive Hashing)
    A technique for near-duplicate detection.

    Regular SHA-256: completely different hash even for tiny changes.
    SimHash: similar texts produce similar hashes (small Hamming distance).

    Algorithm:
    1. Tokenize text into words
    2. For each word, compute hash and add/subtract to a vector
    3. Convert vector to binary fingerprint

    This allows comparing articles that are slightly different.
    """
    tokens = text.lower().split()
    if not tokens:
        return 0

    # Initialize a vector of 'bits' dimensions
    vector = [0] * bits

    for token in tokens:
        # Hash each token
        token_hash = int(hashlib.md5(token.encode()).hexdigest(), 16)

        # Update the vector
        for i in range(bits):
            if token_hash & (1 << i):
                vector[i] += 1
            else:
                vector[i] -= 1

    # Convert vector to binary fingerprint
    fingerprint = 0
    for i in range(bits):
        if vector[i] > 0:
            fingerprint |= (1 << i)

    return fingerprint


def hamming_distance(hash1: int, hash2: int) -> int:
    """
    Compute the Hamming distance between two SimHashes.
    Hamming distance = number of bit positions that differ.

    Lower distance = more similar documents.
    Distance 0 = identical documents.
    Distance > 10 = likely different documents.
    """
    xor = hash1 ^ hash2
    # Count set bits (Brian Kernighan's algorithm)
    count = 0
    while xor:
        xor &= xor - 1
        count += 1
    return count


def simhash_similarity(text1: str, text2: str, bits: int = 64) -> float:
    """
    Compute similarity between two texts using SimHash.
    Returns a value between 0.0 and 1.0.

    1.0 = identical texts
    0.0 = completely different texts
    """
    h1 = compute_simhash(text1, bits)
    h2 = compute_simhash(text2, bits)
    dist = hamming_distance(h1, h2)
    # Normalize: max distance = bits
    similarity = 1.0 - (dist / bits)
    return max(0.0, min(1.0, similarity))


def get_all_hash_info(headline: str, content: str) -> dict:
    """
    Return a complete hash information dictionary for an article.
    Used in the DSA Analysis page for demonstration.
    """
    norm_headline = normalize_text(headline, remove_stopwords=False)
    norm_content = normalize_text(content, remove_stopwords=True)
    combined = headline + " " + content

    return {
        "headline_hash_sha256": compute_sha256(norm_headline),
        "content_hash_sha256": compute_sha256(norm_content),
        "normalized_hash": compute_normalized_hash(headline, content),
        "short_hash": get_short_hash(combined),
        "simhash": compute_simhash(combined),
        "normalized_headline": norm_headline,
        "normalized_content": norm_content[:200] + "..." if len(norm_content) > 200 else norm_content
    }
