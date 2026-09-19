from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import product as product_crud
from app.db.session import get_db
from app.schemas.product import CategoryOut

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
async def list_categories(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[CategoryOut]:
    categories = await product_crud.list_categories(db)
    return [CategoryOut.model_validate(c) for c in categories]
