"""数据库模块 - SQLAlchemy 2.0 最佳实践

支持：
- 异步连接池
- 类型安全查询
- 连接复用
- 更好的错误处理
- 性能优化
"""

from datetime import datetime
from typing import Optional, List, AsyncIterator, Dict, Any
from pathlib import Path
from contextlib import asynccontextmanager

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
    select,
    func,
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


def get_data_dir() -> Path:
    """Resolve writable data directory (MOX_DATA_DIR / settings.DATA_DIR)."""
    path = Path(settings.DATA_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_default_db_path(filename: str = "mox.db") -> Path:
    return get_data_dir() / filename


def resolve_database_url(db_url: Optional[str] = None) -> str:
    if db_url:
        return db_url
    url = settings.DATABASE_URL
    if url.startswith("sqlite+aiosqlite:///"):
        suffix = url.removeprefix("sqlite+aiosqlite:///")
        if suffix in {"data/mox.db", "mox.db"} or suffix.replace("\\", "/").endswith("/mox.db"):
            return f"sqlite+aiosqlite:///{get_default_db_path('mox.db').as_posix()}"
    return url


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


_CORE_TABLES = (
    AttackRecord.__table__,
    DefenseRecord.__table__,
    EvaluationRecord.__table__,
)


# ============ 扩展数据模型 (audit / reports / scheduling) ============


class UserAccountRecord(Base):
    __tablename__ = "user_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False, unique=True, index=True)
    email = Column(String(200))
    password_hash = Column(String(200), nullable=False)
    scopes = Column(JSON, default=list)
    disabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)


class ReportRecord(Base):
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


_EXTENDED_TABLES = (
    UserAccountRecord.__table__,
    ReportRecord.__table__,
    AttackTemplateRecord.__table__,
    ScheduledTaskRecord.__table__,
    AuditLogRecord.__table__,
    ScanScheduleRecord.__table__,
    CICDConfigRecord.__table__,
    ModelScoreRecord.__table__,
)

_ALL_TABLES = _CORE_TABLES + _EXTENDED_TABLES

_EXTENDED_MODELS = (
    UserAccountRecord,
    ReportRecord,
    AttackTemplateRecord,
    ScheduledTaskRecord,
    AuditLogRecord,
    ScanScheduleRecord,
    CICDConfigRecord,
    ModelScoreRecord,
)

_LEGACY_EXT_MARKER = ".mox_legacy_ext_migrated"


def _sqlite_db_path(db_url: str) -> Optional[Path]:
    if db_url.startswith("sqlite+aiosqlite:///"):
        return Path(db_url.removeprefix("sqlite+aiosqlite:///"))
    return None


def _model_from_row(model: type, row: Any) -> Any:
    columns = [column.name for column in model.__table__.columns]
    return model(**{column: getattr(row, column) for column in columns})


async def migrate_legacy_extended_database(target: "Database") -> int:
    """One-time import from legacy data/mox_ext.db into the unified database."""
    legacy_path = get_default_db_path("mox_ext.db")
    main_path = _sqlite_db_path(target.db_url)
    if main_path is None or not legacy_path.exists():
        return 0
    if legacy_path.resolve() == main_path.resolve():
        return 0

    marker = get_data_dir() / _LEGACY_EXT_MARKER
    if marker.exists():
        return 0

    legacy = Database(db_path=legacy_path)
    migrated = 0
    try:
        async with target.get_session() as target_session:
            async with legacy.get_session() as legacy_session:
                for model in _EXTENDED_MODELS:
                    rows = (await legacy_session.execute(select(model))).scalars().all()
                    for row in rows:
                        row_id = getattr(row, "id", None)
                        if row_id is not None and await target_session.get(model, row_id):
                            continue
                        if model is UserAccountRecord:
                            existing = (
                                await target_session.execute(
                                    select(UserAccountRecord).where(
                                        UserAccountRecord.username == row.username
                                    )
                                )
                            ).scalars().first()
                            if existing:
                                continue
                        target_session.add(_model_from_row(model, row))
                        migrated += 1
    finally:
        await legacy.close()

    backup = legacy_path.with_suffix(".db.bak")
    if backup.exists():
        backup.unlink()
    legacy_path.rename(backup)
    marker.write_text(f"backup={backup.name}\nrows={migrated}\n", encoding="utf-8")
    logger.info(
        "Legacy extended DB migrated into unified store (%s rows, backup=%s)",
        migrated,
        backup.name,
    )
    return migrated


