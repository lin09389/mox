"""攻击循环配置

使用 Pydantic 提供强类型验证和清晰的字段级错误提示。
支持从 YAML / JSON 文件加载配置。
"""

import json
from pathlib import Path
from typing import List, Optional, Any, Dict

import yaml
from pydantic import BaseModel, Field, field_validator, ValidationError


class AttackLoopConfig(BaseModel):
    """攻击循环完整配置"""

    # === 核心配置 ===
    models: List[str] = Field(..., min_length=1, description="目标模型列表")
    attack_types: List[str] = Field(..., min_length=1, description="攻击类型列表")
    prompts: List[str] = Field(default_factory=list, description="测试提示列表")
    iterations_per_combo: int = Field(default=1, ge=1, le=1000, description="每个组合的测试次数")
    delay_between_tests: float = Field(default=1.0, ge=0, le=600, description="测试间隔（秒）")
    max_concurrency: int = Field(default=1, ge=1, le=50, description="最大并发数")
    max_retries: int = Field(default=3, ge=0, le=20, description="失败重试次数")
    retry_delay: float = Field(default=1.0, ge=0, le=60, description="重试延迟（秒）")

    # === 输出配置 ===
    output_dir: str = Field(default="attack_loop_results", description="输出目录")

    # === LLM 配置 ===
    base_url: str = Field(default="http://localhost:11434/v1", description="Ollama / API 服务地址")

    # === 攻击参数 ===
    success_threshold: float = Field(default=0.6, ge=0, le=1, description="成功判定阈值")
    max_iterations: int = Field(default=5, ge=1, le=500, description="单次攻击最大迭代次数")

    # === 随机提示配置 ===
    random_prompts: bool = Field(default=False, description="是否启用随机提示生成")
    random_prompt_count: int = Field(default=10, ge=1, le=10000, description="随机提示生成数量（当 random_prompts=true 时生效）")
    random_prompt_templates: List[str] = Field(default_factory=list, description="自定义随机提示模板")

    # === 检查点配置 ===
    checkpoint_enabled: bool = Field(default=True, description="是否启用检查点（断点续跑）")
    checkpoint_interval: int = Field(default=10, ge=1, le=10000, description="检查点保存间隔（每完成 N 个测试保存一次）")

    # === 日志配置 ===
    log_file: Optional[str] = Field(default=None, description="日志文件路径")
    log_level: str = Field(default="INFO", description="日志级别")

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"日志级别必须是以下之一: {', '.join(sorted(valid_levels))}")
        return v_upper

    # === 配置加载方法 ===

    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'AttackLoopConfig':
        """从 YAML 文件加载配置，提供清晰的字段级错误提示

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: YAML 解析失败或字段验证失败（含具体字段信息）
        """
        path = Path(yaml_path)
        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {yaml_path}")

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"YAML 解析失败: {e}") from e

        if not isinstance(data, dict):
            raise ValueError("YAML 文件内容必须是键值对格式（顶层为 mapping）")

        return cls._from_dict_with_clear_errors(data, source=f"YAML 文件 {yaml_path}")

    @classmethod
    def from_json(cls, json_path: str) -> 'AttackLoopConfig':
        """从 JSON 文件加载配置

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: JSON 解析失败或字段验证失败（含具体字段信息）
        """
        path = Path(json_path)
        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {json_path}")

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 解析失败: {e}") from e

        if not isinstance(data, dict):
            raise ValueError("JSON 文件内容必须是对象格式（顶层为 object）")

        return cls._from_dict_with_clear_errors(data, source=f"JSON 文件 {json_path}")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AttackLoopConfig':
        """从字典加载配置，带清晰错误提示"""
        return cls._from_dict_with_clear_errors(data, source="字典数据")

    @classmethod
    def _from_dict_with_clear_errors(cls, data: Dict[str, Any], source: str) -> 'AttackLoopConfig':
        """从字典加载配置，将 Pydantic 验证错误转换为人类可读的消息"""
        try:
            return cls(**data)
        except ValidationError as e:
            errors = e.errors()
            error_lines = [f"配置验证失败（来源: {source}），共 {len(errors)} 个错误:"]
            for i, err in enumerate(errors, 1):
                loc = " -> ".join(str(loc) for loc in err["loc"])
                msg = err["msg"]
                error_lines.append(f"  {i}. 字段 '{loc}': {msg}")
            raise ValueError("\n".join(error_lines)) from e

    def to_yaml(self, yaml_path: str) -> Path:
        """保存配置到 YAML 文件"""
        path = Path(yaml_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(
                self.model_dump(),
                f,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False
            )
        return path

    def to_json(self, json_path: str) -> Path:
        """保存配置到 JSON 文件"""
        path = Path(json_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.model_dump(), f, ensure_ascii=False, indent=2)
        return path

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.model_dump()

    def get_effective_prompts(self) -> int:
        """获取实际生效的提示数量

        如果启用了随机提示，则返回 random_prompt_count；
        否则返回 prompts 列表长度。
        """
        if self.random_prompts:
            return self.random_prompt_count
        return len(self.prompts)

    def calculate_total_tests(self) -> int:
        """计算总测试数"""
        return (
            len(self.models)
            * len(self.attack_types)
            * self.get_effective_prompts()
            * self.iterations_per_combo
        )
