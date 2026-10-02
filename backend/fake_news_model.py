"""
backend/fake_news_model.py
Machine Learning model for fake news detection.

Approach: TF-IDF Vectorization + Logistic Regression
- TF-IDF: Converts text to numerical vectors based on term frequency and rarity.
- Logistic Regression: A simple, interpretable binary classifier.

Why Logistic Regression?
- Fast training on small datasets
- Interpretable (weights show which words matter)
- No GPU required
- Works well with TF-IDF features

Disclaimer: This is a demonstration model trained on DEMO DATA.
It is NOT a reliable tool for determining truth or falsehood.
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Tuple, Optional, Dict, List
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.pipeline import Pipeline

# Model file paths
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "fake_news_model.pkl")
VECTORIZER_PATH = os.path.join(BASE_DIR, "models", "vectorizer.pkl")
PIPELINE_PATH = os.path.join(BASE_DIR, "models", "pipeline.pkl")
DATASET_PATH = os.path.join(BASE_DIR, "data", "news_dataset.csv")


class FakeNewsModel:
    """
    TF-IDF + Logistic Regression pipeline for fake news classification.

    Pipeline steps:
    1. TF-IDF Vectorizer: text → numerical feature matrix
    2. Logistic Regression: feature matrix → REAL/FAKE probability
    """

    def __init__(self):
        self.pipeline: Optional[Pipeline] = None
        self.is_trained: bool = False
        self.training_accuracy: float = 0.0
        self.label_mapping = {0: "FAKE", 1: "REAL"}

    def _build_pipeline(self) -> Pipeline:
        """
        Build the sklearn Pipeline.
        Pipelines chain transformers and estimators into a single object.
        """
        vectorizer = TfidfVectorizer(
            max_features=10000,    # Use top 10000 terms for richer vocabulary
            ngram_range=(1, 3),    # Unigrams, bigrams and trigrams
            stop_words='english',  # Remove English stop words
            min_df=1,              # Minimum document frequency
            max_df=0.95,           # Maximum document frequency (ignore very common)
            sublinear_tf=True      # Apply log normalization to TF
        )

        classifier = LogisticRegression(
            max_iter=2000,
            C=5.0,                 # Less regularization — works better on small balanced datasets
            solver='lbfgs',
            random_state=42,
            class_weight='balanced'  # Handles imbalanced real/fake class distribution
        )

        return Pipeline([
            ("tfidf", vectorizer),
            ("classifier", classifier)
        ])

    def train(self, dataset_path: str = None) -> Dict:
        """
        Train the model from a CSV dataset.

        Expected CSV format:
            text,label
            "Article content here","real"
            "Another article","fake"

        Returns a dict with training results.
        """
        if dataset_path is None:
            dataset_path = DATASET_PATH

        if not os.path.exists(dataset_path):
            return {"success": False, "error": f"Dataset not found at {dataset_path}"}

        try:
            # Load dataset
            df = pd.read_csv(dataset_path)
            df.columns = df.columns.str.strip().str.lower()

            if "text" not in df.columns or "label" not in df.columns:
                return {"success": False, "error": "Dataset must have 'text' and 'label' columns"}

            df = df.dropna(subset=["text", "label"])
            df["label"] = df["label"].str.strip().str.lower()

            # Encode labels: real=1, fake=0
            df["label_encoded"] = df["label"].apply(lambda x: 1 if x == "real" else 0)

            X = df["text"].tolist()
            y = df["label_encoded"].tolist()

            if len(X) < 4:
                return {"success": False, "error": "Need at least 4 samples for training"}

            # Split data (80% train, 20% test)
            test_size = min(0.2, max(2, int(len(X) * 0.2)) / len(X))
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42, stratify=y if len(set(y)) > 1 else None
            )

            # Build and train pipeline
            self.pipeline = self._build_pipeline()
            self.pipeline.fit(X_train, y_train)

            # Evaluate
            y_pred = self.pipeline.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            self.training_accuracy = accuracy
            self.is_trained = True

            # Save model
            self.save()

            return {
                "success": True,
                "accuracy": round(accuracy * 100, 1),
                "training_samples": len(X_train),
                "test_samples": len(X_test),
                "total_samples": len(X),
                "classes": list(set(df["label"].tolist()))
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def predict(self, text: str, headline: str = "") -> Dict:
        """
        Predict whether a given text is REAL, FAKE, or SUSPICIOUS.

        Returns a dict with:
        - prediction: "REAL", "FAKE", or "SUSPICIOUS"
        - confidence: float 0.0 to 1.0
        - fake_probability: probability of being fake
        - real_probability: probability of being real

        DISCLAIMER: This is a system assessment based on a DEMO model.
        It should NOT be used as a reliable truth-detection tool.
        """
        if not self.is_trained or self.pipeline is None:
            # Attempt to load model
            if not self.load():
                return {
                    "prediction": "UNKNOWN",
                    "confidence": 0.0,
                    "real_probability": 0.0,
                    "fake_probability": 0.0,
                    "error": "Model not trained. Please train the model first."
                }

        try:
            combined_text = f"{headline} {text}".strip()

            # Get probability estimates
            proba = self.pipeline.predict_proba([combined_text])[0]
            # proba[0] = P(FAKE), proba[1] = P(REAL)
            fake_prob = float(proba[0])
            real_prob = float(proba[1])

            # Determine prediction with SUSPICIOUS zone
            if real_prob >= 0.65:
                prediction = "REAL"
                confidence = real_prob
            elif fake_prob >= 0.65:
                prediction = "FAKE"
                confidence = fake_prob
            else:
                prediction = "SUSPICIOUS"
                confidence = max(real_prob, fake_prob)

            return {
                "prediction": prediction,
                "confidence": round(confidence, 4),
                "real_probability": round(real_prob, 4),
                "fake_probability": round(fake_prob, 4),
                "disclaimer": "System assessment based on DEMO model. Not a reliable truth indicator."
            }

        except Exception as e:
            return {
                "prediction": "UNKNOWN",
                "confidence": 0.0,
                "real_probability": 0.0,
                "fake_probability": 0.0,
                "error": str(e)
            }

    def save(self) -> bool:
        """Save the trained model pipeline to disk."""
        try:
            os.makedirs(os.path.dirname(PIPELINE_PATH), exist_ok=True)
            joblib.dump(self.pipeline, PIPELINE_PATH)
            return True
        except Exception as e:
            print(f"[MODEL] Save error: {e}")
            return False

    def load(self) -> bool:
        """Load a previously trained model from disk."""
        try:
            if os.path.exists(PIPELINE_PATH):
                self.pipeline = joblib.load(PIPELINE_PATH)
                self.is_trained = True
                return True
            return False
        except Exception as e:
            print(f"[MODEL] Load error: {e}")
            return False

    def get_important_features(self, text: str, top_n: int = 10) -> List[Tuple[str, float]]:
        """
        Return top features (words) that influenced the prediction.
        Provides explainability — WHY did the model make this prediction?
        """
        if not self.is_trained or self.pipeline is None:
            return []

        try:
            vectorizer = self.pipeline.named_steps["tfidf"]
            classifier = self.pipeline.named_steps["classifier"]

            # Transform text
            tfidf_matrix = vectorizer.transform([text])
            feature_names = vectorizer.get_feature_names_out()
            tfidf_array = tfidf_matrix.toarray()[0]

            # Get classifier coefficients for FAKE class (class 0)
            if hasattr(classifier, 'coef_'):
                coefs = classifier.coef_[0]
                # Combine TF-IDF weights with classifier coefficients
                scores = [(feature_names[i], tfidf_array[i] * abs(coefs[i]))
                          for i in range(len(feature_names)) if tfidf_array[i] > 0]
                scores.sort(key=lambda x: x[1], reverse=True)
                return scores[:top_n]
        except Exception as e:
            print(f"[MODEL] Feature extraction error: {e}")
        return []


# ─────────────────────────────────────────────
# Global model instance (singleton)
# ─────────────────────────────────────────────
_model_instance: Optional[FakeNewsModel] = None


def get_model() -> FakeNewsModel:
    """Get the global FakeNewsModel instance."""
    global _model_instance
    if _model_instance is None:
        _model_instance = FakeNewsModel()
        # Try to load pre-trained model
        _model_instance.load()
    return _model_instance


def ensure_model_trained() -> Dict:
    """
    Ensure the model is trained. Trains automatically if not found.
    Called on application startup.
    """
    model = get_model()
    if not model.is_trained:
        print("[MODEL] No trained model found. Training on demo dataset...")
        result = model.train()
        if result.get("success"):
            print(f"[MODEL] Training complete. Accuracy: {result.get('accuracy')}%")
        else:
            print(f"[MODEL] Training failed: {result.get('error')}")
        return result
    return {"success": True, "message": "Model already trained", "accuracy": model.training_accuracy * 100}
