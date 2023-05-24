from __future__ import annotations

import os
from functools import cache
from typing import TYPE_CHECKING

import beanie
import pytest
from mongomock import MongoClient as MongoMockClient
from mongomock_motor import AsyncMongoMockClient
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from shared.models import Apartment, OfferType, Price, Rooms, Size, Source, Status
from shared.settings import Settings

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Any, Type, TypeAlias

    from _pytest.python import Function

    PyMongoClient = MongoClient | MongoMockClient
    PyMongoClientClass = Type[PyMongoClient]
    MotorClient: TypeAlias = AsyncIOMotorClient | AsyncMongoMockClient
    MotorClientClass = Type[MotorClient]


def pytest_itemcollected(item: Function) -> None:
    """
    Modifies API test names depending on what type df is used:
        running MongoDB instance or mongomock.
    Also adds mongo marker for tests using mongodb, so
    integration tests can be easily launched using `pytest -m mongo`
    """
    if "motor_client_class" not in item.fixturenames:
        return

    if is_mongo_running():
        item.add_marker("mongo")
        suffix = "[mongo]"
    else:
        suffix = "[mock]"

    # TODO: maybe add suffix after class if exists
    item._nodeid += suffix


@cache
def is_mongo_running() -> bool:
    """Naive but working test."""
    mongo_url = os.environ.get("MONGO_URL")
    client: MongoClient[dict[str, Any]] = MongoClient(
        mongo_url, serverSelectionTimeoutMS=1_000
    )
    try:
        client.server_info()
        return True
    except PyMongoError:
        return False


@pytest.fixture
def test_settings() -> Settings:
    settings = Settings()
    settings.MONGO_DATABASE = "dummy_db"
    return settings


@pytest.fixture
def pymongo_client_class() -> PyMongoClientClass:
    return MongoClient if is_mongo_running() else MongoMockClient


@pytest.fixture
def motor_client_class() -> MotorClientClass:
    return AsyncIOMotorClient if is_mongo_running() else AsyncMongoMockClient


@pytest.fixture
def pymongo_client(
    pymongo_client_class: PyMongoClientClass,
    test_settings: Settings,
) -> Iterator[PyMongoClient]:
    client = pymongo_client_class(test_settings.MONGO_URL)
    yield client
    client.close()


@pytest.fixture
def random_objectid() -> beanie.PydanticObjectId:
    return beanie.PydanticObjectId()


@pytest.fixture
def yit_apartment() -> Apartment:
    return Apartment(
        url="https://www.yit.sk/en/flats-for-sale/bratislava/foo/bar/123456",  # type: ignore[arg-type]
        source=Source.SCRAPER,
        offer_type=OfferType.SELL,
        status=Status.FREE,
        floor=3,
        price=Price(price=300_000, currency="EUR"),
        size=Size(usable=60, total=70.3),
        rooms=Rooms(amount=3),
        description="some description",
    )


@pytest.fixture
def yit_apartment_from_server(yit_apartment: Apartment) -> dict[str, Any]:
    return {
        "Fields": {
            "ProductItemForSale": True,
            "ProductItemForRent": False,
            "ReservationStatusKey": "Free",
            "WebProjectStatusKey": "ReadyToMoveIn",
            "SalesPrice": yit_apartment.price.price,
            "ApartmentSize": yit_apartment.size.usable,
            "TotalAreaSize": yit_apartment.size.total,
            "FloorNumberCorrectedFrom": yit_apartment.floor,
            "NumberOfRooms": str(yit_apartment.rooms.amount),
            "ProjectCoordinatesLatitude": None,
            "ProjectCoordinatesLongitude": None,
            "MarketingDescription": yit_apartment.description,
            "_Url": "/en/flats-for-sale/bratislava/foo/bar/123456",
        }
    }
