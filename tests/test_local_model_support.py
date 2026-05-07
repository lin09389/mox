"""本地模型安全测试支持验证

验证内容:
1. HuggingFaceLLM 模型加载与属性访问
2. ModelInfo 序列化与反序列化
3. SafetyCard 模型指纹信息展示
4. TrainingDataExporter 数据导出
5. 配置项读取
"""

import json
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from mox.core.types import ModelInfo, AttackOutcome, DefenseResult, EvaluationReport, AttackResult, ThreatLevel
from mox.evaluation.safety_card import ModelSafetyCard, SafetyCardGenerator, SafetyTestResult, SafetyCategory
from mox.evaluation.training_data_exporter import (
    TrainingDataExporter,
    TrainingDataFormat,
    DPOExample,
    RLHFExample,
    SafetyTuningExample,
)
from mox.infrastructure.config import Settings


# ============ ModelInfo Tests ============

class TestModelInfo:
    def test_model_info_creation(self):
        info = ModelInfo(
            model_name="qwen2.5-7b",
            model_path="/models/qwen2.5-7b",
            base_model="Qwen/Qwen2.5-7B-Instruct",
            adapter_path="/adapters/lora-v1",
            checkpoint="checkpoint-500",
            quantization="4bit",
            torch_dtype="bfloat16",
            device_map="auto",
            model_hash="abc123" * 8,
        )
        assert info.model_name == "qwen2.5-7b"
        assert info.quantization == "4bit"
        assert info.model_hash == "abc123" * 8

    def test_model_info_serialization(self):
        info = ModelInfo(model_name="test-model", model_path="/path/to/model")
        data = info.model_dump()
        assert data["model_name"] == "test-model"
        assert data["model_path"] == "/path/to/model"
        assert data["base_model"] is None

    def test_model_info_from_dict(self):
        data = {
            "model_name": "llama3-8b",
            "quantization": "8bit",
            "torch_dtype": "float16",
        }
        info = ModelInfo(**data)
        assert info.model_name == "llama3-8b"
        assert info.quantization == "8bit"


# ============ AttackOutcome / DefenseResult / EvaluationReport with ModelInfo ============

class TestOutcomeWithModelInfo:
    def test_attack_outcome_with_model_info(self):
        model_info = ModelInfo(model_name="test-model")
        outcome = AttackOutcome(
            result=AttackResult.SUCCESS,
            success_score=0.9,
            model_info=model_info,
        )
        assert outcome.model_info.model_name == "test-model"
        assert outcome.is_successful is True

    def test_defense_result_with_model_info(self):
        model_info = ModelInfo(model_name="test-model")
        result = DefenseResult(
            is_malicious=True,
            confidence=0.95,
            model_info=model_info,
        )
        assert result.model_info.model_name == "test-model"
        assert result.is_safe is False

    def test_evaluation_report_with_model_info(self):
        model_info = ModelInfo(model_name="test-model")
        report = EvaluationReport(
            total_attacks=10,
            successful_attacks=3,
            failed_attacks=7,
            attack_success_rate=0.3,
            defense_success_rate=0.7,
            avg_iterations=5.0,
            model_info=model_info,
        )
        assert report.model_info.model_name == "test-model"
        assert "Total: 10" in report.summary


# ============ SafetyCard with ModelInfo ============

class TestSafetyCardModelInfo:
    def test_safety_card_with_model_info(self):
        model_info = ModelInfo(
            model_name="qwen2.5-7b",
            model_path="/models/qwen2.5-7b",
            base_model="Qwen/Qwen2.5-7B-Instruct",
            quantization="4bit",
        )
        card = ModelSafetyCard(
            model_name="qwen2.5-7b",
            model_version="v1.0",
            provider="huggingface",
            model_info=model_info,
        )
        data = card.to_dict()
        assert data["model_name"] == "qwen2.5-7b"
        assert "model_info" in data
        assert data["model_info"]["model_path"] == "/models/qwen2.5-7b"
        assert data["model_info"]["quantization"] == "4bit"

    def test_safety_card_without_model_info(self):
        card = ModelSafetyCard(
            model_name="gpt-4",
            model_version="2024-01",
            provider="openai",
        )
        data = card.to_dict()
        assert "model_info" not in data

    def test_safety_card_markdown_with_model_info(self):
        model_info = ModelInfo(
            model_name="qwen2.5-7b",
            model_path="/models/qwen2.5-7b",
            base_model="Qwen/Qwen2.5-7B-Instruct",
            quantization="4bit",
            torch_dtype="bfloat16",
        )
        card = ModelSafetyCard(
            model_name="qwen2.5-7b",
            model_version="v1.0",
            provider="huggingface",
            model_info=model_info,
        )
        md = card.to_markdown()
        assert "模型指纹信息" in md
        assert "/models/qwen2.5-7b" in md
        assert "4bit" in md
        assert "bfloat16" in md

    def test_safety_card_markdown_without_model_info(self):
        card = ModelSafetyCard(
            model_name="gpt-4",
            model_version="2024-01",
            provider="openai",
        )
        md = card.to_markdown()
        assert "模型指纹信息" not in md

    @pytest.mark.asyncio
    async def test_safety_card_generator_with_model_info(self):
        generator = SafetyCardGenerator()
        model_info = ModelInfo(model_name="test-model", model_path="/path")
        card = await generator.generate(
            model_name="test-model",
            model_version="v1",
            provider="huggingface",
            model_info=model_info,
        )
        assert card.model_info is not None
        assert card.model_info.model_path == "/path"


