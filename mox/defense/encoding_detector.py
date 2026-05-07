"""编码检测器 - 兼容旧测试的模块

提供 EncodingDetector 和 DefensePipeline 类。
"""

import base64
import re
import unicodedata
from typing import List, Tuple


class EncodingDetector:
    """编码和混淆检测器"""

    CONTROL_CHARS = {
        "\u200b",  # zero width space
        "\u200c",  # zero width non-joiner
        "\u200d",  # zero width joiner
        "\u202a",  # left-to-right embedding
        "\u202b",  # right-to-left embedding
        "\u202c",  # pop directional formatting
        "\u202d",  # left-to-right override
        "\u202e",  # right-to-left override
        "\u202f",  # narrow no-break space
        "\ufeff",  # zero width no-break space
    }

    @classmethod
    def detect_encoding(cls, text: str) -> List[str]:
        detected = []
        if re.search(r"[A-Za-z0-9+/]{8,}={0,2}", text.strip()) and re.search(r"[A-Za-z0-9+/]{8,}", text.strip()):
            try:
                candidates = re.findall(r"[A-Za-z0-9+/]{8,}={0,2}", text.strip())
                for c in candidates:
                    if len(c) >= 8:
                        decoded = base64.b64decode(c).decode("utf-8", errors="strict")
                        if decoded.isprintable() or all(ch.isprintable() or ch in "\n\r\t" for ch in decoded):
                            detected.append("base64")
                            break
            except Exception:
                pass
        if any(c in text for c in cls.CONTROL_CHARS):
            detected.append("control_chars")
        if "%" in text and re.search(r"%[0-9A-Fa-f]{2}", text):
            detected.append("url_encoded")
        return detected

    @classmethod
    def decode_safe(cls, text: str) -> Tuple[str, bool]:
        candidates = re.findall(r"[A-Za-z0-9+/]{8,}={0,2}", text)
        candidates.sort(key=len, reverse=True)
        for c in candidates:
            try:
                decoded = base64.b64decode(c).decode("utf-8", errors="strict")
                if decoded.isprintable() or all(ch.isprintable() or ch in "\n\r\t" for ch in decoded):
                    return decoded, True
            except Exception:
                continue
        return text, False

    @classmethod
    def sanitize_control_chars(cls, text: str) -> str:
        """清除控制字符"""
        for c in cls.CONTROL_CHARS:
            text = text.replace(c, "")
        return text


class DefensePipeline:
    """防御管道"""

    def __init__(self, layers: List = None):
        self.layers = layers or []

    async def check(self, text: str):
        """逐层检查输入"""
        from mox.defense.base import DefenseResult

        is_malicious = False
        confidence = 0.0
        detected = []
        for layer in self.layers:
            result = await layer.detect(text)
            if result.is_malicious:
                is_malicious = True
                confidence = max(confidence, result.confidence)
                detected.extend(result.detected_patterns or [])
        return DefenseResult(
            is_malicious=is_malicious,
            confidence=confidence,
            detected_patterns=detected,
        )
