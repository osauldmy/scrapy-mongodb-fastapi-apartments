from __future__ import annotations

from typing import TYPE_CHECKING

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from scrapy import signals
from scrapy.exceptions import DropItem

from shared.odm import ApartmentBeanie

if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorCollection
    from scrapy import Spider
    from scrapy.crawler import Crawler
    from typing_extensions import Self

    from shared.models import Apartment
    from shared.settings import Settings


# TODO: consider rewriting like in docs
# https://docs.scrapy.org/en/latest/topics/item-pipeline.html#write-items-to-mongodb
class SaveToMongoWithDuplicatesCheck:
    @classmethod
    def from_crawler(cls, crawler: Crawler) -> Self:
        settings: Settings = crawler.settings["DOTENV_SETTINGS"]
        client = AsyncIOMotorClient(settings.MONGO_URL)
        collection = client[settings.MONGO_DATABASE][settings.MONGO_COLLECTION]

        instance = cls(client=client, collection=collection)
        crawler.signals.connect(instance._init_beanie, signals.engine_started)
        crawler.signals.connect(instance._close_motor_client, signals.engine_stopped)
        return instance

    def __init__(
        self, client: AsyncIOMotorClient, collection: AsyncIOMotorCollection
    ) -> None:
        self.client = client
        self.collection = collection

    async def drop_if_duplicate(self, item: Apartment) -> None:
        duplicate = False  # TODO duplicates checker
        if duplicate:
            raise DropItem(f"{item.id} is duplicate!")

    async def process_item(self, item: Apartment, spider: Spider) -> Apartment:
        apartment = ApartmentBeanie.parse_obj(item)
        await self.drop_if_duplicate(apartment)
        await apartment.insert()
        return item

    async def _init_beanie(self) -> None:
        database = self.collection.database
        await init_beanie(
            database=database, document_models=[ApartmentBeanie]  # type: ignore[arg-type]
        )

    def _close_motor_client(self) -> None:
        self.client.close()
