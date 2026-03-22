"""评估模块 - 攻防效果评估"""

from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import json

from mox.core import (
    AttackOutcome,
    AttackResult,
    DefenseResult,
    EvaluationReport,
    AttackType,
)


@dataclass
class EvaluationMetrics:
    attack_success_rate: float = 0.0
    defense_success_rate: float = 0.0
    avg_iterations: float = 0.0
    avg_response_time: float = 0.0
    total_tests: int = 0
    successful_attacks: int = 0
    failed_attacks: int = 0
    blocked_attacks: int = 0


@dataclass
class AttackTypeMetrics:
    attack_type: AttackType
    total: int = 0
    successful: int = 0
    failed: int = 0
    success_rate: float = 0.0
    avg_iterations: float = 0.0


class AttackEvaluator:
    """攻击效果评估器"""

    def __init__(self):
        self.results: List[AttackOutcome] = []
        self.metrics_by_type: Dict[AttackType, AttackTypeMetrics] = {}

    def add_result(self, outcome: AttackOutcome) -> None:
        self.results.append(outcome)
        self._update_metrics(outcome)

    def _update_metrics(self, outcome: AttackOutcome) -> None:
        attack_type = outcome.metadata.get("attack_type", AttackType.PROMPT_INJECTION)
        if isinstance(attack_type, str):
            try:
                attack_type = AttackType(attack_type)
            except ValueError:
                attack_type = AttackType.PROMPT_INJECTION

        if attack_type not in self.metrics_by_type:
            self.metrics_by_type[attack_type] = AttackTypeMetrics(attack_type=attack_type)

        metrics = self.metrics_by_type[attack_type]
        metrics.total += 1

        if outcome.result == AttackResult.SUCCESS:
            metrics.successful += 1
        else:
            metrics.failed += 1

        metrics.success_rate = metrics.successful / metrics.total if metrics.total > 0 else 0.0

        total_iterations = sum(
            r.iterations for r in self.results if r.metadata.get("attack_type") == attack_type
        )
        metrics.avg_iterations = total_iterations / metrics.total if metrics.total > 0 else 0.0

    def get_overall_metrics(self) -> EvaluationMetrics:
        if not self.results:
            return EvaluationMetrics()

        total = len(self.results)
        successful = sum(1 for r in self.results if r.result == AttackResult.SUCCESS)
        failed = total - successful

        return EvaluationMetrics(
            attack_success_rate=successful / total if total > 0 else 0.0,
            defense_success_rate=failed / total if total > 0 else 0.0,
            avg_iterations=sum(r.iterations for r in self.results) / total,
            total_tests=total,
            successful_attacks=successful,
            failed_attacks=failed,
            blocked_attacks=failed,
        )

    def get_metrics_by_type(self) -> Dict[str, AttackTypeMetrics]:
        return {metrics.attack_type.value: metrics for metrics in self.metrics_by_type.values()}

    def generate_report(self) -> EvaluationReport:
        overall = self.get_overall_metrics()

        return EvaluationReport(
            total_attacks=overall.total_tests,
            successful_attacks=overall.successful_attacks,
            failed_attacks=overall.failed_attacks,
            attack_success_rate=overall.attack_success_rate,
            defense_success_rate=overall.defense_success_rate,
            avg_iterations=overall.avg_iterations,
            detailed_results=self.results,
        )

    def export_results(self, filepath: str) -> None:
        data = {
            "timestamp": datetime.now().isoformat(),
            "overall_metrics": {
                "attack_success_rate": self.get_overall_metrics().attack_success_rate,
                "defense_success_rate": self.get_overall_metrics().defense_success_rate,
                "total_tests": len(self.results),
            },
            "metrics_by_type": {
                k: {
                    "total": v.total,
                    "successful": v.successful,
                    "failed": v.failed,
                    "success_rate": v.success_rate,
                    "avg_iterations": v.avg_iterations,
                }
                for k, v in self.get_metrics_by_type().items()
            },
            "detailed_results": [
                {
                    "result": r.result.value,
                    "original_prompt": r.original_prompt,
                    "adversarial_prompt": r.adversarial_prompt,
                    "model_response": r.model_response[:500] + "..."
                    if len(r.model_response) > 500
                    else r.model_response,
                    "iterations": r.iterations,
                    "success_score": r.success_score,
                    "timestamp": r.timestamp.isoformat(),
                }
                for r in self.results
            ],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


class DefenseEvaluator:
    """防御效果评估器"""

    def __init__(self):
        self.results: List[DefenseResult] = []
        self.true_positives = 0
        self.true_negatives = 0
        self.false_positives = 0
        self.false_negatives = 0

    def add_result(
        self,
        result: DefenseResult,
        actual_malicious: bool,
    ) -> None:
        self.results.append(result)

        if result.is_malicious and actual_malicious:
            self.true_positives += 1
        elif not result.is_malicious and not actual_malicious:
            self.true_negatives += 1
        elif result.is_malicious and not actual_malicious:
            self.false_positives += 1
        else:
            self.false_negatives += 1

    def get_metrics(self) -> Dict[str, float]:
        total = (
            self.true_positives + self.true_negatives + self.false_positives + self.false_negatives
        )

        accuracy = (self.true_positives + self.true_negatives) / total if total > 0 else 0.0

        precision = (
            self.true_positives / (self.true_positives + self.false_positives)
            if (self.true_positives + self.false_positives) > 0
            else 0.0
        )

        recall = (
            self.true_positives / (self.true_positives + self.false_negatives)
            if (self.true_positives + self.false_negatives) > 0
            else 0.0
        )

        f1_score = (
            2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        )

        return {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "true_positives": self.true_positives,
            "true_negatives": self.true_negatives,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
            "total_samples": total,
        }


class RobustnessEvaluator:
    """鲁棒性评估器"""

    def __init__(self):
        self.perturbation_results: List[Dict[str, Any]] = []

    async def evaluate_perturbation_robustness(
        self,
        original_input: str,
        perturbed_inputs: List[str],
        model_responses: List[str],
    ) -> Dict[str, Any]:
        if len(perturbed_inputs) != len(model_responses):
            raise ValueError("Perturbed inputs and responses must have same length")

        if not original_input or not perturbed_inputs or not model_responses:
            return {
                "total_perturbations": 0,
                "avg_consistency": 0.0,
            }

        original_words = set(original_input.lower().split())

        consistency_scores = []
        for perturbed, response in zip(perturbed_inputs, model_responses):
            perturbed_words = set(perturbed.lower().split())

            if not original_words or not perturbed_words:
                consistency_scores.append(0.0)
                continue

            intersection = original_words & perturbed_words
            union = original_words | perturbed_words
            jaccard_similarity = len(intersection) / len(union) if union else 0.0

            response_words = set(response.lower().split())
            if response_words:
                response_overlap = len(intersection & response_words) / len(response_words)
            else:
                response_overlap = 0.0

            consistency_score = (jaccard_similarity + response_overlap) / 2
            consistency_scores.append(consistency_score)

        avg_consistency = (
            sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0.0
        )

        return {
            "total_perturbations": len(perturbed_inputs),
            "avg_consistency": avg_consistency,
            "consistency_scores": consistency_scores,
            "original_input_length": len(original_input),
        }

    def get_robustness_score(self) -> float:
        if not self.perturbation_results:
            return 0.0

        if not self.perturbation_results[0].get("consistency_score", None):
            return 0.0

        total_score = sum(r.get("consistency_score", 0.0) for r in self.perturbation_results)
        return total_score / len(self.perturbation_results) if self.perturbation_results else 0.0


class BenchmarkRunner:
    """基准测试运行器"""

    def __init__(self):
        self.attack_evaluator = AttackEvaluator()
        self.defense_evaluator = DefenseEvaluator()
        self.robustness_evaluator = RobustnessEvaluator()

    async def run_attack_benchmark(
        self,
        attack,
        payloads: List,
    ) -> EvaluationReport:
        for payload in payloads:
            outcome = await attack.generate_attack(payload)
            self.attack_evaluator.add_result(outcome)

        return self.attack_evaluator.generate_report()

    async def run_defense_benchmark(
        self,
        defense,
        test_cases: List[Dict[str, Any]],
    ) -> Dict[str, float]:
        for case in test_cases:
            input_text = case["input"]
            actual_malicious = case.get("is_malicious", False)

            result = await defense.detect(input_text)
            self.defense_evaluator.add_result(result, actual_malicious)

        return self.defense_evaluator.get_metrics()

    def get_comprehensive_report(self) -> Dict[str, Any]:
        return {
            "attack_evaluation": {
                "overall_metrics": self.attack_evaluator.get_overall_metrics().__dict__,
                "metrics_by_type": self.attack_evaluator.get_metrics_by_type(),
            },
            "defense_evaluation": self.defense_evaluator.get_metrics(),
            "robustness_score": self.robustness_evaluator.get_robustness_score(),
            "timestamp": datetime.now().isoformat(),
        }
