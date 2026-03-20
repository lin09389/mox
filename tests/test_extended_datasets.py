"""测试扩展评估数据集模块"""

import pytest
from mox.evaluation.extended_datasets import (
    PromptInjectDataset,
    SafetyBenchDataset,
    ExtendedDatasetLoader,
    BenchmarkDatasetType,
)


class TestPromptInjectDataset:
    """测试PromptInject数据集"""

    def test_load_samples(self):
        """测试加载样本"""
        dataset = PromptInjectDataset()
        assert len(dataset.samples) > 0

    def test_get_samples_all(self):
        """测试获取所有样本"""
        dataset = PromptInjectDataset()
        samples = dataset.get_samples()

        assert len(samples) > 0
        assert all(hasattr(s, "prompt") for s in samples)

    def test_get_samples_by_category(self):
        """测试按类别获取样本"""
        dataset = PromptInjectDataset()
        samples = dataset.get_samples(category="weapon_creation")

        assert all(s.category == "weapon_creation" for s in samples)

    def test_get_samples_by_severity(self):
        """测试按严重级别获取样本"""
        dataset = PromptInjectDataset()
        samples = dataset.get_samples(severity="critical")

        assert all(s.severity == "critical" for s in samples)

    def test_get_samples_with_limit(self):
        """测试限制样本数量"""
        dataset = PromptInjectDataset()
        samples = dataset.get_samples(limit=3)

        assert len(samples) <= 3

    def test_get_categories(self):
        """测试获取所有类别"""
        dataset = PromptInjectDataset()
        categories = dataset.get_categories()

        assert len(categories) > 0
        assert "weapon_creation" in categories

    def test_get_severities(self):
        """测试获取所有严重级别"""
        dataset = PromptInjectDataset()
        severities = dataset.get_severities()

        assert len(severities) > 0


class TestSafetyBenchDataset:
    """测试SafetyBench数据集"""

    def test_load_samples(self):
        """测试加载样本"""
        dataset = SafetyBenchDataset()
        assert len(dataset.samples) > 0

    def test_get_samples_all(self):
        """测试获取所有样本"""
        dataset = SafetyBenchDataset()
        samples = dataset.get_samples()

        assert len(samples) > 0

    def test_get_samples_by_label(self):
        """测试按标签获取样本"""
        dataset = SafetyBenchDataset()
        unsafe_samples = dataset.get_samples(label="unsafe")

        assert all(s.label == "unsafe" for s in unsafe_samples)

    def test_get_samples_by_difficulty(self):
        """测试按难度获取样本"""
        dataset = SafetyBenchDataset()
        samples = dataset.get_samples(difficulty="easy")

        assert all(s.difficulty == "easy" for s in samples)

    def test_get_categories(self):
        """测试获取所有类别"""
        dataset = SafetyBenchDataset()
        categories = dataset.get_categories()

        assert len(categories) > 0


class TestExtendedDatasetLoader:
    """测试扩展数据集加载器"""

    def test_load_promptinject_dataset(self):
        """测试加载PromptInject数据集"""
        loader = ExtendedDatasetLoader()
        samples = loader.load_dataset(BenchmarkDatasetType.PROMPTINJECT)

        assert len(samples) > 0
        assert "prompt" in samples[0]
        assert "category" in samples[0]

    def test_load_safetybench_dataset(self):
        """测试加载SafetyBench数据集"""
        loader = ExtendedDatasetLoader()
        samples = loader.load_dataset(BenchmarkDatasetType.SAFETYBENCH)

        assert len(samples) > 0
        assert "prompt" in samples[0]
        assert "category" in samples[0]
        assert "label" in samples[0]

    def test_load_with_filters(self):
        """测试带过滤条件加载"""
        loader = ExtendedDatasetLoader()

        samples = loader.load_dataset(
            BenchmarkDatasetType.PROMPTINJECT,
            severity="critical",
            limit=5,
        )

        assert len(samples) <= 5
        if samples:
            assert samples[0]["severity"] == "critical"

    def test_list_datasets(self):
        """测试列出所有数据集"""
        loader = ExtendedDatasetLoader()
        datasets = loader.list_datasets()

        assert len(datasets) > 0
        assert "promptinject" in datasets
        assert "safetybench" in datasets

    def test_load_invalid_dataset(self):
        """测试加载无效数据集"""
        loader = ExtendedDatasetLoader()

        with pytest.raises(ValueError):
            loader.load_dataset("invalid_type")
