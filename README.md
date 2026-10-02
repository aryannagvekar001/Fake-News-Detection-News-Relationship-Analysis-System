# 🔍 Fake News Intelligence
## News Detection & Relationship Analysis System
### College DSA Project — Unit IV: Graph and Hashing Concepts

---

## Problem Statement

The rapid spread of misinformation through digital media presents a serious challenge. This project builds a **Fake News Detection & News Relationship Analysis System** that demonstrates Graph and Hashing concepts from a Data Structures and Algorithms course by applying them to a real-world problem domain.

---

## Objectives

1. Implement **Hashing** for fast duplicate detection and keyword indexing
2. Implement **Graph data structures** to model relationships between news articles
3. Demonstrate **BFS and DFS** traversal algorithms on the news graph
4. Identify **Connected Components** (news clusters)
5. Build a working **Machine Learning classifier** (TF-IDF + Logistic Regression)
6. Create a functional, polished desktop application as a demonstration platform

---

## Features

| Feature | Description |
|---|---|
| News Analysis | Full pipeline: preprocessing → hashing → ML prediction → graph |
| Duplicate Detection | Exact (SHA-256) and near-duplicate (SimHash + cosine similarity) |
| Fake News Classification | TF-IDF + Logistic Regression with confidence scores |
| Knowledge Graph | Directed graph with 5 relationship types |
| BFS Traversal | Find articles within N relationship levels |
| DFS Traversal | Explore entire connected clusters |
| Connected Components | Identify news clusters |
| Keyword Hash Table | Custom hash table with separate chaining |
| Dashboard | Real-time statistics and charts |
| Source Analysis | Per-publisher statistics (neutral wording) |
| Timeline | Chronological view of articles |
| DSA Analysis Page | Interactive demonstration of all DSA concepts |
| History | Search, filter, view, delete analyzed articles |

---

## Technologies

| Technology | Purpose |
|---|---|
| Python 3.x | Core language |
| CustomTkinter | Modern dark-themed desktop GUI |
| SQLite | Local persistent database |
| NetworkX | Graph data structure |
| matplotlib | Graph visualization and charts |
| scikit-learn | TF-IDF vectorizer + Logistic Regression |
| pandas | Dataset loading |
| hashlib | SHA-256 / MD5 hashing (stdlib) |
| joblib | Model save/load |

---

## System Architecture

```
User → Frontend (CustomTkinter) → Backend Modules → SQLite DB
                                        ↕
                              Graph Manager (NetworkX)
                                        ↕
                              Keyword Hash Table (Custom)
```

---

## Project Structure

```
fake_news_detection/
├── main.py                    ← Entry point
├── requirements.txt
├── README.md
│
├── data/
│   ├── news_dataset.csv       ← DEMO training data (labelled)
│   └── news_database.db       ← SQLite database (auto-created)
│
├── models/
│   └── pipeline.pkl           ← Trained ML pipeline (auto-saved)
│
├── backend/
│   ├── database.py            ← SQLite CRUD operations
│   ├── news_analyzer.py       ← Main analysis orchestrator
│   ├── fake_news_model.py     ← TF-IDF + Logistic Regression
│   ├── text_processor.py      ← NLP preprocessing, cosine similarity
│   ├── hashing.py             ← SHA-256, SimHash, Hamming distance
│   ├── hash_table.py          ← Custom hash table (separate chaining)
│   ├── graph_manager.py       ← NetworkX graph management
│   ├── graph_algorithms.py    ← BFS, DFS, Connected Components
│   └── keyword_manager.py     ← Keyword → article index (hash table)
│
├── frontend/
│   ├── dashboard.py           ← Statistics dashboard
│   ├── analyze_page.py        ← Article submission and results
│   ├── graph_page.py          ← Graph visualization + traversal
│   ├── history_page.py        ← Article history and search
│   ├── article_page.py        ← Detailed article view
│   ├── sources_page.py        ← Source statistics
│   ├── dsa_page.py            ← Interactive DSA demonstration
│   ├── timeline_page.py       ← Chronological timeline
│   └── components.py          ← Reusable UI widgets
│
└── utils/
    └── helpers.py             ← Utility functions
```

---

## Graph Implementation

### Representation
- **Type**: Directed Graph (DiGraph) via NetworkX
- **Internal representation**: Adjacency list (O(V + E) space)

### Nodes
Each node represents an analyzed news article:
```
Article ID → { headline, source, prediction, topic, pub_date, confidence }
```

### Edges (Relationships)
Each edge represents a relationship between articles:
```
Article A ─[SIMILAR_CONTENT, score=0.73]→ Article B
```

**Relationship types:**
| Type | Condition |
|---|---|
| `DUPLICATE` | Cosine similarity ≥ 0.85 or exact hash match |
| `SIMILAR_CONTENT` | Cosine similarity ≥ 0.40 |
| `SAME_TOPIC` | Same detected topic + Jaccard similarity ≥ 0.30 |
| `SAME_SOURCE` | Same publisher |
| `RELATED_KEYWORDS` | High keyword overlap |

### Graph Algorithms

