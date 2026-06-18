"""变更日志管理模块

提供版本变更日志管理:
1. 版本变更记录
2. 弃用信息跟踪
3. 迁移指南管理
4. 变更日志生成

使用示例:
    from mox.core.changelog import ChangelogManager, ChangeType

    # 获取变更日志
    manager = ChangelogManager()
    changelog = manager.get_changelog()

    # 检查版本变化
    changes = manager.get_changes_since("0.2.0")
"""

from typing import Optional, List, Dict
from dataclasses import dataclass, field
from datetime import date
from enum import Enum


class ChangeType(Enum):
    """变更类型"""

    ADDED = "added"  # 新增功能
    CHANGED = "changed"  # 功能变更
    DEPRECATED = "deprecated"  # 弃用功能
    REMOVED = "removed"  # 移除功能
    FIXED = "fixed"  # 修复问题
    SECURITY = "security"  # 安全更新


@dataclass
class ChangeEntry:
    """变更条目"""

    type: ChangeType
    description: str
    version: str
    date: Optional[date] = None
    breaking: bool = False
    migration_guide: Optional[str] = None
    related_issues: List[str] = field(default_factory=list)
    affected_components: List[str] = field(default_factory=list)


@dataclass
class VersionInfo:
    """版本信息"""

    version: str
    release_date: date
    changes: List[ChangeEntry] = field(default_factory=list)
    summary: str = ""
    breaking_changes: List[str] = field(default_factory=list)
    deprecations: List[str] = field(default_factory=list)
    migration_guides: List[str] = field(default_factory=list)


