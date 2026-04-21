"""数据库模块 - SQLAlchemy 2.0 最佳实践

支持：
- 异步连接池
- 类型安全查询
- 连接复用
- 更好的错误处理
- 性能优化
"""

from datetime import datetime
from typing import Optional, List, AsyncIterator
from pathlib import Path
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    Boolean,
    JSON,
    select,
    func,
    update,
    delete,
)
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.pool import NullPool, QueuePool

from .config import settings
from .logging import get_logger

logger = get_logger("database")


# ============ 基础模型类 ============

class Base(DeclarativeBase):
    """SQLAlchemy 2.0 声明式基类"""
    pass


# ============ 数据模型 ============

class AttackRecord(Base):
    """攻击记录表 - SQLAlchemy 2.0 风格"""
    __tablename__ = "attack_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    attack_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    original_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    adversarial_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    model_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result: Mapped[Optional[str]] = mapped_column(String(20), index=True)
    success_score: Mapped[float] = mapped_column(Float, default=0.0)
    iterations: Mapped[int] = mapped_column(Integer, default=0)
    model_name: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    record_meta: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)

    def __repr__(self) -> str:
        return f"<AttackRecord(id={self.id}, type={self.attack_type}, result={self.result})>"


class DefenseRecord(Base):
    """防御记录表 - SQLAlchemy 2.0 风格"""
    __tablename__ = "defense_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    defense_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    output_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_malicious: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    detected_patterns: Mapped[list] = mapped_column(JSON, default=list)
    model_name: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    record_meta: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)

    def __repr__(self) -> str:
        return f"<DefenseRecord(id={self.id}, type={self.defense_type}, malicious={self.is_malicious})>"


class EvaluationRecord(Base):
    """评估记录表 - SQLAlchemy 2.0 风格"""
    __tablename__ = "evaluation_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    evaluation_name: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    total_attacks: Mapped[int] = mapped_column(Integer, default=0)
    successful_attacks: Mapped[int] = mapped_column(Integer, default=0)
    failed_attacks: Mapped[int] = mapped_column(Integer, default=0)
    attack_success_rate: Mapped[float] = mapped_column(Float, default=0.0)
    defense_success_rate: Mapped[float] = mapped_column(Float, default=0.0)
    avg_iterations: Mapped[float] = mapped_column(Float, default=0.0)
    model_name: Mapped[Optional[str]] = mapped_column(String(50))
    record_meta: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)

    def __repr__(self) -> str:
        return f"<EvaluationRecord(id={self.id}, name={self.evaluation_name})>"


