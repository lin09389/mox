"""AttackPayload 统一接口测试

验证以下功能:
1. AttackPayload 基本创建
2. AttackPayload 别名支持
3. AttackPayload 工厂方法
4. RedTeamScenario 统一接口
"""

import pytest

from mox.core import AttackPayload, AttackType
from mox.evaluation.redteam import RedTeamScenario, AttackTechnique


class TestAttackPayload:
    """测试 AttackPayload"""

    def test_basic_creation(self):
        """测试基本创建"""
        payload = AttackPayload(
            attack_type=AttackType.PROMPT_INJECTION,
            prompt="Test prompt",
            target_behavior="test behavior",
        )

        assert payload.attack_type == AttackType.PROMPT_INJECTION
        assert payload.prompt == "Test prompt"
        assert payload.target_behavior == "test behavior"

    def test_alias_support(self):
        """测试别名支持"""
        # 使用 target_objective 作为别名
        payload = AttackPayload(
            attack_type=AttackType.JAILBREAK,
            prompt="Test prompt",
            target_objective="test objective",
        )

        assert payload.target_behavior == "test objective"

    def test_create_factory(self):
        """测试工厂方法"""
        payload = AttackPayload.create(
            attack_type=AttackType.GCG,
            prompt="Test prompt",
            target="test target",
        )

        assert payload.attack_type == AttackType.GCG
        assert payload.prompt == "Test prompt"
        assert payload.target_behavior == "test target"

    def test_metadata(self):
        """测试元数据"""
        payload = AttackPayload(
            attack_type=AttackType.PROMPT_INJECTION,
            prompt="Test prompt",
            target_behavior="test behavior",
            metadata={"key": "value"},
        )

        assert payload.metadata == {"key": "value"}

    def test_validation(self):
        """测试验证"""
        # 空 prompt 应该失败
        with pytest.raises(ValueError):
            AttackPayload(
                attack_type=AttackType.PROMPT_INJECTION,
                prompt="",
                target_behavior="test behavior",
            )

        # 空 target_behavior 应该失败
        with pytest.raises(ValueError):
            AttackPayload(
                attack_type=AttackType.PROMPT_INJECTION,
                prompt="Test prompt",
                target_behavior="",
            )


class TestRedTeamScenario:
    """测试 RedTeamScenario"""

    def test_scenario_creation(self):
        """测试场景创建"""
        scenario = RedTeamScenario(
            scenario_id="test_001",
            name="Test Scenario",
            description="A test scenario",
            technique=AttackTechnique.JAILBREAK,
            target_objective="test objective",
            success_criteria="test criteria",
        )

        assert scenario.scenario_id == "test_001"
        assert scenario.target_objective == "test objective"

    def test_target_property(self):
        """测试 target 属性"""
        # 只有 target_objective
        scenario = RedTeamScenario(
            scenario_id="test_001",
            name="Test Scenario",
            description="A test scenario",
            technique=AttackTechnique.JAILBREAK,
            target_objective="test objective",
            success_criteria="test criteria",
        )
        assert scenario.target == "test objective"

        # 有 target_behavior
        scenario = RedTeamScenario(
            scenario_id="test_001",
            name="Test Scenario",
            description="A test scenario",
            technique=AttackTechnique.JAILBREAK,
            target_objective="test objective",
            success_criteria="test criteria",
            target_behavior="test behavior",
        )
        assert scenario.target == "test behavior"

    def test_to_attack_payload(self):
        """测试转换为 AttackPayload"""
        scenario = RedTeamScenario(
            scenario_id="test_001",
            name="Test Scenario",
            description="A test scenario",
            technique=AttackTechnique.JAILBREAK,
            target_objective="test objective",
            success_criteria="test criteria",
        )

        payload = scenario.to_attack_payload()

        assert isinstance(payload, AttackPayload)
        assert payload.prompt == "test objective"
        assert payload.target_behavior == "test objective"

    def test_to_attack_payload_with_type(self):
        """测试指定攻击类型"""
        scenario = RedTeamScenario(
            scenario_id="test_001",
            name="Test Scenario",
            description="A test scenario",
            technique=AttackTechnique.JAILBREAK,
            target_objective="test objective",
            success_criteria="test criteria",
        )

        payload = scenario.to_attack_payload(attack_type=AttackType.JAILBREAK)

        assert payload.attack_type == AttackType.JAILBREAK


class TestModuleExports:
    """测试模块导出"""

    def test_imports(self):
        """测试导入"""
        from mox.core import AttackPayload, AttackType

        assert AttackPayload is not None
        assert AttackType is not None

    def test_redteam_imports(self):
        """测试红队模块导入"""
        from mox.evaluation.redteam import RedTeamScenario, AttackTechnique

        assert RedTeamScenario is not None
        assert AttackTechnique is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
