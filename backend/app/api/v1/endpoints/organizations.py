from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import AdminUser, CurrentUser, get_db
from app.models.auth import Organization
from app.schemas.auth import OrganizationRead, OrganizationUpdate

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.get("/me", response_model=OrganizationRead)
async def get_my_organization(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if not current_user.organization_id:
        raise HTTPException(status_code=404, detail="Организация не найдена")
    result = await db.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Организация не найдена")
    return OrganizationRead.model_validate(org)


@router.patch("/me", response_model=OrganizationRead)
async def update_my_organization(
    data: OrganizationUpdate,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Организация не найдена")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(org, field, value)
    await db.commit()
    await db.refresh(org)
    return OrganizationRead.model_validate(org)
