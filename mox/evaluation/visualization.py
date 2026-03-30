"""
可视化模块 - 图表和报告生成
"""

import json
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from mox.core import AttackOutcome


@dataclass
class ChartData:
    """图表数据"""

    labels: List[str]
    values: List[float]
    title: str
    chart_type: str = "bar"


class ReportGenerator:
    """报告生成器"""

    def __init__(self):
        self.results: List[Dict[str, Any]] = []

    def add_result(self, outcome: AttackOutcome, attack_type: str = ""):
        self.results.append(
            {
                "attack_type": attack_type or outcome.metadata.get("attack_type", "unknown"),
                "result": outcome.result.value,
                "success_score": outcome.success_score,
                "iterations": outcome.iterations,
                "timestamp": datetime.now().isoformat(),
                "model_response": outcome.response[:200],
            }
        )

    def get_attack_success_rate(self) -> ChartData:
        """获取攻击成功率"""
        if not self.results:
            return ChartData(labels=[], values=[], title="攻击成功率")

        success = sum(1 for r in self.results if r["result"] == "success")
        total = len(self.results)

        return ChartData(
            labels=["成功", "失败"],
            values=[success, total - success],
            title="攻击成功率",
            chart_type="pie",
        )

    def get_attack_type_distribution(self) -> ChartData:
        """获取攻击类型分布"""
        if not self.results:
            return ChartData(labels=[], values=[], title="攻击类型分布")

        dist = {}
        for r in self.results:
            attack_type = r["attack_type"]
            dist[attack_type] = dist.get(attack_type, 0) + 1

        return ChartData(
            labels=list(dist.keys()),
            values=list(dist.values()),
            title="攻击类型分布",
            chart_type="doughnut",
        )

    def get_success_by_type(self) -> ChartData:
        """各类型攻击成功率"""
        if not self.results:
            return ChartData(labels=[], values=[], title="各类型成功率")

        type_stats = {}
        for r in self.results:
            attack_type = r["attack_type"]
            if attack_type not in type_stats:
                type_stats[attack_type] = {"success": 0, "total": 0}
            type_stats[attack_type]["total"] += 1
            if r["result"] == "success":
                type_stats[attack_type]["success"] += 1

        labels = list(type_stats.keys())
        values = [type_stats[t]["success"] / type_stats[t]["total"] * 100 for t in labels]

        return ChartData(
            labels=labels, values=values, title="各类型攻击成功率 (%)", chart_type="bar"
        )

    def get_iterations_distribution(self) -> ChartData:
        """迭代次数分布"""
        if not self.results:
            return ChartData(labels=[], values=[], title="迭代次数分布")

        iterations = [r["iterations"] for r in self.results]

        buckets = {"1-5": 0, "6-10": 0, "11-20": 0, "20+": 0}
        for it in iterations:
            if it <= 5:
                buckets["1-5"] += 1
            elif it <= 10:
                buckets["6-10"] += 1
            elif it <= 20:
                buckets["11-20"] += 1
            else:
                buckets["20+"] += 1

        return ChartData(
            labels=list(buckets.keys()),
            values=list(buckets.values()),
            title="迭代次数分布",
            chart_type="bar",
        )

    def generate_html_report(self, title: str = "Mox 安全评估报告") -> str:
        """生成HTML报告"""
        success_rate = self.get_attack_success_rate()
        type_dist = self.get_attack_type_distribution()
        success_by_type = self.get_success_by_type()
        iterations_dist = self.get_iterations_distribution()

        total = len(self.results)
        success = sum(1 for r in self.results if r["result"] == "success")

        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{
            text-align: center;
            padding: 40px 0;
            color: white;
        }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .header p {{ opacity: 0.8; }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .stat-card {{
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 24px;
            color: white;
            text-align: center;
        }}
        .stat-card .value {{
            font-size: 3em;
            font-weight: bold;
            background: linear-gradient(135deg, #00d4ff, #7c3aed);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .stat-card .label {{ opacity: 0.8; margin-top: 8px; }}
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 24px;
            margin: 30px 0;
        }}
        .chart-card {{
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 24px;
            color: white;
        }}
        .chart-card h3 {{ margin-bottom: 20px; font-weight: 500; }}
        .chart-container {{ position: relative; height: 300px; }}
        .table-section {{
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 24px;
            margin: 30px 0;
            color: white;
        }}
        .table-section h3 {{ margin-bottom: 20px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }}
        th {{ opacity: 0.7; font-weight: 500; }}
        .success {{ color: #10b981; }}
        .failure {{ color: #ef4444; }}
        .footer {{
            text-align: center;
            padding: 40px;
            color: rgba(255,255,255,0.5);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ {title}</h1>
            <p>生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
        
        <div class="summary">
            <div class="stat-card">
                <div class="value">{total}</div>
                <div class="label">总测试数</div>
            </div>
            <div class="stat-card">
                <div class="value">{success}</div>
                <div class="label">成功攻击</div>
            </div>
            <div class="stat-card">
                <div class="value">{total - success}</div>
                <div class="label">失败攻击</div>
            </div>
            <div class="stat-card">
                <div class="value">{success / total * 100:.1f}%</div>
                <div class="label">成功率</div>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-card">
                <h3>{success_rate.title}</h3>
                <div class="chart-container">
                    <canvas id="successChart"></canvas>
                </div>
            </div>
            <div class="chart-card">
                <h3>{type_dist.title}</h3>
                <div class="chart-container">
                    <canvas id="typeChart"></canvas>
                </div>
            </div>
            <div class="chart-card">
                <h3>{success_by_type.title}</h3>
                <div class="chart-container">
                    <canvas id="successByTypeChart"></canvas>
                </div>
            </div>
            <div class="chart-card">
                <h3>{iterations_dist.title}</h3>
                <div class="chart-container">
                    <canvas id="iterationsChart"></canvas>
                </div>
            </div>
        </div>
        
        <div class="table-section">
            <h3>详细结果</h3>
            <table>
                <thead>
                    <tr>
                        <th>攻击类型</th>
                        <th>结果</th>
                        <th>成功分数</th>
                        <th>迭代次数</th>
                    </tr>
                </thead>
                <tbody>
                    {
            "".join(
                f'''
                    <tr>
                        <td>{r['attack_type']}</td>
                        <td class="{r['result']}">{r['result']}</td>
                        <td>{r['success_score']:.2f}</td>
                        <td>{r['iterations']}</td>
                    </tr>'''
                for r in self.results
            )
        }
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            <p>Generated by Mox - 大模型对抗攻防平台</p>
        </div>
    </div>
    
    <script>
        const chartOptions = {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{ position: 'bottom', labels: {{ color: 'white' }} }}
            }}
        }};
        
        new Chart(document.getElementById('successChart'), {{
            type: 'pie',
            data: {{
                labels: {json.dumps(success_rate.labels)},
                datasets: [{{
                    data: {json.dumps(success_rate.values)},
                    backgroundColor: ['#10b981', '#ef4444']
                }}]
            }},
            options: chartOptions
        }});
        
        new Chart(document.getElementById('typeChart'), {{
            type: 'doughnut',
            data: {{
                labels: {json.dumps(type_dist.labels)},
                datasets: [{{
                    data: {json.dumps(type_dist.values)},
                    backgroundColor: ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#ef4444']
                }}]
            }},
            options: chartOptions
        }});
        
        new Chart(document.getElementById('successByTypeChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(success_by_type.labels)},
                datasets: [{{
                    label: '成功率 (%)',
                    data: {json.dumps(success_by_type.values)},
                    backgroundColor: '#8b5cf6'
                }}]
            }},
            options: {{
                ...chartOptions,
                scales: {{
                    y: {{ beginAtZero: true, max: 100, ticks: {{ color: 'white' }}, grid: {{ color: 'rgba(255,255,255,0.1)' }} }},
                    x: {{ ticks: {{ color: 'white' }}, grid: {{ color: 'rgba(255,255,255,0.1)' }} }}
                }}
            }}
        }});
        
        new Chart(document.getElementById('iterationsChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(iterations_dist.labels)},
                datasets: [{{
                    label: '次数',
                    data: {json.dumps(iterations_dist.values)},
                    backgroundColor: '#3b82f6'
                }}]
            }},
            options: {{
                ...chartOptions,
                scales: {{
                    y: {{ beginAtZero: true, ticks: {{ color: 'white' }}, grid: {{ color: 'rgba(255,255,255,0.1)' }} }},
                    x: {{ ticks: {{ color: 'white' }}, grid: {{ color: 'rgba(255,255,255,0.1)' }} }}
                }}
            }}
        }});
    </script>
