"""基准数据集管理测试

验证以下功能:
1. 数据集加载
2. 数据集过滤
3. 数据集采样
4. 数据集统计
5. 数据集导出
"""

import pytest
import json
import tempfile
from pathlib import Path

from mox.evaluation.datasets import (
    DatasetFormat,
    DatasetMetadata,
    BenchmarkCase,
    HarmBenchCase,
    DatasetManager,
    get_dataset_manager,
    load_dataset,
    filter_dataset,
    sample_dataset,
    list_datasets,
    get_dataset_statistics,
)
from mox.core import AttackPayload, AttackType


class TestDatasetFormat:
    """测试数据集格式"""

    def test_formats(self):
        """测试数据集格式枚举"""
        assert DatasetFormat.JSON.value == "json"
        assert DatasetFormat.YAML.value == "yaml"
        assert DatasetFormat.CSV.value == "csv"
        assert DatasetFormat.INTERNAL.value == "internal"


class TestBenchmarkCase:
    """测试基准测试用例"""

    def test_case_creation(self):
        """测试用例创建"""
        case = BenchmarkCase(
            id="test_001",
            category="test",
            payload=AttackPayload(
                attack_type=AttackType.PROMPT_INJECTION,
                prompt="Test prompt",
                target_behavior="test behavior",
            ),
            expected_behavior="refusal",
            severity="high",
        )

        assert case.id == "test_001"
        assert case.category == "test"
        assert case.severity == "high"


class TestHarmBenchCase:
    """测试 HarmBench 用例"""

    def test_case_creation(self):
        """测试用例创建"""
        case = HarmBenchCase(
            id="hb_001",
            behavior="Test behavior",
            category="cyberattack",
            attack_type=AttackType.JAILBREAK,
            target_behavior="test_target",
            seed_prompts=["prompt1", "prompt2"],
        )

        assert case.id == "hb_001"
        assert case.category == "cyberattack"
        assert len(case.seed_prompts) == 2


class TestDatasetManager:
    """测试数据集管理器"""

    def test_manager_creation(self):
        """测试管理器创建"""
        manager = DatasetManager()
        assert manager is not None

    def test_list_datasets(self):
        """测试列出数据集"""
        manager = DatasetManager()
        datasets = manager.list_datasets()

        assert "advbench" in datasets
        assert "harmbench" in datasets
        assert "harmbench_standard" in datasets
        assert "defense_test" in datasets
        assert "jailbreakbench" in datasets
        assert "owasp_llm" in datasets

    def test_load_advbench(self):
        """测试加载 AdvBench"""
        manager = DatasetManager()
        dataset = manager.load("advbench")

        assert len(dataset) > 0
        assert all(isinstance(case, BenchmarkCase) for case in dataset)

    def test_load_harmbench(self):
        """测试加载 HarmBench"""
        manager = DatasetManager()
        dataset = manager.load("harmbench")

        assert len(dataset) > 0
        assert all(isinstance(case, BenchmarkCase) for case in dataset)

    def test_load_harmbench_standard(self):
        """测试加载 HarmBench Standard"""
        manager = DatasetManager()
        dataset = manager.load("harmbench_standard")

        assert len(dataset) > 0
        assert all(isinstance(case, HarmBenchCase) for case in dataset)

    def test_load_defense_test(self):
        """测试加载防御测试"""
        manager = DatasetManager()
        dataset = manager.load("defense_test")

        assert len(dataset) > 0
        assert all(isinstance(case, dict) for case in dataset)

    def test_load_jailbreakbench(self):
        """测试加载 JailbreakBench"""
        manager = DatasetManager()
        dataset = manager.load("jailbreakbench")

        assert len(dataset) > 0
        assert all(isinstance(prompt, str) for prompt in dataset)

    def test_load_owasp_llm(self):
        """测试加载 OWASP LLM"""
        manager = DatasetManager()
        dataset = manager.load("owasp_llm")

        assert len(dataset) > 0
        assert all(isinstance(case, BenchmarkCase) for case in dataset)

    def test_filter_by_category(self):
        """测试按类别过滤"""
        manager = DatasetManager()
        filtered = manager.filter("harmbench_standard", category="cyberattack")

        assert len(filtered) > 0
        assert all(case.category == "cyberattack" for case in filtered)

    def test_sample_dataset(self):
        """测试采样数据集"""
        manager = DatasetManager()
        sampled = manager.sample("harmbench_standard", n=3, seed=42)

        assert len(sampled) == 3

    def test_get_categories(self):
        """测试获取类别"""
        manager = DatasetManager()
        categories = manager.get_categories("harmbench_standard")

        assert len(categories) > 0
        assert "cyberattack" in categories

    def test_get_metadata(self):
        """测试获取元数据"""
        manager = DatasetManager()
        metadata = manager.get_metadata("advbench")

        assert metadata.name == "advbench"
        assert metadata.size > 0
        assert len(metadata.categories) > 0

    def test_get_statistics(self):
        """测试获取统计"""
        manager = DatasetManager()
        stats = manager.get_statistics("harmbench_standard")

        assert stats["name"] == "harmbench_standard"
        assert stats["total_cases"] > 0
        assert len(stats["categories"]) > 0

    def test_export_json(self):
        """测试导出 JSON"""
        manager = DatasetManager()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_path = f.name

        try:
            manager.export_dataset("advbench", output_path, format="json")

            with open(output_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            assert len(data) > 0
        finally:
            Path(output_path).unlink(missing_ok=True)


class TestConvenienceFunctions:
    """测试便捷函数"""

    def test_get_dataset_manager(self):
        """测试获取数据集管理器"""
        manager = get_dataset_manager()
        assert manager is not None

    def test_load_dataset(self):
        """测试加载数据集"""
        dataset = load_dataset("advbench")
        assert len(dataset) > 0

    def test_filter_dataset(self):
        """测试过滤数据集"""
        filtered = filter_dataset("harmbench_standard", category="cyberattack")
        assert len(filtered) > 0

    def test_sample_dataset(self):
        """测试采样数据集"""
        sampled = sample_dataset("harmbench_standard", n=3)
        assert len(sampled) == 3

    def test_list_datasets(self):
        """测试列出数据集"""
        datasets = list_datasets()
        assert len(datasets) > 0

    def test_get_dataset_statistics(self):
        """测试获取数据集统计"""
        stats = get_dataset_statistics("advbench")
        assert "name" in stats
        assert "total_cases" in stats


class TestModuleExports:
    """测试模块导出"""

    def test_imports(self):
        """测试导入"""
        from mox.evaluation.datasets import (
            DatasetFormat,
            DatasetMetadata,
            BenchmarkCase,
            HarmBenchCase,
            DatasetManager,
            get_dataset_manager,
            load_dataset,
            filter_dataset,
            sample_dataset,
            list_datasets,
            get_dataset_statistics,
        )

        assert DatasetFormat is not None
        assert DatasetMetadata is not None
        assert BenchmarkCase is not None
        assert HarmBenchCase is not None
        assert DatasetManager is not None
        assert get_dataset_manager is not None
        assert load_dataset is not None
        assert filter_dataset is not None
        assert sample_dataset is not None
        assert list_datasets is not None
        assert get_dataset_statistics is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
