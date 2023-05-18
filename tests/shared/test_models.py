from __future__ import annotations

import pytest
from pydantic import ValidationError
from pytest_lazyfixture import lazy_fixture

from shared.models import Apartment


@pytest.mark.parametrize("apartment", (lazy_fixture("yit_apartment"),))
class TestApartment:
    def test_from_to_dict(self, apartment: Apartment) -> None:
        assert Apartment.parse_obj(apartment.dict()) == apartment

    def test_from_to_json(self, apartment: Apartment) -> None:
        assert Apartment.parse_raw(apartment.json()) == apartment

    def test_from_to_json_pretty(self, apartment: Apartment) -> None:
        pretty = apartment.json(ensure_ascii=True, indent=4, exclude_none=True)
        assert Apartment.parse_raw(pretty) == apartment

    def test_add_garbage_to_history(self, apartment: Apartment) -> None:
        apartment.history.append("foobar")  # type: ignore[arg-type]
        # Intentionally testing adding wrong type. It's not validated at append,
        # but when serialised and deserialised it fails as expected.
        with pytest.raises(ValidationError, match="history"):
            Apartment.parse_obj(apartment.dict())

        with pytest.raises(ValidationError, match="history"):
            Apartment.parse_raw(apartment.json())
