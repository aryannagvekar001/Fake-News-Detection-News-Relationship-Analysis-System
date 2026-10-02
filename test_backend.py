"""
Test script for all backend modules.
Run: python test_backend.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 50)
print("Backend Module Tests")
print("=" * 50)

# Test 1: Database
print("\n[1] Testing database...")
from backend.database import init_database, save_article, get_all_articles
init_database()
print("  ✓ Database initialized")

# Test 2: Text Processor
print("\n[2] Testing text processor...")
from backend.text_processor import (
    extract_keywords, compute_cosine_similarity,
    detect_topic, normalize_text, get_text_statistics
)
kw = extract_keywords("Scientists discover new vaccine for disease treatment hospital", top_n=5)
print(f"  ✓ Keywords: {kw}")
sim = compute_cosine_similarity("government policy education", "government announces education policy")
print(f"  ✓ Cosine similarity: {sim:.3f}")
topic = detect_topic("The stock market rose sharply as investors bought technology stocks", "Market Rally")
print(f"  ✓ Topic detected: {topic}")

# Test 3: Hashing
print("\n[3] Testing hashing...")
from backend.hashing import (
    compute_sha256, compute_normalized_hash,
    get_short_hash, simhash_similarity
)
h = compute_sha256("test text")
print(f"  ✓ SHA-256 (first 16 chars): {h[:16]}...")
nh = compute_normalized_hash("Government announces new policy", "The government has announced a new policy for education")
print(f"  ✓ Normalized hash: {nh[:16]}...")
sh = get_short_hash("test")
print(f"  ✓ Short hash: {sh}")
sim = simhash_similarity("government education policy", "government announces education policy")
print(f"  ✓ SimHash similarity: {sim:.3f}")

# Test 4: Hash Table
print("\n[4] Testing custom hash table...")
from backend.hash_table import HashTable
ht = HashTable(size=64)
ht.insert("technology", "A01")
ht.insert("technology", "A05")
ht.insert("health", "A02")
ht.insert("politics", "A03")
result = ht.lookup("technology")
print(f"  ✓ Inserted 4 entries")
print(f"  ✓ Lookup 'technology': {result}")
print(f"  ✓ Table stats: {ht.get_bucket_info()}")
deleted = ht.delete("health")
print(f"  ✓ Delete 'health': {deleted}")

# Test 5: Graph
print("\n[5] Testing graph manager...")
from backend.graph_manager import reset_graph_manager
gm = reset_graph_manager()
gm.add_article_node("ART-TEST1-0001", {
    "headline": "Test Article 1",
    "source": "TestSource",
    "prediction": "REAL",
    "topic": "Technology",
    "pub_date": "2024-01-01",
    "confidence": 0.85
})
gm.add_article_node("ART-TEST2-0002", {
    "headline": "Test Article 2",
    "source": "TestSource",
    "prediction": "FAKE",
    "topic": "Technology",
    "pub_date": "2024-01-02",
    "confidence": 0.75
})
gm.add_article_node("ART-TEST3-0003", {
    "headline": "Test Article 3",
    "source": "OtherSource",
    "prediction": "SUSPICIOUS",
    "topic": "Health",
    "pub_date": "2024-01-03",
    "confidence": 0.60
})
gm.add_relationship("ART-TEST1-0001", "ART-TEST2-0002", "SIMILAR_CONTENT", 0.72)
gm.add_relationship("ART-TEST2-0002", "ART-TEST3-0003", "SAME_TOPIC", 0.55)
stats = gm.get_graph_stats()
print(f"  ✓ Graph: {stats['nodes']} nodes, {stats['edges']} edges")
neighbors = gm.get_neighbors("ART-TEST2-0002")
print(f"  ✓ Neighbors of TEST2: {neighbors}")

# Test 6: Graph Algorithms
print("\n[6] Testing graph algorithms...")
from backend.graph_algorithms import bfs, dfs, find_connected_components
bfs_result = bfs(gm.get_nx_graph(), "ART-TEST1-0001", max_depth=3)
print(f"  ✓ BFS traversal: {bfs_result['traversal_order']}")
dfs_result = dfs(gm.get_nx_graph(), "ART-TEST1-0001")
print(f"  ✓ DFS traversal: {dfs_result['traversal_order']}")
comp_result = find_connected_components(gm.get_nx_graph())
print(f"  ✓ Connected components: {comp_result['count']} component(s)")

# Test 7: ML Model
print("\n[7] Testing ML model...")
from backend.fake_news_model import ensure_model_trained, get_model
result = ensure_model_trained()
print(f"  ✓ Model status: success={result.get('success')}")
model = get_model()
pred = model.predict(
    "Scientists discover new vaccine that prevents disease with 95% effectiveness",
    "New vaccine shows 95% effectiveness in clinical trials"
)
print(f"  ✓ Prediction: {pred['prediction']} ({pred['confidence']*100:.1f}% confidence)")

# Test 8: Keyword Manager
print("\n[8] Testing keyword manager...")
from backend.keyword_manager import reset_keyword_table, index_article, lookup_keyword, get_table_stats
reset_keyword_table()
index_article("ART-TEST1-0001", ["vaccine", "disease", "clinical", "health"], "Health")
index_article("ART-TEST2-0002", ["government", "policy", "education"], "Politics")
result = lookup_keyword("vaccine")
print(f"  ✓ Keyword lookup 'vaccine': {result}")
result2 = lookup_keyword("government")
print(f"  ✓ Keyword lookup 'government': {result2}")
stats = get_table_stats()
print(f"  ✓ Keyword table stats: {stats}")

# Test 9: News Analyzer (end-to-end)
print("\n[9] Testing full analysis pipeline...")
from backend.news_analyzer import analyze_article
analysis = analyze_article(
    headline="Scientists discover new treatment for diabetes",
    content="Medical researchers at the National Institute have discovered a new treatment for Type 2 diabetes that reduces blood sugar levels by 40 percent. The treatment was tested in clinical trials on 500 patients. The results were published in the New England Journal of Medicine.",
    source="Medical News Today",
    pub_date="2024-01-15"
)
if analysis.get("success"):
    print(f"  ✓ Analysis complete:")
    print(f"    Article ID: {analysis['article_id']}")
    print(f"    Prediction: {analysis['prediction']} ({analysis['confidence']:.1f}%)")
    print(f"    Keywords: {analysis['keywords'][:5]}")
    print(f"    Is Duplicate: {analysis['is_duplicate']}")
    print(f"    Graph Connections: {analysis['graph_connections']}")
    print(f"    Credibility Score: {analysis['credibility_score']}")
else:
    print(f"  ✗ Analysis failed: {analysis.get('error')}")

print("\n" + "=" * 50)
print("ALL TESTS PASSED")
print("=" * 50)
