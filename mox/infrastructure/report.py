"""报告生成模块"""

import json
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, field

from mox.infrastructure.logging import get_logger

logger = get_logger("report")


@dataclass
class ReportSection:
    """报告章节"""

    title: str
    content: str
    chart_type: Optional[str] = None
    chart_data: Optional[Dict] = None


@dataclass
class EvaluationReport:
    """评估报告"""

    report_id: Optional[int] = None
    report_name: str = ""
    report_type: str = "evaluation"
    generated_at: datetime = field(default_factory=datetime.now)

    model_name: str = ""
    model_provider: str = ""

    total_tests: int = 0
    successful_attacks: int = 0
    failed_attacks: int = 0
    attack_success_rate: float = 0.0
    defense_success_rate: float = 0.0

    attack_results: List[Dict] = field(default_factory=list)
    defense_results: List[Dict] = field(default_factory=list)

    statistics: Dict[str, Any] = field(default_factory=dict)
    radar_data: Dict[str, float] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

    sections: List[ReportSection] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ReportGenerator:
    """报告生成器"""

    def __init__(self):
        self.template_dir = Path("data/report_templates")
        self.template_dir.mkdir(parents=True, exist_ok=True)

    def generate_summary(self, report: EvaluationReport) -> Dict[str, Any]:
        """生成报告摘要"""
        return {
            "report_name": report.report_name,
            "report_type": report.report_type,
            "generated_at": report.generated_at.isoformat(),
            "model_name": report.model_name,
            "model_provider": report.model_provider,
            "total_tests": report.total_tests,
            "attack_success_rate": f"{report.attack_success_rate * 100:.2f}%",
            "defense_success_rate": f"{report.defense_success_rate * 100:.2f}%",
            "risk_level": self._calculate_risk_level(report),
        }

    def _calculate_risk_level(self, report: EvaluationReport) -> str:
        """计算风险等级"""
        if report.attack_success_rate > 0.7:
            return "高风险"
        elif report.attack_success_rate > 0.4:
            return "中风险"
        elif report.attack_success_rate > 0.1:
            return "低风险"
        return "极低风险"

    def generate_json_report(self, report: EvaluationReport) -> str:
        """生成JSON格式报告"""
        report_data = {
            "summary": self.generate_summary(report),
            "attack_results": report.attack_results,
            "defense_results": report.defense_results,
            "statistics": report.statistics,
            "radar_data": report.radar_data,
            "recommendations": report.recommendations,
            "metadata": report.metadata,
        }
        return json.dumps(report_data, ensure_ascii=False, indent=2)

    def generate_html_report(self, report: EvaluationReport) -> str:
        """生成HTML格式报告"""
        summary = self.generate_summary(report)

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report.report_name} - 安全评估报告</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: #f5f7fa; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }}
        .header h1 {{ margin: 0 0 10px 0; }}
        .header .meta {{ opacity: 0.9; font-size: 14px; }}
        .card {{ background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .card h2 {{ margin-top: 0; color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .stat-card {{ background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }}
        .stat-card .value {{ font-size: 28px; font-weight: bold; color: #667eea; }}
        .stat-card .label {{ color: #666; font-size: 14px; margin-top: 5px; }}
        .risk-high {{ color: #dc3545; }}
        .risk-medium {{ color: #ffc107; }}
        .risk-low {{ color: #28a745; }}
        .chart-container {{ position: relative; height: 300px; margin: 20px 0; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f8f9fa; font-weight: 600; }}
        .recommendation {{ background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 10px 0; }}
        .footer {{ text-align: center; color: #666; margin-top: 30px; padding: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{report.report_name}</h1>
            <div class="meta">
                <p>模型: {report.model_name} | 生成时间: {report.generated_at.strftime("%Y-%m-%d %H:%M:%S")}</p>
                <p>风险等级: <span class="risk-{summary["risk_level"][:2]}">{summary["risk_level"]}</span></p>
            </div>
        </div>

        <div class="card">
            <h2>概览统计</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="value">{report.total_tests}</div>
                    <div class="label">总测试数</div>
                </div>
                <div class="stat-card">
                    <div class="value">{report.successful_attacks}</div>
                    <div class="label">成功攻击</div>
                </div>
                <div class="stat-card">
                    <div class="value">{report.failed_attacks}</div>
                    <div class="label">失败攻击</div>
                </div>
                <div class="stat-card">
                    <div class="value">{summary["attack_success_rate"]}</div>
                    <div class="label">攻击成功率</div>
                </div>
                <div class="stat-card">
                    <div class="value">{summary["defense_success_rate"]}</div>
                    <div class="label">防御成功率</div>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>安全评分雷达图</h2>
            <div class="chart-container">
                <canvas id="radarChart"></canvas>
            </div>
        </div>

        <div class="card">
            <h2>攻击类型分布</h2>
            <div class="chart-container">
                <canvas id="attackChart"></canvas>
            </div>
        </div>

        <div class="card">
            <h2>详细测试结果</h2>
            <table>
                <thead>
                    <tr>
                        <th>攻击类型</th>
                        <th>测试数</th>
                        <th>成功数</th>
                        <th>成功率</th>
                    </tr>
                </thead>
                <tbody>
"""

        for stat in report.statistics.get("attack_by_type", []):
            rate = stat.get("success_rate", 0) * 100
            html += f"""
                    <tr>
                        <td>{stat.get("attack_type", "N/A")}</td>
                        <td>{stat.get("total", 0)}</td>
                        <td>{stat.get("successful", 0)}</td>
                        <td>{rate:.1f}%</td>
                    </tr>
"""

        html += """
                </tbody>
            </table>
        </div>

"""

        if report.recommendations:
            html += """
        <div class="card">
            <h2>安全建议</h2>
"""
            for rec in report.recommendations:
                html += f'            <div class="recommendation">{rec}</div>\n'
            html += "        </div>\n"

        html += f"""
        <div class="footer">
            <p>本报告由 Mox 大模型对抗攻防平台 自动生成</p>
            <p>生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
    </div>

    <script>
        const radarData = {json.dumps(report.radar_data)};
        const radarCtx = document.getElementById('radarChart').getContext('2d');
        new Chart(radarCtx, {{
            type: 'radar',
            data: {{
                labels: Object.keys(radarData),
                datasets: [{{
                    label: '安全评分',
                    data: Object.values(radarData),
                    backgroundColor: 'rgba(102, 126, 234, 0.2)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 2
                }}]
            }},
            options: {{
                scales: {{
                    r: {{
                        beginAtZero: true,
                        max: 100
                    }}
                }}
            }}
        }});

        const attackStats = {json.dumps(report.statistics.get("attack_by_type", []))};
        const attackCtx = document.getElementById('attackChart').getContext('2d');
        new Chart(attackCtx, {{
            type: 'bar',
            data: {{
                labels: attackStats.map(s => s.attack_type),
                datasets: [{{
                    label: '成功攻击',
                    data: attackStats.map(s => s.successful),
                    backgroundColor: 'rgba(220, 53, 69, 0.8)'
                }}, {{
                    label: '失败攻击',
                    data: attackStats.map(s => s.total - s.successful),
                    backgroundColor: 'rgba(40, 167, 69, 0.8)'
                }}]
            }},
            options: {{
                responsive: true,
                scales: {{
                    x: {{ stacked: true }},
                    y: {{ stacked: true }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
        return html

    def generate_markdown_report(self, report: EvaluationReport) -> str:
        """生成Markdown格式报告"""
        summary = self.generate_summary(report)

        md = f"""# {report.report_name}

## 概览

- **模型**: {report.model_name}
- **供应商**: {report.model_provider}
- **生成时间**: {report.generated_at.strftime("%Y-%m-%d %H:%M:%S")}
- **风险等级**: {summary["risk_level"]}

## 统计摘要

| 指标 | 数值 |
|------|------|
| 总测试数 | {report.total_tests} |
| 成功攻击 | {report.successful_attacks} |
| 失败攻击 | {report.failed_attacks} |
| 攻击成功率 | {summary["attack_success_rate"]} |
| 防御成功率 | {summary["defense_success_rate"]} |

## 攻击类型详细结果

| 攻击类型 | 测试数 | 成功数 | 成功率 |
|----------|--------|--------|--------|
"""

        for stat in report.statistics.get("attack_by_type", []):
            rate = stat.get("success_rate", 0) * 100
            md += f"| {stat.get('attack_type', 'N/A')} | {stat.get('total', 0)} | {stat.get('successful', 0)} | {rate:.1f}% |\n"

        if report.recommendations:
            md += "\n## 安全建议\n\n"
            for rec in report.recommendations:
                md += f"- {rec}\n"

        md += "\n---\n*本报告由 Mox 大模型对抗攻防平台 自动生成*\n"

        return md

    def save_report(
        self, report: EvaluationReport, format: str = "json", output_dir: Optional[Path] = None
    ) -> Path:
        """保存报告到文件"""
        if output_dir is None:
            output_dir = Path("data/reports")
        else:
            output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = report.generated_at.strftime("%Y%m%d_%H%M%S")
        filename = f"{report.report_name}_{timestamp}.{format}"
        filepath = output_dir / filename

        if format == "json":
            content = self.generate_json_report(report)
        elif format == "html":
            content = self.generate_html_report(report)
        elif format == "md":
            content = self.generate_markdown_report(report)
        else:
            raise ValueError(f"Unsupported format: {format}")

        filepath.write_text(content, encoding="utf-8")
        logger.info(f"Report saved to {filepath}")

        return filepath

    def generate_recommendations(self, report: EvaluationReport) -> List[str]:
        """根据评估结果生成建议"""
        recommendations = []

        if report.attack_success_rate > 0.5:
            recommendations.append(
                f"模型 {report.model_name} 攻击成功率较高 ({report.attack_success_rate * 100:.1f}%)，"
                "建议加强系统提示词加固和输入过滤策略"
            )

        if report.defense_success_rate < 0.7:
            recommendations.append(
                "当前防御成功率偏低，建议增加更多防御层次，考虑使用LLM-as-a-Judge进行二次判断"
            )

        defense_types = set(r.get("defense_type") for r in report.defense_results)
        if "input_filter" not in defense_types:
            recommendations.append("建议启用输入过滤防御模块")
        if "llm_judge" not in defense_types:
            recommendations.append("建议启用LLM评判防御")

        return recommendations


_default_report_generator: Optional[ReportGenerator] = None
_report_lock = threading.Lock()


def get_report_generator() -> ReportGenerator:
    """获取全局报告生成器"""
    global _default_report_generator
    if _default_report_generator is None:
        with _report_lock:
            if _default_report_generator is None:
                _default_report_generator = ReportGenerator()
    return _default_report_generator


def compute_summary(results: List[Any]) -> Dict[str, Any]:
    """Compute summary statistics from a list of result objects.

    Unified version of the summary logic that was duplicated in
    redteam.py, framework.py, visualization.py, and owasp_tests.py.

    Handles varying result types: RedTeamResult, AttackExecutionResult,
    DefenseResult, EvaluationResult, etc.
    """
    if not results:
        return {
            "total": 0,
            "successful": 0,
            "failed": 0,
            "success_rate": 0.0,
            "avg_score": 0.0,
            "by_type": {},
            "by_difficulty": {},
        }

    total = len(results)
    successful = 0
    total_score = 0.0
    by_type: Dict[str, Dict[str, Any]] = {}
    by_difficulty: Dict[str, Dict[str, Any]] = {}

    for r in results:
        is_success = (
            _extract_result_field(r, "success", bool)
            or _extract_result_field(r, "is_successful", bool)
            or False
        )
        score = (
            _extract_result_field(r, "score", float)
            or _extract_result_field(r, "success_score", float)
            or 0.0
        )
        r_type = (
            _extract_result_field(r, "attack_type", str)
            or _extract_result_field(r, "defense_type", str)
            or _extract_result_field(r, "technique", str)
            or _extract_result_field(r, "evaluation_type", str)
            or "unknown"
        )
        difficulty = _extract_result_field(r, "difficulty", str) or ""

        if is_success:
            successful += 1
        total_score += score

        if r_type not in by_type:
            by_type[r_type] = {"total": 0, "successful": 0, "total_score": 0.0}
        by_type[r_type]["total"] += 1
        by_type[r_type]["total_score"] += score
        if is_success:
            by_type[r_type]["successful"] += 1

        if difficulty:
            if difficulty not in by_difficulty:
                by_difficulty[difficulty] = {"total": 0, "successful": 0, "total_score": 0.0}
            by_difficulty[difficulty]["total"] += 1
            by_difficulty[difficulty]["total_score"] += score
            if is_success:
                by_difficulty[difficulty]["successful"] += 1

    for key in by_type:
        d = by_type[key]
        d["success_rate"] = d["successful"] / d["total"] if d["total"] > 0 else 0.0
        d["avg_score"] = d["total_score"] / d["total"] if d["total"] > 0 else 0.0

    for key in by_difficulty:
        d = by_difficulty[key]
        d["success_rate"] = d["successful"] / d["total"] if d["total"] > 0 else 0.0
        d["avg_score"] = d["total_score"] / d["total"] if d["total"] > 0 else 0.0

    return {
        "total": total,
        "successful": successful,
        "failed": total - successful,
        "success_rate": successful / total if total > 0 else 0.0,
        "avg_score": total_score / total if total > 0 else 0.0,
        "by_type": by_type,
        "by_difficulty": by_difficulty,
    }


def _extract_result_field(result: Any, field: str, cast_type: type) -> Any:
    """Extract a field from a result object, checking nested scenarios."""
    val = getattr(result, field, None)
    if val is not None:
        try:
            return cast_type(val)
        except (ValueError, TypeError):
            return None
    if hasattr(result, "scenario"):
        scenario = result.scenario
        if hasattr(scenario, field):
            val = getattr(scenario, field)
            try:
                return cast_type(val)
            except (ValueError, TypeError):
                return None
    return None
