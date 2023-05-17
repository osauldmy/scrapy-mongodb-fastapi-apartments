from __future__ import annotations

import json
from itertools import islice
from typing import TYPE_CHECKING

import pytest
from scrapy.exceptions import CloseSpider

from scraper.spiders.yit import YitSkFlatsForSale
from tests.scraper.spiders import make_fake_json_response

if TYPE_CHECKING:
    from typing import Any

    from shared.models import Apartment


class TestYitSkFlatsForSale:
    spider = YitSkFlatsForSale()

    def test_start_requests(self) -> None:
        dozen = tuple(islice(self.spider.start_requests(), 10))
        for index, request in enumerate(dozen):
            assert request.url == self.spider.API_URL
            assert request.method == "POST"
            assert request.callback == self.spider.process_listing
            assert json.loads(request.body)["PageSize"] == self.spider.PER_PAGE
            assert json.loads(request.body)["StartPage"] == index

    def test_process_listing_empty(self) -> None:
        response = make_fake_json_response({"IsMoreAvailable": True, "Hits": []})
        assert tuple(self.spider.process_listing(response)) == ()

    def test_process_listing_no_more_available_raises(self) -> None:
        response = make_fake_json_response({"IsMoreAvailable": False})
        with pytest.raises(CloseSpider):
            next(self.spider.process_listing(response))

    def test_process_listing_single_hit(
        self, yit_apartment_from_server: dict[str, Any]
    ) -> None:
        response = make_fake_json_response(
            {"IsMoreAvailable": True, "Hits": [yit_apartment_from_server]}
        )
        aux_requests = tuple(self.spider.process_listing(response))
        assert len(aux_requests) == 1
        [photo_request] = aux_requests
        assert photo_request.url == (
            "https://www.yit.sk" + yit_apartment_from_server["Fields"]["_Url"]
        )

    def test_yield_item(
        self, yit_apartment_from_server: dict[str, Any], yit_apartment: Apartment
    ) -> None:
        expected = yit_apartment
        apartments = tuple(
            self.spider.yield_item(None, yit_apartment_from_server["Fields"])
        )
        assert len(apartments) == 1

        [result] = apartments
        assert result.dict(exclude={"id"}) == expected.dict(exclude={"id"})

        result.id, expected.id = None, None
        assert result == expected
