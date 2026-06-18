"""测试攻击循环脚本的功能

这个脚本用于验证攻击循环脚本的基本功能，包括：
1. 配置解析
2. 结果数据结构
3. 统计计算
4. 报告生成
5. 核心模块功能
"""

import asyncio
import sys
import os
import tempfile
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from examples.attack_loop_core import (
    AttackTestResult,
    LoopConfig,
    TestStatistics,
    AttackExecutor,
    ReportGenerator,
    CheckpointManager,
    PromptGenerator,
    ATTACK_REGISTRY,
    AttackCategory,
    setup_logger,
)


def test_attack_registry():
    """测试攻击注册表"""
    print("测试攻击注册表...")
    
    # 检查所有攻击类型是否都已注册
    expected_types = [
        "tool_chaining", "indirect_injection", "privilege_escalation",
        "tool_confusion", "data_exfiltration", "multi_agent",
        "many_shot", "skeleton_key", "deceptive_alignment",
        "cognitive_overload", "context_overflow", "role_confusion"
    ]
    
    for attack_type in expected_types:
        assert attack_type in ATTACK_REGISTRY, f"缺少攻击类型: {attack_type}"
        attack_info = ATTACK_REGISTRY[attack_type]
        assert attack_info.name is not None, f"攻击类型 {attack_type} 缺少名称"
        assert attack_info.attack_class is not None, f"攻击类型 {attack_type} 缺少类"
        assert attack_info.category is not None, f"攻击类型 {attack_type} 缺少类别"
        assert attack_info.description is not None, f"攻击类型 {attack_type} 缺少描述"
    
    print(f"✓ 攻击注册表正确，共 {len(expected_types)} 种攻击类型")
    
    # 按类别统计
    categories = {}
    for attack_type, attack_info in ATTACK_REGISTRY.items():
        category = attack_info.category.value
        if category not in categories:
            categories[category] = 0
        categories[category] += 1
    
    print(f"  攻击类别分布: {categories}")


def test_data_structures():
    """测试数据结构"""
    print("\n测试数据结构...")
    
    # 测试 AttackTestResult
    result = AttackTestResult(
        test_id="test_1",
        timestamp="2026-06-15T10:00:00",
        model="llama3",
        attack_type="tool_chaining",
        attack_name="工具链攻击",
        prompt="测试提示",
        success=True,
        success_score=0.85,
        iterations=3,
        adversarial_prompt="对抗提示",
        model_response="模型响应",
        error=None,
        duration=12.5,
        metadata={"attempt": 1}
    )
    
    assert result.test_id == "test_1"
    assert result.success is True
    assert result.success_score == 0.85
    assert result.metadata["attempt"] == 1
    
    # 测试 to_dict 和 from_dict
    result_dict = result.to_dict()
    result_from_dict = AttackTestResult.from_dict(result_dict)
    assert result_from_dict.test_id == result.test_id
    assert result_from_dict.success == result.success
    
    print("✓ AttackTestResult 数据结构正确")
    
    # 测试 LoopConfig
    config = LoopConfig(
        models=["llama3", "qwen3:4b"],
        attack_types=["tool_chaining", "privilege_escalation"],
        prompts=["测试提示1", "测试提示2"],
        iterations_per_combo=2,
        delay_between_tests=1.0,
        max_concurrency=3,
        output_dir="test_results"
    )
    
    assert len(config.models) == 2
    assert config.iterations_per_combo == 2
    assert config.max_concurrency == 3
    
    # 测试 YAML 保存和加载
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml_path = f.name
    config.to_yaml(yaml_path)
    config_from_yaml = LoopConfig.from_yaml(yaml_path)
    assert config_from_yaml.models == config.models
    os.unlink(yaml_path)
    
    # 测试 JSON 保存和加载
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json_path = f.name
    config.to_json(json_path)
    config_from_json = LoopConfig.from_json(json_path)
    assert config_from_json.models == config.models
    os.unlink(json_path)
    
    print("✓ LoopConfig 数据结构正确")


def test_statistics_calculation():
    """测试统计计算"""
    print("\n测试统计计算...")
    
    # 创建测试结果
    results = [
        AttackTestResult(
            test_id=f"test_{i}",
            timestamp="2026-06-15T10:00:00",
            model="llama3" if i % 2 == 0 else "qwen3:4b",
            attack_type="tool_chaining" if i % 3 == 0 else "privilege_escalation",
            attack_name="工具链攻击" if i % 3 == 0 else "权限提升攻击",
            prompt="测试提示",
            success=i % 2 == 0,  # 偶数成功，奇数失败
            success_score=0.8 if i % 2 == 0 else 0.3,
            iterations=3,
            adversarial_prompt=None,
            model_response=None,
            error="测试错误" if i == 9 else None,
            duration=10.0 + i
        )
        for i in range(10)
    ]
    
    # 计算统计
    stats = TestStatistics.calculate(results)
    
    assert stats.total_tests == 10
    assert stats.successful_tests == 5
    assert stats.failed_tests == 5
    assert stats.error_tests == 1
    assert abs(stats.avg_score - 0.55) < 0.01  # (0.8*5 + 0.3*5) / 10 = 0.55
    
    # 检查模型统计
    assert "llama3" in stats.model_stats
    assert "qwen3:4b" in stats.model_stats
    assert stats.model_stats["llama3"]["total"] == 5
    assert stats.model_stats["llama3"]["successful"] == 5
    
    # 检查攻击类型统计
    assert "tool_chaining" in stats.attack_stats
    assert "privilege_escalation" in stats.attack_stats
    
    # 检查最危险的攻击
    assert len(stats.top_dangerous_attacks) > 0
    
    print(f"✓ 统计计算正确:")
    print(f"  总数: {stats.total_tests}")
    print(f"  成功: {stats.successful_tests}")
    print(f"  失败: {stats.failed_tests}")
    print(f"  错误: {stats.error_tests}")
    print(f"  平均分: {stats.avg_score:.2f}")
    print(f"  模型数: {len(stats.model_stats)}")
    print(f"  攻击类型数: {len(stats.attack_stats)}")


