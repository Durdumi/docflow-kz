import uuid
from datetime import UTC, datetime
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.reports import Report, ReportStatus
from app.schemas.reports import ReportCreate, ReportRead, ReportListItem


class ReportService:
    def __init__(self, db: AsyncSession, schema_name: str):
        self.db = db
        self.schema_name = schema_name

    async def create(self, data: ReportCreate, user_id: uuid.UUID, org_id: uuid.UUID) -> ReportRead:
        report = Report(
            title=data.title,
            type=data.type,
            format=data.format,
            period_from=data.period_from,
            period_to=data.period_to,
            parameters=data.parameters,
            status=ReportStatus.PENDING,
            created_by_id=user_id,
            organization_id=org_id,
        )
        self.db.add(report)
        await self.db.flush()
        await self.db.refresh(report)

        # Запускаем генерацию в Celery
        from app.tasks.report_tasks import generate_report_task
        generate_report_task.delay(str(report.id), self.schema_name)

        await self.db.commit()
        return ReportRead.model_validate(report)

    async def get_list(self, org_id: uuid.UUID, page: int = 1, page_size: int = 20) -> dict:
        offset = (page - 1) * page_size
        result = await self.db.execute(
            select(Report)
            .where(Report.organization_id == org_id)
            .order_by(desc(Report.created_at))
            .offset(offset)
            .limit(page_size)
        )
        reports = result.scalars().all()
        return {
            "items": [ReportListItem.model_validate(r) for r in reports],
            "page": page,
            "page_size": page_size,
        }

    async def get_by_id(self, report_id: uuid.UUID, org_id: uuid.UUID) -> ReportRead | None:
        result = await self.db.execute(
            select(Report).where(Report.id == report_id, Report.organization_id == org_id)
        )
        report = result.scalar_one_or_none()
        if not report:
            return None
        return ReportRead.model_validate(report)

    async def delete(self, report_id: uuid.UUID, org_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            select(Report).where(Report.id == report_id, Report.organization_id == org_id)
        )
        report = result.scalar_one_or_none()
        if not report:
            return False
        await self.db.delete(report)
        await self.db.commit()
        return True
