import sys

models_str = '''
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

'''

methods_str = '''
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

'''

with open('mox/core/database.py', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
models_end_idx = 0
methods_end_idx = 0

for i, line in enumerate(lines):
    if '# ============ 数据库管理器 ============' in line:
        models_end_idx = i - 1
    if '# ============ 全局实例 ============' in line:
        methods_end_idx = i - 1

new_content = '\n'.join(lines[:models_end_idx]) + '\n' + models_str + '\n' + '\n'.join(lines[models_end_idx:methods_end_idx]) + '\n' + methods_str + '\n' + '\n'.join(lines[methods_end_idx:])

with open('mox/core/database.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Merged models and methods into database.py")