# ============ TrainingDataExporter Tests ============

class TestTrainingDataExporter:
    def test_add_attack_outcome_success(self):
        exporter = TrainingDataExporter()
        outcome = AttackOutcome(
            result=AttackResult.SUCCESS,
            success_score=0.9,
            original_prompt="test prompt",
            response="harmful response",
            metadata={"attack_type": "jailbreak"},
        )
        exporter.add_attack_outcome(outcome)
        stats = exporter.get_statistics()
        assert stats["dpo_examples"] == 1
        assert stats["rlhf_examples"] == 1
        assert stats["safety_examples"] == 1
        assert stats["unsafe_count"] == 1

    def test_add_attack_outcome_failure(self):
        exporter = TrainingDataExporter()
        outcome = AttackOutcome(
            result=AttackResult.FAILURE,
            success_score=0.1,
            original_prompt="test prompt",
            response="safe response",
            metadata={"attack_type": "prompt_injection"},
        )
        exporter.add_attack_outcome(outcome)
        stats = exporter.get_statistics()
        assert stats["safe_count"] == 1
        assert stats["unsafe_count"] == 0

    def test_add_defense_result_malicious(self):
        exporter = TrainingDataExporter()
        result = DefenseResult(
            is_malicious=True,
            confidence=0.95,
            metadata={"defense_type": "input_filter"},
        )
        exporter.add_defense_result(result, "bad prompt", "bad response")
        stats = exporter.get_statistics()
        assert stats["dpo_examples"] == 1
        assert stats["safety_examples"] == 1
        assert stats["unsafe_count"] == 1

    def test_export_dpo(self, tmp_path):
        exporter = TrainingDataExporter()
        outcome = AttackOutcome(
            result=AttackResult.SUCCESS,
            success_score=0.9,
            original_prompt="prompt",
            response="response",
            metadata={"attack_type": "jailbreak"},
        )
        exporter.add_attack_outcome(outcome)
        output = tmp_path / "dpo.json"
        exporter.export(TrainingDataFormat.DPO, str(output))
        assert output.exists()
        data = json.loads(output.read_text(encoding="utf-8"))
        assert len(data) == 1
        assert "prompt" in data[0]
        assert "chosen" in data[0]
        assert "rejected" in data[0]

    def test_export_rlhf(self, tmp_path):
        exporter = TrainingDataExporter()
        outcome = AttackOutcome(
            result=AttackResult.SUCCESS,
            success_score=0.9,
            original_prompt="prompt",
            response="response",
        )
        exporter.add_attack_outcome(outcome)
        output = tmp_path / "rlhf.json"
        exporter.export(TrainingDataFormat.RLHF, str(output))
        data = json.loads(output.read_text(encoding="utf-8"))
        assert len(data) == 1
        assert data[0]["reward"] == -1.0

    def test_export_safety_tuning(self, tmp_path):
        exporter = TrainingDataExporter()
        outcome = AttackOutcome(
            result=AttackResult.FAILURE,
            success_score=0.1,
            original_prompt="prompt",
            response="safe response",
        )
        exporter.add_attack_outcome(outcome)
        output = tmp_path / "safety.json"
        exporter.export(TrainingDataFormat.SAFETY_TUNING, str(output))
        data = json.loads(output.read_text(encoding="utf-8"))
        assert len(data) == 1
        assert data[0]["safe"] is True

    def test_export_custom_jsonl(self, tmp_path):
        exporter = TrainingDataExporter()
        outcome = AttackOutcome(
            result=AttackResult.SUCCESS,
            success_score=0.9,
            original_prompt="prompt",
            response="response",
        )
        exporter.add_attack_outcome(outcome)
        output = tmp_path / "data.jsonl"
        exporter.export(TrainingDataFormat.CUSTOM_JSONL, str(output))
        lines = output.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 3  # dpo + rlhf + safety

    def test_dataset_card_generation(self):
        exporter = TrainingDataExporter(
            model_info=ModelInfo(model_name="test-model")
        )
        outcome = AttackOutcome(
            result=AttackResult.SUCCESS,
            success_score=0.9,
            original_prompt="prompt",
            response="response",
        )
        exporter.add_attack_outcome(outcome)
        card = exporter.generate_dataset_card()
        assert "Mox Safety Training Dataset" in card
        assert "test-model" in card

    def test_statistics_with_model_info(self):
        model_info = ModelInfo(model_name="qwen2.5-7b")
        exporter = TrainingDataExporter(model_info=model_info)
        stats = exporter.get_statistics()
        assert stats["model_info"]["model_name"] == "qwen2.5-7b"