class ChangelogManager:
    """变更日志管理器"""

    def __init__(self):
        self._versions: Dict[str, VersionInfo] = {}
        self._current_version: str = "0.3.0"
        self._init_changelog()

    def _init_changelog(self):
        """初始化变更日志"""
        # 版本 0.1.0 - 初始版本
        self._add_version(
            version="0.1.0",
            release_date=date(2024, 1, 1),
            summary="Initial release with basic attack and defense capabilities",
            changes=[
                ChangeEntry(
                    type=ChangeType.ADDED,
                    description="Basic attack modules (prompt injection, jailbreak)",
                    version="0.1.0",
                ),
                ChangeEntry(
                    type=ChangeType.ADDED,
                    description="Defense modules (input filter, output filter)",
                    version="0.1.0",
                ),
                ChangeEntry(
                    type=ChangeType.ADDED,
                    description="CLI and API interfaces",
                    version="0.1.0",
                ),
            ],
        )

        # 版本 0.2.0 - 高级攻击模块
        self._add_version(
            version="0.2.0",
            release_date=date(2024, 6, 1),
            summary="Advanced attack modules and evaluation framework",
            changes=[
                ChangeEntry(
                    type=ChangeType.ADDED,
                    description="GCG and AutoDAN attack modules",
                    version="0.2.0",
                ),
                ChangeEntry(
                    type=ChangeType.ADDED,
                    description="TAP and PAIR attack modules",
                    version="0.2.0",
                ),
                ChangeEntry(
                    type=ChangeType.ADDED,
                    description="Evaluation framework with benchmarks",
                    version="0.2.0",
                ),
                ChangeEntry(
                    type=ChangeType.ADDED,
                    description="Red team orchestrator",
                    version="0.2.0",
                ),
            ],
        )

        # 版本 0.3.0 - 统一框架
        self._add_version(
            version="0.3.0",
            release_date=date(2025, 1, 1),
            summary="Unified attack framework with improved gradient computation",
            changes=[
                ChangeEntry(
                    type=ChangeType.ADDED,
                    description="Unified attack registry with dynamic registration",
                    version="0.3.0",
                    affected_components=["mox.attacks.registry"],
                ),
                ChangeEntry(
                    type=ChangeType.ADDED,
                    description="Multimodal attack support (image injection, visual prompt)",
                    version="0.3.0",
                    affected_components=["mox.attacks.multimodal_attacks"],
                ),
                ChangeEntry(
                    type=ChangeType.ADDED,
                    description="Knowledge extraction attacks (progressive, feature probing)",
                    version="0.3.0",
                    affected_components=["mox.attacks.knowledge_extraction"],
                ),
                ChangeEntry(
                    type=ChangeType.ADDED,
                    description="Deprecation management system",
                    version="0.3.0",
                    affected_components=["mox.core.deprecation"],
                ),
                ChangeEntry(
                    type=ChangeType.CHANGED,
                    description="Improved gradient computation for GCG attacks",
                    version="0.3.0",
                    affected_components=["mox.attacks.gradient_attack", "mox.attacks.gcg"],
                    breaking=False,
                    migration_guide="Use GradientBasedSuffixAttack instead of FGSMAttack/PGDAttack",
                ),
                ChangeEntry(
                    type=ChangeType.CHANGED,
                    description="Renamed MultimodalAdversarialAttack to TextBasedAdversarialAttack",
                    version="0.3.0",
                    affected_components=["mox.attacks.advanced_attacks"],
                    breaking=False,
                    migration_guide="Use TextBasedAdversarialAttack instead of MultimodalAdversarialAttack",
                ),
                ChangeEntry(
                    type=ChangeType.CHANGED,
                    description="Renamed KnowledgeDistillationAttack to KnowledgeExtractionAttack",
                    version="0.3.0",
                    affected_components=["mox.attacks.advanced_attacks"],
                    breaking=False,
                    migration_guide="Use KnowledgeExtractionAttack instead of KnowledgeDistillationAttack",
                ),
                ChangeEntry(
                    type=ChangeType.DEPRECATED,
                    description="FGSMAttack and PGDAttack",
                    version="0.3.0",
                    affected_components=["mox.attacks.gradient_attack"],
                    migration_guide="Use GradientBasedSuffixAttack with improved gradient computation",
                ),
                ChangeEntry(
                    type=ChangeType.DEPRECATED,
                    description="MultimodalAdversarialAttack alias",
                    version="0.3.0",
                    affected_components=["mox.attacks.advanced_attacks"],
                    migration_guide="Use TextBasedAdversarialAttack directly",
                ),
                ChangeEntry(
                    type=ChangeType.DEPRECATED,
                    description="KnowledgeDistillationAttack alias",
                    version="0.3.0",
                    affected_components=["mox.attacks.advanced_attacks"],
                    migration_guide="Use KnowledgeExtractionAttack directly",
                ),
                ChangeEntry(
                    type=ChangeType.FIXED,
                    description="Fixed gradient computation in GCG attacks",
                    version="0.3.0",
                    affected_components=["mox.attacks.gradient_attack", "mox.attacks.gcg"],
                ),
                ChangeEntry(
                    type=ChangeType.FIXED,
                    description="Fixed LLM Judge fallback mechanism",
                    version="0.3.0",
                    affected_components=["mox.evaluation.judge"],
                ),
                ChangeEntry(
                    type=ChangeType.FIXED,
                    description="Fixed red team evaluator accuracy",
                    version="0.3.0",
                    affected_components=["mox.evaluation.redteam"],
                ),
            ],
            breaking_changes=[
                "GradientAttackConfig default epsilon changed from 0.25 to 0.1",
                "GCGConfig default batch_size changed from 64 to 512",
            ],
            deprecations=[
                "FGSMAttack - Use GradientBasedSuffixAttack",
                "PGDAttack - Use GradientBasedSuffixAttack",
                "AdversarialSuffixAttack - Use GradientBasedSuffixAttack",
                "MultimodalAdversarialAttack - Use TextBasedAdversarialAttack",
                "KnowledgeDistillationAttack - Use KnowledgeExtractionAttack",
            ],
            migration_guides=[
                "See docs/migration/0.2_to_0.3.md for detailed migration guide",
            ],
        )

    def _add_version(
        self,
        version: str,
        release_date: date,
        summary: str = "",
        changes: Optional[List[ChangeEntry]] = None,
        breaking_changes: Optional[List[str]] = None,
        deprecations: Optional[List[str]] = None,
        migration_guides: Optional[List[str]] = None,
    ):
        """添加版本信息"""
        info = VersionInfo(
            version=version,
            release_date=release_date,
            changes=changes or [],
            summary=summary,
            breaking_changes=breaking_changes or [],
            deprecations=deprecations or [],
            migration_guides=migration_guides or [],
        )
        self._versions[version] = info

    def get_changelog(self) -> List[VersionInfo]:
        """获取完整变更日志"""
        return sorted(
            self._versions.values(),
            key=lambda v: v.release_date,
            reverse=True,
        )

    def get_version_info(self, version: str) -> Optional[VersionInfo]:
        """获取指定版本信息"""
        return self._versions.get(version)

    def get_current_version(self) -> str:
        """获取当前版本"""
        return self._current_version

    def get_changes_since(self, version: str) -> List[ChangeEntry]:
        """获取指定版本以来的所有变更"""
        changes = []
        for v_info in self._versions.values():
            if self._compare_versions(v_info.version, version) > 0:
                changes.extend(v_info.changes)
        return changes

    def get_deprecations_since(self, version: str) -> List[str]:
        """获取指定版本以来的所有弃用"""
        deprecations = []
        for v_info in self._versions.values():
            if self._compare_versions(v_info.version, version) > 0:
                deprecations.extend(v_info.deprecations)
        return deprecations

    def get_breaking_changes_since(self, version: str) -> List[str]:
        """获取指定版本以来的所有破坏性变更"""
        breaking = []
        for v_info in self._versions.values():
            if self._compare_versions(v_info.version, version) > 0:
                breaking.extend(v_info.breaking_changes)
        return breaking

    def get_migration_guide(self, from_version: str, to_version: str) -> List[str]:
        """获取迁移指南"""
        guides = []
        for v_info in self._versions.values():
            if self._compare_versions(v_info.version, from_version) > 0:
                if self._compare_versions(v_info.version, to_version) <= 0:
                    guides.extend(v_info.migration_guides)
        return guides

    def _compare_versions(self, v1: str, v2: str) -> int:
        """比较版本号"""

        def parse_version(v: str) -> List[int]:
            return [int(x) for x in v.split(".")]

        parts1 = parse_version(v1)
        parts2 = parse_version(v2)

        for p1, p2 in zip(parts1, parts2):
            if p1 < p2:
                return -1
            elif p1 > p2:
                return 1

        return 0

    def generate_changelog_markdown(self) -> str:
        """生成 Markdown 格式的变更日志"""
        lines = ["# Changelog\n"]
        lines.append("All notable changes to this project will be documented in this file.\n")
        lines.append(
            "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),\n"
        )
        lines.append(
            "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).\n"
        )

        for version_info in self.get_changelog():
            lines.append(f"\n## [{version_info.version}] - {version_info.release_date}\n")

            if version_info.summary:
                lines.append(f"{version_info.summary}\n")

            # 按类型分组
            changes_by_type: Dict[ChangeType, List[ChangeEntry]] = {}
            for change in version_info.changes:
                if change.type not in changes_by_type:
                    changes_by_type[change.type] = []
                changes_by_type[change.type].append(change)

            # 输出各类型变更
            for change_type in ChangeType:
                if change_type in changes_by_type:
                    lines.append(f"\n### {change_type.value.title()}\n")
                    for change in changes_by_type[change_type]:
                        breaking_marker = " **BREAKING**" if change.breaking else ""
                        lines.append(f"- {change.description}{breaking_marker}")
                        if change.affected_components:
                            lines.append(f"  - Affected: {', '.join(change.affected_components)}")
                        if change.migration_guide:
                            lines.append(f"  - Migration: {change.migration_guide}")

            # 破坏性变更
            if version_info.breaking_changes:
                lines.append("\n### Breaking Changes\n")
                for breaking in version_info.breaking_changes:
                    lines.append(f"- {breaking}")

            # 弃用
            if version_info.deprecations:
                lines.append("\n### Deprecations\n")
                for deprecation in version_info.deprecations:
                    lines.append(f"- {deprecation}")

            # 迁移指南
            if version_info.migration_guides:
                lines.append("\n### Migration Guides\n")
                for guide in version_info.migration_guides:
                    lines.append(f"- {guide}")

        return "\n".join(lines)

    def generate_migration_guide(self, from_version: str) -> str:
        """生成迁移指南"""
        lines = [f"# Migration Guide: {from_version} to {self._current_version}\n"]

        changes = self.get_changes_since(from_version)
        deprecations = self.get_deprecations_since(from_version)
        breaking_changes = self.get_breaking_changes_since(from_version)

        if breaking_changes:
            lines.append("\n## Breaking Changes\n")
            for i, breaking in enumerate(breaking_changes, 1):
                lines.append(f"{i}. {breaking}")

        if deprecations:
            lines.append("\n## Deprecations\n")
            lines.append(
                "The following features are deprecated and will be removed in future versions:\n"
            )
            for i, deprecation in enumerate(deprecations, 1):
                lines.append(f"{i}. {deprecation}")

        # 按组件分组的变更
        changes_by_component: Dict[str, List[ChangeEntry]] = {}
        for change in changes:
            for component in change.affected_components:
                if component not in changes_by_component:
                    changes_by_component[component] = []
                changes_by_component[component].append(change)

        if changes_by_component:
            lines.append("\n## Changes by Component\n")
            for component, component_changes in changes_by_component.items():
                lines.append(f"\n### {component}\n")
                for change in component_changes:
                    lines.append(f"- [{change.type.value}] {change.description}")
                    if change.migration_guide:
                        lines.append(f"  - Migration: {change.migration_guide}")

        return "\n".join(lines)


