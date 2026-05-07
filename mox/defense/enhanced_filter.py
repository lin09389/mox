# Enhanced defense filter - compatibility alias module.
# Exports classes from input_filter under legacy names for backward compatibility.

from .input_filter import (
    InputFilter as EnhancedInputFilter,
    StatisticalAnomalyFilter,
    EnhancedDefenseConfig,
    MaliciousPattern,
    MALICIOUS_PATTERNS as ENHANCED_MALICIOUS_PATTERNS,
)


class SemanticDetector:
    """Semantic detector (placeholder)."""

    def __init__(self, threshold: float = 0.85):
        self.threshold = threshold


class StatisticalAnomalyDetector(StatisticalAnomalyFilter):
    """Statistical anomaly detector alias."""

    def __init__(self, anomaly_threshold: float = 2.0):
        super().__init__(threshold=anomaly_threshold)
        self.threshold = anomaly_threshold

    def _extract_features(self, text: str) -> dict:
        length = len(text)
        words = text.split()
        word_count = len(words)
        digit_ratio = sum(1 for c in text if c.isdigit()) / max(length, 1)
        upper_ratio = sum(1 for c in text if c.isupper()) / max(length, 1)
        special_ratio = sum(1 for c in text if not c.isalnum() and not c.isspace()) / max(length, 1)
        return {
            "length": length,
            "word_count": word_count,
            "digit_ratio": digit_ratio,
            "upper_ratio": upper_ratio,
            "special_ratio": special_ratio,
        }


class AdversarialSampleDetector:
    """Adversarial sample detector (placeholder)."""

    def __init__(self):
        import re

        self._suspicious_patterns = [
            (r"(.)\1{15,}", 0.8, "char_repeat"),
            (r"[^\w\s]{10,}", 0.7, "special_chars"),
        ]


class MultiLayerDefensePipeline:
    """Multi-layer defense pipeline (placeholder)."""

    def __init__(self):
        self.layers = []

    def add_layer(self, layer):
        self.layers.append(layer)


__all__ = [
    "EnhancedInputFilter",
    "EnhancedDefenseConfig",
    "SemanticDetector",
    "StatisticalAnomalyDetector",
    "AdversarialSampleDetector",
    "MultiLayerDefensePipeline",
    "MaliciousPattern",
    "ENHANCED_MALICIOUS_PATTERNS",
]
