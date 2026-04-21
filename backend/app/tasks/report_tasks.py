from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3, name="report_tasks.generate_report")
def generate_report_task(self, report_id: str, schema_name: str):
    import asyncio
    import uuid
    from datetime import UTC, datetime
    from sqlalchemy import select, text
    from app.core.database import AsyncSessionLocal
    from app.models.reports import Report, ReportStatus, ReportFormat
    from app.services.generators.pdf_generator import generate_pdf
    from app.services.generators.excel_generator import generate_excel
    from app.services.storage_service import upload_file

    async def _run():
        async with AsyncSessionLocal() as db:
            await db.execute(text(f'SET search_path TO "{schema_name}", public'))

            result = await db.execute(
                select(Report).where(Report.id == uuid.UUID(report_id))
            )
            report = result.scalar_one_or_none()
            if not report:
                return

            try:
                report.status = ReportStatus.GENERATING
                await db.commit()

                report_data = {
                    "title": report.title,
                    "type": report.type,
                    "period_from": report.period_from.strftime("%d.%m.%Y") if report.period_from else "—",
                    "period_to": report.period_to.strftime("%d.%m.%Y") if report.period_to else "—",
                    "columns": report.parameters.get("columns", ["Показатель", "Значение"]),
                    "data": report.parameters.get("data", []),
                }

                if report.format == ReportFormat.EXCEL:
                    file_bytes = generate_excel(report_data)
                    content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    ext = "xlsx"
                else:
                    file_bytes = generate_pdf(report_data)
                    content_type = "application/pdf"
                    ext = "pdf"

                filename = f"{report.title}_{report.id}.{ext}"
                file_url = upload_file("reports", file_bytes, filename, content_type)

                report.status = ReportStatus.READY
                report.file_url = file_url
                report.file_size = len(file_bytes)
                report.completed_at = datetime.now(UTC)
                await db.commit()

            except Exception as exc:
                report.status = ReportStatus.FAILED
                report.error_message = str(exc)
                await db.commit()
                raise self.retry(exc=exc, countdown=60)

    asyncio.run(_run())