# ============ 数据库管理器 ============


class Database:
    """数据库管理器 - SQLAlchemy 2.0 最佳实践

    特性：
    - 异步连接池
    - 类型安全查询
    - 自动重连
    - 性能监控
    - 统一存储：历史记录 + 报告/用户/审计/模板
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
            self.db_url = f"sqlite+aiosqlite:///{db_path.as_posix()}"
        else:
            self.db_url = resolve_database_url()
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
            kwargs.update(
                {
                    "pool_size": settings.DB_POOL_SIZE,
                    "max_overflow": settings.DB_MAX_OVERFLOW,
                    "pool_timeout": settings.DB_POOL_TIMEOUT,
                    "pool_recycle": settings.DB_POOL_RECYCLE,
                    "pool_pre_ping": True,
                }
            )
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
        """Initialize all tables and migrate legacy mox_ext.db if present."""
        async with self.engine.begin() as conn:
            await conn.run_sync(
                lambda sync_conn: Base.metadata.create_all(
                    sync_conn, tables=list(_ALL_TABLES)
                )
            )
        migrated = await migrate_legacy_extended_database(self)
        logger.info(
            "Database tables initialized%s",
            f" (migrated {migrated} legacy rows)" if migrated else "",
        )

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

    # ============ 扩展表操作 (报告/用户/审计/模板) ============

    async def save_report(self, data: Dict[str, Any]) -> int:
        async with self.get_session() as session:
            record = ReportRecord(**data)
            session.add(record)
            await session.flush()
            return record.id

    async def get_reports(
        self, limit: int = 50, report_type: Optional[str] = None
    ) -> List[ReportRecord]:
        async with self.get_session() as session:
            stmt = select(ReportRecord)
            if report_type:
                stmt = stmt.where(ReportRecord.report_type == report_type)
            stmt = stmt.order_by(ReportRecord.created_at.desc()).limit(limit)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_report(self, report_id: int) -> Optional[ReportRecord]:
        async with self.get_session() as session:
            return await session.get(ReportRecord, report_id)

    async def delete_report(self, report_id: int) -> bool:
        async with self.get_session() as session:
            record = await session.get(ReportRecord, report_id)
            if not record:
                return False
            await session.delete(record)
            return True

    async def save_user_account(self, data: Dict[str, Any]) -> int:
        async with self.get_session() as session:
            record = UserAccountRecord(**data)
            session.add(record)
            await session.flush()
            return record.id

    async def get_user_account(self, username: str) -> Optional[UserAccountRecord]:
        async with self.get_session() as session:
            stmt = select(UserAccountRecord).where(UserAccountRecord.username == username)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def list_user_accounts(self) -> List[UserAccountRecord]:
        async with self.get_session() as session:
            result = await session.execute(select(UserAccountRecord))
            return list(result.scalars().all())

    async def save_template(self, data: Dict[str, Any]) -> int:
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
        async with self.get_session() as session:
            template = await session.get(AttackTemplateRecord, template_id)
            if template:
                template.usage_count += 1

    async def toggle_template_favorite(self, template_id: int) -> bool:
        async with self.get_session() as session:
            template = await session.get(AttackTemplateRecord, template_id)
            if template:
                template.is_favorite = not template.is_favorite
                return template.is_favorite
            return False

    async def get_template(self, template_id: int) -> Optional[AttackTemplateRecord]:
        async with self.get_session() as session:
            return await session.get(AttackTemplateRecord, template_id)

    async def update_template(
        self, template_id: int, data: Dict[str, Any]
    ) -> Optional[AttackTemplateRecord]:
        async with self.get_session() as session:
            template = await session.get(AttackTemplateRecord, template_id)
            if not template:
                return None
            for key, value in data.items():
                if key != "id" and hasattr(template, key):
                    setattr(template, key, value)
            return template

    async def delete_template(self, template_id: int) -> bool:
        async with self.get_session() as session:
            template = await session.get(AttackTemplateRecord, template_id)
            if not template:
                return False
            await session.delete(template)
            return True

    async def save_audit_log(self, data: Dict[str, Any]) -> int:
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

    async def save_scheduled_task(self, data: Dict[str, Any]) -> int:
        async with self.get_session() as session:
            record = ScheduledTaskRecord(**data)
            session.add(record)
            await session.flush()
            return record.id

    async def get_scheduled_tasks(
        self, is_active: Optional[bool] = None
    ) -> List[ScheduledTaskRecord]:
        async with self.get_session() as session:
            stmt = select(ScheduledTaskRecord)
            if is_active is not None:
                stmt = stmt.where(ScheduledTaskRecord.is_active == is_active)
            stmt = stmt.order_by(ScheduledTaskRecord.created_at.desc())
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def update_scheduled_task_status(self, task_id: int, success: bool) -> None:
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
        async with self.get_session() as session:
            record = ScanScheduleRecord(**data)
            session.add(record)
            await session.flush()
            return record.id

    async def get_scan_schedules(
        self, is_active: Optional[bool] = None
    ) -> List[ScanScheduleRecord]:
        async with self.get_session() as session:
            stmt = select(ScanScheduleRecord)
            if is_active is not None:
                stmt = stmt.where(ScanScheduleRecord.is_active == is_active)
            stmt = stmt.order_by(ScanScheduleRecord.created_at.desc())
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def save_cicd_config(self, data: Dict[str, Any]) -> int:
        async with self.get_session() as session:
            record = CICDConfigRecord(**data)
            session.add(record)
            await session.flush()
            return record.id

    async def get_cicd_configs(self, is_active: Optional[bool] = None) -> List[CICDConfigRecord]:
        async with self.get_session() as session:
            stmt = select(CICDConfigRecord)
            if is_active is not None:
                stmt = stmt.where(CICDConfigRecord.is_active == is_active)
            stmt = stmt.order_by(CICDConfigRecord.created_at.desc())
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def update_cicd_run_history(self, config_id: int, run_result: Dict[str, Any]) -> None:
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
        async with self.get_session() as session:
            record = ModelScoreRecord(**data)
            session.add(record)
            await session.flush()
            return record.id

    async def get_model_scores(self, model_name: Optional[str] = None) -> List[ModelScoreRecord]:
        async with self.get_session() as session:
            stmt = select(ModelScoreRecord)
            if model_name:
                stmt = stmt.where(ModelScoreRecord.model_name == model_name)
            stmt = stmt.order_by(ModelScoreRecord.evaluated_at.desc())
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_latest_model_score(self, model_name: str) -> Optional[ModelScoreRecord]:
        async with self.get_session() as session:
            stmt = (
                select(ModelScoreRecord)
                .where(ModelScoreRecord.model_name == model_name)
                .order_by(ModelScoreRecord.evaluated_at.desc())
                .limit(1)
            )
            result = await session.execute(stmt)
            return result.scalars().first()

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
            stmt = select(
                AttackRecord.attack_type,
                func.count(AttackRecord.id).label("count"),
                func.avg(AttackRecord.success_score).label("avg_score"),
            ).group_by(AttackRecord.attack_type)
            result = await session.execute(stmt)
            return {
                row.attack_type: {
                    "count": row.count,
                    "avg_score": row.avg_score or 0.0,
                }
                for row in result
            }


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


def reset_database() -> None:
    """Reset the database singleton (for tests)."""
    global _default_db
    _default_db = None


# Backward-compatible aliases (unified single database)
ExtendedDatabase = Database


def get_extended_database() -> Database:
    return get_database()


def reset_extended_database() -> None:
    reset_database()


async def init_extended_database(
    db_path: Optional[Path] = None,
    db_url: Optional[str] = None,
) -> Database:
    return await init_database(db_path=db_path, db_url=db_url)


async def close_extended_database() -> None:
    await close_database()



