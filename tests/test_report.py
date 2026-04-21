"""测试报告生成模块"""

import pytest
from datetime import datetime
from mox.infrastructure.report import ReportGenerator, EvaluationReport


class TestReportGenerator:
    """测试报告生成器"""

    def test_report_summary(self):
        """测试报告摘要生成"""
        generator = ReportGenerator()

        report = EvaluationReport(
            report_name="Test Report",
            report_type="evaluation",
            model_name="gpt-4",
            total_tests=100,
            successful_attacks=30,
            failed_attacks=70,
            attack_success_rate=0.3,
            defense_success_rate=0.8,
        )

        summary = generator.generate_summary(report)

        assert summary["report_name"] == "Test Report"
        assert summary["model_name"] == "gpt-4"
        assert summary["total_tests"] == 100
        assert summary["attack_success_rate"] == "30.00%"
        assert summary["risk_level"] == "低风险"

    def test_risk_level_calculation(self):
        """测试风险等级计算"""
        generator = ReportGenerator()

        report_high = EvaluationReport(attack_success_rate=0.8)
        report_medium = EvaluationReport(attack_success_rate=0.5)
        report_low = EvaluationReport(attack_success_rate=0.2)

        assert generator._calculate_risk_level(report_high) == "高风险"
        assert generator._calculate_risk_level(report_medium) == "中风险"
        assert generator._calculate_risk_level(report_low) == "低风险"

    def test_json_report_generation(self):
        """测试JSON报告生成"""
        generator = ReportGenerator()

        report = EvaluationReport(
            report_name="Test Report",
            report_type="evaluation",
            model_name="gpt-4",
            total_tests=10,
            successful_attacks=3,
            failed_attacks=7,
            attack_success_rate=0.3,
            defense_success_rate=0.8,
        )

        json_report = generator.generate_json_report(report)

        assert '"report_name": "Test Report"' in json_report
        assert '"model_name": "gpt-4"' in json_report

    def test_markdown_report_generation(self):
        """测试Markdown报告生成"""
        generator = ReportGenerator()

        report = EvaluationReport(
            report_name="Test Report",
            model_name="gpt-4",
            total_tests=10,
            successful_attacks=3,
            failed_attacks=7,
            attack_success_rate=0.3,
            defense_success_rate=0.8,
            statistics={
                "attack_by_type": [
                    {"attack_type": "prompt_injection", "total": 5, "successful": 2},
                ]
            },
        )

        md_report = generator.generate_markdown_report(report)

        assert "# Test Report" in md_report
        assert "| 总测试数 | 10 |" in md_report

    def test_html_report_generation(self):
        """测试HTML报告生成"""
        generator = ReportGenerator()

        report = EvaluationReport(
            report_name="Test Report",
            model_name="gpt-4",
            total_tests=10,
            successful_attacks=3,
            failed_attacks=7,
            attack_success_rate=0.3,
            defense_success_rate=0.8,
            radar_data={
                "prompt_injection": 70,
                "jailbreak": 80,
                "privacy": 90,
            },
            statistics={
                "attack_by_type": [
                    {
                        "attack_type": "prompt_injection",
                        "total": 5,
                        "successful": 2,
                        "success_rate": 0.4,
                    },
                ]
            },
        )

        html_report = generator.generate_html_report(report)

        assert "<!DOCTYPE html>" in html_report
        assert "Test Report" in html_report

    def test_recommendations_generation(self):
        """测试建议生成"""
        generator = ReportGenerator()

        report_high_attack = EvaluationReport(
            attack_success_rate=0.6,
            defense_success_rate=0.8,
            model_name="test-model",
            defense_results=[{"defense_type": "llm_judge"}],
        )

        recommendations = generator.generate_recommendations(report_high_attack)

        assert len(recommendations) > 0
        assert any("攻击成功率" in r for r in recommendations)

    def test_save_report(self):
        """测试报告保存"""
        import tempfile
        import os

        generator = ReportGenerator()

        report = EvaluationReport(
            report_name="Test Report",
            model_name="gpt-4",
            total_tests=10,
            successful_attacks=3,
            failed_attacks=7,
            attack_success_rate=0.3,
            defense_success_rate=0.8,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = generator.save_report(report, format="json", output_dir=tmpdir)

            assert os.path.exists(filepath)
            assert filepath.suffix == ".json"
