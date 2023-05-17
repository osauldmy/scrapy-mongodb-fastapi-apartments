from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from shared.models import Apartment, OfferType, Price, Rooms, Size, Source, Status

if TYPE_CHECKING:
    from typing import Any


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