class ReportRecord(Base):
    """评估报告记录表"""
    __tablename__ = "report_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    report_name: Mapped[str] = mapped_column(String(200), nullable=False)
    report_type: Mapped[Optional[str]] = mapped_column(String(50))
    model_name: Mapped[Optional[str]] = mapped_column(String(100))
    template_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text)
    format: Mapped[str] = mapped_column(String(20), default="json")
    summary: Mapped[Optional[dict]] = mapped_column(JSON)
    file_path: Mapped[Optional[str]] = mapped_column(String(500))
    created_by: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class AttackTemplateRecord(Base):
    """攻击模板记录表"""
    __tablename__ = "attack_template_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    attack_type: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(50))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[list] = mapped_column(JSON, default=list)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    created_by: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class ScheduledTaskRecord(Base):
    """定时任务记录表"""
    __tablename__ = "scheduled_task_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_name: Mapped[str] = mapped_column(String(200), nullable=False)
    task_type: Mapped[Optional[str]] = mapped_column(String(50))
    cron_expression: Mapped[Optional[str]] = mapped_column(String(100))
    interval_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    config: Mapped[Optional[dict]] = mapped_column(JSON)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    next_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    run_count: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class AuditLogRecord(Base):
    """审计日志记录表"""
    __tablename__ = "audit_log_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(100))
    username: Mapped[Optional[str]] = mapped_column(String(100))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource: Mapped[Optional[str]] = mapped_column(String(200))
    method: Mapped[Optional[str]] = mapped_column(String(20))
    endpoint: Mapped[Optional[str]] = mapped_column(String(500))
    request_body: Mapped[Optional[str]] = mapped_column(Text)
    response_status: Mapped[Optional[int]] = mapped_column(Integer)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
    is_sensitive: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class ScanScheduleRecord(Base):
    """扫描计划记录表"""
    __tablename__ = "scan_schedule_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scan_name: Mapped[str] = mapped_column(String(200), nullable=False)
    scan_type: Mapped[Optional[str]] = mapped_column(String(50))
    target_models: Mapped[list] = mapped_column(JSON, default=list)
    attack_types: Mapped[list] = mapped_column(JSON, default=list)
    defense_types: Mapped[list] = mapped_column(JSON, default=list)
    schedule_type: Mapped[Optional[str]] = mapped_column(String(20))
    cron_expression: Mapped[Optional[str]] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    config: Mapped[Optional[dict]] = mapped_column(JSON)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    next_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_by: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class CICDConfigRecord(Base):
    """CI/CD配置记录表"""
    __tablename__ = "cicd_config_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    config_name: Mapped[str] = mapped_column(String(200), nullable=False)
    project_name: Mapped[Optional[str]] = mapped_column(String(200))
    project_url: Mapped[Optional[str]] = mapped_column(String(500))
    security_threshold: Mapped[float] = mapped_column(Float, default=0.8)
    attack_types: Mapped[list] = mapped_column(JSON, default=list)
    defense_types: Mapped[list] = mapped_column(JSON, default=list)
    auto_approve: Mapped[bool] = mapped_column(Boolean, default=False)
    webhook_url: Mapped[Optional[str]] = mapped_column(String(500))
    webhook_secret: Mapped[Optional[str]] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    config: Mapped[Optional[dict]] = mapped_column(JSON)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    run_history: Mapped[list] = mapped_column(JSON, default=list)
    created_by: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class ModelScoreRecord(Base):
    """模型安全评分记录表"""
    __tablename__ = "model_score_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_provider: Mapped[Optional[str]] = mapped_column(String(50))
    security_score: Mapped[float] = mapped_column(Float, default=0.0)
    attack_resistance: Mapped[float] = mapped_column(Float, default=0.0)
    defense_effectiveness: Mapped[float] = mapped_column(Float, default=0.0)
    robustness_score: Mapped[float] = mapped_column(Float, default=0.0)
    scores: Mapped[dict] = mapped_column(JSON, default=dict)
    radar_data: Mapped[dict] = mapped_column(JSON, default=dict)
    benchmark_results: Mapped[dict] = mapped_column(JSON, default=dict)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


# ============ 数据库管理器 ============

