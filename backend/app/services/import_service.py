import io
import uuid
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.imports import DataImport, ImportSourceType, ImportStatus
from app.schemas.imports import DataImportListItem, DataImportRead


class ImportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_from_file(
        self,
        file_bytes: bytes,
        filename: str,
        name: str,
        category: str | None,
        user_id: uuid.UUID,
        org_id: uuid.UUID,
    ) -> DataImportRead:
        ext = filename.rsplit(".", 1)[-1].lower()
        if ext in ("xlsx", "xls"):
            source_type = ImportSourceType.EXCEL
            columns, preview, all_data = self._parse_excel(file_bytes)
        elif ext == "csv":
            source_type = ImportSourceType.CSV
            columns, preview, all_data = self._parse_csv(file_bytes)
        elif ext == "json":
            source_type = ImportSourceType.JSON
            columns, preview, all_data = self._parse_json(file_bytes)
        else:
            raise ValueError(f"Неподдерживаемый формат файла: .{ext}")

        record = DataImport(
            name=name,
            category=category,
            source_type=source_type,
            status=ImportStatus.DONE,
            original_filename=filename,
            row_count=len(all_data),
            columns=columns,
            preview_data=preview[:10],
            imported_data=all_data,
            created_by_id=user_id,
            organization_id=org_id,
        )
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record)
        await self.db.commit()
        return DataImportRead.model_validate(record)

    async def get_list(
        self, org_id: uuid.UUID, page: int = 1, page_size: int = 20
    ) -> dict:
        offset = (page - 1) * page_size
        result = await self.db.execute(
            select(DataImport)
            .where(DataImport.organization_id == org_id)
            .order_by(desc(DataImport.created_at))
            .offset(offset)
            .limit(page_size)
        )
        items = result.scalars().all()
        return {
            "items": [DataImportListItem.model_validate(i) for i in items],
            "page": page,
            "page_size": page_size,
        }

    async def get_by_id(
        self, import_id: uuid.UUID, org_id: uuid.UUID
    ) -> DataImportRead | None:
        result = await self.db.execute(
            select(DataImport).where(
                DataImport.id == import_id,
                DataImport.organization_id == org_id,
            )
        )
        record = result.scalar_one_or_none()
        if not record:
            return None
        return DataImportRead.model_validate(record)

    async def delete(self, import_id: uuid.UUID, org_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            select(DataImport).where(
                DataImport.id == import_id,
                DataImport.organization_id == org_id,
            )
        )
        record = result.scalar_one_or_none()
        if not record:
            return False
        await self.db.delete(record)
        await self.db.commit()
        return True

    def _parse_excel(self, file_bytes: bytes) -> tuple[list, list, list]:
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return [], [], []

        headers = [
            str(h).strip() if h is not None else f"Колонка_{i+1}"
            for i, h in enumerate(rows[0])
        ]

        data = []
        for row in rows[1:]:
            if any(v is not None for v in row):
                row_dict = {}
                for i, val in enumerate(row):
                    if i < len(headers):
                        row_dict[headers[i]] = str(val) if val is not None else ""
                data.append(row_dict)

        return headers, data[:10], data

    def _parse_csv(self, file_bytes: bytes) -> tuple[list, list, list]:
        import csv
        for encoding in ("utf-8-sig", "utf-8", "cp1251", "koi8-r"):
            try:
                text = file_bytes.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            text = file_bytes.decode("utf-8", errors="replace")

        reader = csv.DictReader(io.StringIO(text))
        headers = reader.fieldnames or []
        data = [dict(row) for row in reader]
        return list(headers), data[:10], data

    def _parse_json(self, file_bytes: bytes) -> tuple[list, list, list]:
        import json
        parsed = json.loads(file_bytes.decode("utf-8"))
        if isinstance(parsed, list) and parsed:
            headers = list(parsed[0].keys()) if isinstance(parsed[0], dict) else []
            data = [
                {str(k): str(v) for k, v in item.items()}
                for item in parsed if isinstance(item, dict)
            ]
            return headers, data[:10], data
        return [], [], []
