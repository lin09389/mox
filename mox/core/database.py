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