class Database:
    """数据库管理器 - SQLAlchemy 2.0 最佳实践
    
    特性：
    - 异步连接池
    - 类型安全查询
    - 自动重连
    - 性能监控
    """

    def __init__(
        self,
        db_path: Optional[Path] = None,
        db_url: Optional[str] = None,
        echo: bool = False,
    ):
        if db_url:
            self.db_url = db_url
        elif db_path:
            db_path = Path(db_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            self.db_url = f"sqlite+aiosqlite:///{db_path}"
        else:
            self.db_url = settings.DATABASE_URL
            if self.db_url.startswith("sqlite"):
                db_path = Path(self.db_url.replace("sqlite+aiosqlite:///", ""))
                db_path.parent.mkdir(parents=True, exist_ok=True)

        # 创建引擎
        self.engine: AsyncEngine = create_async_engine(
            self.db_url,
            **self._get_engine_kwargs(echo),
        )

        # 创建会话工厂 - 使用 async_sessionmaker
        self.session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

        logger.info(f"Database engine created: {self._mask_url(self.db_url)}")

    def _get_engine_kwargs(self, echo: bool = False) -> dict:
        """根据数据库类型获取引擎配置"""
        kwargs = {"echo": echo or (settings.DEBUG and settings.LOG_LEVEL == "DEBUG")}

        if self.db_url.startswith("sqlite"):
            kwargs["poolclass"] = NullPool
            kwargs["connect_args"] = {
                "check_same_thread": False,
                "timeout": 30,
            }
        elif self.db_url.startswith("postgresql"):
            kwargs["poolclass"] = QueuePool
            kwargs.update({
                "pool_size": settings.DB_POOL_SIZE,
                "max_overflow": settings.DB_MAX_OVERFLOW,
                "pool_timeout": settings.DB_POOL_TIMEOUT,
                "pool_recycle": settings.DB_POOL_RECYCLE,
                "pool_pre_ping": True,
            })
        else:
            kwargs["pool_pre_ping"] = True

        return kwargs

    def _mask_url(self, url: str) -> str:
        """隐藏 URL 中的敏感信息"""
        if "@" in url:
            parts = url.split("://")
            if len(parts) == 2:
                protocol, rest = parts
                if "@" in rest:
                    credentials, host = rest.split("@", 1)
                    if ":" in credentials:
                        user, _ = credentials.split(":", 1)
                        return f"{protocol}://{user}:***@{host}"
        return url

    async def init_db(self) -> None:
        """初始化数据库表"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized")

    async def close(self) -> None:
        """关闭数据库连接池"""
        await self.engine.dispose()
        logger.info("Database connection pool closed")

    @asynccontextmanager
    async def get_session(self) -> AsyncIterator[AsyncSession]:
        """获取数据库会话（上下文管理器）"""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    # ============ 攻击记录操作 ============

    async def save_attack_record(
        self,
        attack_type: str,
        original_prompt: str,
        adversarial_prompt: Optional[str] = None,
        model_response: Optional[str] = None,
        result: Optional[str] = None,
        success_score: float = 0.0,
        iterations: int = 0,
        model_name: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> int:
        """保存攻击记录"""
        async with self.get_session() as session:
            record = AttackRecord(
                attack_type=attack_type,
                original_prompt=original_prompt,
                adversarial_prompt=adversarial_prompt,
                model_response=model_response,
                result=result,
                success_score=success_score,
                iterations=iterations,
                model_name=model_name,
                record_meta=metadata or {},
            )
            session.add(record)
            await session.flush()
            await session.refresh(record)
            return record.id

    async def get_attack_records(
        self,
        limit: int = 100,
        attack_type: Optional[str] = None,
        offset: int = 0,
    ) -> List[AttackRecord]:
        """获取攻击记录 - 使用 SQLAlchemy 2.0 select()"""
        async with self.get_session() as session:
            stmt = select(AttackRecord)
            if attack_type:
                stmt = stmt.where(AttackRecord.attack_type == attack_type)
            stmt = stmt.order_by(AttackRecord.created_at.desc()).limit(limit).offset(offset)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def count_attack_records(self, attack_type: Optional[str] = None) -> int:
        """统计攻击记录数量"""
        async with self.get_session() as session:
            stmt = select(func.count(AttackRecord.id))
            if attack_type:
                stmt = stmt.where(AttackRecord.attack_type == attack_type)
            result = await session.execute(stmt)
            return result.scalar() or 0

    # ============ 防御记录操作 ============

    async def save_defense_record(
        self,
        defense_type: str,
        input_text: str,
        output_text: Optional[str] = None,
        is_malicious: bool = False,
        confidence: float = 0.0,
        detected_patterns: Optional[list] = None,
        model_name: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> int:
        """保存防御记录"""
        async with self.get_session() as session:
            record = DefenseRecord(
                defense_type=defense_type,
                input_text=input_text,
                output_text=output_text,
                is_malicious=is_malicious,
                confidence=confidence,
                detected_patterns=detected_patterns or [],
                model_name=model_name,
                record_meta=metadata or {},
            )
            session.add(record)
            await session.flush()
            await session.refresh(record)
            return record.id

    async def get_defense_records(
        self,
        limit: int = 100,
        defense_type: Optional[str] = None,
        offset: int = 0,
    ) -> List[DefenseRecord]:
        """获取防御记录"""
        async with self.get_session() as session:
            stmt = select(DefenseRecord)
            if defense_type:
                stmt = stmt.where(DefenseRecord.defense_type == defense_type)
            stmt = stmt.order_by(DefenseRecord.created_at.desc()).limit(limit).offset(offset)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def count_defense_records(self, defense_type: Optional[str] = None) -> int:
        """统计防御记录数量"""
        async with self.get_session() as session:
            stmt = select(func.count(DefenseRecord.id))
            if defense_type:
                stmt = stmt.where(DefenseRecord.defense_type == defense_type)
            result = await session.execute(stmt)
            return result.scalar() or 0

    # ============ 统计信息 ============

    async def get_stats(self) -> dict:
        """获取数据库统计信息"""
        return {
            "total_attacks": await self.count_attack_records(),
            "total_defenses": await self.count_defense_records(),
        }

    async def get_attack_stats_by_type(self) -> dict:
        """按类型统计攻击记录"""
        async with self.get_session() as session:
            stmt = (
                select(
                    AttackRecord.attack_type,
                    func.count(AttackRecord.id).label("count"),
                    func.avg(AttackRecord.success_score).label("avg_score"),
                )
                .group_by(AttackRecord.attack_type)
            )
            result = await session.execute(stmt)
            return {
                row.attack_type: {
                    "count": row.count,
                    "avg_score": row.avg_score or 0.0,
                }
                for row in result
            }

    # ============ 报告与模板操作 ============

    async def save_report(self, data: dict) -> int:
        """保存报告"""
        async with self.get_session() as session:
            record = ReportRecord(**data)
            session.add(record)
            await session.flush()
            return record.id

    async def get_reports(
        self,
        limit: int = 50,
        report_type: Optional[str] = None,
    ) -> List[ReportRecord]:
        """获取报告列表"""
        async with self.get_session() as session:
            stmt = select(ReportRecord)
            if report_type:
                stmt = stmt.where(ReportRecord.report_type == report_type)
            stmt = stmt.order_by(ReportRecord.created_at.desc()).limit(limit)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def save_template(self, data: dict) -> int:
        """保存攻击模板"""
        async with self.get_session() as session:
            record = AttackTemplateRecord(**data)
            session.add(record)
            await session.flush()
            return record.id

    async def get_templates(
        self,
        limit: int = 100,
        attack_type: Optional[str] = None,
        is_favorite: Optional[bool] = None,
    ) -> List[AttackTemplateRecord]:
        """获取攻击模板列表"""
        async with self.get_session() as session:
            stmt = select(AttackTemplateRecord)
            if attack_type:
                stmt = stmt.where(AttackTemplateRecord.attack_type == attack_type)
            if is_favorite is not None:
                stmt = stmt.where(AttackTemplateRecord.is_favorite == is_favorite)
            stmt = stmt.order_by(AttackTemplateRecord.usage_count.desc()).limit(limit)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def update_template_usage(self, template_id: int) -> None:
        """更新模板使用次数"""
        async with self.get_session() as session:
            template = await session.get(AttackTemplateRecord, template_id)
            if template:
                template.usage_count += 1

    async def toggle_template_favorite(self, template_id: int) -> bool:
        """切换模板收藏状态"""
        async with self.get_session() as session:
            template = await session.get(AttackTemplateRecord, template_id)
            if template:
                template.is_favorite = not template.is_favorite
                return template.is_favorite
            return False

    # ============ 审计与其他记录 ============

    async def save_audit_log(self, data: dict) -> int:
        """保存审计日志"""
        async with self.get_session() as session:
            record = AuditLogRecord(**data)
            session.add(record)
            await session.flush()
            return record.id

    async def get_audit_logs(
        self,
        limit: int = 100,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[AuditLogRecord]:
        """获取审计日志"""
        async with self.get_session() as session:
            stmt = select(AuditLogRecord)
            if user_id:
                stmt = stmt.where(AuditLogRecord.user_id == user_id)
            if action:
                stmt = stmt.where(AuditLogRecord.action == action)
            if start_date:
                stmt = stmt.where(AuditLogRecord.created_at >= start_date)
            if end_date:
                stmt = stmt.where(AuditLogRecord.created_at <= end_date)
            stmt = stmt.order_by(AuditLogRecord.created_at.desc()).limit(limit)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def save_scheduled_task(self, data: dict) -> int:
        """保存定时任务"""
        async with self.get_session() as session:
            record = ScheduledTaskRecord(**data)
            session.add(record)
            await session.flush()
            return record.id

    async def get_scheduled_tasks(
        self, is_active: Optional[bool] = None
    ) -> List[ScheduledTaskRecord]:
        """获取定时任务"""
        async with self.get_session() as session:
            stmt = select(ScheduledTaskRecord)
            if is_active is not None:
                stmt = stmt.where(ScheduledTaskRecord.is_active == is_active)
            stmt = stmt.order_by(ScheduledTaskRecord.created_at.desc())
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def update_scheduled_task_status(self, task_id: int, success: bool) -> None:
        """更新定时任务状态"""
        async with self.get_session() as session:
            task = await session.get(ScheduledTaskRecord, task_id)
            if task:
                task.run_count += 1
                if success:
                    task.success_count += 1
                else:
                    task.failure_count += 1
                task.last_run_at = datetime.now()

    async def save_scan_schedule(self, data: dict) -> int:
        """保存扫描计划"""
        async with self.get_session() as session:
            record = ScanScheduleRecord(**data)
            session.add(record)
            await session.flush()
            return record.id

    async def get_scan_schedules(
        self, is_active: Optional[bool] = None
    ) -> List[ScanScheduleRecord]:
        """获取扫描计划"""
        async with self.get_session() as session:
            stmt = select(ScanScheduleRecord)
            if is_active is not None:
                stmt = stmt.where(ScanScheduleRecord.is_active == is_active)
            stmt = stmt.order_by(ScanScheduleRecord.created_at.desc())
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def save_cicd_config(self, data: dict) -> int:
        """保存CI/CD配置"""
        async with self.get_session() as session:
            record = CICDConfigRecord(**data)
            session.add(record)
            await session.flush()
            return record.id

    async def get_cicd_configs(self, is_active: Optional[bool] = None) -> List[CICDConfigRecord]:
        """获取CI/CD配置"""
        async with self.get_session() as session:
            stmt = select(CICDConfigRecord)
            if is_active is not None:
                stmt = stmt.where(CICDConfigRecord.is_active == is_active)
            stmt = stmt.order_by(CICDConfigRecord.created_at.desc())
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def update_cicd_run_history(self, config_id: int, run_result: dict) -> None:
        """更新CI/CD运行历史"""
        async with self.get_session() as session:
            config = await session.get(CICDConfigRecord, config_id)
            if config:
                history = config.run_history or []
                history.append(run_result)
                if len(history) > 100:
                    history = history[-100:]
                config.run_history = history
                config.last_run_at = datetime.now()

    async def save_model_score(self, data: dict) -> int:
        """保存模型评分"""
        async with self.get_session() as session:
            record = ModelScoreRecord(**data)
            session.add(record)
            await session.flush()
            return record.id

    async def get_model_scores(self, model_name: Optional[str] = None) -> List[ModelScoreRecord]:
        """获取模型评分"""
        async with self.get_session() as session:
            stmt = select(ModelScoreRecord)
            if model_name:
                stmt = stmt.where(ModelScoreRecord.model_name == model_name)
            stmt = stmt.order_by(ModelScoreRecord.evaluated_at.desc())
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_latest_model_score(self, model_name: str) -> Optional[ModelScoreRecord]:
        """获取最新模型评分"""
        async with self.get_session() as session:
            stmt = select(ModelScoreRecord).where(ModelScoreRecord.model_name == model_name).order_by(ModelScoreRecord.evaluated_at.desc()).limit(1)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()


# ============ 全局实例 ============

_default_db: Optional[Database] = None


def get_database() -> Database:
    """获取全局数据库实例"""
    global _default_db
    if _default_db is None:
        _default_db = Database()
    return _default_db


async def init_database(
    db_path: Optional[Path] = None,
    db_url: Optional[str] = None,
) -> Database:
    """初始化数据库"""
    db = Database(db_path=db_path, db_url=db_url)
    await db.init_db()
    global _default_db
    _default_db = db
    return db


async def close_database() -> None:
    """关闭数据库连接"""
    global _default_db
    if _default_db is not None:
        await _default_db.close()
        _default_db = None
