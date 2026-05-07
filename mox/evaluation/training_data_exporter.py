"""训练数据导出模块

将安全测试结果导出为 DPO/RLHF 训练数据格式，支持：
- DPO (Direct Preference Optimization) 格式
- RLHF (PPO) 格式
- Safety-Tuning 格式
- 自定义 JSONL 格式
"""

from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import json
import hashlib

from mox.core.types import AttackOutcome, DefenseResult, ModelInfo
from mox.infrastructure.logging import get_logger

logger = get_logger("evaluation.training_data_exporter")


class TrainingDataFormat(str, Enum):
    """训练数据格式"""
    DPO = "dpo"
    RLHF = "rlhf"
    SAFETY_TUNING = "safety_tuning"
    CUSTOM_JSONL = "custom_jsonl"


@dataclass
class DPOExample:
    """DPO 训练样本"""
    prompt: str
    chosen: str
    rejected: str
    system: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prompt": self.prompt,
            "chosen": self.chosen,
            "rejected": self.rejected,
            "system": self.system,
            **self.metadata,
        }


@dataclass
class RLHFExample:
    """RLHF 训练样本"""
    prompt: str
    completion: str
    reward: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prompt": self.prompt,
            "completion": self.completion,
            "reward": self.reward,
            **self.metadata,
        }


@dataclass
class SafetyTuningExample:
    """安全微调训练样本"""
    instruction: str
    input_text: str
    output: str
    safe: bool
    attack_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "instruction": self.instruction,
            "input": self.input_text,
            "output": self.output,
            "safe": self.safe,
            "attack_type": self.attack_type,
            **self.metadata,
        }


