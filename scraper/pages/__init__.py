from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from web_poet.pages import WebPage

from shared.models import Apartment

if TYPE_CHECKING:
    from typing import Any

    from scrapy.http import Response

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


# Separation of scraping and data cleaning logic
# More: https://web-poet.readthedocs.io/
class ApartmentPage(WebPage[Apartment]):
    response: Response | None  # type: ignore[assignment]
    data: dict[str, Any]

    def __init__(self, data: dict[str, Any], *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.data = data

    @property
    @abstractmethod
    def url(self) -> str:
        ...

    @property
    @abstractmethod
    def source(self) -> Source:
        ...

    @property
    @abstractmethod
    def offer_type(self) -> OfferType:
        ...

    @property
    @abstractmethod
    def status(self) -> Status:
        ...

    @property
    @abstractmethod
    def price(self) -> Price:
        ...

    @property
    @abstractmethod
    def size(self) -> Size:
        ...

    @property
    @abstractmethod
    def rooms(self) -> Rooms:
        ...

    @property
    @abstractmethod
    def floor(self) -> int | None:
        ...

    @property
    @abstractmethod
    def location(self) -> Location | None:
        ...

    @property
    @abstractmethod
    def details(self) -> Details | None:
        ...

    @property
    @abstractmethod
    def description(self) -> str | None:
        ...

    @property
    @abstractmethod
    def photos(self) -> list[str] | None:
        ...

    def to_item(self) -> Apartment:  # type: ignore[override]
        return Apartment(
            url=self.url,  # type: ignore[arg-type]
            source=self.source,
            offer_type=self.offer_type,
            status=self.status,
            price=self.price,
            size=self.size,
            rooms=self.rooms,
            floor=self.floor,
            location=self.location,
            details=self.details,
            description=self.description,
            photos=self.photos or [],
        )
