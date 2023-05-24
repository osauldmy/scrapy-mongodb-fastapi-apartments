from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest

from scraper.pipelines.mongo import SaveToMongoWithDuplicatesCheck
from shared.models import Apartment
from shared.odm import ApartmentBeanie

if TYPE_CHECKING:
    from collections.abc import Iterator

    from shared.settings import Settings
    from tests.conftest import MotorClientClass, PyMongoClient


@pytest.fixture
def mongo_pipeline_instance(
    test_settings: Settings,
    motor_client_class: MotorClientClass,
) -> SaveToMongoWithDuplicatesCheck:
    return SaveToMongoWithDuplicatesCheck(
        client=motor_client_class(test_settings.MONGO_URL),
        database=test_settings.MONGO_DATABASE,
    )


@pytest.fixture
def mongo_pipeline(
    mongo_pipeline_instance: SaveToMongoWithDuplicatesCheck,
    pymongo_client: PyMongoClient,
) -> Iterator[SaveToMongoWithDuplicatesCheck]:
    pipeline = mongo_pipeline_instance
    pipeline.open_spider(None)
    yield pipeline
    pipeline.close_spider(None)
    pymongo_client.drop_database(pipeline.database)


class TestSaveToMongoWithDuplicatesCheck:
    def test_open_spider_no_running_loop(
        self, mongo_pipeline_instance: SaveToMongoWithDuplicatesCheck
    ) -> None:
        with pytest.raises(RuntimeError):
            asyncio.get_running_loop()

        mongo_pipeline_instance.open_spider(None)
        mongo_pipeline_instance.close_spider(None)
        assert True

    @pytest.mark.asyncio
    async def test_open_spider_with_running_loop(
        self, mongo_pipeline_instance: SaveToMongoWithDuplicatesCheck
    ) -> None:
        mongo_pipeline_instance.open_spider(None)
        mongo_pipeline_instance.close_spider(None)
        assert True

    @pytest.mark.asyncio
    async def test_process_item(
        self,
        test_settings: Settings,
        mongo_pipeline: SaveToMongoWithDuplicatesCheck,
        yit_apartment: Apartment,
    ) -> None:
        _db = mongo_pipeline.client[mongo_pipeline.database]
        collection = _db[test_settings.MONGO_COLLECTION]

        assert await collection.find().to_list(None) == []
        assert await ApartmentBeanie.find_all().to_list() == []

        await mongo_pipeline.process_item(yit_apartment, None)

        await collection.find().to_list(None) == [yit_apartment]
        await ApartmentBeanie.find_all().to_list() == [yit_apartment]

    @pytest.mark.xfail(reason="Not yet implemented")
    @pytest.mark.asyncio
    async def test_is_duplicate(
        self,
        mongo_pipeline: SaveToMongoWithDuplicatesCheck,
        yit_apartment: Apartment,
    ) -> None:
        apartment = ApartmentBeanie.parse_obj(yit_apartment)
        await apartment.insert()
        assert await mongo_pipeline.is_duplicate(apartment) is True
