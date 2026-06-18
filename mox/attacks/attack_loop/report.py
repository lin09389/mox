"""报告生成器

支持 JSON、CSV、TXT、HTML 四种格式的报告输出。
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .config import AttackLoopConfig
from .result import AttackTestResult, TestStatistics


class ReportGenerator:
    """报告生成器"""

    def __init__(self, output_dir: str):
        self.output_path = Path(output_dir)
        self.output_path.mkdir(parents=True, exist_ok=True)

    def save_json(
        self,
        results: List[AttackTestResult],
        filename: Optional[str] = None,
    ) -> Path:
        """保存 JSON 格式结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = filename or f"attack_loop_{timestamp}.json"
        json_path = self.output_path / filename

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump([r.to_dict() for r in results], f, ensure_ascii=False, indent=2)

        return json_path

    def save_csv(
        self,
        results: List[AttackTestResult],
        filename: Optional[str] = None,
    ) -> Path:
        """保存 CSV 格式结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = filename or f"attack_loop_{timestamp}.csv"
        csv_path = self.output_path / filename

        if results:
            with open(csv_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=results[0].to_dict().keys())
                writer.writeheader()
                for result in results:
                    writer.writerow(result.to_dict())

        return csv_path

    def save_text_report(
        self,
        results: List[AttackTestResult],
        stats: TestStatistics,
        config: AttackLoopConfig,
        filename: Optional[str] = None,
    ) -> Path:
        """保存文本报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = filename or f"attack_loop_report_{timestamp}.txt"
        report_path = self.output_path / filename

        prompt_count = config.get_effective_prompts()

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("自动化攻击测试循环报告\n")
            f.write("=" * 60 + "\n\n")

            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # 测试配置
            f.write("测试配置:\n")
            f.write(f"  模型: {', '.join(config.models)}\n")
            f.write(f"  攻击类型: {', '.join(config.attack_types)}\n")
            f.write(f"  测试提示数: {prompt_count}\n")
            f.write(f"  每组合迭代: {config.iterations_per_combo}\n")
            f.write(f"  并发数: {config.max_concurrency}\n")
            f.write(f"  成功阈值: {config.success_threshold}\n\n")

            # 总体统计
            f.write("总体统计:\n")
            f.write(f"  总测试数: {stats.total_tests}\n")
            f.write(f"  成功数: {stats.successful_tests}\n")
            f.write(f"  失败数: {stats.failed_tests}\n")
            f.write(f"  错误数: {stats.error_tests}\n")
            if stats.total_tests > 0:
                f.write(f"  成功率: {stats.successful_tests / stats.total_tests * 100:.1f}%\n")
            f.write(f"  平均分数: {stats.avg_score:.2f}\n")
            f.write(f"  平均耗时: {stats.avg_duration:.1f}s\n")
            f.write(f"  总耗时: {stats.total_duration:.1f}s\n\n")

            # 按模型统计
            f.write("按模型统计:\n")
            for model, model_info in stats.model_stats.items():
                f.write(f"  {model}:\n")
                f.write(f"    测试数: {model_info['total']}\n")
                f.write(f"    成功数: {model_info['successful']}\n")
                f.write(f"    成功率: {model_info['success_rate']:.1f}%\n")
                f.write(f"    平均分: {model_info['avg_score']:.2f}\n")
                f.write(f"    平均耗时: {model_info['avg_duration']:.1f}s\n")
            f.write("\n")

            # 按攻击类型统计
            f.write("按攻击类型统计:\n")
            for attack_type, attack_info in stats.attack_stats.items():
                f.write(f"  {attack_info['name']} ({attack_type}):\n")
                f.write(f"    测试数: {attack_info['total']}\n")
                f.write(f"    成功数: {attack_info['successful']}\n")
                f.write(f"    成功率: {attack_info['success_rate']:.1f}%\n")
                f.write(f"    平均分: {attack_info['avg_score']:.2f}\n")
                f.write(f"    平均耗时: {attack_info['avg_duration']:.1f}s\n")
            f.write("\n")

            # 最危险的攻击
            f.write("最危险的攻击 (成功率最高):\n")
            for i, attack in enumerate(stats.top_dangerous_attacks[:5], 1):
                f.write(f"  {i}. {attack['name']}: {attack['success_rate']:.1f}% 成功率\n")
            f.write("\n")

            # 详细结果
            f.write("详细结果:\n")
            f.write("-" * 60 + "\n")
            for result in results:
                status = "成功" if result.success else "失败"
                f.write(f"[{result.test_id}] {result.model} - {result.attack_name}\n")
                f.write(f"  状态: {status}\n")
                f.write(f"  分数: {result.success_score:.2f}\n")
                f.write(f"  耗时: {result.duration:.1f}s\n")
                if result.error:
                    f.write(f"  错误: {result.error}\n")
                f.write("\n")

        return report_path

    def save_html_report(
        self,
        results: List[AttackTestResult],
        stats: TestStatistics,
        config: AttackLoopConfig,
        filename: Optional[str] = None,
    ) -> Path:
        """保存 HTML 报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = filename or f"attack_loop_report_{timestamp}.html"
        html_path = self.output_path / filename

        html_content = self._generate_html_content(results, stats, config)

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return html_path

    def _generate_html_content(
        self,
        results: List[AttackTestResult],
        stats: TestStatistics,
        config: AttackLoopConfig,
    ) -> str:
        """生成 HTML 报告内容"""

        # 模型统计表格行
        model_rows = ""
        for model, model_info in stats.model_stats.items():
            model_rows += f"""
                <tr>
                    <td>{model}</td>
                    <td>{model_info['total']}</td>
                    <td>{model_info['successful']}</td>
                    <td>{model_info['success_rate']:.1f}%</td>
                    <td>{model_info['avg_score']:.2f}</td>
                    <td>{model_info['avg_duration']:.1f}s</td>
                    <td><div class="progress-bar"><div class="progress-fill" style="width: {model_info['success_rate']}%"></div></div></td>
                </tr>"""

        # 攻击类型统计表格行
        attack_rows = ""
        for attack_type, attack_info in stats.attack_stats.items():
            attack_rows += f"""
                <tr>
                    <td>{attack_info['name']}</td>
                    <td>{attack_type}</td>
                    <td>{attack_info['total']}</td>
                    <td>{attack_info['successful']}</td>
                    <td>{attack_info['success_rate']:.1f}%</td>
                    <td>{attack_info['avg_score']:.2f}</td>
                    <td><div class="progress-bar"><div class="progress-fill" style="width: {attack_info['success_rate']}%"></div></div></td>
                </tr>"""

        # 详细结果表格行（限制前 100 条）
        detail_rows = ""
        for r in results[:100]:
            status_class = "success" if r.success else "failure"
            status_text = "成功" if r.success else "失败"
            error_text = (r.error[:30] + '...') if r.error and len(r.error) > 30 else (r.error or '-')
            prompt_text = (r.prompt[:40] + '...') if len(r.prompt) > 40 else r.prompt
            detail_rows += f"""
                <tr>
                    <td>{r.test_id}</td>
                    <td>{r.model}</td>
                    <td>{r.attack_name}</td>
                    <td title="{r.prompt}">{prompt_text}</td>
                    <td class="{status_class}">{status_text}</td>
                    <td>{r.success_score:.2f}</td>
                    <td>{r.duration:.1f}s</td>
                    <td>{error_text}</td>
                </tr>"""

        success_rate = (
            stats.successful_tests / stats.total_tests * 100
            if stats.total_tests > 0
            else 0
        )

        prompt_count = config.get_effective_prompts()

        return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>攻击测试循环报告</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; border-radius: 16px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 30px 40px; }}
        .header h1 {{ font-size: 2em; margin-bottom: 10px; }}
        .header .subtitle {{ opacity: 0.8; font-size: 0.9em; }}
        .content {{ padding: 30px 40px; }}
        h2 {{ color: #1e3c72; margin: 30px 0 15px; padding-bottom: 10px; border-bottom: 2px solid #e0e0e0; }}
        h2:first-child {{ margin-top: 0; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin: 20px 0; }}
        .stat-card {{ background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); padding: 20px; border-radius: 12px; text-align: center; transition: transform 0.2s; }}
        .stat-card:hover {{ transform: translateY(-5px); }}
        .stat-value {{ font-size: 2.2em; font-weight: bold; color: #1e3c72; }}
        .stat-label {{ color: #666; margin-top: 5px; font-size: 0.9em; }}
        .stat-card.success .stat-value {{ color: #28a745; }}
        .stat-card.failure .stat-value {{ color: #dc3545; }}
        .stat-card.warning .stat-value {{ color: #ffc107; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 0.9em; }}
        th {{ background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 12px 15px; text-align: left; font-weight: 600; }}
        td {{ padding: 10px 15px; border-bottom: 1px solid #e0e0e0; }}
        tr:nth-child(even) {{ background: #f8f9fa; }}
        tr:hover {{ background: #e8f4fd; }}
        .success {{ color: #28a745; font-weight: 600; }}
        .failure {{ color: #dc3545; font-weight: 600; }}
        .progress-bar {{ width: 100%; height: 24px; background: #e9ecef; border-radius: 12px; overflow: hidden; }}
        .progress-fill {{ height: 100%; background: linear-gradient(90deg, #28a745, #20c997); transition: width 0.3s; border-radius: 12px; }}
        .timestamp {{ color: rgba(255,255,255,0.8); font-size: 0.85em; }}
        .config-section {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 15px 0; }}
        .config-item {{ display: inline-block; margin: 5px 10px; padding: 5px 12px; background: white; border-radius: 20px; font-size: 0.85em; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .danger-list {{ list-style: none; }}
        .danger-list li {{ padding: 10px 15px; margin: 5px 0; background: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px; }}
        .footer {{ background: #f8f9fa; padding: 20px 40px; text-align: center; color: #666; font-size: 0.85em; }}
        @media (max-width: 768px) {{
            .content {{ padding: 20px; }}
            .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>攻击测试循环报告</h1>
            <p class="timestamp">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="content">
            <h2>总体统计</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{stats.total_tests}</div>
                    <div class="stat-label">总测试数</div>
                </div>
                <div class="stat-card success">
                    <div class="stat-value">{stats.successful_tests}</div>
                    <div class="stat-label">成功数</div>
                </div>
                <div class="stat-card failure">
                    <div class="stat-value">{stats.failed_tests}</div>
                    <div class="stat-label">失败数</div>
                </div>
                <div class="stat-card warning">
                    <div class="stat-value">{stats.error_tests}</div>
                    <div class="stat-label">错误数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{success_rate:.1f}%</div>
                    <div class="stat-label">成功率</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{stats.avg_score:.2f}</div>
                    <div class="stat-label">平均分数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{stats.avg_duration:.1f}s</div>
                    <div class="stat-label">平均耗时</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{stats.total_duration:.1f}s</div>
                    <div class="stat-label">总耗时</div>
                </div>
            </div>

            <h2>测试配置</h2>
            <div class="config-section">
                <span class="config-item">模型: {', '.join(config.models)}</span>
                <span class="config-item">攻击类型: {len(config.attack_types)}种</span>
                <span class="config-item">测试提示: {prompt_count}个</span>
                <span class="config-item">每组合迭代: {config.iterations_per_combo}次</span>
                <span class="config-item">并发数: {config.max_concurrency}</span>
                <span class="config-item">成功阈值: {config.success_threshold}</span>
            </div>

            <h2>最危险的攻击</h2>
            <ul class="danger-list">
                {"".join(f'<li><strong>{i+1}. {attack["name"]}</strong> - 成功率: {attack["success_rate"]:.1f}%, 平均分: {attack["avg_score"]:.2f}</li>' for i, attack in enumerate(stats.top_dangerous_attacks[:5]))}
            </ul>

            <h2>按模型统计</h2>
            <table>
                <thead>
                    <tr>
                        <th>模型</th>
                        <th>测试数</th>
                        <th>成功数</th>
                        <th>成功率</th>
                        <th>平均分</th>
                        <th>平均耗时</th>
                        <th>成功率可视化</th>
                    </tr>
                </thead>
                <tbody>
                    {model_rows}
                </tbody>
            </table>

            <h2>按攻击类型统计</h2>
            <table>
                <thead>
                    <tr>
                        <th>攻击名称</th>
                        <th>攻击类型</th>
                        <th>测试数</th>
                        <th>成功数</th>
                        <th>成功率</th>
                        <th>平均分</th>
                        <th>成功率可视化</th>
                    </tr>
                </thead>
                <tbody>
                    {attack_rows}
                </tbody>
            </table>

            <h2>详细结果 (前100条)</h2>
            <table>
                <thead>
                    <tr>
                        <th>测试ID</th>
                        <th>模型</th>
                        <th>攻击类型</th>
                        <th>提示</th>
                        <th>状态</th>
                        <th>分数</th>
                        <th>耗时</th>
                        <th>错误</th>
                    </tr>
                </thead>
                <tbody>
                    {detail_rows}
                </tbody>
            </table>
        </div>

        <div class="footer">
            <p>Mox - 大模型对抗攻防平台 | 攻击测试循环报告</p>
            <p>共 {stats.total_tests} 个测试 | 成功率 {success_rate:.1f}%</p>
        </div>
    </div>
</body>
</html>"""

    def save_all_reports(
        self,
        results: List[AttackTestResult],
        stats: TestStatistics,
        config: AttackLoopConfig,
    ) -> dict:
        """保存所有格式的报告

        Returns:
            各格式报告的路径字典
        """
        return {
            "json": self.save_json(results),
            "csv": self.save_csv(results),
            "txt": self.save_text_report(results, stats, config),
            "html": self.save_html_report(results, stats, config),
        }
