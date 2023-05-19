from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Literal, cast

from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException

from shared.models import Apartment, Source
from shared.odm import ApartmentBeanie

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/apartments", tags=["Apartments"])


# TODO: filtering
@router.get("", summary="Get all apartments")
async def list_() -> Sequence[Apartment]:
    return await ApartmentBeanie.find_all().to_list()


@router.get("/{id}", summary="Get one apartment")
async def get(id: PydanticObjectId) -> Apartment:
    if not (item := await ApartmentBeanie.get(id)):
        raise HTTPException(404)
    return Apartment.from_orm(item)


@router.post("", summary="Insert/create one apartment")
async def create(item: Apartment) -> PydanticObjectId:
    item.source = Source.API
    x = ApartmentBeanie.parse_obj(item)
    await x.insert()
    return cast(PydanticObjectId, x.id)


@router.delete("/{id}", summary="Delete apartment if exists")
async def delete(id: PydanticObjectId) -> Literal["OK"]:
    if not (item := await ApartmentBeanie.get(id)):
        raise HTTPException(404)
    status = await item.delete()
    if not status or status.deleted_count != 1:
        logger.error(f"Cannot delete {id}")
        raise HTTPException(500, detail=f"Error deleting {id}")
    return "OK"


# TODO: router.put for update/replace
