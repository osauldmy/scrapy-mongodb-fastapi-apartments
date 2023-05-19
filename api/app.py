from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from beanie import init_beanie
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

from api import apartments
from shared.odm import ApartmentBeanie
from shared.settings import Settings

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Newer API for `@app.on_event("startup")` and `@app.on_event("shutdown")`
    https://fastapi.tiangolo.com/advanced/events/#alternative-events-deprecated
    https://fastapi.tiangolo.com/advanced/events/#lifespan
    """
    settings = Settings()
    mongo_client = AsyncIOMotorClient(settings.MONGO_URL)
    database = mongo_client[settings.MONGO_DATABASE]
    collection = database[settings.MONGO_COLLECTION]
    await init_beanie(database=database, document_models=[ApartmentBeanie])  # type: ignore[arg-type]
    app.state.mongo_collection = collection
    yield
    mongo_client.close()


app = FastAPI(
    title="Apartments API",
    description="Simple CRUD API for scraped apartments",
    lifespan=lifespan,
)


@app.get("/")
async def index() -> str:
    return "It works!"


app.include_router(apartments.router)