def test_prompt_generator():
    """测试提示生成器"""
    print("\n测试提示生成器...")
    
    generator = PromptGenerator()
    
    # 生成单个提示
    prompt = generator.generate()
    assert isinstance(prompt, str)
    assert len(prompt) > 0
    print(f"  单个提示: {prompt}")
    
    # 生成多个提示
    prompts = generator.generate_batch(5)
    assert len(prompts) == 5
    assert len(set(prompts)) == 5  # 确保不重复
    print(f"  批量提示: {prompts}")
    
    # 测试自定义模板
    custom_generator = PromptGenerator(["执行{command_type}命令", "访问{resource_type}资源"])
    custom_prompt = custom_generator.generate()
    assert "命令" in custom_prompt or "资源" in custom_prompt
    print(f"  自定义提示: {custom_prompt}")
    
    print("✓ 提示生成器正确")


def test_report_generator():
    """测试报告生成器"""
    print("\n测试报告生成器...")
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        report_generator = ReportGenerator(temp_dir)
        
        # 创建测试数据
        results = [
            AttackTestResult(
                test_id=f"test_{i}",
                timestamp="2026-06-15T10:00:00",
                model="llama3",
                attack_type="tool_chaining",
                attack_name="工具链攻击",
                prompt="测试提示",
                success=i % 2 == 0,
                success_score=0.8 if i % 2 == 0 else 0.3,
                iterations=3,
                adversarial_prompt=None,
                model_response=None,
                error=None,
                duration=10.0 + i
            )
            for i in range(5)
        ]
        
        config = LoopConfig(
            models=["llama3"],
            attack_types=["tool_chaining"],
            prompts=["测试提示"],
        )
        
        stats = TestStatistics.calculate(results)
        
        # 测试 JSON 保存
        json_path = report_generator.save_json(results)
        assert json_path.exists()
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        assert len(json_data) == 5
        print(f"  JSON 报告: {json_path.name}")
        
        # 测试 CSV 保存
        csv_path = report_generator.save_csv(results)
        assert csv_path.exists()
        print(f"  CSV 报告: {csv_path.name}")
        
        # 测试文本报告
        text_path = report_generator.save_text_report(results, stats, config)
        assert text_path.exists()
        print(f"  文本报告: {text_path.name}")
        
        # 测试 HTML 报告
        html_path = report_generator.save_html_report(results, stats, config)
        assert html_path.exists()
        print(f"  HTML 报告: {html_path.name}")
        
        print("✓ 报告生成器正确")


def test_checkpoint_manager():
    """测试检查点管理器"""
    print("\n测试检查点管理器...")
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        checkpoint_manager = CheckpointManager(temp_dir)
        
        # 测试保存
        completed_tests = ["test_1", "test_2", "test_3"]
        results = [
            AttackTestResult(
                test_id="test_1",
                timestamp="2026-06-15T10:00:00",
                model="llama3",
                attack_type="tool_chaining",
                attack_name="工具链攻击",
                prompt="测试提示",
                success=True,
                success_score=0.8,
                iterations=3,
                adversarial_prompt=None,
                model_response=None,
                error=None,
                duration=10.0
            )
        ]
        
        checkpoint_manager.save(completed_tests, results)
        
        # 测试加载
        loaded_data = checkpoint_manager.load()
        assert len(loaded_data["completed_tests"]) == 3
        assert len(loaded_data["results"]) == 1
        print(f"  保存检查点: {len(completed_tests)} 个测试")
        print(f"  加载检查点: {len(loaded_data['completed_tests'])} 个测试")
        
        # 测试清除
        checkpoint_manager.clear()
        loaded_data_after_clear = checkpoint_manager.load()
        assert len(loaded_data_after_clear["completed_tests"]) == 0
        print(f"  清除检查点: 成功")
        
        print("✓ 检查点管理器正确")


async def test_attack_executor():
    """测试攻击执行器"""
    print("\n测试攻击执行器...")
    
    config = LoopConfig(
        models=["llama3"],
        attack_types=["tool_chaining"],
        prompts=["测试提示"],
    )
    
    executor = AttackExecutor(config)
    
    # 测试获取攻击信息
    attack_info = executor.get_attack_info("tool_chaining")
    assert attack_info is not None
    assert attack_info.name == "工具链攻击"
    print(f"  攻击信息: {attack_info.name}")
    
    # 测试未知攻击类型
    unknown_info = executor.get_attack_info("unknown_attack")
    assert unknown_info is None
    print(f"  未知攻击: {unknown_info}")
    
    print("✓ 攻击执行器正确")


async def main():
    """运行所有测试"""
    print("=" * 60)
    print("攻击循环脚本功能测试")
    print("=" * 60)
    
    try:
        test_attack_registry()
        test_data_structures()
        test_statistics_calculation()
        test_prompt_generator()
        test_report_generator()
        test_checkpoint_manager()
        await test_attack_executor()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)