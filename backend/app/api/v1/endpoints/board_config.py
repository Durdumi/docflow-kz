import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.deps import AdminUser, CurrentUser, get_db
from app.models.auth import Organization
from app.models.board_config import BoardColumn, LabelColor

router = APIRouter(prefix="/board", tags=["Board Config"])

DEFAULT_COLUMNS = [
    {"key": "todo",        "label": "📋 Надо сделать", "color": "#f5f5f5", "position": 0},
    {"key": "in_progress", "label": "⚡ В работе",      "color": "#e6f4ff", "position": 1},
    {"key": "review",      "label": "👀 На проверке",   "color": "#fff7e6", "position": 2},
    {"key": "done",        "label": "✅ Готово",         "color": "#f6ffed", "position": 3, "is_done_column": True},
]

DEFAULT_LABELS = [
    {"color": "#ff4d4f", "name": "Срочно"},
    {"color": "#1677ff", "name": "Разработка"},
    {"color": "#52c41a", "name": "Готово к релизу"},
    {"color": "#faad14", "name": "На согласовании"},
    {"color": "#722ed1", "name": "Дизайн"},
]


async def _get_schema(current_user, db: AsyncSession) -> str:
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="Нет организации")
    result = await db.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Организация не найдена")
    return org.schema_name


# ─── Schemas ──────────────────────────────────────────────────
class ColumnCreate(BaseModel):
    key: str = Field(..., min_length=1, max_length=50)
    label: str = Field(..., min_length=1, max_length=100)
    color: str = "#f5f5f5"
    position: int = 0


class ColumnUpdate(BaseModel):
    label: str | None = None
    color: str | None = None
    position: int | None = None
    is_active: bool | None = None
    is_done_column: bool | None = None


class LabelColorCreate(BaseModel):
    color: str
    name: str = Field(..., min_length=1, max_length=100)


# ─── Columns ──────────────────────────────────────────────────
@router.get("/columns")
async def get_columns(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    schema = await _get_schema(current_user, db)
    await db.execute(text(f'SET search_path TO "{schema}", public'))

    result = await db.execute(
        select(BoardColumn)
        .where(
            BoardColumn.organization_id == current_user.organization_id,
            BoardColumn.is_active == True,
        )
        .order_by(BoardColumn.position)
    )
    columns = result.scalars().all()

    if not columns:
        for col_data in DEFAULT_COLUMNS:
            col = BoardColumn(**col_data, organization_id=current_user.organization_id)
            db.add(col)
        await db.commit()
        result = await db.execute(
            select(BoardColumn)
            .where(
                BoardColumn.organization_id == current_user.organization_id,
                BoardColumn.is_active == True,
            )
            .order_by(BoardColumn.position)
        )
        columns = result.scalars().all()

    return [
        {
            "id": str(c.id), "key": c.key, "label": c.label,
            "color": c.color, "position": c.position, "is_done_column": c.is_done_column,
        }
        for c in columns
    ]


@router.post("/columns", status_code=status.HTTP_201_CREATED)
async def create_column(
    data: ColumnCreate,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    schema = await _get_schema(current_user, db)
    await db.execute(text(f'SET search_path TO "{schema}", public'))
    col = BoardColumn(
        key=data.key, label=data.label, color=data.color,
        position=data.position, organization_id=current_user.organization_id,
    )
    db.add(col)
    await db.commit()
    await db.refresh(col)
    return {"id": str(col.id), "key": col.key, "label": col.label, "color": col.color}


@router.patch("/columns/{column_id}")
async def update_column(
    column_id: uuid.UUID,
    data: ColumnUpdate,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    schema = await _get_schema(current_user, db)
    await db.execute(text(f'SET search_path TO "{schema}", public'))
    result = await db.execute(
        select(BoardColumn).where(
            BoardColumn.id == column_id,
            BoardColumn.organization_id == current_user.organization_id,
        )
    )
    col = result.scalar_one_or_none()
    if not col:
        raise HTTPException(status_code=404, detail="Колонка не найдена")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(col, field, value)
    await db.commit()
    return {"id": str(col.id), "key": col.key, "label": col.label, "is_active": col.is_active}


@router.delete("/columns/{column_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_column(
    column_id: uuid.UUID,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    schema = await _get_schema(current_user, db)
    await db.execute(text(f'SET search_path TO "{schema}", public'))
    result = await db.execute(
        select(BoardColumn).where(
            BoardColumn.id == column_id,
            BoardColumn.organization_id == current_user.organization_id,
        )
    )
    col = result.scalar_one_or_none()
    if not col:
        raise HTTPException(status_code=404, detail="Колонка не найдена")
    col.is_active = False
    await db.commit()


# ─── Labels ───────────────────────────────────────────────────
@router.get("/labels")
async def get_labels(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    schema = await _get_schema(current_user, db)
    await db.execute(text(f'SET search_path TO "{schema}", public'))
    result = await db.execute(
        select(LabelColor).where(LabelColor.organization_id == current_user.organization_id)
    )
    labels = result.scalars().all()

    if not labels:
        for d in DEFAULT_LABELS:
            db.add(LabelColor(**d, organization_id=current_user.organization_id))
        await db.commit()
        result = await db.execute(
            select(LabelColor).where(LabelColor.organization_id == current_user.organization_id)
        )
        labels = result.scalars().all()

    return [{"id": str(l.id), "color": l.color, "name": l.name} for l in labels]


@router.post("/labels", status_code=status.HTTP_201_CREATED)
async def create_label(
    data: LabelColorCreate,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    schema = await _get_schema(current_user, db)
    await db.execute(text(f'SET search_path TO "{schema}", public'))
    label = LabelColor(color=data.color, name=data.name, organization_id=current_user.organization_id)
    db.add(label)
    await db.commit()
    await db.refresh(label)
    return {"id": str(label.id), "color": label.color, "name": label.name}


@router.delete("/labels/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_label(
    label_id: uuid.UUID,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    schema = await _get_schema(current_user, db)
    await db.execute(text(f'SET search_path TO "{schema}", public'))
    result = await db.execute(
        select(LabelColor).where(
            LabelColor.id == label_id,
            LabelColor.organization_id == current_user.organization_id,
        )
    )
    label = result.scalar_one_or_none()
    if not label:
        raise HTTPException(status_code=404, detail="Метка не найдена")
    await db.delete(label)
    await db.commit()
