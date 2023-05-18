from __future__ import annotations

from functools import cached_property
from typing import cast

from scraper.pages import ApartmentPage
from shared.models import (
    Details,
    Location,
    OfferType,
    Price,
    Rooms,
    Size,
    Source,
    Status,
)


class YitSkJsonApartmentPage(ApartmentPage):
    @property
    def url(self) -> str:
        return "https://www.yit.sk" + cast(str, self.data["_Url"])

    @property
    def source(self) -> Source:
        return Source.SCRAPER

    @property
    def offer_type(self) -> OfferType:
        return OfferType.SELL

    @property
    def status(self) -> Status:
        match self.data:
            case {
                "ReservationStatusKey": "Free",
                "WebProjectStatusKey": "ReadyToMoveIn",
            }:
                status = Status.FREE
            case {"ReservationStatusKey": "Free", "WebProjectStatusKey": "ToBeReady"}:
                status = Status.IN_CONSTRUCTION
            case {"ReservationStatusKey": _}:
                status = Status.RESERVED
            case _:
                status = Status.UNKNOWN
        return status

    @property
    def price(self) -> Price:
        # NOTE: currency was not in the response JSON,
        # but for this particular situation, we know SK has EUR
        return Price(price=self.data["SalesPrice"], currency="EUR")

    @property
    def size(self) -> Size:
        return Size(usable=self.data["ApartmentSize"], total=self.data["TotalAreaSize"])

    @property
    def rooms(self) -> Rooms:
        # NOTE: somehow `NumberOfRooms` can be '1,5' which is float?
        # replace comma with dot, cast it to float and then to int
        amount = int(float(self.data["NumberOfRooms"].replace(",", ".")))
        return Rooms(amount=amount)

    @property
    def floor(self) -> int | None:
        return self.data.get("FloorNumberCorrectedFrom")

    @cached_property
    def location(self) -> Location | None:
        return Location.geolocate(
            latitude=self.data["ProjectCoordinatesLatitude"],
            longitude=self.data["ProjectCoordinatesLongitude"],
        )

    @property
    def details(self) -> Details | None:
        details = Details(
            balcony=self.data.get("BalconyKey"),
            terrace=self.data.get("TerraceKey"),
            # ... to be set other stuff
        )
        return None if details.dict(exclude_none=True) == {} else details

    @property
    def description(self) -> str | None:
        project = self.data.get("ProjectMarketingDescription") or ""
        apartment = self.data.get("MarketingDescription") or ""
        combined = f"{project}\n{apartment}".strip()
        return combined or None

    @property
    def photos(self) -> list[str] | None:
        if self.response is None:
            return None
        return cast(list[str], self.response.css("img::attr(data-src)").getall())