class TrainingDataExporter:
    """训练数据导出器"""

    def __init__(self, model_info: Optional[ModelInfo] = None):
        self.model_info = model_info
        self._dpo_examples: List[DPOExample] = []
        self._rlhf_examples: List[RLHFExample] = []
        self._safety_examples: List[SafetyTuningExample] = []

    def add_attack_outcome(self, outcome: AttackOutcome) -> None:
        """从攻击结果生成训练样本"""
        if not outcome.response:
            return

        prompt = outcome.original_prompt or outcome.adversarial_prompt or ""
        response = outcome.response

        # DPO: 攻击成功 -> rejected, 防御成功 -> chosen
        if outcome.result.value == "success":
            # 攻击成功：对抗提示 -> 有害输出 (rejected)
            # 理想情况：拒绝回答 (chosen)
            dpo = DPOExample(
                prompt=prompt,
                chosen="我无法回答这个问题。",
                rejected=response,
                system="You are a helpful and harmless AI assistant.",
                metadata={
                    "attack_type": outcome.metadata.get("attack_type", "unknown"),
                    "success": True,
                    "model_name": self.model_info.model_name if self.model_info else None,
                },
            )
            self._dpo_examples.append(dpo)

            # RLHF: 攻击成功 -> 低奖励
            rlhf = RLHFExample(
                prompt=prompt,
                completion=response,
                reward=-1.0,
                metadata={
                    "attack_type": outcome.metadata.get("attack_type", "unknown"),
                    "success": True,
                },
            )
            self._rlhf_examples.append(rlhf)

            # Safety Tuning: 标记为不安全
            safety = SafetyTuningExample(
                instruction=prompt,
                input_text="",
                output=response,
                safe=False,
                attack_type=outcome.metadata.get("attack_type", "unknown"),
                metadata={
                    "model_name": self.model_info.model_name if self.model_info else None,
                },
            )
            self._safety_examples.append(safety)
        else:
            # 攻击失败/防御成功：安全输出 -> chosen
            dpo = DPOExample(
                prompt=prompt,
                chosen=response,
                rejected="",
                system="You are a helpful and harmless AI assistant.",
                metadata={
                    "attack_type": outcome.metadata.get("attack_type", "unknown"),
                    "success": False,
                    "model_name": self.model_info.model_name if self.model_info else None,
                },
            )
            self._dpo_examples.append(dpo)

            # RLHF: 防御成功 -> 高奖励
            rlhf = RLHFExample(
                prompt=prompt,
                completion=response,
                reward=1.0,
                metadata={
                    "attack_type": outcome.metadata.get("attack_type", "unknown"),
                    "success": False,
                },
            )
            self._rlhf_examples.append(rlhf)

            # Safety Tuning: 标记为安全
            safety = SafetyTuningExample(
                instruction=prompt,
                input_text="",
                output=response,
                safe=True,
                attack_type=outcome.metadata.get("attack_type", "unknown"),
                metadata={
                    "model_name": self.model_info.model_name if self.model_info else None,
                },
            )
            self._safety_examples.append(safety)

    def add_defense_result(self, result: DefenseResult, original_prompt: str, model_response: str) -> None:
        """从防御结果生成训练样本"""
        if result.is_malicious:
            # 输入被判定为恶意 -> 理想输出是拒绝
            dpo = DPOExample(
                prompt=original_prompt,
                chosen="我无法回答这个问题。",
                rejected=model_response,
                system="You are a helpful and harmless AI assistant.",
                metadata={
                    "defense_type": result.metadata.get("defense_type", "unknown"),
                    "confidence": result.confidence,
                    "model_name": self.model_info.model_name if self.model_info else None,
                },
            )
            self._dpo_examples.append(dpo)

            safety = SafetyTuningExample(
                instruction=original_prompt,
                input_text="",
                output=model_response,
                safe=False,
                attack_type=result.metadata.get("attack_type", "unknown"),
                metadata={
                    "defense_triggered": True,
                    "confidence": result.confidence,
                },
            )
            self._safety_examples.append(safety)
        else:
            # 输入安全 -> 正常回答
            safety = SafetyTuningExample(
                instruction=original_prompt,
                input_text="",
                output=model_response,
                safe=True,
                metadata={
                    "defense_triggered": False,
                    "confidence": result.confidence,
                },
            )
            self._safety_examples.append(safety)

    def export(
        self,
        format: TrainingDataFormat,
        output_path: str,
        include_metadata: bool = True,
    ) -> str:
        """导出训练数据到文件"""
        if format == TrainingDataFormat.DPO:
            return self._export_dpo(output_path, include_metadata)
        elif format == TrainingDataFormat.RLHF:
            return self._export_rlhf(output_path, include_metadata)
        elif format == TrainingDataFormat.SAFETY_TUNING:
            return self._export_safety_tuning(output_path, include_metadata)
        elif format == TrainingDataFormat.CUSTOM_JSONL:
            return self._export_custom_jsonl(output_path)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _export_dpo(self, output_path: str, include_metadata: bool) -> str:
        """导出 DPO 格式"""
        data = []
        for ex in self._dpo_examples:
            item = {
                "prompt": ex.prompt,
                "chosen": ex.chosen,
                "rejected": ex.rejected,
            }
            if include_metadata:
                item["system"] = ex.system
                item.update(ex.metadata)
            data.append(item)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Exported {len(data)} DPO examples to {output_path}")
        return output_path

    def _export_rlhf(self, output_path: str, include_metadata: bool) -> str:
        """导出 RLHF 格式"""
        data = []
        for ex in self._rlhf_examples:
            item = {
                "prompt": ex.prompt,
                "completion": ex.completion,
                "reward": ex.reward,
            }
            if include_metadata:
                item.update(ex.metadata)
            data.append(item)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Exported {len(data)} RLHF examples to {output_path}")
        return output_path

    def _export_safety_tuning(self, output_path: str, include_metadata: bool) -> str:
        """导出 Safety Tuning 格式"""
        data = []
        for ex in self._safety_examples:
            item = {
                "instruction": ex.instruction,
                "input": ex.input_text,
                "output": ex.output,
                "safe": ex.safe,
            }
            if include_metadata:
                item["attack_type"] = ex.attack_type
                item.update(ex.metadata)
            data.append(item)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Exported {len(data)} safety tuning examples to {output_path}")
        return output_path

    def _export_custom_jsonl(self, output_path: str) -> str:
        """导出自定义 JSONL 格式 (合并所有类型)"""
        with open(output_path, "w", encoding="utf-8") as f:
            # DPO samples
            for ex in self._dpo_examples:
                record = {
                    "format": "dpo",
                    **ex.to_dict(),
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

            # RLHF samples
            for ex in self._rlhf_examples:
                record = {
                    "format": "rlhf",
                    **ex.to_dict(),
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

            # Safety tuning samples
            for ex in self._safety_examples:
                record = {
                    "format": "safety_tuning",
                    **ex.to_dict(),
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

        total = len(self._dpo_examples) + len(self._rlhf_examples) + len(self._safety_examples)
        logger.info(f"Exported {total} examples to {output_path}")
        return output_path

    def get_statistics(self) -> Dict[str, Any]:
        """获取导出数据统计"""
        safe_count = sum(1 for ex in self._safety_examples if ex.safe)
        unsafe_count = len(self._safety_examples) - safe_count

        return {
            "dpo_examples": len(self._dpo_examples),
            "rlhf_examples": len(self._rlhf_examples),
            "safety_examples": len(self._safety_examples),
            "safe_count": safe_count,
            "unsafe_count": unsafe_count,
            "model_info": self.model_info.model_dump() if self.model_info else None,
            "generated_at": datetime.now().isoformat(),
        }

    def generate_dataset_card(self) -> str:
        """生成数据集卡片 (HuggingFace 格式)"""
        stats = self.get_statistics()

        card = f"""---
license: mit
task_categories:
- text-generation
- reinforcement-learning
language:
- zh
- en
size_categories:
- {self._size_category(stats['safety_examples'])}
---

# Mox Safety Training Dataset

This dataset was generated by [Mox](https://github.com/mox-ai/mox) for safety alignment of large language models.

## Dataset Description

- **DPO Examples**: {stats['dpo_examples']}
- **RLHF Examples**: {stats['rlhf_examples']}
- **Safety Tuning Examples**: {stats['safety_examples']}
- **Safe Responses**: {stats['safe_count']}
- **Unsafe Responses**: {stats['unsafe_count']}

## Model Information

```json
{json.dumps(stats['model_info'], indent=2, ensure_ascii=False)}
```

## Usage

### DPO Training

```python
from datasets import load_dataset

dataset = load_dataset("json", data_files="dpo_data.json")
```

### Safety Tuning

```python
from datasets import load_dataset

dataset = load_dataset("json", data_files="safety_tuning_data.json")
```

## Citation

If you use this dataset in your research, please cite the Mox project.
"""
        return card

    @staticmethod
    def _size_category(n: int) -> str:
        if n < 1000:
            return "n<1K"
        elif n < 10000:
            return "1K<n<10K"
        elif n < 100000:
            return "10K<n<100K"
        else:
            return "100K<n<1M"


# ============ 导出 ============

__all__ = [
    "TrainingDataFormat",
    "DPOExample",
    "RLHFExample",
    "SafetyTuningExample",
    "TrainingDataExporter",
]
