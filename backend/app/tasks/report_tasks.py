from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3, name="report_tasks.generate_report")
def generate_report_task(self, report_id: str, schema_name: str):
    import asyncio
    import uuid
    from datetime import UTC, datetime

    from sqlalchemy import select, text
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    from sqlalchemy.pool import NullPool

    from app.core.config import settings
    from app.models.reports import Report, ReportFormat, ReportStatus
    from app.services.generators.excel_generator import generate_excel
    from app.services.generators.pdf_generator import generate_pdf
    from app.services.storage_service import upload_file

    report_uuid = uuid.UUID(report_id)

    async def _make_session():
        engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
        factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        return engine, factory

    async def _run():
        # Каждый commit-блок — отдельный engine+session, чтобы SET search_path
        # не сбрасывался при получении нового соединения из пула.

        # ── Шаг 1: загрузить отчёт, выставить GENERATING ──────────────────
        report_snapshot: dict = {}
        engine, SessionLocal = await _make_session()
        try:
            async with SessionLocal() as db:
                await db.execute(text(f'SET search_path TO "{schema_name}", public'))
                result = await db.execute(
                    select(Report).where(Report.id == report_uuid)
                )
                report = result.scalar_one_or_none()
                if not report:
                    return

                report_snapshot = {
                    "title": report.title,
                    "type": report.type,
                    "format": report.format,
                    "period_from": (
                        report.period_from.strftime("%d.%m.%Y")
                        if report.period_from else "—"
                    ),
                    "period_to": (
                        report.period_to.strftime("%d.%m.%Y")
                        if report.period_to else "—"
                    ),
                    "columns": report.parameters.get("columns", ["Показатель", "Значение"]),
                    "data": report.parameters.get("data", []),
                }

                report.status = ReportStatus.GENERATING
                await db.commit()
        finally:
            await engine.dispose()

        # ── Шаг 2: генерация файла (без БД) ────────────────────────────────
        try:
            fmt = report_snapshot["format"]
            if fmt == ReportFormat.EXCEL:
                file_bytes = generate_excel(report_snapshot)
                content_type = (
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                ext = "xlsx"
            else:
                file_bytes = generate_pdf(report_snapshot)
                content_type = "application/pdf"
                ext = "pdf"

            filename = f"{report_snapshot['title']}_{report_uuid}.{ext}"
            object_name = upload_file("reports", file_bytes, filename, content_type)
        except Exception as exc:
            # ── Шаг 2b: записать FAILED ────────────────────────────────────
            failed_created_by = None
            engine, SessionLocal = await _make_session()
            try:
                async with SessionLocal() as db:
                    await db.execute(text(f'SET search_path TO "{schema_name}", public'))
                    result = await db.execute(
                        select(Report).where(Report.id == report_uuid)
                    )
                    report = result.scalar_one_or_none()
                    if report:
                        failed_created_by = report.created_by_id
                        report.status = ReportStatus.FAILED
                        report.error_message = str(exc)
                        await db.commit()
            finally:
                await engine.dispose()

            # Telegram уведомление — FAILED
            try:
                from app.models.auth import User
                from app.services.telegram_service import send_report_failed

                async def _notify_failed():
                    engine, SessionLocal = await _make_session()
                    try:
                        async with SessionLocal() as notify_db:
                            user_result = await notify_db.execute(
                                select(User).where(User.id == failed_created_by)
                            )
                            user = user_result.scalar_one_or_none()
                            if user and user.telegram_chat_id:
                                await send_report_failed(
                                    user.telegram_chat_id,
                                    report_snapshot.get("title", ""),
                                    str(exc),
                                )
                    finally:
                        await engine.dispose()

                await _notify_failed()
            except Exception:
                pass

            raise self.retry(exc=exc, countdown=60)

        # ── Шаг 3: выставить READY ──────────────────────────────────────────
        saved_title = report_snapshot["title"]
        saved_created_by = None
        engine, SessionLocal = await _make_session()
        try:
            async with SessionLocal() as db:
                await db.execute(text(f'SET search_path TO "{schema_name}", public'))
                result = await db.execute(
                    select(Report).where(Report.id == report_uuid)
                )
                report = result.scalar_one_or_none()
                if report:
                    saved_created_by = report.created_by_id
                    report.status = ReportStatus.READY
                    report.file_url = object_name
                    report.file_size = len(file_bytes)
                    report.completed_at = datetime.now(UTC)
                    await db.commit()
        finally:
            await engine.dispose()

        # ── Шаг 4: Telegram уведомление — READY ────────────────────────────
        try:
            from app.models.auth import User
            from app.services.telegram_service import send_report_ready

            async def _notify_ready():
                engine, SessionLocal = await _make_session()
                try:
                    async with SessionLocal() as notify_db:
                        user_result = await notify_db.execute(
                            select(User).where(User.id == saved_created_by)
                        )
                        user = user_result.scalar_one_or_none()
                        if user and user.telegram_chat_id:
                            await send_report_ready(
                                user.telegram_chat_id,
                                saved_title,
                                str(report_uuid),
                            )
                finally:
                    await engine.dispose()

            await _notify_ready()
        except Exception:
            pass

    asyncio.run(_run())
