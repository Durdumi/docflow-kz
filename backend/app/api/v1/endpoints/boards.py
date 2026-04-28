import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.deps import CurrentUser, get_db
from app.models.auth import Organization
from app.models.boards import Board

router = APIRouter(prefix="/boards", tags=["Boards"])


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


class BoardCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    color: str = "#1677ff"


class BoardUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    color: str | None = None
    is_archived: bool | None = None


@router.get("")
async def list_boards(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    schema = await _get_schema(current_user, db)
    await db.execute(text(f'SET search_path TO "{schema}", public'))
    result = await db.execute(
        select(Board).where(
            Board.organization_id == current_user.organization_id,
            Board.is_archived == False,
        ).order_by(Board.created_at)
    )
    boards = result.scalars().all()

    if not boards:
        default_board = Board(
            name="Основная доска",
            description="Доска по умолчанию",
            color="#1677ff",
            organization_id=current_user.organization_id,
            created_by_id=current_user.id,
        )
        db.add(default_board)
        await db.commit()
        await db.refresh(default_board)
        boards = [default_board]

    return [
        {
            "id": str(b.id),
            "name": b.name,
            "description": b.description,
            "color": b.color,
            "is_archived": b.is_archived,
            "created_at": b.created_at.isoformat(),
        }
        for b in boards
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_board(
    data: BoardCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    schema = await _get_schema(current_user, db)
    await db.execute(text(f'SET search_path TO "{schema}", public'))
    board = Board(
        name=data.name,
        description=data.description,
        color=data.color,
        organization_id=current_user.organization_id,
        created_by_id=current_user.id,
    )
    db.add(board)
    await db.commit()
    await db.refresh(board)
    return {"id": str(board.id), "name": board.name, "color": board.color}


@router.patch("/{board_id}")
async def update_board(
    board_id: uuid.UUID,
    data: BoardUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    schema = await _get_schema(current_user, db)
    await db.execute(text(f'SET search_path TO "{schema}", public'))
    result = await db.execute(
        select(Board).where(
            Board.id == board_id,
            Board.organization_id == current_user.organization_id,
        )
    )
    board = result.scalar_one_or_none()
    if not board:
        raise HTTPException(status_code=404, detail="Доска не найдена")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(board, field, value)
    await db.commit()
    return {"id": str(board.id), "name": board.name}


@router.delete("/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_board(
    board_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    schema = await _get_schema(current_user, db)
    await db.execute(text(f'SET search_path TO "{schema}", public'))
    result = await db.execute(
        select(Board).where(
            Board.id == board_id,
            Board.organization_id == current_user.organization_id,
        )
    )
    board = result.scalar_one_or_none()
    if not board:
        raise HTTPException(status_code=404, detail="Доска не найдена")
    board.is_archived = True
    await db.commit()
