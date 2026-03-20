"""数据库模块 - 优化版

支持连接池、连接复用和更好的错误处理。
"""

from datetime import datetime
from typing import Optional, List, Any
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
    event,
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

from .config import settings
from .logging import get_logger

logger = get_logger("database")

Base = declarative_base()


# ============ 数据模型 ============

@dataclass
class AttackRecordDB:
    """攻击记录数据传输对象"""

    id: Optional[int] = None
    attack_type: str = ""
    original_prompt: str = ""
    adversarial_prompt: str = ""
    model_response: str = ""
    result: str = ""
    success_score: float = 0.0
    iterations: int = 0
    model_name: str = ""
    metadata: dict = field(default_factory=dict)
    created_at: Optional[datetime] = None


@dataclass
class DefenseRecordDB:
    """防御记录数据传输对象"""

    id: Optional[int] = None
    defense_type: str = ""
    input_text: str = ""
    output_text: str = ""
    is_malicious: bool = False
    confidence: float = 0.0
    detected_patterns: list = field(default_factory=list)
    model_name: str = ""
    metadata: dict = field(default_factory=dict)
    created_at: Optional[datetime] = None


class AttackRecord(Base):
    """攻击记录表"""

    __tablename__ = "attack_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    attack_type = Column(String(50), nullable=False, index=True)
    original_prompt = Column(Text, nullable=False)
    adversarial_prompt = Column(Text)
    model_response = Column(Text)
    result = Column(String(20), index=True)
    success_score = Column(Float, default=0.0)
    iterations = Column(Integer, default=0)
    model_name = Column(String(50), index=True)
    record_meta = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.now, index=True)


class DefenseRecord(Base):
    """防御记录表"""

    __tablename__ = "defense_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    defense_type = Column(String(50), nullable=False, index=True)
    input_text = Column(Text, nullable=False)
    output_text = Column(Text)
    is_malicious = Column(Boolean, default=False, index=True)
    confidence = Column(Float, default=0.0)
    detected_patterns = Column(JSON, default=list)
    model_name = Column(String(50), index=True)
    record_meta = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.now, index=True)


class EvaluationRecord(Base):
    """评估记录表"""

    __tablename__ = "evaluation_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    evaluation_name = Column(String(100), index=True)
    total_attacks = Column(Integer, default=0)
    successful_attacks = Column(Integer, default=0)
    failed_attacks = Column(Integer, default=0)
    attack_success_rate = Column(Float, default=0.0)
    defense_success_rate = Column(Float, default=0.0)
    avg_iterations = Column(Float, default=0.0)
    model_name = Column(String(50))
    record_meta = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.now, index=True)


# ============ 数据库管理器 ============

