"""攻击循环测试结果数据结构"""

from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Dict, List, Any, Optional


@dataclass
class AttackTestResult:
    """单次攻击测试结果"""
    test_id: str
    timestamp: str
    model: str
    attack_type: str
    attack_name: str
    prompt: str
    success: bool
    success_score: float
    iterations: int
    adversarial_prompt: Optional[str]
    model_response: Optional[str]
    error: Optional[str]
    duration: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AttackTestResult':
        """从字典创建"""
        # 过滤掉不识别的字段，保持向后兼容
        import dataclasses
        valid_fields = {f.name for f in dataclasses.fields(cls)}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


@dataclass
class TestStatistics:
    """测试统计信息"""
    total_tests: int = 0
    successful_tests: int = 0
    failed_tests: int = 0
    error_tests: int = 0
    total_duration: float = 0.0
    avg_score: float = 0.0
    avg_duration: float = 0.0

    # 按模型统计
    model_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # 按攻击类型统计
    attack_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # 最危险的攻击
    top_dangerous_attacks: List[Dict[str, Any]] = field(default_factory=list)

    # 时间分布
    time_distribution: Dict[str, int] = field(default_factory=dict)

    @classmethod
    def calculate(cls, results: List[AttackTestResult]) -> 'TestStatistics':
        """从测试结果计算统计信息"""
        if not results:
            return cls()

        stats = cls()
        stats.total_tests = len(results)
        stats.successful_tests = sum(1 for r in results if r.success)
        stats.failed_tests = stats.total_tests - stats.successful_tests
        stats.error_tests = sum(1 for r in results if r.error)
        stats.total_duration = sum(r.duration for r in results)
        stats.avg_score = sum(r.success_score for r in results) / stats.total_tests
        stats.avg_duration = stats.total_duration / stats.total_tests

        # 按模型统计
        models = set(r.model for r in results)
        for model in models:
            model_results = [r for r in results if r.model == model]
            model_success = sum(1 for r in model_results if r.success)
            model_avg = sum(r.success_score for r in model_results) / len(model_results)
            stats.model_stats[model] = {
                "total": len(model_results),
                "successful": model_success,
                "failed": len(model_results) - model_success,
                "success_rate": model_success / len(model_results) * 100,
                "avg_score": model_avg,
                "avg_duration": sum(r.duration for r in model_results) / len(model_results)
            }

        # 按攻击类型统计
        attack_types = set(r.attack_type for r in results)
        for attack_type in attack_types:
            attack_results = [r for r in results if r.attack_type == attack_type]
            attack_success = sum(1 for r in attack_results if r.success)
            attack_avg = sum(r.success_score for r in attack_results) / len(attack_results)
            attack_name = attack_results[0].attack_name if attack_results else attack_type
            stats.attack_stats[attack_type] = {
                "name": attack_name,
                "total": len(attack_results),
                "successful": attack_success,
                "failed": len(attack_results) - attack_success,
                "success_rate": attack_success / len(attack_results) * 100,
                "avg_score": attack_avg,
                "avg_duration": sum(r.duration for r in attack_results) / len(attack_results)
            }

        # 最危险的攻击
        attack_danger_list = []
        for attack_type, attack_info in stats.attack_stats.items():
            attack_danger_list.append({
                "type": attack_type,
                "name": attack_info["name"],
                "success_rate": attack_info["success_rate"],
                "avg_score": attack_info["avg_score"]
            })
        stats.top_dangerous_attacks = sorted(
            attack_danger_list,
            key=lambda x: x["success_rate"],
            reverse=True
        )[:5]

        # 时间分布（按小时）
        for result in results:
            try:
                hour = datetime.fromisoformat(result.timestamp).strftime("%Y-%m-%d %H:00")
                stats.time_distribution[hour] = stats.time_distribution.get(hour, 0) + 1
            except Exception:
                pass

        return stats