# 全局变更日志管理器
_manager: Optional[ChangelogManager] = None


def get_changelog_manager() -> ChangelogManager:
    """获取全局变更日志管理器"""
    global _manager
    if _manager is None:
        _manager = ChangelogManager()
    return _manager


def get_changelog() -> List[VersionInfo]:
    """获取变更日志"""
    manager = get_changelog_manager()
    return manager.get_changelog()


def get_current_version() -> str:
    """获取当前版本"""
    manager = get_changelog_manager()
    return manager.get_current_version()


def get_changes_since(version: str) -> List[ChangeEntry]:
    """获取指定版本以来的变更"""
    manager = get_changelog_manager()
    return manager.get_changes_since(version)


def get_deprecations_since(version: str) -> List[str]:
    """获取指定版本以来的弃用"""
    manager = get_changelog_manager()
    return manager.get_deprecations_since(version)


def get_breaking_changes_since(version: str) -> List[str]:
    """获取指定版本以来的破坏性变更"""
    manager = get_changelog_manager()
    return manager.get_breaking_changes_since(version)


def generate_changelog_markdown() -> str:
    """生成 Markdown 格式的变更日志"""
    manager = get_changelog_manager()
    return manager.generate_changelog_markdown()


def generate_migration_guide(from_version: str) -> str:
    """生成迁移指南"""
    manager = get_changelog_manager()
    return manager.generate_migration_guide(from_version)


__all__ = [
    "ChangeType",
    "ChangeEntry",
    "VersionInfo",
    "ChangelogManager",
    "get_changelog_manager",
    "get_changelog",
    "get_current_version",
    "get_changes_since",
    "get_deprecations_since",
    "get_breaking_changes_since",
    "generate_changelog_markdown",
    "generate_migration_guide",
]