</body>
</html>
        """
        return html

    def save_html_report(self, filename: str = "mox_report.html"):
        """保存HTML报告"""
        html = self.generate_html_report()
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)
        return filename

    def generate_json_report(self) -> Dict[str, Any]:
        """生成JSON报告"""
        return {
            "summary": {
                "total": len(self.results),
                "success": sum(1 for r in self.results if r["result"] == "success"),
                "failure": sum(1 for r in self.results if r["result"] == "failure"),
                "success_rate": sum(1 for r in self.results if r["result"] == "success")
                / len(self.results)
                if self.results
                else 0,
            },
            "attack_distribution": self.get_attack_type_distribution().__dict__,
            "success_by_type": self.get_success_by_type().__dict__,
            "iterations_distribution": self.get_iterations_distribution().__dict__,
            "results": self.results,
        }


def create_quick_report(outcomes: List[AttackOutcome], attack_types: List[str] = None) -> str:
    """快速生成报告"""
    report = ReportGenerator()
    attack_types = attack_types or [""]

    for i, outcome in enumerate(outcomes):
        attack_type = attack_types[i] if i < len(attack_types) else ""
        report.add_result(outcome, attack_type)

    return report.save_html_report()


__all__ = [
    "ChartData",
    "ReportGenerator",
    "create_quick_report",
]