# ============ Configuration Tests ============

class TestLocalModelConfig:
    def test_settings_local_model_fields(self):
        """验证配置中有本地模型相关字段"""
        settings = Settings()
        # 这些字段应该存在（有默认值）
        assert hasattr(settings, "LOCAL_MODEL_PATH")
        assert hasattr(settings, "LORA_ADAPTER_PATH")
        assert hasattr(settings, "LOAD_IN_4BIT")
        assert hasattr(settings, "LOAD_IN_8BIT")
        assert hasattr(settings, "DEVICE_MAP")
        assert hasattr(settings, "TORCH_DTYPE")

    def test_settings_defaults(self):
        settings = Settings()
        assert settings.LOCAL_MODEL_PATH is None
        assert settings.LOAD_IN_4BIT is False
        assert settings.LOAD_IN_8BIT is False
        assert settings.DEVICE_MAP == "auto"
        assert settings.TORCH_DTYPE == "bfloat16"


# ============ HuggingFaceLLM Import Test ============

class TestHuggingFaceLLMImport:
    def test_huggingface_llm_importable(self):
        """验证 HuggingFaceLLM 可以正确导入"""
        from mox.core.llm import HuggingFaceLLM
        assert HuggingFaceLLM is not None

    def test_huggingface_llm_in_factory(self):
        """验证 LLMFactory 支持 HUGGINGFACE provider"""
        from mox.core.llm import LLMFactory, ModelProvider
        assert hasattr(ModelProvider, "HUGGINGFACE")


# ============ Integration-style Tests ============

class TestEndToEndLocalModelFlow:
    def test_model_info_flow_through_evaluation(self):
        """验证 ModelInfo 可以在评估流程中传递"""
        model_info = ModelInfo(
            model_name="qwen2.5-7b",
            model_path="/models/qwen2.5-7b",
            quantization="4bit",
        )

        # 攻击结果携带模型信息
        outcome = AttackOutcome(
            result=AttackResult.SUCCESS,
            success_score=0.8,
            model_info=model_info,
        )

        # 评估报告携带模型信息
        report = EvaluationReport(
            total_attacks=1,
            successful_attacks=1,
            failed_attacks=0,
            attack_success_rate=1.0,
            defense_success_rate=0.0,
            avg_iterations=1.0,
            detailed_results=[outcome],
            model_info=model_info,
        )

        # 安全卡片携带模型信息
        card = ModelSafetyCard(
            model_name="qwen2.5-7b",
            model_version="v1",
            provider="huggingface",
            model_info=model_info,
        )

        assert report.model_info.quantization == "4bit"
        assert card.to_dict()["model_info"]["quantization"] == "4bit"

    def test_training_data_exporter_with_model_info(self):
        """验证 TrainingDataExporter 可以携带模型信息导出"""
        model_info = ModelInfo(model_name="test-model")
        exporter = TrainingDataExporter(model_info=model_info)

        outcome = AttackOutcome(
            result=AttackResult.SUCCESS,
            success_score=0.9,
            original_prompt="prompt",
            response="response",
        )
        exporter.add_attack_outcome(outcome)

        stats = exporter.get_statistics()
        assert stats["model_info"]["model_name"] == "test-model"
