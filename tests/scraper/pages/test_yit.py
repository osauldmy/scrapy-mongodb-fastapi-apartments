from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pytest_lazyfixture import lazy_fixture

from scraper.pages.yit import YitSkJsonApartmentPage

if TYPE_CHECKING:
    from typing import Any

    from shared.models import Apartment


class TestYitSkJsonApartmentPage:
    @pytest.mark.parametrize(
        "raw, expected",
        ((lazy_fixture("yit_apartment_from_server"), lazy_fixture("yit_apartment")),),
    )
    def test_page_to_item(
        self,
        raw: dict[str, Any],
        expected: Apartment,
    ) -> None:
        item = YitSkJsonApartmentPage(response=None, data=raw["Fields"]).to_item()
        assert item.dict(exclude={"id"}) == expected.dict(exclude={"id"})
        item.id, expected.id = None, None
        assert item == expected
