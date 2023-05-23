from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from scrapy.exceptions import DropItem

from shared.odm import ApartmentBeanie

if TYPE_CHECKING:
    from scrapy import Spider
    from scrapy.crawler import Crawler
    from typing_extensions import Self

    from shared.models import Apartment
    from shared.settings import Settings


class SaveToMongoWithDuplicatesCheck:
    @classmethod
    def from_crawler(cls, crawler: Crawler) -> Self:
        settings: Settings = crawler.settings["DOTENV_SETTINGS"]
        return cls(
            client=AsyncIOMotorClient(settings.MONGO_URL),
            database=settings.MONGO_DATABASE,
        )

    def __init__(self, client: AsyncIOMotorClient, database: str) -> None:
        self.client = client
        self.database = database

    def open_spider(self, _: Spider) -> None:
        loop = asyncio.get_event_loop()
        coroutine = init_beanie(self.client[self.database], document_models=[ApartmentBeanie])  # type: ignore[arg-type]
        if loop.is_running():
            # https://docs.python.org/3/library/asyncio-task.html#asyncio.create_task
            # Seems like `asyncio.ensure_future` is getting deprecated/is not recommended.
            asyncio.create_task(coroutine)
        else:
            loop.run_until_complete(coroutine)

    async def is_duplicate(self, item: Apartment) -> bool:
        is_duplicate = False  # TODO duplicates checker
        return is_duplicate

    async def process_item(self, item: Apartment, _: Spider) -> Apartment:
        apartment = ApartmentBeanie.parse_obj(item)
        is_duplicate = await self.is_duplicate(apartment)
        if is_duplicate:
            raise DropItem(f"{item.id} is duplicate!")
        await apartment.insert()
        return item

    def close_spider(self, _: Spider) -> None:
        self.client.close()
