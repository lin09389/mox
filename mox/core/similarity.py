"""Unified similarity and scoring utilities.

Consolidates word overlap, cosine similarity, and semantic similarity
calculations previously duplicated across:
- attacks/evaluation.py (keyword overlap)
- evaluation/attack_evaluator.py (keyword overlap, cosine similarity)
- evaluation/multi_dim_evaluator.py (word overlap, cosine similarity)
"""

import math
from typing import Optional, List, Dict


def word_overlap_score(response: str, target: str) -> float:
    """Calculate keyword overlap ratio between response and target.

    This is the unified version of the word overlap calculation that was
    duplicated in 3+ files. Computes the fraction of target keywords
    found in the response.

    Args:
        response: The model's response text.
        target: The target behavior description.

    Returns:
        Float between 0.0 and 1.0 representing overlap ratio.
    """
    if not target or not response:
        return 0.0

    target_words = set(target.lower().split())
    if not target_words:
        return 0.0

    response_words = set(response.lower().split())
    overlap = target_words & response_words

    return len(overlap) / len(target_words)


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Calculate cosine similarity between two vectors.

    Unified version that was duplicated in attack_evaluator.py and
    multi_dim_evaluator.py.

    Args:
        vec_a: First vector.
        vec_b: Second vector.

    Returns:
        Float between -1.0 and 1.0. Returns 0.0 for zero vectors.
    """
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot_product / (norm_a * norm_b)


def semantic_similarity(
    text_a: str,
    text_b: str,
    model=None,
    model_name: str = "all-MiniLM-L6-v2",
) -> float:
    """Calculate semantic similarity between two texts using embeddings.

    Uses sentence-transformers if available, falls back to word overlap.

    Args:
        text_a: First text.
        text_b: Second text.
        model: Optional pre-loaded SentenceTransformer model.
        model_name: Model name to load if model is None.

    Returns:
        Float between 0.0 and 1.0.
    """
    if not text_a or not text_b:
        return 0.0

    if model is not None:
        try:
            embeddings = model.encode([text_a, text_b])
            if hasattr(embeddings, "numpy"):
                import numpy as np

                embeddings = np.array(embeddings)
            sim = cosine_similarity(embeddings[0].tolist(), embeddings[1].tolist())
            return max(0.0, sim)
        except Exception:
            pass

    try:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(model_name)
        embeddings = _model.encode([text_a, text_b])
        import numpy as np

        embeddings_np = np.array(embeddings)
        sim = cosine_similarity(embeddings_np[0].tolist(), embeddings_np[1].tolist())
        return max(0.0, sim)
    except (ImportError, OSError):
        return word_overlap_score(text_a, text_b)


class SimilarityCalculator:
    """Cached similarity calculator for repeated comparisons.

    Lazily loads the sentence-transformers model and caches embeddings.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self._cache: Dict[str, List[float]] = {}

    def _ensure_model(self):
        if self._model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        except (ImportError, OSError):
            self._model = None

    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding for text, with caching."""
        if text in self._cache:
            return self._cache[text]

        self._ensure_model()
        if self._model is None:
            return None

        try:
            emb = self._model.encode(text)
            import numpy as np

            if isinstance(emb, np.ndarray):
                emb = emb.tolist()
            self._cache[text] = emb
            return emb
        except Exception:
            return None

    def similarity(self, text_a: str, text_b: str) -> float:
        """Calculate semantic similarity with caching."""
        emb_a = self.get_embedding(text_a)
        emb_b = self.get_embedding(text_b)

        if emb_a is not None and emb_b is not None:
            return cosine_similarity(emb_a, emb_b)

        return word_overlap_score(text_a, text_b)

    def clear_cache(self):
        self._cache.clear()
