from __future__ import annotations

import datetime
import enum
from typing import Any

import countryinfo
import geojson
import geopy
from beanie import PydanticObjectId
from pydantic import (
    BaseModel,
    Field,
    HttpUrl,
    NonNegativeInt,
    PositiveFloat,
    PositiveInt,
    validator,
)


class Source(str, enum.Enum):
    """Source where real estate came into DB from."""

    SCRAPER = "scraper"
    API = "api"
    # GUI = "gui"
    # MANUAL = "manual"


class OfferType(str, enum.Enum):
    """All possible options to do with real estates."""

    SELL = "SELL"
    RENT = "RENT"
    SHARE = "SHARE"


class Status(str, enum.Enum):
    """Status of real estate: free, reserved, etc."""

    UNKNOWN = "UNKNOWN"
    FREE = "FREE"
    RESERVED = "RESERVED"
    IN_CONSTRUCTION = "IN CONSTRUCTION"
    SOLD = "SOLD"
    # RENTED = "RENTED"
    # ...


class StrictBaseModel(
    BaseModel,
    extra="forbid",
    allow_population_by_field_name=True,
    validate_assignment=True,
    validate_all=True,
    # allow_mutation=False,
):
    pass


class Location(StrictBaseModel, arbitrary_types_allowed=True):
    country_code: str
    gps: geojson.Point | None
    address: str | None

    @classmethod
    def geolocate(
        cls, latitude: float | int, longitude: float | int
    ) -> Location | None:
        float_or_int = lambda x: isinstance(x, float | int)
        if not float_or_int(latitude) or not float_or_int(longitude):
            return None

        point = (latitude, longitude)
        geolocator = geopy.Nominatim(user_agent="my test app")
        if not (place := geolocator.reverse(point)):
            return None

        return cls(
            country_code=place.raw["address"]["country_code"],
            gps=geojson.Point(point),
            address=place.address,
        )

    @validator("gps")
    def validate_point(cls, value: Any, **kwargs: Any) -> geojson.Point | None:
        match value:
            case None:
                return None
            # expecting valid lat&lng here and there, but also could be checked
            case geojson.Point():
                return value
            case {"type": "Point", "coordinates": [float() | int(), float() | int()]}:
                return geojson.Point(**value)
            case _:
                raise ValueError(
                    "gps should be either None, geojson.Point or its JSON representation"
                )

    @validator("country_code")
    def validate_country(cls, value: str, **kwargs: Any) -> str:
        try:
            countryinfo.CountryInfo(value).area()
        except KeyError as error:
            raise ValueError("Not existing country code!") from error
        return value


class Price(StrictBaseModel):
    # Choosing PositiveFloat for selling, as it can be thousands with decimal point.
    # For renting PositiveInt should be enough, but then this model is not enough,
    # because it doesn't take into account deposit, fees, etc.
    # This PoC is optimized for 1 web with flats selling.
    price: PositiveFloat
    currency: str
    note: str | None


class Size(StrictBaseModel):
    usable: PositiveFloat
    total: PositiveFloat
    note: str | None


class Rooms(StrictBaseModel):
    amount: PositiveInt
    note: str | None


class Details(StrictBaseModel):
    lift: bool | None
    balcony: bool | None
    loggia: bool | None
    terrace: bool | None
    garage: bool | None
    parking: bool | None
    # ... maybe some other stuff not covering this PoC


class Change(StrictBaseModel):
    what: dict[str, Any]
    when: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)


class Apartment(StrictBaseModel):
    id: PydanticObjectId | None = Field(default_factory=PydanticObjectId, alias="_id")
    url: HttpUrl
    source: Source
    offer_type: OfferType
    status: Status
    price: Price
    size: Size
    rooms: Rooms
    floor: NonNegativeInt | None
    location: Location | None
    details: Details | None
    description: str | None

    photos: list[str] = Field(default_factory=list)

    # to be modified when some changes are found, so we don't have almost duplicates
    history: list[Change] = Field(default_factory=list)

    @property
    def created(self) -> datetime.datetime | None:
        if self.id is None:
            return None
        return self.id.generation_time.replace(tzinfo=None)

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "url": "https://some.web.com/real_estate/foo",
                "source": Source.API,
                "offer_type": OfferType.SELL,
                "status": Status.FREE,
                "price": {"price": 300_000, "currency": "EUR"},
                "size": Size(usable=40.5, total=50, note="9.5m for balcony"),
                "rooms": Rooms(amount=3, note="2+1"),
                "floor": 3,
                "location": None,
                "details": Details(balcony=True),
                "description": "very nice apartment",
                "photos": [
                    "https://upload.wikimedia.org/wikipedia/commons/c/c0/Gingerbread_House_Essex_CT.jpg"
                ],
            }
        }