class Database:
    """数据库管理器 - 支持连接池和异步操作"""

    def __init__(self, db_path: Optional[Path] = None, db_url: Optional[str] = None):
        """
        初始化数据库管理器
        
        Args:
            db_path: SQLite 数据库文件路径
            db_url: 完整的数据库 URL (优先于 db_path)
        """
        if db_url:
            self.db_url = db_url
        elif db_path:
            db_path = Path(db_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            self.db_url = f"sqlite+aiosqlite:///{db_path}"
        else:
            # 使用配置中的数据库 URL
            self.db_url = settings.DATABASE_URL
            if self.db_url.startswith("sqlite"):
                # 确保 SQLite 数据库目录存在
                db_path = Path(self.db_url.replace("sqlite+aiosqlite:///", ""))
                db_path.parent.mkdir(parents=True, exist_ok=True)

        # 创建引擎，根据数据库类型配置连接池
        engine_kwargs = self._get_engine_kwargs()
        self.engine = create_async_engine(self.db_url, **engine_kwargs)
        
        # 创建会话工厂
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

        logger.info(f"Database engine created: {self._mask_url(self.db_url)}")

    def _get_engine_kwargs(self) -> dict:
        """根据数据库类型获取引擎配置"""
        kwargs = {"echo": settings.DEBUG and settings.LOG_LEVEL == "DEBUG"}
        
        if self.db_url.startswith("sqlite"):
            # SQLite 不支持连接池，使用 NullPool
            kwargs["poolclass"] = NullPool
            # SQLite 特定配置
            kwargs["connect_args"] = {
                "check_same_thread": False,
                "timeout": 30,
            }
        else:
            # PostgreSQL / MySQL 等使用连接池
            kwargs.update({
                "pool_size": settings.DB_POOL_SIZE,
                "max_overflow": settings.DB_MAX_OVERFLOW,
                "pool_timeout": settings.DB_POOL_TIMEOUT,
                "pool_recycle": settings.DB_POOL_RECYCLE,
                "pool_pre_ping": True,
            })
        
        return kwargs

    def _mask_url(self, url: str) -> str:
        """隐藏 URL 中的敏感信息"""
        if "@" in url:
            # 隐藏密码
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
    async def get_session(self) -> AsyncSession:
        """获取数据库会话（上下文管理器）"""
        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def save_attack_record(self, record: AttackRecordDB) -> int:
        """保存攻击记录"""
        async with self.get_session() as session:
            db_record = AttackRecord(
                attack_type=record.attack_type,
                original_prompt=record.original_prompt,
                adversarial_prompt=record.adversarial_prompt,
                model_response=record.model_response,
                result=record.result,
                success_score=record.success_score,
                iterations=record.iterations,
                model_name=record.model_name,
                record_meta=record.metadata,
                created_at=record.created_at or datetime.now(),
            )
            session.add(db_record)
            await session.flush()
            await session.refresh(db_record)
            return db_record.id

    async def save_defense_record(self, record: DefenseRecordDB) -> int:
        """保存防御记录"""
        async with self.get_session() as session:
            db_record = DefenseRecord(
                defense_type=record.defense_type,
                input_text=record.input_text,
                output_text=record.output_text,
                is_malicious=record.is_malicious,
                confidence=record.confidence,
                detected_patterns=record.detected_patterns,
                model_name=record.model_name,
                record_meta=record.metadata,
                created_at=record.created_at or datetime.now(),
            )
            session.add(db_record)
            await session.flush()
            await session.refresh(db_record)
            return db_record.id

    async def get_attack_records(
        self,
        limit: int = 100,
        attack_type: Optional[str] = None,
        offset: int = 0,
    ) -> List[AttackRecord]:
        """获取攻击记录"""
        async with self.get_session() as session:
            query = await session.execute(
                self._build_attack_query(attack_type, limit, offset)
            )
            return query.scalars().all()

    def _build_attack_query(self, attack_type: Optional[str], limit: int, offset: int):
        """构建攻击记录查询"""
        from sqlalchemy import select
        stmt = select(AttackRecord)
        if attack_type:
            stmt = stmt.where(AttackRecord.attack_type == attack_type)
        return stmt.order_by(AttackRecord.created_at.desc()).limit(limit).offset(offset)

    async def get_defense_records(
        self,
        limit: int = 100,
        defense_type: Optional[str] = None,
        offset: int = 0,
    ) -> List[DefenseRecord]:
        """获取防御记录"""
        async with self.get_session() as session:
            from sqlalchemy import select
            stmt = select(DefenseRecord)
            if defense_type:
                stmt = stmt.where(DefenseRecord.defense_type == defense_type)
            stmt = stmt.order_by(DefenseRecord.created_at.desc()).limit(limit).offset(offset)
            result = await session.execute(stmt)
            return result.scalars().all()

    async def count_attack_records(self, attack_type: Optional[str] = None) -> int:
        """统计攻击记录数量"""
        async with self.get_session() as session:
            from sqlalchemy import select, func
            stmt = select(func.count(AttackRecord.id))
            if attack_type:
                stmt = stmt.where(AttackRecord.attack_type == attack_type)
            result = await session.execute(stmt)
            return result.scalar() or 0

    async def count_defense_records(self, defense_type: Optional[str] = None) -> int:
        """统计防御记录数量"""
        async with self.get_session() as session:
            from sqlalchemy import select, func
            stmt = select(func.count(DefenseRecord.id))
            if defense_type:
                stmt = stmt.where(DefenseRecord.defense_type == defense_type)
            result = await session.execute(stmt)
            return result.scalar() or 0

    async def get_stats(self) -> dict:
        """获取数据库统计信息"""
        return {
            "total_attacks": await self.count_attack_records(),
            "total_defenses": await self.count_defense_records(),
        }


# ============ 全局实例 ============

_default_db: Optional[Database] = None


def get_database() -> Database:
    """获取全局数据库实例"""
    global _default_db
    if _default_db is None:
        _default_db = Database()
    return _default_db


async def init_database(db_path: Optional[Path] = None, db_url: Optional[str] = None) -> Database:
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