**BFS (Breadth-First Search)**
```python
queue = deque([(start_node, 0)])
while queue:
    node, depth = queue.popleft()
    if depth < max_depth:
        for neighbor in graph.neighbors(node):
            if neighbor not in visited:
                queue.append((neighbor, depth + 1))
```
Time: O(V + E) | Space: O(V) | Data Structure: Queue (FIFO)

**DFS (Depth-First Search)**
```python
stack = [start_node]
while stack:
    node = stack.pop()
    if node not in visited:
        visited.add(node)
        for neighbor in graph.neighbors(node):
            stack.append(neighbor)
```
Time: O(V + E) | Space: O(V) | Data Structure: Stack (LIFO)

**Connected Components**
Apply BFS/DFS from each unvisited node. Each call discovers a new component.
Time: O(V + E)

---

## Hashing Implementation

### SHA-256 (Exact Duplicates)
```python
import hashlib
hash = hashlib.sha256(text.encode('utf-8')).hexdigest()  # 64-char hex string
```

**Normalization pipeline:**
1. Convert to lowercase
2. Remove URLs and special characters
3. Remove extra whitespace
4. Remove stop words (optional)

Two articles are **exact duplicates** if `hash(normalize(A)) == hash(normalize(B))`

### SimHash (Near-Duplicates)
```python
# For each token, compute hash and vote +1/-1 per bit position
# Final fingerprint: bit i = 1 if vector[i] > 0 else 0
# Similarity: 1 - hamming_distance(h1, h2) / bits
```

Hamming distance measures how many bits differ.
- Distance 0 = identical
- Distance < 6 = near-duplicate
- Distance > 15 = likely different

### Custom Hash Table (Keyword Index)
```python
class HashTable:
    # Polynomial rolling hash function
    def _hash(key): return sum(ord(c) * 31**i for i, c in enumerate(key)) % size
    
    # Separate chaining: each bucket = linked list of (key, value) pairs
    def insert(key, value): ...
    def lookup(key): ...  # O(1) average
```

---

## Machine Learning

**Pipeline**: TF-IDF → Logistic Regression

**TF-IDF**: Converts text to feature vectors.
- TF(t) = count(t) / total_tokens
- IDF(t) = log(N / df(t)) where N = total docs, df(t) = docs containing t
- TF-IDF(t) = TF × IDF

**Logistic Regression**: Binary classifier → probability of REAL/FAKE

**Thresholds**:
- P(REAL) ≥ 0.65 → **REAL**
- P(FAKE) ≥ 0.65 → **FAKE**
- Otherwise → **SUSPICIOUS**

**⚠️ DISCLAIMER**: Model trained on DEMO data only. NOT a reliable truth detector.

---

## Database Design

### Tables
```sql
articles (id, article_id, headline, content, source, pub_date,
          prediction, confidence, credibility_score, keywords,
          hash_headline, hash_content, hash_normalized, graph_node_id,
          is_duplicate, duplicate_of, similarity_score, topic, timestamp, word_count)

relationships (id, article_id_a, article_id_b, relationship_type,
               similarity_score, created_at)

sources (id, source_name, total_articles, real_count, fake_count,
         suspicious_count, duplicate_count, first_seen, last_seen)
```

---

## Installation

### Step 1: Create virtual environment (recommended)
```bash
python -m venv venv
venv\Scripts\activate
```

### Step 2: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Run the application
```bash
python main.py
```

The application will:
1. Initialize the SQLite database
2. Load the graph from stored data
3. Train the ML model (first run only, ~5 seconds)
4. Open the main window

---

## How to Run

```bash
python main.py
```

### Navigation
- **Ctrl+1** → Dashboard
- **Ctrl+2** → Analyze News
- **Ctrl+3** → News Graph
- **Ctrl+4** → History

---

## Screenshots

*(Add screenshots here after running the application)*

---

## DSA Concepts Demonstrated

| Concept | Location | Viva Points |
|---|---|---|
| Hashing | `hashing.py`, `hash_table.py` | SHA-256, normalization, collision handling |
| Hash Table | `hash_table.py` | Separate chaining, load factor, O(1) lookup |
| Graph | `graph_manager.py` | DiGraph, adjacency list, V+E |
| BFS | `graph_algorithms.py` | Queue, level-by-level traversal |
| DFS | `graph_algorithms.py` | Stack, deep traversal, backtracking |
| Connected Components | `graph_algorithms.py` | Cluster identification |
| TF-IDF | `text_processor.py`, `fake_news_model.py` | Term weighting |
| Cosine Similarity | `text_processor.py` | Vector similarity, dot product |

---

## Future Scope

1. **Real dataset**: Train on LIAR or FakeNewsNet datasets
2. **Web crawling**: Auto-fetch articles from RSS feeds
3. **Temporal analysis**: Track how fake news evolves over time
4. **NLP improvements**: Named entity recognition, sentiment analysis
5. **Graph enhancements**: PageRank for source credibility
6. **Export**: PDF/CSV export of analysis results
7. **Multi-language**: Extend to regional languages

---

## Important Note

> **All predictions in this application are SYSTEM ASSESSMENTS based on a DEMO MODEL trained on SAMPLE DATA. They are NOT verified ground truth determinations. This application is a college project for educational purposes only.**
