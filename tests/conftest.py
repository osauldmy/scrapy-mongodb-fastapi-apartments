from __future__ import annotations

import os
from functools import cache
from typing import TYPE_CHECKING

import beanie
import pytest
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from shared.models import Apartment, OfferType, Price, Rooms, Size, Source, Status

if TYPE_CHECKING:
    from typing import Any

    from _pytest.python import Function


def pytest_itemcollected(item: Function) -> None:
    """
    Modifies API test names depending on what type df is used:
        running MongoDB instance or mongomock.
    Also adds mongo marker for tests using mongodb, so
    integration tests can be easily launched using `pytest -m mongo`
    """
    if "set_mongo" not in item.fixturenames:
        return

    if not is_mongo_running():
        item._nodeid += "[mock]"
        return

    item.add_marker("mongo")
    item._nodeid += "[mongo]"


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
