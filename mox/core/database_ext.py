"""扩展数据库模块 - 支持更多数据持久化功能"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
from contextlib import asynccontextmanager
from dataclasses import dataclass, field, asdict

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    Boolean,
    JSON,
    ForeignKey,
    Enum,
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship

from mox.core.config import settings
from mox.core.logging import get_logger

logger = get_logger("database_ext")

Base = declarative_base()


class ReportRecord(Base):
    """评估报告记录表"""

    __tablename__ = "report_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_name = Column(String(200), nullable=False)
    report_type = Column(String(50))
    model_name = Column(String(100))
    template_id = Column(Integer, ForeignKey("attack_template_records.id"), nullable=True)
    content = Column(Text)
    format = Column(String(20), default="json")
    summary = Column(JSON)
    file_path = Column(String(500))
    created_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class AttackTemplateRecord(Base):
    """攻击模板记录表"""

    __tablename__ = "attack_template_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    attack_type = Column(String(50), nullable=False)
    category = Column(String(50))
    content = Column(Text, nullable=False)
    variables = Column(JSON, default=list)
    is_public = Column(Boolean, default=True)
    is_favorite = Column(Boolean, default=False)
    usage_count = Column(Integer, default=0)
    tags = Column(JSON, default=list)
    created_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class ScheduledTaskRecord(Base):
    """定时任务记录表"""

    __tablename__ = "scheduled_task_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_name = Column(String(200), nullable=False)
    task_type = Column(String(50))
    cron_expression = Column(String(100))
    interval_minutes = Column(Integer)
    is_active = Column(Boolean, default=True)
    config = Column(JSON)
    last_run_at = Column(DateTime)
    next_run_at = Column(DateTime)
    run_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    created_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.now)


class AuditLogRecord(Base):
    """审计日志记录表"""

    __tablename__ = "audit_log_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100))
    username = Column(String(100))
    action = Column(String(100), nullable=False)
    resource = Column(String(200))
    method = Column(String(20))
    endpoint = Column(String(500))
    request_body = Column(Text)
    response_status = Column(Integer)
    ip_address = Column(String(50))
    user_agent = Column(Text)
    duration_ms = Column(Integer)
    is_sensitive = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)


class ScanScheduleRecord(Base):
    """扫描计划记录表"""

    __tablename__ = "scan_schedule_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_name = Column(String(200), nullable=False)
    scan_type = Column(String(50))
    target_models = Column(JSON, default=list)
    attack_types = Column(JSON, default=list)
    defense_types = Column(JSON, default=list)
    schedule_type = Column(String(20))
    cron_expression = Column(String(100))
    is_active = Column(Boolean, default=True)
    config = Column(JSON)
    last_run_at = Column(DateTime)
    next_run_at = Column(DateTime)
    status = Column(String(20), default="pending")
    created_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class CICDConfigRecord(Base):
    """CI/CD配置记录表"""

    __tablename__ = "cicd_config_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_name = Column(String(200), nullable=False)
    project_name = Column(String(200))
    project_url = Column(String(500))
    security_threshold = Column(Float, default=0.8)
    attack_types = Column(JSON, default=list)
    defense_types = Column(JSON, default=list)
    auto_approve = Column(Boolean, default=False)
    webhook_url = Column(String(500))
    webhook_secret = Column(String(200))
    is_active = Column(Boolean, default=True)
    config = Column(JSON)
    last_run_at = Column(DateTime)
    run_history = Column(JSON, default=list)
    created_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class ModelScoreRecord(Base):
    """模型安全评分记录表"""

    __tablename__ = "model_score_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String(100), nullable=False)
    model_provider = Column(String(50))
    security_score = Column(Float, default=0.0)
    attack_resistance = Column(Float, default=0.0)
    defense_effectiveness = Column(Float, default=0.0)
    robustness_score = Column(Float, default=0.0)
    scores = Column(JSON, default=dict)
    radar_data = Column(JSON, default=dict)
    benchmark_results = Column(JSON, default=dict)
    evaluated_at = Column(DateTime, default=datetime.now)


class ExtendedDatabase:
    """扩展数据库管理器"""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = Path("data/mox_ext.db")

        db_path.parent.mkdir(parents=True, exist_ok=True)

        self.db_url = f"sqlite+aiosqlite:///{db_path}"
        self.engine = create_async_engine(self.db_url, echo=False)
        self.async_session = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def init_db(self) -> None:
        """初始化数据库表"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info(f"Extended database initialized: {self.db_url}")

    async def close(self) -> None:
        """关闭数据库连接"""
        await self.engine.dispose()

    @asynccontextmanager
    async def get_session(self) -> AsyncSession:
        """获取数据库会话"""
        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def save_report(self, data: Dict[str, Any]) -> int:
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
            query = session.query(ReportRecord)
            if report_type:
                query = query.filter(ReportRecord.report_type == report_type)
            return await query.order_by(ReportRecord.created_at.desc()).limit(limit).all()

    async def save_template(self, data: Dict[str, Any]) -> int:
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
            query = session.query(AttackTemplateRecord)
            if attack_type:
                query = query.filter(AttackTemplateRecord.attack_type == attack_type)
            if is_favorite is not None:
                query = query.filter(AttackTemplateRecord.is_favorite == is_favorite)
            return await query.order_by(AttackTemplateRecord.usage_count.desc()).limit(limit).all()

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

    async def save_audit_log(self, data: Dict[str, Any]) -> int:
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
            query = session.query(AuditLogRecord)
            if user_id:
                query = query.filter(AuditLogRecord.user_id == user_id)
            if action:
                query = query.filter(AuditLogRecord.action == action)
            if start_date:
                query = query.filter(AuditLogRecord.created_at >= start_date)
            if end_date:
                query = query.filter(AuditLogRecord.created_at <= end_date)
            return await query.order_by(AuditLogRecord.created_at.desc()).limit(limit).all()

    async def save_scheduled_task(self, data: Dict[str, Any]) -> int:
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
            query = session.query(ScheduledTaskRecord)
            if is_active is not None:
                query = query.filter(ScheduledTaskRecord.is_active == is_active)
            return await query.order_by(ScheduledTaskRecord.created_at.desc()).all()

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

    async def save_scan_schedule(self, data: Dict[str, Any]) -> int:
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
            query = session.query(ScanScheduleRecord)
            if is_active is not None:
                query = query.filter(ScanScheduleRecord.is_active == is_active)
            return await query.order_by(ScanScheduleRecord.created_at.desc()).all()

    async def save_cicd_config(self, data: Dict[str, Any]) -> int:
        """保存CI/CD配置"""
        async with self.get_session() as session:
            record = CICDConfigRecord(**data)
            session.add(record)
            await session.flush()
            return record.id

    async def get_cicd_configs(self, is_active: Optional[bool] = None) -> List[CICDConfigRecord]:
        """获取CI/CD配置"""
        async with self.get_session() as session:
            query = session.query(CICDConfigRecord)
            if is_active is not None:
                query = query.filter(CICDConfigRecord.is_active == is_active)
            return await query.order_by(CICDConfigRecord.created_at.desc()).all()

    async def update_cicd_run_history(self, config_id: int, run_result: Dict[str, Any]) -> None:
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

    async def save_model_score(self, data: Dict[str, Any]) -> int:
        """保存模型评分"""
        async with self.get_session() as session:
            record = ModelScoreRecord(**data)
            session.add(record)
            await session.flush()
            return record.id

    async def get_model_scores(self, model_name: Optional[str] = None) -> List[ModelScoreRecord]:
        """获取模型评分"""
        async with self.get_session() as session:
            query = session.query(ModelScoreRecord)
            if model_name:
                query = query.filter(ModelScoreRecord.model_name == model_name)
            return await query.order_by(ModelScoreRecord.evaluated_at.desc()).all()

    async def get_latest_model_score(self, model_name: str) -> Optional[ModelScoreRecord]:
        """获取最新模型评分"""
        async with self.get_session() as session:
            return (
                await session.query(ModelScoreRecord)
                .filter(ModelScoreRecord.model_name == model_name)
                .order_by(ModelScoreRecord.evaluated_at.desc())
                .first()
            )


_default_ext_db: Optional[ExtendedDatabase] = None


def get_extended_database() -> ExtendedDatabase:
    """获取全局扩展数据库实例"""
    global _default_ext_db
    if _default_ext_db is None:
        _default_ext_db = ExtendedDatabase()
    return _default_ext_db


async def init_extended_database(db_path: Optional[Path] = None) -> ExtendedDatabase:
    """初始化扩展数据库"""
    db = ExtendedDatabase(db_path)
    await db.init_db()
    global _default_ext_db
    _default_ext_db = db
    return db
