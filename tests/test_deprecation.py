"""版本管理和弃用机制测试

验证以下功能:
1. 弃用装饰器
2. 弃用管理器
3. 变更日志管理
4. 版本兼容性检查
"""

import pytest
import warnings

from mox.core.deprecation import (
    DeprecationLevel,
    DeprecationInfo,
    DeprecationManager,
    DeprecationError,
    FeatureRemovedError,
    deprecated,
    deprecated_class,
    check_deprecation,
    warn_deprecation,
    get_deprecation_stats,
    get_all_deprecations,
)


class TestDeprecationLevel:
    """测试弃用级别"""

    def test_levels(self):
        """测试弃用级别枚举"""
        assert DeprecationLevel.WARNING.value == "warning"
        assert DeprecationLevel.ERROR.value == "error"
        assert DeprecationLevel.REMOVED.value == "removed"


class TestDeprecationInfo:
    """测试弃用信息"""

    def test_info_creation(self):
        """测试信息创建"""
        info = DeprecationInfo(
            name="test_feature",
            since="0.2.0",
            removed_in="0.4.0",
            use_instead="new_feature",
            message="Test deprecation",
        )

        assert info.name == "test_feature"
        assert info.since == "0.2.0"
        assert info.removed_in == "0.4.0"
        assert info.use_instead == "new_feature"
        assert info.message == "Test deprecation"
        assert info.usage_count == 0


class TestDeprecationManager:
    """测试弃用管理器"""

    def test_manager_creation(self):
        """测试管理器创建"""
        manager = DeprecationManager(current_version="0.3.0")
        assert manager.current_version == "0.3.0"

    def test_register_deprecation(self):
        """测试注册弃用项"""
        manager = DeprecationManager()

        manager.register(
            name="test_feature",
            since="0.2.0",
            removed_in="0.4.0",
            use_instead="new_feature",
        )

        info = manager.check("test_feature")
        assert info is not None
        assert info.name == "test_feature"
        assert info.since == "0.2.0"

    def test_warn_deprecation(self):
        """测试发出弃用警告"""
        manager = DeprecationManager()

        manager.register(
            name="test_feature",
            since="0.2.0",
            removed_in="0.4.0",
            use_instead="new_feature",
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            manager.warn("test_feature", stacklevel=2)

            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "test_feature" in str(w[0].message)

    def test_error_level(self):
        """测试错误级别"""
        manager = DeprecationManager()

        manager.register(
            name="test_feature",
            since="0.2.0",
            removed_in="0.4.0",
            level=DeprecationLevel.ERROR,
        )

        with pytest.raises(DeprecationError):
            manager.warn("test_feature")

    def test_removed_level(self):
        """测试已移除级别"""
        manager = DeprecationManager()

        manager.register(
            name="test_feature",
            since="0.2.0",
            removed_in="0.4.0",
            level=DeprecationLevel.REMOVED,
        )

        with pytest.raises(FeatureRemovedError):
            manager.warn("test_feature")

    def test_suppress_warnings(self):
        """测试抑制警告"""
        manager = DeprecationManager()

        manager.register(
            name="test_feature",
            since="0.2.0",
        )

        manager.suppress("test_feature")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            manager.warn("test_feature")
            assert len(w) == 0

    def test_usage_stats(self):
        """测试使用统计"""
        manager = DeprecationManager()

        manager.register(
            name="test_feature",
            since="0.2.0",
        )

        manager.warn("test_feature", stacklevel=2)

        stats = manager.get_usage_stats()
        assert stats["total_deprecations"] == 1
        assert stats["total_usage"] == 1

    def test_version_compatibility(self):
        """测试版本兼容性"""
        manager = DeprecationManager()

        manager.register(
            name="test_feature",
            since="0.2.0",
            removed_in="0.4.0",
        )

        warnings_list = manager.check_version_compatibility("0.4.0")
        assert len(warnings_list) > 0
        assert "test_feature" in warnings_list[0]


class TestDeprecatedDecorator:
    """测试弃用装饰器"""

    def test_function_deprecation(self):
        """测试函数弃用"""

        @deprecated(since="0.2.0", removed_in="0.4.0", use_instead="new_function")
        def old_function():
            return "old"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = old_function()

            assert result == "old"
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)

    def test_class_deprecation(self):
        """测试类弃用"""

        @deprecated_class(since="0.2.0", removed_in="0.4.0", use_instead="NewClass")
        class OldClass:
            pass

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            instance = OldClass()

            assert instance is not None
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)


class TestConvenienceFunctions:
    """测试便捷函数"""

    def test_check_deprecation(self):
        """测试检查弃用"""
        from mox.core.deprecation import get_deprecation_manager

        manager = get_deprecation_manager()
        manager.register(
            name="test_feature",
            since="0.2.0",
        )

        info = check_deprecation("test_feature")
        assert info is not None
        assert info.name == "test_feature"

    def test_get_deprecation_stats(self):
        """测试获取弃用统计"""
        stats = get_deprecation_stats()
        assert "total_deprecations" in stats
        assert "active_deprecations" in stats

    def test_get_all_deprecations(self):
        """测试获取所有弃用项"""
        deprecations = get_all_deprecations()
        assert isinstance(deprecations, dict)


class TestModuleExports:
    """测试模块导出"""

    def test_imports(self):
        """测试导入"""
        from mox.core.deprecation import (
            DeprecationLevel,
            DeprecationInfo,
            DeprecationManager,
            DeprecationError,
            FeatureRemovedError,
            get_deprecation_manager,
            deprecated,
            deprecated_class,
            check_deprecation,
            get_deprecation_stats,
            get_all_deprecations,
        )

        assert DeprecationLevel is not None
        assert DeprecationInfo is not None
        assert DeprecationManager is not None
        assert DeprecationError is not None
        assert FeatureRemovedError is not None
        assert get_deprecation_manager is not None
        assert deprecated is not None
        assert deprecated_class is not None
        assert check_deprecation is not None
        assert warn_deprecation is not None
        assert get_deprecation_stats is not None
        assert get_all_deprecations is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
