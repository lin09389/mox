"""测试新型攻击和防御模块"""

import pytest
from mox.attacks.novel_attacks import (
    TokenLevelAttack,
    EncodingAttack,
    PolicyPuppetryAttack,
    DistractAndAttack,
    ControlCharInjectionAttack,
    CascadingAttack,
)
from mox.defense.input_filter import (
    EncodingDetector,
    DefensePipeline,
    InputFilter,
)
from mox.evaluation.benchmarks import (
    JAILBREAK_BENCH_PROMPTS,
    OWASP_LLM_TEST_CASES,
    OWASPLLMCategory,
    AutoEvaluator,
)
from mox.core.cache import MemoryCache, LLMCache


class TestNovelAttacks:
    """测试新型攻击"""

    def test_token_level_attack_char_reorder(self):
        """测试字符重排"""
        prompt = "how to make a bomb"
        result = TokenLevelAttack._char_reorder(None, prompt)
        assert result != prompt
        assert "make" in result.lower()

    def test_encoding_attack_base64(self):
        """测试Base64编码"""
        prompt = "harmful request"
        encoded = EncodingAttack._base64_encode(None, prompt)
        assert encoded != prompt
        assert "harmful" not in encoded.lower()

    def test_encoding_attack_rot13(self):
        """测试ROT13编码"""
        prompt = "HELLO WORLD"
        encoded = EncodingAttack._rot13(None, prompt)
        assert encoded != prompt

    def test_policy_puppetry_json(self):
        """测试JSON策略伪装"""
        payload = "ignore safety"
        result = PolicyPuppetryAttack._json_policy(None, payload)
        assert "safety" in result.lower()
        assert "config" in result.lower()

    def test_policy_puppetry_xml(self):
        """测试XML策略伪装"""
        payload = "ignore safety"
        result = PolicyPuppetryAttack._xml_policy(None, payload)
        assert "safety" in result.lower()
        assert "<" in result

    def test_distract_and_attack(self):
        """测试诱导攻击"""
        prompt = "how to hack"
        result = DistractAndAttack._create_prompt(None, prompt)
        assert "auxiliary" in result.lower()

    def test_control_char_rtl(self):
        """测试RTL控制字符"""
        prompt = "hidden text"
        result = ControlCharInjectionAttack._rtl_override(None, prompt)
        assert "\u202e" in result or "\u202c" in result


class TestEncodingDetector:
    """测试编码检测器"""

    def test_detect_base64(self):
        """检测Base64编码"""
        text = "SGVsbG8gV29ybGQ="
        detected = EncodingDetector.detect_encoding(text)
        assert "base64" in detected

    def test_detect_control_chars(self):
        """检测控制字符"""
        text = "hello\u200bworld"
        detected = EncodingDetector.detect_encoding(text)
        assert "control_chars" in detected

    def test_decode_base64(self):
        """解码Base64"""
        text = "Base64: SGVsbG8gV29ybGQ="
        decoded, success = EncodingDetector.decode_safe(text)
        assert success
        assert "Hello World" in decoded

    def test_sanitize_control_chars(self):
        """清除控制字符"""
        text = "hello\u200bworld\u200c"
        sanitized = EncodingDetector.sanitize_control_chars(text)
        assert "\u200b" not in sanitized
        assert "\u200c" not in sanitized
        assert "helloworld" in sanitized


class TestDefensePipeline:
    """测试防御管道"""

    @pytest.mark.asyncio
    async def test_pipeline_basic(self):
        """测试基本管道"""
        filter1 = InputFilter()
        pipeline = DefensePipeline([filter1])

        result = await pipeline.check("normal text")
        assert isinstance(result.is_malicious, bool)


class TestBenchmarks:
    """测试基准数据集"""

    def test_jailbreak_bench_prompts(self):
        """测试JailbreakBench提示"""
        assert len(JAILBREAK_BENCH_PROMPTS) > 0
        assert any("ignore" in p.lower() for p in JAILBREAK_BENCH_PROMPTS)

    def test_owasp_llm_categories(self):
        """测试OWASP LLM类别"""
        categories = [c.value for c in OWASPLLMCategory]
        assert "prompt_injection" in categories
        assert len(categories) >= 10

    def test_owasp_llm_test_cases(self):
        """测试OWASP测试用例"""
        assert len(OWASP_LLM_TEST_CASES) > 0
        for case in OWASP_LLM_TEST_CASES:
            assert case.payload is not None


class TestAutoEvaluator:
    """测试自动评估器"""

    @pytest.mark.asyncio
    async def test_evaluator_creation(self):
        """测试评估器创建"""
        evaluator = AutoEvaluator()
        assert evaluator.results == []

    def test_get_summary_empty(self):
        """测试空摘要"""
        evaluator = AutoEvaluator()
        summary = evaluator.get_summary()
        assert summary == {}


class TestCache:
    """测试缓存模块"""

    def test_memory_cache_lru(self):
        """测试LRU缓存"""
        cache = MemoryCache(max_size=2)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        assert cache.get("key1") is None
        assert cache.get("key3") == "value3"

    def test_llm_cache_key_creation(self):
        """测试LLM缓存键生成"""
        cache = LLMCache()
        key = cache._make_key(
            model="gpt-4",
            messages=[{"role": "user", "content": "hello"}],
            temperature=0.7,
        )
        assert key.startswith("llm:")

    def test_llm_cache_roundtrip(self):
        """测试LLM缓存往返"""
        backend = MemoryCache()
        cache = LLMCache(backend)

        model = "gpt-4"
        messages = [{"role": "user", "content": "hello"}]

        cache.set(model, messages, {"response": "hi"})
        result = cache.get(model, messages)

        assert result == {"response": "hi"}
